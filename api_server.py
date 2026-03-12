"""
FastAPI inference server for ChildArt Analyzer.
Run from project root:
    uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import base64
import io
import re
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.explain.perception_api import PerceptionPipeline

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
    success, buf = cv2.imencode(".jpg", arr)
    if not success:
        raise RuntimeError("cv2.imencode failed")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def create_app(
    static_dir: Optional[str | Path] = None,
    preload_model: bool = False,
    device: str = "cpu",
) -> FastAPI:
    static_path = Path(static_dir).resolve() if static_dir and Path(static_dir).exists() else None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        app.state.pipeline = None

    app = FastAPI(title="ChildArt Inference API", version="1.0.0", lifespan=lifespan)
    app.state.pipeline = PerceptionPipeline(device=device) if preload_model else None
    app.state.pipeline_lock = Lock()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )

    def get_pipeline(request: Request) -> PerceptionPipeline:
        pipeline = getattr(request.app.state, "pipeline", None)
        if pipeline is None:
            with request.app.state.pipeline_lock:
                pipeline = getattr(request.app.state, "pipeline", None)
                if pipeline is None:
                    pipeline = PerceptionPipeline(device=device)
                    request.app.state.pipeline = pipeline
        return pipeline

    @app.get("/health")
    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.post("/predict")
    @app.post("/api/predict")
    async def predict(
        request: Request,
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
        if not upload.content_type or not upload.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

        payload = await upload.read()
        try:
            pil_img = Image.open(io.BytesIO(payload)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Uploaded file must be a valid image.") from exc

        try:
            result = get_pipeline(request).run(pil_img, text.strip() if text else "")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        heatmap_emotion_b64 = (
            _ndarray_to_base64_jpeg(result["heatmap_emotion"])
            if result.get("heatmap_emotion") is not None
            else None
        )
        heatmap_gender_b64 = (
            _ndarray_to_base64_jpeg(result["heatmap_gender"])
            if result.get("heatmap_gender") is not None
            else None
        )

        def _token_list(tokens, scores):
            if tokens is None or scores is None:
                return []
            return [
                {"token": token, "score": float(score)}
                for token, score in zip(tokens, scores)
                if token not in ("[CLS]", "[SEP]", "[PAD]")
            ]

        probs_emotion = result["probs_emotion"].tolist()
        probs_gender = result["probs_gender"].tolist()
        confidence_emotion = round(float(max(probs_emotion)) * 100, 1)
        confidence_gender = round(float(max(probs_gender)) * 100, 1)
        lang_norm = _normalize_lang(lang)
        explanation = _build_explanation(
            pred_emotion=result["pred_emotion"],
            pred_gender=result["pred_gender"],
            confidence_emotion=confidence_emotion,
            confidence_gender=confidence_gender,
            has_text=bool(text and text.strip()),
            lang=lang_norm,
        )
        explanation = _strip_text_rationale(explanation)

        return JSONResponse(
            content={
                "pred_emotion": result["pred_emotion"],
                "pred_gender": result["pred_gender"],
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

    if static_path is not None:
        assets_dir = static_path / "assets"
        index_file = static_path / "index.html"

        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        if index_file.is_file():
            @app.get("/")
            async def frontend_index():
                return FileResponse(index_file)

            @app.get("/{full_path:path}")
            async def frontend_routes(full_path: str):
                if full_path.startswith("api/") or full_path in {"api", "health", "predict"}:
                    raise HTTPException(status_code=404, detail="Not found.")

                candidate = static_path / full_path
                if candidate.is_file():
                    return FileResponse(candidate)
                return FileResponse(index_file)

    return app


app = create_app()
