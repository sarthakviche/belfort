# Tasks: from v0.1 to Belfort 1.0 for Windows

> Temporary file for the founders. **Devansh owns every task below** unless the Owner says otherwise. When you start a task, set Owner and Status in your first commit. When it merges, set Status to Done and add the PR link.
>
> Work roughly in phase order. Inside a phase, any `Ready` task can go next. Every task follows the flow in [CONTRIBUTING.md](../CONTRIBUTING.md) and the definition of done in [CLAUDE.md](../CLAUDE.md).

**Priority:** P0 do first · P1 needed for 1.0 · P2 nice for 1.0 · P3 after 1.0
**Size:** S under half a day · M one to two days · L three days or more
**Status:** `Ready` · `Blocked` (on a named task or decision) · `In progress` · `Done`

## Overview

| ID | Task | Phase | P | Size | Status |
|---|---|---|---|---|---|
| T01 | Run Belfort and fix setup docs | 0 Onboarding | P0 | S | In progress |
| T02 | Try Ask Belfort with a real key | 0 Onboarding | P0 | S | Ready |
| T03 | Fuzzy stock picker everywhere | 1 Practice | P0 | M | Ready |
| T04 | Trade ticket: quote, mini chart, position-size helper | 1 Practice | P0 | M | Blocked on T03 |
| T05 | Faster portfolio: bar cache and daily settlement | 1 Practice | P1 | M | Ready |
| T06 | Replay: keep hidden bars on the server | 1 Practice | P1 | M | Ready |
| T07 | Trailing stops and partial exits | 1 Practice | P1 | M | Ready |
| T08 | Journal analytics | 1 Practice | P1 | M | Ready |
| T09 | Total open risk and size warnings | 1 Practice | P1 | S | Ready |
| T10 | Export and import the journal | 1 Practice | P2 | S | Ready |
| T11 | Equity curve | 1 Practice | P2 | M | Blocked on T05 |
| T12 | Content checker in CI | 2 Learn | P0 | S | Ready |
| T13 | Lessons: sessions, moving averages, volume | 2 Learn | P1 | M | Ready |
| T14 | Lessons: R multiples, losing streaks | 2 Learn | P1 | M | Ready |
| T15 | Lessons: Setups module (4) | 2 Learn | P1 | L | Ready |
| T16 | Lessons: Business check module (3) | 2 Learn | P1 | M | Ready |
| T17 | Lessons: Indicators and patterns module (3) | 2 Learn | P1 | M | Ready |
| T18 | Lessons: Journal module (3) | 2 Learn | P1 | M | Ready |
| T19 | Lessons: Market context module (3) | 2 Learn | P1 | M | Ready |
| T20 | Lessons: Portfolio and Psychology modules (4) | 2 Learn | P1 | M | Ready |
| T21 | Lessons: Taxes and records module (2) | 2 Learn | P1 | M | Ready |
| T22 | Lessons: Safety module (3) | 2 Learn | P1 | M | Ready |
| T23 | Replay drills inside lessons | 2 Learn | P1 | M | Ready |
| T24 | Module checkpoints and progress summary | 2 Learn | P2 | S | Ready |
| T25 | Editable rule profiles | 3 Research and News | P1 | L | Blocked on D1 |
| T26 | Watchlists and in-app alerts | 3 Research and News | P1 | M | Blocked on T03 |
| T27 | Market context panel | 3 Research and News | P2 | M | Ready |
| T28 | News: tag every NSE company | 3 Research and News | P1 | M | Blocked on T03 |
| T29 | News: NSE announcements and events calendar | 3 Research and News | P2 | L | Ready |
| T30 | A stock's news inside its report | 3 Research and News | P2 | S | Blocked on T28 |
| T31 | Browser end-to-end tests in CI | 4 Quality | P0 | M | Ready |
| T32 | Accessibility and small-window pass | 4 Quality | P1 | M | Ready |
| T33 | Error handling, logging and a "something went wrong" screen | 4 Quality | P1 | M | Ready |
| T34 | Gradual type checking with mypy | 4 Quality | P2 | M | Ready |
| T35 | Per-user data folder in %LOCALAPPDATA% | 5 Ship | P0 | M | Ready |
| T36 | Consolidate into one entry point | 5 Ship | P0 | M | Ready |
| T37 | Bundle fonts and chart library for offline use | 5 Ship | P0 | S | Ready |
| T38 | Windows build and installer | 5 Ship | P0 | L | Blocked on T35, T36, T37 |
| T39 | Release workflow | 5 Ship | P0 | M | Blocked on T38 |
| T40 | Ship Belfort 1.0 for Windows | 5 Ship | P0 | L | Blocked on all P0 and P1 tasks |
| T41 | Apply the brand decision | 5 Ship | P1 | S | Blocked on D2 |

