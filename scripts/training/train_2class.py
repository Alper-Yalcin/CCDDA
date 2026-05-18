"""
train_2class.py — Dataset/Images/Emotion ile 2 sinifli model

Siniflar:
  Happiness -> label 0 (Pozitif)
  Sadness   -> label 1 (Negatif)

Egitim seti: Dataset/Images/Emotion/train/ (4614+4614=9228)
Val/Test: Emotion/test/ bolunmesi (816+816=1632) + qwen'den mutlu/uzgun

Cikti: out/twoclass_run/
"""
from __future__ import annotations
import json, random, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import (accuracy_score, classification_report,
                             f1_score, precision_score, recall_score)
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

IMAGE_ROOT  = Path("Dataset/Images/Emotion")
QWEN_MANIFEST = Path("out/manifest_qwen.csv")
OUT         = Path("out/twoclass_run")
CLASSES     = ["Positive", "Negative"]
NUM_CLASSES = 2
SEED        = 42
BATCH       = 32
NUM_WORKERS = 0
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
MAX_EPOCHS  = 60
LR          = 5e-5
WEIGHT_DECAY = 2e-4
PATIENCE    = 12
LABEL_SMOOTH = 0.06
IMG_EXTS    = {".jpg", ".jpeg", ".png", ".webp"}
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]

# Emotion klasoru: Happiness=0 (Positive), Sadness=1 (Negative)
LABEL_MAP = {"Happiness": 0, "Sadness": 1}

# qwen'den: Happy=0, (Sad+Angry+Fear)=1
QWEN_MAP = {0: 0, 1: 1, 2: 1, 3: 1}   # label_id -> 2-class id


class TwoClassDataset(Dataset):
    def __init__(self, records: list[dict], transform):
        self.records = records
        self.tf = transform

    def __len__(self): return len(self.records)

    def __getitem__(self, i):
        r = self.records[i]
        try:
            img = Image.open(r["path"]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224), 128)
        return {"image": self.tf(img),
                "label": torch.tensor(r["label"], dtype=torch.long)}


class SimpleEfficientNet(nn.Module):
    def __init__(self, num_classes=2, pretrained=True):
        super().__init__()
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        net = efficientnet_b0(weights=weights)
        self.features = net.features
        self.avgpool  = net.avgpool
        self.head = nn.Sequential(
            nn.Dropout(0.35),
            nn.Linear(1280, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.20),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.head(x)


def set_seed(s):
    random.seed(s); np.random.seed(s)
    torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def make_transforms():
    train_tf = transforms.Compose([
        transforms.Resize(256), transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.3), transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.3, hue=0.08),
        transforms.RandomGrayscale(p=0.10),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        transforms.RandomErasing(p=0.25),
    ])
    val_tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD),
    ])
    return train_tf, val_tf


def collect_emotion_records(split: str) -> list[dict]:
    records = []
    split_dir = IMAGE_ROOT / split
    if not split_dir.exists():
        return records
    for cls_dir in sorted(split_dir.iterdir()):
        if not cls_dir.is_dir() or cls_dir.name not in LABEL_MAP:
            continue
        lid = LABEL_MAP[cls_dir.name]
        for f in sorted(cls_dir.iterdir()):
            if f.suffix.lower() in IMG_EXTS:
                records.append({"path": str(f.resolve()), "label": lid, "source": "emotion"})
    return records


def collect_qwen_records(split: str) -> list[dict]:
    qwen = pd.read_csv(QWEN_MANIFEST)
    sub  = qwen[qwen["split"] == split]
    records = []
    for _, row in sub.iterrows():
        lid = QWEN_MAP.get(int(row["label_id"]), -1)
        if lid < 0:
            continue
        records.append({"path": str(row["image_path"]), "label": lid, "source": "qwen"})
    return records


