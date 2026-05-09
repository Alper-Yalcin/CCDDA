"""
build_manifest_v2.py

Guclu ogretmen modeli icin temiz manifest olusturur.

Kaynaklar (guvenilir etiketli, gercek cocuk cizimleri):
  1. dataset_qwen_selected  — train/val/test bolunmesi korunur
  2. Dataset/data           — Kaggle Children Drawings (Angry/Fear/Happy/Sad)
  3. Dataset/NewArts2       — Kaggle ek set (ayni etiket yapisi)

Val/Test seti = manifest_qwen.csv'deki 212+212 ornek (sabit, karsilastirma icin)
Train seti = qwen train (984) + Dataset/data (702) + Dataset/NewArts2 (407) = 2,093+

Cikti: out/manifest_v2.csv
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pandas as pd

QWEN_MANIFEST = Path("out/manifest_qwen.csv")
KAGGLE_DATA   = Path("Dataset/data")        # Angry / Fear / Happy / Sad
NEWARTS2      = Path("Dataset/NewArts2/NewArts2")  # Angry / Fear / Happy / Sad
OUT_CSV       = Path("out/manifest_v2.csv")
OUT_REPORT    = Path("out/manifest_v2_report.json")
SEED          = 42

LABEL_MAP = {
    "angry": ("Angry", 2),
    "anger": ("Angry", 2),
    "fear":  ("Fear",  3),
    "happy": ("Happy", 0),
    "sad":   ("Sad",   1),
    "sadness": ("Sad", 1),
}

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def collect_dir(root: Path, source: str) -> list[dict]:
    rows = []
    if not root.exists():
        print(f"[warn] {root} bulunamadi, atlaniyor")
        return rows
    for cls_dir in sorted(root.iterdir()):
        if not cls_dir.is_dir():
            continue
        key = cls_dir.name.lower()
        if key not in LABEL_MAP:
            print(f"[warn] Tanimsiz sinif: {cls_dir.name}, atlaniyor")
            continue
        label, label_id = LABEL_MAP[key]
        for i, f in enumerate(sorted(cls_dir.iterdir())):
            if f.suffix.lower() not in IMG_EXTS:
                continue
            rows.append({
                "sample_id":  f"{source}_{cls_dir.name[:3].lower()}_{i:05d}",
                "image_path": str(f.resolve()),
                "label":      label,
                "label_id":   label_id,
                "split":      "train",
                "source":     source,
                "confidence": 1.0,
            })
    return rows


def main():
    random.seed(SEED)

    # 1. Orijinal qwen manifesti (train/val/test korunur)
    qwen_df = pd.read_csv(QWEN_MANIFEST)
    qwen_df["source"] = "qwen"
    qwen_df["confidence"] = 1.0
    print(f"[qwen] {len(qwen_df)} ornek  "
          f"(train={len(qwen_df[qwen_df.split=='train'])}, "
          f"val={len(qwen_df[qwen_df.split=='val'])}, "
          f"test={len(qwen_df[qwen_df.split=='test'])})")

    # 2. Dataset/data (Kaggle Children Drawings)
    kaggle_rows = collect_dir(KAGGLE_DATA, "kaggle")
    kaggle_df = pd.DataFrame(kaggle_rows)
    print(f"[kaggle/data] {len(kaggle_df)} ornek")
    if len(kaggle_df) > 0:
        print(f"  sinif dagilimi: {dict(kaggle_df['label'].value_counts())}")

    # 3. Dataset/NewArts2
    newarts_rows = collect_dir(NEWARTS2, "newarts2")
    newarts_df = pd.DataFrame(newarts_rows)
    print(f"[newarts2] {len(newarts_df)} ornek")
    if len(newarts_df) > 0:
        print(f"  sinif dagilimi: {dict(newarts_df['label'].value_counts())}")

    # 4. Birlestir
    parts = [qwen_df]
    if len(kaggle_df) > 0:
        parts.append(kaggle_df)
    if len(newarts_df) > 0:
        parts.append(newarts_df)
    combined = pd.concat(parts, ignore_index=True)

    # sample_id benzersizligi
    combined["sample_id"] = combined["sample_id"].astype(str)
    dupes = combined["sample_id"].duplicated().sum()
    if dupes:
        print(f"[warn] {dupes} tekrarlayan sample_id — otomatik duzeltiliyor")
        combined["sample_id"] = combined.apply(
            lambda r: f"{r['source']}_{r['label_id']}_{r.name:06d}", axis=1)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_CSV, index=False)

    train_df = combined[combined["split"] == "train"]
    val_df   = combined[combined["split"] == "val"]
    test_df  = combined[combined["split"] == "test"]

    report = {
        "total": int(len(combined)),
        "train": int(len(train_df)),
        "val":   int(len(val_df)),
        "test":  int(len(test_df)),
        "sources": {k: int(v) for k, v in combined["source"].value_counts().items()},
        "train_class_dist": {k: int(v) for k, v in train_df["label"].value_counts().items()},
        "val_class_dist":   {k: int(v) for k, v in val_df["label"].value_counts().items()},
        "test_class_dist":  {k: int(v) for k, v in test_df["label"].value_counts().items()},
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n[save] {OUT_CSV}  ({len(combined)} satir)")
    print(f"  train={len(train_df)}  val={len(val_df)}  test={len(test_df)}")
    print(f"  train sinif dagilimi: {report['train_class_dist']}")


if __name__ == "__main__":
    main()