---

## Phase 0: onboarding

### T01 · Run Belfort and fix setup docs
- **Owner:** Devansh · **P0 · S · Status:** In progress · **Area:** platform
- **Do:** Follow [ONBOARDING.md](ONBOARDING.md) on a clean clone. Fix anything wrong or unclear in ONBOARDING.md, README.md or CLAUDE.md.
- **Done when:** Merged PR `docs: fix onboarding steps (T01)`, or a PR that only marks the task Done if nothing needed fixing.

### T02 · Try Ask Belfort with a real key
- **Owner:** Devansh · **P0 · S · Status:** Ready · **Area:** assistant
- **Do:** Use a free Gemini key and, if possible, a local Ollama (`OpenAI-compatible`, base URL `http://localhost:11434/v1`). Ask about a report, a lesson and a news story ("Explain this"). Try a wrong key and no internet.
- **Done when:** All three contexts work with at least one provider, every error message tells the user what to do, and anything broken is fixed in this PR or filed as a new task.

## Phase 1: Practice (the paper trading upgrade)

The paper account works but is hard to use: you must already know the NSE symbol, the form gives no price or chart, and sizing happens on another screen. Fix that first.

### T03 · Fuzzy stock picker everywhere
- **Owner:** Devansh · **P0 · M · Status:** Ready · **Area:** data, ui
- **Why:** Nobody should have to look up an NSE symbol. Typing "hd" must show HDFC Bank, HDFC Life and HDFC AMC.
- **Backend:** Upgrade `NseArchiveProvider.search` (`belfort/data/providers.py`) or move it to `belfort/data/symbols.py`:
  - Match on symbol prefix, word prefixes of the company name, initials, and typo tolerance (stdlib `difflib`, or `rapidfuzz` if you add it as a pinned dependency).
  - A small alias table for names people actually use (`sbi` → SBIN, `jio` → JIOFIN, `l&t` → LT, `infy`/`infosys` → INFY, `m&m`/`mahindra` → M&M); keep it in `content/` or `belfort/data/` as data, not code.
  - Rank exact symbol, then prefix, then large caps first, then fuzzy matches. Return `symbol`, `name`, `sector` and, when cached, `last_close` and `as_of`.
  - Fall back to the built-in universe when the NSE listing file cannot be fetched.
  - Under 30 ms for the full listing (about 2,300 companies) after warm-up.
- **Front end:** A reusable `belfort/static/stock-picker.js` attached to any input with `data-stock-picker`. Dropdown from the first character, keyboard navigation (up, down, Enter, Escape), name and symbol and last price in each row, recent picks when the field is empty. The visible field shows the company name; the form submits the symbol. Use it in the sidebar search, the paper order form, the prediction form, and later watchlists (T26).
- **Tests:** A fixture listing; cases for `hd`, `hdfc bank`, `hdcf bank` (typo), `reliance`, `jio`, `sbi`, `l&t`, an empty query, and a symbol that does not exist.
- **Done when:** You can place a paper trade and log a prediction without ever typing a symbol, in the running app.

### T04 · Trade ticket: quote, mini chart, position-size helper
- **Owner:** Devansh · **P0 · M · Status:** Blocked on T03 · **Area:** practice, ui
- **Do:** When a stock is picked in the order form, show last close and date, day change, a 3-month mini chart with the nearest support, and a suggested stop. Add "Size it": a risk % field that fills the quantity with `floor(account value × risk % ÷ (entry − stop))`, reusing `belfort/research/analysis/sizing.py` through `GET /api/practice/size`. Show the rupee risk and the share of the account it uses before the order is placed.
- **Done when:** Tests cover the endpoint (never risks more than the limit, capped by available points); the ticket works in the app.

