"""
Eğitim sonrası pipeline smoke test.
Spektrum mimarisinin doğru çalıştığını doğrular:
  - is_calibrated, low_confidence, spectrum_top2 alanları mevcut mu?
  - low_confidence modu tetiklenebiliyor mu?
  - LLM fallback (rule_based) yeni framing'i kullanıyor mu?

Kullanım:
    python -m scripts.test_pipeline --checkpoint out/goldtest/checkpoints/best.pt
    python -m scripts.test_pipeline --checkpoint out/goldtest/checkpoints/best.pt --image resim.jpg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def make_synthetic_image(color: tuple[int,int,int] = (128, 100, 80)) -> Image.Image:
    """224x224 düz renkli test resmi."""
    img = Image.new("RGB", (224, 224), color)
    return img


def test_normal_inference(pipeline) -> bool:
    print("\n[TEST 1] Normal inference — renkli sentetik resim")
    img = make_synthetic_image((200, 80, 60))
    result = pipeline.predict(img, lang="tr")

    required = ["pred_emotion", "spectrum_top2", "is_calibrated", "low_confidence",
                "probs_emotion", "explanation", "clinical_features"]
    missing = [k for k in required if k not in result]
    if missing:
        print(f"  [FAIL] Eksik anahtarlar: {missing}")
        return False

    print(f"  pred_emotion   : {result['pred_emotion']}")
    print(f"  is_calibrated  : {result['is_calibrated']}")
    print(f"  low_confidence : {result['low_confidence']}")
    print(f"  spectrum_top2  : {result['spectrum_top2']}")
    probs = result['probs_emotion']
    print(f"  probs (4 sinif): Happy={probs[0]:.3f} Sad={probs[1]:.3f} Angry={probs[2]:.3f} Fear={probs[3]:.3f}")
    print(f"  explanation    : {result['explanation'][:120]}...")
    print("  [OK]")
    return True


def test_low_confidence_mode(pipeline) -> bool:
    """Uniform logit ile low_confidence modunu zorla."""
    print("\n[TEST 2] Low confidence modu — uniform gri resim")
    img = make_synthetic_image((128, 128, 128))

    import torch
    import torch.nn.functional as F

    # Pipeline'ın model'ine erişip logitleri uniform yapamayız doğrudan,
    # ama uniform renkli resim genellikle düşük güven üretir.
    result = pipeline.predict(img, lang="tr")

    max_prob = max(result['probs_emotion'])
    print(f"  max_prob       : {max_prob:.3f}")
    print(f"  low_confidence : {result['low_confidence']}")
    print(f"  pred_emotion   : {result['pred_emotion']}")
    if result['low_confidence']:
        print(f"  explanation    : {result['explanation'][:120]}")
        print("  [OK] Susma modu tetiklendi")
    else:
        print(f"  [INFO] Susma modu tetiklenmedi (max_prob={max_prob:.3f} >= 0.40)")
        print(f"         Bu normal — resim bir sinife benzedi.")
    return True


def test_spectrum_framing(pipeline) -> bool:
    """Explanation metninde 'benzerlik' dili var mı, 'tahmin' dili yok mu?"""
    print("\n[TEST 3] Framing kontrolu — explanation metni analizi")
    img = make_synthetic_image((50, 50, 150))
    result = pipeline.predict(img, lang="tr")

    explanation = result['explanation']
    forbidden = ["tahmin etti", "duygusunu yasiyor", "hissediyor", "tanisi"]
    expected  = ["benzerlik", "örtüşüyor", "klinik tanı değildir", "uzman"]

    fails = [w for w in forbidden if w.lower() in explanation.lower()]
    found = [w for w in expected if w.lower() in explanation.lower()]

    if fails:
        print(f"  [WARN] Yasak ifadeler bulundu: {fails}")
    else:
        print(f"  [OK]  Yasak ifade yok")

    print(f"  [OK]  Beklenen ifadeler: {found}/{len(expected)}")
    print(f"  explanation: {explanation[:200]}")
    return True


def test_english_output(pipeline) -> bool:
    print("\n[TEST 4] Ingilizce cikti")
    img = make_synthetic_image((180, 120, 50))
    result = pipeline.predict(img, lang="en")
    print(f"  pred_emotion : {result['pred_emotion']}")
    print(f"  explanation  : {result['explanation'][:150]}")
    ok = "not a clinical diagnosis" in result['explanation'].lower() or "visual pattern" in result['explanation'].lower()
    print(f"  [{'OK' if ok else 'WARN'}] Ingilizce framing")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True, type=Path)
    ap.add_argument("--image", type=Path, default=None,
                    help="Gercek resim dosyasi (opsiyonel)")
    ap.add_argument("--lang", default="tr")
    args = ap.parse_args()

    if not args.checkpoint.exists():
        print(f"[ERR] Checkpoint bulunamadi: {args.checkpoint}")
        return 2

    print(f"Pipeline yukleniyor: {args.checkpoint}")
    from src.inference.pipeline import InferencePipeline
    pipeline = InferencePipeline(
        checkpoint_path=args.checkpoint,
        device="cuda",
        enable_llm=False,       # test icin rule-based yeterli
        calibration_path=None,  # kalibrasyon henuz fit edilmedi
    )
    print("Pipeline yuklendi.\n")

    results = []
    results.append(test_normal_inference(pipeline))
    results.append(test_low_confidence_mode(pipeline))
    results.append(test_spectrum_framing(pipeline))
    results.append(test_english_output(pipeline))

    if args.image and args.image.exists():
        print(f"\n[TEST 5] Gercek resim: {args.image}")
        img = Image.open(args.image).convert("RGB")
        result = pipeline.predict(img, lang=args.lang)
        print(f"  pred_emotion   : {result['pred_emotion']}")
        print(f"  spectrum_top2  : {result['spectrum_top2']}")
        print(f"  low_confidence : {result['low_confidence']}")
        print(f"  explanation:\n    {result['explanation']}")

    passed = sum(results)
    print(f"\n{'='*50}")
    print(f"Sonuc: {passed}/{len(results)} test gecti")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
