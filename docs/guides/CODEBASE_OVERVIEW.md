# Belfort: codebase overview

A short map of the project for someone new to it. For a deeper, code-level walkthrough, run `/explain-codebase`.

## 1. The big idea

Belfort is a free, open-source (MIT) desktop app that helps people in India learn about the stock market safely. It has four parts:

- **Research:** a rule-based report on any NSE stock.
- **Learn:** a game-style course with lessons, exercises, XP and streaks.
- **Practice:** paper trading, predictions and chart replay, all with virtual points.
- **News:** public RSS feeds, cleaned up and tagged.

On top of those, **Tip Check** reads a forwarded WhatsApp or Telegram stock tip and points out its red flags. An optional AI assistant explains what is on screen, using the user's own API key.

It runs entirely on the user's own computer. There is no Belfort server, no telemetry and no money. It never gives buy, sell or hold advice and never predicts prices; `docs/COMPLIANCE.md` sets these rules.

## 2. Tech stack

| Technology | What it is used for |
|---|---|
| Python 3.12 + FastAPI + Uvicorn | The local backend and its JSON API |
| pandas, numpy | Price data and indicator calculations |
| yfinance, httpx | Fetching prices, company figures, NSE files and RSS feeds |
| SQLite | One local file (`data/belfort.db`) holding trades, progress and settings |
| Plain HTML, CSS and JavaScript | The interface. There is no build step and no framework. |
| TradingView Lightweight Charts | Price charts (vendored in `belfort/static/vendor/`) |
| pywebview + PyInstaller | The Windows app window, and packaging it as one `Belfort.exe` |
| Java + the Android SDK | The Android app, built without Gradle |
| pytest, Ruff, pre-commit, GitHub Actions | Tests, linting and CI |

## 3. How the parts fit together

```
 Desktop window (pywebview)    or    Browser    or    Android app (WebView)
            │                                                 │
            │  static HTML/CSS/JS + JSON calls                │  same pages over Wi-Fi
            ▼                                                 ▼
 ┌───────────────────── FastAPI on 127.0.0.1 (belfort/main.py) ─────────────────────┐
 │  research/   learn/   practice/   news/   tipcheck/   assistant/                 │
 │      │          │         │         │         │            │                     │
 │      └──────────┴─── core/ (compliance wording, glossary, SQLite, languages) ───┘│
 │                         data/ (providers + disk cache)                            │
 └───────────────────────────────────────────────────────────────────────────────────┘
            │                         │                         │
     Yahoo Finance, NSE files   publisher RSS feeds    the AI provider chosen by the user
```

- The front end is static files served by FastAPI. Each part of the app calls its own `/api/...` router.
- Each router uses pure "rules" modules that do no input or output, which makes them easy to test. Database and network access goes through `core/db.py` and `data/`.
- Lessons, the syllabus, the news feed list and the company aliases are plain files in `content/`, not code.
- The AI key stays in the user's browser. It is sent with each request in `X-AI-*` headers and is never stored.
- `run_desktop.py` starts the server and opens it in an app window. PyInstaller turns that into `Belfort.exe`.
- The Android app shows a start screen and an offline Tip Check. It then loads Belfort's interface from the PC over Wi-Fi.

## 4. File by file

### Root
- `README.md`: what Belfort is, what's built, and how to run it.
- `CLAUDE.md`: hard rules for AI assistants (no AI attribution, compliance, work from the task list).
- `CHANGELOG.md`: changes users would notice. `CHANGES.md` and `CHANGES_Devansh.md` are the developers' iteration logs.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `LICENSE`: standard project policies.
- `pyproject.toml`: Ruff and pytest settings, and the coverage threshold (70%).
- `requirements.txt`, `requirements-dev.txt`, `requirements-build.txt`: pinned dependencies for running, developing and packaging.
- `run.bat`: starts the app from source on Windows.
- `run_desktop.py`: the desktop launcher. It shows the loader, starts the server and opens the app window.
- `.env.example`: optional settings, with placeholders only. `.pre-commit-config.yaml`: lint and commit-message hooks.
- `.editorconfig`, `.gitattributes`, `.gitignore`: editor and git housekeeping.

### `belfort/`: the backend
- `main.py`: builds the FastAPI app, includes every router and serves `static/`.
- `settings.py`: every threshold and style preset the rules use, in one place.

**`core/`** (shared by every part)
- `compliance.py`: banned wording, the disclaimer and the AI notice. Changes need Sarthak's approval.
- `db.py`: the SQLite connection and numbered migrations.
- `glossary.py`, `glossary_search.py`: the plain-language dictionary and its ranked search.
- `i18n.py`, `prefs.py`: language lookup for messages the server sends, and each user's settings.
- `users.py`: works out who is using Belfort for the current request.

**`data/`** (where all outside data comes in)
- `providers.py`: the Yahoo and NSE providers. Every number they return has a source and a date.
- `market.py`: daily price bars for any part of the app. `lagged()` keeps lesson charts at least 30 days old.
- `cache.py`: a disk cache with a time-to-live.
- `symbols.py`: finds a company from part of its name, its initials, a nickname or a typo.
- `universe.py`: a built-in list of large companies with their sectors, used for peers and backtests.

**`research/`**
- `router.py`: search, screens, the per-stock report and pattern reliability.
- `screens.py`: three stock filters with fixed, visible criteria.
- `analysis/`:
  - `pipeline.py` runs the whole report for one stock.
  - `indicators.py`, `pivots.py`, `structure.py` and `patterns.py` read the chart.
  - `fundamentals.py` reads the company's figures.
  - `sizing.py` suggests a stop and a position size.
  - `verdict.py` gives the single descriptive label.
  - `explain.py` and `context.py` write the plain-language explanations.
