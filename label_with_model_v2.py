"""
label_with_model_v2.py — Dataset/Images/Emotion goruntuleri model-labeled ile yeniden etiketle

Ogretmen: out/model_labeled_run/checkpoints/best.pt (Acc=%63.97, F1=0.59)
Cikti: out/labels_model_v2.csv
"""
from __future__ import annotations
import sys, json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from src.models.fusion_classifier import ClinicalFusionClassifier

TEACHER_CKPT = Path("out/model_labeled_run/checkpoints/best.pt")
IMAGE_ROOT   = Path("Dataset/Images/Emotion")
OUT_CSV      = Path("out/labels_model_v2.csv")
OUT_REPORT   = Path("out/labels_model_v2_report.json")

CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES = 4
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
BATCH       = 64
IMG_EXTS    = {".jpg", ".jpeg", ".png", ".webp"}
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]
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
    if not TEACHER_CKPT.exists():
        print(f"[hata] Checkpoint bulunamadi: {TEACHER_CKPT}")
        return 1

    print(f"[init] device={DEVICE}  ogretmen={TEACHER_CKPT}")

    ckpt = torch.load(TEACHER_CKPT, map_location=DEVICE, weights_only=False)
    model = ClinicalFusionClassifier(num_classes=NUM_CLASSES, pretrained=False).to(DEVICE)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    print(f"[model] val_macro_f1={ckpt.get('val_macro_f1', '?'):.4f}")

    tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224),
        transforms.ToTensor(), transforms.Normalize(MEAN, STD),
    ])

    all_paths, orig_labels, splits = [], [], []
    for split in ["train", "test"]:
        split_dir = IMAGE_ROOT / split
        if not split_dir.exists():
            continue
        for cls_dir in sorted(split_dir.iterdir()):
            if not cls_dir.is_dir():
                continue
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    all_paths.append(str(f.resolve()))
                    orig_labels.append(cls_dir.name)
                    splits.append(split)

    print(f"[data] {len(all_paths)} goruntu")

    ds = PathDataset(all_paths, tf)
    loader = DataLoader(ds, batch_size=BATCH, shuffle=False, num_workers=0, pin_memory=True)

    dummy_c = torch.zeros(BATCH, 18, device=DEVICE)
    all_probs = []

    print("[score] Skorlaniyor...")
    with torch.no_grad():
        for i, (imgs, _) in enumerate(loader):
            bs = imgs.size(0)
            imgs = imgs.to(DEVICE)
            logits = model(imgs, dummy_c[:bs], dummy_c[:bs])
            probs  = F.softmax(logits, dim=1).cpu().numpy()
            all_probs.append(probs)
            if (i + 1) % 20 == 0:
                print(f"  {min((i+1)*BATCH, len(all_paths))}/{len(all_paths)}")

    all_probs = np.concatenate(all_probs, axis=0)
    preds = all_probs.argmax(axis=1)
    confs = all_probs.max(axis=1)

    rows = []
    for i, (path, orig_lbl, split) in enumerate(zip(all_paths, orig_labels, splits)):
        rows.append({
            "sample_id":   f"modelv2_{split}_{orig_lbl[:3].lower()}_{i:06d}",
            "image_path":  path,
            "orig_label":  orig_lbl,
            "orig_label_2": ORIG_LABEL_MAP.get(orig_lbl, orig_lbl),
            "split":       split,
            "label":       CLASSES[preds[i]],
            "label_id":    int(preds[i]),
            "confidence":  float(confs[i]),
            "source":      "model_v2_pseudo",
            "happy_prob":  float(all_probs[i][0]),
            "sad_prob":    float(all_probs[i][1]),
            "angry_prob":  float(all_probs[i][2]),
            "fear_prob":   float(all_probs[i][3]),
        })

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    report = {
        "total": len(df),
        "pred_dist": {k: int(v) for k, v in df["label"].value_counts().items()},
        "conf_mean": float(df["confidence"].mean()),
        "conf_over_065": int((df["confidence"] >= 0.65).sum()),
        "conf_over_070": int((df["confidence"] >= 0.70).sum()),
        "conf_over_080": int((df["confidence"] >= 0.80).sum()),
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n[save] {OUT_CSV}")
    print(f"Tahmin dagilimi: {report['pred_dist']}")
    print(f"Guven ort: {report['conf_mean']:.3f}  >=0.65: {report['conf_over_065']}  >=0.70: {report['conf_over_070']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
