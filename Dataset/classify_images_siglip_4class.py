from __future__ import annotations

import csv
import shutil
from pathlib import Path

import torch
from PIL import Image
from tqdm import tqdm
from transformers import AutoModel, AutoProcessor


ROOT = Path(__file__).resolve().parent
IMAGE_ROOT = ROOT / "Images" / "Emotion"
OUT_IMAGE_ROOT = ROOT / "Images" / "Emotion_SigLIP_4Class"
OUT_TEXT_ROOT = ROOT / "Texts" / "Emotion_SigLIP_4Class"

MODEL_ID = "google/siglip-base-patch16-224"
BATCH_SIZE = 32

LABEL_PROMPTS = {
    "Happy": "a child drawing expressing happiness",
    "Sad": "a child drawing expressing sadness",
    "Angry": "a child drawing expressing anger",
    "Fear": "a child drawing expressing fear or anxiety",
}


def reset_output_dirs() -> None:
    for path in (OUT_IMAGE_ROOT, OUT_TEXT_ROOT):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    for split in ("train", "test"):
        for label in LABEL_PROMPTS:
            (OUT_IMAGE_ROOT / split / label).mkdir(parents=True, exist_ok=True)


def iter_images() -> list[Path]:
    files: list[Path] = []
    for split in ("train", "test"):
        for source_label in ("Happiness", "Sadness"):
            files.extend(sorted((IMAGE_ROOT / split / source_label).glob("*.jpg")))
    return files


def load_images(paths: list[Path]) -> list[Image.Image]:
    images: list[Image.Image] = []
    for path in paths:
        with Image.open(path) as image:
            images.append(image.convert("RGB"))
    return images


def split_and_source(path: Path) -> tuple[str, str]:
    source_label = path.parent.name
    split = path.parent.parent.name
    return split, source_label


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = (
        "image_id",
        "split",
        "source_label",
        "predicted_label",
        "confidence",
        "score_Happy",
        "score_Sad",
        "score_Angry",
        "score_Fear",
        "source_path",
        "target_path",
        "model_id",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def class_counts(rows: list[dict[str, str]]) -> str:
    lines = ["split,label,count"]
    for split in ("train", "test"):
        for label in LABEL_PROMPTS:
            count = sum(
                1
                for row in rows
                if row["split"] == split and row["predicted_label"] == label
            )
            lines.append(f"{split},{label},{count}")
    return "\n".join(lines) + "\n"


def write_readme(counts_csv: str) -> None:
    readme = f"""# Emotion SigLIP 4-Class Dataset

This dataset was automatically classified from the local KIDO-style child
drawing images using a zero-shot vision-language model.

## Model

- Model: `{MODEL_ID}`
- Method: zero-shot image classification with text prompts

## Labels and Prompts

| Label | Prompt |
| --- | --- |
| Happy | {LABEL_PROMPTS['Happy']} |
| Sad | {LABEL_PROMPTS['Sad']} |
| Angry | {LABEL_PROMPTS['Angry']} |
| Fear | {LABEL_PROMPTS['Fear']} |

## Files

- Images: `Images/Emotion_SigLIP_4Class/<split>/<label>/*.jpg`
- Predictions: `Texts/Emotion_SigLIP_4Class/predictions.csv`
- Counts: `Texts/Emotion_SigLIP_4Class/class_counts.csv`

## Class Counts

```csv
{counts_csv.strip()}
```

## Important Note

These are automatic model predictions, not human-verified clinical labels. Use
them as pseudo-labels and manually review a sample, especially low-confidence
predictions, before presenting them as final ground truth.
"""
    (OUT_TEXT_ROOT / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    reset_output_dirs()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModel.from_pretrained(MODEL_ID).to(device)
    model.eval()

    labels = list(LABEL_PROMPTS)
    prompts = [LABEL_PROMPTS[label] for label in labels]
    files = iter_images()
    rows: list[dict[str, str]] = []

    for start in tqdm(range(0, len(files), BATCH_SIZE), desc="Classifying images"):
        batch_paths = files[start : start + BATCH_SIZE]
        images = load_images(batch_paths)
        inputs = processor(
            text=prompts,
            images=images,
            return_tensors="pt",
            padding="max_length",
        )
        inputs = {key: value.to(device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            probs = outputs.logits_per_image.softmax(dim=1).cpu()

        for path, prob in zip(batch_paths, probs):
            best_idx = int(prob.argmax())
            predicted_label = labels[best_idx]
            confidence = float(prob[best_idx])
            split, source_label = split_and_source(path)
            target = OUT_IMAGE_ROOT / split / predicted_label / path.name
            shutil.copy2(path, target)

            rows.append(
                {
                    "image_id": path.stem,
                    "split": split,
                    "source_label": source_label,
                    "predicted_label": predicted_label,
                    "confidence": f"{confidence:.6f}",
                    "score_Happy": f"{float(prob[labels.index('Happy')]):.6f}",
                    "score_Sad": f"{float(prob[labels.index('Sad')]):.6f}",
                    "score_Angry": f"{float(prob[labels.index('Angry')]):.6f}",
                    "score_Fear": f"{float(prob[labels.index('Fear')]):.6f}",
                    "source_path": str(path.relative_to(ROOT)),
                    "target_path": str(target.relative_to(ROOT)),
                    "model_id": MODEL_ID,
                }
            )

    write_csv(OUT_TEXT_ROOT / "predictions.csv", rows)
    counts_csv = class_counts(rows)
    (OUT_TEXT_ROOT / "class_counts.csv").write_text(counts_csv, encoding="utf-8")
    write_readme(counts_csv)
    print(counts_csv, end="")


if __name__ == "__main__":
    main()
