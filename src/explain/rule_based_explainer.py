"""
LLM erisimi olmadiginda kullanilan deterministik kural-tabanli aciklayici.

Cerceve: "gorsel oruntu eslesmesi" — model bir cocugun duygusunu OLCMUYOR,
cizimin piksel/renk/cizgi ozelliklerinin egitim kumelerine benzerligi raporluyor.
"""

from __future__ import annotations


def _gt(features: dict[str, float], validity: dict[str, int], key: str, threshold: float) -> bool:
    return validity.get(key, 0) == 1 and float(features.get(key, 0.0)) >= threshold


def _lt(features: dict[str, float], validity: dict[str, int], key: str, threshold: float) -> bool:
    return validity.get(key, 0) == 1 and float(features.get(key, 0.0)) <= threshold


def _label_tr(label: str) -> str:
    return {"Happy": "Mutluluk", "Sad": "Üzüntü", "Angry": "Öfke", "Fear": "Korku/Kaygı"}.get(label, label)


def _label_en(label: str) -> str:
    return {"Happy": "Joy", "Sad": "Sadness", "Angry": "Anger", "Fear": "Fear/Anxiety"}.get(label, label)


# Duygu sınıfına özgü görsel bağlam cümleleri (TR)
_CONTEXT_TR = {
    "Happy": "Çizim, açık kompozisyon, canlı renkler ve geniş figür kullanımı gibi Mutluluk örüntüleriyle güçlü benzerlik göstermektedir.",
    "Sad":   "Çizim; küçük ya da geri çekilmiş figür, soluk/koyu renk tonları ve parçalı çizgi yapısı gibi Üzüntü örüntüleriyle belirgin benzerlik taşımaktadır.",
    "Angry": "Çizim, baskılı ve köşeli çizgiler, yoğun gölgeleme ile sınırlı boşluk kullanımı gibi Öfke örüntüleriyle güçlü örtüşme sergilemektedir.",
    "Fear":  "Çizim; karanlık/koyu tonlar, küçük ya da izole figür ve parçalı çizgi yapısı gibi Korku/Kaygı örüntüleriyle belirgin benzerlik göstermektedir.",
}

# Duygu sınıfına özgü görsel bağlam cümleleri (EN)
_CONTEXT_EN = {
    "Happy": "The drawing shows strong visual similarity to Joy patterns, characterised by open composition, vivid colours, and expansive figure placement.",
    "Sad":   "The drawing bears notable resemblance to Sadness patterns, including small or withdrawn figures, muted/dark tones, and fragmented line work.",
    "Angry": "The drawing exhibits strong overlap with Anger patterns, reflected in heavy, angular strokes, pronounced shading, and compressed spatial layout.",
    "Fear":  "The drawing shows clear similarity to Fear/Anxiety patterns, including dark tones, small or isolated figures, and fragmented line structure.",
}


def _build_visual_sentence_tr(
    f: dict[str, float],
    v: dict[str, int],
    label: str,
) -> str:
    """Clinical özelliklerden doğal Türkçe görsel betimleme cümlesi üret."""
    observations: list[str] = []

    # Çizgi özellikleri
    if _gt(f, v, "shading_ratio", 0.45):
        observations.append("yoğun gölgeleme")
    if _gt(f, v, "stroke_darkness_mean", 0.55):
        observations.append("baskılı koyu çizgiler")
    if _gt(f, v, "sharp_angle_ratio", 0.35):
        observations.append("köşeli ve sert çizgi yapısı")
    if _gt(f, v, "component_count_norm", 8):
        observations.append("parçalı ve dağınık çizgi düzeni")

    # Figür boyutu
    if _lt(f, v, "fg_area_ratio", 0.10):
        observations.append("sayfanın köşesine çekilmiş küçük figür")
    elif _gt(f, v, "fg_area_ratio", 0.35):
        observations.append("tuvale yayılmış geniş ve güçlü figür")

    # Renk
    if _gt(f, v, "dark_color_ratio", 0.20):
        observations.append("karanlık renk tonlarının baskınlığı")
    elif _gt(f, v, "warm_ratio", 0.55):
        observations.append("sıcak ve canlı renk kullanımı")

    if not observations:
        return ""

    if len(observations) == 1:
        return f"Çizimdeki {observations[0]} bu örüntüyle örtüşen temel görsel unsur olarak öne çıkmaktadır."
    last = observations[-1]
    rest = ", ".join(observations[:-1])
    return f"Çizimdeki {rest} ve {last} bu örüntüyle örtüşen temel görsel unsurlar arasındadır."


