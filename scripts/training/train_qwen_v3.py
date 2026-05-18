"""
dataset_qwen_selected — 4-sinif duygu siniflandirmasi (v3)

Strateji (kucuk veri seti icin kanitlanmis transfere ogrenme):
  Phase 1 — Linear probe : Backbone tamamen dondurulmus, yalnizca head egitilir.
  Phase 2 — Fine-tune    : Son 2 MBConv blogu + head, cok dusuk LR ile acilir.

Cikti:
  out/qwen_v3/checkpoints/best.pt
  out/qwen_v3/test_results.json
  out/qwen_v3/train_history.json
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
from PIL import Image
from sklearn.metrics import (
    accuracy_score, classification_report,
    f1_score, precision_score, recall_score,
)
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
MANIFEST    = Path("out/manifest_qwen.csv")
OUT         = Path("out/qwen_v3")
CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES = 4
SEED        = 42
BATCH       = 32
NUM_WORKERS = 0
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"

P1_LR       = 1e-2   # head only, backbone frozen
P1_EPOCHS   = 25
P1_PATIENCE = 10

P2_LR_HEAD  = 5e-4   # head
P2_LR_BACK  = 1e-5   # backbone last blocks
P2_EPOCHS   = 35
P2_PATIENCE = 12

WD          = 5e-4
LABEL_SMOOTH = 0.08


# ── Dataset ───────────────────────────────────────────────────────────────────
class DrawingDataset(Dataset):
    def __init__(self, manifest_csv: Path, split: str, transform=None):
        df = pd.read_csv(manifest_csv)
        df = df[df["split"] == split].reset_index(drop=True)
        if df.empty:
            raise ValueError(f"'{split}' split bos")
        self.df = df
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img = Image.open(row["image_path"]).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, int(row["label_id"])


# ── Transforms ────────────────────────────────────────────────────────────────
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]

def train_tf():
    return transforms.Compose([
        transforms.Resize(256),
        transforms.RandomCrop(224),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.15, hue=0.05),
        transforms.RandomGrayscale(p=0.08),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
        transforms.RandomErasing(p=0.15, scale=(0.02, 0.12), ratio=(0.3, 3.3)),
    ])

def val_tf():
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])


# ── Model ─────────────────────────────────────────────────────────────────────
def build_model():
    net = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
    in_features = net.classifier[1].in_features   # 1280
    net.classifier = nn.Sequential(
        nn.Dropout(p=0.4),
        nn.Linear(in_features, NUM_CLASSES),
    )
    return net


def freeze_backbone(model):
    for name, p in model.named_parameters():
        if "classifier" not in name:
            p.requires_grad = False


def unfreeze_top_blocks(model, n_blocks: int = 2):
    """Son n_blocks MBConv (features[-n_blocks:]) + BN + head acilir."""
    for name, p in model.named_parameters():
        # features.7 ve features.8 son iki bloktur
        if "classifier" in name:
            p.requires_grad = True
        elif any(f"features.{8 - i}" in name for i in range(n_blocks)):
            p.requires_grad = True


# ── Sampler / loss weights ────────────────────────────────────────────────────
def make_sampler(labels: list[int]) -> WeightedRandomSampler:
    counts = np.bincount(labels, minlength=NUM_CLASSES).astype(np.float32)
    counts[counts == 0] = 1.0
    w = 1.0 / counts
    return WeightedRandomSampler([float(w[y]) for y in labels],
                                 num_samples=len(labels), replacement=True)


def class_weights_tensor(labels: list[int]) -> torch.Tensor:
    counts = np.bincount(labels, minlength=NUM_CLASSES).astype(np.float32)
    counts[counts == 0] = 1.0
    inv = counts.sum() / (NUM_CLASSES * counts)
    return torch.tensor(inv, dtype=torch.float32, device=DEVICE)


# ── Mixup ─────────────────────────────────────────────────────────────────────
def mixup_batch(imgs, labels, alpha=0.3):
    if alpha <= 0:
        return imgs, labels, labels, 1.0
    lam = np.random.beta(alpha, alpha)
    batch = imgs.size(0)
    idx = torch.randperm(batch, device=imgs.device)
    mixed = lam * imgs + (1 - lam) * imgs[idx]
    return mixed, labels, labels[idx], lam


# ── Epoch loop ────────────────────────────────────────────────────────────────
def run_epoch(model, loader, criterion, optimizer, train: bool, use_mixup: bool = False):
    model.train() if train else model.eval()
    total_loss = 0.0
    preds_all, tgts_all = [], []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for imgs, labels in loader:
            imgs, labels = imgs.to(DEVICE), labels.to(DEVICE)
            if train and use_mixup:
                imgs, y_a, y_b, lam = mixup_batch(imgs, labels, alpha=0.3)
                logits = model(imgs)
                loss = lam * criterion(logits, y_a) + (1 - lam) * criterion(logits, y_b)
            else:
                logits = model(imgs)
                loss = criterion(logits, labels)
            if train:
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += loss.item() * imgs.size(0)
            preds_all.extend(logits.argmax(1).cpu().tolist())
            tgts_all.extend(labels.cpu().tolist())
    n = max(len(tgts_all), 1)
    return {
        "loss": total_loss / n,
        "acc": float(accuracy_score(tgts_all, preds_all)),
        "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)),
    }, tgts_all, preds_all


# ── Phase loop ────────────────────────────────────────────────────────────────
def train_phase(label, model, train_loader, val_loader, criterion,
                optimizer, scheduler, epochs, patience, use_mixup, history):
    best_f1, best_state, bad = -1.0, None, 0
    t0 = time.time()
    for ep in range(1, epochs + 1):
        tr, _, _ = run_epoch(model, train_loader, criterion, optimizer, True, use_mixup)
        va, _, _ = run_epoch(model, val_loader, criterion, None, False)
        if scheduler:
            scheduler.step()
        elapsed = time.time() - t0
        history.append({"phase": label, "epoch": ep, "train": tr, "val": va})
        print(f"[{label} {ep:02d}/{epochs}] "
              f"tr_loss={tr['loss']:.4f} tr_f1={tr['macro_f1']:.4f}  "
              f"va_loss={va['loss']:.4f} va_f1={va['macro_f1']:.4f}  ({elapsed:.0f}s)")
        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            bad = 0
            print(f"    [BEST] val_macro_f1={best_f1:.4f}")
        else:
            bad += 1
            if bad >= patience:
                print(f"    [early stop] patience={patience}")
                break
    return best_f1, best_state


# ── Main ──────────────────────────────────────────────────────────────────────
def set_seed(s):
    random.seed(s); np.random.seed(s)
    torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def main():
    set_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(parents=True, exist_ok=True)
    print(f"[init] device={DEVICE}  seed={SEED}")

    train_ds = DrawingDataset(MANIFEST, "train", train_tf())
    val_ds   = DrawingDataset(MANIFEST, "val",   val_tf())
    test_ds  = DrawingDataset(MANIFEST, "test",  val_tf())
    print(f"[data] train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    cw  = class_weights_tensor(train_labels)
    print(f"[data] class_weights={cw.cpu().tolist()}")

    sampler = make_sampler(train_labels)
    train_loader = DataLoader(train_ds, batch_size=BATCH, sampler=sampler, num_workers=NUM_WORKERS)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False,   num_workers=NUM_WORKERS)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH, shuffle=False,   num_workers=NUM_WORKERS)

    model = build_model().to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=LABEL_SMOOTH)
    history: list[dict] = []

    # ── Phase 1: Linear probe (backbone frozen) ───────────────────────────────
    print("\n=== PHASE 1: Linear probe (backbone frozen) ===")
    freeze_backbone(model)
    head_params = [p for p in model.parameters() if p.requires_grad]
    print(f"    trainable params: {sum(p.numel() for p in head_params):,}")
    opt1 = AdamW(head_params, lr=P1_LR, weight_decay=WD)
    sch1 = CosineAnnealingLR(opt1, T_max=P1_EPOCHS, eta_min=1e-5)
    best_f1, best_state = train_phase(
        "P1", model, train_loader, val_loader, criterion,
        opt1, sch1, P1_EPOCHS, P1_PATIENCE, use_mixup=False, history=history
    )

    # restore best before phase 2
    if best_state:
        model.load_state_dict(best_state)

    # ── Phase 2: Fine-tune last 2 blocks + head ───────────────────────────────
    print("\n=== PHASE 2: Fine-tune top-2 blocks + head ===")
    unfreeze_top_blocks(model, n_blocks=2)
    trainable = [p for p in model.parameters() if p.requires_grad]
    print(f"    trainable params: {sum(p.numel() for p in trainable):,}")

    backbone_params = [p for n, p in model.named_parameters()
                       if p.requires_grad and "classifier" not in n]
    head_params2    = [p for n, p in model.named_parameters()
                       if p.requires_grad and "classifier" in n]
    opt2 = AdamW([
        {"params": backbone_params, "lr": P2_LR_BACK},
        {"params": head_params2,    "lr": P2_LR_HEAD},
    ], weight_decay=WD)
    sch2 = CosineAnnealingLR(opt2, T_max=P2_EPOCHS, eta_min=1e-7)
    f2, state2 = train_phase(
        "P2", model, train_loader, val_loader, criterion,
        opt2, sch2, P2_EPOCHS, P2_PATIENCE, use_mixup=True, history=history
    )
    if f2 > best_f1:
        best_f1, best_state = f2, state2
        print(f"Phase 2 yeni best: val_macro_f1={best_f1:.4f}")

    # ── Save ──────────────────────────────────────────────────────────────────
    if best_state:
        model.load_state_dict(best_state)
    torch.save({"model_state": model.state_dict(), "val_macro_f1": best_f1,
                "classes": CLASSES}, OUT / "checkpoints" / "best.pt")
    (OUT / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"\n[save] best.pt  val_macro_f1={best_f1:.4f}")

    # ── Test evaluation ───────────────────────────────────────────────────────
    print("\n=== TEST SET EVALUATION ===")
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
    report = classification_report(tgts, preds, target_names=CLASSES, zero_division=0)
    print(report)

    # per-class f1
    per_class_f1 = f1_score(tgts, preds, average=None, zero_division=0)
    per_class = {CLASSES[i]: float(per_class_f1[i]) for i in range(NUM_CLASSES)}

    results = {
        "accuracy": acc, "precision": prec, "recall": rec, "macro_f1": f1,
        "per_class_f1": per_class,
        "best_val_macro_f1": best_f1,
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "test_samples": len(test_ds),
    }
    (OUT / "test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Sonuclar kaydedildi: {OUT}/test_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
