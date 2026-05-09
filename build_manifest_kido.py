"""
build_manifest_kido.py

Dataset/Images/Emotion_4Class (KIDO 4-sinif) + dataset_qwen_selected birlestirip
manifest_kido.csv uretir.

Sinif eslestirmesi:
  KIDO Anger    -> Angry   (label_id=2)
  KIDO Anxiety  -> Fear    (label_id=3)  [klinik olarak yakin)
  KIDO Happy    -> Happy   (label_id=0)
  KIDO Sadness  -> Sad     (label_id=1)

Strateji:
  - qwen_selected: train/val/test olduğu gibi korunur
  - KIDO: yalnizca train'e eklenir
  - Sinif dengesi: Happy/Sad'i 1000'de, Angry/Anxiety hepsini kullan

Cikti:
  out/manifest_kido.csv
  out/kido_report.json
"""
from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

import pandas as pd

QWEN_MANIFEST = Path("out/manifest_qwen.csv")
KIDO_ROOT     = Path("Dataset/Images/Emotion_4Class")
OUT_CSV       = Path("out/manifest_kido.csv")
OUT_REPORT    = Path("out/kido_report.json")
SEED          = 42
MAX_HAPPY_SAD = 1000   # KIDO'dan Happy/Sad icin max

KIDO_MAP = {
    "Anger":   ("Angry", 2),
    "Anxiety": ("Fear",  3),
    "Happy":   ("Happy", 0),
    "Sadness": ("Sad",   1),
}


def main():
    random.seed(SEED)

    # 1. Orijinal qwen manifest
    qwen_df = pd.read_csv(QWEN_MANIFEST)
    qwen_df["source"] = "qwen"
    qwen_df["confidence"] = 1.0
    print(f"[qwen] {len(qwen_df)} ornek")

    existing_paths = set(qwen_df["image_path"].str.lower())

    # 2. KIDO goruntuleri topla (train + test -> hepsini train'e ekle)
    kido_rows = []
    kido_counts = {}
    for kido_cls, (our_label, label_id) in KIDO_MAP.items():
        images = []
        for split_dir in ["train", "test"]:
            d = KIDO_ROOT / split_dir / kido_cls
            if not d.is_dir():
                continue
            for f in d.iterdir():
                if f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                    continue
                abs_p = str(f.resolve())
                if abs_p.lower() in existing_paths:
                    continue
                images.append(abs_p)

        # Happy ve Sad'i kaliteli sekilde sinirla
        cap = MAX_HAPPY_SAD if our_label in ("Happy", "Sad") else len(images)
        selected = random.sample(images, min(len(images), cap))
        kido_counts[our_label] = len(selected)

        for i, path in enumerate(selected):
            fname = Path(path).stem
            kido_rows.append({
                "sample_id":  f"kido_{kido_cls[:2]}_{i:05d}",
                "image_path": path,
                "label":      our_label,
                "label_id":   label_id,
                "split":      "train",
                "source":     "kido",
                "confidence": 1.0,
            })

    kido_df = pd.DataFrame(kido_rows)
    print(f"[kido] {len(kido_df)} ornek: {kido_counts}")

    # 3. Birlestir
    combined = pd.concat([qwen_df, kido_df], ignore_index=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_CSV, index=False)
    print(f"[save] {OUT_CSV}  ({len(combined)} satir)")

    train_df = combined[combined["split"] == "train"]
    report = {
        "qwen_samples":  len(qwen_df),
        "kido_selected": len(kido_df),
        "kido_per_label": kido_counts,
        "total_combined": len(combined),
        "train_total": int((combined["split"] == "train").sum()),
        "val_total":   int((combined["split"] == "val").sum()),
        "test_total":  int((combined["split"] == "test").sum()),
        "train_class_dist": {
            cls: int((train_df["label"] == cls).sum())
            for cls in ["Happy", "Sad", "Angry", "Fear"]
        },
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"[save] {OUT_REPORT}")
    print("\n=== KIDO MANIFEST OZETI ===")
    for k, v in report.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
