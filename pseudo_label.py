"""
pseudo_label.py

SigLIP_4Class_Filtered_045 görüntülerini V1 modeli ile skorlar.
Confidence >= THRESHOLD olanlara pseudo-label atar ve manifest_expanded.csv üretir.

Çıktı:
  out/manifest_expanded.csv  — qwen orijinal 1408 + pseudo-labeled N
  out/pseudo_label_report.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms

from src.models.fusion_classifier import ClinicalFusionClassifier
from src.features.feature_spec import NUM_FEATURES

# ── Config ────────────────────────────────────────────────────────────────────
CKPT        = Path("out/qwen_run/checkpoints/best.pt")
MANIFEST    = Path("out/manifest_qwen.csv")
SIGLIP_ROOT = Path("Dataset/Images/Emotion_SigLIP_4Class_Filtered_045")
OUT_CSV     = Path("out/manifest_expanded.csv")
OUT_REPORT  = Path("out/pseudo_label_report.json")
THRESHOLD   = 0.70
BATCH       = 64
NUM_WORKERS = 0
CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"


# ── Model ─────────────────────────────────────────────────────────────────────
def build_model(ckpt_path: Path):
    net = ClinicalFusionClassifier(num_classes=4, pretrained=False)
    ckpt = torch.load(ckpt_path, map_location=DEVICE)
    state = ckpt.get("model_state", ckpt)
    net.load_state_dict(state, strict=True)
    net.eval()
    return net.to(DEVICE)


# ── Transform ─────────────────────────────────────────────────────────────────
MEAN = [0.485, 0.456, 0.406]
STD  = [0.229, 0.224, 0.225]

def val_tf():
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])


# ── Collect SigLIP images not in qwen manifest ───────────────────────────────
def collect_new_images(manifest_df: pd.DataFrame) -> list[dict]:
    qwen_paths = set(manifest_df["image_path"].str.lower().tolist())
    new_images = []
    for split in ["train", "test"]:
        for cls in ["Angry", "Fear", "Happy", "Sad"]:
            d = SIGLIP_ROOT / split / cls
            if not d.is_dir():
                continue
            for fname in d.iterdir():
                if fname.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                    continue
                abs_path = str(fname.resolve())
                if abs_path.lower() in qwen_paths:
                    continue
                new_images.append({"image_path": abs_path, "true_class": cls})
    return new_images


# ── Inference in batches ──────────────────────────────────────────────────────
def score_images(model, images: list[dict], tf) -> list[dict]:
    results = []
    n = len(images)
    for i in range(0, n, BATCH):
        batch_meta = images[i: i + BATCH]
        tensors = []
        valid_meta = []
        for meta in batch_meta:
            try:
                img = Image.open(meta["image_path"]).convert("RGB")
                tensors.append(tf(img))
                valid_meta.append(meta)
            except Exception:
                continue
        if not tensors:
            continue
        x = torch.stack(tensors).to(DEVICE)
        B = x.size(0)
        zeros_clin = torch.zeros(B, NUM_FEATURES, device=DEVICE)
        zeros_val  = torch.zeros(B, NUM_FEATURES, device=DEVICE)
        with torch.no_grad():
            logits = model(x, zeros_clin, zeros_val)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        for meta, p in zip(valid_meta, probs):
            pred_id = int(np.argmax(p))
            conf = float(p[pred_id])
            results.append({
                "image_path": meta["image_path"],
                "true_class": meta["true_class"],
                "pred_label": CLASSES[pred_id],
                "pred_label_id": pred_id,
                "confidence": conf,
                "probs": p.tolist(),
            })
        done = min(i + BATCH, n)
        print(f"  scored {done}/{n}", end="\r", flush=True)
    print()
    return results


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"[init] device={DEVICE}  threshold={THRESHOLD}")

    # Load original manifest
    qwen_df = pd.read_csv(MANIFEST)
    print(f"[qwen] {len(qwen_df)} original samples")

    # Collect new images
    print("[siglip] collecting new images …")
    new_images = collect_new_images(qwen_df)
    print(f"[siglip] found {len(new_images)} images not in qwen manifest")

    # Load model
    print(f"[model] loading {CKPT} …")
    model = build_model(CKPT)

    # Score
    print("[score] running inference …")
    tf = val_tf()
    scored = score_images(model, new_images, tf)
    print(f"[score] scored {len(scored)} images")

    # Filter by threshold
    accepted = [r for r in scored if r["confidence"] >= THRESHOLD]
    rejected = [r for r in scored if r["confidence"] < THRESHOLD]
    print(f"[filter] accepted={len(accepted)}  rejected={len(rejected)}")

    # Class distribution of accepted
    from collections import Counter
    class_dist = Counter(r["pred_label"] for r in accepted)
    print(f"[filter] class distribution: {dict(class_dist)}")

    # Build pseudo rows
    pseudo_rows = []
    for r in accepted:
        fname = Path(r["image_path"]).stem
        pseudo_rows.append({
            "sample_id":  f"pseudo_{fname}",
            "image_path": r["image_path"],
            "label":      r["pred_label"],
            "label_id":   r["pred_label_id"],
            "split":      "train",   # pseudo samples go to train only
            "source":     "pseudo",
            "confidence": r["confidence"],
        })

    # Add source column to original qwen rows
    qwen_df = qwen_df.copy()
    qwen_df["source"] = "qwen"
    qwen_df["confidence"] = 1.0

    pseudo_df = pd.DataFrame(pseudo_rows)

    # Combine
    expanded_df = pd.concat([qwen_df, pseudo_df], ignore_index=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    expanded_df.to_csv(OUT_CSV, index=False)
    print(f"[save] {OUT_CSV}  ({len(expanded_df)} rows)")

    # Report
    report = {
        "threshold": THRESHOLD,
        "siglip_total": len(new_images),
        "siglip_scored": len(scored),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "class_distribution_accepted": dict(class_dist),
        "original_qwen_samples": len(qwen_df),
        "total_expanded_samples": len(expanded_df),
        "train_samples": int((expanded_df["split"] == "train").sum()),
        "val_samples":   int((expanded_df["split"] == "val").sum()),
        "test_samples":  int((expanded_df["split"] == "test").sum()),
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[save] {OUT_REPORT}")
    print("\n=== PSEUDO-LABEL SUMMARY ===")
    for k, v in report.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
