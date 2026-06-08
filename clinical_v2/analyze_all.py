"""
clinical_v2 — tum modellerin karsilastirmali analizi.

Karsilastirir:
  B6   : ResNet-50 gorsel-only (referans, en iyi onceki)
  M1   : gated fusion + standartlastirma (18 feat)
  CB1/2: Concept Bottleneck (18 feat) — B sigortasi
  V2_* : Concept Bottleneck (16 figur-farkinda v2 gosterge) — Yon C

En iyi v2 modeli ile B6 arasinda McNemar testi yapar.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from scipy.stats import chi2 as chi2_dist
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader
from torchvision import transforms

from clinical_v2.dataset_v2 import DrawingDatasetV2
from clinical_v2.feature_spec_v2 import NUM_FEATURES_V2
from src.data.dataset import SigLIPDrawingDataset
from src.models.concept_bottleneck_classifier import ConceptBottleneckClassifier
from src.models.flexible_classifier import FlexibleFusionClassifier

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CLASSES = ["Happy", "Sad", "Angry", "Fear"]
TF = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                         transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])


def show_table():
    rows = [
        ("B6  ResNet gorsel-only", "out/experiments_clean/B6/result.json"),
        ("M1  gated+standart(18)", "out/experiments_clean/M1/result.json"),
        ("CB1 bottleneck(18)", "out/experiments_clean/CB1/result.json"),
        ("CB2 hybrid(18)", "out/experiments_clean/CB2/result.json"),
        ("V2_CB1 bottleneck(16)", "out/experiments_v2/V2_CB1/result.json"),
        ("V2_CB2 hybrid(16)", "out/experiments_v2/V2_CB2/result.json"),
        ("V2_CB3 hybrid cw2(16)", "out/experiments_v2/V2_CB3/result.json"),
    ]
    print("%-26s %7s %7s | %6s %6s %6s %6s" % ("Model", "Mac.F1", "Acc", "Happy", "Sad", "Angry", "Fear"))
    print("-" * 80)
    for name, p in rows:
        if not Path(p).exists():
            print("%-26s  (henuz yok)" % name); continue
        r = json.load(open(p))
        pc = r["per_class_f1"]
        print("%-26s %7.4f %7.4f | %6.3f %6.3f %6.3f %6.3f" % (
            name, r["test_macro_f1"], r["test_acc"],
            pc["Happy"], pc["Sad"], pc["Angry"], pc["Fear"]))


def get_preds_v2(ckpt):
    ck = torch.load(ckpt, map_location=DEVICE, weights_only=False)
    m = ConceptBottleneckClassifier(backbone="resnet50", num_concepts=NUM_FEATURES_V2,
                                    mode=ck["mode"], pretrained=False).to(DEVICE)
    m.load_state_dict(ck["model_state"]); m.eval()
    ds = DrawingDatasetV2("out/real/manifest_sadaug.csv", "test", TF,
                          "out/real/features_v2.csv", "out/real/feature_stats_v2.json")
    ld = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)
    pr, tg = [], []
    with torch.no_grad():
        for b in ld:
            lo = m(b["image"].to(DEVICE))
            pr.extend(lo.argmax(1).cpu().tolist()); tg.extend(b["label"].tolist())
    return np.array(pr), np.array(tg)


def get_preds_b6():
    ck = torch.load("out/experiments_clean/B6/checkpoints/best.pt", map_location=DEVICE, weights_only=False)
    m = FlexibleFusionClassifier(backbone="resnet50", image_only=True, pretrained=False).to(DEVICE)
    m.load_state_dict(ck["model_state"]); m.eval()
    ds = SigLIPDrawingDataset("out/real/manifest_clean.csv", "test", transform=TF)
    ld = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)
    pr, tg = [], []
    with torch.no_grad():
        for b in ld:
            lo = m(b["image"].to(DEVICE), b["clinical_features"].to(DEVICE), b["clinical_validity"].to(DEVICE))
            pr.extend(lo.argmax(1).cpu().tolist()); tg.extend(b["label"].tolist())
    return np.array(pr), np.array(tg)


def mcnemar(a, b, t, mask=None):
    if mask is not None:
        a, b, t = a[mask], b[mask], t[mask]
    c1, c2 = (a == t), (b == t)
    bb = int(np.sum(~c1 & c2)); cc = int(np.sum(c1 & ~c2)); n = bb + cc
    if n < 1:
        return 1.0, bb, cc
    chi2 = (abs(bb - cc) - 1) ** 2 / n if n >= 25 else (bb - cc) ** 2 / max(n, 1)
    return float(1 - chi2_dist.cdf(chi2, df=1)), bb, cc


def main():
    print("=" * 80)
    print("  TUM MODELLER — Temiz Test Seti")
    print("=" * 80)
    show_table()

    # En iyi v2 modelini sec
    best_v2, best_f1 = None, -1
    for e in ["V2_CB1", "V2_CB2", "V2_CB3"]:
        p = f"out/experiments_v2/{e}/result.json"
        if Path(p).exists():
            f = json.load(open(p))["test_macro_f1"]
            if f > best_f1:
                best_f1, best_v2 = f, e
    if best_v2 is None:
        print("\nv2 modeli henuz yok.")
        return

    print(f"\nEn iyi v2 modeli: {best_v2} (F1={best_f1:.4f})")
    print("=" * 80)
    print(f"  McNemar: {best_v2} (figur-farkinda klinik) vs B6 (gorsel-only)")
    print("=" * 80)
    pv, tg = get_preds_v2(f"out/experiments_v2/{best_v2}/checkpoints/best.pt")
    p6, tg6 = get_preds_b6()
    # Test setleri ayni siralamada mi? ikisi de manifest test, ayni 775 ornek
    pg, bb, cc = mcnemar(pv, p6, tg)
    print(f"GENEL: v2-dogru/B6-dogru +{cc}/-{bb}  p={pg:.4f}  -> {'ANLAMLI' if pg<0.05 else 'anlamli degil'}")
    for i, c in enumerate(CLASSES):
        mask = (tg == i)
        pv_, bb_, cc_ = mcnemar(pv, p6, tg, mask)
        print(f"  {c:<6} (n={int(mask.sum()):3d}): +{cc_}/-{bb_}  p={pv_:.4f} {'<-- anlamli' if pv_<0.05 else ''}")


if __name__ == "__main__":
    main()
