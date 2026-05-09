"""
train_expanded.py

manifest_expanded.csv (qwen 1,408 + siglip 4,028 = 5,436 toplam)
ile ClinicalFusionClassifier eğitimi.

Test seti: manifest_qwen.csv'deki orijinal 212 örnek (karşılaştırılabilirlik).

Çıktı:
  out/expanded_run/checkpoints/best.pt
  out/expanded_run/train_history.json
  out/expanded_run/test_results.json
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score, classification_report,
    f1_score, precision_score, recall_score,
)
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, WeightedRandomSampler

from torchvision import transforms

from src.data.dataset import SigLIPDrawingDataset
from src.models.fusion_classifier import ClinicalFusionClassifier

# ── Config ────────────────────────────────────────────────────────────────────
TRAIN_MANIFEST = Path("out/manifest_expanded.csv")
TEST_MANIFEST  = Path("out/manifest_qwen.csv")   # orijinal test seti
OUT            = Path("out/expanded_run")
CLASSES        = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES    = 4
SEED           = 42
BATCH          = 32
NUM_WORKERS    = 0
DEVICE         = "cuda" if torch.cuda.is_available() else "cpu"
MAX_EPOCHS     = 60
LR             = 8e-5
WEIGHT_DECAY   = 2e-4
PATIENCE       = 12
LABEL_SMOOTH   = 0.10


MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]


def make_transforms():
    train_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.RandomCrop(224),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
        transforms.RandomGrayscale(p=0.10),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
        transforms.RandomErasing(p=0.20, scale=(0.02, 0.15)),
    ])
    val_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    return train_tf, val_tf


# ── Helpers ───────────────────────────────────────────────────────────────────
def set_seed(s):
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def compute_class_weights(labels, num_classes):
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    inv = counts.sum() / (num_classes * counts)
    return torch.tensor(inv, dtype=torch.float32, device=DEVICE)


def make_sampler(labels, num_classes):
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    w = 1.0 / counts
    return WeightedRandomSampler([float(w[y]) for y in labels],
                                 num_samples=len(labels), replacement=True)


def run_epoch(model, loader, criterion, optimizer, train: bool):
    model.train() if train else model.eval()
    total_loss, preds_all, tgts_all = 0.0, [], []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for batch in loader:
            img   = batch["image"].to(DEVICE, non_blocking=True)
            clin  = batch["clinical_features"].to(DEVICE, non_blocking=True)
            valid = batch["clinical_validity"].to(DEVICE, non_blocking=True)
            y     = batch["label"].to(DEVICE, non_blocking=True)
            logits = model(img, clin, valid)
            loss = criterion(logits, y)
            if train:
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += float(loss.item()) * y.size(0)
            preds_all.extend(logits.argmax(1).detach().cpu().tolist())
            tgts_all.extend(y.detach().cpu().tolist())
    n = max(len(tgts_all), 1)
    return {
        "loss":     total_loss / n,
        "acc":      float(accuracy_score(tgts_all, preds_all)),
        "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)),
    }, tgts_all, preds_all


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    set_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(parents=True, exist_ok=True)
    print(f"[init] device={DEVICE}  seed={SEED}")

    train_tf, val_tf = make_transforms()

    # Train/val from expanded manifest; test from qwen manifest
    train_ds = SigLIPDrawingDataset(TRAIN_MANIFEST, "train", train_tf)
    val_ds   = SigLIPDrawingDataset(TRAIN_MANIFEST, "val",   val_tf)
    test_ds  = SigLIPDrawingDataset(TEST_MANIFEST,  "test",  val_tf)

    print(f"[data] train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    cw = compute_class_weights(train_labels, NUM_CLASSES)
    print(f"[data] class_weights={cw.cpu().tolist()}")

    sampler      = make_sampler(train_labels, NUM_CLASSES)
    train_loader = DataLoader(train_ds, batch_size=BATCH, sampler=sampler, num_workers=NUM_WORKERS)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False,   num_workers=NUM_WORKERS)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH, shuffle=False,   num_workers=NUM_WORKERS)

    model     = ClinicalFusionClassifier(num_classes=NUM_CLASSES, pretrained=True).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=LABEL_SMOOTH)
    optimizer = AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = CosineAnnealingLR(optimizer, T_max=MAX_EPOCHS, eta_min=1e-6)

    history: list[dict] = []
    best_f1, best_state, bad_count = -1.0, None, 0
    t0 = time.time()

    print(f"\n[train] max_epochs={MAX_EPOCHS}  patience={PATIENCE}  lr={LR}")
    for ep in range(1, MAX_EPOCHS + 1):
        tr, _, _ = run_epoch(model, train_loader, criterion, optimizer, True)
        va, _, _ = run_epoch(model, val_loader,   criterion, None,      False)
        scheduler.step()
        elapsed = time.time() - t0
        history.append({"epoch": ep, "train": tr, "val": va})
        marker = ""
        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            bad_count = 0
            marker = " * BEST"
        else:
            bad_count += 1
        print(f"[{ep:02d}/{MAX_EPOCHS}] "
              f"tr_loss={tr['loss']:.4f} tr_f1={tr['macro_f1']:.4f}  "
              f"va_loss={va['loss']:.4f} va_f1={va['macro_f1']:.4f}  "
              f"({elapsed:.0f}s){marker}")
        if bad_count >= PATIENCE:
            print(f"[early stop] patience={PATIENCE} reached at epoch {ep}")
            break

    # Save best checkpoint
    if best_state:
        model.load_state_dict(best_state)
    torch.save({"model_state": model.state_dict(), "val_macro_f1": best_f1,
                "classes": CLASSES}, OUT / "checkpoints" / "best.pt")
    (OUT / "train_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8")
    print(f"\n[save] best.pt  val_macro_f1={best_f1:.4f}")

    # Test evaluation
    print("\n=== TEST SET EVALUATION (orijinal qwen 212 test) ===")
    _, tgts, preds = run_epoch(model, test_loader, criterion, None, False)
    acc  = accuracy_score(tgts, preds)
    prec = precision_score(tgts, preds, average="macro", zero_division=0)
    rec  = recall_score(tgts, preds, average="macro", zero_division=0)
    f1   = f1_score(tgts, preds, average="macro", zero_division=0)

    print(f"Accuracy  : {acc:.4f}")
    print(f"Precision : {prec:.4f}")
    print(f"Recall    : {rec:.4f}")
    print(f"Macro F1  : {f1:.4f}")
    print()
    print(classification_report(tgts, preds, target_names=CLASSES, zero_division=0))

    per_class_f1 = f1_score(tgts, preds, average=None, zero_division=0)
    results = {
        "accuracy":          float(acc),
        "precision":         float(prec),
        "recall":            float(rec),
        "macro_f1":          float(f1),
        "per_class_f1":      {CLASSES[i]: float(per_class_f1[i]) for i in range(NUM_CLASSES)},
        "best_val_macro_f1": float(best_f1),
        "train_samples":     len(train_ds),
        "val_samples":       len(val_ds),
        "test_samples":      len(test_ds),
    }
    (OUT / "test_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print(f"[save] {OUT}/test_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
