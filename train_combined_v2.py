"""
train_combined_v2.py — Gercek etiket + Pseudo etiket birlesik egitim

Kaynaklar:
  - Gercek: Dataset/data/ (702, Angry/Fear/Happy/Sad)
  - Gercek: Dataset/NewArts2/NewArts2/ (407, Angry/Fear/Happy/Sad)
  - Pseudo: out/labels_model_v2.csv (model-labeled v2 teacher ile Emotion)

Val/Test: SADECE gercek etiketli veri (data + NewArts2)
Train: pseudo + gercek (70% split)

Cikti: out/combined_v2_run/
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
from sklearn.model_selection import train_test_split
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

PSEUDO_CSV   = Path("out/labels_model_v2.csv")
REAL_DIRS    = [Path("Dataset/data"), Path("Dataset/NewArts2/NewArts2")]
OUT          = Path("out/combined_v2_run")
CLASSES      = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES  = 4
SEED         = 42
BATCH        = 32
NUM_WORKERS  = 0
DEVICE       = "cuda" if torch.cuda.is_available() else "cpu"
MAX_EPOCHS   = 80
LR           = 4e-5
WEIGHT_DECAY = 2e-4
PATIENCE     = 15
LABEL_SMOOTH = 0.07
CONF_THRESH  = 0.65
MAX_PER_CLASS_PSEUDO = 2500
IMG_EXTS     = {".jpg", ".jpeg", ".png", ".webp"}
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]
LABEL_MAP = {"Happy": 0, "Sad": 1, "Angry": 2, "Fear": 3}


class ImgDataset(Dataset):
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
    def __init__(self, num_classes=4, pretrained=True):
        super().__init__()
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        net = efficientnet_b0(weights=weights)
        self.features = net.features
        self.avgpool  = net.avgpool
        self.head = nn.Sequential(
            nn.Dropout(0.40),
            nn.Linear(1280, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.15),
            nn.Linear(128, num_classes),
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
        transforms.RandomHorizontalFlip(p=0.4),
        transforms.RandomRotation(25),
        transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.3, hue=0.08),
        transforms.RandomGrayscale(p=0.10),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        transforms.RandomErasing(p=0.20),
    ])
    val_tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD),
    ])
    return train_tf, val_tf


def load_real_records() -> list[dict]:
    records = []
    for base in REAL_DIRS:
        if not base.exists():
            print(f"  [uyari] {base} bulunamadi")
            continue
        for cls_dir in sorted(base.iterdir()):
            if not cls_dir.is_dir():
                continue
            cls_name = cls_dir.name
            if cls_name not in LABEL_MAP:
                continue
            lid = LABEL_MAP[cls_name]
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    records.append({"path": str(f.resolve()),
                                    "label": lid, "source": "real"})
    return records


def load_pseudo_records() -> list[dict]:
    if not PSEUDO_CSV.exists():
        print(f"[hata] {PSEUDO_CSV} bulunamadi — once label_with_model_v2.py calistirin")
        return []
    df = pd.read_csv(PSEUDO_CSV)
    df = df[df["label"].notna() & (df["confidence"] >= CONF_THRESH)].copy()
    parts = []
    for cls in CLASSES:
        cls_df = df[df["label"] == cls].sort_values("confidence", ascending=False)
        parts.append(cls_df.head(MAX_PER_CLASS_PSEUDO))
    df_filt = pd.concat(parts, ignore_index=True)
    records = []
    for _, row in df_filt.iterrows():
        lid = LABEL_MAP.get(str(row["label"]), -1)
        if lid < 0:
            continue
        records.append({"path": str(row["image_path"]),
                        "label": lid, "source": "pseudo"})
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
            loss   = criterion(logits, y)
            if train:
                optimizer.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += loss.item() * y.size(0)
            preds_all.extend(logits.argmax(1).detach().cpu().tolist())
            tgts_all.extend(y.detach().cpu().tolist())
    n = max(len(tgts_all), 1)
    return {"loss": total_loss / n,
            "acc": float(accuracy_score(tgts_all, preds_all)),
            "macro_f1": float(f1_score(tgts_all, preds_all,
                                       average="macro", zero_division=0))
            }, tgts_all, preds_all


def main():
    set_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(exist_ok=True)
    print(f"[init] device={DEVICE}")

    # --- Gercek etiketli veri ---
    real_records = load_real_records()
    print(f"[real] {len(real_records)} gercek etiketli goruntu")
    dist_real = {c: sum(1 for r in real_records if r["label"] == i)
                 for i, c in enumerate(CLASSES)}
    print(f"  Dagilim: {dist_real}")

    # Train/val/test split (70/15/15) — sadece gercek etiketli
    labels_real = [r["label"] for r in real_records]
    train_real_idx, valtest_idx = train_test_split(
        range(len(real_records)), test_size=0.30, random_state=SEED,
        stratify=labels_real)
    valtest_labels = [labels_real[i] for i in valtest_idx]
    val_idx, test_idx = train_test_split(
        list(valtest_idx), test_size=0.50, random_state=SEED,
        stratify=valtest_labels)

    real_train = [real_records[i] for i in train_real_idx]
    val_records  = [real_records[i] for i in val_idx]
    test_records = [real_records[i] for i in test_idx]

    # --- Pseudo etiketli veri (sadece train icin) ---
    pseudo_records = load_pseudo_records()
    print(f"[pseudo] {len(pseudo_records)} pseudo etiketli goruntu (conf>={CONF_THRESH})")
    dist_pseudo = {c: sum(1 for r in pseudo_records if r["label"] == i)
                   for i, c in enumerate(CLASSES)}
    print(f"  Dagilim: {dist_pseudo}")

    train_records = real_train + pseudo_records
    random.shuffle(train_records)

    print(f"\n[data] train={len(train_records)}  val={len(val_records)}  test={len(test_records)}")
    print(f"  train real={len(real_train)} pseudo={len(pseudo_records)}")
    dist_val  = {c: sum(1 for r in val_records  if r["label"] == i) for i, c in enumerate(CLASSES)}
    dist_test = {c: sum(1 for r in test_records if r["label"] == i) for i, c in enumerate(CLASSES)}
    print(f"  val dist:  {dist_val}")
    print(f"  test dist: {dist_test}")

    train_tf, val_tf = make_transforms()
    train_ds = ImgDataset(train_records, train_tf)
    val_ds   = ImgDataset(val_records,   val_tf)
    test_ds  = ImgDataset(test_records,  val_tf)

    # Sinif agirliklar
    train_labels = [r["label"] for r in train_records]
    counts = np.bincount(train_labels, minlength=NUM_CLASSES).astype(np.float32)
    cw = torch.tensor(counts.sum() / (NUM_CLASSES * counts), dtype=torch.float32, device=DEVICE)
    w_per_sample = [1.0 / counts[y] for y in train_labels]
    sampler = WeightedRandomSampler(w_per_sample, num_samples=len(train_labels), replacement=True)
    print(f"[class_weights] {[round(x, 3) for x in cw.tolist()]}")

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
    print(f"\n[train] max_epochs={MAX_EPOCHS}  patience={PATIENCE}\n")

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
    (OUT / "train_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8")
    print(f"\n[save] val_macro_f1={best_f1:.4f}")

    print(f"\n=== TEST ({len(test_ds)} ornek, GERCEK ETIKETLI) ===")
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
        "train_samples": len(train_ds), "val_samples": len(val_ds),
        "test_samples": len(test_ds),
        "real_train": len(real_train), "pseudo_train": len(pseudo_records),
    }
    (OUT / "test_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print(f"[save] {OUT}/test_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
