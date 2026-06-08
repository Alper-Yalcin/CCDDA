"""
Azınlık sınıfları (angry, fear) için offline data augmentation.

Strateji:
  - angry (359) ve fear (399) → her biri ~1100-1200 resme çıkar (3x)
  - happy ve sad'e dokunulmaz
  - Augmented resimler ayrı bir klasöre yazılır (orijinal dataset bozulmaz)
  - Her augmented dosya aug_{i}_{orijinal_isim}.jpg formatında kaydedilir

Uygulanan augmentationlar (klinik açıdan güvenli):
  ✓ Rotation ±15°          — kompozisyon korunur
  ✓ Brightness/Contrast     — renk analizi için gürültü ekler
  ✓ Gaussian Noise          — model robustluğu
  ✓ Random Crop + Resize    — hafif zoom efekti
  ✓ Color Jitter (HSV)      — renk varyasyonu
  ✗ Horizontal Flip         — kapalı (yön klinik anlam taşıyabilir)
  ✗ Vertical Flip           — kapalı (resmi bozar)
  ✗ Perspective Warp        — kapalı (kompozisyon bozulur)

Kullanım:
  python -m scripts.augment_minority_classes \
    --src Dataset/_ocuk__izimlerinden_Duygu_Durumu_Analizi_Veri_Seti-classification-export \
    --dst Dataset/augmented_dataset \
    --target-per-class 1100
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import albumentations as A
import cv2
import numpy as np
from PIL import Image


MINORITY_CLASSES = ["angry", "fear"]
ALL_CLASSES      = ["angry", "fear", "happy", "sad"]
VALID_EXTS       = {".jpg", ".jpeg", ".png", ".webp"}


def build_pipeline() -> A.Compose:
    """
    Klinik açıdan güvenli augmentation pipeline.
    Her transform kendi olasılığı ile uygulanır — her resim farklı kombinasyon alır.
    """
    return A.Compose([
        A.Rotate(limit=15, border_mode=cv2.BORDER_REFLECT_101, p=0.8),
        A.RandomBrightnessContrast(brightness_limit=0.25, contrast_limit=0.25, p=0.7),
        A.HueSaturationValue(
            hue_shift_limit=10,
            sat_shift_limit=20,
            val_shift_limit=15,
            p=0.6,
        ),
        A.GaussNoise(std_range=(0.02, 0.1), p=0.4),
        A.RandomResizedCrop(
            size=(362, 512),
            scale=(0.85, 1.0),
            ratio=(512/362 * 0.95, 512/362 * 1.05),
            p=0.5,
        ),
        A.Sharpen(alpha=(0.1, 0.3), lightness=(0.9, 1.1), p=0.3),
    ])


def load_image_np(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)


def save_image_np(arr: np.ndarray, path: Path) -> None:
    Image.fromarray(arr).save(path, quality=92)


def copy_class(src_dir: Path, dst_dir: Path) -> int:
    """Orijinal resimleri değiştirmeden kopyala."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in sorted(src_dir.iterdir()):
        if f.suffix.lower() in VALID_EXTS:
            import shutil
            shutil.copy2(f, dst_dir / f.name)
            count += 1
    return count


def augment_class(
    src_dir: Path,
    dst_dir: Path,
    target: int,
    seed: int,
) -> tuple[int, int]:
    """
    src_dir'deki resimleri önce kopyala, sonra target sayısına ulaşana kadar augment et.
    Returns: (orijinal_sayi, augmented_sayi)
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    random.seed(seed)
    np.random.seed(seed)

    files = sorted([f for f in src_dir.iterdir() if f.suffix.lower() in VALID_EXTS])
    orig_count = len(files)

    # Orijinalleri kopyala
    import shutil
    for f in files:
        shutil.copy2(f, dst_dir / f.name)

    if orig_count >= target:
        print(f"  Zaten yeterli ({orig_count} >= {target}), augmentation atlandı.")
        return orig_count, 0

    pipeline = build_pipeline()
    needed   = target - orig_count
    aug_count = 0
    idx = 0

    # Tüm orijinalleri önceden yükle (hız için)
    images = [load_image_np(f) for f in files]

    while aug_count < needed:
        src_img  = images[idx % len(images)]
        src_name = files[idx % len(files)].stem
        augmented = pipeline(image=src_img)["image"]
        out_name  = f"aug{aug_count+1:04d}_{src_name}.jpg"
        save_image_np(augmented, dst_dir / out_name)
        aug_count += 1
        idx += 1

    return orig_count, aug_count


def print_summary(dst_root: Path) -> None:
    print("\n=== Augmented Dataset Dağılımı ===")
    total = 0
    for cls in ALL_CLASSES:
        cls_dir = dst_root / cls
        if cls_dir.exists():
            count = len([f for f in cls_dir.iterdir() if f.suffix.lower() in VALID_EXTS])
            print(f"  {cls:<8}: {count}")
            total += count
    print(f"  {'TOPLAM':<8}: {total}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, type=Path,
                    help="Orijinal dataset klasörü")
    ap.add_argument("--dst", required=True, type=Path,
                    help="Augmented dataset çıktı klasörü")
    ap.add_argument("--target-per-class", type=int, default=1100,
                    help="Azınlık sınıflar için hedef resim sayısı (default: 1100)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if not args.src.is_dir():
        print(f"[ERR] src bulunamadı: {args.src}", file=sys.stderr)
        return 2

    args.dst.mkdir(parents=True, exist_ok=True)

    for cls in ALL_CLASSES:
        src_cls = args.src / cls
        dst_cls = args.dst / cls

        if not src_cls.is_dir():
            print(f"[WARN] Klasör yok, atlandı: {src_cls}", file=sys.stderr)
            continue

        if cls in MINORITY_CLASSES:
            print(f"[{cls}] Augmentation basliyor -> hedef: {args.target_per_class}")
            orig, aug = augment_class(src_cls, dst_cls, args.target_per_class, args.seed)
            print(f"  Orijinal: {orig}  |  Augmented: {aug}  |  Toplam: {orig + aug}")
        else:
            print(f"[{cls}] Kopyalanıyor (augmentation yok)...")
            count = copy_class(src_cls, dst_cls)
            print(f"  {count} resim kopyalandı")

    print_summary(args.dst)
    return 0


if __name__ == "__main__":
    sys.exit(main())
