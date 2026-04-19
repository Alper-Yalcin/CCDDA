from __future__ import annotations

import ctypes
import os
import socket
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path

import uvicorn

from api_server import create_app
from src.app_paths import executable_dir, resolve_frontend_dist


APP_TITLE = "ChildArt Analyzer"
WEBVIEW2_CLIENT_ID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WEBVIEW2_DOWNLOAD_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"


def _ensure_standard_streams() -> None:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8", buffering=1)
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8", buffering=1)
    if sys.stdin is None:
        sys.stdin = open(os.devnull, "r", encoding="utf-8")


def _error_log_path() -> Path:
    return executable_dir() / "ChildArtAnalyzer-error.log"


def _append_error_log(title: str, details: str) -> Path:
    log_path = _error_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {title}\n{details.rstrip()}\n\n")
    return log_path


def _show_error_dialog(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(None, message, APP_TITLE, 0x10)
    except Exception:
        pass


def _read_webview2_version() -> str | None:
    try:
        import winreg
    except ImportError:
        return None

    subkey = rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_CLIENT_ID}"
    hives = ("HKEY_CURRENT_USER", "HKEY_LOCAL_MACHINE")
    views = (
        getattr(winreg, "KEY_WOW64_32KEY", 0),
        getattr(winreg, "KEY_WOW64_64KEY", 0),
    )

    for hive_name in hives:
        hive = getattr(winreg, hive_name)
        for view in views:
            try:
                with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ | view) as key:
                    version, _ = winreg.QueryValueEx(key, "pv")
            except OSError:
                continue
            if version and version != "0.0.0.0":
                return str(version)
    return None


def _ensure_webview2_runtime() -> None:
    if _read_webview2_version():
        return
    raise RuntimeError(
        "Microsoft Edge WebView2 Runtime is not installed. "
        f"Install it and reopen the app: {WEBVIEW2_DOWNLOAD_URL}"
    )


def _run_server(server: uvicorn.Server, state: dict[str, object]) -> None:
    try:
        server.run()
    except BaseException as exc:
        state["exception"] = exc
        state["traceback"] = traceback.format_exc()


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(
    url: str,
    server_thread: threading.Thread,
    state: dict[str, object],
    timeout: float = 45.0,
) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if state.get("exception") is not None:
            raise RuntimeError("Embedded API server failed to start.") from state["exception"]
        if not server_thread.is_alive():
            break
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.25)

    if state.get("exception") is not None:
        raise RuntimeError("Embedded API server failed to start.") from state["exception"]
    raise RuntimeError(f"Server did not become ready within {timeout:.0f} seconds: {url}")


def main() -> None:
    _ensure_standard_streams()

    static_dir = resolve_frontend_dist()
    if static_dir is None:
        raise SystemExit("Web/dist not found. Run `npm run build` inside `Web/` before starting the desktop app.")

    _ensure_webview2_runtime()

    port = _find_free_port()
    app = create_app(static_dir=static_dir, preload_model=False, device="cpu")
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
    )
    server_state: dict[str, object] = {}

    server_thread = threading.Thread(
        target=_run_server,
        args=(server, server_state),
        name="fastapi-server",
        daemon=True,
    )
    server_thread.start()
    _wait_for_server(f"http://127.0.0.1:{port}/health", server_thread, server_state)

    try:
        import webview
    except ImportError as exc:
        server.should_exit = True
        server_thread.join(timeout=5)
        raise RuntimeError("pywebview is required to launch the desktop shell.") from exc

    try:
        webview.create_window(
            APP_TITLE,
            url=f"http://127.0.0.1:{port}/",
            width=1280,
            height=900,
            min_size=(1100, 720),
        )
        webview.start(gui="edgechromium")
    finally:
        server.should_exit = True
        server_thread.join(timeout=5)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        details = traceback.format_exc()
        log_path = _append_error_log(type(exc).__name__, details)
        _show_error_dialog(
            f"{exc}\n\nDetails were written to:\n{log_path}"
        )
        raise SystemExit(1) from exc
