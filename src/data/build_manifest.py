"""
SigLIP Filtered_045 dataset için manifest oluşturucu.

Dataset/Images/Emotion_SigLIP_4Class_Filtered_045/{train,test}/{Happy,Sad,Angry,Fear}
klasor yapisini tarayip her ornek icin satir uretir.
Train icinden stratified val split (default 0.15, seed=42).
predictions_filtered.csv'den SigLIP soft skorlari join edilir.
SHA-256 cakisma kontrolu yapilir; ayni hash farkli sinifta ise hard fail.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
from PIL import Image
from sklearn.model_selection import train_test_split


CLASSES = ["Happy", "Sad", "Angry", "Fear"]
LABEL_TO_ID = {c: i for i, c in enumerate(CLASSES)}
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(images_root: Path) -> list[dict]:
    rows: list[dict] = []
    for split_dir_name in ("train", "test"):
        split_dir = images_root / split_dir_name
        if not split_dir.is_dir():
            raise FileNotFoundError(f"Beklenen alt klasor yok: {split_dir}")
        for cls in CLASSES:
            cls_dir = split_dir / cls
            if not cls_dir.is_dir():
                print(f"[WARN] Sinif klasoru yok: {cls_dir}", file=sys.stderr)
                continue
            for p in sorted(cls_dir.iterdir()):
                if p.suffix.lower() not in VALID_EXTS:
                    continue
                sample_id = p.stem
                rows.append({
                    "sample_id": sample_id,
                    "image_path": str(p.resolve()),
                    "label": cls,
                    "label_id": LABEL_TO_ID[cls],
                    "_raw_split": split_dir_name,
                })
    return rows


def enrich_with_image_meta(rows: list[dict]) -> None:
    for r in rows:
        try:
            with Image.open(r["image_path"]) as im:
                r["width"], r["height"] = im.size
        except Exception:
            r["width"], r["height"] = 0, 0
        r["sha256"] = sha256_of(Path(r["image_path"]))


def detect_hash_conflicts(rows: list[dict]) -> list[tuple[str, set[str]]]:
    by_hash: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        by_hash[r["sha256"]].add(r["label"])
    conflicts = [(h, labels) for h, labels in by_hash.items() if len(labels) > 1]
    return conflicts


def stratified_val_split(rows: list[dict], val_ratio: float, seed: int) -> None:
    train_rows = [r for r in rows if r["_raw_split"] == "train"]
    test_rows = [r for r in rows if r["_raw_split"] == "test"]

    if not train_rows:
        for r in test_rows:
            r["split"] = "test"
        return

    indices = list(range(len(train_rows)))
    labels = [r["label_id"] for r in train_rows]

    train_idx, val_idx = train_test_split(
        indices,
        test_size=val_ratio,
        random_state=seed,
        stratify=labels,
    )
    val_set = set(val_idx)
    for i, r in enumerate(train_rows):
        r["split"] = "val" if i in val_set else "train"
    for r in test_rows:
        r["split"] = "test"


def join_siglip_scores(rows: list[dict], predictions_csv: Path | None) -> None:
    score_cols = ["score_Happy", "score_Sad", "score_Angry", "score_Fear", "confidence"]
    if predictions_csv is None or not predictions_csv.is_file():
        for r in rows:
            for c in score_cols:
                r[c] = ""
        return
    df = pd.read_csv(predictions_csv)
    df.columns = [c.strip() for c in df.columns]
    if "image_id" not in df.columns:
        for r in rows:
            for c in score_cols:
                r[c] = ""
        return
    lookup = df.set_index("image_id")
    for r in rows:
        if r["sample_id"] in lookup.index:
            row = lookup.loc[r["sample_id"]]
            for c in score_cols:
                r[c] = float(row[c]) if c in row and pd.notna(row[c]) else ""
        else:
            for c in score_cols:
                r[c] = ""


def write_manifest(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_id", "image_path", "label", "label_id", "split",
        "sha256", "width", "height",
        "score_Happy", "score_Sad", "score_Angry", "score_Fear", "confidence",
    ]
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
    print(f"\nToplam: {len(rows)} ornek")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images-root", required=True, type=Path)
    ap.add_argument("--predictions", type=Path, default=None,
                    help="predictions_filtered.csv yolu (opsiyonel)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--val-ratio", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--allow-hash-conflicts", action="store_true",
                    help="Sinif arasi hash cakismasini sadece uyari yap")
    args = ap.parse_args()

    if not args.images_root.is_dir():
        print(f"[ERR] images-root bulunamadi: {args.images_root}", file=sys.stderr)
        return 2

    print(f"[1/5] Dosyalar taraniyor: {args.images_root}")
    rows = collect_files(args.images_root)
    print(f"      {len(rows)} dosya bulundu")

    print(f"[2/5] Boyut + SHA-256 hesaplaniyor...")
    enrich_with_image_meta(rows)

    print(f"[3/5] Hash cakisma kontrolu...")
    conflicts = detect_hash_conflicts(rows)
    if conflicts:
        msg = f"      {len(conflicts)} hash farkli sinifta gorundu"
        for h, labels in conflicts[:5]:
            msg += f"\n        - {h[:12]}... -> {sorted(labels)}"
        if args.allow_hash_conflicts:
            print(f"[WARN] {msg}", file=sys.stderr)
        else:
            print(f"[ERR] {msg}", file=sys.stderr)
            print("      --allow-hash-conflicts ile devam edebilirsin.", file=sys.stderr)
            return 3
    else:
        print("      Cakisma yok.")

    print(f"[4/5] Stratified val split (ratio={args.val_ratio}, seed={args.seed})...")
    stratified_val_split(rows, args.val_ratio, args.seed)

    print(f"[5/5] SigLIP skorlari join ediliyor: {args.predictions}")
    join_siglip_scores(rows, args.predictions)

    write_manifest(rows, args.out)
    print(f"\nManifest yazildi: {args.out}")
    print_distribution(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