### T05 · Faster portfolio: bar cache and daily settlement
- **P1 · M · Status:** Ready · **Area:** practice, data
- **Why:** Every portfolio load fetches bars for every open symbol.
- **Do:** Cache daily bars per symbol until the next market close; settle at most once per new trading day; store last settled date. Do not change the rules in `belfort/practice/engine.py`.
- **Done when:** With 20 open symbols the portfolio loads in under a second on the second visit; tests cover cache expiry and the once-per-day settlement.

### T06 · Replay: keep hidden bars on the server
- **P1 · M · Status:** Ready · **Area:** practice
- **Do:** Store replay sessions server-side (id, symbol, window). `/replay/new` returns only the visible bars and an id; `/replay/score` takes the id and the plan and returns the rest.
- **Done when:** No response contains hidden bars before the decision; tests prove it.

### T07 · Trailing stops and partial exits
- **P1 · M · Status:** Ready · **Area:** practice
- **Do:** Let the user raise a stop (never lower it, per the lesson), add an optional trailing stop (percentage or ATR multiple, ratcheting on closes), and sell part of a position. Extend `engine.py` with pure functions and full tests; add a migration.
- **Done when:** Settlement rules for trailing and partial exits are documented in the engine docstring and covered by tests.

### T08 · Journal analytics
- **P1 · M · Status:** Ready · **Area:** practice
- **Do:** Mistake tags on closed trades (moved stop, no plan, chased, sized too big, exited early), R distribution chart, results by setup tag and by holding time, and best and worst habits.
- **Done when:** Analytics come from a tested pure module; the review screen shows them.

### T09 · Total open risk and size warnings
- **P1 · S · Status:** Ready · **Area:** practice
- **Do:** Show total rupee risk across open positions (sum of distance to stop × quantity) as a share of the account, and warn on an order that pushes it above a threshold in `settings.py` or risks over 2% on one trade.

### T10 · Export and import the journal
- **P2 · S · Status:** Ready · **Area:** practice
- **Do:** Download trades, predictions and replays as CSV and as one JSON backup; import the JSON backup with validation.

### T11 · Equity curve
- **P2 · M · Status:** Blocked on T05 · **Area:** practice
- **Do:** Snapshot account value each settled day; draw the curve and the largest drawdown.

## Phase 2: Learn (finish the syllabus)

Write lessons in module order. Each lesson: 5 to 8 minutes, objectives, a `::chart` where a chart helps, a `::try`, and at least three quiz questions. Follow [docs/SYLLABUS.md](../docs/SYLLABUS.md). Use `content(learn): ...` commit types.

### T12 · Content checker in CI
- **P0 · S · Status:** Ready · **Area:** learn, ci
- **Do:** `scripts/ci/check_content.py`: front matter present, quiz has 3+ valid questions, every `::chart` symbol exists in the listing fixture, every syllabus lesson not marked planned has a file and vice versa, banned wording absent, reading time roughly matches `minutes`. Add a CI step. Code-owned path: request Sarthak's review.
- **Done when:** CI fails on a deliberately broken lesson and passes on main.

### T13 · Lessons: market hours and circuits, moving averages, volume
- **P1 · M · Status:** Ready · Lesson ids: `circuits-and-sessions`, `moving-averages`, `volume`. Check NSE session times and circuit rules at the source and cite them.

### T14 · Lessons: R multiples, losing streaks
- **P1 · M · Status:** Ready · Lesson ids: `r-multiples`, `risk-of-ruin`. Tie them to the Practice stats (average R, win rate).

### T15 · Lessons: Setups module
- **P1 · L · Status:** Ready · `pullback-setup`, `breakout-setup`, `exits`, `results-season`.

### T16 · Lessons: Business check module
- **P1 · M · Status:** Ready · `five-numbers`, `pe-vs-peers`, `red-flags`. Match the figures the Research business section shows.

