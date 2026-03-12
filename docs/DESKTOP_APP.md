# Desktop packaging

This project can now be packaged as a Windows desktop app that embeds:

- the React frontend from `Web/dist`
- the FastAPI inference backend
- a `pywebview` desktop shell
- the trained checkpoint in `checkpoints/best_multimodal.pt`

## What changed

- `desktop_app.py` starts a local FastAPI server on a random localhost port and opens it inside a desktop window.
- `api_server.py` now supports an app factory and can serve the built frontend in the same process.
- `src/explain/perception_api.py` keeps the model in memory instead of rebuilding it on every request.
- `src/models/multimodal_effnet_bert.py` can skip ImageNet weight downloads for offline packaged inference.
- `desktop_app.spec` defines the PyInstaller bundle.
- `installer/ChildArtAnalyzer.iss` defines the Windows installer.
- `tools/build_desktop.ps1` builds the frontend, exports cached BERT assets, runs PyInstaller, and optionally runs Inno Setup.

## Prerequisites

1. Use a real CPython install from python.org, not the Windows Store alias.
2. Create a fresh virtual environment if your `.venv\pyvenv.cfg` points to `WindowsApps`.
3. Install desktop dependencies:

```powershell
pip install -r requirements-desktop.txt
```

4. Make sure `Web/node_modules` exists:

```powershell
cd Web
npm install
cd ..
```

5. Make sure the checkpoint exists:

```text
checkpoints/best_multimodal.pt
```

6. Make sure the BERT model is available locally at least once.

The build script first looks for `models/bert-base-turkish-cased`. If it does not exist, it copies the model from the local HuggingFace cache:

```text
%USERPROFILE%\.cache\huggingface\hub\models--dbmdz--bert-base-turkish-cased
```

## Build the desktop bundle

```powershell
.\tools\build_desktop.ps1
```

If the default `.venv` points to the Windows Store alias, the script now falls back to a real interpreter from the Python launcher when possible.

Optional flags:

```powershell
.\tools\build_desktop.ps1 -SkipInstaller
.\tools\build_desktop.ps1 -PythonExe "C:\Python311\python.exe"
.\tools\build_desktop.ps1 -IsccExe "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

Outputs:

- PyInstaller app bundle: `dist\ChildArtAnalyzer`
- Installer: `artifacts\installer\ChildArtAnalyzer-Setup.exe`

## Notes

- The packaged app runs the model on CPU by default.
- The installer now blocks installation when the Edge WebView2 runtime is missing.
- The desktop shell explicitly uses Edge WebView2. If startup fails, the app writes a traceback to `ChildArtAnalyzer-error.log` next to the executable and shows the path in a dialog.
- If the installer step is skipped or Inno Setup is missing, the app bundle in `dist\ChildArtAnalyzer` is still runnable.
