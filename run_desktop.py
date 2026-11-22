"""Belfort desktop launcher: starts the backend and shows the UI in its own app window.

One process does both jobs. Closing the window stops the server.
Works from source (`python run_desktop.py`) and as the packaged Windows app (Belfort.exe).
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
# Bundled files live next to the code (or in PyInstaller's unpack folder); user data never does.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
if FROZEN:
    DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Belfort"
    os.environ.setdefault("BELFORT_DATA_DIR", str(DATA_DIR))
else:
    DATA_DIR = Path(os.environ.get("BELFORT_DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

PREFERRED_PORT = int(os.environ.get("BELFORT_PORT", "8766"))  # 8765 is the older Belfort AI
WINDOW_TITLE = "Belfort"
LR_LOADFROMFILE, IMAGE_ICON, WM_SETICON = 0x10, 1, 0x80  # Win32 constants for the window icon

# A windowed app has no console, so stdout/stderr are None and logging would crash the server.
if sys.stdout is None or sys.stderr is None:
    _log = open(DATA_DIR / "belfort.log", "a", encoding="utf-8", buffering=1)  # noqa: SIM115 (open for the whole run)
    sys.stdout = sys.stdout or _log
    sys.stderr = sys.stderr or _log


def port_in_use(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def is_belfort(port: int) -> bool:
    """True if this port already serves this Belfort (its config reports a version)."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/config", timeout=2) as r:
            return "version" in json.loads(r.read().decode("utf-8"))
    except Exception:
        return False


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port: int):
    import uvicorn

    from belfort.main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", log_config=None)
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    return server


def wait_ready(port: int, seconds: float = 60) -> bool:
    end = time.time() + seconds
    while time.time() < end:
        if port_in_use(port):
            return True
        time.sleep(0.25)
    return False


def set_icon():
    """Give the app window the Belfort logo (taskbar, Alt+Tab, title bar)."""
    try:
        import ctypes

        u = ctypes.windll.user32
        ico = str(ROOT / "scripts" / "belfort.ico")
        for _ in range(40):  # wait for the window to exist
            hwnd = u.FindWindowW(None, WINDOW_TITLE)
            if hwnd:
                break
            time.sleep(0.25)
        else:
            return
        for kind, size in ((1, 48), (0, 16)):  # big icon (taskbar), small icon (title bar)
            h = u.LoadImageW(None, ico, IMAGE_ICON, size, size, LR_LOADFROMFILE)
            if h:
                u.SendMessageW(hwnd, WM_SETICON, kind, h)
    except Exception:
        pass


def main():
    server = None
    port = PREFERRED_PORT
    if port_in_use(port) and not is_belfort(port):
        port = free_port()  # something else (for example the older Belfort AI) holds the port
    if not port_in_use(port):  # already running? just open a window on it
        server = start_server(port)
        if not wait_ready(port):
            sys.exit("Belfort: the server did not start.")
    url = f"http://127.0.0.1:{port}"

    try:
        import webview
    except ImportError:  # no pywebview: fall back to an Edge app window
        subprocess.Popen(["msedge", f"--app={url}"])
        if server:
            while True:
                time.sleep(3600)
        return

    store = DATA_DIR / "webview"  # keeps open files, settings and the AI key between launches
    store.mkdir(parents=True, exist_ok=True)
    try:  # own taskbar identity, so Windows stops grouping it under Python
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Belfort.App")
    except Exception:
        pass
    webview.create_window(WINDOW_TITLE, url, width=1500, height=950, min_size=(1000, 650), background_color="#08080a")
    webview.start(set_icon, private_mode=False, storage_path=str(store))
    if server:
        server.should_exit = True


if __name__ == "__main__":
    main()
