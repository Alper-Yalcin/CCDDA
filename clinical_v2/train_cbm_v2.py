"""
clinical_v2 — v2 gostergeleriyle Concept Bottleneck egitimi.

kayip = CE(emotion,y) + concept_weight * MSE(tahmin_kavram, gercek_kavram)

Kullanim:
  python -m clinical_v2.train_cbm_v2 --exp-id V2_CB1 --mode bottleneck
  python -m clinical_v2.train_cbm_v2 --exp-id V2_CB2 --mode hybrid
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
from sklearn.metrics import accuracy_score, classification_report, f1_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, WeightedRandomSampler

from clinical_v2.dataset_v2 import DrawingDatasetV2
from clinical_v2.feature_spec_v2 import NUM_FEATURES_V2
from src.data.transforms import get_image_transforms
from src.models.concept_bottleneck_classifier import ConceptBottleneckClassifier

CLASSES = ["Happy", "Sad", "Angry", "Fear"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def make_sampler(labels):
    c = np.bincount(labels, minlength=4).astype(np.float32); c[c == 0] = 1.0
    return WeightedRandomSampler([1.0/c[y] for y in labels], len(labels), replacement=True)


def class_weights(labels):
    c = np.bincount(labels, minlength=4).astype(np.float32); c[c == 0] = 1.0
    return torch.tensor(c.sum()/(4*c), dtype=torch.float32)


def run_epoch(model, loader, ce, opt, train, cw):
    model.train() if train else model.eval()
    preds, tgts = [], []
    tot_cl = 0.0
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for b in loader:
            img = b["image"].to(DEVICE, non_blocking=True)
            tc = b["clinical_features"].to(DEVICE, non_blocking=True)
            val = b["clinical_validity"].to(DEVICE, non_blocking=True)
            y = b["label"].to(DEVICE, non_blocking=True)
            logits, pc = model(img, return_concepts=True)
            loss_ce = ce(logits, y)
            diff = (pc - tc) ** 2 * val
            loss_c = diff.sum() / val.sum().clamp(min=1.0)
            loss = loss_ce + cw * loss_c
            if train:
                opt.zero_grad(); loss.backward(); opt.step()
            tot_cl += float(loss_c.item()) * y.size(0)
            preds.extend(logits.argmax(1).cpu().tolist()); tgts.extend(y.cpu().tolist())
    n = len(tgts) or 1
    return {"concept": tot_cl/n, "acc": accuracy_score(tgts, preds),
            "macro_f1": f1_score(tgts, preds, average="macro", zero_division=0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp-id", required=True)
    ap.add_argument("--mode", default="bottleneck", choices=["bottleneck", "hybrid"])
    ap.add_argument("--manifest", type=Path, default=Path("out/real/manifest_sadaug.csv"))
    ap.add_argument("--features", type=Path, default=Path("out/real/features_v2.csv"))
    ap.add_argument("--stats", type=Path, default=Path("out/real/feature_stats_v2.json"))
    ap.add_argument("--backbone", default="resnet50")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--patience", type=int, default=7)
    ap.add_argument("--concept-weight", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    set_seed(args.seed)
    out_dir = Path("out/experiments_v2") / args.exp_id
    (out_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
    print(f"=== {args.exp_id} === mode={args.mode} cw={args.concept_weight} feats=v2({NUM_FEATURES_V2})", flush=True)

    train_tf, val_tf = get_image_transforms(image_size=224)
    stats = str(args.stats)
    tr = DrawingDatasetV2(args.manifest, "train", train_tf, args.features, stats)
    va = DrawingDatasetV2(args.manifest, "val", val_tf, args.features, stats)
    te = DrawingDatasetV2(args.manifest, "test", val_tf, args.features, stats)
    print(f"train={len(tr)} val={len(va)} test={len(te)}", flush=True)

    labels = tr.df["label_id"].astype(int).tolist()
    cw = class_weights(labels).to(DEVICE)
    sampler = make_sampler(labels)
    trl = DataLoader(tr, batch_size=args.batch_size, sampler=sampler, num_workers=0)
    val = DataLoader(va, batch_size=args.batch_size, shuffle=False, num_workers=0)
    tel = DataLoader(te, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = ConceptBottleneckClassifier(backbone=args.backbone, num_concepts=NUM_FEATURES_V2,
                                        mode=args.mode).to(DEVICE)
    ce = nn.CrossEntropyLoss(weight=cw)
    opt = AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sch = CosineAnnealingLR(opt, T_max=args.epochs)

    best, bad, t0 = -1.0, 0, time.time()
    for ep in range(1, args.epochs + 1):
        t = run_epoch(model, trl, ce, opt, True, args.concept_weight)
        v = run_epoch(model, val, ce, opt, False, args.concept_weight)
        sch.step()
        print(f"  ep{ep:02d} tr_f1={t['macro_f1']:.4f} val_f1={v['macro_f1']:.4f} "
              f"cMSE={v['concept']:.3f} ({time.time()-t0:.0f}s)", flush=True)
        ck = {"model_state": model.state_dict(), "epoch": ep, "val_macro_f1": v["macro_f1"],
              "backbone": args.backbone, "mode": args.mode, "num_concepts": NUM_FEATURES_V2}
        torch.save(ck, out_dir / "checkpoints" / "last.pt")
        if v["macro_f1"] > best:
            best = v["macro_f1"]; bad = 0
            torch.save(ck, out_dir / "checkpoints" / "best.pt")
            print(f"         [BEST] {best:.4f}", flush=True)
        else:
            bad += 1
            if bad >= args.patience:
                print("  [early stop]", flush=True); break

    bk = torch.load(out_dir / "checkpoints" / "best.pt", map_location=DEVICE, weights_only=False)
    model.load_state_dict(bk["model_state"]); model.eval()
    preds, tgts = [], []
    with torch.no_grad():
        for b in tel:
            logits = model(b["image"].to(DEVICE))
            preds.extend(logits.argmax(1).cpu().tolist()); tgts.extend(b["label"].tolist())
    rep = classification_report(tgts, preds, target_names=CLASSES, output_dict=True, zero_division=0)
    res = {"exp_id": args.exp_id, "mode": args.mode, "feature_version": "v2",
           "num_concepts": NUM_FEATURES_V2, "best_val_f1": round(float(best), 4),
           "train_time_s": round(time.time()-t0, 1),
           "test_acc": round(accuracy_score(tgts, preds), 4),
           "test_macro_f1": round(f1_score(tgts, preds, average="macro", zero_division=0), 4),
           "per_class_f1": {c: round(rep[c]["f1-score"], 4) for c in CLASSES},
           "per_class_recall": {c: round(rep[c]["recall"], 4) for c in CLASSES},
           "per_class_precision": {c: round(rep[c]["precision"], 4) for c in CLASSES}}
    (out_dir / "result.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(f"\n{args.exp_id}: Test F1={res['test_macro_f1']:.4f} Acc={res['test_acc']:.4f}", flush=True)
    for c in CLASSES:
        print(f"  {c:<6} F1={res['per_class_f1'][c]:.4f}", flush=True)


if __name__ == "__main__":
    main()
