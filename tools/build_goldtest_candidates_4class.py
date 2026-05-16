from __future__ import annotations

import argparse
import csv
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = ROOT / "Dataset"
IMAGE_ROOT = DATASET_ROOT / "Images"
TEXT_ROOT = DATASET_ROOT / "Texts"
DEFAULT_OUT = IMAGE_ROOT / "GoldTest_Candidates_Auto4Class"
DEFAULT_METADATA_OUT = TEXT_ROOT / "GoldTest_Candidates_Auto4Class"

SOURCE_IMAGE_ROOTS = ("Education", "Emotion", "Gender")
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
LABELS = ("Happy", "Sad", "Angry", "Fear")
LABEL_DIRS = {
    "Happy": "happy",
    "Sad": "sad",
    "Angry": "angry",
    "Fear": "fear",
}

TEXT_LABEL_MAP = {
    "Happy": "Happy",
    "Happiness": "Happy",
    "Sad": "Sad",
    "Sadness": "Sad",
    "Anger": "Angry",
    "Angry": "Angry",
    "Anxiety": "Fear",
    "Fear": "Fear",
}


@dataclass(frozen=True)
class TextInfo:
    label: str
    confidence: str
    rule: str
    text_tr: str
    text_en: str
    source_label: str


@dataclass(frozen=True)
class VisualInfo:
    label: str
    confidence: float
    score_happy: str
    score_sad: str
    score_angry: str
    score_fear: str
    model_id: str


@dataclass(frozen=True)
class PhenotypeInfo:
    cluster: str
    distance: str
    clinical_label: str
    clinical_margin: float
    score_happy: float
    score_sad: float
    score_angry: float
    score_fear: float


@dataclass(frozen=True)
class Decision:
    label: str
    reason: str
    review_flag: str
    review_priority: int


def read_text_labels() -> dict[str, TextInfo]:
    out: dict[str, TextInfo] = {}
    for split in ("Train", "Test"):
        path = TEXT_ROOT / "Emotion_4Class" / f"Emotion_4Class_{split}.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                label = TEXT_LABEL_MAP.get(row["label"], row["label"])
                out[row["image_id"]] = TextInfo(
                    label=label,
                    confidence=row.get("confidence", ""),
                    rule=row.get("rule", ""),
                    text_tr=row.get("text_tr", ""),
                    text_en=row.get("text_en", ""),
                    source_label=row.get("source_label", ""),
                )
    return out


def read_visual_labels() -> dict[str, VisualInfo]:
    path = TEXT_ROOT / "Emotion_SigLIP_4Class" / "predictions.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    out: dict[str, VisualInfo] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            out[row["image_id"]] = VisualInfo(
                label=TEXT_LABEL_MAP.get(row["predicted_label"], row["predicted_label"]),
                confidence=float(row["confidence"]),
                score_happy=row.get("score_Happy", ""),
                score_sad=row.get("score_Sad", ""),
                score_angry=row.get("score_Angry", ""),
                score_fear=row.get("score_Fear", ""),
                model_id=row.get("model_id", ""),
            )
    return out


def _to_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _zscore(row: dict[str, str], stats: dict[str, tuple[float, float]], name: str) -> float:
    mean, std = stats[name]
    if std == 0:
        return 0.0
    return (_to_float(row.get(name, "0")) - mean) / std


def _raw(row: dict[str, str], name: str) -> float:
    return _to_float(row.get(name, "0"))


