# Builds dist\Belfort.exe from the current checkout.
# Usage (from the repo root):  powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv\Scripts\python.exe")) { py -3.12 -m venv .venv }
.venv\Scripts\python -m pip install -q -r requirements.txt -r requirements-build.txt
.venv\Scripts\python -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging\belfort.spec

$exe = Get-Item "dist\Belfort.exe"
$hash = (Get-FileHash $exe -Algorithm SHA256).Hash
Set-Content -Path "dist\Belfort.exe.sha256" -Value "$hash  Belfort.exe" -Encoding ascii
Write-Host ("Built {0} ({1:N0} MB), SHA-256 {2}" -f $exe.FullName, ($exe.Length / 1MB), $hash)
