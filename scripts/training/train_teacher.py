"""
train_teacher.py — Ogretmen Modeli

manifest_v2.csv (qwen + Kaggle/data + NewArts2) ile guclu EfficientNet egitimi.
Bu model KIDO ve SigLIP veri setlerini pseudo-label etmek icin kullanilacak.

Train: 2,093 (dengeli ~520/sinif)  Val/Test: 212/212 (qwen sabit set)
Cikti: out/teacher_run/
"""
from __future__ import annotations

import json, random, sys, time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import transforms

from src.data.dataset import SigLIPDrawingDataset
from src.models.fusion_classifier import ClinicalFusionClassifier

MANIFEST    = Path("out/manifest_v2.csv")
OUT         = Path("out/teacher_run")
CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES = 4
SEED        = 42
BATCH       = 32
NUM_WORKERS = 0
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
MAX_EPOCHS  = 80
LR          = 6e-5
WEIGHT_DECAY = 2e-4
PATIENCE    = 15
LABEL_SMOOTH = 0.08

MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]


def make_transforms():
    train_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.3),
        transforms.RandomVerticalFlip(p=0.05),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.3, hue=0.08),
        transforms.RandomGrayscale(p=0.12),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
        transforms.RandomErasing(p=0.25, scale=(0.02, 0.20)),
    ])
    val_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    return train_tf, val_tf


def set_seed(s):
    random.seed(s); np.random.seed(s)
    torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def class_weights_tensor(labels, n):
    counts = np.bincount(labels, minlength=n).astype(np.float32)
    counts[counts == 0] = 1.0
    inv = counts.sum() / (n * counts)
    return torch.tensor(inv, dtype=torch.float32, device=DEVICE)


def make_sampler(labels, n):
    counts = np.bincount(labels, minlength=n).astype(np.float32)
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
                optimizer.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += loss.item() * y.size(0)
            preds_all.extend(logits.argmax(1).detach().cpu().tolist())
            tgts_all.extend(y.detach().cpu().tolist())
    n = max(len(tgts_all), 1)
    return {
        "loss": total_loss / n,
        "acc": float(accuracy_score(tgts_all, preds_all)),
        "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)),
    }, tgts_all, preds_all


def main():
    set_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(parents=True, exist_ok=True)
    print(f"[init] device={DEVICE}  Ogretmen modeli")
    print(f"[manifest] {MANIFEST}")

    train_tf, val_tf = make_transforms()
    train_ds = SigLIPDrawingDataset(MANIFEST, "train", train_tf)
    val_ds   = SigLIPDrawingDataset(MANIFEST, "val",   val_tf)
    test_ds  = SigLIPDrawingDataset(MANIFEST, "test",  val_tf)
    print(f"[data] train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    cw      = class_weights_tensor(train_labels, NUM_CLASSES)
    sampler = make_sampler(train_labels, NUM_CLASSES)
    print(f"[data] class_weights={[round(x, 3) for x in cw.tolist()]}")

    train_loader = DataLoader(train_ds, batch_size=BATCH, sampler=sampler,
                              num_workers=NUM_WORKERS, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=True)

    model     = ClinicalFusionClassifier(num_classes=NUM_CLASSES, pretrained=True).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=LABEL_SMOOTH)
    optimizer = AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = CosineAnnealingLR(optimizer, T_max=MAX_EPOCHS, eta_min=5e-7)

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
            best_f1   = va["macro_f1"]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            bad_count = 0; marker = " * BEST"
        else:
            bad_count += 1
        print(f"[{ep:02d}/{MAX_EPOCHS}] tr_loss={tr['loss']:.4f} tr_f1={tr['macro_f1']:.4f}  "
              f"va_loss={va['loss']:.4f} va_f1={va['macro_f1']:.4f}  ({elapsed:.0f}s){marker}")
        if bad_count >= PATIENCE:
            print(f"[early stop] epoch {ep}")
            break

    if best_state:
        model.load_state_dict(best_state)
    torch.save({"model_state": model.state_dict(), "val_macro_f1": best_f1,
                "classes": CLASSES, "num_classes": NUM_CLASSES},
               OUT / "checkpoints" / "best.pt")
    (OUT / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"\n[save] best.pt  val_macro_f1={best_f1:.4f}")

    print("\n=== TEST (qwen 212) ===")
    _, tgts, preds = run_epoch(model, test_loader, criterion, None, False)
    acc  = accuracy_score(tgts, preds)
    prec = precision_score(tgts, preds, average="macro", zero_division=0)
    rec  = recall_score(tgts, preds, average="macro", zero_division=0)
    f1   = f1_score(tgts, preds, average="macro", zero_division=0)
    print(f"Accuracy: {acc:.4f}  Precision: {prec:.4f}  Recall: {rec:.4f}  F1: {f1:.4f}")
    print(classification_report(tgts, preds, target_names=CLASSES, zero_division=0))

    per_class_f1 = f1_score(tgts, preds, average=None, zero_division=0)
    results = {
        "accuracy": float(acc), "precision": float(prec),
        "recall": float(rec), "macro_f1": float(f1),
        "per_class_f1": {CLASSES[i]: float(per_class_f1[i]) for i in range(NUM_CLASSES)},
        "best_val_macro_f1": float(best_f1),
        "train_samples": len(train_ds), "val_samples": len(val_ds), "test_samples": len(test_ds),
    }
    (OUT / "test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[save] {OUT}/test_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