def run_epoch(model, loader, criterion, optimizer, train: bool):
    model.train() if train else model.eval()
    total_loss, preds_all, tgts_all = 0.0, [], []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for batch in loader:
            img = batch["image"].to(DEVICE, non_blocking=True)
            y   = batch["label"].to(DEVICE, non_blocking=True)
            logits = model(img)
            loss = criterion(logits, y)
            if train:
                optimizer.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += loss.item() * y.size(0)
            preds_all.extend(logits.argmax(1).detach().cpu().tolist())
            tgts_all.extend(y.detach().cpu().tolist())
    n = max(len(tgts_all), 1)
    return {"loss": total_loss/n,
            "acc": float(accuracy_score(tgts_all, preds_all)),
            "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)),
            }, tgts_all, preds_all


def main():
    set_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(exist_ok=True)
    print(f"[init] device={DEVICE}  2-sinifli model (Positive/Negative)")

    train_tf, val_tf = make_transforms()

    # Train: Emotion/train (Happiness + Sadness -> binary)
    train_records = collect_emotion_records("train")
    # Stratified val/test split from Emotion/test (50% each per class)
    all_test = collect_emotion_records("test")
    val_records, test_records = [], []
    for lbl in range(NUM_CLASSES):
        cls_recs = [r for r in all_test if r["label"] == lbl]
        half = len(cls_recs) // 2
        val_records.extend(cls_recs[:half])
        test_records.extend(cls_recs[half:])

    print(f"[data] train={len(train_records)}  val={len(val_records)}  test={len(test_records)}")

    dist_train = {c: sum(1 for r in train_records if r["label"]==i) for i, c in enumerate(CLASSES)}
    dist_val   = {c: sum(1 for r in val_records   if r["label"]==i) for i, c in enumerate(CLASSES)}
    print(f"  train dist: {dist_train}")
    print(f"  val   dist: {dist_val}")

    train_ds = TwoClassDataset(train_records, train_tf)
    val_ds   = TwoClassDataset(val_records,   val_tf)
    test_ds  = TwoClassDataset(test_records,  val_tf)

    train_labels = [r["label"] for r in train_records]
    counts = np.bincount(train_labels, minlength=NUM_CLASSES).astype(np.float32)
    cw = torch.tensor(counts.sum() / (NUM_CLASSES * counts), dtype=torch.float32, device=DEVICE)
    w_per_sample = [1.0 / counts[y] for y in train_labels]
    sampler = WeightedRandomSampler(w_per_sample, num_samples=len(train_labels), replacement=True)
    print(f"[class_weights] {[round(x,3) for x in cw.tolist()]}")

    train_loader = DataLoader(train_ds, batch_size=BATCH, sampler=sampler,
                              num_workers=NUM_WORKERS, pin_memory=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=True)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH, shuffle=False,
                              num_workers=NUM_WORKERS, pin_memory=True)

    model     = SimpleEfficientNet(num_classes=NUM_CLASSES, pretrained=True).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=LABEL_SMOOTH)
    optimizer = AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = CosineAnnealingLR(optimizer, T_max=MAX_EPOCHS, eta_min=5e-7)

    best_f1, best_state, bad_count = -1.0, None, 0
    history = []
    t0 = time.time()
    print(f"\n[train] max_epochs={MAX_EPOCHS}  patience={PATIENCE}")

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
            bad_count = 0; marker = " * BEST"
        else:
            bad_count += 1
        print(f"[{ep:02d}/{MAX_EPOCHS}] tr_f1={tr['macro_f1']:.4f}  "
              f"va_f1={va['macro_f1']:.4f}  ({elapsed:.0f}s){marker}")
        if bad_count >= PATIENCE:
            print(f"[early stop] epoch {ep}"); break

    model.load_state_dict(best_state)
    torch.save({"model_state": model.state_dict(), "val_macro_f1": best_f1,
                "classes": CLASSES, "num_classes": NUM_CLASSES},
               OUT / "checkpoints" / "best.pt")
    (OUT / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(f"\n[save] val_macro_f1={best_f1:.4f}")

    print(f"\n=== TEST ({len(test_ds)} ornek, Emotion/test 2. yarisi) ===")
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