### T17 · Lessons: Indicators and patterns module
- **P1 · M · Status:** Ready · `atr`, `rsi-macd`, `pattern-evidence` (use the backtest figures from `data/pattern_stats.json`).

### T18 · Lessons: Journal module
- **P1 · M · Status:** Ready · `trade-journal`, `expectancy`, `calibration`. Point at the Practice journal and prediction scores.

### T19 · Lessons: Market context module
- **P1 · M · Status:** Ready · `index-trend`, `sectors`, `flows-and-events`.

### T20 · Lessons: Portfolio and Psychology modules
- **P1 · M · Status:** Ready · `open-risk`, `drawdown-rules`, `biases`, `rules`.

### T21 · Lessons: Taxes and records module
- **P1 · M · Status:** Ready · `capital-gains`, `records`. Rates change every Budget: describe the rules, cite the current official source and date, and request Sarthak's review.

### T22 · Lessons: Safety module
- **P1 · M · Status:** Ready · `tip-scams`, `check-registration` (how to verify a SEBI registration and file a complaint, with official links), `myths`.

### T23 · Replay drills inside lessons
- **P1 · M · Status:** Ready · **Area:** learn, practice
- **Do:** A `::drill KIND` directive (for example `support`, `stop`, `trend`) that opens a replay chart inside the lesson with a specific question ("Where would the stop go?") and checks the answer against the engine's levels. Lagged data only.

### T24 · Module checkpoints and progress summary
- **P2 · S · Status:** Ready · A short mixed quiz at the end of each module; a progress page per track.

## Phase 3: Research and News

### T25 · Editable rule profiles
- **P1 · L · Status:** Blocked on D1 (pricing decides how much of Research we keep) · **Area:** research
- **Do:** Read rule thresholds from `%LOCALAPPDATA%\Belfort\rules.json` with defaults from `settings.py`; a settings screen to edit them with validation; show the active profile in every report.

### T26 · Watchlists and in-app alerts
- **P1 · M · Status:** Blocked on T03 · **Area:** research
- **Do:** Named watchlists (uses the stock picker), refreshed at end of day, with in-app notices when a rule condition changes ("TCS: all conditions now met"). Alerts stay inside the app: no email, Telegram or push (see COMPLIANCE.md).

### T27 · Market context panel
- **P2 · M · Status:** Ready · Nifty 50 trend under the same rule, breadth (share of the built-in universe above its 50-day average), and sector strength, on the Research home.

### T28 · News: tag every NSE company
- **P1 · M · Status:** Blocked on T03 · Reuse the picker's alias index for tagging; tests for false positives (common words, short names); manual check of 50 real headlines in the PR.

### T29 · News: NSE announcements and events calendar
- **P2 · L · Status:** Ready · Corporate announcements and results dates from NSE public files (best effort, shown as missing when blocked) and RBI policy dates; a calendar view.

### T30 · A stock's news inside its report
- **P2 · S · Status:** Blocked on T28 · A "News" folder in the dossier listing tagged stories for the symbol.

## Phase 4: Quality

### T31 · Browser end-to-end tests in CI
- **P0 · M · Status:** Ready · **Area:** ci
- **Do:** Playwright (Python) tests against the app with all network sources faked: open a report, pass a quiz, pick a stock and place a paper trade, log a prediction, play a replay, filter news. Run on `windows-latest` in CI. Code-owned path: request Sarthak's review.

### T32 · Accessibility and small-window pass
- **P1 · M · Status:** Ready · Keyboard-only use of every screen, visible focus, labels on every control, contrast, and layouts at 1024×700 and 1366×768 (the smallest window sizes people use on laptops). Screenshots in the PR.

### T33 · Error handling, logging and a friendly error screen
- **P1 · M · Status:** Ready · Structured logs to the user data folder with rotation, a clear screen when the backend or data source fails, and a "Copy details" button for bug reports. No telemetry.

### T34 · Gradual type checking with mypy
- **P2 · M · Status:** Ready · Add mypy to CI for `belfort/practice`, `belfort/learn` and `belfort/core` first; widen over time.

## Phase 5: ship the Windows app