def _clinical_scores(row: dict[str, str], stats: dict[str, tuple[float, float]]) -> dict[str, float]:
    z = lambda name: _zscore(row, stats, name)
    edge_x = abs(_raw(row, "centroid_x_norm") - 0.5) * 2.0
    upper_pull = max(0.0, 0.5 - _raw(row, "centroid_y_norm")) * 2.0

    return {
        "Happy": (
            0.95 * z("warm_ratio")
            + 0.65 * z("unique_hue_count")
            + 0.45 * z("bbox_area_ratio")
            + 0.35 * z("fg_area_ratio")
            - 0.55 * z("dark_color_ratio")
            - 0.35 * z("shading_ratio")
            - 0.25 * z("empty_space_ratio")
        ),
        "Sad": (
            0.90 * z("empty_space_ratio")
            - 0.65 * z("fg_area_ratio")
            - 0.45 * z("bbox_area_ratio")
            - 0.35 * z("stroke_darkness_mean")
            - 0.30 * z("unique_hue_count")
            + 0.25 * z("dark_color_ratio")
        ),
        "Angry": (
            0.85 * z("stroke_darkness_mean")
            + 0.70 * z("stroke_darkness_std")
            + 0.65 * z("shading_ratio")
            + 0.55 * z("dark_color_ratio")
            + 0.45 * z("sharp_angle_ratio")
            + 0.40 * z("component_count_norm")
            + 0.35 * z("skeleton_break_count_norm")
            + 0.20 * z("warm_ratio")
            - 0.25 * z("empty_space_ratio")
        ),
        "Fear": (
            0.75 * z("empty_space_ratio")
            - 0.45 * z("fg_area_ratio")
            - 0.35 * z("bbox_area_ratio")
            + 0.45 * z("dark_color_ratio")
            + 0.40 * edge_x
            + 0.30 * upper_pull
            + 0.25 * z("dominant_orientation_abs")
            + 0.20 * z("skeleton_break_count_norm")
            - 0.20 * z("warm_ratio")
        ),
    }


