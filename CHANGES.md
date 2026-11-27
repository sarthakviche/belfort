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

## 2026-11-28 — T47 landing site

### Changes
- `site/index.html` rebuilt (PR #34, stacked on the README PR #31): canvas candlestick hero under a 60% black layer and vignette, mascot, Buffett quote, Tip Check, Learn path, Practice/Research/News cards, accounts, open source, compliance footer. `site/img/` holds the mascot GIFs and two screenshots.
- To use a video hero, add `site/img/hero-bg.mp4` (or `.webm`); it replaces the canvas. Reduced motion shows a static frame.
- Tip Check, streak and XP on the page are illustrations; those features ship with T44 and T42.

## 2026-11-28 — T50 languages

Branch `feat/T50-languages`, built on `feat/T42-gamified-learn` with T22 (safety lessons), T46 (loader and intro) and T45 (dictionary search) merged in.

### Decisions
- **Catalogues:** flat JSON per language in `belfort/static/i18n/`, English as source and fallback, `{name}` placeholders, `_one` plural keys, `@key` placeholder values. About 630 keys. Written for the web and reusable by Android.
- **Code uses `T()`** as well as `t()`: several files have local variables named `t`, so `T` is the same function under a name that cannot be shadowed. Static markup uses `data-i18n*`.
- **No reload:** `setLanguage` re-applies markup and fires `belfort:language`; app.js redraws the current view. A Learn run in progress is restarted on a language change, because the exercise text and the server grading must be in the same language (ordering exercises compare the translated items).
- **Server messages** that carry a catalogue key (locked stage, no hearts) are translated from the same files and send `X-Error-Key`, so the page stops matching English words.
- **Lessons:** `lessons/<lang>/<id>.md`, same structure and quiz answers; the English file is the fallback. Hindi for all 16 Beginner lessons. The old Learn code in `verticals.js` (replaced by T42) was deleted instead of translated.
- **Compliance:** the Hindi banned list is data in `content/compliance/banned.hi.json`; `core/compliance.py` is untouched. The `disclaimer` catalogue key must equal `DISCLAIMER` in English (tested), and its translations need a fluent reader and Sarthak's review.
- **Not translated:** strings the Python engines write (verdicts, rule explanations, glossary meanings, news, practice notes).
- **Tests:** `tests/test_i18n.py`. One existing test no longer looks for a planned Beginner lesson (none are left after T22).

## 2026-11-28 — T46 startup loader and intro

Branch `feat/T46-startup-loader`.

### Decisions
- The Windows launcher loads `belfort/static/splash.html` from disk straight away, starts the server in a thread and, once the server answers and 2.3 s have passed, calls `window.load_url(app_url)`. The URL carries `?splash=0` so the app does not play the loader a second time.
- In a browser, `index.html` carries the same loader as an overlay at half duration (`--k: .5`), shown for at least 1.2 s and until `app.js` fires `belfort:app-ready`; a 9 s safety timer removes it regardless.
- The intro runs after `belfort:splash-done`, is remembered in `localStorage` (`belfort.intro.seen`, in try/catch) and fires `belfort:intro-done` (detail `{action}`) for T43 to hook its sign-in screen. There is no server-side settings store, so there is no server flag.
- The quote lives in `INTRO_QUOTE` in `intro.js`. System serif fonts (Instrument Serif where the app already loads it, then Georgia).

### Changes
- New: `belfort/static/splash.html`, `splash.css`, `splash.js`, `intro.css`, `intro.js`, `tests/test_desktop.py`.
- `run_desktop.py`: `splash_url`, `app_url`, `navigate_when_ready`; the window opens on the loader.
- `belfort/static/index.html` (loader div and four includes) and `app.js` (one event after init).
## 2026-11-28 — T45 dictionary search

### Decisions
- **Own router and module.** `belfort/assistant/glossary_router.py` (`/api/glossary/search`, `/ask`, `/web-search`) and the pure ranking in `belfort/core/glossary_search.py`; `assistant/chat.py` and `core/glossary.py` are untouched. `ask()` is called in `general` mode, so the existing compliance filter applies.
- **Web search from pywebview.** The desktop window does not open new browser windows, so inside it the page asks the backend (`POST /api/glossary/web-search`, loopback only) to call `webbrowser.open`; in a normal browser it uses `window.open`. The URL is `https://www.google.com/search?q=<term> stock market meaning`, URL-encoded.
- **Ranking.** Exact term, exact phrase, prefix, word prefix, substring, difflib closeness (0.75 cutoff), then a whole word in the explanation. Empty query returns the full glossary for browsing by category.
- **Old drawer.** The sidebar Dictionary button now opens the new page; the old drawer markup is left in place, unused.
- **Privacy.** Nothing about a query leaves the computer except on the user's own click on Ask Belfort (their AI provider) or Search the web (their browser).

### Changes
- New: `belfort/static/dictionary.js`, `dictionary.css`, `tests/test_dictionary.py`.
- Touched: `belfort/main.py` (router), `belfort/static/index.html` (nav item, section, links), `belfort/static/app.js` (view list, button, start hash), `CHANGELOG.md`, `docs/STATUS.md`, `docs/TASKS.md`.

## 2026-11-28 — T49 exercise types

Branch `content/T49-exercise-types`, built on `feat/T42-gamified-learn` (#37) with `content/T21-taxes-records` (#35) and `content/T22-safety` (#36) merged in. PR #38.

### What changed
- **Content:** 97 new exercises in all 38 lessons: 45 `number`, 41 `tf`, 11 `order`. Existing multiple-choice items are untouched. Every lesson has at least two new items of at least two types, each with a `why`. Numbers come from the lesson's own figures (position sizing, R multiples, expectancy, ATR stops, P/E, LTCG, Brier points).
- **Merge:** lesson counts now read "38 of 38"; both T21 and T22 are Done in `docs/TASKS.md`. A missing `),` and `(` between two glossary entries from the merge was fixed in `belfort/core/glossary.py`.
- **Tests:** new `tests/test_learn_exercises.py`. `test_quiz_grading_and_progress` falls back to an unknown id, because no planned lesson is left.

### Decisions
- Lessons with no calculation (biases, flows-and-events, myths, tip-scams, trend) use tf and order only.
- Wording avoids the banned phrases the content tests reject, for example "cannot lose" and "guarantee" were rephrased.

## 2026-11-28 — T42 gamified Learn

Branch `feat/T42-gamified-learn`, built on the sprint plan in #30.

### What changed
- **Engine (pure, no I/O):** `belfort/learn/engine.py` holds XP, the daily goal and streak with freezes, hearts, stage unlock rules, test sampling and the path builder. Dates are passed in. `belfort/learn/game.py` is the thin SQLite layer around it; `belfort/learn/router.py` gains `/path`, `/lessons/{id}/check`, `/tests/{kind}/{key}`, `/sessions/{id}/grade`, `/weak-spots`, `/goal` and `/placement/dismiss`. Thresholds are named constants in `belfort/settings.py`.
- **Exercise types:** `curriculum.py` validates and grades `mc`, `tf`, `order` and `number`. The public quiz payload has no answers; `order` items are shuffled on the server; grading is server side.
- **Locks:** the API returns 403 with a friendly sentence for the content, check and quiz of a lesson in a locked stage, and for starting a checkpoint or stage test there. Beginner is always open.
- **Database:** migration 8 (renumbered at merge; 7 is the optional stop-loss from #40) adds `learn_profile`, `learn_xp_days`, `learn_lessons`, `learn_tests`, `learn_weak` and `learn_sessions`, each with `user_id` (default `local`).
- **UI:** new `belfort/static/learn-game.js` and `learn-game.css` (path, lesson cards, exercises, results, confetti) and two still mascot PNGs for reduced motion. Only `index.html` changed (a link and a script tag).

### Decisions
- **Stage order:** stage comes from each module's `stage`; inside a stage, syllabus order. Safety is in the file under the Advanced track but is shown in Beginner.
- **Planned lessons** show as "coming soon" nodes and are not counted toward stage progress or the stage test, so unwritten Safety and Taxes lessons do not block anyone.
- **Stage test and checkpoints** open once every written lesson in the module or stage is done. Checkpoint: up to 8 questions from the module. Stage test: up to 12 from the stage. Both sample evenly across lessons. Pass mark 80%; 20 XP only on the first pass.
- **Placement test** is 12 questions from Beginner, offered on first open, and unlocks Intermediate only. Advanced always needs the Intermediate stage test.
- **Lessons in an unlocked stage are all open** (order is not forced); the first not-done node is highlighted as next. Once a stage test is passed, leftover checkpoints in that stage are not highlighted.
- **A lesson completes at 60%** (as before). Tests are graded all at once with no hearts lost; hearts are lost only on instant-feedback answers inside lessons. If hearts reach zero mid-lesson the run ends without XP.
- **XP:** 10 for a first completion, +5 for no mistakes, 5 for replaying a done lesson, 5 for a Weak spots review. Streak counts days the daily goal was met; a missed day spends a freeze if one is held; one freeze is earned at each multiple of 7 days, up to two.
- **Hearts:** 5 a day, refilled lazily when the date changes. With none left a new lesson cannot be started; a Weak spots review (up to 8 questions you missed) refills them when finished, whatever the score.
- **Test sessions:** a checkpoint, stage test, placement test or review is a server-side session of question references, graded once, so a page cannot grade a hand-picked easy subset.
- **Old progress counts:** rows in `lesson_progress` are treated as done for the local user, and finished lessons are still written there for the local user.
- **Order exercises** use tap-to-order (no drag), which also works on touch screens.
- **Hooks into other files:** the old Learn loader in `verticals.js` is left in place; `learn-game.js` loads after it, replaces `onView.learn` and makes `renderSyllabus` a no-op.
- **Tests:** an existing test now looks for a planned lesson in the Beginner stage, because planned lessons in locked stages answer 403 before 404.
## 2026-11-28 — T21 taxes and records lessons (Sarthak's agent)

### Changes
- `content/learn/lessons/capital-gains.md` and `records.md`: the two Taxes and records lessons, each with a quiz and a Sources line. Facts checked: STCG 20%, LTCG 12.5% above 1.25 lakh and the 12-month rule (Budget 2024, effective 23 July 2024, unchanged in Budget 2026 reporting), STT on delivery trades, loss set-off and 8-year carry-forward (Income Tax Department), intraday as speculative and F&O as non-speculative business income, ITR-2 against ITR-3.
- Left out because sources disagreed or could not be verified: tax audit turnover thresholds, exact reassessment time limits (the lesson says to check the current rule), exact STT percentages (the lesson points to the official sites).
- `content/learn/syllabus.json`: removed `planned` from both lessons. `belfort/core/glossary.py`: added STCG, LTCG, ITR.
- `CHANGELOG.md`, `docs/STATUS.md`, `docs/ABOUT.md`, `docs/TASKS.md`: 35 of 38 lessons written; T21 Done.
## 2026-11-28 — T22 scams, tips and your rights lessons (Sarthak's agent)

### Changes
- `content/learn/lessons/tip-scams.md`, `check-registration.md`, `myths.md`: the three Safety lessons, each with a quiz and a Sources line. They describe SEBI's January 2022 interim order on a Telegram tip channel, the May 2026 interim order on social-media pump-and-dump, and SEBI's October 2026 warning on invitation-only WhatsApp groups; how to search SEBI's registered intermediaries, SEBI Check, SCORES and NSE complaints; and six myths mapped to earlier lessons.
- Wording avoids the banned promise phrases, which the content test scans for, so "promised returns" and "buy at once" stand in for the usual scam phrases.
- Left out because unverified: a "Know your broker" NSE page (not found), helpline numbers, the exact SCORES stage-by-stage flow, the August 2024 SEBI circular text. The SCORES one-year limit and 21-day reply time come from secondary summaries and are hedged in the lesson. The statement that SEBI studies found most individual traders lose money is from memory and is flagged in the lesson's Sources line.
- Tip Check (T44) is referred to in words only; it may not have shipped when this merges.
- `content/learn/syllabus.json`: removed `planned` from the three lessons. `belfort/core/glossary.py`: added Pump and dump, Investment adviser, Research analyst, SCORES.
- `CHANGELOG.md`, `docs/STATUS.md`, `docs/ABOUT.md`, `docs/TASKS.md`: 36 of 38 on this branch alone (38 of 38 once T21 merges too; the count lines will need a trivial merge fix).
## 2026-11-28 — T44 Tip Check (Devansh's agent, branch `feat/T44-tip-check`)

### Decisions
- **Nine checks, in a fixed order:**
  1. SEBI registration
  2. Promised returns
  3. A price target with a deadline
  4. Pressure to hurry
  5. Claimed insider or secret information
  6. Requests for money or a move to a private group (added: this is where most tip scams take the money)
  7. NSE surveillance lists
  8. Pump pattern
  9. What the stock did the last time it looked like this

  The first eight count as red flags. The ninth is context only. Status per card: flag (red), clear (green), not checked (grey), context (yellow).
- **Surveillance data comes from NSE's daily `REG1_IND<ddmmyy>.csv`** on nsearchives (the host the app already uses). It has one column per measure: GSM, long- and short-term ASM, ESM, NSE's own flags for stocks named in unsolicited SMS and social-media tips, and insolvency. A value of 100 means "not under the measure"; any other value is the stage. Checked against the live file of 27 Nov 2026 (3,599 symbols).
- **SEBI registers:** SEBI has no download and no API, and its site refused scripted requests. So numbers get an offline shape check (INA or INH plus nine digits; INZ broker and INP portfolio-manager numbers are flagged as the wrong kind). They are compared with a local copy the user imports with `python -m belfort.tipcheck.register <saved lists>` (kept in the data folder, never in git). A match is reported as "in the copy of <date>, confirm the sender really is them", never as proof. Claims that SEBI "approved" a tip are always a flag.
- **Pump pattern** = at least two of three signals:
  - a session in the last 5 with volume at least 5× its 50-session average
  - a rise of at least 30% in 20 sessions or 60% in 60
  - a market value under ₹5,000 crore

  All thresholds are in `settings.py`.
- **"Last time"** uses only bars at least 30 days old, for both the episode and its outcome (20 and 60 sessions later, and the lowest close). It always ends with "This is what happened once before, not what will happen now."
- **Languages:** the tip's wording is matched from `belfort/tipcheck/phrases.json`, split by flag and language (`en`, `hinglish`, `hi`), so adding a language is a data change. Overlapping matches merge into one quote ("100% sure shot"). Every sentence Belfort shows is in `belfort/tipcheck/strings.py`, ready for T50's catalogues.
- **Compliance:** the tip's own words (which include banned phrases such as "sure shot") are shown only as quoted evidence in `<q data-quoted-tip>`. Belfort's wording is tested free of banned phrases. Every result says Belfort can't tell whether a trade will work and never calls a stock good, safe, or one to buy or sell. `compliance.py` and `chat.py` are unchanged.
- **Screenshots:** they're read by a new `belfort/assistant/vision.py` with the user's own key (Gemini or any OpenAI-compatible model). It only transcribes, and the text is put in the box for the user to see before the rules run.
- **Speed:** the stock checks run in parallel with an eight-second budget; a slow source shows as "not checked". A live check of a SUZLON tip took 1.3 s.

### Changes
- New `belfort/tipcheck/`: `rules.py` (pure checks), `phrases.json`, `strings.py`, `sources.py`, `register.py`, `service.py`, `router.py` (`POST /api/tipcheck`, `POST /api/tipcheck/image`).
- New `belfort/assistant/vision.py`.
- `belfort/settings.py`: the `TIP_*` thresholds.
- `belfort/main.py`: mounts the router.
- New `belfort/static/tipcheck.js` and `tipcheck.css`. `index.html` gets one nav item, one section, a stylesheet and a script tag; `app.js` gets the view name only. They add:
  - a "Paste a tip" box on the Research home
  - the Tip Check page with paste, upload, drop or paste-in screenshots
  - flag cards that flip in one by one (none under reduced motion)
  - a three-step risk meter
  - the mascot shrugging when flags are found
  - a stock picker to correct the stock
  - next steps with links to SEBI and SCORES, and the Safety lessons (shown as "coming soon" until T22 lands)
  - a 9:16 share card through the share sheet (or a download), and "Copy as text"
- Tests: `tests/test_tipcheck.py` (31 offline tests), with fixtures `tests/fixtures/reg1_ind_sample.csv` (NSE's real column header, made-up rows) and `tests/fixtures/sebi_register_sample.csv`.
- Docs: CHANGELOG, `docs/ARCHITECTURE.md`, `docs/STATUS.md`.

### Checked
- `ruff check`, `ruff format --check`, and `pytest --cov`: all pass, coverage 81.9%.
- In the running app (port 8766, live NSE and Yahoo data):
  - an English and Hinglish SUZLON tip gave 6 red flags in 8 checks, with SUZLON's 30 Nov 2023 volume spike shown as context
  - a Hindi (Devanagari) IRFC tip gave 4 red flags
  - a tip with no stock named offered the picker; picking Yes Bank re-ran the checks
  - the share card was generated and inspected
  - the page was checked at 375 px wide with no sideways scroll

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


- **Multi-language (T50):** English first, with Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati and Kannada. Interface strings in shared catalogues for desktop and Android; Beginner lessons in Hindi first; Ask Belfort, Tip Check and the dictionary answer in the chosen language. Tip Check reads Hinglish tips. Owned by Sarthak's side, starting after T42 to avoid editing every screen twice.
- **Agent coordination** happens in `conversations.md` on the `collab` branch. The Android app (T48) is built on Devansh's machine.

### Changes
- `docs/TASKS.md`: Phase 6 with tasks T42 to T49 and the shared contracts (current user, stages, exercise types, new UI in its own files).
- `content/learn/syllabus.json`: every module has a `stage`.
- `belfort/core/users.py`: `current_user_id()` stub that returns `"local"` until T43.
- `belfort/static/img/mascot/`: the two mascot GIFs.
