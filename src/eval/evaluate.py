"""
Test split degerlendirme:
  - metrics.json (accuracy, macro_f1, balanced_accuracy, per-class)
  - confusion_matrix.csv
  - predictions_test.csv (sample_id, true, pred, top1/2 conf, entropy, probs)
  - calibration.json (ECE 10-bin)
  - misclassified.csv, high_confidence_errors.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from torch.utils.data import DataLoader

from src.data.dataset import SigLIPDrawingDataset
from src.data.transforms import get_image_transforms
from src.models.fusion_classifier import ClinicalFusionClassifier


CLASSES = ["Happy", "Sad", "Angry", "Fear"]


def load_model(ckpt_path: Path, device: str) -> ClinicalFusionClassifier:
    state = torch.load(ckpt_path, map_location=device)
    model = ClinicalFusionClassifier(num_classes=4).to(device)
    model.load_state_dict(state["model_state"])
    model.eval()
    return model


def ece_score(probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> dict:
    confidences = probs.max(axis=1)
    predictions = probs.argmax(axis=1)
    accuracies = (predictions == labels).astype(np.float32)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    bins = []
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        mask = (confidences > lo) & (confidences <= hi) if i > 0 else (confidences >= lo) & (confidences <= hi)
        n_in = int(mask.sum())
        if n_in > 0:
            avg_conf = float(confidences[mask].mean())
            avg_acc = float(accuracies[mask].mean())
            ece += (n_in / len(probs)) * abs(avg_acc - avg_conf)
            bins.append({"bin": i, "lo": float(lo), "hi": float(hi), "n": n_in, "avg_conf": avg_conf, "avg_acc": avg_acc})
        else:
            bins.append({"bin": i, "lo": float(lo), "hi": float(hi), "n": 0, "avg_conf": 0.0, "avg_acc": 0.0})
    return {"ece": float(ece), "bins": bins}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--features", type=Path, default=None)
    ap.add_argument("--ckpt", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--split", type=str, default="test")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    _, val_tf = get_image_transforms(image_size=224)

    ds = SigLIPDrawingDataset(args.manifest, args.split, transform=val_tf, features_csv=args.features)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)
    print(f"[data] {args.split}={len(ds)}")

    model = load_model(args.ckpt, args.device)

    sample_ids: list[str] = []
    targets: list[int] = []
    all_probs: list[np.ndarray] = []
    with torch.no_grad():
        for batch in loader:
            img = batch["image"].to(args.device)
            clin = batch["clinical_features"].to(args.device)
            valid = batch["clinical_validity"].to(args.device)
            logits = model(img, clin, valid)
            probs = F.softmax(logits, dim=1).cpu().numpy()
            all_probs.append(probs)
            targets.extend(batch["label"].numpy().tolist())
            sample_ids.extend(batch["sample_id"])

    probs = np.concatenate(all_probs, axis=0)
    targets_arr = np.array(targets)
    preds = probs.argmax(axis=1)

    # metrikler
    acc = float(accuracy_score(targets_arr, preds))
    macro = float(f1_score(targets_arr, preds, average="macro", zero_division=0))
    balanced = float(balanced_accuracy_score(targets_arr, preds))
    p, r, f, sup = precision_recall_fscore_support(targets_arr, preds, labels=list(range(4)), zero_division=0)
    per_class = []
    for i, name in enumerate(CLASSES):
        per_class.append({
            "label": name,
            "precision": float(p[i]),
            "recall": float(r[i]),
            "f1": float(f[i]),
            "support": int(sup[i]),
        })

    metrics = {
        "split": args.split,
        "n": len(targets_arr),
        "accuracy": acc,
        "macro_f1": macro,
        "balanced_accuracy": balanced,
        "per_class": per_class,
    }
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # confusion matrix
    cm = confusion_matrix(targets_arr, preds, labels=list(range(4)))
    cm_df = pd.DataFrame(cm, index=[f"true_{c}" for c in CLASSES], columns=[f"pred_{c}" for c in CLASSES])
    cm_df.to_csv(args.out / "confusion_matrix.csv")

    # per-sample
    sorted_probs = np.sort(probs, axis=1)
    top1 = sorted_probs[:, -1]
    top2 = sorted_probs[:, -2]
    eps = 1e-12
    entropy = -np.sum(probs * np.log(probs + eps), axis=1)

    pred_df = pd.DataFrame({
        "sample_id": sample_ids,
        "true_label_id": targets_arr,
        "true_label": [CLASSES[i] for i in targets_arr],
        "pred_label_id": preds,
        "pred_label": [CLASSES[i] for i in preds],
        "top1_conf": top1,
        "top2_conf": top2,
        "entropy": entropy,
        "prob_Happy": probs[:, 0],
        "prob_Sad": probs[:, 1],
        "prob_Angry": probs[:, 2],
        "prob_Fear": probs[:, 3],
        "correct": (preds == targets_arr).astype(int),
    })
    pred_df.to_csv(args.out / f"predictions_{args.split}.csv", index=False)

    # calibration
    cal = ece_score(probs, targets_arr, n_bins=10)
    (args.out / "calibration.json").write_text(json.dumps(cal, indent=2), encoding="utf-8")

    # error analysis
    misc = pred_df[pred_df["correct"] == 0]
    misc.to_csv(args.out / "misclassified.csv", index=False)
    high_conf_err = misc[misc["top1_conf"] >= 0.85]
    high_conf_err.to_csv(args.out / "high_confidence_errors.csv", index=False)

    print(f"\n[metrics] acc={acc:.4f} macro_f1={macro:.4f} balanced_acc={balanced:.4f} ECE={cal['ece']:.4f}")
    print("[per-class]")
    for pc in per_class:
        print(f"  {pc['label']:<8} P={pc['precision']:.3f} R={pc['recall']:.3f} F1={pc['f1']:.3f} (n={pc['support']})")
    print(f"\nCikti: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
