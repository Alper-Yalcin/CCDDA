"""
pseudo_label_v2.py — Ogretmen ile KIDO + SigLIP pseudo-labeling

Ogretmen: out/teacher_run/checkpoints/best.pt
Kaynaklar:
  1. Dataset/Images/Emotion_4Class (KIDO) — tum siniflar
  2. Dataset/Images/Emotion_SigLIP_4Class_Filtered_045 (SigLIP)

Strateji:
  - KIDO Anger/Anxiety (kucuk siniflar): guven >= 0.55, hepsini al
  - KIDO Happy/Sadness (buyuk siniflar): guven >= 0.65, en fazla 800/sinif
  - SigLIP her sinif: guven >= 0.70, en fazla 700/sinif

Cikti: out/pseudo_v2.csv  +  out/pseudo_v2_report.json
"""
from __future__ import annotations

import json, random, sys
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from src.models.fusion_classifier import ClinicalFusionClassifier

# En iyi modelimiz KIDO run (val F1=0.59, test F1=0.52) ogretmen olarak kullanilir
TEACHER_CKPT = Path("out/kido_run/checkpoints/best.pt")
SIGLIP_ROOT  = Path("Dataset/Images/Emotion_SigLIP_4Class_Filtered_045")
EXISTING_CSV = Path("out/manifest_kido.csv")   # KIDO zaten mevcut
OUT_CSV      = Path("out/pseudo_v2.csv")
OUT_REPORT   = Path("out/pseudo_v2_report.json")

CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES = 4
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
BATCH       = 64
SEED        = 42
NUM_WORKERS = 0

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

SIGLIP_MAP = {
    "Angry": ("Angry", 2),
    "Fear":  ("Fear",  3),
    "Happy": ("Happy", 0),
    "Sad":   ("Sad",   1),
}

# SigLIP esikleri — ogretmen guclu oldugu icin daha yuksek esik guvenli
SIGLIP_THRESH      = 0.72
MAX_SIGLIP_PER_CLASS = 1200  # Her sinif icin max SigLIP ornegi

MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]


class ImagePathDataset(Dataset):
    def __init__(self, paths: list[str], transform):
        self.paths = paths
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        try:
            img = Image.open(self.paths[idx]).convert("RGB")
            return self.transform(img), idx
        except Exception:
            img = Image.new("RGB", (224, 224), (128, 128, 128))
            return self.transform(img), idx


def load_teacher() -> ClinicalFusionClassifier:
    ckpt = torch.load(TEACHER_CKPT, map_location=DEVICE, weights_only=False)
    model = ClinicalFusionClassifier(num_classes=NUM_CLASSES, pretrained=False).to(DEVICE)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    print(f"[teacher] val_macro_f1={ckpt['val_macro_f1']:.4f}")
    return model


@torch.no_grad()
def score_images(model, paths: list[str]) -> np.ndarray:
    """Goruntu listesini skorla, (N, NUM_CLASSES) softmax prob matrisi don."""
    tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    ds = ImagePathDataset(paths, tf)
    loader = DataLoader(ds, batch_size=BATCH, shuffle=False, num_workers=NUM_WORKERS)
    probs_list = []
    dummy_clin  = torch.zeros(BATCH, 18, device=DEVICE)
    dummy_valid = torch.zeros(BATCH, 18, device=DEVICE)

    for imgs, idxs in loader:
        bs = imgs.size(0)
        imgs = imgs.to(DEVICE)
        clin  = dummy_clin[:bs]
        valid = dummy_valid[:bs]
        logits = model(imgs, clin, valid)
        probs  = F.softmax(logits, dim=1).cpu().numpy()
        probs_list.append(probs)

    return np.concatenate(probs_list, axis=0)


def collect_images(root: Path, label_map: dict) -> dict[str, list[str]]:
    """Klasor -> goruntu yolu listesi sozlugu don."""
    result: dict[str, list[str]] = defaultdict(list)
    for split_dir in root.iterdir():
        if not split_dir.is_dir():
            continue
        for cls_dir in split_dir.iterdir():
            if not cls_dir.is_dir():
                continue
            if cls_dir.name not in label_map:
                continue
            for f in cls_dir.iterdir():
                if f.suffix.lower() in IMG_EXTS:
                    result[cls_dir.name].append(str(f.resolve()))
    return result


def main():
    random.seed(SEED)
    np.random.seed(SEED)

    if not TEACHER_CKPT.exists():
        print(f"[hata] Ogretmen checkpoint bulunamadi: {TEACHER_CKPT}")
        print("Once train_teacher.py calistirin.")
        return 1

    model = load_teacher()

    # Mevcut manifest yollarini cikart (tekrar eklememek icin)
    existing_paths: set[str] = set()
    if EXISTING_CSV.exists():
        ex = pd.read_csv(EXISTING_CSV)
        existing_paths = set(ex["image_path"].str.lower().tolist())
    print(f"[existing] {len(existing_paths)} goruntu zaten mevcut manifestte")

    all_rows: list[dict] = []
    report = {}

    # ── SigLIP ────────────────────────────────────────────────────────────────
    print("\n[siglip] Goruntular toplanıyor...")
    siglip_imgs = collect_images(SIGLIP_ROOT, SIGLIP_MAP)

    siglip_stats = {}
    for cls_name, paths in siglip_imgs.items():
        label, label_id = SIGLIP_MAP[cls_name]
        paths = [p for p in paths if p.lower() not in existing_paths]
        if not paths:
            siglip_stats[cls_name] = 0
            continue

        print(f"  [siglip/{cls_name}] {len(paths)} goruntu skorlaniyor...")
        probs = score_images(model, paths)
        max_probs  = probs.max(axis=1)
        pred_ids   = probs.argmax(axis=1)

        mask = (pred_ids == label_id) & (max_probs >= SIGLIP_THRESH)
        sel_idxs = np.where(mask)[0]

        if len(sel_idxs) > MAX_SIGLIP_PER_CLASS:
            top_k = np.argsort(max_probs[sel_idxs])[::-1][:MAX_SIGLIP_PER_CLASS]
            sel_idxs = sel_idxs[top_k]

        siglip_stats[cls_name] = len(sel_idxs)
        print(f"    -> {len(sel_idxs)} kabul edildi (threshold={SIGLIP_THRESH})")

        for rank, i in enumerate(sel_idxs):
            all_rows.append({
                "sample_id":  f"siglip_{cls_name[:3].lower()}_{rank:05d}",
                "image_path": paths[i],
                "label":      label,
                "label_id":   label_id,
                "split":      "train",
                "source":     "siglip_pseudo",
                "confidence": float(max_probs[i]),
            })

    report["siglip"] = siglip_stats
    report["siglip_total"] = sum(siglip_stats.values())

    # ── Kaydet ────────────────────────────────────────────────────────────────
    pseudo_df = pd.DataFrame(all_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    pseudo_df.to_csv(OUT_CSV, index=False)

    report["pseudo_total"] = len(pseudo_df)
    if len(pseudo_df) > 0:
        report["pseudo_class_dist"] = {k: int(v) for k, v in pseudo_df["label"].value_counts().items()}
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n[save] {OUT_CSV}  ({len(pseudo_df)} pseudo-label)")
    if len(pseudo_df) > 0:
        print(f"  sinif dagilimi: {report['pseudo_class_dist']}")
    print(f"  SigLIP toplam: {report['siglip_total']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
