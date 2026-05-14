"""
High-confidence pseudo-label pipeline.

Stages:
  1. Extract Dataset/huggingface parquet images to JPEG files.
  2. Build a deduplicated inventory from all usable images under Dataset/.
  3. Label every non-heldout candidate with the current best teacher
     (out/combined_v3_run/checkpoints/best.pt).
  4. Build two training manifests: confidence >= 0.85 and >= 0.75.
  5. Train one EfficientNet-B3 student for each manifest, sequentially.

Outputs live under out/highconf_pipeline/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from collections import Counter
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageFile
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import (
    EfficientNet_B2_Weights,
    EfficientNet_B3_Weights,
    efficientnet_b2,
    efficientnet_b3,
)

ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out" / "highconf_pipeline"
HF_PARQUET_DIR = ROOT / "Dataset" / "huggingface"
HF_EXTRACT_DIR = ROOT / "Dataset" / "huggingface_extracted"
TEACHER_CKPT = ROOT / "out" / "combined_v3_run" / "checkpoints" / "best.pt"

CLASSES = ["Happy", "Sad", "Angry", "Fear"]
LABEL_TO_ID = {c: i for i, c in enumerate(CLASSES)}
REAL_DIRS = [ROOT / "Dataset" / "data", ROOT / "Dataset" / "NewArts2" / "NewArts2"]
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
SEED = 42

CATEGORY_EN = {
    "나무": "Tree",
    "남자사람": "MaleFigure",
    "여자사람": "FemaleFigure",
    "집": "House",
}
GENDER_EN = {"남": "M", "여": "F"}


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifests").mkdir(exist_ok=True)
    (OUT / "runs").mkdir(exist_ok=True)


def extract_huggingface(force: bool = False) -> Path:
    out_csv = OUT / "huggingface_extracted_manifest.csv"
    if out_csv.exists() and not force:
        print(f"[hf_extract] exists: {out_csv}")
        return out_csv

    HF_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    t0 = time.time()
    total = 0

    parquet_files = sorted(HF_PARQUET_DIR.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found: {HF_PARQUET_DIR}")

    print(f"[hf_extract] parquet files={len(parquet_files)} -> {HF_EXTRACT_DIR}")
    for parquet_path in parquet_files:
        split = "validation" if parquet_path.name.startswith("validation") else "train"
        pf = pq.ParquetFile(parquet_path)
        for rg in range(pf.metadata.num_row_groups):
            table = pf.read_row_group(rg)
            data = table.to_pydict()
            n = len(data["id"])
            for i in range(n):
                img_obj = data["image"][i]
                img_bytes = img_obj.get("bytes") if isinstance(img_obj, dict) else None
                if not img_bytes:
                    continue
                category = str(data["category"][i])
                category_en = CATEGORY_EN.get(category, "Unknown")
                age = str(data["age"][i])
                gender = str(data["gender"][i])
                gender_en = GENDER_EN.get(gender, "U")
                source_id = str(data["id"][i])
                sample_id = (
                    f"hf_{split}_{category_en}_{age}_{gender_en}_"
                    f"{source_id}_{rg:03d}_{i:03d}"
                )
                out_dir = HF_EXTRACT_DIR / split / category_en
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{sample_id}.jpg"
                if force or not out_path.exists():
                    try:
                        with Image.open(BytesIO(img_bytes)) as im:
                            im.convert("RGB").save(out_path, "JPEG", quality=92)
                    except Exception as exc:
                        print(f"  [hf_extract err] {sample_id}: {exc}")
                        continue

                rows.append({
                    "sample_id": sample_id,
                    "image_path": str(out_path.resolve()),
                    "source": "huggingface",
                    "hf_split": split,
                    "category": category,
                    "category_en": category_en,
                    "age": age,
                    "gender": gender,
                    "gender_en": gender_en,
                    "hf_id": source_id,
                    "parquet_file": parquet_path.name,
                })
                total += 1
            if total and total % 5000 == 0:
                print(f"  [hf_extract] {total} images ({time.time() - t0:.0f}s)")

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"[hf_extract] saved {len(df)} rows -> {out_csv}")
    return out_csv


def image_size(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return 0, 0


def collect_real_records() -> list[dict]:
    records: list[dict] = []
    for base in REAL_DIRS:
        if not base.exists():
            continue
        for cls_dir in sorted(base.iterdir()):
            if not cls_dir.is_dir() or cls_dir.name not in LABEL_TO_ID:
                continue
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in VALID_EXTS:
                    records.append({
                        "image_path": str(f.resolve()),
                        "label": cls_dir.name,
                        "label_id": LABEL_TO_ID[cls_dir.name],
                        "source": f"real:{base.name}",
                    })
    return records


def split_real_records() -> tuple[list[dict], list[dict], list[dict]]:
    real = collect_real_records()
    labels = [r["label_id"] for r in real]
    train_idx, valtest_idx = train_test_split(
        list(range(len(real))),
        test_size=0.30,
        random_state=SEED,
        stratify=labels,
    )
    valtest_labels = [labels[i] for i in valtest_idx]
    val_idx, test_idx = train_test_split(
        list(valtest_idx),
        test_size=0.50,
        random_state=SEED,
        stratify=valtest_labels,
    )
    return (
        [real[i] for i in train_idx],
        [real[i] for i in val_idx],
        [real[i] for i in test_idx],
    )


def build_inventory(force: bool = False) -> Path:
    out_csv = OUT / "all_images_inventory.csv"
    if out_csv.exists() and not force:
        print(f"[inventory] exists: {out_csv}")
        return out_csv

    rows: list[dict] = []
    t0 = time.time()
    seen_paths: set[str] = set()
    print("[inventory] scanning Dataset/ for image files")
    for path in sorted((ROOT / "Dataset").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in VALID_EXTS:
            continue
        # Only image files; parquet source folder has no image files.
        resolved = str(path.resolve())
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        try:
            h = sha256_file(path)
            w, ht = image_size(path)
        except Exception as exc:
            print(f"  [inventory err] {path}: {exc}")
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        source = "dataset"
        if "Dataset/huggingface_extracted/" in rel:
            source = "huggingface"
        elif "Dataset/data/" in rel:
            source = "real_data"
        elif "Dataset/NewArts2/" in rel:
            source = "real_newarts2"
        elif "Dataset/Images/" in rel:
            source = "dataset_images"
        rows.append({
            "sample_id": f"img_{len(rows):08d}",
            "image_path": resolved,
            "rel_path": rel,
            "sha256": h,
            "width": w,
            "height": ht,
            "source": source,
        })
        if len(rows) % 10000 == 0:
            print(f"  [inventory] {len(rows)} files ({time.time() - t0:.0f}s)")

    df = pd.DataFrame(rows)
    before = len(df)
    df = df.sort_values(["source", "rel_path"]).drop_duplicates("sha256", keep="first")
    df.to_csv(out_csv, index=False)
    report = {
        "raw_files": int(before),
        "unique_hashes": int(len(df)),
        "source_dist": {k: int(v) for k, v in df["source"].value_counts().items()},
    }
    (OUT / "all_images_inventory_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[inventory] raw={before} unique={len(df)} -> {out_csv}")
    print(f"[inventory] source_dist={report['source_dist']}")
    return out_csv


class EfficientNetB2Teacher(nn.Module):
    def __init__(self, num_classes: int = 4) -> None:
        super().__init__()
        net = efficientnet_b2(weights=EfficientNet_B2_Weights.IMAGENET1K_V1)
        self.features = net.features
        self.avgpool = net.avgpool
        self.head = nn.Sequential(
            nn.Dropout(0.40),
            nn.Linear(1408, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.15),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.head(x)


class PathImageDataset(Dataset):
    def __init__(self, df: pd.DataFrame, transform) -> None:
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict:
        row = self.df.iloc[idx]
        path = str(row["image_path"])
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            img = Image.new("RGB", (260, 260), 128)
        return {
            "image": self.transform(img),
            "sample_id": str(row["sample_id"]),
            "image_path": path,
            "sha256": str(row["sha256"]),
            "source": str(row["source"]),
            "width": int(row["width"]),
            "height": int(row["height"]),
        }


def teacher_transform():
    return transforms.Compose([
        transforms.Resize(288),
        transforms.CenterCrop(260),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])


def load_teacher(device: str) -> EfficientNetB2Teacher:
    if not TEACHER_CKPT.exists():
        raise FileNotFoundError(f"Teacher checkpoint missing: {TEACHER_CKPT}")
    model = EfficientNetB2Teacher(num_classes=4).to(device)
    state = torch.load(TEACHER_CKPT, map_location=device)
    model.load_state_dict(state["model_state"])
    model.eval()
    return model


def label_inventory(
    inventory_csv: Path,
    batch_size: int,
    num_workers: int,
    device: str,
    force: bool = False,
) -> Path:
    out_csv = OUT / "teacher_labels_all.csv"
    if out_csv.exists() and not force:
        print(f"[label] exists: {out_csv}")
        return out_csv

    inv = pd.read_csv(inventory_csv)

    real_train, real_val, real_test = split_real_records()
    heldout_hashes: set[str] = set()
    real_hashes: set[str] = set()
    for split_name, records in (("val", real_val), ("test", real_test), ("train", real_train)):
        for r in records:
            h = sha256_file(Path(r["image_path"]))
            real_hashes.add(h)
            if split_name in {"val", "test"}:
                heldout_hashes.add(h)

    # Teacher labels are used only for non-real, non-heldout candidate images.
    candidates = inv[
        ~inv["sha256"].isin(real_hashes)
        & ~inv["sha256"].isin(heldout_hashes)
    ].copy()
    candidates = candidates.reset_index(drop=True)
    print(f"[label] candidates={len(candidates)} from inventory={len(inv)}")

    loader = DataLoader(
        PathImageDataset(candidates, teacher_transform()),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=(device == "cuda"),
    )
    model = load_teacher(device)
    rows: list[dict] = []
    t0 = time.time()
    seen = 0
    with torch.no_grad():
        for batch in loader:
            imgs = batch["image"].to(device, non_blocking=True)
            logits = model(imgs)
            probs = F.softmax(logits, dim=1).detach().cpu().numpy()
            pred_ids = probs.argmax(axis=1)
            confs = probs.max(axis=1)
            n = len(pred_ids)
            for i in range(n):
                row = {
                    "sample_id": batch["sample_id"][i],
                    "image_path": batch["image_path"][i],
                    "sha256": batch["sha256"][i],
                    "source": batch["source"][i],
                    "width": int(batch["width"][i]),
                    "height": int(batch["height"][i]),
                    "label": CLASSES[int(pred_ids[i])],
                    "label_id": int(pred_ids[i]),
                    "confidence": float(confs[i]),
                    "prob_Happy": float(probs[i, 0]),
                    "prob_Sad": float(probs[i, 1]),
                    "prob_Angry": float(probs[i, 2]),
                    "prob_Fear": float(probs[i, 3]),
                    "teacher": "combined_v3_b2",
                }
                rows.append(row)
            seen += n
            if seen % (batch_size * 20) == 0 or seen == len(candidates):
                rate = seen / max(time.time() - t0, 1e-6)
                eta = (len(candidates) - seen) / max(rate, 1e-6) / 60
                print(f"  [label] {seen}/{len(candidates)} rate={rate:.1f}/s eta={eta:.1f}m")

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    report = {
        "total_labeled": int(len(df)),
        "pred_dist": {k: int(v) for k, v in df["label"].value_counts().items()},
        "conf_mean": float(df["confidence"].mean()) if len(df) else 0.0,
        "conf_ge_085": int((df["confidence"] >= 0.85).sum()) if len(df) else 0,
        "conf_ge_075": int((df["confidence"] >= 0.75).sum()) if len(df) else 0,
    }
    (OUT / "teacher_labels_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[label] saved {len(df)} rows -> {out_csv}")
    print(f"[label] report={report}")
    return out_csv


def real_manifest_rows() -> tuple[list[dict], list[dict], list[dict]]:
    real_train, real_val, real_test = split_real_records()
    output = []
    for split_name, records in (("train", real_train), ("val", real_val), ("test", real_test)):
        rows = []
        for idx, r in enumerate(records):
            path = Path(r["image_path"])
            h = sha256_file(path)
            w, ht = image_size(path)
            rows.append({
                "sample_id": f"real_{split_name}_{idx:06d}",
                "image_path": str(path.resolve()),
                "label": r["label"],
                "label_id": r["label_id"],
                "split": split_name,
                "source": r["source"],
                "confidence": 1.0,
                "sample_weight": 1.0,
                "sha256": h,
                "width": w,
                "height": ht,
                "prob_Happy": "",
                "prob_Sad": "",
                "prob_Angry": "",
                "prob_Fear": "",
            })
        output.append(rows)
    return tuple(output)  # type: ignore[return-value]


def build_threshold_manifest(
    labels_csv: Path,
    threshold: float,
    max_per_class: int,
    force: bool = False,
) -> Path:
    tag = f"{int(threshold * 100):03d}"
    out_csv = OUT / "manifests" / f"manifest_highconf_{tag}.csv"
    if out_csv.exists() and not force:
        print(f"[manifest {tag}] exists: {out_csv}")
        return out_csv

    labels = pd.read_csv(labels_csv)
    selected_parts = []
    labels = labels[labels["confidence"] >= threshold].copy()
    for cls in CLASSES:
        cls_df = labels[labels["label"] == cls].sort_values("confidence", ascending=False)
        selected_parts.append(cls_df.head(max_per_class))
    pseudo = pd.concat(selected_parts, ignore_index=True) if selected_parts else pd.DataFrame()

    real_train, real_val, real_test = real_manifest_rows()
    rows = real_train + real_val + real_test

    for i, r in pseudo.iterrows():
        rows.append({
            "sample_id": f"pseudo_{tag}_{i:08d}",
            "image_path": r["image_path"],
            "label": r["label"],
            "label_id": int(r["label_id"]),
            "split": "train",
            "source": f"pseudo_{r['source']}",
            "confidence": float(r["confidence"]),
            "sample_weight": max(0.25, float(r["confidence"])),
            "sha256": r["sha256"],
            "width": int(r["width"]),
            "height": int(r["height"]),
            "prob_Happy": float(r["prob_Happy"]),
            "prob_Sad": float(r["prob_Sad"]),
            "prob_Angry": float(r["prob_Angry"]),
            "prob_Fear": float(r["prob_Fear"]),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    report = {
        "threshold": threshold,
        "max_per_class": max_per_class,
        "total_rows": int(len(df)),
        "pseudo_selected": int(len(pseudo)),
        "split_dist": {
            split: {k: int(v) for k, v in part["label"].value_counts().items()}
            for split, part in df.groupby("split")
        },
        "pseudo_dist": {k: int(v) for k, v in pseudo["label"].value_counts().items()} if len(pseudo) else {},
        "pseudo_source_dist": {k: int(v) for k, v in pseudo["source"].value_counts().items()} if len(pseudo) else {},
    }
    report_path = OUT / "manifests" / f"manifest_highconf_{tag}_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[manifest {tag}] saved -> {out_csv}")
    print(f"[manifest {tag}] pseudo_dist={report['pseudo_dist']}")
    print(f"[manifest {tag}] split_dist={report['split_dist']}")
    return out_csv


class ManifestDataset(Dataset):
    def __init__(self, manifest: Path, split: str, transform) -> None:
        df = pd.read_csv(manifest)
        self.df = df[df["split"] == split].reset_index(drop=True)
        self.transform = transform
        if self.df.empty:
            raise ValueError(f"Empty split: {split} in {manifest}")

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict:
        row = self.df.iloc[idx]
        try:
            img = Image.open(row["image_path"]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (280, 280), 128)
        return {
            "image": self.transform(img),
            "label": torch.tensor(int(row["label_id"]), dtype=torch.long),
            "sample_weight": torch.tensor(float(row.get("sample_weight", 1.0)), dtype=torch.float32),
        }


class B3Classifier(nn.Module):
    def __init__(self, num_classes: int = 4, pretrained: bool = True) -> None:
        super().__init__()
        weights = EfficientNet_B3_Weights.IMAGENET1K_V1 if pretrained else None
        net = efficientnet_b3(weights=weights)
        self.features = net.features
        self.avgpool = net.avgpool
        self.head = nn.Sequential(
            nn.Dropout(0.35),
            nn.Linear(1536, 512),
            nn.GELU(),
            nn.Dropout(0.20),
            nn.Linear(512, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        return self.head(x)

    def freeze_backbone(self) -> None:
        for p in self.features.parameters():
            p.requires_grad = False

    def unfreeze_all(self) -> None:
        for p in self.parameters():
            p.requires_grad = True


def b3_transforms():
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


def class_weights(labels: list[int], n: int, device: str) -> torch.Tensor:
    counts = np.bincount(labels, minlength=n).astype(np.float32)
    counts[counts == 0] = 1.0
    return torch.tensor(counts.sum() / (n * counts), dtype=torch.float32, device=device)


def sampler_for(labels: list[int], n: int) -> WeightedRandomSampler:
    counts = np.bincount(labels, minlength=n).astype(np.float32)
    counts[counts == 0] = 1.0
    w = 1.0 / counts
    return WeightedRandomSampler([float(w[y]) for y in labels], len(labels), replacement=True)


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer,
    scaler,
    device: str,
    train: bool,
) -> tuple[dict, list[int], list[int]]:
    model.train() if train else model.eval()
    total_loss = 0.0
    preds_all: list[int] = []
    tgts_all: list[int] = []
    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for batch in loader:
            img = batch["image"].to(device, non_blocking=True)
            y = batch["label"].to(device, non_blocking=True)
            sw = batch["sample_weight"].to(device, non_blocking=True)
            with torch.amp.autocast("cuda", enabled=(device == "cuda")):
                logits = model(img)
                loss_per = criterion(logits, y)
                loss = (loss_per * sw).mean()
            if train:
                optimizer.zero_grad(set_to_none=True)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
            total_loss += float(loss.item()) * y.size(0)
            preds_all.extend(logits.argmax(1).detach().cpu().tolist())
            tgts_all.extend(y.detach().cpu().tolist())
    n = max(len(tgts_all), 1)
    return (
        {
            "loss": total_loss / n,
            "acc": float(accuracy_score(tgts_all, preds_all)),
            "macro_f1": float(f1_score(tgts_all, preds_all, average="macro", zero_division=0)),
        },
        tgts_all,
        preds_all,
    )


def train_b3_manifest(
    manifest: Path,
    tag: str,
    batch_size: int,
    num_workers: int,
    device: str,
    force: bool = False,
) -> Path:
    out_dir = OUT / "runs" / f"b3_highconf_{tag}"
    test_json = out_dir / "test_results.json"
    if test_json.exists() and not force:
        print(f"[train {tag}] exists: {test_json}")
        return out_dir

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "checkpoints").mkdir(exist_ok=True)
    train_tf, val_tf = b3_transforms()
    train_ds = ManifestDataset(manifest, "train", train_tf)
    val_ds = ManifestDataset(manifest, "val", val_tf)
    test_ds = ManifestDataset(manifest, "test", val_tf)

    labels = train_ds.df["label_id"].astype(int).tolist()
    cw = class_weights(labels, 4, device)
    sampler = sampler_for(labels, 4)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        sampler=sampler,
        num_workers=num_workers,
        pin_memory=(device == "cuda"),
        persistent_workers=(num_workers > 0),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=(device == "cuda"),
        persistent_workers=(num_workers > 0),
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=(device == "cuda"),
        persistent_workers=(num_workers > 0),
    )

    print(f"[train {tag}] train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}")
    print(f"[train {tag}] train_dist={dict(Counter(labels))}")
    print(f"[train {tag}] class_weights={[round(x, 3) for x in cw.detach().cpu().tolist()]}")

    model = B3Classifier(num_classes=4, pretrained=True).to(device)
    criterion = nn.CrossEntropyLoss(weight=cw, label_smoothing=0.07, reduction="none")
    scaler = torch.amp.GradScaler("cuda", enabled=(device == "cuda"))
    history: list[dict] = []
    best_f1 = -1.0
    best_state = None
    best_phase = ""
    t0 = time.time()

    phases = [
        ("p1", 8, 5, 3e-4, 1e-4, True),
        ("p2", 70, 14, 2e-5, 2e-4, False),
    ]
    for phase_name, max_epochs, patience, lr, wd, freeze in phases:
        if freeze:
            model.freeze_backbone()
        else:
            model.unfreeze_all()
        optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=wd)
        scheduler = CosineAnnealingLR(optimizer, T_max=max_epochs, eta_min=5e-7)
        bad = 0
        print(f"[train {tag}] phase={phase_name} epochs={max_epochs} trainable={sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
        for ep in range(1, max_epochs + 1):
            tr, _, _ = run_epoch(model, train_loader, criterion, optimizer, scaler, device, True)
            va, _, _ = run_epoch(model, val_loader, criterion, None, scaler, device, False)
            scheduler.step()
            rec = {"phase": phase_name, "epoch": ep, "train": tr, "val": va}
            history.append(rec)
            marker = ""
            if va["macro_f1"] > best_f1:
                best_f1 = va["macro_f1"]
                best_phase = phase_name
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                bad = 0
                marker = " * BEST"
                torch.save(
                    {
                        "model_state": model.state_dict(),
                        "val_macro_f1": best_f1,
                        "classes": CLASSES,
                        "manifest": str(manifest),
                        "threshold_tag": tag,
                        "phase": phase_name,
                    },
                    out_dir / "checkpoints" / "best.pt",
                )
            else:
                bad += 1
            elapsed = time.time() - t0
            print(
                f"  [{tag} {phase_name} {ep:02d}/{max_epochs}] "
                f"tr_f1={tr['macro_f1']:.4f} va_f1={va['macro_f1']:.4f} "
                f"({elapsed:.0f}s){marker}",
                flush=True,
            )
            if bad >= patience:
                print(f"  [train {tag}] early stop {phase_name} epoch={ep}")
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    (out_dir / "train_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")

    _, tgts, preds = run_epoch(model, test_loader, criterion, None, scaler, device, False)
    acc = accuracy_score(tgts, preds)
    prec = precision_score(tgts, preds, average="macro", zero_division=0)
    rec = recall_score(tgts, preds, average="macro", zero_division=0)
    f1 = f1_score(tgts, preds, average="macro", zero_division=0)
    per_class = f1_score(tgts, preds, average=None, zero_division=0)
    report = classification_report(tgts, preds, target_names=CLASSES, zero_division=0)
    print(f"[train {tag}] TEST acc={acc:.4f} precision={prec:.4f} recall={rec:.4f} f1={f1:.4f}")
    print(report)
    results = {
        "threshold_tag": tag,
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "macro_f1": float(f1),
        "per_class_f1": {CLASSES[i]: float(per_class[i]) for i in range(4)},
        "best_val_macro_f1": float(best_f1),
        "best_phase": best_phase,
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "test_samples": len(test_ds),
    }
    test_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out_dir / "classification_report.txt").write_text(report, encoding="utf-8")
    return out_dir


def write_summary(run_dirs: list[Path]) -> None:
    rows = []
    for run_dir in run_dirs:
        p = run_dir / "test_results.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            rows.append(d)
    if rows:
        pd.DataFrame(rows).to_csv(OUT / "summary_results.csv", index=False)
        (OUT / "summary_results.json").write_text(
            json.dumps(rows, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-extract", action="store_true")
    parser.add_argument("--force-inventory", action="store_true")
    parser.add_argument("--force-label", action="store_true")
    parser.add_argument("--force-manifests", action="store_true")
    parser.add_argument("--force-train", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--batch-label", type=int, default=96)
    parser.add_argument("--batch-train", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=max(2, min(8, (os.cpu_count() or 6) - 2)))
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max-per-class", type=int, default=6000)
    args = parser.parse_args()

    set_seed(SEED)
    ensure_dirs()
    print(f"[init] device={args.device} workers={args.num_workers}")
    print(f"[init] torch={torch.__version__} cuda={torch.cuda.is_available()}")
    if args.device == "cuda":
        print(f"[init] gpu={torch.cuda.get_device_name(0)}")

    extract_huggingface(force=args.force_extract)
    inventory_csv = build_inventory(force=args.force_inventory)
    labels_csv = label_inventory(
        inventory_csv,
        batch_size=args.batch_label,
        num_workers=args.num_workers,
        device=args.device,
        force=args.force_label,
    )
    manifest_085 = build_threshold_manifest(
        labels_csv,
        threshold=0.85,
        max_per_class=args.max_per_class,
        force=args.force_manifests,
    )
    manifest_075 = build_threshold_manifest(
        labels_csv,
        threshold=0.75,
        max_per_class=args.max_per_class,
        force=args.force_manifests,
    )

    run_dirs: list[Path] = []
    if not args.skip_train:
        run_dirs.append(train_b3_manifest(
            manifest_085,
            tag="085",
            batch_size=args.batch_train,
            num_workers=args.num_workers,
            device=args.device,
            force=args.force_train,
        ))
        run_dirs.append(train_b3_manifest(
            manifest_075,
            tag="075",
            batch_size=args.batch_train,
            num_workers=args.num_workers,
            device=args.device,
            force=args.force_train,
        ))
    write_summary(run_dirs)
    print(f"[done] outputs -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