def read_phenotypes() -> dict[str, PhenotypeInfo]:
    path = ROOT / "out" / "phenotype_images" / "manifest_multitask.csv"
    out: dict[str, PhenotypeInfo] = {}
    if not path.exists():
        return out

    numeric_features = (
        "fg_area_ratio",
        "empty_space_ratio",
        "bbox_area_ratio",
        "centroid_x_norm",
        "centroid_y_norm",
        "stroke_darkness_mean",
        "stroke_darkness_std",
        "component_count_norm",
        "skeleton_break_count_norm",
        "shading_ratio",
        "unique_hue_count",
        "warm_ratio",
        "dark_color_ratio",
        "sharp_angle_ratio",
        "dominant_orientation_abs",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    stats: dict[str, tuple[float, float]] = {}
    for name in numeric_features:
        values = [_to_float(row.get(name, "0")) for row in rows]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        stats[name] = (mean, variance ** 0.5)

    for row in rows:
        stem = Path(row["image_path"]).stem
        scores = _clinical_scores(row, stats)
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        margin = ordered[0][1] - ordered[1][1]
        out[stem] = PhenotypeInfo(
            cluster=row.get("phenotype_cluster", ""),
            distance=row.get("phenotype_distance", ""),
            clinical_label=ordered[0][0],
            clinical_margin=margin,
            score_happy=scores["Happy"],
            score_sad=scores["Sad"],
            score_angry=scores["Angry"],
            score_fear=scores["Fear"],
        )
    return out


def iter_source_images() -> list[Path]:
    files: list[Path] = []
    for root_name in SOURCE_IMAGE_ROOTS:
        root = IMAGE_ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in VALID_EXTS:
                files.append(path)
    return sorted(files)


def fallback_label_from_stem(stem: str) -> str:
    suffix = stem.rsplit("-", 1)[-1].upper()
    if suffix == "H":
        return "Happy"
    if suffix == "S":
        return "Sad"
    return "Sad"


def decide(
    image_id: str,
    text: TextInfo | None,
    visual: VisualInfo | None,
    phenotype: PhenotypeInfo | None,
) -> Decision:
    text_label = text.label if text else fallback_label_from_stem(image_id)
    clinical_label = phenotype.clinical_label if phenotype else ""
    clinical_margin = phenotype.clinical_margin if phenotype else 0.0

    if visual is None:
        return Decision(text_label, "text_only_no_visual_prediction", "missing_visual", 2)

    visual_label = visual.label
    conflict = visual_label != text_label

    if text_label in {"Happy", "Angry", "Fear"}:
        if clinical_label and clinical_label != text_label and clinical_margin >= 1.00:
            return Decision(text_label, "text_primary_clinical_conflict", "clinical_conflict", 1)
        if conflict and visual.confidence >= 0.55:
            return Decision(text_label, "text_primary_visual_conflict", "visual_conflict", 1)
        return Decision(text_label, "text_clinical_primary", "", 3)

    if text_label == "Sad" and clinical_label in {"Angry", "Fear"}:
        if visual_label == clinical_label and visual.confidence >= 0.45 and clinical_margin >= 0.45:
            return Decision(clinical_label, "text_sad_clinical_visual_agree", "promoted_from_sad", 1)
        if clinical_margin >= 1.25:
            return Decision(clinical_label, "text_sad_strong_clinical_signal", "promoted_from_sad", 1)

    if clinical_label and clinical_label != text_label and clinical_margin >= 1.00:
        return Decision(text_label, "text_primary_clinical_conflict", "clinical_conflict", 1)
    if conflict and visual.confidence >= 0.65:
        return Decision(text_label, "text_primary_visual_conflict", "visual_conflict", 1)

    return Decision(text_label, "text_clinical_primary", "", 3 if not conflict else 2)


def reset_output(path: Path, force: bool) -> None:
    if path.exists():
        if not force:
            raise FileExistsError(f"{path} exists. Re-run with --force to rebuild it.")
        shutil.rmtree(path)
    for label in LABELS:
        (path / LABEL_DIRS[label]).mkdir(parents=True, exist_ok=True)


def reset_metadata(path: Path, force: bool) -> None:
    if path.exists():
        if not force:
            raise FileExistsError(f"{path} exists. Re-run with --force to rebuild it.")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_readme(metadata_root: Path, unique_counts: Counter[str], file_counts: Counter[str], total_files: int) -> None:
    lines = [
        "# GoldTest Candidates Auto4Class",
        "",
        "Automatically prepared review folders for a future human-corrected gold test set.",
        "",
        "Labels: Happy, Sad, Angry, Fear.",
        "",
        "Method:",
        "- Text-derived 4-class label is the primary signal.",
        "- Clinical feature scores are computed from the Chapter 6 phenotype feature table.",
        "- Sad items can be promoted to Angry/Fear when clinical evidence is strong, or when clinical and visual evidence agree.",
        "- SigLIP image prediction is kept as a secondary visual signal and conflict marker.",
        "- Phenotype cluster, distance, clinical label, and clinical class scores are preserved in metadata.",
        "",
        "Folder layout is flat: fear, happy, sad, angry.",
        "Only one file is copied for each unique drawing ID because the source tree contains three duplicate copies of each drawing.",
        "",
        "Unique drawing counts:",
        "label,count",
    ]
    for label in LABELS:
        lines.append(f"{label},{unique_counts[label]}")
    lines.extend(["", "Copied file counts:", "label,count"])
    for label in LABELS:
        lines.append(f"{label},{file_counts[label]}")
    lines.extend([
        "",
        f"Total copied files: {total_files}",
        "",
        "Important: these are automatic candidate labels, not final clinical ground truth.",
        "Use _metadata/review_queue.csv first; it prioritizes visual/text conflicts and promoted samples.",
        "",
    ])
    (metadata_root / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--metadata-out", type=Path, default=DEFAULT_METADATA_OUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    out_root = args.out if args.out.is_absolute() else ROOT / args.out
    metadata_root = args.metadata_out if args.metadata_out.is_absolute() else ROOT / args.metadata_out
    reset_output(out_root, args.force)
    reset_metadata(metadata_root, args.force)

    text_labels = read_text_labels()
    visual_labels = read_visual_labels()
    phenotypes = read_phenotypes()
    source_images = iter_source_images()
    by_id: dict[str, list[Path]] = {}
    for path in source_images:
        by_id.setdefault(path.stem, []).append(path)
    unique_ids = sorted(by_id)

    decisions: dict[str, Decision] = {}
    unique_rows: list[dict[str, str]] = []
    unique_counts: Counter[str] = Counter()

    for image_id in unique_ids:
        text = text_labels.get(image_id)
        visual = visual_labels.get(image_id)
        phenotype = phenotypes.get(image_id)
        decision = decide(image_id, text, visual, phenotype)
        decisions[image_id] = decision
        unique_counts[decision.label] += 1
        unique_rows.append({
            "image_id": image_id,
            "final_label": decision.label,
            "decision_reason": decision.reason,
            "review_flag": decision.review_flag,
            "review_priority": str(decision.review_priority),
            "text_label": text.label if text else "",
            "text_confidence": text.confidence if text else "",
            "text_rule": text.rule if text else "",
            "source_label": text.source_label if text else "",
            "visual_label": visual.label if visual else "",
            "visual_confidence": f"{visual.confidence:.6f}" if visual else "",
            "score_Happy": visual.score_happy if visual else "",
            "score_Sad": visual.score_sad if visual else "",
            "score_Angry": visual.score_angry if visual else "",
            "score_Fear": visual.score_fear if visual else "",
            "phenotype_cluster": phenotype.cluster if phenotype else "",
            "phenotype_distance": phenotype.distance if phenotype else "",
            "clinical_label": phenotype.clinical_label if phenotype else "",
            "clinical_margin": f"{phenotype.clinical_margin:.6f}" if phenotype else "",
            "clinical_score_Happy": f"{phenotype.score_happy:.6f}" if phenotype else "",
            "clinical_score_Sad": f"{phenotype.score_sad:.6f}" if phenotype else "",
            "clinical_score_Angry": f"{phenotype.score_angry:.6f}" if phenotype else "",
            "clinical_score_Fear": f"{phenotype.score_fear:.6f}" if phenotype else "",
            "text_tr": text.text_tr if text else "",
            "text_en": text.text_en if text else "",
        })

    file_rows: list[dict[str, str]] = []
    file_counts: Counter[str] = Counter()
    for image_id in unique_ids:
        decision = decisions[image_id]
        sources = sorted(
            by_id[image_id],
            key=lambda path: (
                0 if "Emotion" in path.parts else 1,
                0 if "Education" in path.parts else 1,
                str(path),
            ),
        )
        source = sources[0]
        target = out_root / LABEL_DIRS[decision.label] / source.name
        shutil.copy2(source, target)
        file_counts[decision.label] += 1
        file_rows.append({
            "image_id": image_id,
            "final_label": decision.label,
            "source_path": str(source.relative_to(ROOT)),
            "target_path": str(target.relative_to(ROOT)),
            "duplicate_source_count": str(len(sources)),
            "all_source_paths": " | ".join(str(path.relative_to(ROOT)) for path in sources),
        })

    unique_fieldnames = [
        "image_id",
        "final_label",
        "decision_reason",
        "review_flag",
        "review_priority",
        "text_label",
        "text_confidence",
        "text_rule",
        "source_label",
        "visual_label",
        "visual_confidence",
        "score_Happy",
        "score_Sad",
        "score_Angry",
        "score_Fear",
        "phenotype_cluster",
        "phenotype_distance",
        "clinical_label",
        "clinical_margin",
        "clinical_score_Happy",
        "clinical_score_Sad",
        "clinical_score_Angry",
        "clinical_score_Fear",
        "text_tr",
        "text_en",
    ]
    file_fieldnames = [
        "image_id",
        "final_label",
        "source_path",
        "target_path",
        "duplicate_source_count",
        "all_source_paths",
    ]
    metadata = metadata_root
    write_csv(metadata / "unique_decisions.csv", unique_rows, unique_fieldnames)
    write_csv(metadata / "all_copied_files.csv", file_rows, file_fieldnames)

    review_rows = sorted(
        unique_rows,
        key=lambda row: (
            int(row["review_priority"]),
            row["final_label"],
            row["image_id"],
        ),
    )
    write_csv(metadata / "review_queue.csv", review_rows, unique_fieldnames)

    counts_rows = []
    for label in LABELS:
        counts_rows.append({
            "label": label,
            "unique_drawings": str(unique_counts[label]),
            "copied_files": str(file_counts[label]),
        })
    write_csv(metadata / "class_counts.csv", counts_rows, ["label", "unique_drawings", "copied_files"])
    write_readme(metadata, unique_counts, file_counts, len(file_rows))

    print(f"Output: {out_root}")
    print(f"Metadata: {metadata_root}")
    print("label,unique_drawings,copied_files")
    for label in LABELS:
        print(f"{label},{unique_counts[label]},{file_counts[label]}")
    print(f"total,{len(unique_ids)},{len(file_rows)}")


if __name__ == "__main__":
    main()
