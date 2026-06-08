"""
B3 modelini gercek klinik ozelliklerle yeniden egitir.

Kullanim:
  python -m scripts.training.train_b3_with_features
"""

from __future__ import annotations

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

from src.data.dataset import SigLIPDrawingDataset
from src.data.transforms import get_image_transforms
from src.models.flexible_classifier import FlexibleFusionClassifier

MANIFEST     = Path("out/real/manifest_clean.csv")
FEATURES_CSV = Path("out/real/features_clinical.csv")
OUT_DIR      = Path("out/experiments/B3_feat")
CLASSES      = ["Happy", "Sad", "Angry", "Fear"]
DEVICE       = "cuda" if torch.cuda.is_available() else "cpu"

BACKBONE    = "resnet50"
IMAGE_ONLY  = False
EPOCHS      = 30
BATCH_SIZE  = 32
LR          = 1e-4
PATIENCE    = 7
SEED        = 42


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def make_sampler(labels: list[int]) -> WeightedRandomSampler:
    counts = np.bincount(labels, minlength=4).astype(np.float32)
    counts[counts == 0] = 1.0
    weights = [float(1.0 / counts[y]) for y in labels]
    return WeightedRandomSampler(weights, len(weights), replacement=True)


def compute_class_weights(labels: list[int]) -> torch.Tensor:
    counts = np.bincount(labels, minlength=4).astype(np.float32)
    counts[counts == 0] = 1.0
    inv = counts.sum() / (4 * counts)
    return torch.tensor(inv, dtype=torch.float32)


def run_epoch(model, loader, criterion, optimizer, device, train: bool) -> dict:
    model.train() if train else model.eval()
    total_loss, all_preds, all_tgts = 0.0, [], []
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
            all_preds.extend(logits.argmax(1).detach().cpu().tolist())
            all_tgts.extend(y.detach().cpu().tolist())
    n = len(all_tgts) or 1
    return {
        "loss":     total_loss / n,
        "acc":      float(accuracy_score(all_tgts, all_preds)),
        "macro_f1": float(f1_score(all_tgts, all_preds, average="macro", zero_division=0)),
    }


def main() -> None:
    set_seed(SEED)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "checkpoints").mkdir(exist_ok=True)

    print(f"Device: {DEVICE}")
    print(f"Manifest: {MANIFEST}")
    print(f"Features: {FEATURES_CSV}")

    train_tf, val_tf = get_image_transforms(image_size=224)

    train_ds = SigLIPDrawingDataset(MANIFEST, "train", transform=train_tf,  features_csv=FEATURES_CSV)
    val_ds   = SigLIPDrawingDataset(MANIFEST, "val",   transform=val_tf,    features_csv=FEATURES_CSV)
    test_ds  = SigLIPDrawingDataset(MANIFEST, "test",  transform=val_tf,    features_csv=FEATURES_CSV)

    print(f"train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    cls_weights  = compute_class_weights(train_labels).to(DEVICE)
    sampler      = make_sampler(train_labels)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler,
                              num_workers=0, pin_memory=(DEVICE == "cuda"))
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=0, pin_memory=(DEVICE == "cuda"))
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False,
                              num_workers=0, pin_memory=(DEVICE == "cuda"))

    model     = FlexibleFusionClassifier(backbone=BACKBONE, image_only=IMAGE_ONLY).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=cls_weights)
    optimizer = AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_f1, bad, history = -1.0, 0, []
    t0 = time.time()

    for epoch in range(1, EPOCHS + 1):
        tr = run_epoch(model, train_loader, criterion, optimizer, DEVICE, train=True)
        va = run_epoch(model, val_loader,   criterion, optimizer, DEVICE, train=False)
        scheduler.step()

        elapsed = time.time() - t0
        history.append({"epoch": epoch, "train": tr, "val": va})
        print(f"  ep{epoch:02d} train_f1={tr['macro_f1']:.4f}  val_f1={va['macro_f1']:.4f}  ({elapsed:.0f}s)", flush=True)

        ckpt = {
            "model_state":  model.state_dict(),
            "epoch":        epoch,
            "val_macro_f1": va["macro_f1"],
            "backbone":     BACKBONE,
            "image_only":   IMAGE_ONLY,
        }
        torch.save(ckpt, OUT_DIR / "checkpoints" / "last.pt")

        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            bad = 0
            torch.save(ckpt, OUT_DIR / "checkpoints" / "best.pt")
            print(f"         [BEST] val_macro_f1={best_f1:.4f}")
        else:
            bad += 1
            if bad >= PATIENCE:
                print(f"  [early stop] patience={PATIENCE}")
                break

    # Test degerlendirmesi
    best_ckpt = torch.load(OUT_DIR / "checkpoints" / "best.pt", map_location=DEVICE, weights_only=False)
    model.load_state_dict(best_ckpt["model_state"])
    model.eval()

    all_preds, all_tgts = [], []
    with torch.no_grad():
        for batch in test_loader:
            img   = batch["image"].to(DEVICE)
            clin  = batch["clinical_features"].to(DEVICE)
            valid = batch["clinical_validity"].to(DEVICE)
            logits = model(img, clin, valid)
            all_preds.extend(logits.argmax(1).cpu().tolist())
            all_tgts.extend(batch["label"].tolist())

    report = classification_report(all_tgts, all_preds, target_names=CLASSES,
                                   output_dict=True, zero_division=0)
    test_f1  = f1_score(all_tgts, all_preds, average="macro", zero_division=0)
    test_acc = accuracy_score(all_tgts, all_preds)

    print(f"\n--- B3_feat Test Sonuclari ---")
    print(f"Test Makro F1 : {test_f1:.4f}")
    print(f"Test Dogruluk : {test_acc:.4f}")
    for cls in CLASSES:
        print(f"  {cls:<8} F1={report[cls]['f1-score']:.4f}")

    result = {
        "exp_id":      "B3_feat",
        "label":       "ResNet-50 + Klinik (gercek ozellikler)",
        "backbone":    BACKBONE,
        "image_only":  IMAGE_ONLY,
        "features_csv": str(FEATURES_CSV),
        "best_val_f1": round(float(best_f1), 4),
        "train_time_s": round(time.time() - t0, 1),
        "test_acc":    round(float(test_acc), 4),
        "test_macro_f1": round(float(test_f1), 4),
        "per_class_f1": {cls: round(report[cls]["f1-score"], 4) for cls in CLASSES},
        "per_class_precision": {cls: round(report[cls]["precision"], 4) for cls in CLASSES},
        "per_class_recall": {cls: round(report[cls]["recall"], 4) for cls in CLASSES},
    }

    (OUT_DIR / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nKaydedildi: {OUT_DIR}/result.json")


if __name__ == "__main__":
    main()
