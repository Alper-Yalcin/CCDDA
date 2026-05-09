"""
label_with_model.py — Dataset/Images/Emotion goruntuleri KIDO modeliyle etiketle

En iyi modelimiz (kido_run/best.pt, val F1=0.59) ile Dataset/Images/Emotion
altindaki tum goruntuleri 4 sinifla (Happy/Sad/Angry/Fear) etiketler.

Cikti: out/labels_model.csv
"""
from __future__ import annotations
import sys, json
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

TEACHER_CKPT = Path("out/kido_run/checkpoints/best.pt")
IMAGE_ROOT   = Path("Dataset/Images/Emotion")
OUT_CSV      = Path("out/labels_model.csv")
OUT_REPORT   = Path("out/labels_model_report.json")

CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES = 4
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
BATCH       = 64
IMG_EXTS    = {".jpg", ".jpeg", ".png", ".webp"}
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]

# Orijinal klasor etiketi -> bizim binary label (adim 4 icin sakla)
ORIG_LABEL_MAP = {"Happiness": "Happy", "Sadness": "Sad"}


class PathDataset(Dataset):
    def __init__(self, paths, transform):
        self.paths = paths
        self.tf = transform

    def __len__(self): return len(self.paths)

    def __getitem__(self, i):
        try:
            img = Image.open(self.paths[i]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224), 128)
        return self.tf(img), i


def main():
    print(f"[init] device={DEVICE}  KIDO modeli ile etiketleme")

    ckpt = torch.load(TEACHER_CKPT, map_location=DEVICE, weights_only=False)
    model = ClinicalFusionClassifier(num_classes=NUM_CLASSES, pretrained=False).to(DEVICE)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    print(f"[model] val_macro_f1={ckpt['val_macro_f1']:.4f}")

    tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD),
    ])

    # Tum goruntuleri topla
    all_paths, orig_labels, splits = [], [], []
    for split in ["train", "test"]:
        split_dir = IMAGE_ROOT / split
        if not split_dir.exists():
            continue
        for cls_dir in sorted(split_dir.iterdir()):
            if not cls_dir.is_dir():
                continue
            orig_lbl = cls_dir.name
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    all_paths.append(str(f.resolve()))
                    orig_labels.append(orig_lbl)
                    splits.append(split)

    print(f"[data] {len(all_paths)} goruntu bulundu")
    if not all_paths:
        print("[hata] Goruntu bulunamadi!")
        return 1

    ds = PathDataset(all_paths, tf)
    loader = DataLoader(ds, batch_size=BATCH, shuffle=False, num_workers=0, pin_memory=True)

    dummy_c = torch.zeros(BATCH, 18, device=DEVICE)
    dummy_v = torch.zeros(BATCH, 18, device=DEVICE)
    all_probs = []

    print(f"[score] {len(all_paths)} goruntu skorlaniyor...")
    with torch.no_grad():
        for i, (imgs, idxs) in enumerate(loader):
            bs = imgs.size(0)
            imgs = imgs.to(DEVICE)
            logits = model(imgs, dummy_c[:bs], dummy_v[:bs])
            probs  = F.softmax(logits, dim=1).cpu().numpy()
            all_probs.append(probs)
            if (i + 1) % 20 == 0:
                print(f"  {(i+1)*BATCH}/{len(all_paths)}")

    all_probs = np.concatenate(all_probs, axis=0)
    preds     = all_probs.argmax(axis=1)
    confs     = all_probs.max(axis=1)

    rows = []
    for i, (path, orig_lbl, split) in enumerate(zip(all_paths, orig_labels, splits)):
        pred_label    = CLASSES[preds[i]]
        pred_label_id = int(preds[i])
        conf          = float(confs[i])
        fname         = Path(path).stem
        rows.append({
            "sample_id":    f"model_{split}_{orig_lbl[:3].lower()}_{i:06d}",
            "image_path":   path,
            "orig_label":   orig_lbl,
            "orig_label_2": ORIG_LABEL_MAP.get(orig_lbl, orig_lbl),
            "split":        split,
            "label":        pred_label,
            "label_id":     pred_label_id,
            "confidence":   conf,
            "source":       "model_pseudo",
            "happy_prob":   float(all_probs[i][0]),
            "sad_prob":     float(all_probs[i][1]),
            "angry_prob":   float(all_probs[i][2]),
            "fear_prob":    float(all_probs[i][3]),
        })

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    report = {
        "total": len(df),
        "pred_dist":  {k: int(v) for k, v in df["label"].value_counts().items()},
        "orig_dist":  {k: int(v) for k, v in df["orig_label"].value_counts().items()},
        "conf_mean":  float(df["confidence"].mean()),
        "conf_over_70": int((df["confidence"] >= 0.70).sum()),
        "conf_over_80": int((df["confidence"] >= 0.80).sum()),
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n[save] {OUT_CSV}")
    print(f"Tahmin dagilimi: {report['pred_dist']}")
    print(f"Ortalama guven: {report['conf_mean']:.3f}")
    print(f"Guven>=0.70: {report['conf_over_70']}  >=0.80: {report['conf_over_80']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
