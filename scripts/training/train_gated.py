"""
Gated fusion egitimi — 3 kademeli iyilestirme.

Bilesenler:
  - Z-score standartlastirma (feature_stats)
  - GatedFusionClassifier (per-feature attention + gating + aux head)
  - Focal Loss (opsiyonel, --focal)
  - Auxiliary clinical loss (--aux-weight)
  - Sad augmentasyonlu manifest (opsiyonel)

Kullanim:
  python -m scripts.training.train_gated --exp-id M1 \
    --manifest out/real/manifest_clean.csv \
    --features out/real/features_clinical.csv \
    --stats out/real/feature_stats.json
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, classification_report, f1_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, WeightedRandomSampler

from src.data.dataset import SigLIPDrawingDataset
from src.data.transforms import get_image_transforms
from src.models.gated_fusion_classifier import GatedFusionClassifier

CLASSES = ["Happy", "Sad", "Angry", "Fear"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def set_seed(s: int) -> None:
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def make_sampler(labels):
    counts = np.bincount(labels, minlength=4).astype(np.float32)
    counts[counts == 0] = 1.0
    w = [1.0 / counts[y] for y in labels]
    return WeightedRandomSampler(w, len(w), replacement=True)


def class_weights(labels):
    counts = np.bincount(labels, minlength=4).astype(np.float32)
    counts[counts == 0] = 1.0
    return torch.tensor(counts.sum() / (4 * counts), dtype=torch.float32)


class FocalLoss(nn.Module):
    """Class-balanced focal loss: zor orneklere (dusuk guven) odaklanir."""
    def __init__(self, weight=None, gamma: float = 2.0):
        super().__init__()
        self.weight = weight
        self.gamma = gamma

    def forward(self, logits, target):
        ce = F.cross_entropy(logits, target, weight=self.weight, reduction="none")
        pt = torch.exp(-ce)
        return ((1 - pt) ** self.gamma * ce).mean()


def run_epoch(model, loader, criterion, optimizer, train, aux_weight):
    model.train() if train else model.eval()
    total, preds, tgts = 0.0, [], []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for b in loader:
            img = b["image"].to(DEVICE, non_blocking=True)
            clin = b["clinical_features"].to(DEVICE, non_blocking=True)
            val = b["clinical_validity"].to(DEVICE, non_blocking=True)
            y = b["label"].to(DEVICE, non_blocking=True)

            if train and aux_weight > 0:
                logits, aux = model(img, clin, val, return_aux=True)
                loss = criterion(logits, y) + aux_weight * criterion(aux, y)
            else:
                logits = model(img, clin, val)
                loss = criterion(logits, y)

            if train:
                optimizer.zero_grad(); loss.backward(); optimizer.step()
            total += float(loss.item()) * y.size(0)
            preds.extend(logits.argmax(1).cpu().tolist())
            tgts.extend(y.cpu().tolist())
    n = len(tgts) or 1
    return {"loss": total / n, "acc": accuracy_score(tgts, preds),
            "macro_f1": f1_score(tgts, preds, average="macro", zero_division=0)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", required=True)
    ap.add_argument("--manifest", type=Path, default=Path("out/real/manifest_clean.csv"))
    ap.add_argument("--features", type=Path, default=Path("out/real/features_clinical.csv"))
    ap.add_argument("--stats", type=Path, default=Path("out/real/feature_stats.json"))
    ap.add_argument("--backbone", default="resnet50")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--patience", type=int, default=7)
    ap.add_argument("--focal", action="store_true")
    ap.add_argument("--gamma", type=float, default=2.0)
    ap.add_argument("--aux-weight", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    set_seed(args.seed)
    out_dir = Path("out/experiments_clean") / args.exp_id
    (out_dir / "checkpoints").mkdir(parents=True, exist_ok=True)

    print(f"=== {args.exp_id} === focal={args.focal} aux={args.aux_weight}", flush=True)
    print(f"manifest={args.manifest.name} features={args.features.name}", flush=True)

    train_tf, val_tf = get_image_transforms(image_size=224)
    stats = str(args.stats)
    train_ds = SigLIPDrawingDataset(args.manifest, "train", train_tf, args.features, stats)
    val_ds   = SigLIPDrawingDataset(args.manifest, "val",   val_tf,   args.features, stats)
    test_ds  = SigLIPDrawingDataset(args.manifest, "test",  val_tf,   args.features, stats)
    print(f"train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}", flush=True)

    labels = train_ds.df["label_id"].astype(int).tolist()
    cw = class_weights(labels).to(DEVICE)
    sampler = make_sampler(labels)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, num_workers=0)
    val_loader   = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    test_loader  = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = GatedFusionClassifier(backbone=args.backbone).to(DEVICE)
    criterion = FocalLoss(weight=cw, gamma=args.gamma) if args.focal else nn.CrossEntropyLoss(weight=cw)
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_f1, bad, t0 = -1.0, 0, time.time()
    for epoch in range(1, args.epochs + 1):
        tr = run_epoch(model, train_loader, criterion, optimizer, True, args.aux_weight)
        va = run_epoch(model, val_loader, criterion, optimizer, False, 0.0)
        scheduler.step()
        print(f"  ep{epoch:02d} train_f1={tr['macro_f1']:.4f} val_f1={va['macro_f1']:.4f} ({time.time()-t0:.0f}s)", flush=True)

        ckpt = {"model_state": model.state_dict(), "epoch": epoch,
                "val_macro_f1": va["macro_f1"], "backbone": args.backbone}
        torch.save(ckpt, out_dir / "checkpoints" / "last.pt")
        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]; bad = 0
            torch.save(ckpt, out_dir / "checkpoints" / "best.pt")
            print(f"         [BEST] {best_f1:.4f}", flush=True)
        else:
            bad += 1
            if bad >= args.patience:
                print(f"  [early stop]", flush=True); break

    # Test
    best = torch.load(out_dir / "checkpoints" / "best.pt", map_location=DEVICE, weights_only=False)
    model.load_state_dict(best["model_state"]); model.eval()
    preds, tgts = [], []
    with torch.no_grad():
        for b in test_loader:
            logits = model(b["image"].to(DEVICE), b["clinical_features"].to(DEVICE), b["clinical_validity"].to(DEVICE))
            preds.extend(logits.argmax(1).cpu().tolist()); tgts.extend(b["label"].tolist())

    rep = classification_report(tgts, preds, target_names=CLASSES, output_dict=True, zero_division=0)
    res = {
        "exp_id": args.exp_id, "backbone": args.backbone,
        "focal": args.focal, "aux_weight": args.aux_weight,
        "manifest": str(args.manifest), "features": str(args.features),
        "best_val_f1": round(float(best_f1), 4),
        "train_time_s": round(time.time() - t0, 1),
        "test_acc": round(accuracy_score(tgts, preds), 4),
        "test_macro_f1": round(f1_score(tgts, preds, average="macro", zero_division=0), 4),
        "per_class_f1": {c: round(rep[c]["f1-score"], 4) for c in CLASSES},
        "per_class_recall": {c: round(rep[c]["recall"], 4) for c in CLASSES},
        "per_class_precision": {c: round(rep[c]["precision"], 4) for c in CLASSES},
    }
    (out_dir / "result.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\n{args.exp_id}: Test F1={res['test_macro_f1']:.4f} Acc={res['test_acc']:.4f}", flush=True)
    for c in CLASSES:
        print(f"  {c:<6} F1={res['per_class_f1'][c]:.4f} (recall={res['per_class_recall'][c]:.4f})", flush=True)


if __name__ == "__main__":
    main()