- `backtest/`: `synthetic.py` builds test charts with known patterns, and `evaluate.py` measures how well the pattern detectors work.

**`learn/`**
- `curriculum.py`: loads the syllabus and the Markdown lessons, renders the exercises and grades them.
- `engine.py`: the pure game rules: XP, daily goal, streak and freezes, hearts and stage unlocks.
- `game.py`: stores game progress in SQLite, on top of `engine.py`.
- `router.py`: the Learn API.

**`practice/`**
- `engine.py`: pure rules for settling paper trades and scoring predictions.
- `service.py`: the paper account, the prediction journal and the chart-replay trainer.
- `analytics.py`: journal statistics. `backup.py`: CSV and JSON export, and restore.
- `router.py`: the Practice API (virtual points only).

**`news/`**
- `feeds.py`: reads RSS feeds, removes duplicates, tags companies and hides tip-like headlines.
- `router.py`: the News API.

**`tipcheck/`**
- `rules.py`: pure red-flag checks.
- `phrases.json`: tip wording for each language.
- `strings.py`: every sentence Tip Check shows.
- `sources.py`: reads NSE's surveillance file and a local copy of SEBI's registers. `register.py` imports those registers.
- `service.py` and `router.py`: run the checks and serve the API.

**`assistant/`**
- `chat.py`: the explainer chat, using the user's own key with Gemini or any OpenAI-compatible provider.
- `vision.py`: reads the text from a screenshot of a tip.
- `router.py`: the assistant API. `glossary_router.py`: the dictionary API.

**`static/`**: the front end
- `index.html`: the single page. Every script and stylesheet loads with a `?v=` version tag.
- `app.js`: the app shell, shared helpers and the Research view. `style.css`: the main styles.
- `verticals.js`: the Practice, News and Settings views.
- `learn-game.js` and `.css`: the Learn path, lesson player and rewards.
- `tipcheck.js` and `.css`: the Tip Check view. `dictionary.js` and `.css`: the Dictionary view.
- `stock-picker.js`: the reusable company search box.
- `i18n.js`, `i18n.css` and `i18n/*.json`: the language switcher and one translation file per language (eight languages).
- `mobile.js` and `.css`: the phone layout and the bridge to the Android app.
- `splash.*`: the startup loader. `intro.*`: the first-open intro.
- Images: mascot GIFs, logo and favicon. `vendor/`: the chart library and its licence.

### `content/`: data, not code
- `learn/syllabus.json`: stages, modules and lessons.
- `learn/lessons/*.md`: 38 English lessons, each with a quiz block. `lessons/hi/` has 16 Hindi drafts.
- `news/feeds.json`: the default news feeds.
- `symbols/aliases.json`: company nicknames. `symbols/companies.json`: the fallback company list.
- `compliance/banned.hi.json`: banned wording in Hindi.

### `android/`: the Android app
- `src/.../MainActivity.java`: the WebView app.
- `Bridge.java`: haptics, sharing and the reminder. `ShareProvider.java` and `ReminderReceiver.java` support those.
- `assets/start.*` and `tipcheck-offline.js`: the start screen and the offline Tip Check.
- `res/`, `AndroidManifest.xml`: Android resources and the app manifest.
- `build_apk.py`: builds the APK with aapt2, javac, d8, zipalign and apksigner, without Gradle.
- `README.md`: how to build and connect it.

### Other folders
- `docs/`:
  - `ARCHITECTURE.md`: the full design.
  - `COMPLIANCE.md`: the rules.
  - `CONVENTIONS.md`: names, branches and commit messages.
  - `TASKS.md`: the task list.
  - `STATUS.md`, `ROADMAP.md`, `SYLLABUS.md`, `ABOUT.md`, `LANDSCAPE.md`: project context.
  - `assets/`: screenshots and the architecture diagram.
- `packaging/belfort.spec`: the PyInstaller recipe for `Belfort.exe`.
- `scripts/`:
  - `build_windows.ps1` builds the exe.
  - `create_shortcut.ps1` makes a desktop shortcut.
  - `run_backtest.py` refreshes `data/pattern_stats.json`.
  - `ci/check_commit_policy.py` blocks AI attribution in commits.
- `data/pattern_stats.json`: measured pattern reliability, shown in the app. This folder also holds the local database at runtime.
- `site/`: the static landing page.
- `tests/`: offline tests, about one file per module, with every network source faked. `fixtures/` has sample NSE and SEBI files.
- `.github/`: the CI workflow, code owners, Dependabot, and issue and PR templates. Owned by Sarthak.

## 5. How to run it

From the repo root on Windows:

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\pre-commit install --hook-type pre-commit --hook-type commit-msg
.venv\Scripts\python -m uvicorn belfort.main:app --port 8765 --reload   # then open http://127.0.0.1:8765
.venv\Scripts\python -m pytest --cov
.venv\Scripts\ruff check . ; .venv\Scripts\ruff format .
```

- **Desktop window:** `run.bat`, or `.venv\Scripts\python run_desktop.py`.
- **Windows exe:** `powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1`, which writes `dist\Belfort.exe`.
- **Android APK:** set `JAVA_HOME` and `ANDROID_HOME`, then run `.venv\Scripts\python android\build_apk.py`, which writes `android\build\Belfort.apk`.

## 6. Where to start

1. `README.md`, then `docs/ARCHITECTURE.md`: what it is and how it's laid out.
2. `docs/COMPLIANCE.md`: the rules every change must follow.
3. `belfort/main.py`: shows how every part is plugged in.
4. `belfort/research/analysis/pipeline.py`: the core report, from start to finish.
5. `belfort/static/app.js`: how the front end talks to the API.