def _build_visual_sentence_en(
    f: dict[str, float],
    v: dict[str, int],
    label: str,
) -> str:
    observations: list[str] = []

    if _gt(f, v, "shading_ratio", 0.45):
        observations.append("heavy shading")
    if _gt(f, v, "stroke_darkness_mean", 0.55):
        observations.append("dark, pressured strokes")
    if _gt(f, v, "sharp_angle_ratio", 0.35):
        observations.append("angular, sharp line work")
    if _gt(f, v, "component_count_norm", 8):
        observations.append("fragmented, scattered line structure")
    if _lt(f, v, "fg_area_ratio", 0.10):
        observations.append("a small figure retreating to the corner of the page")
    elif _gt(f, v, "fg_area_ratio", 0.35):
        observations.append("a large, expansive figure filling the canvas")
    if _gt(f, v, "dark_color_ratio", 0.20):
        observations.append("dominant dark colour tones")
    elif _gt(f, v, "warm_ratio", 0.55):
        observations.append("warm, vivid colour palette")

    if not observations:
        return ""

    if len(observations) == 1:
        return f"The most salient visual feature consistent with this pattern is {observations[0]}."
    last = observations[-1]
    rest = ", ".join(observations[:-1])
    return f"Visual features consistent with this pattern include {rest}, and {last}."


def explain_rule_based(
    predicted_label: str,
    probs: dict[str, float],
    clinical_features: dict[str, float],
    clinical_validity: dict[str, int],
    gradcam_summary: str,
    lang: str = "tr",
    spectrum_top2: list[tuple[str, float]] | None = None,
    is_calibrated: bool = False,
    low_confidence: bool = False,
) -> str:
    # Belirsiz çizim
    if low_confidence:
        if lang == "en":
            return (
                "The visual patterns in this drawing did not show sufficient similarity "
                "to any emotion cluster in our training data. "
                "Expert evaluation is recommended for a reliable assessment."
            )
        return (
            "Bu çizimin görsel örüntüleri, eğitim veri setimizde yer alan hiçbir "
            "duygu kümesiyle belirgin bir benzerlik göstermemiştir. "
            "Güvenilir bir değerlendirme için uzman incelemesi önerilir."
        )

    f = clinical_features
    v = clinical_validity

    top1_pct = round(probs.get(predicted_label, 0.0) * 100, 1)
    top2_label, top2_pct = None, None
    if spectrum_top2 and len(spectrum_top2) >= 2:
        top2_label = spectrum_top2[1][0]
        top2_pct = round(spectrum_top2[1][1] * 100, 1)

    if lang == "en":
        parts: list[str] = []

        # 1. Duygu bağlamı
        parts.append(_CONTEXT_EN.get(predicted_label, f"The drawing shows primary visual overlap with **{_label_en(predicted_label)}** patterns."))

        # 2. Görsel özellikler
        vis = _build_visual_sentence_en(f, v, predicted_label)
        if vis:
            parts.append(vis)

        # 3. İkincil örüntü
        if top2_label and top2_pct and top2_pct >= 10:
            parts.append(f"Secondary signals from the **{_label_en(top2_label)}** cluster ({top2_pct}%) are also present, suggesting some emotional complexity in the drawing.")

        # 4. Grad-CAM
        if gradcam_summary:
            parts.append(f"The model's attention was primarily focused on the {gradcam_summary} area of the drawing.")

        # 5. Disclaimer
        parts.append("This output reflects visual pattern similarity to training data — it is not a clinical diagnosis and should complement expert evaluation.")

        return " ".join(parts)

    # --- Türkçe ---
    parts_tr: list[str] = []

    # 1. Duygu bağlamı
    primary_name_tr = _label_tr(predicted_label)
    context = _CONTEXT_TR.get(predicted_label, f"Çizim, ağırlıklı olarak **{primary_name_tr}** örüntüleriyle örtüşmektedir.")
    # Benzerlik oranını ekle
    context = context.rstrip(".") + f" (%{top1_pct} benzerlik)."
    parts_tr.append(context)

    # 2. Görsel özellikler
    vis_tr = _build_visual_sentence_tr(f, v, predicted_label)
    if vis_tr:
        parts_tr.append(vis_tr)

    # 3. İkincil örüntü (yalnızca anlamlıysa, >%10)
    if top2_label and top2_pct and top2_pct >= 10:
        secondary_name_tr = _label_tr(top2_label)
        parts_tr.append(f"Arka planda **{secondary_name_tr}** örüntülerinden de sinyaller gözlemlenmekte (%{top2_pct}), bu durum çizimin duygusal karmaşıklığına işaret edebilir.")

    # 4. Grad-CAM
    if gradcam_summary:
        parts_tr.append(f"Modelin dikkati çizimin {gradcam_summary} bölgesinde yoğunlaşmaktadır.")

    # 5. Disclaimer
    parts_tr.append("Bu çıktı klinik tanı niteliği taşımaz; uzman değerlendirmesini destekler.")

    return " ".join(parts_tr)
