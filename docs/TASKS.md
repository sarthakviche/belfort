# Tasks: from v0.1 to Belfort 1.0 for Windows

> The public task board. Anyone can pick a `Ready` task: comment on its issue (or open one titled with the task id) to claim it, then follow [CONTRIBUTING.md](../CONTRIBUTING.md). When you start, set Owner and Status in your first commit; when it merges, set Status to Done with the PR link.
>
> Work roughly in phase order. Inside a phase, any `Ready` task can go next. Every task follows the flow in [CONTRIBUTING.md](../CONTRIBUTING.md) and the definition of done in [CLAUDE.md](../CLAUDE.md).

**Priority:** P0 do first · P1 needed for 1.0 · P2 nice for 1.0 · P3 after 1.0
**Size:** S under half a day · M one to two days · L three days or more
**Status:** `Ready` · `Blocked` (on a named task or decision) · `In progress` · `Done`

## Overview

| ID | Task | Phase | P | Size | Status |
|---|---|---|---|---|---|
| T01 | Run Belfort and fix setup docs | 0 Onboarding | P0 | S | Done ([#7](https://github.com/sarthakviche/belfort/pull/7)) |
| T02 | Try Ask Belfort with a real key | 0 Onboarding | P0 | S | Done ([#8](https://github.com/sarthakviche/belfort/pull/8)) |
| T03 | Fuzzy stock picker everywhere | 1 Practice | P0 | M | Done ([#9](https://github.com/sarthakviche/belfort/pull/9)) |
| T04 | Trade ticket: quote, mini chart, position-size helper | 1 Practice | P0 | M | Done ([#10](https://github.com/sarthakviche/belfort/pull/10)) |
| T05 | Faster portfolio: bar cache and daily settlement | 1 Practice | P1 | M | Done ([#11](https://github.com/sarthakviche/belfort/pull/11)) |
| T06 | Replay: keep hidden bars on the server | 1 Practice | P1 | M | Done ([#12](https://github.com/sarthakviche/belfort/pull/12)) |
| T07 | Trailing stops and partial exits | 1 Practice | P1 | M | Done ([#13](https://github.com/sarthakviche/belfort/pull/13)) |
| T08 | Journal analytics | 1 Practice | P1 | M | Done ([#15](https://github.com/sarthakviche/belfort/pull/15)) |
| T09 | Total open risk and size warnings | 1 Practice | P1 | S | Done ([#14](https://github.com/sarthakviche/belfort/pull/14)) |
| T10 | Export and import the journal | 1 Practice | P2 | S | Done ([#16](https://github.com/sarthakviche/belfort/pull/16)) |
| T11 | Equity curve | 1 Practice | P2 | M | Done ([#18](https://github.com/sarthakviche/belfort/pull/18)) |
| T12 | Content checker in CI | 2 Learn | P0 | S | Ready |
| T13 | Lessons: sessions, moving averages, volume | 2 Learn | P1 | M | Done ([#20](https://github.com/sarthakviche/belfort/pull/20)) |
| T14 | Lessons: R multiples, losing streaks | 2 Learn | P1 | M | Done ([#21](https://github.com/sarthakviche/belfort/pull/21)) |
| T15 | Lessons: Setups module (4) | 2 Learn | P1 | L | Done ([#22](https://github.com/sarthakviche/belfort/pull/22)) |
| T16 | Lessons: Business check module (3) | 2 Learn | P1 | M | Done ([#23](https://github.com/sarthakviche/belfort/pull/23)) |
| T17 | Lessons: Indicators and patterns module (3) | 2 Learn | P1 | M | Done ([#24](https://github.com/sarthakviche/belfort/pull/24)) |
| T18 | Lessons: Journal module (3) | 2 Learn | P1 | M | Done ([#25](https://github.com/sarthakviche/belfort/pull/25)) |
| T19 | Lessons: Market context module (3) | 2 Learn | P1 | M | Done ([#26](https://github.com/sarthakviche/belfort/pull/26)) |
| T20 | Lessons: Portfolio and Psychology modules (4) | 2 Learn | P1 | M | Done ([#27](https://github.com/sarthakviche/belfort/pull/27)) |
| T21 | Lessons: Taxes and records module (2) | 2 Learn | P1 | M | Done ([#35](https://github.com/sarthakviche/belfort/pull/35)) |
| T22 | Lessons: Safety module (3) | 2 Learn | P1 | M | Done ([#36](https://github.com/sarthakviche/belfort/pull/36)) |
| T23 | Replay drills inside lessons | 2 Learn | P1 | M | Ready |
| T24 | Module checkpoints and progress summary | 2 Learn | P2 | S | Superseded by T42 |
| T25 | Editable rule profiles | 3 Research and News | P1 | L | Blocked on D1 |
| T26 | Watchlists and in-app alerts | 3 Research and News | P1 | M | Ready |
| T27 | Market context panel | 3 Research and News | P2 | M | Ready |
| T28 | News: tag every NSE company | 3 Research and News | P1 | M | Ready |
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
| T42 | Gamified Learn: stages, locks, XP, streaks, hearts | 6 Belfort 2 | P0 | L | Done ([#37](https://github.com/sarthakviche/belfort/pull/37)) |
| T43 | Accounts and sync across devices | 6 Belfort 2 | P0 | L | In progress (Devansh) |
| T44 | Tip Check: is this stock tip a trap? | 6 Belfort 2 | P0 | L | In progress (Devansh) |
| T45 | Dictionary search with an Ask and web fallback | 6 Belfort 2 | P1 | S | Done ([#33](https://github.com/sarthakviche/belfort/pull/33)) |
| T46 | Startup loader and intro with the mascot | 6 Belfort 2 | P0 | M | Done ([#32](https://github.com/sarthakviche/belfort/pull/32)) |
| T47 | Landing site rebuild | 6 Belfort 2 | P1 | M | In progress |
| T48 | Belfort for Android | 6 Belfort 2 | P0 | L | In progress (Devansh) |
| T49 | New exercise types in every lesson | 6 Belfort 2 | P1 | M | Done ([#38](https://github.com/sarthakviche/belfort/pull/38)) |
| T50 | Belfort in Indian languages | 6 Belfort 2 | P0 | L | Done ([#41](https://github.com/sarthakviche/belfort/pull/41)) |

---

## Phase 0: onboarding

### T01 · Run Belfort and fix setup docs
- **Owner:** Devansh · **P0 · S · Status:** Done ([#7](https://github.com/sarthakviche/belfort/pull/7)) · **Area:** platform
- **Do:** Follow the setup in CONTRIBUTING.md on a clean clone. Fix anything wrong or unclear in it, README.md or CLAUDE.md.
- **Done when:** Merged PR `docs: fix onboarding steps (T01)`, or a PR that only marks the task Done if nothing needed fixing.

### T02 · Try Ask Belfort with a real key
- **Owner:** Devansh · **P0 · S · Status:** Done ([#8](https://github.com/sarthakviche/belfort/pull/8)) · **Area:** assistant
- **Do:** Use a free Gemini key and, if possible, a local Ollama (`OpenAI-compatible`, base URL `http://localhost:11434/v1`). Ask about a report, a lesson and a news story ("Explain this"). Try a wrong key and no internet.
- **Done when:** All three contexts work with at least one provider, every error message tells the user what to do, and anything broken is fixed in this PR or filed as a new task.

## Phase 1: Practice (the paper trading upgrade)

The paper account works but is hard to use: you must already know the NSE symbol, the form gives no price or chart, and sizing happens on another screen. Fix that first.

### T03 · Fuzzy stock picker everywhere
- **Owner:** Devansh · **P0 · M · Status:** Done ([#9](https://github.com/sarthakviche/belfort/pull/9)) · **Area:** data, ui
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
- **Owner:** Devansh · **P0 · M · Status:** Done ([#10](https://github.com/sarthakviche/belfort/pull/10)) · **Area:** practice, ui
- **Do:** When a stock is picked in the order form, show last close and date, day change, a 3-month mini chart with the nearest support, and a suggested stop. Add "Size it": a risk % field that fills the quantity with `floor(account value × risk % ÷ (entry − stop))`, reusing `belfort/research/analysis/sizing.py` through `GET /api/practice/size`. Show the rupee risk and the share of the account it uses before the order is placed.
- **Done when:** Tests cover the endpoint (never risks more than the limit, capped by available points); the ticket works in the app.

### T05 · Faster portfolio: bar cache and daily settlement
- **Owner:** Devansh · **P1 · M · Status:** Done ([#11](https://github.com/sarthakviche/belfort/pull/11)) · **Area:** practice, data
- **Why:** Every portfolio load fetches bars for every open symbol.
- **Do:** Cache daily bars per symbol until the next market close; settle at most once per new trading day; store last settled date. Do not change the rules in `belfort/practice/engine.py`.
- **Done when:** With 20 open symbols the portfolio loads in under a second on the second visit; tests cover cache expiry and the once-per-day settlement.

### T06 · Replay: keep hidden bars on the server
- **Owner:** Devansh · **P1 · M · Status:** Done ([#12](https://github.com/sarthakviche/belfort/pull/12)) · **Area:** practice
- **Do:** Store replay sessions server-side (id, symbol, window). `/replay/new` returns only the visible bars and an id; `/replay/score` takes the id and the plan and returns the rest.
- **Done when:** No response contains hidden bars before the decision; tests prove it.

### T07 · Trailing stops and partial exits
- **Owner:** Devansh · **P1 · M · Status:** Done ([#13](https://github.com/sarthakviche/belfort/pull/13)) · **Area:** practice
- **Do:** Let the user raise a stop (never lower it, per the lesson), add an optional trailing stop (percentage or ATR multiple, ratcheting on closes), and sell part of a position. Extend `engine.py` with pure functions and full tests; add a migration.
- **Done when:** Settlement rules for trailing and partial exits are documented in the engine docstring and covered by tests.

### T08 · Journal analytics
- **Owner:** Devansh · **P1 · M · Status:** Done ([#15](https://github.com/sarthakviche/belfort/pull/15)) · **Area:** practice
- **Do:** Mistake tags on closed trades (moved stop, no plan, chased, sized too big, exited early), R distribution chart, results by setup tag and by holding time, and best and worst habits.
- **Done when:** Analytics come from a tested pure module; the review screen shows them.

### T09 · Total open risk and size warnings
- **Owner:** Devansh · **P1 · S · Status:** Done ([#14](https://github.com/sarthakviche/belfort/pull/14)) · **Area:** practice
- **Do:** Show total rupee risk across open positions (sum of distance to stop × quantity) as a share of the account, and warn on an order that pushes it above a threshold in `settings.py` or risks over 2% on one trade.

### T10 · Export and import the journal
- **Owner:** Devansh · **P2 · S · Status:** Done ([#16](https://github.com/sarthakviche/belfort/pull/16)) · **Area:** practice
- **Do:** Download trades, predictions and replays as CSV and as one JSON backup; import the JSON backup with validation.

### T11 · Equity curve
- **Owner:** Devansh · **P2 · M · Status:** Done ([#18](https://github.com/sarthakviche/belfort/pull/18)) · **Area:** practice
- **Do:** Snapshot account value each settled day; draw the curve and the largest drawdown.

## Phase 2: Learn (finish the syllabus)

Write lessons in module order. Each lesson: 5 to 8 minutes, objectives, a `::chart` where a chart helps, a `::try`, and at least three quiz questions. Follow [docs/SYLLABUS.md](../docs/SYLLABUS.md). Use `content(learn): ...` commit types.

### T12 · Content checker in CI
- **P0 · S · Status:** Ready · **Area:** learn, ci
- **Do:** `scripts/ci/check_content.py`: front matter present, quiz has 3+ valid questions, every `::chart` symbol exists in the listing fixture, every syllabus lesson not marked planned has a file and vice versa, banned wording absent, reading time roughly matches `minutes`. Add a CI step. Code-owned path: request Sarthak's review.
- **Done when:** CI fails on a deliberately broken lesson and passes on main.

### T13 · Lessons: market hours and circuits, moving averages, volume
- **Owner:** Devansh · **P1 · M · Status:** Done ([#20](https://github.com/sarthakviche/belfort/pull/20)) · Lesson ids: `circuits-and-sessions`, `moving-averages`, `volume`. Check NSE session times and circuit rules at the source and cite them.

### T14 · Lessons: R multiples, losing streaks
- **Owner:** Devansh · **P1 · M · Status:** Done ([#21](https://github.com/sarthakviche/belfort/pull/21)) · Lesson ids: `r-multiples`, `risk-of-ruin`. Tie them to the Practice stats (average R, win rate).

### T15 · Lessons: Setups module
- **Owner:** Devansh · **P1 · L · Status:** Done ([#22](https://github.com/sarthakviche/belfort/pull/22)) · `pullback-setup`, `breakout-setup`, `exits`, `results-season`.

### T16 · Lessons: Business check module
- **Owner:** Devansh · **P1 · M · Status:** Done ([#23](https://github.com/sarthakviche/belfort/pull/23)) · `five-numbers`, `pe-vs-peers`, `red-flags`. Match the figures the Research business section shows.

### T17 · Lessons: Indicators and patterns module
- **Owner:** Devansh · **P1 · M · Status:** Done ([#24](https://github.com/sarthakviche/belfort/pull/24)) · `atr`, `rsi-macd`, `pattern-evidence` (use the backtest figures from `data/pattern_stats.json`).

### T18 · Lessons: Journal module
- **Owner:** Devansh · **P1 · M · Status:** Done ([#25](https://github.com/sarthakviche/belfort/pull/25)) · `trade-journal`, `expectancy`, `calibration`. Point at the Practice journal and prediction scores.

### T19 · Lessons: Market context module
- **Owner:** Devansh · **P1 · M · Status:** Done ([#26](https://github.com/sarthakviche/belfort/pull/26)) · `index-trend`, `sectors`, `flows-and-events`.

### T20 · Lessons: Portfolio and Psychology modules
- **Owner:** Devansh · **P1 · M · Status:** Done ([#27](https://github.com/sarthakviche/belfort/pull/27)) · `open-risk`, `drawdown-rules`, `biases`, `rules`.

### T21 · Lessons: Taxes and records module
- **Owner:** Sarthak (agent) · **P1 · M · Status:** Done ([#35](https://github.com/sarthakviche/belfort/pull/35)) · `capital-gains`, `records`. Rates change every Budget: describe the rules, cite the current official source and date, and request Sarthak's review.

### T22 · Lessons: Safety module
- **Owner:** Sarthak (agent) · **P1 · M · Status:** Done ([#36](https://github.com/sarthakviche/belfort/pull/36)) · `tip-scams`, `check-registration` (how to verify a SEBI registration and file a complaint, with official links), `myths`.

### T23 · Replay drills inside lessons
- **P1 · M · Status:** Ready · **Area:** learn, practice
- **Do:** A `::drill KIND` directive (for example `support`, `stop`, `trend`) that opens a replay chart inside the lesson with a specific question ("Where would the stop go?") and checks the answer against the engine's levels. Lagged data only.

### T24 · Module checkpoints and progress summary
- **P2 · S · Status:** Superseded by [T42](#t42--gamified-learn-stages-locks-xp-streaks-hearts) · A short mixed quiz at the end of each module; a progress page per track. T42 adds a checkpoint node to every module and a stage test, and the path shows progress.

## Phase 3: Research and News

### T25 · Editable rule profiles
- **P1 · L · Status:** Blocked on D1 (pricing decides how much of Research we keep) · **Area:** research
- **Do:** Read rule thresholds from `%LOCALAPPDATA%\Belfort\rules.json` with defaults from `settings.py`; a settings screen to edit them with validation; show the active profile in every report.

### T26 · Watchlists and in-app alerts
- **P1 · M · Status:** Ready · **Area:** research
- **Do:** Named watchlists (uses the stock picker), refreshed at end of day, with in-app notices when a rule condition changes ("TCS: all conditions now met"). Alerts stay inside the app: no email, Telegram or push (see COMPLIANCE.md).

### T27 · Market context panel
- **P2 · M · Status:** Ready · Nifty 50 trend under the same rule, breadth (share of the built-in universe above its 50-day average), and sector strength, on the Research home.

### T28 · News: tag every NSE company
- **P1 · M · Status:** Ready · Reuse the picker's alias index for tagging; tests for false positives (common words, short names); manual check of 50 real headlines in the PR.

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
- **Do:** Final consolidation pass: remove dead code and temporary files, make README "What is built" true, update ARCHITECTURE and COMPLIANCE, full manual regression on a clean Windows machine using the installer, bump to 1.0.0, CHANGELOG, tag `v1.0.0`, and publish the release once D1, D3, D6 and D7 are settled.
- **Done when:** Anyone with the download link can install and use Belfort on Windows without Python.

### T41 · Apply the brand decision
- **P1 · S · Status:** Blocked on D2 · Rename the wordmark, window title, installer name and icon to whatever D2 decides.

## Phase 6: Belfort 2 (accounts, gamified Learn, mobile)

Decided by the maintainers on 2026-11-27 (see `CHANGES.md`): Belfort gets accounts so practice and learning follow the user between Windows and Android; Learn becomes a Duolingo-style path in three stages; the mascot (the headless suit with the yellow tie, `belfort/static/img/mascot/`) appears across the app. Every rule in [COMPLIANCE.md](COMPLIANCE.md) still holds: XP, gems and hearts are virtual, never redeemable, never bought.

Shared contracts every Phase 6 task uses:
- **Current user:** `belfort/core/users.py::current_user_id(request)`. It returns `"local"` until T43 replaces its body. Any new per-user table has a `user_id TEXT NOT NULL DEFAULT 'local'` column and every query filters on it.
- **Stages:** each module in `content/learn/syllabus.json` has `"stage": "beginner" | "intermediate" | "advanced"`. Beginner = Foundations plus Scams, tips and your rights. Intermediate = Practitioner plus Taxes and records. Advanced = Market context, Running several trades, Psychology.
- **Exercise types** in a lesson's `quiz` block: an item with no `type` (or `"type": "mc"`) keeps today's shape `{q, options, answer, why}`; `{"type": "tf", q, answer: true|false, why}`; `{"type": "order", q, items: [...in the correct order], why}` (shown shuffled); `{"type": "number", q, answer, tolerance, unit?, why}`.
- **New UI** goes in its own file under `belfort/static/` (for example `learn-game.js`, `auth.js`, `tipcheck.js`), with only a script tag and a nav hook added to `index.html` and `app.js`, so parallel branches do not collide.

### T42 · Gamified Learn: stages, locks, XP, streaks, hearts
- **Owner:** Sarthak · **P0 · L · Status:** Done ([#37](https://github.com/sarthakviche/belfort/pull/37)) · **Area:** learn, ui · Supersedes T24.
- **Path:** a vertical map per stage: one node per lesson, a checkpoint node at the end of each module and a stage test at the end of the stage. Next node pulses; done nodes show a crown when the quiz was perfect.
- **Locks:** a new user sees Beginner only. Intermediate and Advanced lessons show their title and a lock; their content and quiz are refused by the API (not only hidden in the page). A stage unlocks when its previous stage test is passed at 80% or more, or by passing the placement test (a 12-question mix from Beginner) on first open.
- **Lesson flow:** the lesson is split into cards at each `## ` heading, one card per screen, with an exercise after the cards. Wrong answers cost a heart (5 per day); hearts refill each day or by finishing a Weak spots review (questions the user got wrong before).
- **Rewards:** XP per lesson (10, +5 for no mistakes), a daily goal the user picks (10, 20 or 50 XP), a streak with one streak freeze earned per 7 days, the mascot reacting (cheer on correct, shrug on wrong), confetti on module and stage completion. Respect `prefers-reduced-motion`.
- **Done when:** the engine (XP, streak, hearts, unlocks) is a pure tested module; the API refuses locked content; the path, lesson cards and all four exercise types work in the running app.

### T43 · Accounts and sync across devices
- **Owner:** Devansh · **P0 · L · Status:** In progress · **Area:** platform
- **Decision:** Supabase Auth (email and password, and Google) with a Postgres table `user_state (user_id, kind, payload jsonb, updated_at)` protected by row-level security. Desktop and Android sign in to the same project. The paper account, journal, predictions, replays and Learn progress sync as whole JSON documents per kind (reusing the T10 backup format), last write wins by `updated_at`.
- **Do:** a sign-in screen (email, password, Google, "continue without an account" keeps today's local mode), `current_user_id` returns the signed-in user, the local SQLite rows are scoped by `user_id`, sync on sign-in, on change (debounced) and on app close. Configuration from `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`; with neither set the app runs local-only. Ship the SQL (table, RLS policies) in `supabase/migrations/`.
- **Done when:** tests (with the Supabase HTTP calls faked) cover sign-in, token refresh, scoping and both sync directions; a user who signs in on a second machine sees the same paper account.

### T44 · Tip Check: is this stock tip a trap?
- **Owner:** Devansh · **P0 · L · Status:** In progress · **Area:** research, assistant · The hackathon hook.
- **What:** paste or screenshot a stock tip from WhatsApp, Telegram or Instagram, in English, Hindi or Hinglish (most tips arrive in Hinglish). Belfort reads it and shows, in about ten seconds, the red flags it found: is the sender a SEBI-registered adviser or research analyst; does the tip promise returns or a target in days (SEBI forbids guaranteed returns); urgency and secrecy language; is the stock in NSE's ASM or GSM surveillance lists; does its recent price and volume look like a pump (volume many times its 50-day average, a sharp run-up, a small company); what happened to the stock the last time it looked like this. It ends with what to do (check the registration yourself on SEBI's site, report on SEBI SCORES) and links to the Safety lessons.
- **Compliance:** it never says a stock is good, safe, a buy or a sell. It reports red flags found and not found, and says Belfort cannot tell whether a trade will work.
- **Done when:** text works offline with rules; a screenshot works with the user's own assistant key (vision); every check is a pure tested function with fixtures for the SEBI registers and the surveillance lists; it works in the running app.

### T45 · Dictionary search with an Ask and web fallback
- **Owner:** Sarthak · **P1 · S · Status:** Done ([#33](https://github.com/sarthakviche/belfort/pull/33)) · **Area:** ui, assistant
- **Do:** a search box over the glossary (fuzzy, by term and match phrases). When nothing matches, show the mascot shrugging and two choices: "Ask Belfort" (a short, plain explanation from the user's assistant key, labelled as AI and checked by the compliance filter) and "Search the web" (opens the default browser on a web search for the term plus "stock market").
- **Done when:** tests cover matching and the fallback; it works in the running app with and without a key.

### T46 · Startup loader and intro with the mascot
- **Owner:** Sarthak · **P0 · M · Status:** Done ([#32](https://github.com/sarthakviche/belfort/pull/32)) · **Area:** ui, platform
- **Do:** a loader that shows while the Windows app starts its server: black screen, a few candles draw in one by one, then the mascot settles in the centre and the Belfort wordmark fades in. Under 2.5 seconds, nothing else on screen. Then, on the first open only, a one-screen intro with the quote "Risk comes from not knowing what you're doing." (Warren Buffett) in a large serif, and a start button. The quote lives in one constant so it is easy to change. Respect `prefers-reduced-motion`.
- **Done when:** the Windows app shows the loader from launch until the UI is ready and the intro on first open.

### T47 · Landing site rebuild
- **Owner:** Sarthak · **P1 · M · Status:** In progress · **Area:** site
- **Do:** rebuild `site/index.html` on top of the current landing page: a moving candlestick background (canvas, replaceable by a video file) under a black layer at about 60% opacity, the mascot, the quote, Tip Check as the lead feature, the gamified path, download and Android sections.

### T48 · Belfort for Android
- **Owner:** Devansh · **P0 · L · Status:** In progress · **Area:** mobile · Built on Devansh's machine (Android SDK).
- **Do:** a native Android app named Belfort with every part of the desktop app in a mobile-first interface, the same mascot, loader and animations, the same account (T43). Coordinated in `conversations.md` on the `collab` branch.

### T49 · New exercise types in every lesson
- **P1 · M · Owner:** Sarthak (agent) · **Status:** Done ([#38](https://github.com/sarthakviche/belfort/pull/38)) · **Area:** learn
- **Do:** add at least two exercises of the new types (tf, order, number) to every lesson, keeping the existing questions. Facts must match the lesson text.
- **Result:** 97 new items across all 38 lessons: 45 number, 41 true/false, 11 order. Every lesson has at least two items of at least two types. `tests/test_learn_exercises.py` keeps it that way.

### T50 · Belfort in Indian languages
- **P0 · L · Owner:** Sarthak (agent) · **Status:** Done ([#41](https://github.com/sarthakviche/belfort/pull/41)) · **Area:** ui, learn, assistant
- English stays the default. Language picker on the intro, in Settings and in the header: English, हिन्दी, मराठी, বাংলা, தமிழ், తెలుగు, ગુજરાતી, ಕನ್ನಡ. Catalogues in `belfort/static/i18n/<lang>.json` (shared with Android), English as the fallback; Beginner lessons in Hindi; Ask Belfort and the dictionary answer in the chosen language; Indian number grouping everywhere. Machine drafts: a fluent speaker must read them before release. See `docs/ARCHITECTURE.md` ("Languages").

## Decisions (maintainers, not code)

| ID | Decision | Why it matters | Blocks | Status |
|---|---|---|---|---|
| D1 | Pricing and licence | Charging for per-stock Research labels may need SEBI research-analyst registration (docs/COMPLIANCE.md). Free, paid, or paid only for Learn and Practice? | T25, T40 | Open |
| D2 | Name and brand | The sidebar still says "Belfort AI". Keep, drop "AI", or rename? | T41 | Open |
| D3 | Securities lawyer review | Before any outside user sees it | T40 | Open |
| D4 | Licensed data | Yahoo and NSE archive data are unofficial; a paid product needs a licensed feed or user-keyed broker data | T40 if paid | Open |
| D5 | Ownership and roles | Founders' agreement, who owns what | | Open |
| D6 | Where users download | GitHub Releases on this repo once it is public, or also a website or store? | T40 | Open |
| D7 | Code signing | Unsigned installers trigger Windows SmartScreen warnings; a certificate costs money each year | T39, T40 | Open |

## Done

- T42 Gamified Learn: stage path, locks, cards, four exercise types, XP, streaks, hearts ([#37](https://github.com/sarthakviche/belfort/pull/37)).
- v0.1 foundation (see README "What is built").
- Production engineering setup: lint, format, coverage, pinned dependencies, CI on Windows and Linux, commit policy, conventions (PR #1).
- T01 Onboarding steps checked on a clean clone and fixed ([#7](https://github.com/sarthakviche/belfort/pull/7)).
- T03 Fuzzy stock picker in search, paper orders and predictions ([#9](https://github.com/sarthakviche/belfort/pull/9)).
- T04 Order ticket with quote, mini chart, stop idea and sizing ([#10](https://github.com/sarthakviche/belfort/pull/10)).
- T05 Bar cache until the next end-of-day release; settlement once per trading day ([#11](https://github.com/sarthakviche/belfort/pull/11)).
- T06 Replay hidden bars kept on the server; reveal date fixed ([#12](https://github.com/sarthakviche/belfort/pull/12)).
- T07 Raised stops, trailing stops and partial exits ([#13](https://github.com/sarthakviche/belfort/pull/13)).
- T08 Journal analytics with setup and mistake tags ([#15](https://github.com/sarthakviche/belfort/pull/15)).
- T09 Total open risk and size warnings ([#14](https://github.com/sarthakviche/belfort/pull/14)).
- T10 Journal export (CSV, JSON) and backup restore ([#16](https://github.com/sarthakviche/belfort/pull/16)).
- T11 Equity curve with largest drawdown ([#18](https://github.com/sarthakviche/belfort/pull/18)).
- T13 Lessons: market hours and circuits, moving averages, volume ([#20](https://github.com/sarthakviche/belfort/pull/20)).
- T14 Lessons: R multiples, losing streaks and risk of ruin ([#21](https://github.com/sarthakviche/belfort/pull/21)).
- T15 Lessons: Setups module, pullbacks, breakouts, exits and results dates ([#22](https://github.com/sarthakviche/belfort/pull/22)).
- T16 Lessons: Business check module, five numbers, P/E against peers and red flags ([#23](https://github.com/sarthakviche/belfort/pull/23)).
- T17 Lessons: Indicators and patterns module, ATR, RSI and MACD, pattern evidence ([#24](https://github.com/sarthakviche/belfort/pull/24)).
- T18 Lessons: Journal module, trade journal, expectancy and calibration ([#25](https://github.com/sarthakviche/belfort/pull/25)).
- T19 Lessons: Market context module, index trend and breadth, sectors, flows and events ([#26](https://github.com/sarthakviche/belfort/pull/26)).
- T20 Lessons: Portfolio and Psychology modules, open risk, drawdown rules, biases and rules ([#27](https://github.com/sarthakviche/belfort/pull/27)).
- T21 Lessons: Taxes and records module, capital gains on shares, records and filing ([#35](https://github.com/sarthakviche/belfort/pull/35)).
- T22 Lessons: Safety module, tip scams, checking registration, myths ([#36](https://github.com/sarthakviche/belfort/pull/36)).
