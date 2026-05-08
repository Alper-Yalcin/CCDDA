from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from inference_sdk import InferenceHTTPClient
from tqdm import tqdm


ROOT = Path(__file__).resolve().parent
IMAGE_ROOT = ROOT / "Images" / "Emotion"
OUT_IMAGE_ROOT = ROOT / "Images" / "Emotion_Roboflow_DrawingFacialEmotions"
OUT_TEXT_ROOT = ROOT / "Texts" / "Emotion_Roboflow_DrawingFacialEmotions"

MODEL_ID = "drawing-facial-emotions/1"
API_URL = "https://serverless.roboflow.com"
CONFIDENCE = 0.01

thread_local = threading.local()


def get_client() -> InferenceHTTPClient:
    client = getattr(thread_local, "client", None)
    if client is None:
        api_key = os.environ.get("ROBOFLOW_API_KEY")
        if not api_key:
            raise RuntimeError("Set ROBOFLOW_API_KEY before running this script.")
        client = InferenceHTTPClient(api_url=API_URL, api_key=api_key)
        thread_local.client = client
    return client


def map_model_class(model_class: str) -> str:
    value = model_class.lower().replace("-", "_").replace(" ", "_")
    if "happy" in value or "joy" in value:
        return "Happy"
    if "sad" in value:
        return "Sad"
    if "angry" in value or "anger" in value:
        return "Angry"
    if "fear" in value or "scared" in value or "anxiety" in value:
        return "Fear"
    if "surpris" in value:
        return "Surprise"
    if "neutral" in value:
        return "Neutral"
    return "OtherDetected"


def iter_images() -> list[Path]:
    files: list[Path] = []
    for split in ("train", "test"):
        for source_label in ("Happiness", "Sadness"):
            files.extend(sorted((IMAGE_ROOT / split / source_label).glob("*.jpg")))
    return files


def split_and_source(path: Path) -> tuple[str, str]:
    return path.parent.parent.name, path.parent.name


def reset_output_dirs() -> None:
    for path in (OUT_IMAGE_ROOT, OUT_TEXT_ROOT):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)


def infer_one(path: Path) -> dict[str, str]:
    split, source_label = split_and_source(path)
    row: dict[str, str] = {
        "image_id": path.stem,
        "split": split,
        "source_label": source_label,
        "model_id": MODEL_ID,
        "source_path": str(path.relative_to(ROOT)),
        "target_path": "",
        "prediction_status": "ok",
        "detection_count": "0",
        "top_model_class": "",
        "predicted_label": "NoDetection",
        "confidence": "0.000000",
        "x": "",
        "y": "",
        "width": "",
        "height": "",
        "all_predictions_json": "[]",
        "error": "",
    }

    try:
        try:
            result = get_client().infer(str(path), model_id=MODEL_ID, confidence=CONFIDENCE)
        except TypeError:
            result = get_client().infer(str(path), model_id=MODEL_ID)
        predictions = result.get("predictions", []) if isinstance(result, dict) else []
        predictions = sorted(
            predictions,
            key=lambda prediction: float(prediction.get("confidence", 0.0)),
            reverse=True,
        )
        row["detection_count"] = str(len(predictions))
        row["all_predictions_json"] = json.dumps(predictions, ensure_ascii=False)

        if not predictions:
            return row

        top = predictions[0]
        model_class = str(top.get("class", ""))
        mapped_label = map_model_class(model_class)
        confidence = float(top.get("confidence", 0.0))

        row.update(
            {
                "top_model_class": model_class,
                "predicted_label": mapped_label,
                "confidence": f"{confidence:.6f}",
                "x": str(top.get("x", "")),
                "y": str(top.get("y", "")),
                "width": str(top.get("width", "")),
                "height": str(top.get("height", "")),
            }
        )

        if mapped_label not in {"NoDetection", "OtherDetected"}:
            target = OUT_IMAGE_ROOT / split / mapped_label / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            row["target_path"] = str(target.relative_to(ROOT))
        return row
    except Exception as exc:
        row["prediction_status"] = "error"
        row["error"] = f"{type(exc).__name__}: {exc}"
        return row


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = (
        "image_id",
        "split",
        "source_label",
        "model_id",
        "source_path",
        "target_path",
        "prediction_status",
        "detection_count",
        "top_model_class",
        "predicted_label",
        "confidence",
        "x",
        "y",
        "width",
        "height",
        "all_predictions_json",
        "error",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_counts(rows: list[dict[str, str]]) -> None:
    labels = sorted({row["predicted_label"] for row in rows})
    lines = ["split,label,count"]
    for split in ("train", "test"):
        for label in labels:
            count = sum(
                1
                for row in rows
                if row["split"] == split and row["predicted_label"] == label
            )
            lines.append(f"{split},{label},{count}")
    (OUT_TEXT_ROOT / "class_counts.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    model_classes = sorted({row["top_model_class"] or "NoDetection" for row in rows})
    lines = ["split,model_class,count"]
    for split in ("train", "test"):
        for model_class in model_classes:
            count = sum(
                1
                for row in rows
                if row["split"] == split
                and (row["top_model_class"] or "NoDetection") == model_class
            )
            lines.append(f"{split},{model_class},{count}")
    (OUT_TEXT_ROOT / "model_class_counts.csv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_readme(rows: list[dict[str, str]]) -> None:
    detected = sum(1 for row in rows if row["predicted_label"] != "NoDetection")
    errors = sum(1 for row in rows if row["prediction_status"] == "error")
    readme = f"""# Emotion Roboflow Drawing Facial Emotions

Images were processed with Roboflow model `{MODEL_ID}`.

This model is an object detection model, not a whole-image classifier. It returns
face/expression detections when it finds them. Images without detections are kept
in `predictions.csv` as `NoDetection` and are not copied into class folders.

Source model page:
https://universe.roboflow.com/tsz-cheung-shawn-wei-jmvvc/drawing-facial-emotions/model/1

## Output

- Images: `Images/Emotion_Roboflow_DrawingFacialEmotions/<split>/<label>/*.jpg`
- Predictions: `Texts/Emotion_Roboflow_DrawingFacialEmotions/predictions.csv`
- Counts: `Texts/Emotion_Roboflow_DrawingFacialEmotions/class_counts.csv`
- Native model class counts: `Texts/Emotion_Roboflow_DrawingFacialEmotions/model_class_counts.csv`

## Summary

- Total images processed: {len(rows)}
- Images with a detection: {detected}
- Prediction errors: {errors}

## Note

Roboflow reports this version as trained on 432 images with mAP@50 25.4%,
precision 51.0%, and recall 20.1%. Treat this output as pseudo-labels that need
manual review before thesis-grade ground truth use.
"""
    (OUT_TEXT_ROOT / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    reset_output_dirs()
    files = iter_images()
    if args.offset:
        files = files[args.offset :]
    if args.limit:
        files = files[: args.limit]

    rows: list[dict[str, str]] = []
    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(infer_one, path) for path in files]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Roboflow inference"):
            rows.append(future.result())

    rows.sort(key=lambda row: (row["split"], row["source_label"], row["image_id"]))
    write_csv(OUT_TEXT_ROOT / "predictions.csv", rows)
    write_counts(rows)
    write_readme(rows)

    elapsed = time.time() - start
    print(f"processed={len(rows)} elapsed_seconds={elapsed:.1f}")
    print((OUT_TEXT_ROOT / "class_counts.csv").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
