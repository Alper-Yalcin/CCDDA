"""
Consensus pseudo-label pipeline.

Teachers:
  A = out/combined_v3_run/checkpoints/best.pt
  B = out/highconf_pipeline/runs/b3_highconf_075/checkpoints/best.pt
  C = Ollama qwen2.5vl vision model

The expensive C stage is resume-safe. By default it runs only on candidates
where A and B already agree with confidence >= 0.75, then keeps samples where
C agrees too. This gives a cleaner 3/3 consensus set instead of chaining one
teacher's errors into the next.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import random
import re
import sys
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import torch
import torch.nn.functional as F
from PIL import Image, ImageFile
from torch.utils.data import DataLoader, Dataset

import run_highconf_pipeline as rhp

ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out" / "consensus_pipeline"
A_LABELS = ROOT / "out" / "highconf_pipeline" / "teacher_labels_all.csv"
B_CKPT = ROOT / "out" / "highconf_pipeline" / "runs" / "b3_highconf_075" / "checkpoints" / "best.pt"
OLLAMA_URL = "http://localhost:11434/api/generate"

CLASSES = rhp.CLASSES
LABEL_TO_ID = rhp.LABEL_TO_ID

PROMPT = """You are analyzing a child's drawing for emotion classification research.

Classify the drawing into EXACTLY ONE dominant emotion:
- happy: warm/bright colors, smiling faces, sun, flowers, open composition
- sad: cool/dark colors, tears, rain, isolated or drooping figures, cramped composition
- angry: sharp/jagged lines, heavy dark marks, aggressive shapes, chaotic layout
- fear: tiny or hidden figures, very dark colors, enclosed/cornered figures, broken lines, avoidance

Rules:
1. Choose only one of: happy, sad, angry, fear.
2. Do not choose happy unless there are clear positive visual indicators.
3. If the evidence is weak, still choose the strongest visual emotion.

