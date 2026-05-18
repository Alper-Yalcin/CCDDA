"""
build_manifest_expanded.py

dataset_qwen_selected (1,408 orijinal) +
Emotion_SigLIP_4Class_Filtered_045 (8,345 ek görüntü) birleştirip
manifest_expanded.csv üretir.

SigLIP veri seti zaten 0.45 güven eşiğiyle filtrelenmiş — klasör etiketleri
doğrudan kullanılır (pseudo-label yerine SigLIP folder label).

Strateji:
- Qwen orijinal örnekleri (train/val/test) olduğu gibi alınır.
- SigLIP görüntüleri yalnızca train'e eklenir.
- Sınıf dengesizliğini bastırmak için her SigLIP sınıfından en fazla
  MAX_PER_CLASS görüntü alınır.

Çıktı:
  out/manifest_expanded.csv
  out/expand_report.json
"""
from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
QWEN_MANIFEST = Path("out/manifest_qwen.csv")
SIGLIP_ROOT   = Path("Dataset/Images/Emotion_SigLIP_4Class_Filtered_045")
OUT_CSV       = Path("out/manifest_expanded.csv")
OUT_REPORT    = Path("out/expand_report.json")
SEED          = 42
MAX_PER_CLASS = 428    # SigLIP Angry sayısına eşitle → tam sınıf dengesi

LABEL_MAP = {
    "Angry": ("Angry", 2),
    "Fear":  ("Fear",  3),
    "Happy": ("Happy", 0),
    "Sad":   ("Sad",   1),
}


def main():
    random.seed(SEED)

    # 1. Qwen orijinal manifest
    qwen_df = pd.read_csv(QWEN_MANIFEST)
    qwen_df["source"] = "qwen"
    qwen_df["confidence"] = 1.0
    print(f"[qwen] {len(qwen_df)} samples  (train/val/test split preserved)")

    # Build set of existing paths to avoid duplicates
    existing_paths = set(qwen_df["image_path"].str.lower().tolist())

    # 2. Collect SigLIP images by class
    siglip_by_class: dict[str, list[str]] = defaultdict(list)
    for split in ["train", "test"]:
        for cls in ["Angry", "Fear", "Happy", "Sad"]:
            d = SIGLIP_ROOT / split / cls
            if not d.is_dir():
                continue
            for f in d.iterdir():
                if f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                    continue
                abs_p = str(f.resolve())
                if abs_p.lower() in existing_paths:
                    continue
                siglip_by_class[cls].append(abs_p)

    print("[siglip] available images per class:")
    for cls, imgs in sorted(siglip_by_class.items()):
        print(f"  {cls}: {len(imgs)}")

    # 3. Sample up to MAX_PER_CLASS per class
    siglip_rows = []
    for cls, imgs in siglip_by_class.items():
        label, label_id = LABEL_MAP[cls]
        selected = random.sample(imgs, min(len(imgs), MAX_PER_CLASS))
        for i, path in enumerate(selected):
            fname = Path(path).stem
            siglip_rows.append({
                "sample_id":  f"siglip_{cls[:2]}_{i:05d}_{fname[:8]}",
                "image_path": path,
                "label":      label,
                "label_id":   label_id,
                "split":      "train",
                "source":     "siglip",
                "confidence": 1.0,
            })

    siglip_df = pd.DataFrame(siglip_rows)
    print(f"\n[siglip] selected {len(siglip_df)} images (max {MAX_PER_CLASS}/class)")
    print("[siglip] selected per class:", dict(Counter(siglip_df["label"])))

    # 4. Combine
    expanded_df = pd.concat([qwen_df, siglip_df], ignore_index=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    expanded_df.to_csv(OUT_CSV, index=False)
    print(f"\n[save] {OUT_CSV}  ({len(expanded_df)} rows)")

    # 5. Report
    train_df = expanded_df[expanded_df["split"] == "train"]
    report = {
        "qwen_samples":    len(qwen_df),
        "siglip_selected": len(siglip_df),
        "siglip_per_class": {cls: int((siglip_df["label"] == cls).sum()) for cls in ["Happy","Sad","Angry","Fear"]},
        "total_expanded":  len(expanded_df),
        "train_total":     int((expanded_df["split"] == "train").sum()),
        "val_total":       int((expanded_df["split"] == "val").sum()),
        "test_total":      int((expanded_df["split"] == "test").sum()),
        "train_class_dist": {
            cls: int((train_df["label"] == cls).sum())
            for cls in ["Happy","Sad","Angry","Fear"]
        },
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[save] {OUT_REPORT}")

    print("\n=== EXPAND SUMMARY ===")
    for k, v in report.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
