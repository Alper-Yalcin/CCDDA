"""
build_and_train_labeled.py

labels_model.csv veya labels_ollama.csv'den manifest olusturup model egitir.
Val/test: labels CSV'deki "test" split'i (dataset orjinal test bolumu)

Kullanim:
  python build_and_train_labeled.py --source model   # model pseudo-labels
  python build_and_train_labeled.py --source ollama  # ollama labels
"""
from __future__ import annotations
import argparse, json, random, sys, time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from PIL import Image

from src.models.fusion_classifier import ClinicalFusionClassifier

CLASSES       = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES   = 4
SEED          = 42
BATCH         = 32
NUM_WORKERS   = 0
DEVICE        = "cuda" if torch.cuda.is_available() else "cpu"
MAX_EPOCHS    = 60
LR            = 6e-5
WEIGHT_DECAY  = 2e-4
PATIENCE      = 12
LABEL_SMOOTH  = 0.08
CONF_THRESH   = 0.65   # minimum guven esigi
MAX_PER_CLASS = 2000   # sinif basi maksimum
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]


class SimpleImageDataset(Dataset):
    def __init__(self, df, transform):
        self.df = df.reset_index(drop=True)
        self.tf = transform

    def __len__(self): return len(self.df)

    def __getitem__(self, i):
        row = self.df.iloc[i]
        try:
            img = Image.open(row["image_path"]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224), 128)
        return {
            "image": self.tf(img),
            "label": torch.tensor(int(row["label_id"]), dtype=torch.long),
            "clinical_features": torch.zeros(18),
            "clinical_validity": torch.zeros(18),
        }


def make_transforms():
    train_tf = transforms.Compose([
        transforms.Resize(256), transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.3), transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.3, hue=0.08),
        transforms.RandomGrayscale(p=0.10),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        transforms.RandomErasing(p=0.25, scale=(0.02, 0.20)),
    ])
    val_tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD),
    ])
    return train_tf, val_tf


def set_seed(s):
    random.seed(s); np.random.seed(s)
    torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def class_weights_tensor(labels, n):
    counts = np.bincount(labels, minlength=n).astype(np.float32)
    counts[counts == 0] = 1.0
    return torch.tensor(counts.sum() / (n * counts), dtype=torch.float32, device=DEVICE)


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
    return {"loss": total_loss/n,
            "acc": float(accuracy_score(tgts_all, preds_all)),
            "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)),
            }, tgts_all, preds_all


def build_train_val_test_df(labels_csv: Path, source_name: str):
    df = pd.read_csv(labels_csv)
    df = df[df["label"].notna()].copy()

    train_raw = df[df["split"] == "train"].copy()
    test_df   = df[df["split"] == "test"].copy()

    # Val: test setinin ilk yarisi (stratified)
    val_parts, test_parts = [], []
    for cls in CLASSES:
        cls_t = test_df[test_df["label"] == cls]
        half  = max(1, len(cls_t) // 2)
        val_parts.append(cls_t.iloc[:half])
        test_parts.append(cls_t.iloc[half:])
    val_df  = pd.concat(val_parts,  ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)

    # Train: conf filtresi + sinif basi cap
    if "confidence" in train_raw.columns:
        train_raw = train_raw[train_raw["confidence"] >= CONF_THRESH].copy()
    print(f"[{source_name}] Train guven>={CONF_THRESH}: {len(train_raw)}")
    print(f"  Sinif dagilimi: {dict(train_raw['label'].value_counts())}")

    parts = []
    for cls in CLASSES:
        cls_df = train_raw[train_raw["label"] == cls].copy()
        if "confidence" in cls_df.columns:
            cls_df = cls_df.sort_values("confidence", ascending=False)
        parts.append(cls_df.head(MAX_PER_CLASS))
    train_df = pd.concat(parts, ignore_index=True)
    print(f"  Dengeleme sonrasi: {len(train_df)}  {dict(train_df['label'].value_counts())}")
    print(f"  Val: {len(val_df)}  Test: {len(test_df)}")
    return train_df, val_df, test_df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["model", "ollama"], required=True)
    args = parser.parse_args()

    set_seed(SEED)
    labels_csv = Path(f"out/labels_{args.source}.csv")
    out_dir    = Path(f"out/{args.source}_labeled_run")

    if not labels_csv.exists():
        print(f"[hata] {labels_csv} bulunamadi!")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "checkpoints").mkdir(exist_ok=True)
    print(f"[init] device={DEVICE}  kaynak={args.source}")

    train_tf, val_tf = make_transforms()

    train_df, val_df, test_df = build_train_val_test_df(labels_csv, args.source)
    print(f"[data] train={len(train_df)}  val={len(val_df)}  test={len(test_df)}")

    train_ds = SimpleImageDataset(train_df, train_tf)
    val_ds   = SimpleImageDataset(val_df,   val_tf)
    test_ds  = SimpleImageDataset(test_df,  val_tf)

    train_labels = train_df["label_id"].astype(int).tolist()
    cw      = class_weights_tensor(train_labels, NUM_CLASSES)
    sampler = make_sampler(train_labels, NUM_CLASSES)
    print(f"[class_weights] {[round(x,3) for x in cw.tolist()]}")

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
    torch.save({"model_state": model.state_dict(), "val_macro_f1": best_f1, "classes": CLASSES,
                "source": args.source},
               out_dir / "checkpoints" / "best.pt")
    (out_dir / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")

    print(f"\n=== TEST ({len(test_ds)} ornek, Emotion test split) ===")
    _, tgts, preds = run_epoch(model, test_loader, criterion, None, False)
    acc  = accuracy_score(tgts, preds)
    prec = precision_score(tgts, preds, average="macro", zero_division=0)
    rec  = recall_score(tgts, preds, average="macro", zero_division=0)
    f1   = f1_score(tgts, preds, average="macro", zero_division=0)
    print(f"Accuracy: {acc:.4f}  Precision: {prec:.4f}  Recall: {rec:.4f}  F1: {f1:.4f}")
    print(classification_report(tgts, preds, target_names=CLASSES, zero_division=0))

    per_class_f1 = f1_score(tgts, preds, average=None, zero_division=0)
    results = {
        "source": args.source,
        "accuracy": float(acc), "precision": float(prec),
        "recall": float(rec), "macro_f1": float(f1),
        "per_class_f1": {CLASSES[i]: float(per_class_f1[i]) for i in range(NUM_CLASSES)},
        "best_val_macro_f1": float(best_f1),
        "train_samples": len(train_ds), "conf_thresh": CONF_THRESH,
    }
    (out_dir / "test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[save] {out_dir}/test_results.json")
    return 0

if __name__ == "__main__":
    sys.exit(main())
