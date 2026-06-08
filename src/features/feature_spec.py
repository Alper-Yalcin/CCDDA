"""
18 klinik ozellik tanimi. clinical_extractor ve dataset/model bu sirayi kullanir.
Confidence tier: high / medium / low — UI'da gostermek icin.
"""

from __future__ import annotations

FEATURE_NAMES: list[str] = [
    # global kompozisyon (high)
    "fg_area_ratio",
    "empty_space_ratio",
    "bbox_area_ratio",
    # konum / yerlesim (medium)
    "centroid_x_norm",
    "centroid_y_norm",
    "top_mass_ratio",
    "bottom_mass_ratio",
    # cizgi / basinc (high)
    "stroke_darkness_mean",
    "stroke_darkness_std",
    "component_count_norm",
    "skeleton_break_count_norm",
    "shading_ratio",
    # renk
    "unique_hue_count",
    "warm_ratio",
    "dark_color_ratio",
    # acisallik / sekil
    "sharp_angle_ratio",
    "dominant_orientation_abs",
    # kompozit / kesfetsel
    "figure_integrity_proxy",
]

NUM_FEATURES = len(FEATURE_NAMES)

CONFIDENCE_TIER: dict[str, str] = {
    "fg_area_ratio": "high",
    "empty_space_ratio": "high",
    "bbox_area_ratio": "high",
    "centroid_x_norm": "medium",
    "centroid_y_norm": "medium",
    "top_mass_ratio": "medium",
    "bottom_mass_ratio": "medium",
    "stroke_darkness_mean": "high",
    "stroke_darkness_std": "medium",
    "component_count_norm": "high",
    "skeleton_break_count_norm": "medium",
    "shading_ratio": "high",
    "unique_hue_count": "low",
    "warm_ratio": "low",
    "dark_color_ratio": "low",
    "sharp_angle_ratio": "medium",
    "dominant_orientation_abs": "medium",
    "figure_integrity_proxy": "low",
}


# UI panelinde one cikarilacak metrikler (high-confidence + sembolik anlamli)
HIGHLIGHTED_FEATURES: list[str] = [
    "fg_area_ratio",
    "stroke_darkness_mean",
    "shading_ratio",
    "component_count_norm",
    "sharp_angle_ratio",
    "warm_ratio",
]
