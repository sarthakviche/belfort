# Changes log (Belfort 2 sprint)

A running log of every change made in the Belfort 2 sprint, newest first. `CHANGELOG.md` stays the user-facing release notes; this file records what was done, by whom, on which branch, and why.

## 2026-11-28 — T48 Belfort for Android, first version (Devansh's agent, branch `feat/T48-android`)

### Decisions
- **Build without Gradle,** with the tools already on Devansh's machine: Android SDK 35 (platform and build-tools 35.0.0) and JDK 21. The pipeline is aapt2, javac, d8, zipalign, then apksigner, in `android/build_apk.py`. There are no downloads, and the debug key is kept next to the SDK, outside git.
- **First version (agreed with Sarthak's agent):**
  - a Java shell whose WebView shows Belfort's own interface from the user's computer over Wi-Fi (with `ACCESS_CODES`)
  - native pieces for the splash, haptics, share sheet and streak notifications
  - an offline start screen with Tip Check's text rules running on the phone
- **Chaquopy is phase 2.** Running the Python core on the phone needs Gradle and an adapter in place of FastAPI (no pydantic-core or curl_cffi builds; numpy 1.26 and pandas 2.1 only).
- **Phone layout is plain web** (`mobile.css`, `mobile.js`), so narrow browser windows get it too:
  - a bottom tab bar in Sarthak's order (Learn, Tip Check, Practice, Research, News)
  - safe areas, 44 px targets, 16 px inputs (no zoom on focus)
  - no hover-only UI
- **The share sheet hooks in through `navigator.share`:** inside the app it's replaced by the native sheet, so Tip Check's share button works unchanged. Haptics are offered as `window.belfortHaptic(kind)` for T42.

### Changes
- **New `android/`:**
  - `AndroidManifest.xml`
  - resources: strings, a theme, the Android 12+ splash theme and a candle splash icon
  - Java: `MainActivity`, `Bridge`, `ShareProvider`, `ReminderReceiver`
  - assets: `start.html`, `start.css`, `start.js`, `tipcheck-offline.js`
  - `build_apk.py`, `README.md`, `.gitignore`
- **New `belfort/static/mobile.js` and `mobile.css`.** `index.html` gets one stylesheet tag, one script tag, and `viewport-fit=cover`.
- **Tests:** `tests/test_android.py`, 7 offline tests. They check the manifest and components, that the bridge matches the page's calls, the share-provider path guard, the build's message when the SDK is missing, the script order, the regex syntax and that no build output or keys are committed.
- **Docs:** CHANGELOG, ARCHITECTURE, STATUS, `android/README.md`.

### Checked
- `ruff`, plus the full test suite.
- **APK:** `android/build_apk.py` built `android/build/Belfort.apk` (104 KB). `apksigner verify` passes, and `aapt2 dump badging` shows `app.belfort.android`, label Belfort, target SDK 35 and the launcher activity.
- **In a 375 px browser:**
  - The start screen's loader and the offline Tip Check work: a Hinglish tip gave 5 red flags, with no sideways scroll.
  - Belfort's interface shows the bottom tab bar and switches views.
- **Not yet:** installing on a phone or emulator. The machine has no platform-tools or emulator.

## 2026-11-27 — sprint set-up (Sarthak's agent)

### Decisions
- **Accounts replace offline-only.** Supabase Auth plus one `user_state` table with row-level security. Desktop and Android sign in to the same project, and the paper account, journal and Learn progress sync as whole JSON documents (the T10 backup format), last write wins. "Continue without an account" keeps today's local mode. (T43)
- **Hook feature: Tip Check.** Paste or screenshot a stock tip and see its red flags in ten seconds: SEBI registration, promised returns, urgency, NSE surveillance lists and a pump-and-dump price and volume check. Chosen because it protects a real person from a real loss and fits every compliance rule: it reports red flags, never a buy or sell view. (T44)
- **Learn becomes a path in three stages.** Beginner = Foundations plus Scams, tips and your rights (scam safety belongs at the start). Intermediate = Practitioner plus Taxes and records. Advanced = Market context, Running several trades, Psychology. Locked stages show titles only; the API refuses their content. (T42)
- **Mascot:** the headless suit with the yellow tie, from `design assets/mascot gifs/`, copied to `belfort/static/img/mascot/` (`mascot-suit.gif`, `mascot-shrug.gif`).
- **Quote** for the intro and landing page: "Risk comes from not knowing what you're doing." (Warren Buffett). It lives in one constant so it can be swapped.
- **Look:** neon green and red candles drawing on black (from the intro inspiration), large editorial serif type for the quote, Belfort yellow (#facc15) for the accent.
- **Inspiration videos and images** in `design assets/intro animation inspos/` stay out of git: they are third-party downloads, for reference only.
- **Work split (equal):** Devansh's side takes T48 Android, T43 accounts and sync, T44 Tip Check (technical architecture and market-domain data). Sarthak's side takes T42 gamified Learn, T45 dictionary, T46 loader, T47 landing site, T21 and T22 lessons, T49 exercises (design, UI and content).
- **Multi-language (T50):** English first, with Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati and Kannada. Interface strings in shared catalogues for desktop and Android; Beginner lessons in Hindi first; Ask Belfort, Tip Check and the dictionary answer in the chosen language. Tip Check reads Hinglish tips. Owned by Sarthak's side, starting after T42 to avoid editing every screen twice.
- **COMPLIANCE.md rule 7 amended** (raised by Devansh's agent): local-first with optional accounts; only the user's own practice, learning and settings documents sync; DPDP Act 2023 privacy notice and in-app account deletion required; legal sign-off is D3. Needs Sarthak's approval at review, per CLAUDE.md.
- **Database migrations:** 7 = Devansh's optional stop-loss (`feat/report-redesign-and-logic`), 8 = T42 Learn game tables, 9 = T43 user_id columns. Whoever merges second renumbers; migrations are appended, never edited after merge.
- **Agent coordination** happens in `conversations.md` on the `collab` branch. The Android app (T48) is built on Devansh's machine.

### Changes
- `docs/TASKS.md`: Phase 6 with tasks T42 to T49 and the shared contracts (current user, stages, exercise types, new UI in its own files).
- `content/learn/syllabus.json`: every module has a `stage`.
- `belfort/core/users.py`: `current_user_id()` stub that returns `"local"` until T43.
- `belfort/static/img/mascot/`: the two mascot GIFs.
