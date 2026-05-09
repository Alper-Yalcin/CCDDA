"""
train_b3.py — EfficientNet-B3 ile final manifest egitimi

EfficientNet-B3: 7.8M parametre, 1536-dim cikis
Aynı manifest_final.csv, 2 fazlı egitim + MixUp

Cikti: out/b3_run/
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
from torchvision.models import EfficientNet_B3_Weights, efficientnet_b3

from src.data.dataset import SigLIPDrawingDataset

MANIFEST    = Path("out/manifest_final.csv")
OUT         = Path("out/b3_run")
CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES = 4
SEED        = 42
BATCH       = 24   # B3 daha buyuk -> kucuk batch
NUM_WORKERS = 0
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"

P1_EPOCHS   = 12
P1_LR       = 3e-4
P1_PATIENCE = 6

P2_EPOCHS   = 80
P2_LR       = 2e-5
P2_WD       = 2e-4
P2_PATIENCE = 18
LABEL_SMOOTH = 0.07
MIXUP_ALPHA  = 0.25

MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]


# ── EfficientNet-B3 Siniflandirici ─────────────────────────────────────────
class B3Classifier(nn.Module):
    def __init__(self, num_classes=4, pretrained=True):
        super().__init__()
        weights = EfficientNet_B3_Weights.IMAGENET1K_V1 if pretrained else None
        net = efficientnet_b3(weights=weights)
        self.features = net.features
        self.avgpool  = net.avgpool
        self.head = nn.Sequential(
            nn.Dropout(0.35),
            nn.Linear(1536, 512),
            nn.GELU(),
            nn.Dropout(0.20),
            nn.Linear(512, num_classes),
        )

    def forward(self, x, *_):   # *_ klinik argumanlari yoksayar (uyumluluk)
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.head(x)

    def freeze_backbone(self):
        for p in self.features.parameters():
            p.requires_grad = False

    def unfreeze_all(self):
        for p in self.parameters():
            p.requires_grad = True


# ── Yardimcilar ────────────────────────────────────────────────────────────
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


def mixup_batch(imgs, labels, alpha):
    if alpha <= 0:
        return imgs, labels, labels, 1.0
    lam = np.random.beta(alpha, alpha)
    idx = torch.randperm(imgs.size(0), device=imgs.device)
    return lam * imgs + (1 - lam) * imgs[idx], labels, labels[idx], lam


def make_transforms():
    train_tf = transforms.Compose([
        transforms.Resize(300),
        transforms.RandomCrop(280),
        transforms.RandomHorizontalFlip(p=0.35),
        transforms.RandomVerticalFlip(p=0.05),
        transforms.RandomRotation(25),
        transforms.ColorJitter(brightness=0.45, contrast=0.45, saturation=0.35, hue=0.10),
        transforms.RandomGrayscale(p=0.12),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
        transforms.RandomErasing(p=0.30, scale=(0.02, 0.25)),
    ])
    val_tf = transforms.Compose([
        transforms.Resize(300),
        transforms.CenterCrop(280),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    return train_tf, val_tf


def run_epoch(model, loader, criterion, optimizer, train: bool):
    model.train() if train else model.eval()
    total_loss, preds_all, tgts_all = 0.0, [], []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for batch in loader:
            img = batch["image"].to(DEVICE, non_blocking=True)
            clin  = batch["clinical_features"].to(DEVICE, non_blocking=True)
            valid = batch["clinical_validity"].to(DEVICE, non_blocking=True)
            y     = batch["label"].to(DEVICE, non_blocking=True)
            if train and MIXUP_ALPHA > 0:
                img, y_a, y_b, lam = mixup_batch(img, y, MIXUP_ALPHA)
                logits = model(img, clin, valid)
                loss = lam * criterion(logits, y_a) + (1 - lam) * criterion(logits, y_b)
                y_use = y_a
            else:
                logits = model(img, clin, valid)
                loss = criterion(logits, y)
                y_use = y
            if train:
                optimizer.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
            total_loss += loss.item() * y_use.size(0)
            preds_all.extend(logits.argmax(1).detach().cpu().tolist())
            tgts_all.extend(y_use.detach().cpu().tolist())
    n = max(len(tgts_all), 1)
    return {"loss": total_loss / n,
            "acc": float(accuracy_score(tgts_all, preds_all)),
            "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)),
            }, tgts_all, preds_all


def train_phase(model, train_ldr, val_ldr, criterion, optimizer, scheduler,
                max_ep, patience, name, t0):
    best_f1, best_state, bad = -1.0, None, 0
    history = []
    for ep in range(1, max_ep + 1):
        tr, _, _ = run_epoch(model, train_ldr, criterion, optimizer, True)
        va, _, _ = run_epoch(model, val_ldr,   criterion, None,      False)
        if scheduler: scheduler.step()
        elapsed = time.time() - t0
        history.append({"epoch": ep, "train": tr, "val": va})
        marker = ""
        if va["macro_f1"] > best_f1:
            best_f1    = va["macro_f1"]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            bad = 0; marker = " * BEST"
        else:
            bad += 1
        print(f"  [{name} {ep:02d}/{max_ep}] tr_f1={tr['macro_f1']:.4f}  "
              f"va_f1={va['macro_f1']:.4f}  ({elapsed:.0f}s){marker}")
        if bad >= patience:
            print(f"  [early stop] {name} epoch {ep}"); break
    return best_f1, best_state, history


def main():
    set_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checkpoints").mkdir(parents=True, exist_ok=True)
    print(f"[init] device={DEVICE}  EfficientNet-B3 (hedef: %70+)")

    train_tf, val_tf = make_transforms()
    train_ds = SigLIPDrawingDataset(MANIFEST, "train", train_tf)
    val_ds   = SigLIPDrawingDataset(MANIFEST, "val",   val_tf)
    test_ds  = SigLIPDrawingDataset(MANIFEST, "test",  val_tf)
    print(f"[data] train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")

    train_labels = train_ds.df["label_id"].astype(int).tolist()
    cw      = class_weights_tensor(train_labels, NUM_CLASSES)
    sampler = make_sampler(train_labels, NUM_CLASSES)
    print(f"[class_weights] {[round(x,3) for x in cw.tolist()]}")

    train_ldr = DataLoader(train_ds, batch_size=BATCH, sampler=sampler,
                           num_workers=NUM_WORKERS, pin_memory=True)
    val_ldr   = DataLoader(val_ds,   batch_size=BATCH, shuffle=False,
                           num_workers=NUM_WORKERS, pin_memory=True)
    test_ldr  = DataLoader(test_ds,  batch_size=BATCH, shuffle=False,
                           num_workers=NUM_WORKERS, pin_memory=True)

    model     = B3Classifier(num_classes=NUM_CLASSES, pretrained=True).to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=LABEL_SMOOTH)
    t0        = time.time()
    all_hist  = []

    n_total = sum(p.numel() for p in model.parameters())
    print(f"[model] B3Classifier  toplam parametre={n_total:,}")

    # Faz 1: Backbone dondur
    print(f"\n=== FAZ 1: Lineer Probe ===")
    model.freeze_backbone()
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  egitimde {n_train:,} parametre")
    opt1 = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=P1_LR, weight_decay=1e-4)
    sch1 = CosineAnnealingLR(opt1, T_max=P1_EPOCHS, eta_min=1e-5)
    f1_p1, state_p1, h1 = train_phase(model, train_ldr, val_ldr, criterion, opt1, sch1,
                                       P1_EPOCHS, P1_PATIENCE, "P1", t0)
    all_hist.extend(h1)
    print(f"[P1] best val_f1={f1_p1:.4f}")
    model.load_state_dict(state_p1)
    torch.save({"model_state": model.state_dict(), "val_macro_f1": f1_p1,
                "classes": CLASSES, "phase": "p1"},
               OUT / "checkpoints" / "best_p1.pt")

    # Faz 2: Tam fine-tune
    print(f"\n=== FAZ 2: Tam ince ayar ===")
    model.unfreeze_all()
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  egitimde {n_train:,} parametre")
    opt2 = AdamW(model.parameters(), lr=P2_LR, weight_decay=P2_WD)
    sch2 = CosineAnnealingLR(opt2, T_max=P2_EPOCHS, eta_min=5e-7)
    f1_p2, state_p2, h2 = train_phase(model, train_ldr, val_ldr, criterion, opt2, sch2,
                                       P2_EPOCHS, P2_PATIENCE, "P2", t0)
    all_hist.extend(h2)
    print(f"[P2] best val_f1={f1_p2:.4f}")

    best_f1    = max(f1_p1, f1_p2)
    best_state = state_p2 if f1_p2 >= f1_p1 else state_p1
    best_phase = "P2" if f1_p2 >= f1_p1 else "P1"
    model.load_state_dict(best_state)
    torch.save({"model_state": model.state_dict(), "val_macro_f1": best_f1,
                "classes": CLASSES, "best_phase": best_phase},
               OUT / "checkpoints" / "best.pt")
    (OUT / "train_history.json").write_text(json.dumps(all_hist, indent=2), encoding="utf-8")
    print(f"\n[best] {best_phase}  val_macro_f1={best_f1:.4f}")

    print("\n=== TEST (qwen 212) ===")
    _, tgts, preds = run_epoch(model, test_ldr, criterion, None, False)
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
        "best_val_macro_f1": float(best_f1), "best_phase": best_phase,
        "train_samples": len(train_ds), "val_samples": len(val_ds), "test_samples": len(test_ds),
    }
    (OUT / "test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[save] {OUT}/test_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
