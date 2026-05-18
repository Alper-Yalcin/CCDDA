"""
label_with_ollama.py — Dataset/Images/Emotion goruntuleri Ollama 7b ile etiketle

qwen2.5vl:7b ile Dataset/Images/Emotion altindaki tum goruntulere
4 duygu etiketi (Happy/Sad/Angry/Fear) verir.

Resume destegi: daha once islenenler atlanir.
Cikti: out/labels_ollama.csv
"""
from __future__ import annotations
import base64, json, re, sys, time
from pathlib import Path
import io

import pandas as pd
import requests
from PIL import Image

IMAGE_ROOT  = Path("Dataset/Images/Emotion")
OUT_CSV     = Path("out/labels_ollama.csv")
OUT_REPORT  = Path("out/labels_ollama_report.json")
OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL       = "qwen2.5vl:7b"
TIMEOUT     = 120
LOG_EVERY   = 100
IMG_EXTS    = {".jpg", ".jpeg", ".png", ".webp"}
CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
ORIG_LABEL_MAP = {"Happiness": "Happy", "Sadness": "Sad"}

PROMPT = """You are analyzing a child's drawing for emotion classification research.

Look carefully at this drawing and classify it into EXACTLY ONE of these four emotions:
- happy: bright/warm colors (yellow, orange, red), smiling faces, sun, flowers, large figures, wide composition
- sad: cool/dark colors (blue, grey), small drooping figures, rain, tears, isolated elements, cramped composition
- angry: dark reds/black, sharp/jagged lines, aggressive shapes, heavy dark marks, chaotic layout
- fear: very dark colors, tiny hidden figures, minimal coverage, broken lines, figures in corners, enclosed/hiding

CRITICAL RULES:
1. Choose ONLY the single most dominant emotion
2. If unsure between two emotions, pick the one with stronger visual evidence
3. "happy" is NOT the default — only choose it if there are clear positive visual indicators
4. dark colors + small figure = sad OR fear (not happy)
5. jagged lines + dark = angry (not sad)

Respond with ONLY valid JSON, nothing else:
{"emotion": "<happy|sad|angry|fear>", "confidence": <0.0-1.0>, "reason": "<one sentence>"}"""


def img_to_b64(path: str) -> str:
    img = Image.open(path).convert("RGB")
    img.thumbnail((512, 512), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def parse_response(text: str) -> dict | None:
    m = re.search(r'\{.*?\}', text, re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group())
        em = str(d.get("emotion", "")).lower().strip()
        if em not in ("happy", "sad", "angry", "fear"):
            return None
        return {"emotion": em, "confidence": float(d.get("confidence", 0.5)),
                "reason": str(d.get("reason", ""))}
    except Exception:
        return None


LABEL_MAP = {"happy": ("Happy", 0), "sad": ("Sad", 1), "angry": ("Angry", 2), "fear": ("Fear", 3)}


def query_ollama(path: str) -> dict | None:
    try:
        b64 = img_to_b64(path)
        payload = {
            "model": MODEL, "prompt": PROMPT,
            "images": [b64], "stream": False,
            "options": {"temperature": 0.05, "top_p": 0.9, "num_predict": 150},
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        if resp.status_code != 200:
            return None
        return parse_response(resp.json().get("response", ""))
    except Exception:
        return None


def main():
    # Tum goruntuleri topla
    all_paths, orig_labels, splits = [], [], []
    for split in ["train", "test"]:
        split_dir = IMAGE_ROOT / split
        if not split_dir.exists():
            continue
        for cls_dir in sorted(split_dir.iterdir()):
            if not cls_dir.is_dir():
                continue
            for f in sorted(cls_dir.iterdir()):
                if f.suffix.lower() in IMG_EXTS:
                    all_paths.append(str(f.resolve()))
                    orig_labels.append(cls_dir.name)
                    splits.append(split)

    print(f"[init] {len(all_paths)} goruntu  model={MODEL}")

    # Resume: daha once islenenler
    done_paths: set[str] = set()
    if OUT_CSV.exists():
        prev = pd.read_csv(OUT_CSV)
        done_paths = set(prev["image_path"].astype(str).tolist())
        print(f"[resume] {len(done_paths)} goruntu zaten islendi")

    rows = []
    failed = 0
    t0 = time.time()

    for idx, (path, orig_lbl, split) in enumerate(zip(all_paths, orig_labels, splits)):
        if path in done_paths:
            continue

        result = query_ollama(path)
        sample_id = f"ollama_{split}_{orig_lbl[:3].lower()}_{idx:06d}"

        if result is None:
            failed += 1
            rows.append({
                "sample_id": sample_id, "image_path": path,
                "orig_label": orig_lbl, "orig_label_2": ORIG_LABEL_MAP.get(orig_lbl, orig_lbl),
                "split": split, "label": None, "label_id": None,
                "confidence": None, "reason": None, "source": "ollama_7b",
            })
        else:
            em = result["emotion"]
            lbl, lid = LABEL_MAP[em]
            rows.append({
                "sample_id": sample_id, "image_path": path,
                "orig_label": orig_lbl, "orig_label_2": ORIG_LABEL_MAP.get(orig_lbl, orig_lbl),
                "split": split, "label": lbl, "label_id": lid,
                "confidence": result["confidence"], "reason": result["reason"],
                "source": "ollama_7b",
            })

        done = idx + 1
        if done % LOG_EVERY == 0 or done == len(all_paths):
            elapsed = time.time() - t0
            rate = len(rows) / elapsed if elapsed > 0 else 0
            remaining = len(all_paths) - done
            eta_h = (remaining / rate / 3600) if rate > 0 else 0
            print(f"  [{done}/{len(all_paths)}] failed={failed}  "
                  f"rate={rate:.2f}/s  ETA={eta_h:.1f}h")
            # Kaydet
            new_df = pd.DataFrame(rows)
            if OUT_CSV.exists():
                combined = pd.concat([pd.read_csv(OUT_CSV), new_df], ignore_index=True)
            else:
                combined = new_df
            OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
            combined.to_csv(OUT_CSV, index=False)
            rows = []

    print(f"\n[done] {OUT_CSV}")
    final = pd.read_csv(OUT_CSV)
    valid = final[final["label"].notna()]
    report = {
        "total": len(final), "valid": len(valid), "failed": int(final["label"].isna().sum()),
        "pred_dist": {k: int(v) for k, v in valid["label"].value_counts().items()} if len(valid) > 0 else {},
        "orig_dist": {k: int(v) for k, v in final["orig_label"].value_counts().items()},
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Toplam: {report['total']}  Gecerli: {report['valid']}  Basarisiz: {report['failed']}")
    if report["pred_dist"]:
        print(f"Tahmin dagilimi: {report['pred_dist']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
