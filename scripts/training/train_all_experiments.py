"""
Tum deneyleri sirayla egiten ana script.

Grup A (Ablasyon):
  A1: EfficientNet-B0, klinik YOK
  A2: EfficientNet-B0, klinik VAR
  A3: EfficientNet-B3, klinik YOK
  A4: EfficientNet-B3, klinik VAR

Grup B (Mimari Karsilastirma, hepsi klinik VAR):
  B1: EfficientNet-B0  (A2 ile ayni — referans)
  B2: EfficientNet-B3  (A4 ile ayni — referans)
  B3: ResNet-50
  B4: MobileNetV3-Large
  B5: ViT-B/16

Kullanim:
  python -m scripts.training.train_all_experiments \
    --manifest out/real/manifest.csv \
    --out-root out/experiments \
    --epochs 30
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, classification_report
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, WeightedRandomSampler

from src.data.dataset import SigLIPDrawingDataset
from src.data.transforms import get_image_transforms
from src.models.flexible_classifier import FlexibleFusionClassifier


CLASSES = ["Happy", "Sad", "Angry", "Fear"]

EXPERIMENTS = [
    # (id,  backbone,          image_only, label)
    ("A1", "efficientnet_b0", True,  "EfficientNet-B0 (gorsel only)"),
    ("A2", "efficientnet_b0", False, "EfficientNet-B0 + Klinik"),
    ("A3", "efficientnet_b3", True,  "EfficientNet-B3 (gorsel only)"),
    ("A4", "efficientnet_b3", False, "EfficientNet-B3 + Klinik"),
    ("B3", "resnet50",        False, "ResNet-50 + Klinik"),
    ("B4", "mobilenet_v3",    False, "MobileNetV3 + Klinik"),
    ("B5", "vit_b16",         False, "ViT-B/16 + Klinik"),
    ("B6", "resnet50",        True,  "ResNet-50 (gorsel only)"),  # Ablasyon: B3 ile karsilastirma
]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def make_sampler(labels: list[int], num_classes: int) -> WeightedRandomSampler:
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    weights = [float(1.0 / counts[y]) for y in labels]
    return WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)


def compute_class_weights(labels: list[int], num_classes: int) -> torch.Tensor:
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    inv = counts.sum() / (num_classes * counts)
    return torch.tensor(inv, dtype=torch.float32)


def run_epoch(model, loader, criterion, optimizer, device, train: bool) -> dict:
    model.train() if train else model.eval()
    total_loss = 0.0
    all_preds, all_targets = [], []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for batch in loader:
            img   = batch["image"].to(device, non_blocking=True)
            clin  = batch["clinical_features"].to(device, non_blocking=True)
            valid = batch["clinical_validity"].to(device, non_blocking=True)
            y     = batch["label"].to(device, non_blocking=True)

            logits = model(img, clin, valid)
            loss   = criterion(logits, y)

            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            total_loss += float(loss.item()) * y.size(0)
            all_preds.extend(logits.argmax(dim=1).detach().cpu().numpy().tolist())
            all_targets.extend(y.detach().cpu().numpy().tolist())

    n = len(all_targets) or 1
    return {
        "loss":      total_loss / n,
        "acc":       float(accuracy_score(all_targets, all_preds)),
        "macro_f1":  float(f1_score(all_targets, all_preds, average="macro", zero_division=0)),
    }


def evaluate_test(model, loader, device) -> dict:
    model.eval()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for batch in loader:
            img   = batch["image"].to(device, non_blocking=True)
            clin  = batch["clinical_features"].to(device, non_blocking=True)
            valid = batch["clinical_validity"].to(device, non_blocking=True)
            y     = batch["label"].to(device, non_blocking=True)
            logits = model(img, clin, valid)
            all_preds.extend(logits.argmax(dim=1).detach().cpu().numpy().tolist())
            all_targets.extend(y.detach().cpu().numpy().tolist())

    report = classification_report(
        all_targets, all_preds,
        target_names=CLASSES,
        output_dict=True,
        zero_division=0,
    )
    # Top-2 accuracy
    top2 = 0
    return {
        "test_acc":      float(accuracy_score(all_targets, all_preds)),
        "test_macro_f1": float(f1_score(all_targets, all_preds, average="macro", zero_division=0)),
        "per_class_f1":  {cls: round(report[cls]["f1-score"], 4) for cls in CLASSES},
        "per_class_precision": {cls: round(report[cls]["precision"], 4) for cls in CLASSES},
        "per_class_recall":    {cls: round(report[cls]["recall"], 4) for cls in CLASSES},
    }


def train_one_experiment(
    exp_id: str,
    backbone: str,
    image_only: bool,
    label: str,
    manifest: Path,
    out_dir: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    patience: int,
    num_workers: int,
    device: str,
    seed: int,
    features_csv: Path = None,
) -> dict:
    print(f"\n{'='*60}", flush=True)
    print(f"[{exp_id}] {label}", flush=True)
    print(f"{'='*60}", flush=True)

    set_seed(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "checkpoints").mkdir(exist_ok=True)

    # Klinik ozellikler: sadece fusion modeller icin, image-only'de None
    feat_csv = features_csv if (not image_only and features_csv is not None) else None

    train_tf, val_tf = get_image_transforms(image_size=224)
    train_ds = SigLIPDrawingDataset(manifest, "train", transform=train_tf, features_csv=feat_csv)
    val_ds   = SigLIPDrawingDataset(manifest, "val",   transform=val_tf,   features_csv=feat_csv)
    test_ds  = SigLIPDrawingDataset(manifest, "test",  transform=val_tf,   features_csv=feat_csv)

    print(f"  train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}", flush=True)
    print(f"  features_csv={'VAR' if feat_csv else 'YOK (image-only)'}", flush=True)

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    cls_weights  = compute_class_weights(train_labels, 4).to(device)
    sampler      = make_sampler(train_labels, 4)

    train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler,
                              num_workers=num_workers, pin_memory=(device=="cuda"))
    val_loader   = DataLoader(val_ds,   batch_size=batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=(device=="cuda"))
    test_loader  = DataLoader(test_ds,  batch_size=batch_size, shuffle=False,
                              num_workers=num_workers, pin_memory=(device=="cuda"))

    model     = FlexibleFusionClassifier(backbone=backbone, image_only=image_only).to(device)
    criterion = nn.CrossEntropyLoss(weight=cls_weights)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs)

    history  = []
    best_f1  = -1.0
    bad      = 0
    t0       = time.time()

    for epoch in range(1, epochs + 1):
        tr = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        va = run_epoch(model, val_loader,   criterion, optimizer, device, train=False)
        scheduler.step()

        elapsed = time.time() - t0
        history.append({"epoch": epoch, "train": tr, "val": va})
        print(f"  ep{epoch:02d} train_f1={tr['macro_f1']:.4f} val_f1={va['macro_f1']:.4f} val_acc={va['acc']:.4f} ({elapsed:.0f}s)", flush=True)

        ckpt = {
            "model_state":   model.state_dict(),
            "epoch":         epoch,
            "val_macro_f1":  va["macro_f1"],
            "backbone":      backbone,
            "image_only":    image_only,
        }
        torch.save(ckpt, out_dir / "checkpoints" / "last.pt")

        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            bad = 0
            torch.save(ckpt, out_dir / "checkpoints" / "best.pt")
            print(f"         [BEST] val_macro_f1={best_f1:.4f}")
        else:
            bad += 1
            if bad >= patience:
                print(f"  [early stop] patience={patience}")
                break

    # Test seti degerlendirmesi (best checkpoint ile)
    best_ckpt = torch.load(out_dir / "checkpoints" / "best.pt", map_location=device)
    model.load_state_dict(best_ckpt["model_state"])
    test_metrics = evaluate_test(model, test_loader, device)

    print(f"\n  --- Test Sonuclari ---")
    print(f"  test_acc      : {test_metrics['test_acc']:.4f}")
    print(f"  test_macro_f1 : {test_metrics['test_macro_f1']:.4f}")
    for cls in CLASSES:
        print(f"  {cls:<8} F1={test_metrics['per_class_f1'][cls]:.4f}")

    train_time = time.time() - t0
    result = {
        "exp_id":       exp_id,
        "label":        label,
        "backbone":     backbone,
        "image_only":   image_only,
        "best_val_f1":  round(best_f1, 4),
        "train_time_s": round(train_time, 1),
        **{k: round(v, 4) if isinstance(v, float) else v
           for k, v in test_metrics.items()},
    }

    (out_dir / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (out_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest",    required=True, type=Path)
    ap.add_argument("--out-root",    required=True, type=Path)
    ap.add_argument("--epochs",      type=int,   default=30)
    ap.add_argument("--batch-size",  type=int,   default=32)
    ap.add_argument("--lr",          type=float, default=1e-4)
    ap.add_argument("--patience",    type=int,   default=7)
    ap.add_argument("--num-workers", type=int,   default=2)
    ap.add_argument("--device",      type=str,   default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed",        type=int,   default=42)
    ap.add_argument("--only",        type=str,   default=None,
                    help="Sadece bu deneyi calistir (ornek: A1,B3)")
    ap.add_argument("--features-csv", type=Path, default=None,
                    help="Klinik ozellik CSV (fusion modeller icin)")
    args = ap.parse_args()

    args.out_root.mkdir(parents=True, exist_ok=True)
    print(f"Device: {args.device} | Epochs: {args.epochs} | Batch: {args.batch_size}")

    only_ids = set(args.only.split(",")) if args.only else None
    all_results = []

    for exp_id, backbone, image_only, label in EXPERIMENTS:
        if only_ids and exp_id not in only_ids:
            continue
        out_dir = args.out_root / exp_id
        result  = train_one_experiment(
            exp_id=exp_id, backbone=backbone, image_only=image_only, label=label,
            manifest=args.manifest, out_dir=out_dir,
            epochs=args.epochs, batch_size=args.batch_size, lr=args.lr,
            patience=args.patience, num_workers=args.num_workers,
            device=args.device, seed=args.seed,
            features_csv=args.features_csv,
        )
        all_results.append(result)
        # Ara ozet kaydet
        (args.out_root / "all_results.json").write_text(
            json.dumps(all_results, indent=2), encoding="utf-8"
        )

    # Final ozet tablosu
    print(f"\n{'='*70}")
    print("TAMAMLANAN DENEYLER OZETI")
    print(f"{'='*70}")
    print(f"{'ID':<4} {'Model':<35} {'Val F1':<8} {'Test F1':<8} {'Test Acc':<9} {'Sure(s)'}")
    print("-" * 70)
    for r in all_results:
        print(f"{r['exp_id']:<4} {r['label']:<35} {r['best_val_f1']:<8.4f} "
              f"{r['test_macro_f1']:<8.4f} {r['test_acc']:<9.4f} {r['train_time_s']:.0f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
