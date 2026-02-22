"""
FastAPI inference server for ChildArt Analyzer.
Run from project root:
    uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
"""

import io
import base64
import tempfile
import os
import re
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.explain.predict_and_explain import run_explanation

app = FastAPI(title="ChildArt Inference API", version="1.0.0")

# Allow the Vite dev-server (port 3000) and any origin when running locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

EMOTION_LABELS = {
    "en": {"Happiness": "Happiness", "Sadness": "Sadness"},
    "tr": {"Happiness": "Mutluluk", "Sadness": "Üzüntü"},
}

GENDER_LABELS = {
    "en": {"Female": "Female", "Male": "Male"},
    "tr": {"Female": "Kız", "Male": "Erkek"},
}


def _normalize_lang(lang: str) -> str:
    if isinstance(lang, str) and lang.lower().startswith("tr"):
        return "tr"
    return "en"


def _label(value: str, kind: str, lang: str) -> str:
    if kind == "emotion":
        return EMOTION_LABELS.get(lang, EMOTION_LABELS["en"]).get(value, value)
    return GENDER_LABELS.get(lang, GENDER_LABELS["en"]).get(value, value)


def _build_explanation(
    pred_emotion: str,
    pred_gender: str,
    confidence_emotion: float,
    confidence_gender: float,
    has_text: bool,
    lang: str,
) -> str:
    emotion_label = _label(pred_emotion, "emotion", lang)
    gender_label = _label(pred_gender, "gender", lang)

    if lang == "tr":
        lines = [
            f"Model, duygu tahminini '{emotion_label}' olarak %{confidence_emotion:.1f} güvenle yaptı.",
            f"Model, cinsiyet tahminini '{gender_label}' olarak %{confidence_gender:.1f} güvenle yaptı.",
            (
                "Görsel örüntü daha dengeli ve olumlu görünüyor."
                if pred_emotion == "Happiness"
                else "Görsel örüntü daha kısıtlı ve düşük enerjili görünüyor."
            ),
            (
                "Çizgi stili model tarafından daha güçlü ve keskin olarak yorumlandı."
                if pred_gender == "Male"
                else "Çizgi stili model tarafından daha yumuşak ve daha detaylı olarak yorumlandı."
            ),
            (
                "Metin girdisi çok modlu karara dahil edildi."
                if has_text
                else "Metin girdisi sağlanmadığı için karar ağırlıklı olarak görsele dayanıyor."
            ),
        ]
    else:
        lines = [
            f"Model predicts emotion '{pred_emotion}' with {confidence_emotion:.1f}% confidence.",
            f"Model predicts gender '{pred_gender}' with {confidence_gender:.1f}% confidence.",
            (
                "Visual pattern appears more balanced and positive."
                if pred_emotion == "Happiness"
                else "Visual pattern appears more restrained and low-energy."
            ),
            (
                "Stroke style is interpreted as stronger and sharper by the model."
                if pred_gender == "Male"
                else "Stroke style is interpreted as softer and more detailed by the model."
            ),
            (
                "Text input was included in the multimodal decision."
                if has_text
                else "No text input was provided, so the decision is image-heavy."
            ),
        ]

    return " ".join(lines)


def _strip_text_rationale(explanation: str) -> str:
    patterns = [
        r"Text input was included in the multimodal decision\.",
        r"No text input was provided, so the decision is image-heavy\.",
        r"Metin girdisi[^.]*\.",
    ]
    out = explanation or ""
    for pattern in patterns:
        out = re.sub(pattern, "", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def _ndarray_to_base64_jpeg(arr: np.ndarray) -> str:
    """Convert a BGR uint8 numpy array to a base64-encoded JPEG string."""
    success, buf = cv2.imencode(".jpg", arr)
    if not success:
        raise RuntimeError("cv2.imencode failed")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def _pil_image_to_ndarray_bgr(pil_img: Image.Image) -> np.ndarray:
    rgb = np.array(pil_img.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
@app.post("/api/predict")
async def predict(
    image: Optional[UploadFile] = File(default=None),
    file: Optional[UploadFile] = File(default=None),
    text: str = Form(default=""),
    lang: str = Form(default="en"),
):
    upload = image or file
    if upload is None:
        raise HTTPException(
            status_code=422,
            detail="Missing upload field. Send multipart field 'image' or 'file'.",
        )
    # ── 1. Validate file type ──────────────────────────────────────────
    if not upload.content_type or not upload.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    # ── 2. Save upload to a temp file (run_explanation needs a path) ───
    suffix = os.path.splitext(upload.filename or "upload.jpg")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await upload.read())
        tmp_path = tmp.name

    try:
        # ── 3. Run model inference + Grad-CAM ─────────────────────────
        result = run_explanation(
            image_path=tmp_path,
            text=text.strip() if text else "",
            device="cpu",  # change to "cuda" if GPU available
            checkpoint="checkpoints/best_multimodal.pt",
            bert_model="dbmdz/bert-base-turkish-cased",
            max_length=128,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        os.unlink(tmp_path)

    # ── 4. Encode heatmaps to base64 ──────────────────────────────────
    heatmap_emotion_b64 = (
        _ndarray_to_base64_jpeg(result["heatmap_emotion_color"])
        if result.get("heatmap_emotion_color") is not None
        else None
    )
    heatmap_gender_b64 = (
        _ndarray_to_base64_jpeg(result["heatmap_gender_color"])
        if result.get("heatmap_gender_color") is not None
        else None
    )

    # ── 5. Token attributions (text) ──────────────────────────────────
    def _token_list(tokens, scores):
        if tokens is None or scores is None:
            return []
        return [
            {"token": t, "score": float(s)}
            for t, s in zip(tokens, scores)
            if t not in ("[CLS]", "[SEP]", "[PAD]")
        ]

    # ── 6. Build response ─────────────────────────────────────────────
    probs_emotion = result["probs_emotion"].tolist()  # [p_happiness, p_sadness]
    probs_gender = result["probs_gender"].tolist()    # [p_female, p_male]
    confidence_emotion = round(float(max(probs_emotion)) * 100, 1)
    confidence_gender = round(float(max(probs_gender)) * 100, 1)
    lang_norm = _normalize_lang(lang)
    explanation = _build_explanation(
        pred_emotion=result["pred_emotion_str"],
        pred_gender=result["pred_gender_str"],
        confidence_emotion=confidence_emotion,
        confidence_gender=confidence_gender,
        has_text=bool(text and text.strip()),
        lang=lang_norm,
    )
    explanation = _strip_text_rationale(explanation)

    return JSONResponse(
        content={
            "pred_emotion": result["pred_emotion_str"],
            "pred_gender": result["pred_gender_str"],
            "confidence_emotion": confidence_emotion,
            "confidence_gender": confidence_gender,
            "explanation": explanation,
            "probs_emotion": probs_emotion,
            "probs_gender": probs_gender,
            "heatmap_emotion_b64": heatmap_emotion_b64,
            "heatmap_gender_b64": heatmap_gender_b64,
            "tokens_emotion": _token_list(result.get("tokens_emotion"), result.get("scores_emotion")),
            "tokens_gender": _token_list(result.get("tokens_gender"), result.get("scores_gender")),
        }
    )
