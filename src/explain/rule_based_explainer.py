"""
LLM erisimi olmadiginda kullanilan deterministik kural-tabanli aciklayici.
Klinik feature degerlerinden 2-4 cumlelik metin uretir (TR/EN).
"""

from __future__ import annotations


def _gt(features: dict[str, float], validity: dict[str, int], key: str, threshold: float) -> bool:
    return validity.get(key, 0) == 1 and float(features.get(key, 0.0)) >= threshold


def _lt(features: dict[str, float], validity: dict[str, int], key: str, threshold: float) -> bool:
    return validity.get(key, 0) == 1 and float(features.get(key, 0.0)) <= threshold


def _label_tr(label: str) -> str:
    return {"Happy": "Mutluluk", "Sad": "Uzuntu", "Angry": "Ofke", "Fear": "Korku/Kaygi"}.get(label, label)


def explain_rule_based(
    predicted_label: str,
    probs: dict[str, float],
    clinical_features: dict[str, float],
    clinical_validity: dict[str, int],
    gradcam_summary: str,
    lang: str = "tr",
) -> str:
    f = clinical_features
    v = clinical_validity

    cues_tr: list[str] = []
    cues_en: list[str] = []

    if _gt(f, v, "shading_ratio", 0.45):
        cues_tr.append(f"yogun golgeleme (shading={f['shading_ratio']:.2f})")
        cues_en.append(f"heavy shading (shading={f['shading_ratio']:.2f})")
    if _gt(f, v, "stroke_darkness_mean", 0.55):
        cues_tr.append(f"koyu cizgi basinci ({f['stroke_darkness_mean']:.2f})")
        cues_en.append(f"dark stroke pressure ({f['stroke_darkness_mean']:.2f})")
    if _gt(f, v, "sharp_angle_ratio", 0.35):
        cues_tr.append(f"yuksek acisallik ({f['sharp_angle_ratio']:.2f})")
        cues_en.append(f"high angularity ({f['sharp_angle_ratio']:.2f})")
    if _lt(f, v, "fg_area_ratio", 0.10):
        cues_tr.append(f"figur kuçuk (alan oranı {f['fg_area_ratio']:.2f})")
        cues_en.append(f"small figure (area ratio {f['fg_area_ratio']:.2f})")
    if _gt(f, v, "fg_area_ratio", 0.35):
        cues_tr.append(f"figur tuvale yayilmis ({f['fg_area_ratio']:.2f})")
        cues_en.append(f"figure fills the canvas ({f['fg_area_ratio']:.2f})")
    if _gt(f, v, "component_count_norm", 8):
        cues_tr.append("cizgide parcalanmislik")
        cues_en.append("fragmented strokes")
    if _gt(f, v, "warm_ratio", 0.55):
        cues_tr.append("sicak renk baskinligi")
        cues_en.append("warm color dominance")
    if _gt(f, v, "dark_color_ratio", 0.20):
        cues_tr.append("koyu renk yogunlugu")
        cues_en.append("dark color density")

    pct = {k: round(v * 100, 1) for k, v in probs.items()}
    top_pct = pct.get(predicted_label, 0.0)

    if lang == "en":
        body = (
            f"The model predicted **{predicted_label}** with {top_pct}% confidence. "
        )
        if cues_en:
            body += "Supporting clinical cues: " + ", ".join(cues_en) + ". "
        else:
            body += "No strong clinical cues exceeded the alert thresholds. "
        if gradcam_summary:
            body += f"The model focused on the {gradcam_summary} region of the drawing. "
        body += "This output is for research support only and is not a clinical diagnosis."
        return body

    body = (
        f"Model **{_label_tr(predicted_label)}** sinifini %{top_pct} guvenle tahmin etti. "
    )
    if cues_tr:
        body += "Destekleyen klinik isaretler: " + ", ".join(cues_tr) + ". "
    else:
        body += "Klinik isaretler esik degerlerini gecmedi. "
    if gradcam_summary:
        body += f"Model agirlikli olarak cizimin {gradcam_summary} bolgesine baktı. "
    body += "Bu cikti yalnizca arastirma destegidir; klinik tani niteligi tasimaz."
    return body
