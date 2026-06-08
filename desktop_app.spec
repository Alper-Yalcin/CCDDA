# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


project_root = Path(SPECPATH)
web_dist = project_root / "Web" / "dist"
# Web'de kullanilan logodan uretilen uygulama ikonu (scripts/make_app_icon.py)
app_icon = project_root / "installer" / "app_icon.ico"
app_icon_path = str(app_icon) if app_icon.exists() else None
# Nihai model: Kavram Darbogazi (Concept Bottleneck) + v2 gosterge istatistikleri
model_ckpt = project_root / "model" / "concept_bottleneck.pt"
model_stats = project_root / "model" / "feature_stats_v2.json"

datas = []
if web_dist.exists():
    datas.append((str(web_dist), "Web/dist"))
if model_ckpt.exists():
    datas.append((str(model_ckpt), "model"))
if model_stats.exists():
    datas.append((str(model_stats), "model"))

hiddenimports = collect_submodules("webview")
# clinical_v2 (gosterge cikarimi + CBM pipeline) ve src modulleri
hiddenimports += collect_submodules("clinical_v2")
hiddenimports += collect_submodules("src")
hiddenimports += [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "anyio._backends._asyncio",
    "src.inference.pipeline_v2",
    "src.models.concept_bottleneck_classifier",
    "clinical_v2.extractor_v2",
    "clinical_v2.feature_spec_v2",
    "cv2",
    "scipy.optimize",
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
    icon=app_icon_path,
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
