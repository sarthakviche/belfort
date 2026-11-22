# PyInstaller spec for the Windows app. Build with:  scripts\build_windows.ps1
# Produces dist\Belfort.exe: one file, windowed, user data in %LOCALAPPDATA%\Belfort.
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).parent  # noqa: F821 (SPECPATH is provided by PyInstaller)

datas = [
    (str(ROOT / "belfort" / "static"), "belfort/static"),
    (str(ROOT / "content"), "content"),
    (str(ROOT / "data" / "pattern_stats.json"), "data"),
    (str(ROOT / "scripts" / "belfort.ico"), "scripts"),
]

hiddenimports = (
    collect_submodules("belfort")
    + collect_submodules("uvicorn")
    + ["webview.platforms.winforms", "webview.platforms.edgechromium"]
)

a = Analysis(  # noqa: F821
    [str(ROOT / "run_desktop.py")],
    pathex=[str(ROOT)],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "matplotlib", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Belfort",
    icon=str(ROOT / "scripts" / "belfort.ico"),
    console=False,
    upx=False,
    version=None,
)
