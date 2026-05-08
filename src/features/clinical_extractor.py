"""
OpenCV tabanli klinik ozellik cikarimi.

Tek API:
    extract_clinical_features(image_pil) -> (features: np.ndarray[18], validity: np.ndarray[18])

CLI: tum manifest icin batch cikarim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm

from src.features.feature_spec import FEATURE_NAMES, NUM_FEATURES


def _safe(value: float, valid: bool) -> tuple[float, int]:
    if not valid or value is None or not np.isfinite(value):
        return float("nan"), 0
    return float(value), 1


def _foreground_mask(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    th = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 25, 10,
    )
    kernel = np.ones((2, 2), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)
    return th  # 0/255


def _skeleton(mask: np.ndarray) -> np.ndarray:
    img = (mask > 0).astype(np.uint8) * 255
    skel = np.zeros(img.shape, np.uint8)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while True:
        opened = cv2.morphologyEx(img, cv2.MORPH_OPEN, element)
        temp = cv2.subtract(img, opened)
        eroded = cv2.erode(img, element)
        skel = cv2.bitwise_or(skel, temp)
        img = eroded.copy()
        if cv2.countNonZero(img) == 0:
            break
    return skel


def _endpoint_count(skel: np.ndarray) -> int:
    bin_skel = (skel > 0).astype(np.uint8)
    if bin_skel.sum() == 0:
        return 0
    kernel = np.array([[1, 1, 1], [1, 10, 1], [1, 1, 1]], dtype=np.uint8)
    filtered = cv2.filter2D(bin_skel, ddepth=cv2.CV_16S, kernel=kernel)
    return int(np.sum(filtered == 11))


def extract_clinical_features(image_pil: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    rgb = np.array(image_pil.convert("RGB"))
    h, w = rgb.shape[:2]
    canvas_area = float(h * w) if h * w > 0 else 1.0
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    fg = _foreground_mask(gray)
    fg_pixels = int(np.sum(fg > 0))

    feats: dict[str, tuple[float, int]] = {}

    # 1) global
    fg_area_ratio = fg_pixels / canvas_area
    feats["fg_area_ratio"] = _safe(fg_area_ratio, fg_pixels > 0)
    feats["empty_space_ratio"] = _safe(1.0 - fg_area_ratio, fg_pixels > 0)

    # 2) bbox
    if fg_pixels > 0:
        ys, xs = np.where(fg > 0)
        bbox_w = xs.max() - xs.min() + 1
        bbox_h = ys.max() - ys.min() + 1
        feats["bbox_area_ratio"] = _safe(bbox_w * bbox_h / canvas_area, True)
    else:
        feats["bbox_area_ratio"] = (float("nan"), 0)

    # 3) centroid + mass split
    if fg_pixels > 0:
        m = cv2.moments(fg)
        if m["m00"] > 0:
            cx = m["m10"] / m["m00"]
            cy = m["m01"] / m["m00"]
            feats["centroid_x_norm"] = _safe(cx / w, True)
            feats["centroid_y_norm"] = _safe(cy / h, True)
            top = int(np.sum(fg[: h // 2] > 0))
            bot = int(np.sum(fg[h // 2 :] > 0))
            feats["top_mass_ratio"] = _safe(top / fg_pixels, True)
            feats["bottom_mass_ratio"] = _safe(bot / fg_pixels, True)
        else:
            for k in ("centroid_x_norm", "centroid_y_norm", "top_mass_ratio", "bottom_mass_ratio"):
                feats[k] = (float("nan"), 0)
    else:
        for k in ("centroid_x_norm", "centroid_y_norm", "top_mass_ratio", "bottom_mass_ratio"):
            feats[k] = (float("nan"), 0)

    # 4) stroke darkness (1 - luma) over fg
    if fg_pixels > 0:
        luma_fg = gray[fg > 0].astype(np.float32) / 255.0
        dark = 1.0 - luma_fg
        feats["stroke_darkness_mean"] = _safe(float(dark.mean()), True)
        feats["stroke_darkness_std"] = _safe(float(dark.std()), True)
    else:
        feats["stroke_darkness_mean"] = (float("nan"), 0)
        feats["stroke_darkness_std"] = (float("nan"), 0)

    # 5) component count normalized
    if fg_pixels > 0:
        n_labels, _, stats, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
        valid_components = max(0, n_labels - 1)
        norm = canvas_area / 10000.0
        feats["component_count_norm"] = _safe(valid_components / max(norm, 1.0), True)
    else:
        feats["component_count_norm"] = (float("nan"), 0)

    # 6) skeleton break count
    if fg_pixels > 50:
        try:
            skel = _skeleton(fg)
            endpoints = _endpoint_count(skel)
            norm = canvas_area / 10000.0
            feats["skeleton_break_count_norm"] = _safe(endpoints / max(norm, 1.0), True)
        except Exception:
            feats["skeleton_break_count_norm"] = (float("nan"), 0)
    else:
        feats["skeleton_break_count_norm"] = (float("nan"), 0)

    # 7) shading ratio: yogun koyu komsuluk
    if fg_pixels > 0:
        dark_mask = (gray < 80).astype(np.uint8) * 255
        dark_dense = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        intersect = cv2.bitwise_and(dark_dense, fg)
        feats["shading_ratio"] = _safe(int(np.sum(intersect > 0)) / float(fg_pixels), True)
    else:
        feats["shading_ratio"] = (float("nan"), 0)

    # 8) renk metrikleri (HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    colored_mask = (sat > 40).astype(np.uint8)
    colored_count = int(colored_mask.sum())
    if colored_count > 50:
        hue = hsv[:, :, 0]
        hue_colored = hue[colored_mask > 0]
        bins = np.bincount(hue_colored // 10, minlength=18)
        unique_h = int((bins > (colored_count * 0.005)).sum())
        feats["unique_hue_count"] = _safe(float(unique_h), True)
        warm = ((hue_colored < 30) | (hue_colored > 150)).sum()
        feats["warm_ratio"] = _safe(float(warm) / colored_count, True)
    else:
        feats["unique_hue_count"] = (float("nan"), 0)
        feats["warm_ratio"] = (float("nan"), 0)

    dark_color = ((val < 70)).astype(np.uint8)
    feats["dark_color_ratio"] = _safe(float(dark_color.sum()) / canvas_area, True)

    # 9) acisallik (contour bazli)
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    big_contours = [c for c in contours if cv2.contourArea(c) > 50]
    if big_contours:
        sharp_total = 0
        total_pts = 0
        for c in big_contours:
            approx = cv2.approxPolyDP(c, epsilon=0.01 * cv2.arcLength(c, True), closed=True)
            if len(approx) < 3:
                continue
            pts = approx.reshape(-1, 2)
            for i in range(len(pts)):
                a = pts[i - 1]
                b = pts[i]
                d = pts[(i + 1) % len(pts)]
                v1 = a - b
                v2 = d - b
                n1 = np.linalg.norm(v1)
                n2 = np.linalg.norm(v2)
                if n1 == 0 or n2 == 0:
                    continue
                cosang = float(np.dot(v1, v2) / (n1 * n2))
                cosang = max(-1.0, min(1.0, cosang))
                ang = np.degrees(np.arccos(cosang))
                total_pts += 1
                if ang < 70:  # keskin koşe
                    sharp_total += 1
        if total_pts > 0:
            feats["sharp_angle_ratio"] = _safe(sharp_total / total_pts, True)
        else:
            feats["sharp_angle_ratio"] = (float("nan"), 0)
    else:
        feats["sharp_angle_ratio"] = (float("nan"), 0)

    # 10) dominant orientation (PCA)
    if fg_pixels > 100:
        ys, xs = np.where(fg > 0)
        coords = np.stack([xs, ys], axis=1).astype(np.float32)
        coords -= coords.mean(axis=0)
        cov = np.cov(coords, rowvar=False)
        try:
            evals, evecs = np.linalg.eigh(cov)
            principal = evecs[:, np.argmax(evals)]
            angle = np.degrees(np.arctan2(principal[1], principal[0]))
            angle_abs = abs(((angle + 90) % 180) - 90) / 90.0  # [0,1]
            feats["dominant_orientation_abs"] = _safe(angle_abs, True)
        except Exception:
            feats["dominant_orientation_abs"] = (float("nan"), 0)
    else:
        feats["dominant_orientation_abs"] = (float("nan"), 0)

    # 11) figure_integrity_proxy: bicim butunlugu kompoziti
    if fg_pixels > 0 and feats["component_count_norm"][1] == 1:
        comp_norm = feats["component_count_norm"][0]
        # az parca + makul alan = bütünluk yuksek
        size_score = min(fg_area_ratio * 4.0, 1.0)
        comp_score = max(0.0, 1.0 - min(comp_norm / 10.0, 1.0))
        integrity = 0.5 * size_score + 0.5 * comp_score
        feats["figure_integrity_proxy"] = _safe(integrity, True)
    else:
        feats["figure_integrity_proxy"] = (float("nan"), 0)

    values = np.zeros(NUM_FEATURES, dtype=np.float32)
    valids = np.zeros(NUM_FEATURES, dtype=np.float32)
    for i, name in enumerate(FEATURE_NAMES):
        v, ok = feats.get(name, (float("nan"), 0))
        if ok:
            values[i] = v
            valids[i] = 1.0
        else:
            values[i] = 0.0  # NaN yerine 0; validity zaten 0
            valids[i] = 0.0
    return values, valids


def _row_for(sample_id: str, image_path: str) -> dict:
    try:
        with Image.open(image_path) as im:
            values, valids = extract_clinical_features(im)
    except Exception:
        values = np.zeros(NUM_FEATURES, dtype=np.float32)
        valids = np.zeros(NUM_FEATURES, dtype=np.float32)
    out: dict = {"sample_id": sample_id}
    for i, name in enumerate(FEATURE_NAMES):
        out[name] = float(values[i]) if valids[i] == 1.0 else float("nan")
        out[f"{name}_valid"] = int(valids[i])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--limit", type=int, default=0, help="0 = tum dataset")
    args = ap.parse_args()

    df = pd.read_csv(args.manifest)
    if args.limit > 0:
        df = df.head(args.limit)

    rows = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Klinik ozellik"):
        rows.append(_row_for(str(row["sample_id"]), row["image_path"]))

    out_df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out, index=False)

    valid_cols = [f"{n}_valid" for n in FEATURE_NAMES]
    valid_rate = out_df[valid_cols].mean().mean()
    print(f"\nKaydedildi: {args.out}")
    print(f"Ortalama validity orani: {valid_rate:.3f}")
    print(f"Toplam ornek: {len(out_df)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
