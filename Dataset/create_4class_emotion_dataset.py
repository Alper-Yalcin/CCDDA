from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEXT_ROOT = ROOT / "Texts" / "Emotion"
IMAGE_ROOT = ROOT / "Images" / "Emotion"

OUT_TEXT_ROOT = ROOT / "Texts" / "Emotion_4Class"
OUT_IMAGE_ROOT = ROOT / "Images" / "Emotion_4Class"

LABELS = ("Happy", "Sadness", "Anger", "Anxiety")

ANXIETY_KEYWORDS = (
    "fear",
    "afraid",
    "scared",
    "frightened",
    "panic",
    "worry",
    "worried",
    "anxious",
    "dark",
    "monster",
    "ghost",
    "nightmare",
    "earthquake",
    "fire",
    "blood",
    "accident",
    "hit by car",
    "car hit",
    "fell",
    "fall down",
    "hospital",
    "doctor",
    "needle",
    "dog bite",
)

ANGER_KEYWORDS = (
    "angry",
    "anger",
    "mad",
    "got mad",
    "fight",
    "quarrel",
    "argue",
    "argument",
    "offended",
    "resent",
    "hit",
    "beat",
    "shout",
    "yell",
    "bully",
    "violence",
    "war",
    "does not let me",
    "not let me",
)


def matches(text: str, keywords: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for keyword in keywords:
        pattern = rf"(?<![a-z]){re.escape(keyword)}(?![a-z])"
        if re.search(pattern, text):
            found.append(keyword)
    return found


def derive_label(source_label: str, text_en: str) -> tuple[str, float, str]:
    source_label = source_label.strip()
    text = (text_en or "").lower()

    if source_label == "Happiness":
        return "Happy", 1.0, "source_happiness"

    if source_label == "Sadness":
        anxiety_matches = matches(text, ANXIETY_KEYWORDS)
        if anxiety_matches:
            return "Anxiety", 0.84, "|".join(anxiety_matches[:5])

        anger_matches = matches(text, ANGER_KEYWORDS)
        if anger_matches:
            return "Anger", 0.84, "|".join(anger_matches[:5])

        return "Sadness", 1.0, "source_sadness_default"

    return "Unknown", 0.0, "unknown_source_label"


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 4:
                continue
            image_id, text_tr, text_en, source_label = row[:4]
            label, confidence, rule = derive_label(source_label, text_en)
            rows.append(
                {
                    "image_id": image_id,
                    "text_tr": text_tr,
                    "text_en": text_en,
                    "source_label": source_label,
                    "label": label,
                    "confidence": f"{confidence:.2f}",
                    "rule": rule,
                }
            )
    return rows


def reset_output_dirs() -> None:
    for path in (OUT_TEXT_ROOT, OUT_IMAGE_ROOT):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    for split in ("train", "test"):
        for label in LABELS:
            (OUT_IMAGE_ROOT / split / label).mkdir(parents=True, exist_ok=True)


def copy_images(split: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    missing: list[str] = []

    for row in rows:
        source = IMAGE_ROOT / split / row["source_label"] / f"{row['image_id']}.jpg"
        target = OUT_IMAGE_ROOT / split / row["label"] / f"{row['image_id']}.jpg"

        row = dict(row)
        row["image_path"] = str(target.relative_to(ROOT))

        if source.exists():
            shutil.copy2(source, target)
            row["image_found"] = "True"
        else:
            missing.append(str(source))
            row["image_found"] = "False"
        copied.append(row)

    if missing:
        (OUT_TEXT_ROOT / f"missing_images_{split}.txt").write_text(
            "\n".join(missing), encoding="utf-8"
        )

    return copied


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = (
        "image_id",
        "text_tr",
        "text_en",
        "source_label",
        "label",
        "confidence",
        "rule",
        "image_path",
        "image_found",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_counts(rows_by_split: dict[str, list[dict[str, str]]]) -> str:
    lines = ["split,label,count"]
    for split, rows in rows_by_split.items():
        counts = {label: 0 for label in LABELS}
        for row in rows:
            counts[row["label"]] += 1
        for label in LABELS:
            lines.append(f"{split},{label},{counts[label]}")
    return "\n".join(lines) + "\n"


def write_readme(counts_csv: str) -> None:
    readme = f"""# Emotion 4-Class Dataset

This dataset was derived from the local two-class KIDO-style emotion dataset.
The original dataset was not modified.

## Labels

- Happy
- Sadness
- Anger
- Anxiety

## Derivation

- Original `Happiness` rows are mapped to `Happy`.
- Original `Sadness` rows are kept as `Sadness` unless the English reflection
  contains rule keywords for `Anger` or `Anxiety`.

These labels are weak/pseudo labels for `Anger` and `Anxiety`; validate a sample
manually before reporting them as final ground truth.

## Files

- Images: `Images/Emotion_4Class/<split>/<label>/*.jpg`
- Train metadata: `Texts/Emotion_4Class/Emotion_4Class_Train.csv`
- Test metadata: `Texts/Emotion_4Class/Emotion_4Class_Test.csv`
- Counts: `Texts/Emotion_4Class/class_counts.csv`

## Class Counts

```csv
{counts_csv.strip()}
```
"""
    (OUT_TEXT_ROOT / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    reset_output_dirs()

    train_rows = copy_images("train", read_rows(TEXT_ROOT / "Emotion_Train.csv"))
    test_rows = copy_images("test", read_rows(TEXT_ROOT / "Emotion_Test.csv"))

    write_csv(OUT_TEXT_ROOT / "Emotion_4Class_Train.csv", train_rows)
    write_csv(OUT_TEXT_ROOT / "Emotion_4Class_Test.csv", test_rows)

    counts_csv = build_counts({"train": train_rows, "test": test_rows})
    (OUT_TEXT_ROOT / "class_counts.csv").write_text(counts_csv, encoding="utf-8")
    write_readme(counts_csv)

    print(counts_csv, end="")


if __name__ == "__main__":
    main()
