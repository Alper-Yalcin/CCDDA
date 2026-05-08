"""
dataset_qwen_selected icin manifest olusturucu.

Klasor yapisi:
  dataset_qwen_selected/{angry,fear,happy,sad}/

Cikti:
  out/manifest_qwen.csv  -> sample_id, image_path, label, label_id, split
  split: stratified 70% train, 15% val, 15% test
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

DATASET_ROOT = Path("dataset_qwen_selected")
OUT_CSV = Path("out/manifest_qwen.csv")

FOLDER_TO_CLASS = {
    "angry": "Angry",
    "fear":  "Fear",
    "happy": "Happy",
    "sad":   "Sad",
}
CLASSES = ["Happy", "Sad", "Angry", "Fear"]
LABEL_TO_ID = {c: i for i, c in enumerate(CLASSES)}
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def collect(root: Path) -> list[dict]:
    rows: list[dict] = []
    for folder, cls in FOLDER_TO_CLASS.items():
        d = root / folder
        if not d.is_dir():
            print(f"[WARN] {d} bulunamadi", file=sys.stderr)
            continue
        for p in sorted(d.iterdir()):
            if p.suffix.lower() not in VALID_EXTS:
                continue
            rows.append({
                "sample_id": p.stem,
                "image_path": str(p.resolve()),
                "label": cls,
                "label_id": LABEL_TO_ID[cls],
            })
    return rows


def split_rows(rows: list[dict], seed: int = 42) -> None:
    labels = [r["label_id"] for r in rows]
    indices = list(range(len(rows)))

    trainval_idx, test_idx = train_test_split(
        indices, test_size=0.15, random_state=seed,
        stratify=labels,
    )
    trainval_labels = [labels[i] for i in trainval_idx]
    train_idx, val_idx = train_test_split(
        trainval_idx, test_size=0.15 / 0.85, random_state=seed,
        stratify=trainval_labels,
    )

    split_map = {}
    for i in train_idx:
        split_map[i] = "train"
    for i in val_idx:
        split_map[i] = "val"
    for i in test_idx:
        split_map[i] = "test"

    for i, r in enumerate(rows):
        r["split"] = split_map[i]


def write_csv(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["sample_id", "image_path", "label", "label_id", "split"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def print_dist(rows: list[dict]) -> None:
    counts: dict[tuple, int] = defaultdict(int)
    for r in rows:
        counts[(r["split"], r["label"])] += 1
    print(f"\n{'split':<8} {'label':<8} {'count':>6}")
    for split in ("train", "val", "test"):
        for cls in CLASSES:
            print(f"{split:<8} {cls:<8} {counts[(split, cls)]:>6}")
    print(f"\nToplam: {len(rows)}")


def main() -> int:
    print(f"[1/3] Dosyalar taraniyor: {DATASET_ROOT}")
    rows = collect(DATASET_ROOT)
    print(f"      {len(rows)} dosya bulundu")

    print("[2/3] Stratified split (70/15/15)...")
    split_rows(rows)

    write_csv(rows, OUT_CSV)
    print(f"[3/3] Manifest yazildi: {OUT_CSV}")
    print_dist(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
