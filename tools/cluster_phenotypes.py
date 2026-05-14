"""
Split-aware phenotype discovery from clinical drawing features.

Default input is the current best 4-class training manifest:
  out/highconf_pipeline/manifests/manifest_highconf_075.csv

Outputs:
  out/phenotype_pipeline/features_clean.csv
  out/phenotype_pipeline/manifest_multitask.csv
  out/phenotype_pipeline/phenotype_report.html
  out/phenotype_pipeline/cluster_report.json

K-Means is fit on train split only. Val/test cluster IDs are assigned by
predicting with the train-fitted scaler + K-Means model, so test information
does not leak into the phenotype centers.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageOps
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "out" / "highconf_pipeline" / "manifests" / "manifest_highconf_075.csv"
DEFAULT_OUT = ROOT / "out" / "phenotype_pipeline"
DEFAULT_IMAGE_ROOT = ROOT / "Dataset" / "Images"
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
LABEL_ALIASES = {
    "happy": ("Happy", 0),
    "happiness": ("Happy", 0),
    "sad": ("Sad", 1),
    "sadness": ("Sad", 1),
    "angry": ("Angry", 2),
    "anger": ("Angry", 2),
    "fear": ("Fear", 3),
    "fearful": ("Fear", 3),
    "anxiety": ("Fear", 3),
}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features.clinical_extractor import extract_clinical_features
from src.features.feature_spec import FEATURE_NAMES


def safe_name(text: str) -> str:
    keep = []
    for ch in str(text):
        keep.append(ch if ch.isalnum() or ch in ("-", "_") else "_")
    return "".join(keep)[:120]


def load_manifest(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    required = {"sample_id", "image_path", "label", "label_id", "split"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Manifest missing columns: {sorted(missing)}")
    df = df.copy()
    df["sample_id"] = df["sample_id"].astype(str)
    df["image_path"] = df["image_path"].astype(str)
    df = df.drop_duplicates("sample_id", keep="first").reset_index(drop=True)
    return df


def label_from_path(path: Path, root: Path) -> tuple[str, int, str] | None:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        rel_parts = path.parts
    for part in reversed(rel_parts[:-1]):
        key = part.lower()
        if key in LABEL_ALIASES:
            label, label_id = LABEL_ALIASES[key]
            return label, label_id, part
    return None


def split_from_path(path: Path, root: Path) -> str | None:
    try:
        rel_parts = [p.lower() for p in path.relative_to(root).parts]
    except ValueError:
        rel_parts = [p.lower() for p in path.parts]
    if "train" in rel_parts:
        return "train"
    if "val" in rel_parts or "valid" in rel_parts or "validation" in rel_parts:
        return "val"
    if "test" in rel_parts:
        return "test"
    return None


def build_manifest_from_image_root(root: Path, out_csv: Path, seed: int = 42) -> pd.DataFrame:
    if not root.exists():
        raise FileNotFoundError(root)

    rows: list[dict] = []
    skipped = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in VALID_EXTS:
            continue
        label_info = label_from_path(path, root)
        if label_info is None:
            skipped += 1
            continue
        label, label_id, original_label = label_info
        split = split_from_path(path, root) or "unsplit"
        rel = path.relative_to(root).as_posix()
        rows.append({
            "sample_id": f"images_{len(rows):08d}",
            "image_path": str(path.resolve()),
            "rel_path": rel,
            "label": label,
            "label_id": label_id,
            "original_label": original_label,
            "split": split,
            "source": "Dataset/Images",
        })

    if not rows:
        raise ValueError(f"No emotion-labeled images found under {root}")

    df = pd.DataFrame(rows).drop_duplicates("image_path", keep="first").reset_index(drop=True)

    # If there is no explicit val split, carve it from train only. Keep test untouched.
    if "val" not in set(df["split"]):
        train_mask = df["split"].isin(["train", "unsplit"])
        train_df = df[train_mask].copy()
        other_df = df[~train_mask].copy()
        if len(train_df) > 10 and train_df["label_id"].nunique() > 1:
            idx_train, idx_val = train_test_split(
                train_df.index.to_list(),
                test_size=0.15,
                random_state=seed,
                stratify=train_df["label_id"].to_list(),
            )
            df.loc[idx_train, "split"] = "train"
            df.loc[idx_val, "split"] = "val"
        else:
            df.loc[train_mask, "split"] = "train"

    # If there is still no test split, create one from train.
    if "test" not in set(df["split"]):
        train_df = df[df["split"] == "train"].copy()
        if len(train_df) > 20 and train_df["label_id"].nunique() > 1:
            idx_train, idx_test = train_test_split(
                train_df.index.to_list(),
                test_size=0.15,
                random_state=seed,
                stratify=train_df["label_id"].to_list(),
            )
            df.loc[idx_train, "split"] = "train"
            df.loc[idx_test, "split"] = "test"

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"[image_root] root={root}")
    print(f"[image_root] labeled={len(df)} skipped_non_emotion={skipped}")
    print(f"[image_root] saved manifest -> {out_csv}")
    return df


def extract_features(manifest: pd.DataFrame, out_csv: Path, force: bool = False, limit: int = 0) -> pd.DataFrame:
    if out_csv.exists() and not force:
        print(f"[features] exists: {out_csv}")
        return pd.read_csv(out_csv)

    rows: list[dict] = []
    work = manifest.head(limit).copy() if limit > 0 else manifest
    total = len(work)
    print(f"[features] extracting {total} images -> {out_csv}")
    for idx, row in work.iterrows():
        sample_id = str(row["sample_id"])
        image_path = str(row["image_path"])
        try:
            with Image.open(image_path) as im:
                values, valids = extract_clinical_features(im)
        except Exception as exc:
            print(f"  [feature err] {sample_id}: {exc}")
            values = np.zeros(len(FEATURE_NAMES), dtype=np.float32)
            valids = np.zeros(len(FEATURE_NAMES), dtype=np.float32)

        out_row: dict = {"sample_id": sample_id, "image_path": image_path}
        for i, name in enumerate(FEATURE_NAMES):
            out_row[name] = float(values[i]) if float(valids[i]) == 1.0 else np.nan
            out_row[f"{name}_valid"] = int(valids[i])
        rows.append(out_row)
        done = len(rows)
        if done % 1000 == 0 or done == total:
            print(f"  [features] {done}/{total}", flush=True)

    out = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)
    valid_cols = [f"{n}_valid" for n in FEATURE_NAMES]
    print(f"[features] saved. mean_validity={out[valid_cols].mean().mean():.3f}")
    return out


def choose_k_if_needed(x_train: np.ndarray, k: int, candidates: list[int]) -> tuple[int, dict]:
    scores = {}
    if k > 0:
        return k, scores
    best_k = candidates[0]
    best_score = -1.0
    for cand in candidates:
        if cand <= 1 or cand >= len(x_train):
            continue
        km = KMeans(n_clusters=cand, random_state=42, n_init=20)
        labels = km.fit_predict(x_train)
        score = float(silhouette_score(x_train, labels)) if len(set(labels)) > 1 else -1.0
        scores[str(cand)] = score
        if score > best_score:
            best_score = score
            best_k = cand
    return best_k, scores


def fit_clusters(manifest: pd.DataFrame, features: pd.DataFrame, k: int, k_candidates: list[int]) -> tuple[pd.DataFrame, dict, Pipeline]:
    df = manifest.merge(features, on=["sample_id", "image_path"], how="left")
    train = df[df["split"] == "train"].copy()
    if train.empty:
        raise ValueError("Train split is empty; cannot fit phenotype clusters.")

    x_train_raw = train[FEATURE_NAMES].to_numpy(dtype=np.float32)
    prep = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    x_train = prep.fit_transform(x_train_raw)
    chosen_k, silhouette_scores = choose_k_if_needed(x_train, k, k_candidates)
    km = KMeans(n_clusters=chosen_k, random_state=42, n_init=50)
    train_clusters = km.fit_predict(x_train)

    x_all = prep.transform(df[FEATURE_NAMES].to_numpy(dtype=np.float32))
    all_clusters = km.predict(x_all)
    distances = km.transform(x_all)
    cluster_distance = distances[np.arange(len(df)), all_clusters]

    df["phenotype_cluster"] = all_clusters.astype(int)
    df["phenotype_distance"] = cluster_distance.astype(float)

    valid_cols = [f"{n}_valid" for n in FEATURE_NAMES]
    report = {
        "k": int(chosen_k),
        "k_selection_silhouette": silhouette_scores,
        "train_silhouette": float(silhouette_score(x_train, train_clusters)) if chosen_k > 1 else None,
        "rows": int(len(df)),
        "split_cluster_counts": {
            split: {str(k): int(v) for k, v in part["phenotype_cluster"].value_counts().sort_index().items()}
            for split, part in df.groupby("split")
        },
        "label_cluster_counts": {
            label: {str(k): int(v) for k, v in part["phenotype_cluster"].value_counts().sort_index().items()}
            for label, part in df.groupby("label")
        },
        "feature_validity_mean": float(df[valid_cols].mean().mean()),
    }

    cluster_summaries = {}
    train_with_clusters = df[df["split"] == "train"].copy()
    global_means = train_with_clusters[FEATURE_NAMES].mean(numeric_only=True)
    global_stds = train_with_clusters[FEATURE_NAMES].std(numeric_only=True).replace(0, np.nan)
    for cluster_id, part in train_with_clusters.groupby("phenotype_cluster"):
        means = part[FEATURE_NAMES].mean(numeric_only=True)
        z = ((means - global_means) / global_stds).replace([np.inf, -np.inf], np.nan).dropna()
        top_high = z.sort_values(ascending=False).head(6)
        top_low = z.sort_values(ascending=True).head(6)
        cluster_summaries[str(int(cluster_id))] = {
            "train_count": int(len(part)),
            "label_dist": {str(k): int(v) for k, v in part["label"].value_counts().items()},
            "top_high_features": {str(k): float(v) for k, v in top_high.items()},
            "top_low_features": {str(k): float(v) for k, v in top_low.items()},
            "mean_distance": float(part["phenotype_distance"].mean()),
        }
    report["cluster_summaries"] = cluster_summaries

    full_pipe = Pipeline([
        ("prep", prep),
        ("kmeans", km),
    ])
    return df, report, full_pipe


def make_embedding(df: pd.DataFrame) -> tuple[np.ndarray, str]:
    x = df[FEATURE_NAMES].to_numpy(dtype=np.float32)
    x = SimpleImputer(strategy="median").fit_transform(x)
    x = StandardScaler().fit_transform(x)
    try:
        import umap  # type: ignore

        reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=25, min_dist=0.1)
        return reducer.fit_transform(x), "UMAP"
    except Exception:
        reducer = PCA(n_components=2, random_state=42)
        return reducer.fit_transform(x), "PCA"


def save_scatter(df: pd.DataFrame, out_png: Path) -> str:
    emb, method = make_embedding(df)
    plot_df = df.copy()
    plot_df["x"] = emb[:, 0]
    plot_df["y"] = emb[:, 1]
    plt.figure(figsize=(9, 7))
    for cid, part in plot_df.groupby("phenotype_cluster"):
        plt.scatter(part["x"], part["y"], s=9, alpha=0.55, label=f"Cluster {cid}")
    plt.title(f"Phenotype clusters ({method})")
    plt.xlabel(f"{method} 1")
    plt.ylabel(f"{method} 2")
    plt.legend(markerscale=2, fontsize=8)
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=160)
    plt.close()
    return method


def make_thumb(src: str, dst: Path, size: int = 150) -> bool:
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((size, size), Image.LANCZOS)
            canvas = Image.new("RGB", (size, size), "white")
            x = (size - im.width) // 2
            y = (size - im.height) // 2
            canvas.paste(im, (x, y))
            dst.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(dst, "JPEG", quality=84)
        return True
    except Exception:
        return False


def write_html_report(df: pd.DataFrame, report: dict, out_html: Path, n_examples: int) -> None:
    assets = out_html.parent / "phenotype_report_assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir(parents=True, exist_ok=True)
    scatter_name = "clusters_scatter.png"
    method = save_scatter(df, assets / scatter_name)

    sections = []
    for cid in sorted(df["phenotype_cluster"].unique()):
        part = df[df["phenotype_cluster"] == cid].copy()
        part = part.sort_values("phenotype_distance", ascending=True).head(n_examples)
        summary = report["cluster_summaries"].get(str(int(cid)), {})
        thumbs = []
        for i, row in enumerate(part.itertuples(index=False)):
            thumb_name = f"cluster_{int(cid)}_{i:03d}_{safe_name(row.sample_id)}.jpg"
            if make_thumb(str(row.image_path), assets / thumb_name):
                thumbs.append(
                    "<figure>"
                    f"<img src='phenotype_report_assets/{thumb_name}' loading='lazy'>"
                    f"<figcaption>{html.escape(str(row.label))}<br>{html.escape(str(row.sample_id))}</figcaption>"
                    "</figure>"
                )
        high = summary.get("top_high_features", {})
        low = summary.get("top_low_features", {})
        label_dist = summary.get("label_dist", {})
        sections.append(f"""
        <section>
          <h2>Cluster {int(cid)}</h2>
          <p><b>Train count:</b> {summary.get("train_count", 0)}
             <b>Label dist:</b> {html.escape(json.dumps(label_dist, ensure_ascii=False))}</p>
          <div class="cols">
            <div><h3>High features</h3><ul>{''.join(f'<li>{html.escape(k)}: {v:.2f}z</li>' for k, v in high.items())}</ul></div>
            <div><h3>Low features</h3><ul>{''.join(f'<li>{html.escape(k)}: {v:.2f}z</li>' for k, v in low.items())}</ul></div>
          </div>
          <div class="grid">{''.join(thumbs)}</div>
        </section>
        """)

    style = """
    body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #202124; }
    h1 { margin-bottom: 4px; }
    .meta { color: #5f6368; margin-bottom: 20px; }
    img.scatter { max-width: 980px; width: 100%; border: 1px solid #ddd; }
    section { border-top: 1px solid #ddd; padding-top: 18px; margin-top: 24px; }
    .cols { display: grid; grid-template-columns: repeat(2, minmax(260px, 1fr)); gap: 16px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
    figure { margin: 0; border: 1px solid #ddd; padding: 6px; background: #fafafa; }
    figure img { width: 100%; aspect-ratio: 1 / 1; object-fit: contain; background: white; }
    figcaption { font-size: 11px; color: #555; overflow-wrap: anywhere; }
    code { background: #f1f3f4; padding: 2px 4px; border-radius: 4px; }
    """
    html_text = f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>Phenotype Cluster Report</title>
  <style>{style}</style>
</head>
<body>
  <h1>Clinical Phenotype Discovery</h1>
  <div class="meta">
    k={report["k"]}, rows={report["rows"]}, train silhouette={report["train_silhouette"]},
    projection={method}
  </div>
  <img class="scatter" src="phenotype_report_assets/{scatter_name}">
  <h2>Split Cluster Counts</h2>
  <pre>{html.escape(json.dumps(report["split_cluster_counts"], indent=2, ensure_ascii=False))}</pre>
  {''.join(sections)}
</body>
</html>
"""
    out_html.write_text(html_text, encoding="utf-8")


def parse_candidates(text: str) -> list[int]:
    out = []
    for part in text.split(","):
        part = part.strip()
        if part:
            out.append(int(part))
    return out or [3, 4, 5, 6]


def stratified_limit(df: pd.DataFrame, limit: int, seed: int = 42) -> pd.DataFrame:
    if limit <= 0 or limit >= len(df):
        return df
    parts = []
    grouped = list(df.groupby(["split", "label_id"], sort=False))
    base = max(1, limit // max(len(grouped), 1))
    remaining = limit
    for _, part in grouped:
        take = min(len(part), base)
        parts.append(part.sample(n=take, random_state=seed))
        remaining -= take
    if remaining > 0:
        used = pd.concat(parts).index if parts else []
        rest = df.drop(index=used)
        if len(rest):
            parts.append(rest.sample(n=min(remaining, len(rest)), random_state=seed))
    return pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["image-root", "manifest"], default="image-root")
    ap.add_argument("--image-root", type=Path, default=DEFAULT_IMAGE_ROOT)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--features-out", type=Path, default=None)
    ap.add_argument("--manifest-out", type=Path, default=None)
    ap.add_argument("--k", type=int, default=4, help="0 = choose by train silhouette over --k-candidates")
    ap.add_argument("--k-candidates", default="3,4,5,6")
    ap.add_argument("--examples", type=int, default=24)
    ap.add_argument("--force-features", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    features_out = args.features_out or (out_dir / "features_clean.csv")
    manifest_out = args.manifest_out or (out_dir / "manifest_multitask.csv")
    source_manifest = out_dir / "manifest_from_dataset_images.csv"
    report_json = out_dir / "cluster_report.json"
    report_html = out_dir / "phenotype_report.html"

    if args.source == "image-root":
        manifest = build_manifest_from_image_root(args.image_root, source_manifest)
    else:
        manifest = load_manifest(args.manifest)
    if args.limit > 0:
        manifest = stratified_limit(manifest, args.limit)
    print(f"[manifest] rows={len(manifest)} split={manifest['split'].value_counts().to_dict()}")
    print(f"[manifest] labels={manifest['label'].value_counts().to_dict()}")

    features = extract_features(manifest, features_out, force=args.force_features, limit=0)
    clustered, report, _ = fit_clusters(
        manifest,
        features,
        k=args.k,
        k_candidates=parse_candidates(args.k_candidates),
    )
    clustered.to_csv(manifest_out, index=False)
    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_html_report(clustered, report, report_html, args.examples)

    print(f"[out] features: {features_out}")
    print(f"[out] manifest: {manifest_out}")
    print(f"[out] report: {report_json}")
    print(f"[out] html: {report_html}")
    print(f"[done] k={report['k']} train_silhouette={report['train_silhouette']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
