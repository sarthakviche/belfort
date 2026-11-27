"""Build Belfort for Android (T48) without Gradle: aapt2 -> javac -> d8 -> zipalign -> apksigner.

Needs a JDK 17 or newer (JAVA_HOME) and the Android SDK with platforms;android-35 and build-tools;35.0.0
(ANDROID_HOME, or --sdk). No downloads: everything comes from those two folders.

    python android/build_apk.py                     development build (debuggable, plain HTTP to your computer)
    python android/build_apk.py --release           not debuggable; the computer's address must use HTTPS
    python android/build_apk.py --phrases FILE      take Tip Check's phrases from FILE (default: belfort/tipcheck/phrases.json)

Output: android/build/Belfort.apk, signed with a debug key kept outside the repository (next to the SDK).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
OUT = APP / "build"
EXE = ".exe" if os.name == "nt" else ""
BAT = ".bat" if os.name == "nt" else ""
PLATFORM, BUILD_TOOLS = "android-35", "35.0.0"


def java_home() -> Path:
    for c in (os.environ.get("JAVA_HOME", ""),):
        if c and (Path(c) / "bin" / f"javac{EXE}").exists():
            return Path(c)
    sys.exit("JDK not found: set JAVA_HOME to a JDK 17 or newer (JDK 21 recommended).")


def run(*cmd, env=None):
    print(">", Path(str(cmd[0])).name, *[str(c) for c in cmd[1:3]], "...")
    subprocess.run([str(c) for c in cmd], check=True, env=env)


def icons(res: Path) -> None:
    """The launcher icon from belfort/static/img/logo.png (512 px). In the highest density folder only: Android
    scales it down for every other screen."""
    d = res / "mipmap-xxxhdpi"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "belfort" / "static" / "img" / "logo.png", d / "ic_launcher.png")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Belfort for Android")
    ap.add_argument("--sdk", default=os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "")
    ap.add_argument("--release", action="store_true", help="not debuggable, HTTPS only")
    ap.add_argument("--phrases", default=str(ROOT / "belfort" / "tipcheck" / "phrases.json"))
    a = ap.parse_args()
    sdk = Path(a.sdk) if a.sdk else None
    if not sdk or not (sdk / "platforms" / PLATFORM / "android.jar").exists() or not (sdk / "build-tools" / BUILD_TOOLS).exists():
        sys.exit(
            f"Android SDK not found: set ANDROID_HOME or pass --sdk (needs platforms;{PLATFORM} and build-tools;{BUILD_TOOLS})."
        )
    jar, bt = sdk / "platforms" / PLATFORM / "android.jar", sdk / "build-tools" / BUILD_TOOLS
    jh = java_home()
    env = dict(os.environ, JAVA_HOME=str(jh), PATH=str(jh / "bin") + os.pathsep + os.environ["PATH"])

    shutil.rmtree(OUT, ignore_errors=True)
    (OUT / "classes").mkdir(parents=True)
    # 0. staged inputs: resources with icons, assets with Tip Check's phrases, the manifest for this build type
    shutil.copytree(APP / "res", OUT / "res")
    icons(OUT / "res")
    shutil.copytree(APP / "assets", OUT / "assets")
    phrases = Path(a.phrases)
    if phrases.exists():
        data = json.loads(phrases.read_text(encoding="utf-8"))
        (OUT / "assets" / "phrases.js").write_text(
            "// Copied from belfort/tipcheck/phrases.json by android/build_apk.py.\nwindow.TIP_PHRASES = "
            + json.dumps(data, ensure_ascii=False)
            + ";\n",
            encoding="utf-8",
        )
    else:
        print(f"note: {phrases} not found, so the offline Tip Check is left out of this build")
    manifest = (APP / "AndroidManifest.xml").read_text(encoding="utf-8")
    if a.release:
        manifest = manifest.replace('android:debuggable="true"', 'android:debuggable="false"').replace(
            'android:usesCleartextTraffic="true"', 'android:usesCleartextTraffic="false"'
        )
    (OUT / "AndroidManifest.xml").write_text(manifest, encoding="utf-8")

    # 1. resources, manifest and assets
    run(bt / f"aapt2{EXE}", "compile", "--dir", OUT / "res", "-o", OUT / "res.zip")
    run(
        bt / f"aapt2{EXE}",
        "link",
        "-o",
        OUT / "base.apk",
        "-I",
        jar,
        "--manifest",
        OUT / "AndroidManifest.xml",
        "-A",
        OUT / "assets",
        "--java",
        OUT / "gen",
        "--min-sdk-version",
        "26",
        "--target-sdk-version",
        "35",
        OUT / "res.zip",
    )
    # 2. Java to classes to dex
    srcs = [str(p) for p in (APP / "src").rglob("*.java")] + [str(p) for p in (OUT / "gen").rglob("*.java")]
    run(
        jh / "bin" / f"javac{EXE}", "--release", "11", "-Xlint:-options", "-classpath", jar, "-d", OUT / "classes", *srcs, env=env
    )
    classes = [str(p) for p in (OUT / "classes").rglob("*.class")]
    run(bt / f"d8{BAT}", "--min-api", "26", "--lib", jar, "--output", OUT, *classes, env=env)
    with zipfile.ZipFile(OUT / "base.apk", "a") as z:
        z.write(OUT / "classes.dex", "classes.dex")
    # 3. align and sign with a debug key kept next to the SDK, never in the repository
    run(bt / f"zipalign{EXE}", "-f", "-p", "4", OUT / "base.apk", OUT / "aligned.apk")
    ks = sdk / "belfort-debug.keystore"
    if not ks.exists():
        run(
            jh / "bin" / f"keytool{EXE}",
            "-genkeypair",
            "-keystore",
            ks,
            "-alias",
            "belfort",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-storepass",
            "android",
            "-keypass",
            "android",
            "-dname",
            "CN=Belfort Debug,O=Belfort,C=IN",
            env=env,
        )
    apk = OUT / "Belfort.apk"
    run(
        bt / f"apksigner{BAT}",
        "sign",
        "--ks",
        ks,
        "--ks-pass",
        "pass:android",
        "--key-pass",
        "pass:android",
        "--out",
        apk,
        OUT / "aligned.apk",
        env=env,
    )
    run(bt / f"apksigner{BAT}", "verify", apk, env=env)
    print(f"\nAPK: {apk} ({apk.stat().st_size // 1024} KB), {'release' if a.release else 'development'} build")


if __name__ == "__main__":
    main()
