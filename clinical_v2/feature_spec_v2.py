"""
clinical_v2 — Gelistirilmis, figur-farkinda klinik gosterge spesifikasyonu.

Mevcut 18 genel goruntu istatistigi yerine, projektif cizim testleri
literaturune (Koppitz 1968, Di Leo 1973) dayali, FIGUR-FARKINDA gostergeler.

Her gosterge:
  - bir Koppitz/Di Leo gostergesine,
  - bir duygusal duruma baglidir.

16 gosterge, 5 klinik grupta.
"""

from __future__ import annotations

# Gosterge sirasi — extractor ve model bu sirayi kullanir.
FEATURE_NAMES_V2: list[str] = [
    # --- Grup 1: Figur Boyutu & Yerlesimi (Koppitz Size/Spatial EI) ---
    "figure_size_ratio",        # kucuk->guvensizlik/uzuntu, buyuk->saldirganlik
    "figure_centrality",        # 0=merkez, 1=kose -> kose/kenar->cekilme
    "figure_vertical_pos",      # 0=ust,1=alt -> ust->kacis, alt->guvensizlik
    "figure_tilt",              # egiklik [0,1] -> egik->instabilite

    # --- Grup 2: Cizgi Kalitesi & Baski (pressure/anxiety) ---
    "stroke_darkness_mean",     # baski: yuksek->ofke/gerginlik
    "line_tremor",              # titrek/puruzlu cizgi->kaygi, kararsizlik
    "pressure_variation",       # baski duzensizligi->durtusellik
    "sharp_angle_ratio",        # keskin kose->saldirganlik

    # --- Grup 3: Golgeleme & Butunluk (anxiety/impulsivity) ---
    "shading_on_figure",        # figur-ici golgeleme->kaygi (Koppitz shading EI)
    "part_fragmentation",       # zayif entegrasyon->durtusellik (Koppitz)
    "component_count_norm",     # parca sayisi

    # --- Grup 4: Kompozisyon (kalici gucluler) ---
    "fg_area_ratio",            # doluluk
    "empty_space_ratio",        # bosluk->izolasyon (uzuntu)
    "dark_color_ratio",         # koyu ton->olumsuz duygu

    # --- Grup 5: Renk (sadelestirilmis, tek gosterge) ---
    "color_warmth",             # sicak ton orani (zayif klinik, referans amacli)

    # --- Kompozit ---
    "figure_integrity_proxy",   # bicim butunlugu kompoziti
]

NUM_FEATURES_V2 = len(FEATURE_NAMES_V2)

# Klinik anlam haritasi (tez + LLM/kural tabanli aciklama icin)
CLINICAL_MEANING: dict[str, dict] = {
    "figure_size_ratio":     {"emotion": "Sad/Angry",  "indicator": "Koppitz figure size",
                              "low": "kucuk figur->guvensizlik, cekilme, uzuntu",
                              "high": "buyuk figur->durtusellik, saldirganlik"},
    "figure_centrality":     {"emotion": "Sad/Fear",   "indicator": "Di Leo spatial placement",
                              "high": "kose/kenar yerlesim->cekilme, izolasyon"},
    "figure_vertical_pos":   {"emotion": "Sad",        "indicator": "Koppitz vertical placement",
                              "high": "alt yerlesim->guvensizlik, depresyon"},
    "figure_tilt":           {"emotion": "Fear",       "indicator": "Koppitz slanting figure EI",
                              "high": "egik figur->instabilite, kararsizlik"},
    "stroke_darkness_mean":  {"emotion": "Angry/Fear", "indicator": "line pressure",
                              "high": "yuksek baski->ofke, gerginlik"},
    "line_tremor":           {"emotion": "Fear",       "indicator": "Koppitz tremulous line EI",
                              "high": "titrek cizgi->kaygi, kararsizlik"},
    "pressure_variation":    {"emotion": "Angry",      "indicator": "pressure inconsistency",
                              "high": "baski duzensizligi->durtusellik"},
    "sharp_angle_ratio":     {"emotion": "Angry",      "indicator": "angularity",
                              "high": "keskin kose->saldirganlik"},
    "shading_on_figure":     {"emotion": "Fear/Angry", "indicator": "Koppitz shading EI",
                              "high": "golgeleme->kaygi"},
    "part_fragmentation":    {"emotion": "Angry",      "indicator": "Koppitz poor integration EI",
                              "high": "kopuk parcalar->durtusellik, immaturite"},
    "component_count_norm":  {"emotion": "neutral",    "indicator": "component count"},
    "fg_area_ratio":         {"emotion": "neutral",    "indicator": "foreground fill"},
    "empty_space_ratio":     {"emotion": "Sad",        "indicator": "emptiness",
                              "high": "bos alan->izolasyon, uzuntu"},
    "dark_color_ratio":      {"emotion": "Fear",       "indicator": "dark tone",
                              "high": "koyu ton->olumsuz duygu"},
    "color_warmth":          {"emotion": "Happy",      "indicator": "color warmth (zayif)",
                              "high": "sicak ton->pozitif duygu"},
    "figure_integrity_proxy":{"emotion": "neutral",    "indicator": "form integrity"},
}
