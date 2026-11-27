# Belfort for Android (T48)

A native Android app named Belfort. This first version is a Java shell around Belfort's own interface, built without Gradle, so it needs nothing beyond the Android SDK and a JDK.

## What it does

- **Start screen** (`assets/start.html`, works offline):
  - the candle loader, which takes over from the Android 12+ system splash
  - the quote
  - the address of the Belfort app on your computer
  - **Tip Check on the phone itself**: the same phrase rules as the desktop (`belfort/tipcheck/phrases.json`, copied in at build time), with no computer and no internet
- **Belfort's interface** in a WebView once connected, with the phone layout from `belfort/static/mobile.css` and `mobile.js`:
  - a bottom tab bar (Learn, Tip Check, Practice, Research, News)
  - safe areas and 44 px touch targets
- **Native pieces** through `window.BelfortNative` (`src/.../Bridge.java`):
  - **Haptics:** a light tap on tabs, "confirm" for a clear result or a right answer, "reject" for red flags or a wrong answer.
  - **The share sheet:** the Tip Check 9:16 card goes to WhatsApp, Instagram and other apps, through `ShareProvider`, read-only.
  - **A daily streak reminder notification:** `remindDaily(hour)`, which asks for notification permission on Android 13+.
- **Links** to SEBI, SCORES and news sources open in the phone's browser.

## Build

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.10.7-hotspot"   # any JDK 17+
$env:ANDROID_HOME = "<your Android SDK>"                              # needs platforms;android-35 and build-tools;35.0.0
.venv\Scripts\python android\build_apk.py
```

The result is `android/build/Belfort.apk` (about 100 KB). It's signed with a debug key that is created next to the SDK, never in this repository. Add `--release` for a build that isn't debuggable and only allows HTTPS.

To install it, copy the APK to the phone and open it (allow "install unknown apps" for your file manager), or use `adb install android/build/Belfort.apk` if platform-tools are installed.

## Connect it to Belfort on your computer

1. On the computer, set an access code, then start Belfort so the phone can reach it:
   ```powershell
   $env:ACCESS_CODES = "pick-a-code"
   .venv\Scripts\python -m uvicorn belfort.main:app --host 0.0.0.0 --port 8766
   ```
2. On the phone (same Wi-Fi), enter `http://<computer's Wi-Fi IP>:8766`, then the access code when asked.

Accounts (T43) switch off while `ACCESS_CODES` is set, because a shared server would share one account.

## What's next (phase 2)

**Running Belfort's Python on the phone,** so Research, Practice and Learn work without the computer. This uses Chaquopy, which needs Gradle. Its package index has numpy 1.26 and pandas 2.1 but no pydantic-core (FastAPI) and no curl_cffi (yfinance). So phase 2 needs:
- a thin adapter in place of FastAPI
- a Yahoo chart-JSON provider
- a CI job that runs the core on those versions

**Signing in on the phone itself** (T43's Supabase, with Google through a Custom Tab and an app link) comes with phase 2, because a phone connected to a computer uses that computer's session.
