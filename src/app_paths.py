from __future__ import annotations

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


def resolve_frontend_dist() -> Optional[Path]:
    return _existing_path(
        bundle_root() / "Web" / "dist",
        executable_dir() / "Web" / "dist",
        PROJECT_ROOT / "Web" / "dist",
    )