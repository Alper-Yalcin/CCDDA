# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPECPATH)
web_dist = project_root / "Web" / "dist"
checkpoint_file = project_root / "checkpoints" / "best_multimodal.pt"
bert_assets = project_root / "models" / "bert-base-turkish-cased"

datas = []
if web_dist.exists():
    datas.append((str(web_dist), "Web/dist"))
if checkpoint_file.exists():
    datas.append((str(checkpoint_file), "checkpoints"))
if bert_assets.exists():
    datas.append((str(bert_assets), "models/bert-base-turkish-cased"))

hiddenimports = collect_submodules("webview")
hiddenimports += [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "anyio._backends._asyncio",
]


a = Analysis(
    ["desktop_app.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ChildArtAnalyzer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ChildArtAnalyzer",
)
