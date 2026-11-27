"""The desktop launcher shows the loader first and opens the app only when the server is ready."""

import time
from pathlib import Path

import run_desktop


class FakeWindow:
    def __init__(self):
        self.calls = []

    def load_url(self, url):
        self.calls.append(("url", url))

    def load_html(self, html):
        self.calls.append(("html", html))


def test_splash_page_exists_and_is_a_file_url():
    url = run_desktop.splash_url()
    assert url and url.startswith("file:")
    assert Path(run_desktop.ROOT, "belfort", "static", "splash.html").is_file()


def test_app_url_tells_the_app_the_loader_already_played():
    assert run_desktop.app_url(8766) == "http://127.0.0.1:8766/?splash=0"


def test_navigates_to_the_app_after_the_minimum_time():
    window = FakeWindow()
    started = time.monotonic()
    assert run_desktop.navigate_when_ready(window, 9, started, ready=lambda p: True, min_seconds=0.2)
    assert window.calls == [("url", "http://127.0.0.1:9/?splash=0")]
    assert time.monotonic() - started >= 0.2


def test_shows_a_message_when_the_server_never_starts():
    window = FakeWindow()
    assert not run_desktop.navigate_when_ready(window, 9, time.monotonic(), ready=lambda p: False, min_seconds=0)
    assert window.calls[0][0] == "html" and "could not start" in window.calls[0][1]


def test_loader_and_intro_are_wired_into_the_app_page():
    static = Path(run_desktop.ROOT, "belfort", "static")
    html = (static / "index.html").read_text(encoding="utf-8")
    for name in ("splash.css", "splash.js", "intro.css", "intro.js"):
        assert name in html and (static / name).is_file()
    assert "belfort:app-ready" in (static / "app.js").read_text(encoding="utf-8")
    assert "INTRO_QUOTE" in (static / "intro.js").read_text(encoding="utf-8")