Respond with ONLY valid JSON:
{"emotion": "<happy|sad|angry|fear>", "confidence": <0.0-1.0>, "reason": "<short reason>"}"""

LOWER_TO_LABEL = {
    "happy": ("Happy", 0),
    "sad": ("Sad", 1),
    "angry": ("Angry", 2),
    "fear": ("Fear", 3),
}


def set_seed(seed: int = rhp.SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True


def ensure_dirs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifests").mkdir(exist_ok=True)
    (OUT / "runs").mkdir(exist_ok=True)


class CandidateDataset(Dataset):
    def __init__(self, df: pd.DataFrame, transform) -> None:
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict:
        row = self.df.iloc[idx]
        try:
            img = Image.open(row["image_path"]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (300, 300), 128)
        return {
            "image": self.transform(img),
            "sample_id": str(row["sample_id"]),
            "image_path": str(row["image_path"]),
            "sha256": str(row["sha256"]),
            "source": str(row["source"]),
            "width": int(row["width"]),
            "height": int(row["height"]),
        }


def label_with_b(
    batch_size: int,
    num_workers: int,
    device: str,
    force: bool = False,
) -> Path:
    out_csv = OUT / "teacher_b_b3_075_labels_all.csv"
    if out_csv.exists() and not force:
        print(f"[teacher_b] exists: {out_csv}")
        return out_csv
    print("[teacher_b] loading A labels", flush=True)
    if not A_LABELS.exists():
        raise FileNotFoundError(f"A labels missing: {A_LABELS}")
    if not B_CKPT.exists():
        raise FileNotFoundError(f"B checkpoint missing: {B_CKPT}")

    a_df = pd.read_csv(A_LABELS)
    print(f"[teacher_b] A rows={len(a_df)}", flush=True)
    _, val_tf = rhp.b3_transforms()
    print("[teacher_b] building dataloader", flush=True)
    loader = DataLoader(
        CandidateDataset(a_df, val_tf),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=(device == "cuda"),
        persistent_workers=(num_workers > 0),
    )

    print(f"[teacher_b] loading B model: {B_CKPT}", flush=True)
    model = rhp.B3Classifier(num_classes=4, pretrained=False).to(device)
    ckpt = torch.load(B_CKPT, map_location=device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    print("[teacher_b] inference start", flush=True)

    rows: list[dict] = []
    seen = 0
    t0 = time.time()
    with torch.no_grad():
        for batch in loader:
            imgs = batch["image"].to(device, non_blocking=True)
            logits = model(imgs)
            probs = F.softmax(logits, dim=1).detach().cpu().numpy()
            pred_ids = probs.argmax(axis=1)
            confs = probs.max(axis=1)
            for i, pred_id in enumerate(pred_ids):
                rows.append({
                    "sample_id": batch["sample_id"][i],
                    "image_path": batch["image_path"][i],
                    "sha256": batch["sha256"][i],
                    "source": batch["source"][i],
                    "width": int(batch["width"][i]),
                    "height": int(batch["height"][i]),
                    "label": CLASSES[int(pred_id)],
                    "label_id": int(pred_id),
                    "confidence": float(confs[i]),
                    "prob_Happy": float(probs[i, 0]),
                    "prob_Sad": float(probs[i, 1]),
                    "prob_Angry": float(probs[i, 2]),
                    "prob_Fear": float(probs[i, 3]),
                    "teacher": "b3_highconf_075",
                })
            seen += len(pred_ids)
            if seen % (batch_size * 20) == 0 or seen == len(a_df):
                rate = seen / max(time.time() - t0, 1e-6)
                eta = (len(a_df) - seen) / max(rate, 1e-6) / 60
                print(f"  [teacher_b] {seen}/{len(a_df)} rate={rate:.1f}/s eta={eta:.1f}m", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    report = {
        "total_labeled": int(len(df)),
        "pred_dist": {k: int(v) for k, v in df["label"].value_counts().items()},
        "conf_mean": float(df["confidence"].mean()) if len(df) else 0.0,
    }
    (OUT / "teacher_b_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[teacher_b] saved {len(df)} -> {out_csv}")
    print(f"[teacher_b] report={report}")
    return out_csv


def build_ab_candidates(
    b_labels_csv: Path,
    min_conf: float,
    scope: str,
    force: bool = False,
) -> Path:
    tag = f"{scope}_{int(min_conf * 100):03d}"
    out_csv = OUT / f"ab_candidates_{tag}.csv"
    if out_csv.exists() and not force:
        print(f"[ab] exists: {out_csv}")
        return out_csv

    a = pd.read_csv(A_LABELS)
    b = pd.read_csv(b_labels_csv)
    keep_cols = ["sample_id", "image_path", "sha256", "source", "width", "height", "label", "label_id", "confidence"]
    m = a[keep_cols].merge(
        b[keep_cols],
        on=["sample_id", "image_path", "sha256", "source", "width", "height"],
        suffixes=("_a", "_b"),
    )
    high = (m["confidence_a"] >= min_conf) & (m["confidence_b"] >= min_conf)
    if scope == "ab_agree":
        selected = m[high & (m["label_id_a"] == m["label_id_b"])].copy()
    elif scope == "ab_highconf":
        selected = m[high].copy()
    else:
        selected = m.copy()

    selected.to_csv(out_csv, index=False)
    report = {
        "scope": scope,
        "min_conf": min_conf,
        "total_joined": int(len(m)),
        "selected": int(len(selected)),
        "a_dist": {k: int(v) for k, v in selected["label_a"].value_counts().items()} if len(selected) else {},
        "b_dist": {k: int(v) for k, v in selected["label_b"].value_counts().items()} if len(selected) else {},
        "ab_agree_count": int((m["label_id_a"] == m["label_id_b"]).sum()),
        "ab_highconf_agree_count": int((high & (m["label_id_a"] == m["label_id_b"])).sum()),
    }
    (OUT / f"ab_candidates_{tag}_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[ab] saved {len(selected)} -> {out_csv}")
    print(f"[ab] report={report}")
    return out_csv


def image_to_b64(path: str, max_size: int) -> str:
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def parse_ollama_response(text: str) -> dict | None:
    m = re.search(r"\{.*?\}", text, re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group())
        emotion = str(d.get("emotion", "")).lower().strip()
        if emotion not in LOWER_TO_LABEL:
            return None
        conf = float(d.get("confidence", 0.5))
        conf = max(0.0, min(1.0, conf))
        label, label_id = LOWER_TO_LABEL[emotion]
        return {
            "label": label,
            "label_id": label_id,
            "confidence": conf,
            "reason": str(d.get("reason", ""))[:300],
        }
    except Exception:
        return None


def query_ollama(path: str, model: str, max_size: int, timeout: int) -> dict | None:
    b64 = image_to_b64(path, max_size)
    payload = {
        "model": model,
        "prompt": PROMPT,
        "images": [b64],
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "temperature": 0.0,
            "top_p": 0.8,
            "num_predict": 80,
            "num_ctx": 512,
        },
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    if resp.status_code != 200:
        return None
    return parse_ollama_response(resp.json().get("response", ""))


def check_ollama_model(model: str) -> None:
    try:
        tags = requests.get("http://localhost:11434/api/tags", timeout=10).json()
    except Exception as exc:
        raise RuntimeError("Ollama service is not reachable at localhost:11434") from exc
    names = {m.get("name") for m in tags.get("models", [])}
    if model not in names:
        raise RuntimeError(f"Ollama model '{model}' not found. Available: {sorted(names)}")


def label_with_ollama(
    candidates_csv: Path,
    model: str,
    max_size: int,
    timeout: int,
    flush_every: int,
    force: bool = False,
    max_items: int | None = None,
) -> Path:
    tag = candidates_csv.stem.replace("ab_candidates_", "")
    out_csv = OUT / f"teacher_c_ollama_{model.replace(':', '_')}_{tag}.csv"
    if force and out_csv.exists():
        out_csv.unlink()

    candidates = pd.read_csv(candidates_csv)
    if max_items is not None:
        candidates = candidates.head(max_items).copy()

    done: set[str] = set()
    if out_csv.exists():
        prev = pd.read_csv(out_csv)
        done = set(prev["sha256"].astype(str))
        print(f"[ollama] resume: {len(done)} already done -> {out_csv}")
    else:
        out_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "sample_id", "image_path", "sha256", "source", "width", "height",
        "label_a", "label_id_a", "confidence_a",
        "label_b", "label_id_b", "confidence_b",
        "label", "label_id", "confidence", "reason", "ok", "teacher",
    ]
    if not out_csv.exists():
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()

    pending = candidates[~candidates["sha256"].astype(str).isin(done)].reset_index(drop=True)
    print(f"[ollama] model={model} pending={len(pending)} total={len(candidates)}")
    rows: list[dict] = []
    failed = 0
    t0 = time.time()

    for idx, r in pending.iterrows():
        result = None
        try:
            result = query_ollama(str(r["image_path"]), model=model, max_size=max_size, timeout=timeout)
        except Exception:
            result = None

        if result is None:
            failed += 1
            result = {"label": "", "label_id": "", "confidence": "", "reason": ""}

        rows.append({
            "sample_id": r["sample_id"],
            "image_path": r["image_path"],
            "sha256": r["sha256"],
            "source": r["source"],
            "width": int(r["width"]),
            "height": int(r["height"]),
            "label_a": r["label_a"],
            "label_id_a": int(r["label_id_a"]),
            "confidence_a": float(r["confidence_a"]),
            "label_b": r["label_b"],
            "label_id_b": int(r["label_id_b"]),
            "confidence_b": float(r["confidence_b"]),
            "label": result["label"],
            "label_id": result["label_id"],
            "confidence": result["confidence"],
            "reason": result["reason"],
            "ok": int(result["label"] != ""),
            "teacher": model,
        })

        done_now = idx + 1
        if len(rows) >= flush_every or done_now == len(pending):
            with out_csv.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerows(rows)
            rows = []

        if done_now % flush_every == 0 or done_now == len(pending):
            rate = done_now / max(time.time() - t0, 1e-6)
            eta_h = (len(pending) - done_now) / max(rate, 1e-6) / 3600
            print(
                f"  [ollama] {done_now}/{len(pending)} failed={failed} "
                f"rate={rate:.3f}/s eta={eta_h:.1f}h",
                flush=True,
            )

    final = pd.read_csv(out_csv)
    valid = final[final["ok"] == 1].copy()
    report = {
        "model": model,
        "total": int(len(final)),
        "valid": int(len(valid)),
        "failed": int((final["ok"] != 1).sum()),
        "pred_dist": {k: int(v) for k, v in valid["label"].value_counts().items()} if len(valid) else {},
    }
    (OUT / f"teacher_c_ollama_{model.replace(':', '_')}_{tag}_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[ollama] saved -> {out_csv}")
    print(f"[ollama] report={report}")
    return out_csv


def load_hf_qwen(model_id: str):
    from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2_5_VLForConditionalGeneration

    print(f"[hf_qwen] loading {model_id} in 4-bit on CUDA", flush=True)
    bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_id,
        quantization_config=bnb_cfg,
        device_map="auto",
        low_cpu_mem_usage=True,
    )
    model.eval()
    processor = AutoProcessor.from_pretrained(model_id)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"
    print(f"[hf_qwen] loaded. cuda_alloc={torch.cuda.memory_allocated() / 1024**3:.2f}GB", flush=True)
    return model, processor


def query_hf_qwen_batch(model, processor, paths: list[str], max_size: int) -> list[dict | None]:
    from qwen_vl_utils import process_vision_info

    try:
        texts = []
        image_inputs = []
        video_inputs = []
        for path in paths:
            img = Image.open(path).convert("RGB")
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {"type": "text", "text": PROMPT},
                ],
            }]
            texts.append(processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
            imgs, vids = process_vision_info(messages)
            image_inputs.extend(imgs or [])
            video_inputs.extend(vids or [])
        inputs = processor(
            text=texts,
            images=image_inputs,
            videos=video_inputs or None,
            padding=True,
            return_tensors="pt",
        ).to("cuda")
        with torch.no_grad():
            gen_ids = model.generate(
                **inputs,
                max_new_tokens=80,
                do_sample=False,
            )
        trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, gen_ids)]
        outputs = processor.batch_decode(
            trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        del inputs, gen_ids, trimmed
        return [parse_ollama_response(output) for output in outputs]
    except Exception as exc:
        print(f"  [hf_qwen batch err] {exc}", flush=True)
        return [None for _ in paths]


def label_with_hf_qwen(
    candidates_csv: Path,
    model_id: str,
    max_size: int,
    flush_every: int,
    batch_size: int,
    force: bool = False,
    max_items: int | None = None,
) -> Path:
    tag = candidates_csv.stem.replace("ab_candidates_", "")
    safe_model = model_id.replace("/", "_").replace(":", "_")
    out_csv = OUT / f"teacher_c_hf_{safe_model}_{tag}.csv"
    if force and out_csv.exists():
        out_csv.unlink()

    candidates = pd.read_csv(candidates_csv)
    if max_items is not None:
        candidates = candidates.head(max_items).copy()

    done: set[str] = set()
    if out_csv.exists():
        prev = pd.read_csv(out_csv)
        done = set(prev["sha256"].astype(str))
        print(f"[hf_qwen] resume: {len(done)} already done -> {out_csv}")
    else:
        out_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "sample_id", "image_path", "sha256", "source", "width", "height",
        "label_a", "label_id_a", "confidence_a",
        "label_b", "label_id_b", "confidence_b",
        "label", "label_id", "confidence", "reason", "ok", "teacher",
    ]
    if not out_csv.exists():
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()

    pending = candidates[~candidates["sha256"].astype(str).isin(done)].reset_index(drop=True)
    print(f"[hf_qwen] model={model_id} pending={len(pending)} total={len(candidates)}")
    model, processor = load_hf_qwen(model_id)
    rows: list[dict] = []
    failed = 0
    t0 = time.time()

    for start in range(0, len(pending), batch_size):
        batch_df = pending.iloc[start:start + batch_size]
        results = query_hf_qwen_batch(
            model,
            processor,
            batch_df["image_path"].astype(str).tolist(),
            max_size=max_size,
        )
        for (_, r), result in zip(batch_df.iterrows(), results):
            if result is None:
                failed += 1
                result = {"label": "", "label_id": "", "confidence": "", "reason": ""}
            rows.append({
                "sample_id": r["sample_id"],
                "image_path": r["image_path"],
                "sha256": r["sha256"],
                "source": r["source"],
                "width": int(r["width"]),
                "height": int(r["height"]),
                "label_a": r["label_a"],
                "label_id_a": int(r["label_id_a"]),
                "confidence_a": float(r["confidence_a"]),
                "label_b": r["label_b"],
                "label_id_b": int(r["label_id_b"]),
                "confidence_b": float(r["confidence_b"]),
                "label": result["label"],
                "label_id": result["label_id"],
                "confidence": result["confidence"],
                "reason": result["reason"],
                "ok": int(result["label"] != ""),
                "teacher": model_id,
            })

        done_now = min(start + len(batch_df), len(pending))
        if len(rows) >= flush_every or done_now == len(pending):
            with out_csv.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerows(rows)
            rows = []

        if done_now % flush_every == 0 or done_now == len(pending):
            rate = done_now / max(time.time() - t0, 1e-6)
            eta_h = (len(pending) - done_now) / max(rate, 1e-6) / 3600
            vram = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0.0
            print(
                f"  [hf_qwen] {done_now}/{len(pending)} failed={failed} "
                f"rate={rate:.3f}/s eta={eta_h:.1f}h vram={vram:.2f}GB",
                flush=True,
            )

    final = pd.read_csv(out_csv)
    valid = final[final["ok"] == 1].copy()
    report = {
        "model": model_id,
        "total": int(len(final)),
        "valid": int(len(valid)),
        "failed": int((final["ok"] != 1).sum()),
        "pred_dist": {k: int(v) for k, v in valid["label"].value_counts().items()} if len(valid) else {},
    }
    (OUT / f"teacher_c_hf_{safe_model}_{tag}_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[hf_qwen] saved -> {out_csv}")
    print(f"[hf_qwen] report={report}")
    return out_csv


def majority_label(row: pd.Series) -> tuple[str | None, int | None, int]:
    labels = [
        int(row["label_id_a"]),
        int(row["label_id_b"]),
        int(row["label_id"]),
    ]
    counts = {x: labels.count(x) for x in set(labels)}
    best_id, votes = max(counts.items(), key=lambda kv: kv[1])
    if votes < 2:
        return None, None, votes
    return CLASSES[best_id], best_id, votes


def build_consensus_manifest(
    ollama_csv: Path,
    min_c_conf: float,
    mode: str,
    max_per_class: int,
    force: bool = False,
) -> Path:
    tag = f"{mode}_c{int(min_c_conf * 100):03d}"
    out_csv = OUT / "manifests" / f"manifest_consensus_{tag}.csv"
    if out_csv.exists() and not force:
        print(f"[manifest] exists: {out_csv}")
        return out_csv

    c = pd.read_csv(ollama_csv)
    c = c[c["ok"] == 1].copy()
    c["label_id"] = c["label_id"].astype(int)
    c["confidence"] = c["confidence"].astype(float)
    c = c[c["confidence"] >= min_c_conf].copy()

    selected_rows = []
    for _, r in c.iterrows():
        if mode == "3of3":
            if int(r["label_id_a"]) != int(r["label_id_b"]) or int(r["label_id_a"]) != int(r["label_id"]):
                continue
            label_id = int(r["label_id"])
            votes = 3
        else:
            label, label_id, votes = majority_label(r)
            if label_id is None:
                continue
        selected_rows.append({
            "sample_id": r["sample_id"],
            "image_path": r["image_path"],
            "sha256": r["sha256"],
            "source": r["source"],
            "width": int(r["width"]),
            "height": int(r["height"]),
            "label": CLASSES[int(label_id)],
            "label_id": int(label_id),
            "votes": votes,
            "confidence_a": float(r["confidence_a"]),
            "confidence_b": float(r["confidence_b"]),
            "confidence_c": float(r["confidence"]),
            "sample_weight": max(0.35, min(float(r["confidence_a"]), float(r["confidence_b"]), float(r["confidence"]))),
        })

    pseudo = pd.DataFrame(selected_rows)
    if len(pseudo):
        parts = []
        for cls in CLASSES:
            cls_df = pseudo[pseudo["label"] == cls].copy()
            cls_df = cls_df.sort_values(
                ["votes", "sample_weight", "confidence_a", "confidence_b", "confidence_c"],
                ascending=False,
            )
            parts.append(cls_df.head(max_per_class))
        pseudo = pd.concat(parts, ignore_index=True)

    real_train, real_val, real_test = rhp.real_manifest_rows()
    rows = real_train + real_val + real_test
    for i, r in pseudo.iterrows():
        rows.append({
            "sample_id": f"consensus_{tag}_{i:08d}",
            "image_path": r["image_path"],
            "label": r["label"],
            "label_id": int(r["label_id"]),
            "split": "train",
            "source": f"consensus_{r['source']}",
            "confidence": float(r["sample_weight"]),
            "sample_weight": float(r["sample_weight"]),
            "sha256": r["sha256"],
            "width": int(r["width"]),
            "height": int(r["height"]),
            "votes": int(r["votes"]),
            "confidence_a": float(r["confidence_a"]),
            "confidence_b": float(r["confidence_b"]),
            "confidence_c": float(r["confidence_c"]),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    report = {
        "mode": mode,
        "min_c_conf": min_c_conf,
        "max_per_class": max_per_class,
        "total_rows": int(len(df)),
        "pseudo_selected": int(len(pseudo)),
        "pseudo_dist": {k: int(v) for k, v in pseudo["label"].value_counts().items()} if len(pseudo) else {},
        "split_dist": {
            split: {k: int(v) for k, v in part["label"].value_counts().items()}
            for split, part in df.groupby("split")
        },
    }
    report_path = OUT / "manifests" / f"manifest_consensus_{tag}_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[manifest] saved -> {out_csv}")
    print(f"[manifest] report={report}")
    return out_csv


def train_manifest(manifest: Path, tag: str, batch_size: int, num_workers: int, device: str, force: bool) -> Path:
    previous_out = rhp.OUT
    try:
        rhp.OUT = OUT
        return rhp.train_b3_manifest(
            manifest=manifest,
            tag=tag,
            batch_size=batch_size,
            num_workers=num_workers,
            device=device,
            force=force,
        )
    finally:
        rhp.OUT = previous_out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--batch-label", type=int, default=128)
    parser.add_argument("--batch-train", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=max(2, min(8, (os.cpu_count() or 6) - 2)))
    parser.add_argument("--ab-conf", type=float, default=0.75)
    parser.add_argument("--ab-scope", choices=["ab_agree", "ab_highconf", "all"], default="ab_agree")
    parser.add_argument("--c-backend", choices=["ollama", "hf"], default="ollama")
    parser.add_argument("--hf-model-id", default="Qwen/Qwen2.5-VL-3B-Instruct")
    parser.add_argument("--hf-batch-size", type=int, default=4)
    parser.add_argument("--ollama-model", default="qwen2.5vl:7b")
    parser.add_argument("--ollama-image-size", type=int, default=448)
    parser.add_argument("--ollama-timeout", type=int, default=180)
    parser.add_argument("--ollama-flush-every", type=int, default=25)
    parser.add_argument("--ollama-max-items", type=int, default=None)
    parser.add_argument("--min-c-conf", type=float, default=0.60)
    parser.add_argument("--consensus-mode", choices=["3of3", "2of3"], default="3of3")
    parser.add_argument("--max-per-class", type=int, default=6000)
    parser.add_argument("--force-b-label", action="store_true")
    parser.add_argument("--force-ab", action="store_true")
    parser.add_argument("--force-ollama", action="store_true")
    parser.add_argument("--force-manifest", action="store_true")
    parser.add_argument("--force-train", action="store_true")
    parser.add_argument("--skip-ollama", action="store_true")
    parser.add_argument("--skip-train", action="store_true")
    args = parser.parse_args()

    set_seed()
    ensure_dirs()
    print(f"[init] device={args.device} workers={args.num_workers}")
    print(f"[init] torch={torch.__version__} cuda={torch.cuda.is_available()}")
    if args.device == "cuda":
        print(f"[init] gpu={torch.cuda.get_device_name(0)}")

    b_csv = label_with_b(args.batch_label, args.num_workers, args.device, force=args.force_b_label)
    ab_csv = build_ab_candidates(b_csv, min_conf=args.ab_conf, scope=args.ab_scope, force=args.force_ab)
    if args.skip_ollama:
        print("[done] skipped C teacher/train")
        return 0

    if args.c_backend == "ollama":
        check_ollama_model(args.ollama_model)
        c_csv = label_with_ollama(
            ab_csv,
            model=args.ollama_model,
            max_size=args.ollama_image_size,
            timeout=args.ollama_timeout,
            flush_every=args.ollama_flush_every,
            force=args.force_ollama,
            max_items=args.ollama_max_items,
        )
    else:
        c_csv = label_with_hf_qwen(
            ab_csv,
            model_id=args.hf_model_id,
            max_size=args.ollama_image_size,
            flush_every=args.ollama_flush_every,
            batch_size=args.hf_batch_size,
            force=args.force_ollama,
            max_items=args.ollama_max_items,
        )
    manifest = build_consensus_manifest(
        c_csv,
        min_c_conf=args.min_c_conf,
        mode=args.consensus_mode,
        max_per_class=args.max_per_class,
        force=args.force_manifest,
    )

    run_dirs = []
    if not args.skip_train:
        tag = f"consensus_{args.consensus_mode}_ab{int(args.ab_conf * 100):03d}_c{int(args.min_c_conf * 100):03d}"
        run_dirs.append(train_manifest(manifest, tag, args.batch_train, args.num_workers, args.device, args.force_train))
        rhp.OUT = OUT
        rhp.write_summary(run_dirs)
    print(f"[done] outputs -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
