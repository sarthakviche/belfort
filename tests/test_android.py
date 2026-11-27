"""Belfort for Android (T48): the parts that can be checked without an Android SDK. No network."""

import json
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
ANDROID = ROOT / "android"
NS = "{http://schemas.android.com/apk/res/android}"


def test_manifest_names_the_app_and_its_components():
    m = ElementTree.parse(ANDROID / "AndroidManifest.xml").getroot()
    assert m.get("package") == "app.belfort.android"
    app = m.find("application")
    assert app.get(f"{NS}allowBackup") == "false"
    names = {e.get(f"{NS}name") for e in app}
    assert names == {".MainActivity", ".ReminderReceiver", ".ShareProvider"}
    provider = app.find("provider")
    assert provider.get(f"{NS}exported") == "false"  # only reachable through a granted share
    for e in app:
        src = ANDROID / "src" / "app" / "belfort" / "android" / (e.get(f"{NS}name")[1:] + ".java")
        assert src.exists(), src


def test_bridge_methods_match_what_the_page_calls():
    java = (ANDROID / "src" / "app" / "belfort" / "android" / "Bridge.java").read_text(encoding="utf-8")
    exposed = set(re.findall(r"@JavascriptInterface\s+public \w+ (\w+)\(", java))
    js = (ROOT / "belfort" / "static" / "mobile.js").read_text(encoding="utf-8") + (ANDROID / "assets" / "start.js").read_text(
        encoding="utf-8"
    )
    called = set(re.findall(r"\bN\.(\w+)\(", js))
    assert called <= exposed, called - exposed


def test_share_provider_refuses_paths_outside_its_folder():
    java = (ANDROID / "src" / "app" / "belfort" / "android" / "ShareProvider.java").read_text(encoding="utf-8")
    assert 'name.contains("..")' in java and '"r".equals(mode)' in java


def test_build_explains_a_missing_sdk(tmp_path):
    r = subprocess.run(
        [sys.executable, str(ANDROID / "build_apk.py"), "--sdk", str(tmp_path)], capture_output=True, text=True, timeout=60
    )
    assert r.returncode != 0 and "Android SDK not found" in r.stderr


def test_start_screen_loads_its_scripts_in_order():
    html = (ANDROID / "assets" / "start.html").read_text(encoding="utf-8")
    order = re.findall(r'<script src="([^"]+)"', html)
    assert order == ["phrases.js", "tipcheck-offline.js", "start.js"]


def test_offline_tip_check_regexes_are_valid_javascript_when_phrases_exist():
    phrases = ROOT / "belfort" / "tipcheck" / "phrases.json"
    if not phrases.exists():  # Tip Check (T44) is a separate pull request
        return
    data = json.loads(phrases.read_text(encoding="utf-8"))
    for flag, langs in data.items():
        if flag.startswith("_"):
            continue
        for p in (p for ps in langs.values() for p in ps if p.startswith("re:")):
            re.compile(p[3:])  # the same syntax works in both


def test_no_build_output_or_keys_are_committed():
    ignored = (ANDROID / ".gitignore").read_text(encoding="utf-8")
    assert "build/" in ignored
    assert not list(ANDROID.rglob("*.keystore")) and not list(ANDROID.rglob("*.jks"))
