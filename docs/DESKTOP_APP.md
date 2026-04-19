# Desktop packaging

Desktop shell remains available, but the legacy AI inference stack was removed.

Current behavior:
- `desktop_app.py` still launches the embedded FastAPI server and React frontend.
- `api_server.py` returns `reset_in_progress` for health checks.
- `/predict` returns `503` until the new image-only model is implemented.

What is still valid:
- PyInstaller spec and installer assets
- WebView2-based desktop shell
- Frontend bundling from `Web/dist`

What is no longer valid:
- references to `best_multimodal.pt`
- packaged legacy checkpoint inference
- BERT/model export steps for the removed multimodal stack

When the new model is ready, this document should be rewritten around the new training artifacts and runtime requirements.