### T35 · Per-user data folder
- **P0 · M · Status:** Ready · **Area:** core, installer
- **Why:** An installed app cannot write next to its program files.
- **Do:** Default data, cache, logs and WebView storage to `%LOCALAPPDATA%\Belfort` (keep `BELFORT_DATA_DIR` as an override); move an existing `./data` on first run; tests for the path logic.

### T36 · Consolidate into one entry point
- **P0 · M · Status:** Ready · **Area:** platform
- **Do:** `python -m belfort` starts the server on a free local port and opens the window (replaces `run_desktop.py` and `run.bat` logic); single-instance lock so a second launch focuses the open window; version from one source; graceful shutdown; remove leftovers from the Belfort AI launcher.

### T37 · Bundle fonts and the chart library
- **P0 · S · Status:** Ready · Serve Instrument Serif, Inter and lightweight-charts from `belfort/static/vendor/` instead of CDNs, with their licence files, so the installed app works without those sites.

### T38 · Windows build and installer
- **P0 · L · Status:** Blocked on T35, T36, T37 · **Area:** installer
- **Do:** PyInstaller (one-folder build) driven by a checked-in spec, wrapped in an Inno Setup installer: Start menu and optional desktop shortcut with the Belfort icon, per-user install without admin rights, uninstaller that offers to keep user data, WebView2 runtime check with the Microsoft bootstrapper when missing, version and publisher metadata. A `scripts/build_windows.ps1` that produces `dist/Belfort-Setup-<version>.exe` locally.
- **Done when:** The installer runs on a clean Windows 10 and Windows 11 machine (or VM), the app starts offline-first, and the uninstaller works. Report size and start time in the PR.

### T39 · Release workflow
- **P0 · M · Status:** Blocked on T38 · **Area:** ci · Code-owned: request Sarthak's review.
- **Do:** `.github/workflows/release.yml` on tags `v*.*.*`: run the full CI, build the installer on `windows-latest`, install it silently, start it and check `/api/config` answers, compute SHA-256, and attach the installer and checksum to a **draft** GitHub Release with the CHANGELOG section as notes. Code signing step left ready for D7.

### T40 · Ship Belfort 1.0 for Windows
- **P0 · L · Status:** Blocked on all P0 and P1 tasks
- **Do:** Final consolidation pass: remove dead code and temporary files (including this `TEAM/` folder, moving anything worth keeping into `docs/`), make README "What is built" true, update ARCHITECTURE and COMPLIANCE, full manual regression on a clean Windows machine using the installer, bump to 1.0.0, CHANGELOG, tag `v1.0.0`, and publish the release once D1, D3, D6 and D7 are settled.
- **Done when:** Anyone with the download link can install and use Belfort on Windows without Python.

### T41 · Apply the brand decision
- **P1 · S · Status:** Blocked on D2 · Rename the wordmark, window title, installer name and icon to whatever D2 decides.

## Decisions (Sarthak and Devansh, not code)

| ID | Decision | Why it matters | Blocks | Status |
|---|---|---|---|---|
| D1 | Pricing and licence | Charging for per-stock Research labels may need SEBI research-analyst registration (docs/COMPLIANCE.md). Free, paid, or paid only for Learn and Practice? | T25, T40 | Open |
| D2 | Name and brand | The sidebar still says "Belfort AI". Keep, drop "AI", or rename? | T41 | Open |
| D3 | Securities lawyer review | Before any outside user sees it | T40 | Open |
| D4 | Licensed data | Yahoo and NSE archive data are unofficial; a paid product needs a licensed feed or user-keyed broker data | T40 if paid | Open |
| D5 | Ownership and roles | Founders' agreement, who owns what | | Open |
| D6 | Where users download | Releases on a private repo cannot be downloaded by the public: a public releases repo, a website, or a store? | T40 | Open |
| D7 | Code signing | Unsigned installers trigger Windows SmartScreen warnings; a certificate costs money each year | T39, T40 | Open |

## Done

- v0.1 foundation (see README "What is built").
- Production engineering setup: lint, format, coverage, pinned dependencies, CI on Windows and Linux, commit policy, conventions (PR #1).
