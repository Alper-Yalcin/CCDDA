"""
clinical_v2 — Klinik akil yurutme ciktisi (tezin vitrini).

Concept Bottleneck modeli bir cizimi:
  1. once klinik gostergelere (kavramlara) cevirir,
  2. sonra bu gostergelerden duyguya ulasir.

Bu modul, modelin tahmin ettigi gostergeleri klinik literature (Koppitz/Di Leo)
baglayan, klinisyene yonelik bir AKIL YURUTME metni uretir. Boylece sistem
"kor siniflandirma" degil, gosterge tabanli gerekce sunar.

Kullanim:
  python -m clinical_v2.clinical_reasoning_v2 --ckpt out/experiments_v2/V2_CB2/checkpoints/best.pt --image <path>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from clinical_v2.extractor_v2 import extract_v2
from clinical_v2.feature_spec_v2 import CLINICAL_MEANING, FEATURE_NAMES_V2, NUM_FEATURES_V2
from src.data.transforms import get_image_transforms
from src.models.concept_bottleneck_classifier import ConceptBottleneckClassifier

CLASSES = ["Happy", "Sad", "Angry", "Fear"]
TR = {"Happy": "Mutlu", "Sad": "Uzgun", "Angry": "Kizgin", "Fear": "Korku"}
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Gostergenin "dikkat cekici" sayilmasi icin z-esigi
Z_THRESHOLD = 0.7


def load_model(ckpt_path):
    ck = torch.load(ckpt_path, map_location=DEVICE, weights_only=False)
    model = ConceptBottleneckClassifier(
        backbone=ck.get("backbone", "resnet50"),
        num_concepts=ck.get("num_concepts", NUM_FEATURES_V2),
        mode=ck.get("mode", "hybrid"),
        pretrained=False,
    ).to(DEVICE)
    model.load_state_dict(ck["model_state"])
    model.eval()
    return model


def reason(model, image_pil, stats_path="out/real/feature_stats_v2.json", lang="tr"):
    stats = json.load(open(stats_path, encoding="utf-8"))
    mean = np.array([stats[n]["mean"] for n in FEATURE_NAMES_V2], dtype=np.float32)
    std = np.array([stats[n]["std"] for n in FEATURE_NAMES_V2], dtype=np.float32)

    _, val_tf = get_image_transforms(image_size=224)
    rgb = image_pil.convert("RGB")
    img_t = val_tf(rgb).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logits, pred_concepts = model(img_t, return_concepts=True)
        probs = torch.softmax(logits, 1)[0].cpu().numpy()
        pred_c_z = pred_concepts[0].cpu().numpy()  # standartlastirilmis (z)

    pred_idx = int(probs.argmax())
    pred_label = CLASSES[pred_idx]

    # OpenCV ile gercek gosterge degerleri (dogrulama icin)
    true_vals, true_valid = extract_v2(rgb)
    true_z = np.where(true_valid > 0, (true_vals - mean) / std, 0.0)

    # Dikkat cekici gostergeler: model tahminine gore |z| buyuk olanlar
    notable = []
    for i, name in enumerate(FEATURE_NAMES_V2):
        z = float(pred_c_z[i])
        if abs(z) >= Z_THRESHOLD:
            meaning = CLINICAL_MEANING.get(name, {})
            direction = "high" if z > 0 else "low"
            desc = meaning.get(direction) or meaning.get("indicator", name)
            notable.append({
                "feature": name, "z": round(z, 2), "direction": direction,
                "indicator": meaning.get("indicator", ""),
                "emotion": meaning.get("emotion", ""),
                "desc": desc,
            })
    notable.sort(key=lambda x: -abs(x["z"]))

    # Narrative uret
    spectrum = sorted([(CLASSES[i], float(probs[i])) for i in range(4)], key=lambda x: -x[1])
    lines = []
    lines.append(f"Birincil oruntu: {TR[pred_label]} (%{probs[pred_idx]*100:.0f})")
    if spectrum[1][1] > 0.15:
        lines.append(f"Ikincil oruntu: {TR[spectrum[1][0]]} (%{spectrum[1][1]*100:.0f})")
    lines.append("")
    lines.append("Klinik gosterge gerekçesi:")
    if notable:
        for n in notable[:5]:
            lines.append(f"  - {n['desc']} (gosterge: {n['indicator']}, z={n['z']})")
    else:
        lines.append("  - Belirgin klinik gosterge one cikmadi; karar agirlikli olarak genel kompozisyona dayaniyor.")
    lines.append("")
    lines.append("Not: Bu cikti gorsel oruntu benzerligini ve klinik gosterge literaturuyle"
                 " (Koppitz 1968, Di Leo 1973) uyumu yansitir; klinik tani degildir.")

    return {
        "pred_label": pred_label,
        "probs": {CLASSES[i]: float(probs[i]) for i in range(4)},
        "notable_concepts": notable,
        "narrative": "\n".join(lines),
        "predicted_concepts_z": {FEATURE_NAMES_V2[i]: round(float(pred_c_z[i]), 3) for i in range(NUM_FEATURES_V2)},
        "true_concepts_z": {FEATURE_NAMES_V2[i]: round(float(true_z[i]), 3) for i in range(NUM_FEATURES_V2)},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True, type=Path)
    ap.add_argument("--image", required=True, type=Path)
    ap.add_argument("--stats", default="out/real/feature_stats_v2.json")
    args = ap.parse_args()
    model = load_model(args.ckpt)
    out = reason(model, Image.open(args.image), args.stats)
    print(out["narrative"])
    print()
    print("Tahmin dagilimi:", {k: round(v, 3) for k, v in out["probs"].items()})


if __name__ == "__main__":
    main()
