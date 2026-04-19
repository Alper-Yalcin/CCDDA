"""
FastAPI inference server for ChildArt Analyzer.
Run from project root:
    uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from PIL import Image

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

RESET_MESSAGE = (
    "Legacy multimodal AI stack was removed from this repository. "
    "The project is being rebuilt from scratch around the new labeled image-only dataset. "
    "Use the upcoming replacement pipeline instead of the retired emotion/gender/text system."
)


def reset_payload(component: str) -> dict[str, str]:
    return {
        "status": "reset_in_progress",
        "component": component,
        "detail": RESET_MESSAGE,
    }


def create_app(
    static_dir: Optional[str | Path] = None,
    preload_model: bool = False,
    device: str = "cpu",
) -> FastAPI:
    static_path = Path(static_dir).resolve() if static_dir and Path(static_dir).exists() else None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    app = FastAPI(title="ChildArt Inference API", version="1.0.0", lifespan=lifespan)
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
            "status": "reset_in_progress",
            "detail": RESET_MESSAGE,
        }

    @app.post("/predict")
    @app.post("/api/predict")
    async def predict(
        image: Optional[UploadFile] = File(default=None),
        file: Optional[UploadFile] = File(default=None),
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
            Image.open(io.BytesIO(payload)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Uploaded file must be a valid image.") from exc

        return JSONResponse(
            status_code=503,
            content=reset_payload("api.predict"),
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
