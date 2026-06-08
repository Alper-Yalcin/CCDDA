"""
4-sinif egitim donguusu (image + klinik fusion).

Cikti:
  out/checkpoints/best.pt    : best macro_f1 model
  out/checkpoints/last.pt    : son epoch
  out/train_history.json     : per-epoch metrikler
  out/config_snapshot.json   : hiperparametreler
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, WeightedRandomSampler

from src.data.dataset import SigLIPDrawingDataset
from src.data.transforms import get_image_transforms
from src.models.fusion_classifier import ClinicalFusionClassifier


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def compute_class_weights(labels: list[int], num_classes: int) -> torch.Tensor:
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    inv = counts.sum() / (num_classes * counts)
    return torch.tensor(inv, dtype=torch.float32)


def make_sampler(labels: list[int], num_classes: int) -> WeightedRandomSampler:
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    weights_per_class = 1.0 / counts
    weights = [float(weights_per_class[y]) for y in labels]
    return WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)


def run_epoch(model, loader, criterion, optimizer, device, train: bool):
    model.train() if train else model.eval()
    total_loss = 0.0
    all_preds: list[int] = []
    all_targets: list[int] = []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for batch in loader:
            img = batch["image"].to(device, non_blocking=True)
            clin = batch["clinical_features"].to(device, non_blocking=True)
            valid = batch["clinical_validity"].to(device, non_blocking=True)
            y = batch["label"].to(device, non_blocking=True)

            logits = model(img, clin, valid)
            loss = criterion(logits, y)
            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += float(loss.item()) * y.size(0)
            preds = logits.argmax(dim=1).detach().cpu().numpy().tolist()
            all_preds.extend(preds)
            all_targets.extend(y.detach().cpu().numpy().tolist())

    n = len(all_targets) if all_targets else 1
    return {
        "loss": total_loss / n,
        "acc": float(accuracy_score(all_targets, all_preds)) if all_targets else 0.0,
        "macro_f1": float(f1_score(all_targets, all_preds, average="macro", zero_division=0)) if all_targets else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--features", type=Path, default=None)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--patience", type=int, default=7)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    set_seed(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "checkpoints").mkdir(parents=True, exist_ok=True)

    print(f"[init] device={args.device} seed={args.seed}")
    train_tf, val_tf = get_image_transforms(image_size=224)

    train_ds = SigLIPDrawingDataset(args.manifest, "train", transform=train_tf, features_csv=args.features)
    val_ds = SigLIPDrawingDataset(args.manifest, "val", transform=val_tf, features_csv=args.features)
    print(f"[data] train={len(train_ds)} val={len(val_ds)}")

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    sampler = make_sampler(train_labels, num_classes=4)
    cls_weights = compute_class_weights(train_labels, num_classes=4).to(args.device)
    print(f"[data] class_weights={cls_weights.cpu().tolist()}")

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, sampler=sampler,
        num_workers=args.num_workers, pin_memory=(args.device == "cuda"),
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False,
        num_workers=args.num_workers, pin_memory=(args.device == "cuda"),
    )

    model = ClinicalFusionClassifier(num_classes=4).to(args.device)
    criterion = nn.CrossEntropyLoss(weight=cls_weights)
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs)

    history: list[dict] = []
    best_f1 = -1.0
    best_epoch = -1
    bad_streak = 0
    t0 = time.time()

    for epoch in range(1, args.epochs + 1):
        tr = run_epoch(model, train_loader, criterion, optimizer, args.device, train=True)
        va = run_epoch(model, val_loader, criterion, optimizer, args.device, train=False)
        scheduler.step()

        elapsed = time.time() - t0
        history.append({"epoch": epoch, "train": tr, "val": va, "lr": scheduler.get_last_lr()[0]})
        print(
            f"[ep {epoch:02d}/{args.epochs}] "
            f"train_loss={tr['loss']:.4f} train_f1={tr['macro_f1']:.4f}  "
            f"val_loss={va['loss']:.4f} val_f1={va['macro_f1']:.4f}  "
            f"({elapsed:.0f}s)"
        )

        meta = {
            "model_state": model.state_dict(),
            "epoch": epoch,
            "val_macro_f1": va["macro_f1"],
            "args": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
        }
        torch.save(meta, args.out / "checkpoints" / "last.pt")

        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            best_epoch = epoch
            bad_streak = 0
            torch.save(meta, args.out / "checkpoints" / "best.pt")
            print(f"        [BEST] best.pt guncellendi (val_macro_f1={best_f1:.4f})")
        else:
            bad_streak += 1
            if bad_streak >= args.patience:
                print(f"[early stop] patience={args.patience} dolduruldu")
                break

    (args.out / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (args.out / "config_snapshot.json").write_text(
        json.dumps({k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()}, indent=2),
        encoding="utf-8",
    )
    print(f"\nBitti. best_epoch={best_epoch} best_val_macro_f1={best_f1:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
