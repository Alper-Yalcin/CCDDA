"""
label_with_hf.py — Dataset/Images/Emotion goruntuleri HuggingFace + GPU ile etiketle

Qwen2.5-VL-7B-Instruct (bitsandbytes 4-bit NF4) ile GPU'da calisir.
label_with_ollama.py ile ayni CSV formati, resume destegi var.

Cikti: out/labels_ollama.csv  (ollama scriptiyle ayni dosya, devam eder)
"""
from __future__ import annotations
import json, re, sys, time
from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from transformers import (AutoProcessor, BitsAndBytesConfig,
                           Qwen2_5_VLForConditionalGeneration)
from qwen_vl_utils import process_vision_info

MODEL_ID    = "Qwen/Qwen2.5-VL-7B-Instruct"
IMAGE_ROOT  = Path("Dataset/Images/Emotion")
OUT_CSV     = Path("out/labels_ollama.csv")
OUT_REPORT  = Path("out/labels_ollama_report.json")
LOG_EVERY   = 100
IMG_EXTS    = {".jpg", ".jpeg", ".png", ".webp"}
CLASSES     = ["Happy", "Sad", "Angry", "Fear"]
ORIG_LABEL_MAP = {"Happiness": "Happy", "Sadness": "Sad"}
LABEL_MAP   = {"happy": ("Happy", 0), "sad": ("Sad", 1),
               "angry": ("Angry", 2), "fear": ("Fear", 3)}

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


def load_model():
    print(f"[model] Loading {MODEL_ID} (4-bit NF4)...")
    bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_cfg,
        device_map="auto",
        low_cpu_mem_usage=True,
    )
    model.eval()
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    print(f"[model] Loaded. GPU mem: {torch.cuda.memory_allocated()/1024**3:.1f} GB")
    return model, processor


def parse_response(text: str) -> dict | None:
    m = re.search(r'\{.*?\}', text, re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group())
        em = str(d.get("emotion", "")).lower().strip()
        if em not in ("happy", "sad", "angry", "fear"):
            return None
        return {"emotion": em,
                "confidence": float(d.get("confidence", 0.5)),
                "reason": str(d.get("reason", ""))}
    except Exception:
        return None


def query_model(model, processor, path: str) -> dict | None:
    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((512, 512), Image.LANCZOS)

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": PROMPT},
            ],
        }]
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text], images=image_inputs, videos=video_inputs,
            padding=True, return_tensors="pt",
        ).to("cuda")

        with torch.no_grad():
            gen_ids = model.generate(
                **inputs,
                max_new_tokens=150,
                do_sample=True,
                temperature=0.05,
                top_p=0.9,
            )
        trimmed = [o[len(i):] for i, o in zip(inputs.input_ids, gen_ids)]
        output = processor.batch_decode(
            trimmed, skip_special_tokens=True,
            clean_up_tokenization_spaces=False)[0]
        return parse_response(output)
    except Exception as e:
        print(f"  [err] {Path(path).name}: {e}", flush=True)
        return None


def main():
    model, processor = load_model()

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

    print(f"[init] {len(all_paths)} goruntu toplandi")

    # Resume
    done_paths: set[str] = set()
    if OUT_CSV.exists():
        prev = pd.read_csv(OUT_CSV)
        done_paths = set(prev["image_path"].astype(str).tolist())
        print(f"[resume] {len(done_paths)} goruntu zaten islendi, devam ediliyor...")

    rows: list[dict] = []
    failed = 0
    t0 = time.time()
    new_count = 0

    for idx, (path, orig_lbl, split) in enumerate(
            zip(all_paths, orig_labels, splits)):
        if path in done_paths:
            continue

        result = query_model(model, processor, path)
        sample_id = f"ollama_{split}_{orig_lbl[:3].lower()}_{idx:06d}"
        new_count += 1

        if result is None:
            failed += 1
            rows.append({
                "sample_id": sample_id, "image_path": path,
                "orig_label": orig_lbl,
                "orig_label_2": ORIG_LABEL_MAP.get(orig_lbl, orig_lbl),
                "split": split, "label": None, "label_id": None,
                "confidence": None, "reason": None, "source": "ollama_7b",
            })
        else:
            em = result["emotion"]
            lbl, lid = LABEL_MAP[em]
            rows.append({
                "sample_id": sample_id, "image_path": path,
                "orig_label": orig_lbl,
                "orig_label_2": ORIG_LABEL_MAP.get(orig_lbl, orig_lbl),
                "split": split, "label": lbl, "label_id": lid,
                "confidence": result["confidence"],
                "reason": result["reason"], "source": "ollama_7b",
            })

        total_done = idx + 1
        if new_count % LOG_EVERY == 0 or total_done == len(all_paths):
            elapsed = time.time() - t0
            rate = new_count / elapsed if elapsed > 0 else 0
            remaining = len(all_paths) - total_done
            eta_h = (remaining / rate / 3600) if rate > 0 else 0
            vram = torch.cuda.memory_allocated() / 1024**3
            print(f"  [{total_done}/{len(all_paths)}] new={new_count}  "
                  f"failed={failed}  rate={rate:.2f}/s  "
                  f"ETA={eta_h:.1f}h  VRAM={vram:.1f}GB", flush=True)
            # Kaydet
            new_df = pd.DataFrame(rows)
            if OUT_CSV.exists():
                combined = pd.concat(
                    [pd.read_csv(OUT_CSV), new_df], ignore_index=True)
            else:
                combined = new_df
            OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
            combined.to_csv(OUT_CSV, index=False)
            rows = []

    # Son kalan satırları kaydet
    if rows:
        new_df = pd.DataFrame(rows)
        if OUT_CSV.exists():
            combined = pd.concat(
                [pd.read_csv(OUT_CSV), new_df], ignore_index=True)
        else:
            combined = new_df
        combined.to_csv(OUT_CSV, index=False)

    print(f"\n[done] {OUT_CSV}")
    final = pd.read_csv(OUT_CSV)
    valid = final[final["label"].notna()]
    report = {
        "total": len(final),
        "valid": len(valid),
        "failed": int(final["label"].isna().sum()),
        "pred_dist": {k: int(v) for k, v in valid["label"].value_counts().items()}
                     if len(valid) > 0 else {},
        "orig_dist": {k: int(v) for k, v in final["orig_label"].value_counts().items()},
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Toplam: {report['total']}  Gecerli: {report['valid']}  "
          f"Basarisiz: {report['failed']}")
    if report["pred_dist"]:
        print(f"Tahmin dagilimi: {report['pred_dist']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
