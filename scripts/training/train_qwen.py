"""
dataset_qwen_selected icin 2-phase transfer learning egitimi.

Phase 1: Backbone dondurulmus, sadece head egitilir (yuksek LR).
Phase 2: Tam model (cok dusuk LR).

Cikti: out/qwen_v2/{checkpoints/best.pt, train_history.json}
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
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import transforms

from src.data.dataset import SigLIPDrawingDataset
from src.models.fusion_classifier import ClinicalFusionClassifier

MANIFEST = Path("out/manifest_qwen.csv")
OUT = Path("out/qwen_v2")
SEED = 42
BATCH = 32
NUM_WORKERS = 0
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

PHASE1_EPOCHS = 15
PHASE1_LR = 5e-3
PHASE2_EPOCHS = 30
PHASE2_LR = 5e-5
PATIENCE = 10

CLASSES = ["Happy", "Sad", "Angry", "Fear"]


def set_seed(s: int) -> None:
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def make_sampler(labels: list[int], num_classes: int) -> WeightedRandomSampler:
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    w = 1.0 / counts
    weights = [float(w[y]) for y in labels]
    return WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)


def class_weights(labels: list[int], num_classes: int, device: str) -> torch.Tensor:
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    inv = counts.sum() / (num_classes * counts)
    return torch.tensor(inv, dtype=torch.float32, device=device)


def run_epoch(model, loader, criterion, optimizer, device: str, train: bool):
    model.train() if train else model.eval()
    total_loss = 0.0
    preds_all: list[int] = []
    tgts_all: list[int] = []
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
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += float(loss.item()) * y.size(0)
            preds_all.extend(logits.argmax(1).cpu().tolist())
            tgts_all.extend(y.cpu().tolist())
    n = max(len(tgts_all), 1)
    return {
        "loss": total_loss / n,
        "acc": float(accuracy_score(tgts_all, preds_all)) if tgts_all else 0.0,
        "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)) if tgts_all else 0.0,
    }, tgts_all, preds_all


def train_phase(model, train_loader, val_loader, criterion, optimizer, scheduler,
                epochs: int, patience: int, device: str, history: list, phase: str):
    best_f1 = -1.0
    best_epoch = -1
    bad_streak = 0
    best_state = None
    t0 = time.time()

    for epoch in range(1, epochs + 1):
        tr, _, _ = run_epoch(model, train_loader, criterion, optimizer, device, train=True)
        va, _, _ = run_epoch(model, val_loader, criterion, optimizer, device, train=False)
        if scheduler is not None:
            scheduler.step()

        elapsed = time.time() - t0
        rec = {"phase": phase, "epoch": epoch, "train": tr, "val": va}
        history.append(rec)
        print(
            f"[{phase} ep {epoch:02d}/{epochs}] "
            f"train_loss={tr['loss']:.4f} train_f1={tr['macro_f1']:.4f}  "
            f"val_loss={va['loss']:.4f} val_f1={va['macro_f1']:.4f}  "
            f"({elapsed:.0f}s)"
        )

        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            best_epoch = epoch
            bad_streak = 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            print(f"        [BEST] val_macro_f1={best_f1:.4f}")
        else:
            bad_streak += 1
            if bad_streak >= patience:
                print(f"[early stop] patience={patience} doldu")
                break

    return best_f1, best_epoch, best_state


def get_transforms(image_size: int = 224):
    train_tf = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomRotation(15),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
        transforms.RandomGrayscale(p=0.05),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        transforms.RandomErasing(p=0.1, scale=(0.02, 0.1)),
    ])
    val_tf = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return train_tf, val_tf


def main() -> int:
    set_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(parents=True, exist_ok=True)

    print(f"[init] device={DEVICE}")
    train_tf, val_tf = get_transforms()

    train_ds = SigLIPDrawingDataset(MANIFEST, "train", transform=train_tf)
    val_ds   = SigLIPDrawingDataset(MANIFEST, "val",   transform=val_tf)
    test_ds  = SigLIPDrawingDataset(MANIFEST, "test",  transform=val_tf)
    print(f"[data] train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}")

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    sampler = make_sampler(train_labels, 4)
    cw = class_weights(train_labels, 4, DEVICE)
    print(f"[data] class_weights={cw.cpu().tolist()}")

    train_loader = DataLoader(train_ds, batch_size=BATCH, sampler=sampler, num_workers=NUM_WORKERS)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False,   num_workers=NUM_WORKERS)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH, shuffle=False,   num_workers=NUM_WORKERS)

    model = ClinicalFusionClassifier(num_classes=4).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=0.1)

    history: list[dict] = []

    # ── Phase 1: backbone frozen ──────────────────────────────────────────
    print("\n=== PHASE 1: backbone frozen ===")
    for p in model.image_backbone.parameters():
        p.requires_grad = False

    head_params = [p for p in model.parameters() if p.requires_grad]
    opt1 = AdamW(head_params, lr=PHASE1_LR, weight_decay=1e-3)
    sch1 = CosineAnnealingLR(opt1, T_max=PHASE1_EPOCHS)
    best_f1, best_epoch, best_state = train_phase(
        model, train_loader, val_loader, criterion, opt1, sch1,
        PHASE1_EPOCHS, PATIENCE, DEVICE, history, "P1"
    )

    # ── Phase 2: full fine-tune ───────────────────────────────────────────
    print("\n=== PHASE 2: full fine-tune ===")
    for p in model.image_backbone.parameters():
        p.requires_grad = True

    opt2 = AdamW([
        {"params": model.image_backbone.parameters(), "lr": PHASE2_LR * 0.1},
        {"params": model.image_proj.parameters(),     "lr": PHASE2_LR},
        {"params": model.clinical_mlp.parameters(),   "lr": PHASE2_LR},
        {"params": model.fusion.parameters(),         "lr": PHASE2_LR},
    ], weight_decay=1e-3)
    sch2 = CosineAnnealingLR(opt2, T_max=PHASE2_EPOCHS)
    f2, e2, state2 = train_phase(
        model, train_loader, val_loader, criterion, opt2, sch2,
        PHASE2_EPOCHS, PATIENCE, DEVICE, history, "P2"
    )
    if f2 > best_f1:
        best_f1, best_epoch, best_state = f2, e2, state2
        print(f"Phase 2 yeni best: val_macro_f1={best_f1:.4f}")

    # ── Save best checkpoint ──────────────────────────────────────────────
    if best_state is not None:
        model.load_state_dict(best_state)
    torch.save({"model_state": model.state_dict(), "val_macro_f1": best_f1}, OUT / "checkpoints" / "best.pt")
    print(f"\n[save] best.pt val_macro_f1={best_f1:.4f}")

    # ── Test evaluation ───────────────────────────────────────────────────
    print("\n=== TEST EVALUATION ===")
    _, tgts, preds = run_epoch(model, test_loader, criterion, None, DEVICE, train=False)
    acc  = accuracy_score(tgts, preds)
    prec = precision_score(tgts, preds, average="macro", zero_division=0)
    rec  = recall_score(tgts, preds, average="macro", zero_division=0)
    f1   = f1_score(tgts, preds, average="macro", zero_division=0)

    print(f"Test Accuracy : {acc:.4f}")
    print(f"Test Precision: {prec:.4f}")
    print(f"Test Recall   : {rec:.4f}")
    print(f"Test Macro F1 : {f1:.4f}")
    print()
    print(classification_report(tgts, preds, target_names=CLASSES, zero_division=0))

    test_results = {
        "accuracy": acc, "precision": prec, "recall": rec, "macro_f1": f1,
        "best_val_macro_f1": best_f1,
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "test_samples": len(test_ds),
    }

    (OUT / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    (OUT / "test_results.json").write_text(json.dumps(test_results, indent=2), encoding="utf-8")
    print(f"\nSonuclar: {OUT}/test_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
