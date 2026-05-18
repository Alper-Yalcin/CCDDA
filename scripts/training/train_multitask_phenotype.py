"""
Multi-task emotion + phenotype training.

Primary metric remains emotion accuracy / macro F1. Phenotype cluster prediction
is used only as an auxiliary task:

  total_loss = loss_emotion + alpha * loss_phenotype

Default manifest/features are produced by tools/cluster_phenotypes.py.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms

from src.features.feature_spec import FEATURE_NAMES, NUM_FEATURES
from src.models.efficientnet_backbone import EfficientNetBackbone

ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "out" / "phenotype_pipeline" / "manifest_multitask.csv"
DEFAULT_FEATURES = ROOT / "out" / "phenotype_pipeline" / "features_clean.csv"
DEFAULT_OUT = ROOT / "out" / "phenotype_pipeline" / "multitask_run"

CLASSES = ["Happy", "Sad", "Angry", "Fear"]
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
SEED = 42


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True


def make_transforms():
    train_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.RandomCrop(224),
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
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    return train_tf, val_tf


class MultiTaskDrawingDataset(Dataset):
    def __init__(self, manifest_csv: Path, split: str, transform, features_csv: Path | None = None) -> None:
        df = pd.read_csv(manifest_csv)
        df = df[df["split"] == split].reset_index(drop=True)
        if df.empty:
            raise ValueError(f"Empty split: {split}")
        if "phenotype_cluster" not in df.columns:
            raise ValueError("manifest must include phenotype_cluster")
        self.df = df
        self.transform = transform
        self.feature_lookup = None
        if features_csv is not None and features_csv.exists():
            self.feature_lookup = pd.read_csv(features_csv).set_index("sample_id")
            self.feature_lookup = self.feature_lookup[~self.feature_lookup.index.duplicated(keep="first")]

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict:
        row = self.df.iloc[idx]
        sample_id = str(row["sample_id"])
        try:
            img = Image.open(row["image_path"]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224), 255)
        image = self.transform(img)

        clinical = np.zeros(NUM_FEATURES, dtype=np.float32)
        validity = np.zeros(NUM_FEATURES, dtype=np.float32)
        if self.feature_lookup is not None and sample_id in self.feature_lookup.index:
            feat_row = self.feature_lookup.loc[sample_id]
            for i, name in enumerate(FEATURE_NAMES):
                v = feat_row.get(name)
                vflag = feat_row.get(f"{name}_valid")
                if v is not None and pd.notna(v) and vflag is not None and int(vflag) == 1:
                    clinical[i] = float(v)
                    validity[i] = 1.0

        return {
            "image": image,
            "clinical_features": torch.from_numpy(clinical),
            "clinical_validity": torch.from_numpy(validity),
            "emotion": torch.tensor(int(row["label_id"]), dtype=torch.long),
            "phenotype": torch.tensor(int(row["phenotype_cluster"]), dtype=torch.long),
            "sample_id": sample_id,
        }


class MultiTaskClinicalFusionClassifier(nn.Module):
    def __init__(
        self,
        num_emotions: int,
        num_phenotypes: int,
        feat_dim: int = NUM_FEATURES,
        image_proj_dim: int = 256,
        clinical_dim: int = 64,
        shared_dim: int = 128,
        pretrained: bool = True,
    ) -> None:
        super().__init__()
        self.image_backbone = EfficientNetBackbone(pretrained=pretrained)
        self.image_proj = nn.Sequential(
            nn.Linear(EfficientNetBackbone.OUT_DIM, image_proj_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
        )
        self.clinical_mlp = nn.Sequential(
            nn.Linear(feat_dim * 2, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, clinical_dim),
            nn.ReLU(inplace=True),
        )
        self.shared = nn.Sequential(
            nn.Linear(image_proj_dim + clinical_dim, shared_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
        )
        self.emotion_head = nn.Linear(shared_dim, num_emotions)
        self.phenotype_head = nn.Linear(shared_dim, num_phenotypes)

    def forward(self, image: torch.Tensor, clinical: torch.Tensor, validity: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        img_feat = self.image_proj(self.image_backbone(image))
        clin_feat = self.clinical_mlp(torch.cat([clinical, validity], dim=-1))
        shared = self.shared(torch.cat([img_feat, clin_feat], dim=-1))
        return self.emotion_head(shared), self.phenotype_head(shared)


def freeze_backbone(model: nn.Module) -> None:
    for name, p in model.named_parameters():
        if "image_backbone" in name:
            p.requires_grad = False
    print(f"[freeze] trainable={sum(p.numel() for p in model.parameters() if p.requires_grad):,}")


def unfreeze_all(model: nn.Module) -> None:
    for p in model.parameters():
        p.requires_grad = True
    print(f"[unfreeze] trainable={sum(p.numel() for p in model.parameters() if p.requires_grad):,}")


def class_weights(labels: list[int], n: int, device: str) -> torch.Tensor:
    counts = np.bincount(labels, minlength=n).astype(np.float32)
    counts[counts == 0] = 1.0
    return torch.tensor(counts.sum() / (n * counts), dtype=torch.float32, device=device)


def make_sampler(labels: list[int], n: int) -> WeightedRandomSampler:
    counts = np.bincount(labels, minlength=n).astype(np.float32)
    counts[counts == 0] = 1.0
    w = 1.0 / counts
    return WeightedRandomSampler([float(w[y]) for y in labels], len(labels), replacement=True)


def metrics(y_true: list[int], y_pred: list[int]) -> dict:
    return {
        "acc": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
    }


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    emotion_criterion,
    phenotype_criterion,
    optimizer,
    scaler,
    device: str,
    alpha: float,
    train: bool,
) -> tuple[dict, list[int], list[int], list[int], list[int]]:
    model.train() if train else model.eval()
    total_loss = 0.0
    emotion_true: list[int] = []
    emotion_pred: list[int] = []
    phenotype_true: list[int] = []
    phenotype_pred: list[int] = []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for batch in loader:
            img = batch["image"].to(device, non_blocking=True)
            clin = batch["clinical_features"].to(device, non_blocking=True)
            valid = batch["clinical_validity"].to(device, non_blocking=True)
            y_em = batch["emotion"].to(device, non_blocking=True)
            y_ph = batch["phenotype"].to(device, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=(device == "cuda")):
                em_logits, ph_logits = model(img, clin, valid)
                loss_em = emotion_criterion(em_logits, y_em)
                loss_ph = phenotype_criterion(ph_logits, y_ph)
                loss = loss_em + alpha * loss_ph
            if train:
                optimizer.zero_grad(set_to_none=True)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()

            total_loss += float(loss.item()) * y_em.size(0)
            emotion_true.extend(y_em.detach().cpu().tolist())
            phenotype_true.extend(y_ph.detach().cpu().tolist())
            emotion_pred.extend(em_logits.argmax(1).detach().cpu().tolist())
            phenotype_pred.extend(ph_logits.argmax(1).detach().cpu().tolist())

    n = max(len(emotion_true), 1)
    em_m = metrics(emotion_true, emotion_pred)
    ph_m = metrics(phenotype_true, phenotype_pred)
    return (
        {
            "loss": total_loss / n,
            "emotion_acc": em_m["acc"],
            "emotion_macro_f1": em_m["macro_f1"],
            "phenotype_acc": ph_m["acc"],
            "phenotype_macro_f1": ph_m["macro_f1"],
        },
        emotion_true,
        emotion_pred,
        phenotype_true,
        phenotype_pred,
    )


def train(args) -> int:
    set_seed(SEED)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "checkpoints").mkdir(exist_ok=True)
    device = args.device

    train_tf, val_tf = make_transforms()
    train_ds = MultiTaskDrawingDataset(args.manifest, "train", train_tf, args.features)
    val_ds = MultiTaskDrawingDataset(args.manifest, "val", val_tf, args.features)
    test_ds = MultiTaskDrawingDataset(args.manifest, "test", val_tf, args.features)

    num_emotions = int(max(train_ds.df["label_id"].max(), val_ds.df["label_id"].max(), test_ds.df["label_id"].max()) + 1)
    num_phenotypes = int(max(train_ds.df["phenotype_cluster"].max(), val_ds.df["phenotype_cluster"].max(), test_ds.df["phenotype_cluster"].max()) + 1)
    print(f"[init] device={device} alpha={args.alpha} emotions={num_emotions} phenotypes={num_phenotypes}")
    print(f"[data] train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}")
    print(f"[data] train emotion dist={train_ds.df['label'].value_counts().to_dict()}")
    print(f"[data] train phenotype dist={train_ds.df['phenotype_cluster'].value_counts().sort_index().to_dict()}")

    em_labels = train_ds.df["label_id"].astype(int).tolist()
    ph_labels = train_ds.df["phenotype_cluster"].astype(int).tolist()
    em_weights = class_weights(em_labels, num_emotions, device)
    ph_weights = class_weights(ph_labels, num_phenotypes, device)
    sampler = make_sampler(em_labels, num_emotions)
    print(f"[weights] emotion={[round(x, 3) for x in em_weights.detach().cpu().tolist()]}")
    print(f"[weights] phenotype={[round(x, 3) for x in ph_weights.detach().cpu().tolist()]}")

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, num_workers=args.num_workers, pin_memory=(device == "cuda"))
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, pin_memory=(device == "cuda"))
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, pin_memory=(device == "cuda"))

    model = MultiTaskClinicalFusionClassifier(num_emotions, num_phenotypes, pretrained=True).to(device)
    emotion_criterion = nn.CrossEntropyLoss(weight=em_weights, label_smoothing=args.label_smoothing)
    phenotype_criterion = nn.CrossEntropyLoss(weight=ph_weights, label_smoothing=0.03)
    scaler = torch.amp.GradScaler("cuda", enabled=(device == "cuda"))

    history: list[dict] = []
    best_f1 = -1.0
    best_state = None
    best_phase = ""
    t0 = time.time()

    phases = [
        ("p1", args.p1_epochs, args.p1_patience, args.p1_lr, 1e-4, True),
        ("p2", args.p2_epochs, args.p2_patience, args.p2_lr, args.weight_decay, False),
    ]
    for phase, max_epochs, patience, lr, wd, freeze in phases:
        freeze_backbone(model) if freeze else unfreeze_all(model)
        optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=wd)
        scheduler = CosineAnnealingLR(optimizer, T_max=max_epochs, eta_min=5e-7)
        bad = 0
        print(f"[phase] {phase} epochs={max_epochs} lr={lr}")
        for ep in range(1, max_epochs + 1):
            tr, *_ = run_epoch(model, train_loader, emotion_criterion, phenotype_criterion, optimizer, scaler, device, args.alpha, True)
            va, *_ = run_epoch(model, val_loader, emotion_criterion, phenotype_criterion, None, scaler, device, args.alpha, False)
            scheduler.step()
            rec = {"phase": phase, "epoch": ep, "train": tr, "val": va}
            history.append(rec)
            marker = ""
            if va["emotion_macro_f1"] > best_f1:
                best_f1 = va["emotion_macro_f1"]
                best_phase = phase
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                torch.save(
                    {
                        "model_state": model.state_dict(),
                        "classes": CLASSES[:num_emotions],
                        "num_phenotypes": num_phenotypes,
                        "val_emotion_macro_f1": best_f1,
                        "best_phase": best_phase,
                        "alpha": args.alpha,
                    },
                    out_dir / "checkpoints" / "best.pt",
                )
                bad = 0
                marker = " * BEST"
            else:
                bad += 1
            elapsed = time.time() - t0
            print(
                f"  [{phase} {ep:02d}/{max_epochs}] "
                f"tr_em_f1={tr['emotion_macro_f1']:.4f} va_em_f1={va['emotion_macro_f1']:.4f} "
                f"tr_ph_f1={tr['phenotype_macro_f1']:.4f} va_ph_f1={va['phenotype_macro_f1']:.4f} "
                f"({elapsed:.0f}s){marker}",
                flush=True,
            )
            if bad >= patience:
                print(f"  [early stop] {phase} epoch={ep}")
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    (out_dir / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")

    _, y_true, y_pred, ph_true, ph_pred = run_epoch(
        model, test_loader, emotion_criterion, phenotype_criterion, None, scaler, device, args.alpha, False
    )
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    per_class_f1 = f1_score(y_true, y_pred, average=None, zero_division=0)
    ph_acc = accuracy_score(ph_true, ph_pred)
    ph_f1 = f1_score(ph_true, ph_pred, average="macro", zero_division=0)
    target_names = CLASSES[:num_emotions]
    report_txt = classification_report(y_true, y_pred, target_names=target_names, zero_division=0)
    print(f"[test] emotion acc={acc:.4f} macro_f1={f1:.4f} phenotype_acc={ph_acc:.4f} phenotype_f1={ph_f1:.4f}")
    print(report_txt)

    results = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "macro_f1": float(f1),
        "per_class_f1": {target_names[i]: float(per_class_f1[i]) for i in range(len(per_class_f1))},
        "phenotype_accuracy": float(ph_acc),
        "phenotype_macro_f1": float(ph_f1),
        "best_val_emotion_macro_f1": float(best_f1),
        "best_phase": best_phase,
        "alpha": args.alpha,
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "test_samples": len(test_ds),
    }
    (out_dir / "test_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out_dir / "classification_report.txt").write_text(report_txt, encoding="utf-8")
    print(f"[done] {out_dir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--alpha", type=float, default=0.25)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--label-smoothing", type=float, default=0.07)
    ap.add_argument("--p1-epochs", type=int, default=8)
    ap.add_argument("--p1-patience", type=int, default=4)
    ap.add_argument("--p1-lr", type=float, default=5e-4)
    ap.add_argument("--p2-epochs", type=int, default=70)
    ap.add_argument("--p2-patience", type=int, default=14)
    ap.add_argument("--p2-lr", type=float, default=4e-5)
    ap.add_argument("--weight-decay", type=float, default=2e-4)
    args = ap.parse_args()
    return train(args)


if __name__ == "__main__":
    raise SystemExit(main())
