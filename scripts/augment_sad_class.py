"""
Sad sinifi icin SIZINTISIZ offline augmentation.

- Sadece TRAIN split'indeki Sad orijinallerinden uretim yapar (test/val asla).
- Uretilen goruntuler ayri klasore yazilir.
- Genisletilmis manifest + genisletilmis ozellik CSV uretir.

Kullanim:
  python -m scripts.augment_sad_class --target 2200
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import pandas as pd
from PIL import Image

from src.features.clinical_extractor import extract_clinical_features
from src.features.feature_spec import FEATURE_NAMES

MANIFEST     = Path("out/real/manifest_clean.csv")
FEATURES     = Path("out/real/features_clinical.csv")
AUG_DIR      = Path("Dataset/augmented_dataset/sad_aug")
OUT_MANIFEST = Path("out/real/manifest_sadaug.csv")
OUT_FEATURES = Path("out/real/features_sadaug.csv")


def build_pipeline() -> A.Compose:
    return A.Compose([
        A.Rotate(limit=12, border_mode=cv2.BORDER_REFLECT_101, p=0.8),
        A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
        A.HueSaturationValue(hue_shift_limit=8, sat_shift_limit=15, val_shift_limit=12, p=0.5),
        A.GaussNoise(std_range=(0.02, 0.08), p=0.3),
        A.RandomResizedCrop(size=(362, 512), scale=(0.88, 1.0),
                            ratio=(512/362*0.95, 512/362*1.05), p=0.4),
    ])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=2200,
                    help="Train Sad hedef ornek sayisi (orijinal + augment)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    mani = pd.read_csv(MANIFEST)
    feat = pd.read_csv(FEATURES)

    # Train split'indeki Sad orijinalleri (augmented olmayan)
    train_sad = mani[(mani.split == "train") & (mani.label == "sad")].copy()
    orig_sad = train_sad[~train_sad.sample_id.str.startswith("aug")]
    print(f"Train Sad toplam: {len(train_sad)}  (orijinal: {len(orig_sad)})")

    target = args.target
    needed = target - len(train_sad)
    if needed <= 0:
        print(f"Zaten yeterli ({len(train_sad)} >= {target}).")
        return

    print(f"Uretilecek augment: {needed}")
    AUG_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = build_pipeline()

    # Orijinal Sad goruntulerini yukle
    src_rows = orig_sad.to_dict("records")
    images = []
    for r in src_rows:
        try:
            images.append((r["sample_id"], np.array(Image.open(r["image_path"]).convert("RGB"))))
        except Exception:
            pass

    new_mani_rows = []
    new_feat_rows = []
    i = 0
    while len(new_mani_rows) < needed:
        sid, img = images[i % len(images)]
        aug = pipeline(image=img)["image"]
        aug_id = f"sadaug{len(new_mani_rows)+1:04d}_{sid}"
        out_path = AUG_DIR / f"{aug_id}.jpg"
        Image.fromarray(aug).save(out_path, quality=92)

        # Klinik ozellik cikar
        vals, valids = extract_clinical_features(Image.fromarray(aug))
        frow = {"sample_id": aug_id}
        for j, name in enumerate(FEATURE_NAMES):
            frow[name] = float(vals[j]) if valids[j] == 1.0 else float("nan")
            frow[f"{name}_valid"] = int(valids[j])
        new_feat_rows.append(frow)

        new_mani_rows.append({
            "sample_id": aug_id,
            "image_path": str(out_path.resolve()),
            "label": "sad",
            "label_id": 1,
            "split": "train",
        })
        i += 1
        if len(new_mani_rows) % 100 == 0:
            print(f"  {len(new_mani_rows)}/{needed}")

    # Birlestir ve kaydet
    ext_mani = pd.concat([mani, pd.DataFrame(new_mani_rows)], ignore_index=True)
    ext_feat = pd.concat([feat, pd.DataFrame(new_feat_rows)], ignore_index=True)
    ext_mani.to_csv(OUT_MANIFEST, index=False)
    ext_feat.to_csv(OUT_FEATURES, index=False)

    print(f"\nKaydedildi:")
    print(f"  {OUT_MANIFEST}  (toplam {len(ext_mani)})")
    print(f"  {OUT_FEATURES}")
    new_train_sad = ext_mani[(ext_mani.split=='train') & (ext_mani.label=='sad')]
    print(f"  Yeni train Sad: {len(new_train_sad)}")
    print(f"  Test/val Sad degismedi: test={len(ext_mani[(ext_mani.split=='test')&(ext_mani.label=='sad')])}, "
          f"val={len(ext_mani[(ext_mani.split=='val')&(ext_mani.label=='sad')])}")


if __name__ == "__main__":
    main()
