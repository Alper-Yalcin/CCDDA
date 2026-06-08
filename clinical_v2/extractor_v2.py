"""
clinical_v2 — figur-farkinda klinik gosterge cikarimi (OpenCV).

Temel fark: once FIGUR izole edilir (en buyuk anlamli baglantili bilesen),
sonra gostergeler figur uzerinden hesaplanir. Boylece "kucuk figur",
"kose yerlesim", "figur-ici golgeleme" gibi gercek Koppitz gostergeleri
hesaplanabilir.

API:
  extract_v2(image_pil) -> (values[16], validity[16])
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm

from clinical_v2.feature_spec_v2 import FEATURE_NAMES_V2, NUM_FEATURES_V2


def _safe(v, ok):
    if not ok or v is None or not np.isfinite(v):
        return float("nan"), 0
    return float(v), 1


def _foreground_mask(gray: np.ndarray) -> np.ndarray:
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 25, 10)
    kernel = np.ones((2, 2), np.uint8)
    return cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)


def _figure_mask(fg: np.ndarray) -> tuple[np.ndarray, dict]:
    """
    Figuru izole et: en buyuk anlamli bilesen(ler).
    Doner: (figure_mask, stats) — stats: bbox, alan, centroid.
    """
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(fg, connectivity=8)
    if n <= 1:
        return np.zeros_like(fg), {}
    # Arka plan disindaki bilesenler
    areas = stats[1:, cv2.CC_STAT_AREA]
    if len(areas) == 0 or areas.max() == 0:
        return np.zeros_like(fg), {}
    # En buyuk bilesen = figur cekirdegi; boyutca yakin diger buyuk parcalari da kat
    max_area = areas.max()
    keep = [i + 1 for i in range(len(areas)) if areas[i] >= 0.15 * max_area]
    fig = np.isin(labels, keep).astype(np.uint8) * 255

    ys, xs = np.where(fig > 0)
    if len(xs) == 0:
        return fig, {}
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    cx, cy = xs.mean(), ys.mean()
    return fig, {
        "bbox": (x0, y0, x1, y1),
        "bbox_w": x1 - x0 + 1, "bbox_h": y1 - y0 + 1,
        "area": int((fig > 0).sum()),
        "cx": cx, "cy": cy,
        "n_components": len(keep),
        "coords": (xs, ys),
    }


def extract_v2(image_pil: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    rgb = np.array(image_pil.convert("RGB"))
    h, w = rgb.shape[:2]
    canvas = float(h * w) if h * w > 0 else 1.0
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    fg = _foreground_mask(gray)
    fg_pixels = int((fg > 0).sum())
    fig, fstat = _figure_mask(fg)
    fig_pixels = fstat.get("area", 0)

    F: dict[str, tuple] = {}

    # === Grup 1: Figur boyutu & yerlesimi ===
    if fig_pixels > 50 and fstat:
        x0, y0, x1, y1 = fstat["bbox"]
        bbox_area = fstat["bbox_w"] * fstat["bbox_h"]
        F["figure_size_ratio"] = _safe(bbox_area / canvas, True)
        # centrality: figur merkezinin sayfa merkezinden uzakligi (kose=1)
        ncx, ncy = fstat["cx"] / w, fstat["cy"] / h
        dist = np.sqrt((ncx - 0.5) ** 2 + (ncy - 0.5) ** 2) / 0.7071
        F["figure_centrality"] = _safe(min(dist, 1.0), True)
        F["figure_vertical_pos"] = _safe(ncy, True)
        # tilt: figur piksellerine PCA
        xs, ys = fstat["coords"]
        coords = np.stack([xs, ys], 1).astype(np.float32)
        coords -= coords.mean(0)
        try:
            cov = np.cov(coords, rowvar=False)
            evals, evecs = np.linalg.eigh(cov)
            pc = evecs[:, np.argmax(evals)]
            ang = np.degrees(np.arctan2(pc[1], pc[0]))
            tilt = abs(((ang + 90) % 180) - 90) / 90.0
            F["figure_tilt"] = _safe(tilt, True)
        except Exception:
            F["figure_tilt"] = (float("nan"), 0)
    else:
        for k in ("figure_size_ratio", "figure_centrality", "figure_vertical_pos", "figure_tilt"):
            F[k] = (float("nan"), 0)

    # === Grup 2: Cizgi kalitesi & baski ===
    if fig_pixels > 0:
        luma = gray[fig > 0].astype(np.float32) / 255.0
        dark = 1.0 - luma
        F["stroke_darkness_mean"] = _safe(float(dark.mean()), True)
        F["pressure_variation"] = _safe(float(dark.std()), True)
    else:
        F["stroke_darkness_mean"] = (float("nan"), 0)
        F["pressure_variation"] = (float("nan"), 0)

    # line_tremor: figur konturunun puruzlulugu (ham uzunluk / convex hull uzunlugu)
    contours, _ = cv2.findContours(fig, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    big = [c for c in contours if cv2.contourArea(c) > 50]
    if big:
        tremor_vals = []
        sharp_total, total_pts = 0, 0
        for c in big:
            raw_len = cv2.arcLength(c, True)
            hull = cv2.convexHull(c)
            hull_len = cv2.arcLength(hull, True)
            if hull_len > 0:
                tremor_vals.append(raw_len / hull_len)  # >1; yuksek=puruzlu
            # keskin aci
            approx = cv2.approxPolyDP(c, 0.01 * raw_len, True)
            if len(approx) >= 3:
                pts = approx.reshape(-1, 2)
                for i in range(len(pts)):
                    a, b, d = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
                    v1, v2 = a - b, d - b
                    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
                    if n1 == 0 or n2 == 0:
                        continue
                    cosang = np.clip(np.dot(v1, v2) / (n1 * n2), -1, 1)
                    ang = np.degrees(np.arccos(cosang))
                    total_pts += 1
                    if ang < 70:
                        sharp_total += 1
        F["line_tremor"] = _safe(float(np.mean(tremor_vals)) if tremor_vals else None, bool(tremor_vals))
        F["sharp_angle_ratio"] = _safe(sharp_total / total_pts if total_pts else None, total_pts > 0)
    else:
        F["line_tremor"] = (float("nan"), 0)
        F["sharp_angle_ratio"] = (float("nan"), 0)

    # === Grup 3: Golgeleme & butunluk ===
    if fig_pixels > 0:
        dark_mask = (gray < 80).astype(np.uint8) * 255
        dark_dense = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        inter = cv2.bitwise_and(dark_dense, fig)
        F["shading_on_figure"] = _safe(int((inter > 0).sum()) / float(fig_pixels), True)
    else:
        F["shading_on_figure"] = (float("nan"), 0)

    # fragmentation: figur iskeleti uc noktalari (kopukluk)
    if fig_pixels > 50:
        img = (fig > 0).astype(np.uint8) * 255
        skel = np.zeros_like(img)
        el = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        work = img.copy()
        for _ in range(200):
            opened = cv2.morphologyEx(work, cv2.MORPH_OPEN, el)
            tmp = cv2.subtract(work, opened)
            eroded = cv2.erode(work, el)
            skel = cv2.bitwise_or(skel, tmp)
            work = eroded
            if cv2.countNonZero(work) == 0:
                break
        bs = (skel > 0).astype(np.uint8)
        if bs.sum() > 0:
            kern = np.array([[1, 1, 1], [1, 10, 1], [1, 1, 1]], np.uint8)
            filt = cv2.filter2D(bs, cv2.CV_16S, kern)
            endpoints = int((filt == 11).sum())
            norm = canvas / 10000.0
            F["part_fragmentation"] = _safe(endpoints / max(norm, 1.0), True)
        else:
            F["part_fragmentation"] = (float("nan"), 0)
    else:
        F["part_fragmentation"] = (float("nan"), 0)

    # component count (tum fg uzerinden)
    if fg_pixels > 0:
        n_lab, _, _, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
        norm = canvas / 10000.0
        F["component_count_norm"] = _safe(max(0, n_lab - 1) / max(norm, 1.0), True)
    else:
        F["component_count_norm"] = (float("nan"), 0)

    # === Grup 4: Kompozisyon ===
    F["fg_area_ratio"] = _safe(fg_pixels / canvas, fg_pixels > 0)
    F["empty_space_ratio"] = _safe(1.0 - fg_pixels / canvas, fg_pixels > 0)
    val = hsv[:, :, 2]
    F["dark_color_ratio"] = _safe(float((val < 70).sum()) / canvas, True)

    # === Grup 5: Renk (tek gosterge) ===
    sat = hsv[:, :, 1]
    colored = (sat > 40).astype(np.uint8)
    cc = int(colored.sum())
    if cc > 50:
        hue = hsv[:, :, 0][colored > 0]
        warm = ((hue < 30) | (hue > 150)).sum()
        F["color_warmth"] = _safe(float(warm) / cc, True)
    else:
        F["color_warmth"] = (float("nan"), 0)

    # === Kompozit ===
    if fig_pixels > 0 and F["component_count_norm"][1] == 1:
        comp = F["component_count_norm"][0]
        size_score = min((fig_pixels / canvas) * 4.0, 1.0)
        comp_score = max(0.0, 1.0 - min(comp / 10.0, 1.0))
        F["figure_integrity_proxy"] = _safe(0.5 * size_score + 0.5 * comp_score, True)
    else:
        F["figure_integrity_proxy"] = (float("nan"), 0)

    values = np.zeros(NUM_FEATURES_V2, dtype=np.float32)
    valids = np.zeros(NUM_FEATURES_V2, dtype=np.float32)
    for i, name in enumerate(FEATURE_NAMES_V2):
        v, ok = F.get(name, (float("nan"), 0))
        if ok:
            values[i] = v
            valids[i] = 1.0
    return values, valids


def _row(sample_id, image_path):
    try:
        with Image.open(image_path) as im:
            vals, valids = extract_v2(im)
    except Exception:
        vals = np.zeros(NUM_FEATURES_V2, dtype=np.float32)
        valids = np.zeros(NUM_FEATURES_V2, dtype=np.float32)
    out = {"sample_id": sample_id}
    for i, name in enumerate(FEATURE_NAMES_V2):
        out[name] = float(vals[i]) if valids[i] == 1.0 else float("nan")
        out[f"{name}_valid"] = int(valids[i])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    df = pd.read_csv(args.manifest)
    rows = [_row(str(r["sample_id"]), r["image_path"])
            for _, r in tqdm(df.iterrows(), total=len(df), desc="v2 ozellik")]
    out_df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out, index=False)
    vcols = [f"{n}_valid" for n in FEATURE_NAMES_V2]
    print(f"\nKaydedildi: {args.out}  (n={len(out_df)})")
    print(f"Ortalama validity: {out_df[vcols].mean().mean():.3f}")


if __name__ == "__main__":
    main()
