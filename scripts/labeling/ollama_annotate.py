"""
ollama_annotate.py

Qwen2.5-VL:7b ile dataset_qwen_selected goruntuleri uzerinde klinik
duygu analizi yapar.

Her goruntu icin modelden istenen cikti:
  - Her duyguda 0-10 puan (Happy / Sad / Angry / Fear)
  - 6 klinik gostergede 0-10 puan
  - Nihai duygu sinifi

Prompt ozellikleri:
  - Cocuk cizimi olarak degerlendirilmesini soyler
  - Klinik kriterleri (renk, cizgi, kompozisyon) acikca tanimlar
  - JSON formatinda cikti ister
  - Hicbir ek aciklama istemez

Cikti: out/ollama_annotations.csv
"""
from __future__ import annotations

import base64
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from PIL import Image
import io

# -- Config -------------------------------------------------------------------
MANIFEST      = Path("out/manifest_qwen.csv")
OUT_CSV       = Path("out/ollama_annotations.csv")
OLLAMA_URL    = "http://localhost:11434/api/generate"
MODEL         = "qwen2.5vl:3b"
TIMEOUT       = 90   # saniye/goruntu
BATCH_LOG     = 50   # her N goruntude ilerleme yazdir

PROMPT = """You are a child psychology drawing analysis expert. Analyze this child's drawing and score emotional indicators.

SCORING CRITERIA — score each item 0 to 10:

EMOTION SCORES (how strongly the drawing expresses each emotion):
- happy_score: Bright/warm colors (yellow, orange, red), large figures, wide composition, smiling faces, sun/flowers, open space → 10 = strongly happy
- sad_score: Cool/dark colors (blue, grey, black), small figures, cramped composition, drooping lines, rain/tears, isolated elements → 10 = strongly sad
- angry_score: Dark reds/blacks, jagged/sharp lines, heavy pressure (dark marks), aggressive shapes, chaotic layout, pointed elements → 10 = strongly angry
- fear_score: Very dark/black colors, tiny figures in corners, minimal coverage, broken/fragmented lines, enclosed/hiding figures → 10 = strongly fear

CLINICAL FEATURE SCORES (objective drawing characteristics):
- color_warmth: 0=only cold/dark colors, 10=only warm/bright colors (yellow/orange/red dominant)
- line_pressure: 0=very light faint lines, 10=very heavy dark bold lines
- figure_size: 0=tiny figure occupying <5% of space, 10=large figure filling >70% of canvas
- composition_openness: 0=completely cramped/corner-only, 10=spread across whole canvas freely
- color_darkness: 0=all bright/white, 10=mostly black/very dark
- line_chaos: 0=calm organized smooth lines, 10=chaotic fragmented jagged marks everywhere

CLASSIFICATION RULE:
- predicted_emotion: pick the ONE highest-scoring emotion (happy/sad/angry/fear)
- confidence: 0.0-1.0 how certain you are

IMPORTANT:
- This is a child's drawing, NOT a photo
- Focus on visual features only, not subject matter interpretation
- Be objective and consistent

Return ONLY valid JSON, no other text:
{
  "happy_score": <0-10>,
  "sad_score": <0-10>,
  "angry_score": <0-10>,
  "fear_score": <0-10>,
  "color_warmth": <0-10>,
  "line_pressure": <0-10>,
  "figure_size": <0-10>,
  "composition_openness": <0-10>,
  "color_darkness": <0-10>,
  "line_chaos": <0-10>,
  "predicted_emotion": "<happy|sad|angry|fear>",
  "confidence": <0.0-1.0>
}"""


