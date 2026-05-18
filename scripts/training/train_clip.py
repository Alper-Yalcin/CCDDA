"""
train_clip.py

CLIP ViT-B/32 backbone ile 4-sinif duygu siniflandirmasi.

Phase 1 — Linear probe : Backbone dondurulmus, yalnizca head egitilir.
Phase 2 — Fine-tune    : Son 3 transformer blogu + head acilir.

Manifest : out/manifest_expanded.csv  (train/val)
Test     : out/manifest_qwen.csv      (212 ornek, karsilastirma icin sabit)

Cikti:
  out/clip_run/checkpoints/best.pt
  out/clip_run/train_history.json
  out/clip_run/test_results.json
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
from transformers import CLIPImageProcessor, CLIPVisionModel

import pandas as pd

# -- Config -------------------------------------------------------------------
TRAIN_MANIFEST = Path("out/manifest_expanded.csv")
TEST_MANIFEST  = Path("out/manifest_qwen.csv")
OUT            = Path("out/clip_run")
CLIP_MODEL     = "openai/clip-vit-base-patch32"
CLASSES        = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES    = 4
SEED           = 42
BATCH          = 32
NUM_WORKERS    = 0
DEVICE         = "cuda" if torch.cuda.is_available() else "cpu"

P1_LR          = 1e-3
P1_EPOCHS      = 20
P1_PATIENCE    = 8

P2_LR_HEAD     = 5e-5
P2_LR_BACK     = 5e-6
P2_EPOCHS      = 30
P2_PATIENCE    = 10

WD             = 1e-4
LABEL_SMOOTH   = 0.05


# -- Dataset ------------------------------------------------------------------
class DrawingDataset(Dataset):
    def __init__(self, manifest: Path, split: str, processor):
        df = pd.read_csv(manifest)
        self.df = df[df["split"] == split].reset_index(drop=True)
        if self.df.empty:
            raise ValueError(f"Split '{split}' bos")
        self.processor = processor

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img = Image.open(row["image_path"]).convert("RGB")
        inputs = self.processor(images=img, return_tensors="pt")
        pixel_values = inputs["pixel_values"].squeeze(0)
        return pixel_values, int(row["label_id"])


# -- Model --------------------------------------------------------------------
class CLIPClassifier(nn.Module):
    def __init__(self, num_classes: int = 4, dropout: float = 0.3):
        super().__init__()
        self.backbone = CLIPVisionModel.from_pretrained(CLIP_MODEL)
        hidden = self.backbone.config.hidden_size  # 768 for ViT-B/32
        self.head = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Dropout(dropout),
            nn.Linear(hidden, 256),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(256, num_classes),
        )

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        out = self.backbone(pixel_values=pixel_values)
        cls_feat = out.last_hidden_state[:, 0, :]  # [CLS] token
        return self.head(cls_feat)

    def freeze_backbone(self):
        for p in self.backbone.parameters():
            p.requires_grad = False

    def unfreeze_last_blocks(self, n: int = 3):
        # CLIP ViT-B/32: encoder.layers[-n:]
        layers = self.backbone.vision_model.encoder.layers
        for layer in layers[-n:]:
            for p in layer.parameters():
                p.requires_grad = True
        # also unfreeze post_layernorm
        for p in self.backbone.vision_model.post_layernorm.parameters():
            p.requires_grad = True


# -- Helpers ------------------------------------------------------------------
def set_seed(s):
    random.seed(s); np.random.seed(s)
    torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def make_sampler(labels, num_classes):
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    w = 1.0 / counts
    return WeightedRandomSampler([float(w[y]) for y in labels],
                                 num_samples=len(labels), replacement=True)


def class_weights(labels, num_classes):
    counts = np.bincount(labels, minlength=num_classes).astype(np.float32)
    counts[counts == 0] = 1.0
    inv = counts.sum() / (num_classes * counts)
    return torch.tensor(inv, dtype=torch.float32, device=DEVICE)


def run_epoch(model, loader, criterion, optimizer, train: bool):
    model.train() if train else model.eval()
    total_loss, preds_all, tgts_all = 0.0, [], []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for pixels, labels in loader:
            pixels = pixels.to(DEVICE)
            labels = labels.to(DEVICE)
            logits = model(pixels)
            loss = criterion(logits, labels)
            if train:
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += loss.item() * pixels.size(0)
            preds_all.extend(logits.argmax(1).cpu().tolist())
            tgts_all.extend(labels.cpu().tolist())
    n = max(len(tgts_all), 1)
    return {
        "loss":     total_loss / n,
        "acc":      float(accuracy_score(tgts_all, preds_all)),
        "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)),
    }, tgts_all, preds_all


def train_phase(label, model, train_loader, val_loader, criterion,
                optimizer, scheduler, epochs, patience, history):
    best_f1, best_state, bad = -1.0, None, 0
    t0 = time.time()
    for ep in range(1, epochs + 1):
        tr, _, _ = run_epoch(model, train_loader, criterion, optimizer, True)
        va, _, _ = run_epoch(model, val_loader,   criterion, None,      False)
        if scheduler:
            scheduler.step()
        elapsed = time.time() - t0
        history.append({"phase": label, "epoch": ep, "train": tr, "val": va})
        marker = ""
        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            bad = 0
            marker = " * BEST"
        else:
            bad += 1
        print(f"[{label} {ep:02d}/{epochs}] "
              f"tr_loss={tr['loss']:.4f} tr_f1={tr['macro_f1']:.4f}  "
              f"va_loss={va['loss']:.4f} va_f1={va['macro_f1']:.4f}  "
              f"({elapsed:.0f}s){marker}")
        if bad >= patience:
            print(f"    [early stop] patience={patience}")
            break
    return best_f1, best_state


# -- Main ---------------------------------------------------------------------
def main():
    set_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(parents=True, exist_ok=True)
    print(f"[init] device={DEVICE}  model={CLIP_MODEL}")

    processor = CLIPImageProcessor.from_pretrained(CLIP_MODEL)

    train_ds = DrawingDataset(TRAIN_MANIFEST, "train", processor)
    val_ds   = DrawingDataset(TRAIN_MANIFEST, "val",   processor)
    test_ds  = DrawingDataset(TEST_MANIFEST,  "test",  processor)
    print(f"[data] train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    cw = class_weights(train_labels, NUM_CLASSES)
    print(f"[data] class_weights={cw.cpu().tolist()}")

    sampler = make_sampler(train_labels, NUM_CLASSES)
    train_loader = DataLoader(train_ds, batch_size=BATCH, sampler=sampler, num_workers=NUM_WORKERS, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False,   num_workers=NUM_WORKERS, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH, shuffle=False,   num_workers=NUM_WORKERS, pin_memory=True)

    model = CLIPClassifier(NUM_CLASSES).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=LABEL_SMOOTH)
    history: list[dict] = []

    # Phase 1: Linear probe
    print("\n=== PHASE 1: Linear probe (backbone frozen) ===")
    model.freeze_backbone()
    head_params = [p for p in model.parameters() if p.requires_grad]
    print(f"    trainable: {sum(p.numel() for p in head_params):,} params")
    opt1 = AdamW(head_params, lr=P1_LR, weight_decay=WD)
    sch1 = CosineAnnealingLR(opt1, T_max=P1_EPOCHS, eta_min=1e-6)
    best_f1, best_state = train_phase(
        "P1", model, train_loader, val_loader, criterion,
        opt1, sch1, P1_EPOCHS, P1_PATIENCE, history)

    if best_state:
        model.load_state_dict(best_state)

    # Phase 2: Fine-tune last 3 blocks + head
    print("\n=== PHASE 2: Fine-tune last 3 transformer blocks + head ===")
    model.unfreeze_last_blocks(n=3)
    trainable = [p for p in model.parameters() if p.requires_grad]
    print(f"    trainable: {sum(p.numel() for p in trainable):,} params")

    back_params = [p for n, p in model.named_parameters()
                   if p.requires_grad and "head" not in n]
    head_params2 = [p for n, p in model.named_parameters()
                    if p.requires_grad and "head" in n]
    opt2 = AdamW([
        {"params": back_params,  "lr": P2_LR_BACK},
        {"params": head_params2, "lr": P2_LR_HEAD},
    ], weight_decay=WD)
    sch2 = CosineAnnealingLR(opt2, T_max=P2_EPOCHS, eta_min=1e-8)
    f2, state2 = train_phase(
        "P2", model, train_loader, val_loader, criterion,
        opt2, sch2, P2_EPOCHS, P2_PATIENCE, history)

    if f2 > best_f1:
        best_f1, best_state = f2, state2
        print(f"Phase 2 yeni best: val_macro_f1={best_f1:.4f}")

    # Save
    if best_state:
        model.load_state_dict(best_state)
    torch.save({"model_state": model.state_dict(), "val_macro_f1": best_f1,
                "classes": CLASSES, "backbone": CLIP_MODEL},
               OUT / "checkpoints" / "best.pt")
    (OUT / "train_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8")
    print(f"\n[save] best.pt  val_macro_f1={best_f1:.4f}")

    # Test
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
        "backbone":          CLIP_MODEL,
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
