"""
build_manifest_from_dataset.py

Dataset/augmented_dataset/{angry,fear,happy,sad}/ dizininden
stratified train/val/test split (70/15/15) ile manifest.csv üretir.

Seed=42 (tüm deneylerdeki ile aynı) — split tekrarlanabilir.
Çıktı: out/real/manifest.csv
"""
from __future__ import annotations
import random, os
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

DATASET_DIR = Path("Dataset/augmented_dataset")
OUT_CSV     = Path("out/real/manifest.csv")
SEED        = 42
VAL_RATIO   = 0.15
TEST_RATIO  = 0.15

LABEL_MAP = {"happy": 0, "sad": 1, "angry": 2, "fear": 3}

rows = []
for label_name, label_id in LABEL_MAP.items():
    class_dir = DATASET_DIR / label_name
    if not class_dir.is_dir():
        print(f"UYARI: {class_dir} bulunamadı, atlanıyor.")
        continue
    files = sorted([f for f in class_dir.iterdir()
                    if f.suffix.lower() in (".jpg", ".jpeg", ".png")])
    print(f"  {label_name}: {len(files)} görüntü")
    for f in files:
        rows.append({
            "sample_id":  f.stem,
            "image_path": str(f.resolve()),
            "label":      label_name,
            "label_id":   label_id,
        })

df = pd.DataFrame(rows)
print(f"\nToplam: {len(df)} örnek")

# Stratified split: train / temp (val+test)
train_df, temp_df = train_test_split(
    df, test_size=VAL_RATIO + TEST_RATIO,
    stratify=df["label_id"], random_state=SEED
)
# temp → val / test
val_df, test_df = train_test_split(
    temp_df, test_size=TEST_RATIO / (VAL_RATIO + TEST_RATIO),
    stratify=temp_df["label_id"], random_state=SEED
)

train_df = train_df.copy(); train_df["split"] = "train"
val_df   = val_df.copy();   val_df["split"]   = "val"
test_df  = test_df.copy();  test_df["split"]  = "test"

final = pd.concat([train_df, val_df, test_df], ignore_index=True)
final = final[["sample_id", "image_path", "label", "label_id", "split"]]

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
final.to_csv(OUT_CSV, index=False)

print(f"\nSplit dağılımı:")
for split in ["train", "val", "test"]:
    s = final[final["split"] == split]
    dist = s["label"].value_counts().to_dict()
    print(f"  {split}: {len(s)} — {dist}")
print(f"\nKaydedildi: {OUT_CSV}")
