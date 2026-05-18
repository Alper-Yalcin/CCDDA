"""
build_manifest_final.py

manifest_v2.csv (gercek etiketli) + pseudo_v2.csv (ogretmen etiketli) birlestirip
manifest_final.csv olusturur.

Sinif dengesi icin her siniftan max MAX_PER_CLASS ornek alinir.
Oncelik sirasi: guven (yuksekten dusuge).

Cikti: out/manifest_final.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

MANIFEST_V2  = Path("out/manifest_kido.csv")   # Temel: KIDO+qwen (en iyi model)
PSEUDO_V2    = Path("out/pseudo_v2.csv")        # Ekstra: SigLIP pseudo-labels
OUT_CSV      = Path("out/manifest_final.csv")
OUT_REPORT   = Path("out/manifest_final_report.json")
MAX_PER_CLASS = 2000   # sinif basi maksimum egitim ornegi
CLASSES       = ["Happy", "Sad", "Angry", "Fear"]


def main():
    v2 = pd.read_csv(MANIFEST_V2)
    pseudo = pd.read_csv(PSEUDO_V2)

    print(f"[v2] {len(v2)} ornek")
    print(f"[pseudo] {len(pseudo)} ornek")

    combined = pd.concat([v2, pseudo], ignore_index=True)

    # Sadece train'i dengele; val/test dokunulmaz
    train = combined[combined["split"] == "train"].copy()
    val   = combined[combined["split"] == "val"].copy()
    test  = combined[combined["split"] == "test"].copy()

    # Guven kolonunu normalize et
    if "confidence" not in train.columns:
        train["confidence"] = 1.0

    # Her siniftan en guvenli MAX_PER_CLASS ornegi sec
    selected_parts = []
    for cls in CLASSES:
        cls_df = train[train["label"] == cls].sort_values("confidence", ascending=False)
        selected = cls_df.head(MAX_PER_CLASS)
        selected_parts.append(selected)
        print(f"  {cls}: {len(cls_df)} mevcut -> {len(selected)} secildi")

    balanced_train = pd.concat(selected_parts, ignore_index=True)
    final = pd.concat([balanced_train, val, test], ignore_index=True)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(OUT_CSV, index=False)

    train_dist = {k: int(v) for k, v in balanced_train["label"].value_counts().items()}
    source_dist = {k: int(v) for k, v in balanced_train["source"].value_counts().items()}
    report = {
        "total": int(len(final)),
        "train": int(len(balanced_train)),
        "val":   int(len(val)),
        "test":  int(len(test)),
        "train_class_dist": train_dist,
        "train_source_dist": source_dist,
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n[save] {OUT_CSV}  ({len(final)} satir)")
    print(f"  train={len(balanced_train)}  val={len(val)}  test={len(test)}")
    print(f"  sinif dagilimi: {train_dist}")
    print(f"  kaynak dagilimi: {source_dist}")


if __name__ == "__main__":
    main()
