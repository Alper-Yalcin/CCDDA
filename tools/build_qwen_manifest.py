"""
dataset_qwen_selected icin manifest olusturucu.
Duz klasor yapisi: dataset_qwen_selected/{angry,fear,happy,sad}/
4 sinif, stratified train/val/test split.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from sklearn.model_selection import train_test_split

CLASSES = ["Happy", "Sad", "Angry", "Fear"]
LABEL_TO_ID = {c: i for i, c in enumerate(CLASSES)}
FOLDER_TO_CLASS = {
    "happy": "Happy",
    "sad": "Sad",
    "angry": "Angry",
    "fear": "Fear",
}
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def collect_files(dataset_root: Path) -> list[dict]:
    rows: list[dict] = []
    for folder_name, class_name in FOLDER_TO_CLASS.items():
        cls_dir = dataset_root / folder_name
        if not cls_dir.is_dir():
            print(f"[WARN] Klasor bulunamadi: {cls_dir}", file=sys.stderr)
            continue
        for p in sorted(cls_dir.iterdir()):
            if p.suffix.lower() not in VALID_EXTS:
                continue
            rows.append({
                "sample_id": p.stem,
                "image_path": str(p.resolve()),
                "label": class_name,
                "label_id": LABEL_TO_ID[class_name],
            })
    return rows


def split_data(rows: list[dict], val_ratio: float, test_ratio: float, seed: int) -> None:
    indices = list(range(len(rows)))
    labels = [r["label_id"] for r in rows]

    train_val_idx, test_idx = train_test_split(
        indices,
        test_size=test_ratio,
        random_state=seed,
        stratify=labels,
    )

    val_ratio_adjusted = val_ratio / (1.0 - test_ratio)
    train_val_labels = [labels[i] for i in train_val_idx]
    train_idx, val_idx = train_test_split(
        train_val_idx,
        test_size=val_ratio_adjusted,
        random_state=seed,
        stratify=train_val_labels,
    )

    train_set = set(train_idx)
    val_set = set(val_idx)
    test_set = set(test_idx)

    for i, r in enumerate(rows):
        if i in train_set:
            r["split"] = "train"
        elif i in val_set:
            r["split"] = "val"
        elif i in test_set:
            r["split"] = "test"
        else:
            r["split"] = "train"


def write_manifest(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["sample_id", "image_path", "label", "label_id", "split"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def print_distribution(rows: list[dict]) -> None:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        counts[(r["split"], r["label"])] += 1
    print("\nSplit / Label dagilimi:")
    print(f"{'split':<8}{'label':<10}{'count':>8}")
    for split in ("train", "val", "test"):
        for cls in CLASSES:
            print(f"{split:<8}{cls:<10}{counts[(split, cls)]:>8}")
    total_train = sum(counts[("train", c)] for c in CLASSES)
    total_val = sum(counts[("val", c)] for c in CLASSES)
    total_test = sum(counts[("test", c)] for c in CLASSES)
    print(f"\nToplam: {len(rows)} ornek  (train={total_train}, val={total_val}, test={total_test})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--val-ratio", type=float, default=0.10)
    ap.add_argument("--test-ratio", type=float, default=0.10)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if not args.dataset_root.is_dir():
        print(f"[ERR] dataset-root bulunamadi: {args.dataset_root}", file=sys.stderr)
        return 2

    print(f"[1/3] Dosyalar taraniyor: {args.dataset_root}")
    rows = collect_files(args.dataset_root)
    print(f"      {len(rows)} dosya bulundu")

    print(f"[2/3] Stratified split (val={args.val_ratio}, test={args.test_ratio}, seed={args.seed})...")
    split_data(rows, args.val_ratio, args.test_ratio, args.seed)

    write_manifest(rows, args.out)
    print(f"[3/3] Manifest yazildi: {args.out}")
    print_distribution(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
