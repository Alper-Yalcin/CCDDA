"""
FastAPI inference server for ChildArt Analyzer (V2 — clinical fusion).

Run from project root:
    uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

Environment:
    CCDDA_CHECKPOINT  -> .pt yolu (default: artifacts/v1_backend/train/checkpoints/best.pt)
    CCDDA_DEVICE      -> cuda | cpu (default: cpu)
    GITHUB_TOKEN      -> GitHub Models token (yoksa rule-based aciklama)
"""

from __future__ import annotations

import io
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from PIL import Image

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


logger = logging.getLogger("ccdda.api")
logging.basicConfig(level=logging.INFO)


DEFAULT_CHECKPOINT = Path("artifacts/v1_backend/train/checkpoints/best.pt")


def _resolve_checkpoint(explicit: Optional[str | Path]) -> Optional[Path]:
    if explicit is not None:
        p = Path(explicit)
        return p if p.is_file() else None
    env = os.environ.get("CCDDA_CHECKPOINT")
    if env:
        p = Path(env)
        return p if p.is_file() else None
    return DEFAULT_CHECKPOINT if DEFAULT_CHECKPOINT.is_file() else None


def create_app(
    static_dir: Optional[str | Path] = None,
    checkpoint_path: Optional[str | Path] = None,
    device: Optional[str] = None,
    enable_llm: bool = True,
) -> FastAPI:
    static_path = Path(static_dir).resolve() if static_dir and Path(static_dir).exists() else None
    resolved_ckpt = _resolve_checkpoint(checkpoint_path)
    resolved_device = device or os.environ.get("CCDDA_DEVICE", "cpu")

    state: dict = {"pipeline": None, "load_error": None, "checkpoint": str(resolved_ckpt) if resolved_ckpt else None}

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if resolved_ckpt is None:
            state["load_error"] = (
                "Checkpoint bulunamadi. Egitim sonrasi best.pt yolunu CCDDA_CHECKPOINT ile belirt "
                "veya artifacts/v1_backend/train/checkpoints/best.pt'i hazirla."
            )
            logger.warning(state["load_error"])
        else:
            try:
                from src.inference.pipeline import InferencePipeline
                state["pipeline"] = InferencePipeline(resolved_ckpt, device=resolved_device, enable_llm=enable_llm)
                logger.info("Pipeline yuklendi: ckpt=%s device=%s llm_enabled=%s", resolved_ckpt, resolved_device, enable_llm)
            except Exception as exc:
                state["load_error"] = f"Pipeline yuklenirken hata: {exc}"
                logger.exception("Pipeline yukleme hatasi")
        yield

    app = FastAPI(title="ChildArt Inference API", version="2.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )

    @app.get("/health")
    @app.get("/api/health")
    async def health():
        return {
            "status": "ok" if state["pipeline"] is not None else "not_ready",
            "checkpoint": state["checkpoint"],
            "device": resolved_device,
            "llm_available": bool(state["pipeline"] and state["pipeline"].llm and state["pipeline"].llm.is_available),
            "load_error": state["load_error"],
        }

    @app.post("/predict")
    @app.post("/api/predict")
    async def predict(
        image: Optional[UploadFile] = File(default=None),
        file: Optional[UploadFile] = File(default=None),
        lang: str = Form(default="tr"),
    ):
        if state["pipeline"] is None:
            raise HTTPException(
                status_code=503,
                detail=state["load_error"] or "Inference pipeline yuklu degil.",
            )

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
            pil = Image.open(io.BytesIO(payload)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Uploaded file must be a valid image.") from exc

        normalized_lang = (lang or "tr").lower()
        if normalized_lang not in ("tr", "en"):
            normalized_lang = "tr"

        try:
            result = state["pipeline"].predict(pil, lang=normalized_lang)
        except Exception as exc:
            logger.exception("predict failure")
            raise HTTPException(status_code=500, detail=f"Inference hatasi: {exc}") from exc

        return JSONResponse(content=result)

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
