# Desktop Packaging

The desktop application (**Child Art Analyzer**) bundles the FastAPI inference
backend and the React frontend into a single Windows executable using
PyInstaller + WebView2.

## How it works

`desktop_app.py` starts the embedded FastAPI server (`api_server.py`), serves the
pre-built frontend from `Web/dist`, and opens a native WebView2 window pointed at
the local server. The same Concept Bottleneck Model used by the web app powers
inference inside the desktop build.

## Building

1. Build the frontend bundle:

   ```powershell
   cd Web
   npm install
   npm run build   # outputs Web/dist
   ```

2. Build the executable from the project root:

   ```powershell
   pyinstaller desktop_app.spec
   ```

   The build reads `desktop_app.spec`, which bundles:
   - the trained checkpoint and feature statistics (`model/`),
   - the frontend bundle (`Web/dist`),
   - the inference source tree (`src/`, `clinical_v2/`).

3. (Optional) Build the Windows installer with Inno Setup:

   ```powershell
   # Requires Inno Setup (ISCC.exe) on PATH
   scripts/build_installer.ps1
   ```

   The installer script (`installer/ChildArtAnalyzer.iss`) packages the PyInstaller
   output into a single setup executable.

## Runtime requirements

- **Model checkpoint** — bundled at build time from `model/concept_bottleneck.pt`
  (resolved via `src/app_paths.py`). If the bundled checkpoint is missing, set
  `CCDDA_CHECKPOINT` to a valid `.pt` path.
- **WebView2 Runtime** — required on the target machine (ships with modern
  Windows 10/11; the installer can prompt for it otherwise).
- **LLM explanations (optional)** — set `GITHUB_TOKEN` to enable LLM-generated
  clinical narratives; without it, the app falls back to the rule-based explainer.

See the top-level [README](../README.md) for the model architecture and results.
