"""
Test seti uzerinde best.pt ile tam degerlendirme.
Kullanim: python eval_test.py <checkpoint.pt>
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import torch
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score,
)
from torch.utils.data import DataLoader
from torchvision import transforms

from src.data.dataset import SigLIPDrawingDataset
from src.models.fusion_classifier import ClinicalFusionClassifier

MANIFEST = Path("out/manifest_qwen.csv")
CLASSES   = ["Happy", "Sad", "Angry", "Fear"]
DEVICE    = "cuda" if torch.cuda.is_available() else "cpu"

def main():
    ckpt_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("out/qwen_run/checkpoints/best.pt")
    print(f"Checkpoint: {ckpt_path}")

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    test_ds = SigLIPDrawingDataset(MANIFEST, "test", transform=val_tf)
    loader  = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)

    model = ClinicalFusionClassifier(num_classes=4, pretrained=False).to(DEVICE)
    ckpt  = torch.load(ckpt_path, map_location=DEVICE)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    preds_all, tgts_all = [], []
    with torch.no_grad():
        for batch in loader:
            img  = batch["image"].to(DEVICE)
            clin = batch["clinical_features"].to(DEVICE)
            val_ = batch["clinical_validity"].to(DEVICE)
            y    = batch["label"]
            logits = model(img, clin, val_)
            preds_all.extend(logits.argmax(1).cpu().tolist())
            tgts_all.extend(y.tolist())

    acc  = accuracy_score(tgts_all, preds_all)
    prec = precision_score(tgts_all, preds_all, average="macro", zero_division=0)
    rec  = recall_score(tgts_all, preds_all, average="macro", zero_division=0)
    f1   = f1_score(tgts_all, preds_all, average="macro", zero_division=0)

    print(f"\nTest Accuracy : {acc:.4f}")
    print(f"Test Precision: {prec:.4f}")
    print(f"Test Recall   : {rec:.4f}")
    print(f"Test Macro F1 : {f1:.4f}")
    print()
    print(classification_report(tgts_all, preds_all, target_names=CLASSES, zero_division=0))
    print("Confusion matrix:")
    print(confusion_matrix(tgts_all, preds_all))

    results = {"accuracy": acc, "precision": prec, "recall": rec, "macro_f1": f1}
    out_json = ckpt_path.parent.parent / "test_results.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSonuclar: {out_json}")

if __name__ == "__main__":
    main()
