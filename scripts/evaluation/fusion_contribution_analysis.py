"""
Klinik Fuzyon Katki Analizi — Tez Bolum 4.2 icin ek kanit

Yapilan analizler:
  1. McNemar Testi : B3 vs B6 istatistiksel fark anlamsiz mi?
  2. Klinik Agirlikli F1 : Klinik oneme gore agirliklandirilmis metrik
  3. Guven Analizi : Angry/Fear dogru tahminlerinde B3 vs B6 guven karsilastirmasi
  4. Sinif Bazli Ozet Tablosu

Kullanim:
  python -m scripts.evaluation.fusion_contribution_analysis
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from scipy.stats import wilcoxon
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader
from torchvision import transforms

from src.data.dataset import SigLIPDrawingDataset
from src.models.flexible_classifier import FlexibleFusionClassifier

# ---------------------------------------------------------------------------
MANIFEST    = Path("out/real/manifest_clean.csv")
EXP_ROOT    = Path("out/experiments")
CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE  = 32

# Klinik agirlik: psikolog perspektifinden her sinifin klinik onemi
# Fear/Angry kacirmanin maliyeti Happy/Sad'den daha yuksek
CLINICAL_WEIGHTS = {
    "Happy": 0.15,
    "Sad":   0.20,
    "Angry": 0.30,
    "Fear":  0.35,
}
# ---------------------------------------------------------------------------


def load_model(exp_id: str) -> FlexibleFusionClassifier:
    result_path = EXP_ROOT / exp_id / "result.json"
    ckpt_path   = EXP_ROOT / exp_id / "checkpoints" / "best.pt"

    with open(result_path, encoding="utf-8") as f:
        cfg = json.load(f)

    model = FlexibleFusionClassifier(
        backbone=cfg["backbone"],
        num_classes=4,
        pretrained=False,
        image_only=cfg["image_only"],
    ).to(DEVICE)

    ckpt = torch.load(ckpt_path, map_location=DEVICE, weights_only=False)
    state = ckpt.get("model_state", ckpt)
    model.load_state_dict(state)
    model.eval()
    return model


def get_test_loader() -> DataLoader:
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    ds = SigLIPDrawingDataset(MANIFEST, "test", transform=tf)
    return DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)


def run_inference(model: FlexibleFusionClassifier, loader: DataLoader):
    """Tum test seti uzerinde tahmin ve olasilik dondurur."""
    all_preds  = []
    all_probs  = []
    all_labels = []

    with torch.no_grad():
        for batch in loader:
            img   = batch["image"].to(DEVICE)
            clin  = batch["clinical_features"].to(DEVICE)
            val_  = batch["clinical_validity"].to(DEVICE)
            y     = batch["label"]

            logits = model(img, clin, val_)
            probs  = F.softmax(logits, dim=-1)

            all_preds.extend(logits.argmax(1).cpu().tolist())
            all_probs.extend(probs.cpu().tolist())
            all_labels.extend(y.tolist())

    return (
        np.array(all_preds),
        np.array(all_probs),
        np.array(all_labels),
    )


def mcnemar_test(preds_b3: np.ndarray, preds_b6: np.ndarray,
                  labels: np.ndarray) -> dict:
    """
    McNemar testi: iki modelin hatalarinin istatistiksel olarak
    birbirinden farkli olup olmadigini test eder.
    H0: iki modelin hata oruntuleri arasinda anlamli fark yok.
    """
    correct_b3 = (preds_b3 == labels)
    correct_b6 = (preds_b6 == labels)

    # B6 dogru B3 yanlis (b), B3 dogru B6 yanlis (c)
    b = int(np.sum(~correct_b3 & correct_b6))
    c = int(np.sum(correct_b3 & ~correct_b6))

    # Wilcoxon signed-rank (McNemar icin n>25 durumunda ki-kare yaklasimi)
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "n": 0, "chi2": 0.0, "p_value": 1.0,
                "significant": False}

    # McNemar chi-kare (devamlılık düzeltmesiz)
    chi2 = (abs(b - c) - 1) ** 2 / (b + c) if n >= 25 else (b - c) ** 2 / (b + c)
    # chi2 df=1 icin p-value
    from scipy.stats import chi2 as chi2_dist
    p_value = 1 - chi2_dist.cdf(chi2, df=1)

    return {
        "b (B6 dogru, B3 yanlis)": b,
        "c (B3 dogru, B6 yanlis)": c,
        "n (toplam farkli)": n,
        "chi2": round(chi2, 4),
        "p_value": round(p_value, 4),
        "significant (p<0.05)": bool(p_value < 0.05),
        "yorum": ("ANLAMLI fark var" if p_value < 0.05
                  else "Anlamli fark YOK -- iki model esdeğer"),
    }


def clinical_weighted_f1(preds: np.ndarray, labels: np.ndarray) -> dict:
    """Her sinif icin ayri F1 hesapla, klinik agirlikla birlestir."""
    per_class = f1_score(labels, preds, average=None, zero_division=0)
    weighted  = sum(
        CLINICAL_WEIGHTS[cls] * per_class[i]
        for i, cls in enumerate(CLASSES)
    )
    return {cls: round(per_class[i], 4) for i, cls in enumerate(CLASSES)} | {
        "klinik_agirlikli_f1": round(weighted, 4),
    }


def confidence_analysis(preds: np.ndarray, probs: np.ndarray,
                         labels: np.ndarray, class_idx: int,
                         class_name: str) -> dict:
    """
    Belirli bir sinif icin dogru tahmin edilen orneklerde
    ortalama guven karsilastirmasi.
    """
    mask = (preds == class_idx) & (labels == class_idx)
    if mask.sum() == 0:
        return {"dogru_tahmin_sayisi": 0, "ort_guven": None}

    confidences = probs[mask, class_idx]
    return {
        "dogru_tahmin_sayisi": int(mask.sum()),
        "ort_guven": round(float(confidences.mean()), 4),
        "std_guven": round(float(confidences.std()), 4),
        "min_guven": round(float(confidences.min()), 4),
        "max_guven": round(float(confidences.max()), 4),
    }


def print_separator(title: str = "") -> None:
    line = "=" * 60
    if title:
        print(f"\n{line}")
        print(f"  {title}")
        print(line)
    else:
        print(line)


def main() -> None:
    print(f"Cihaz: {DEVICE}")
    print("Modeller yukleniyor...")

    model_b3 = load_model("B3")
    model_b6 = load_model("B6")
    loader   = get_test_loader()

    print("Test seti uzerinde tahmin yapiliyor...")
    preds_b3, probs_b3, labels = run_inference(model_b3, loader)
    preds_b6, probs_b6, _      = run_inference(model_b6, loader)

    n_test = len(labels)

    # ------------------------------------------------------------------
    print_separator("1. GENEL PERFORMANS OZETI")
    macro_b3 = f1_score(labels, preds_b3, average="macro", zero_division=0)
    macro_b6 = f1_score(labels, preds_b6, average="macro", zero_division=0)
    acc_b3   = (preds_b3 == labels).mean()
    acc_b6   = (preds_b6 == labels).mean()

    print(f"{'Model':<30} {'Makro F1':>10} {'Dogruluk':>10}")
    print("-" * 52)
    print(f"{'B3 ResNet-50 + Klinik':<30} {macro_b3:>10.4f} {acc_b3:>10.4f}")
    print(f"{'B6 ResNet-50 (gorsel-only)':<30} {macro_b6:>10.4f} {acc_b6:>10.4f}")
    print(f"{'Delta (B3 - B6)':<30} {macro_b3-macro_b6:>+10.4f} {acc_b3-acc_b6:>+10.4f}")

    # ------------------------------------------------------------------
    print_separator("2. MCNEMAR TESTI (B3 vs B6)")
    mc = mcnemar_test(preds_b3, preds_b6, labels)
    for k, v in mc.items():
        print(f"  {k}: {v}")

    # ------------------------------------------------------------------
    print_separator("3. KLINIK AGIRLIKLI F1 METRIGI")
    print(f"  Agirliklar: Happy={CLINICAL_WEIGHTS['Happy']}, "
          f"Sad={CLINICAL_WEIGHTS['Sad']}, "
          f"Angry={CLINICAL_WEIGHTS['Angry']}, "
          f"Fear={CLINICAL_WEIGHTS['Fear']}")
    print()

    cw_b3 = clinical_weighted_f1(preds_b3, labels)
    cw_b6 = clinical_weighted_f1(preds_b6, labels)

    print(f"{'Sinif':<12} {'B3 F1':>10} {'B6 F1':>10} {'Delta':>10}")
    print("-" * 44)
    for cls in CLASSES:
        delta = cw_b3[cls] - cw_b6[cls]
        print(f"{cls:<12} {cw_b3[cls]:>10.4f} {cw_b6[cls]:>10.4f} {delta:>+10.4f}")
    print("-" * 44)
    delta_cw = cw_b3["klinik_agirlikli_f1"] - cw_b6["klinik_agirlikli_f1"]
    print(f"{'AGIRLIKLI':12} {cw_b3['klinik_agirlikli_f1']:>10.4f} "
          f"{cw_b6['klinik_agirlikli_f1']:>10.4f} {delta_cw:>+10.4f}")

    if cw_b3["klinik_agirlikli_f1"] > cw_b6["klinik_agirlikli_f1"]:
        print("\n  >>> Klinik agirlikli metrikte B3 > B6: fuzyon klinik acidan daha iyi!")
    else:
        print("\n  >>> Klinik agirlikli metrikte B3 <= B6.")

    # ------------------------------------------------------------------
    print_separator("4. GUVEN ANALIZI — ANGRY ve FEAR DOGRU TAHMINLERI")

    for cls_idx, cls_name in [(2, "Angry"), (3, "Fear")]:
        print(f"\n  {cls_name} sinifi — dogru tahmin edilenlerde ortalama guven:")
        ca_b3 = confidence_analysis(preds_b3, probs_b3, labels, cls_idx, cls_name)
        ca_b6 = confidence_analysis(preds_b6, probs_b6, labels, cls_idx, cls_name)
        print(f"    B3 (n={ca_b3['dogru_tahmin_sayisi']}): "
              f"ort={ca_b3['ort_guven']}, std={ca_b3['std_guven']}")
        print(f"    B6 (n={ca_b6['dogru_tahmin_sayisi']}): "
              f"ort={ca_b6['ort_guven']}, std={ca_b6['std_guven']}")

        if ca_b3["ort_guven"] and ca_b6["ort_guven"]:
            diff = ca_b3["ort_guven"] - ca_b6["ort_guven"]
            print(f"    Delta: {diff:+.4f} ({'B3 daha guvenli' if diff > 0 else 'B6 daha guvenli'})")

    # ------------------------------------------------------------------
    print_separator("5. SONUC OZETI")
    print(f"  Test seti (n={n_test})")
    print(f"  {'Makro F1':<18}: B3={macro_b3:.4f}  B6={macro_b6:.4f}  Delta={macro_b3-macro_b6:+.4f}")
    print(f"  {'McNemar p-value':<18}: {mc['p_value']}  -- {mc['yorum']}")
    print(f"  {'Klinik Agirlikli':<18}: B3={cw_b3['klinik_agirlikli_f1']:.4f}  B6={cw_b6['klinik_agirlikli_f1']:.4f}  Delta={delta_cw:+.4f}")
    print(f"  {'Angry F1':<18}: B3={cw_b3['Angry']:.4f}  B6={cw_b6['Angry']:.4f}  Delta={cw_b3['Angry']-cw_b6['Angry']:+.4f}")
    print(f"  {'Fear F1':<18}: B3={cw_b3['Fear']:.4f}  B6={cw_b6['Fear']:.4f}  Delta={cw_b3['Fear']-cw_b6['Fear']:+.4f}")
    perc = (1 - 1282 / 1706) * 100
    print(f"  {'Egitim suresi':<18}: B3=1282s  B6=1706s  (B3 %{perc:.0f} daha hizli)")

    # JSON olarak kaydet
    out = {
        "mcnemar": mc,
        "clinical_weighted_f1_b3": cw_b3,
        "clinical_weighted_f1_b6": cw_b6,
        "macro_f1": {"b3": round(macro_b3, 4), "b6": round(macro_b6, 4)},
        "accuracy": {"b3": round(float(acc_b3), 4), "b6": round(float(acc_b6), 4)},
    }
    out_path = EXP_ROOT / "fusion_contribution_analysis.json"
    out_path.write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  Sonuclar kaydedildi: {out_path}")


if __name__ == "__main__":
    main()
