from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return PROJECT_ROOT


def executable_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


def _existing_path(*candidates: Path) -> Optional[Path]:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _huggingface_snapshot(repo_id: str) -> Optional[Path]:
    cache_root = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{repo_id.replace('/', '--')}"
    refs_main = cache_root / "refs" / "main"
    if refs_main.is_file():
        revision = refs_main.read_text(encoding="utf-8").strip()
        snapshot_dir = cache_root / "snapshots" / revision
        if snapshot_dir.is_dir():
            return snapshot_dir

    snapshots_dir = cache_root / "snapshots"
    if not snapshots_dir.is_dir():
        return None

    snapshots = sorted(path for path in snapshots_dir.iterdir() if path.is_dir())
    return snapshots[-1] if snapshots else None


def resolve_checkpoint_path(filename: str = "best_multimodal.pt") -> Path:
    env_path = os.getenv("CCDDA_CHECKPOINT")
    if env_path:
        return Path(env_path)

    return _existing_path(
        bundle_root() / "checkpoints" / filename,
        executable_dir() / "checkpoints" / filename,
        PROJECT_ROOT / "checkpoints" / filename,
    ) or (PROJECT_ROOT / "checkpoints" / filename)


def resolve_bert_model_path(default_repo_id: str = "dbmdz/bert-base-turkish-cased") -> str:
    env_path = os.getenv("CCDDA_BERT_MODEL")
    if env_path:
        return env_path

    local_dir = _existing_path(
        bundle_root() / "models" / "bert-base-turkish-cased",
        executable_dir() / "models" / "bert-base-turkish-cased",
        PROJECT_ROOT / "models" / "bert-base-turkish-cased",
    )
    if local_dir is not None:
        return str(local_dir)

    cached_snapshot = _huggingface_snapshot(default_repo_id)
    if cached_snapshot is not None:
        return str(cached_snapshot)

    return default_repo_id


def resolve_frontend_dist() -> Optional[Path]:
    return _existing_path(
        bundle_root() / "Web" / "dist",
        executable_dir() / "Web" / "dist",
        PROJECT_ROOT / "Web" / "dist",
    )
