from __future__ import annotations

import csv
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TEXT_ROOT = ROOT / "Texts" / "Emotion"
IMAGE_ROOT = ROOT / "Images" / "Emotion"

OUT_TEXT_ROOT = ROOT / "Texts" / "Emotion_Derived_6Class"
OUT_IMAGE_ROOT = ROOT / "Images" / "Emotion_Derived_6Class"


@dataclass(frozen=True)
class Rule:
    label: str
    keywords: tuple[str, ...]
    confidence: float


SADNESS_RULES = (
    Rule(
        "Grief_Loss",
        (
            "die",
            "death",
            "dead",
            "died",
            "lost",
            "loss",
            "passed away",
            "funeral",
            "grave",
            "leave",
            "left us",
            "miss my",
            "separation",
        ),
        0.88,
    ),
    Rule(
        "Fear_Anxiety",
        (
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
        ),
        0.84,
    ),
    Rule(
        "Anger_Conflict",
        (
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
        ),
        0.84,
    ),
)


HAPPINESS_RULES = (
    Rule(
        "Affection_Belonging",
        (
            "love",
            "family",
            "mother",
            "father",
            "mom",
            "dad",
            "friend",
            "friends",
            "teacher",
            "sister",
            "brother",
            "grandmother",
            "grandfather",
            "birthday",
            "hug",
        ),
        0.80,
    ),
)


LABELS = (
    "Happiness_General",
    "Affection_Belonging",
    "Sadness_General",
    "Anger_Conflict",
    "Grief_Loss",
    "Fear_Anxiety",
)


def normalize_text(value: str) -> str:
    return (value or "").lower()


def matched_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    for keyword in keywords:
        pattern = rf"(?<![a-z]){re.escape(keyword)}(?![a-z])"
        if re.search(pattern, text):
            matches.append(keyword)
    return matches


def derive_label(source_label: str, text_tr: str, text_en: str) -> tuple[str, float, str]:
    # The local CSV is UTF-8, but some Turkish text is already mojibake in the
    # source. The English reflection column gives cleaner rule matches.
    text = normalize_text(text_en)
    source_label = source_label.strip()

    if source_label == "Sadness":
        for rule in SADNESS_RULES:
            matched = matched_keywords(text, rule.keywords)
            if matched:
                return rule.label, rule.confidence, "|".join(matched[:5])
        return "Sadness_General", 0.65, "source_sadness_default"

    if source_label == "Happiness":
        for rule in HAPPINESS_RULES:
            matched = matched_keywords(text, rule.keywords)
            if matched:
                return rule.label, rule.confidence, "|".join(matched[:5])
        return "Happiness_General", 0.65, "source_happiness_default"

    return "Unknown", 0.0, "unknown_source_label"


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 4:
                continue
            image_id, text_tr, text_en, source_label = row[:4]
            derived_label, confidence, rule = derive_label(source_label, text_tr, text_en)
            rows.append(
                {
                    "image_id": image_id,
                    "text_tr": text_tr,
                    "text_en": text_en,
                    "source_label": source_label,
                    "derived_label": derived_label,
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


def image_source_path(split: str, source_label: str, image_id: str) -> Path:
    return IMAGE_ROOT / split / source_label / f"{image_id}.jpg"


def copy_images(split: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    copied_rows: list[dict[str, str]] = []
    missing: list[str] = []

    for row in rows:
        source = image_source_path(split, row["source_label"], row["image_id"])
        target = OUT_IMAGE_ROOT / split / row["derived_label"] / f"{row['image_id']}.jpg"
        row = dict(row)
        row["image_path"] = str(target.relative_to(ROOT))

        if not source.exists():
            missing.append(str(source))
            row["image_found"] = "False"
        else:
            shutil.copy2(source, target)
            row["image_found"] = "True"
        copied_rows.append(row)

    if missing:
        missing_path = OUT_TEXT_ROOT / f"missing_images_{split}.txt"
        missing_path.write_text("\n".join(missing), encoding="utf-8")

    return copied_rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = (
        "image_id",
        "text_tr",
        "text_en",
        "source_label",
        "derived_label",
        "confidence",
        "rule",
        "image_path",
        "image_found",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows_by_split: dict[str, list[dict[str, str]]]) -> str:
    lines = ["split,label,count"]
    for split, rows in rows_by_split.items():
        counts = {label: 0 for label in LABELS}
        for row in rows:
            counts[row["derived_label"]] = counts.get(row["derived_label"], 0) + 1
        for label in LABELS:
            lines.append(f"{split},{label},{counts[label]}")
    return "\n".join(lines) + "\n"


def write_readme(summary_csv: str) -> None:
    readme = f"""# Emotion Derived 6-Class Dataset

This is a derived dataset created from the local KIDO-style two-class emotion data.
The original files are not modified.

The new labels are pseudo-labels derived from each child's written reflection, not
new manual annotations. Use them in a thesis as secondary or weak labels.

## Labels

- Happiness_General
- Affection_Belonging
- Sadness_General
- Anger_Conflict
- Grief_Loss
- Fear_Anxiety

## Files

- Images: `Images/Emotion_Derived_6Class/<split>/<label>/*.jpg`
- Text metadata: `Texts/Emotion_Derived_6Class/Emotion_Derived_Train.csv`
- Text metadata: `Texts/Emotion_Derived_6Class/Emotion_Derived_Test.csv`
- Counts: `Texts/Emotion_Derived_6Class/class_counts.csv`

## Class Counts

```csv
{summary_csv.strip()}
```

## Important Method Note

The original emotional ground truth remains Happiness/Sadness. These derived labels
are rule-based weak labels inferred from reflection text. They should be validated
manually on a sample before being presented as final emotion classes.
"""
    (OUT_TEXT_ROOT / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    reset_output_dirs()

    train_rows = read_rows(TEXT_ROOT / "Emotion_Train.csv")
    test_rows = read_rows(TEXT_ROOT / "Emotion_Test.csv")

    train_rows = copy_images("train", train_rows)
    test_rows = copy_images("test", test_rows)

    write_csv(OUT_TEXT_ROOT / "Emotion_Derived_Train.csv", train_rows)
    write_csv(OUT_TEXT_ROOT / "Emotion_Derived_Test.csv", test_rows)

    summary = summarize({"train": train_rows, "test": test_rows})
    (OUT_TEXT_ROOT / "class_counts.csv").write_text(summary, encoding="utf-8")
    write_readme(summary)

    print(summary, end="")


if __name__ == "__main__":
    main()
