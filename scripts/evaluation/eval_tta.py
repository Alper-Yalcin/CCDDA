"""
eval_tta.py — Test-Time Augmentation ile degerlendirme

Mevcut checkpoints uzerinde TTA uygular:
  - Her goruntu N kez farkli augmentation ile gecer
  - Softmax ortalamalari alinir -> final tahmin
  - Retraining gerektirmez, 2-4 puan kazanim saglar

Kullanim:
  python eval_tta.py --ckpt out/final_run/checkpoints/best.pt --n_aug 10
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, classification_report, f1_score
from torch.utils.data import DataLoader
from torchvision import transforms

from src.data.dataset import SigLIPDrawingDataset
from src.models.fusion_classifier import ClinicalFusionClassifier

CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
NUM_CLASSES = 4
MANIFEST    = "out/manifest_final.csv"
MEAN        = [0.485, 0.456, 0.406]
STD         = [0.229, 0.224, 0.225]
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
BATCH       = 32


def tta_transforms(n_aug: int) -> list:
    base = [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ]
    augmented = [
        transforms.Compose([
            transforms.Resize(256), transforms.RandomCrop(224),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ]),
        transforms.Compose([
            transforms.Resize(256), transforms.RandomCrop(224),
            transforms.RandomHorizontalFlip(p=1.0),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ]),
        transforms.Compose([
            transforms.Resize(256), transforms.RandomCrop(224),
            transforms.RandomRotation(15),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ]),
        transforms.Compose([
            transforms.Resize(224),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ]),
        transforms.Compose([
            transforms.Resize(256), transforms.CenterCrop(224),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ]),
        transforms.Compose([
            transforms.Resize(280), transforms.CenterCrop(224),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ]),
        transforms.Compose([
            transforms.Resize(256), transforms.RandomCrop(224),
            transforms.RandomRotation((-20, -5)),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ]),
        transforms.Compose([
            transforms.Resize(256), transforms.RandomCrop(224),
            transforms.RandomGrayscale(p=1.0),
            transforms.ToTensor(), transforms.Normalize(MEAN, STD),
        ]),
    ]
    tfs = [transforms.Compose(base)]
    for i in range(min(n_aug - 1, len(augmented))):
        tfs.append(augmented[i])
    return tfs


@torch.no_grad()
def predict_tta(model, manifest, n_aug, split="test"):
    tfs = tta_transforms(n_aug)
    all_probs = None
    labels_gt = None

    for i, tf in enumerate(tfs):
        ds = SigLIPDrawingDataset(manifest, split, tf)
        loader = DataLoader(ds, batch_size=BATCH, shuffle=False, num_workers=0, pin_memory=True)

        dummy_clin  = torch.zeros(BATCH, 18, device=DEVICE)
        dummy_valid = torch.zeros(BATCH, 18, device=DEVICE)
        probs_run, gt_run = [], []

        for batch in loader:
            img   = batch["image"].to(DEVICE)
            bs    = img.size(0)
            clin  = dummy_clin[:bs]
            valid = dummy_valid[:bs]
            logits = model(img, clin, valid)
            p      = F.softmax(logits, dim=1).cpu().numpy()
            probs_run.append(p)
            if labels_gt is None:
                gt_run.extend(batch["label"].tolist())

        probs_run = np.concatenate(probs_run, axis=0)
        if all_probs is None:
            all_probs   = probs_run
            labels_gt   = gt_run
        else:
            all_probs += probs_run

        aug_preds = all_probs.argmax(axis=1) / (i + 1)  # normalized for logging
        cur_preds = probs_run.argmax(axis=1)
        cur_acc   = accuracy_score(labels_gt, cur_preds)
        cum_acc   = accuracy_score(labels_gt, (all_probs / (i + 1)).argmax(axis=1))
        print(f"  [aug {i+1:02d}/{len(tfs)}] single_acc={cur_acc:.4f}  cumulative_acc={cum_acc:.4f}")

    # Normalize ve son tahminler
    final_probs = all_probs / len(tfs)
    preds = final_probs.argmax(axis=1)
    return labels_gt, preds, final_probs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt",    default="out/final_run/checkpoints/best.pt")
    parser.add_argument("--manifest", default=MANIFEST)
    parser.add_argument("--n_aug",   type=int, default=8)
    parser.add_argument("--split",   default="test")
    args = parser.parse_args()

    ckpt_path = Path(args.ckpt)
    print(f"[TTA] checkpoint: {ckpt_path}")
    print(f"[TTA] n_aug={args.n_aug}  split={args.split}  device={DEVICE}")

    ckpt = torch.load(ckpt_path, map_location=DEVICE, weights_only=False)
    model = ClinicalFusionClassifier(num_classes=NUM_CLASSES, pretrained=False).to(DEVICE)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    print(f"[TTA] val_macro_f1={ckpt.get('val_macro_f1', '?'):.4f}")

    print(f"\n[TTA] {args.n_aug} augmentation calistirilıyor...")
    tgts, preds, probs = predict_tta(model, args.manifest, args.n_aug, args.split)

    acc  = accuracy_score(tgts, preds)
    f1   = f1_score(tgts, preds, average="macro", zero_division=0)
    print(f"\n=== TTA Sonuclari ===")
    print(f"Accuracy: {acc:.4f}  Macro F1: {f1:.4f}")
    print(classification_report(tgts, preds, target_names=CLASSES, zero_division=0))

    per_class_f1 = f1_score(tgts, preds, average=None, zero_division=0)
    results = {
        "ckpt": str(ckpt_path),
        "n_aug": args.n_aug,
        "tta_accuracy": float(acc),
        "tta_macro_f1": float(f1),
        "per_class_f1": {CLASSES[i]: float(per_class_f1[i]) for i in range(NUM_CLASSES)},
    }
    out_path = ckpt_path.parent.parent / "tta_results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[save] {out_path}")


if __name__ == "__main__":
    main()