# -- Helpers ------------------------------------------------------------------
def image_to_b64(path: str) -> str:
    img = Image.open(path).convert("RGB")
    img.thumbnail((512, 512), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def parse_json(text: str) -> dict | None:
    text = text.strip()
    # JSON block'u bul
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None


EXPECTED_KEYS = [
    "happy_score", "sad_score", "angry_score", "fear_score",
    "color_warmth", "line_pressure", "figure_size",
    "composition_openness", "color_darkness", "line_chaos",
    "predicted_emotion", "confidence",
]

LABEL_MAP = {"happy": 0, "sad": 1, "angry": 2, "fear": 3}


def query_ollama(image_path: str) -> dict | None:
    try:
        b64 = image_to_b64(image_path)
        payload = {
            "model": MODEL,
            "prompt": PROMPT,
            "images": [b64],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 300,
            }
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        if resp.status_code != 200:
            return None
        text = resp.json().get("response", "")
        result = parse_json(text)
        if result is None:
            return None
        # validate keys
        for k in EXPECTED_KEYS:
            if k not in result:
                return None
        return result
    except Exception:
        return None


def empty_row(sample_id: str, image_path: str, orig_label: str, orig_label_id: int) -> dict:
    row = {
        "sample_id": sample_id,
        "image_path": image_path,
        "orig_label": orig_label,
        "orig_label_id": orig_label_id,
        "ollama_emotion": None,
        "ollama_emotion_id": None,
        "ollama_confidence": None,
        "ollama_agree": None,
    }
    for k in EXPECTED_KEYS[:-2]:  # skip predicted_emotion, confidence
        row[f"ollama_{k}"] = None
    return row


# -- Main ---------------------------------------------------------------------
def main():
    df = pd.read_csv(MANIFEST)
    print(f"[init] {len(df)} goruntu  model={MODEL}")

    # Resume destegi: daha once islenenleri atla
    done_ids: set[str] = set()
    if OUT_CSV.exists():
        prev = pd.read_csv(OUT_CSV)
        done_ids = set(prev["sample_id"].astype(str).tolist())
        print(f"[resume] {len(done_ids)} goruntu zaten islendi")

    rows: list[dict] = []
    failed = 0
    t0 = time.time()

    for idx, record in df.iterrows():
        sid = str(record["sample_id"])
        if sid in done_ids:
            continue

        result = query_ollama(str(record["image_path"]))
        orig_label = str(record["label"])
        orig_label_id = int(record["label_id"])

        if result is None:
            failed += 1
            rows.append(empty_row(sid, str(record["image_path"]), orig_label, orig_label_id))
        else:
            pred_em = str(result.get("predicted_emotion", "")).lower().strip()
            pred_id = LABEL_MAP.get(pred_em, -1)
            agree = (pred_id == orig_label_id) if pred_id >= 0 else None
            row = {
                "sample_id":          sid,
                "image_path":         str(record["image_path"]),
                "orig_label":         orig_label,
                "orig_label_id":      orig_label_id,
                "ollama_emotion":     pred_em,
                "ollama_emotion_id":  pred_id,
                "ollama_confidence":  float(result.get("confidence", 0)),
                "ollama_agree":       int(agree) if agree is not None else None,
            }
            for k in EXPECTED_KEYS[:-2]:
                row[f"ollama_{k}"] = result.get(k)
            rows.append(row)

        # Her 50 goruntude kaydet (resume icin)
        done = idx + 1
        if done % BATCH_LOG == 0 or done == len(df):
            elapsed = time.time() - t0
            rate = done / elapsed
            eta = (len(df) - done) / rate if rate > 0 else 0
            print(f"  [{done}/{len(df)}] failed={failed}  "
                  f"rate={rate:.1f}/s  ETA={eta/60:.1f}min")

            # Mevcut ile birlestir
            new_df = pd.DataFrame(rows)
            if OUT_CSV.exists():
                existing = pd.read_csv(OUT_CSV)
                combined = pd.concat([existing, new_df], ignore_index=True)
            else:
                combined = new_df
            combined.to_csv(OUT_CSV, index=False)
            rows = []

    print(f"\n[done] Kaydedildi: {OUT_CSV}")
    final = pd.read_csv(OUT_CSV)
    print(f"Toplam: {len(final)}  Basarisiz: {failed}")

    # Istatistikler
    valid = final[final["ollama_emotion"].notna()]
    if len(valid) > 0:
        agree_rate = valid["ollama_agree"].mean()
        print(f"Ollama-Qwen etiket anlasma orani: {agree_rate:.3f} ({agree_rate*100:.1f}%)")
        print("Ollama sinif dagilimi:", dict(valid["ollama_emotion"].value_counts()))
        print("Orjinal sinif dagilimi:", dict(valid["orig_label"].value_counts()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
