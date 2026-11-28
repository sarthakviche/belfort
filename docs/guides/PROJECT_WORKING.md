# How Belfort works

This guide explains what happens behind the scenes, step by step, and why it was built that way. For a map of where each file is, see `CODEBASE_OVERVIEW.md`. Code is quoted only as evidence, with `file:line` references.

## 1. The problem

Many new Indian retail traders learn from Telegram and WhatsApp "tip" groups. Those groups promise sure-shot returns and push small stocks so the people running them can sell into the buying. SEBI has acted against several such groups. A beginner needs four things: a way to look at a stock without being told what to do, a safe place to practise, plain lessons, and a quick way to see that a tip is a trap.

This is hard because of the rules. In India, a tool that gives per-stock buy or sell calls for money falls under SEBI's research-analyst rules, and learning content may not use live prices for named stocks. So Belfort has to be useful without ever advising, predicting or promising.

## 2. The big idea

Belfort runs entirely on your own computer as one small Python web server, with a plain web page as its interface. Every judgement it makes comes from fixed, written rules over numbers it computes itself. The same data always gives the same answer, and every answer shows its source and date. Labels say whether a rule's conditions are met ("Conditions met", "Partly met", "Rule excludes"), never "buy" or "sell". The optional AI only explains what is already on screen, uses your own key, and its replies pass through the same banned-wording filter as everything else.

```
 You (desktop window, browser or Android phone)
        |  clicks become JSON calls to /api/...
        v
 FastAPI server on 127.0.0.1 (belfort/main.py)
        |
        +-- research/  Fetch prices -> pivots, trend, levels -> stop and size -> 7 checks -> one label
        +-- tipcheck/  Tip text -> phrase and registration rules (offline) + NSE and price checks (8 s budget)
        +-- practice/  Paper orders -> replayed against later daily bars -> fills, exits, R multiples
        +-- learn/     Markdown lessons -> server-graded exercises -> XP, streak, hearts, stage unlocks
        +-- news/      RSS feeds -> dedupe, tag companies, hide tip-style headlines -> cached 15 minutes
        +-- assistant/ Your question + what is on screen -> your AI provider -> banned-wording filter
        |
        +-- core/ (compliance wording, SQLite store, glossary, languages)
        +-- data/ (Yahoo + NSE providers, disk cache)
```

## 3. The journey, stage by stage

### Stage 0: Starting the app

- **In:** a double-click on `Belfort.exe` (or `python run_desktop.py`).
- **Out:** an app window showing Belfort, served from your own machine.
- **What happens:**
  1. The launcher picks a data folder: `%LOCALAPPDATA%\Belfort` for the packaged app, `data/` from source (`run_desktop.py:20-24`).
  2. It tries port 8766. If something that is not Belfort already holds that port, it takes a free one instead (`run_desktop.py:129-130`).
  3. It starts Uvicorn in a background thread (`run_desktop.py:60-68`).
  4. It shows the loader page straight from disk while the server starts. It switches to the app only once the server answers and the loader has played for at least 2.3 seconds (`run_desktop.py:112-123`).
- **Why:** the comments say the window should never be blank while the server starts (`run_desktop.py:103`). The fixed minimum time is the loader animation's length (`run_desktop.py:29`).
- **The server itself:** `belfort/main.py` builds one FastAPI app and attaches eight routers (`main.py:62-72`). Every router is guarded by an optional access code, which applies only when `ACCESS_CODES` is set (`main.py:35-38`). The page's files are served with `Cache-Control: no-cache`, so an updated app.js is never hidden behind a stale copy (`main.py:75-86`).

### Stage 1: Getting data

- **In:** an NSE symbol or company name.
- **Out:** daily price bars, company figures, and side data such as delivery percentage, bulk deals and the results date. Each item carries a source and an as-of date.
- **What happens:**
  - Prices come from Yahoo Finance through `YahooProvider.history` (`data/providers.py:65`).
  - Sessions Yahoo hasn't published yet are filled in from NSE's end-of-day file (`providers.py:209`). Those bars are added only if their price is within 25% of Yahoo's last close. This guards against an unadjusted split between the two sources (`research/analysis/pipeline.py:271-278`).
  - Results are kept in a disk cache with a time-to-live (`data/cache.py:37`). For cached values Belfort computes itself, the cache key includes a hash of every Python file (`cache.py:23-33`), so changing the code automatically discards stale results.
  - Practice works out which day's bars are current with `market.data_day()` (`data/market.py:43`), treating end-of-day data as ready at 18:00 IST (`settings.py:100`).
- **Why:** the docs ask for local-first data ("fetched by the user's own computer") and for every number to have a source and a date (`docs/ARCHITECTURE.md`, Principles 1 and 3).

### Stage 2: The Research report

`analyze()` in `research/analysis/pipeline.py:246` runs the whole report.

1. **Fetch in parallel.** History, fundamentals, the earnings date, delivery, bulk deals and peer info are all fetched at once on an 8-thread pool (`pipeline.py:259-265`). If a side fetch fails, it becomes a "missing, with a reason" entry instead of breaking the report (`pipeline.py:39-43`).
2. **Swing points (pivots).** A bar is a swing high if it is the highest within `k` bars on each side (`pivots.py:15-25`). `k` is 5 for swing trades and 10 for positional ones (`settings.py:48-49`). Highs and lows are then forced to alternate (`pivots.py:28-38`). A pivot is only "known" `k` bars later (`pivots.py:41-43`), so the backtest never uses information from the future.
3. **Trend.** `trend_state` combines three views (`structure.py:11-69`):
   - **Structure:** higher highs and higher lows.
   - **Alignment:** close > 20-day average > 50-day average, for swing trades.
   - **Break of structure:** a close beyond the last swing point.

   The trend is "up" only when the close is above the slow average and at least one of those views agrees (`structure.py:38-40`). The break-of-structure test exists, the comment says, because pivots lag, and "without this a V-shaped recovery reads as down" (`structure.py:28-29`).
4. **Levels.** Swing points within 0.75 ATR of each other merge into one support or resistance zone. ATR (average true range) is the stock's typical daily range, gaps included. Three or more touches make a "strong" level (`structure.py:77`, `settings.py:55-65`).
5. **Sizing comes before the label** (comment at `pipeline.py:289`).
   - The suggested stop sits half an ATR below the nearest support. That support must leave a gap of at least 0.75 ATR (swing) and no more than the style's maximum stop distance (8% for swing). Otherwise the stop is 1.5 ATR below the close (`sizing.py:12-30`).
   - Position size = floor(capital × risk% ÷ (entry − stop)), capped by what the capital can buy (`sizing.py:58-62`). Risk can never exceed the limit you set.
6. **The label.** `verdict.decide` runs up to seven pass/fail checks (`verdict.py:23-150`):

   | Check | Rule |
   |---|---|
   | Trend is up | `direction == "up"` |
   | Price is at a sensible entry area | a confirmed breakout on 1.5× volume, or within 1.5 ATR of support, or 0 to 1 ATR above the fast average |
   | Price is not stretched | (close − fast average) ÷ ATR ≤ 3 |
   | Stop distance is acceptable | (entry − stop) ÷ entry ≤ 8% (swing) or 15% (positional) |
   | Room to the next resistance | (resistance − entry) ÷ (entry − stop) ≥ 1.5 |
   | No results due inside the holding window | swing only: no results within 5 trading days |
   | Business concerns check ran | the fundamentals were available |

   The label is then chosen (`verdict.py:152-173`):
   - **Rule excludes:** the trend is down, or the business has a serious concern.
   - **Conditions met:** every check passed.
   - **Partly met:** anything else.
   - **Insufficient data:** fewer than 120 bars for swing trades, or 250 for positional.
7. **Words.** `explain.py` and `context.py` turn the numbers into sentences. No language model is involved, as `explain.py`'s docstring says.
8. **Clean up.** The report is made JSON-safe: NaN becomes null and numpy types become plain numbers (`pipeline.py:46-60`).

**Why patterns are not in the label:** `verdict.py:3-4` says chart patterns' "measured value on history is weak", so they are shown as context only. The measurements are in `data/pattern_stats.json`, covered under section 6.

### Stage 3: Tip Check

`tipcheck/service.py:48` (`check`) handles a tip.

1. The text is cut to 5,000 characters (`settings.py:153`).
2. **Text checks, all offline** (`rules.py:376-378`):
   - **Registration:** looks for SEBI numbers matching `IN[AHZP]` plus digits (`rules.py:37`). A number must have exactly 9 digits. INZ and INP numbers are the wrong kind for advice. A number in your imported register counts as "found", but "never as proof", because scammers copy real numbers (`rules.py:126-160`).
   - **Five phrase checks** (promises, target in days, urgency, secrecy, money ask) match phrases from `phrases.json`, so a new language is new data, not new code.
3. **Stock checks, in parallel with an 8-second budget** (`service.py:60-64`). Anything slower is reported as "could not check".
   - **Surveillance:** is the stock on NSE's daily list of surveillance measures?
   - **Pump pattern:** flagged when at least two of three signals hold (`rules.py:276-313`):
     - volume at least 5× its 50-session average in the last 5 sessions;
     - a rise of 30% in 20 sessions, or 60% in 60 sessions;
     - market value below ₹5,000 crore.
4. **Level:** 0 red flags is "low", 1 to 2 is "some", 3 or more is "many" (`rules.py:370-373`). If NSE itself flags the stock for a tip campaign, that finding leads the results (`service.py:79-85`).
5. **Wording:** Belfort's own sentences live in `strings.py` and are tested for banned phrases. The tip's own words are only shown as quoted evidence.

### Stage 4: Practice (paper trading with virtual points)

- **In:** an order: symbol, quantity, optional stop, target and thesis. You start with 1,000,000 points (`settings.py:98`).
- **Out:** fills, exits, the portfolio, R multiples (the result divided by the risk planned at entry) and prediction scores.
- **What happens:**
  1. `place_trade` (`practice/service.py:329`) validates the order and stores it as `pending`.
  2. On a portfolio read, `settle_all` (`service.py:57`) replays new daily bars through `engine.settle_trade` (`practice/engine.py:73-138`). It does this at most once per data day, because new bars arrive once a day.
  3. A market order fills at the next session's open. A limit order fills when the low reaches the limit and expires after 5 sessions.
  4. Exits are checked in a fixed order each day:
     1. a close you requested;
     2. a gap below the stop (exit at the open);
     3. a gap above the target;
     4. the stop being touched;
     5. the target being touched.
  5. Stops can only move up. Each raise is kept with its date, so replaying old bars uses the stop that applied on that day.
  6. Costs of 0.05% per side are applied (`settings.py:101`).
- **Predictions:** each one is scored with the Brier score: (1 − confidence)² if right, confidence² if wrong (`engine.py:154-156`). Points = round(100 × (1 − 4 × Brier)) (`engine.py:159-162`). A 50% call scores 0, and being confident and wrong costs more than being confident and right earns. The docstring's reason is that this "rewards honest confidence, not bold calls".
- **Why the engine is pure:** "No database, no network: easy to test" (`engine.py:1`).

### Stage 5: Learn

- **In:** the syllabus (`content/learn/syllabus.json`) and 38 Markdown lessons, each with a quiz block.
- **Out:** lesson cards, graded exercises, XP, streak, hearts and unlocked stages.
- **What happens:**
  - Answers are graded on the server (`learn/curriculum.py:196`, `216`).
  - A lesson is complete at 60% (`settings.py:137`).
  - XP is 10 for a first completion, plus 5 for no mistakes, or 5 for a replay (`learn/engine.py:67-71`).
  - The streak moves on the first time each day's XP reaches your daily goal. Missed days are covered automatically by "freezes" if you have them, and a freeze is earned every 7 days of streak, up to 2 (`engine.py:74-94`).
  - Wrong answers cost a heart. Hearts refill daily or after a Weak spots review.
  - Intermediate opens when the Beginner stage test or the placement test is passed at 80%, and Advanced opens the same way after Intermediate (`engine.py:122-133`).
- **Why:** charts in lessons use `market.lagged()` (`market.py:88-91`), so named stocks only show prices at least 30 days old. `settings.py:94` cites SEBI's July 2026 education norms.

### Stage 6: News

- `news/feeds.py` fetches every feed in `content/news/feeds.json` on 6 threads.
- Stories with the same first 80 title characters count as duplicates (`feeds.py:218-224`). Stories are sorted newest first and kept to the latest 150.
- Each story is tagged with companies (`feeds.py:178`).
- A regular expression marks headlines that relay buy or sell calls, targets or "multibaggers" as tips (`feeds.py:83-95`). The comment says Belfort "does not relay stock tips, even when a publisher prints them".
- The whole result is cached in 15-minute slots (`feeds.py:245-249`).

### Stage 7: The assistant (bring your own key)

- The page sends your question, what is on screen, and your provider and key in `X-AI-*` headers.
- If no key arrives with the request, the provider falls back to `GEMINI_API_KEY` or `OPENAI_API_KEY` from the environment (`assistant/chat.py:56-60`).
- The question is cut to 2,000 characters and the context to 6,000 (`chat.py:168-170`).
- **Tip Check's web check** (`tipcheck/webcheck.py`, on a button): Gemini with its `google_search` tool, or Groq's `gpt-oss-120b` with `browser_search` when there is no Gemini key or Gemini's search quota is used up, looks for SEBI and exchange actions, scam reports and news about the tip, and lists the sources. The flag count still comes from the rules.
- Every reply is checked with `find_banned`. A reply using promise-style wording such as "guaranteed", "sure shot" or "multibagger" (`core/compliance.py:7-25`) is replaced with a refusal (`chat.py:171-175`).

## 4. One worked example

These numbers are real output from running the project's own code offline on its test data. They come from the sample tip in `tests/test_tipcheck.py` and the synthetic price series from `tests/helpers.py:price_frame`.

**A tip through Tip Check.** The input is the test's sample tip:

> 🚀 SUZLON 100% SURE SHOT CALL 🚀 Buy above 52, Target 60/68 in 3 days. Jaldi entry lo, operator game chal raha hai. Join our VIP premium group, pay 4999 via UPI. SEBI registered. Kisi ko mat batana!

| Check | Result | Evidence quoted back |
|---|---|---|
| Registration | flag | "sebi registered" (a claim, but no number) |
| Promises | flag | "100% sure shot" |
| Target in days | flag | "target 60/68 in 3 days" |
| Urgency | flag | "jaldi entry lo" |
| Secrecy | flag | "operator game", "kisi ko mat batana" |
| Money ask | flag | "join our", "premium group", "upi" |

The stock found in the text is `SUZLON`, and the level is **many (6 red flags)** from the text alone. In the app, the surveillance and pump checks would then run on SUZLON within the 8-second budget.

**A stock through the Research rule (swing style).** The input is 400 synthetic daily bars with a gentle upward drift, with the business check treated as clean.

1. Close ₹140.13, ATR ₹1.81, 20-day average ₹138.53, 50-day average ₹133.19. The trend is **up, established**.
2. The nearest support is ₹127.39 (2 touches), and the nearest resistance is ₹141.65.
3. The stop under support would be about ₹126.49, which is 9.7% below the close. That is over the 8% swing limit, so the stop falls back to 1.5 × ATR: **₹137.40** ("no usable support nearby").
4. Size with ₹1,00,000 capital at 1% risk: the budget is ₹1,000 and the risk per share is ₹2.73, giving **366 shares**. That puts ₹997.50 at risk in a ₹51,285.90 position (51% of capital, a 1.94% stop).
5. Checks:

   | Check | Result | Detail |
   |---|---|---|
   | Trend is up | passed | |
   | Sensible entry area | passed | pulled back to the 20-day average |
   | Not stretched | passed | 0.9 ATR above the average, limit 3 |
   | Stop distance | passed | 1.9%, limit 8% |
   | Room to the next resistance | **failed** | ₹141.65 is only 0.6× the stop distance away, the rule wants 1.5 |
   | No results due inside the holding window | passed | |
   | Business concerns check ran | passed | |

6. The label is **Partly met**: "6 of 7 conditions are met; the rule needs all of them." The detected pattern, "Rising trend line", is shown but plays no part in the label.

## 5. Key decisions and trade-offs

| Decision | What it is | Why (as recorded) | Alternative |
|---|---|---|---|
| Local-first, no Belfort server | Everything runs on 127.0.0.1 and is fetched by your own machine | Cheap, private, and "on the right side of data-licence and SEBI rules" (ARCHITECTURE, Principle 1). A hosted research service is "deliberately not planned" | A hosted web app, which would fall under research-analyst rules |
| Rules first, language second | Labels, fills and scores come from fixed code; the AI only explains | Reproducible and testable (Principle 2) | AI-generated verdicts that can't be pinned down by tests |
| Descriptive labels | "Conditions met / Partly met / Rule excludes" | `settings.py:84`: "They are not buy or sell words" | Buy, sell or hold labels, which the compliance rules ban |
| Patterns kept out of the label | Shown with a measured reliability table | Weak measured value on history (`verdict.py:3-4`) | Scoring patterns as signals |
| Size before the signal | The stop and quantity are computed first | Risk can never exceed the stated limit (`sizing.py:1`) | A label without a risk plan |
| No look-ahead pivots | A pivot is usable only `k` bars later | Keeps the backtest honest (`pivots.py:1`) | Using hindsight, which inflates results |
| Pure engines plus a thin I/O layer | The settlement, Learn and Tip Check rules have no network or database access | "Easy to test" (`practice/engine.py:1`) | Mixed logic and I/O |
| End-of-day paper fills | Fills at the next open, replayed from daily bars | A practice tool, not a broker; virtual points only | Intraday simulation, which needs live data feeds |
| Brier scoring for predictions | Confident and wrong loses more | "Rewards honest confidence, not bold calls" | Points for correct calls only |
| Lagged charts in lessons | Prices at least 30 days old | SEBI education norms (`settings.py:94`) | Live charts, which aren't allowed for education content |
| Tip Check time budget | 8 seconds, then "could not check" | An answer "in about ten seconds even on a slow connection" (`tipcheck/service.py:3-5`) | Waiting on slow NSE servers |
| No front-end build step | Static HTML, CSS and JS | "Anyone with Python can run, read and change it" (Principle 5) | React or Vite, which add a toolchain |
| Android without Gradle | aapt2, javac, d8, zipalign, apksigner | Needs only the SDK and a JDK (android/README) | Gradle, which is heavier and download-hungry |

## 6. What happens in the background

- **Disk cache:**
  - Fetched data is stored under `data/cache` with a time-to-live.
  - Results Belfort computes itself are tied to a hash of the code, so they are discarded automatically after an update (`cache.py:23-47`).
  - Price bars stay valid until the next end-of-day release.
- **Settlement on read:** paper trades are settled when you open the portfolio, at most once per data day (`practice/service.py:57-66`). There is no scheduler.
- **News refresh:** each 15-minute slot has its own cache key, so the feeds are re-read at most every 15 minutes (`feeds.py:246-249`).
- **Pattern backtest (offline, run by hand):** `scripts/run_backtest.py` writes `data/pattern_stats.json`, which the report shows. The current file was generated on 2026-11-17 from 47 large NSE stocks, 2021-11-16 to 2026-11-13.
  - **Synthetic charts:** the double-top detector found 99.5% of drawn double tops and fired on 8.5% of random charts.
  - **Real history (swing):** cup-and-handle reached its target first only 7.7% of the time, against 13.5% for random entries with the same target and stop.
- **SEBI register import:** `python -m belfort.tipcheck.register` refreshes a local copy, because SEBI offers no download.
- **Database migrations:** `core/db.py` applies numbered migrations to `data/belfort.db` the first time each database file is opened in a run (`db.py:160-165`).
- **Builds:**
  - `scripts/build_windows.ps1` runs PyInstaller with `packaging/belfort.spec` to make `dist/Belfort.exe`, plus a SHA-256 file.
  - `android/build_apk.py` makes `android/build/Belfort.apk`, signed with a debug key kept outside the repo.

## 7. How we know it works

- **Tests:**
  - 23 test files, 393 tests passing on main at the last run (commit 9972294).
  - All offline: every network source is replaced by fixtures or synthetic data (`tests/helpers.py`, `tests/fixtures/`).
  - Pure engines (settlement, Learn rules, Tip Check rules, sizing, verdict) are tested directly.
- **Coverage:** CI fails below 70% (`pyproject.toml:38`, "never lower it").
- **CI** (`.github/workflows/ci.yml`):
  - lint (Ruff check and format);
  - tests on Windows and Linux;
  - a dependency audit;
  - a commit-policy check (`scripts/ci/check_commit_policy.py`) that rejects AI attribution.
- **Wording tests:** tests in files such as `test_tipcheck.py`, `test_i18n.py` and `test_learn_exercises.py` run `find_banned`. For each language, the banned phrases come from `content/compliance/banned.<lang>.json` (`core/i18n.py:110`).
- **Pattern reliability:** measured, not assumed. See the numbers in section 6.
- **Not verified:**
  - **Browsers:** there are no browser end-to-end tests yet. Playwright is listed as planned in ARCHITECTURE.
  - **Android:** the app has not been installed on a real phone yet.
  - **Hindi lessons:** they are machine drafts that still need a fluent reviewer.
  - **Live data sources:** they can change without warning, and tests can't catch that.

## 8. Limits and assumptions

- **Unofficial data.** Yahoo Finance and NSE archive files are best-effort sources and can break or lag. Prices are split-adjusted but not dividend-adjusted (`pipeline.py:373`). Live order books, promoter pledges and announcements are not connected, and the report says so.
- **Long only, end of day.** Sizing and practice handle long positions only (`sizing.py:56`). There are no intraday fills.
- **Thresholds are fixed choices.** Examples: 1.5 reward to risk, an 8% maximum swing stop, 0.75 ATR level zones, and 5× volume for a pump (`settings.py`). The code doesn't record why each value was picked. They are in one file so they can be read and changed.
- **Universe bias.** Peers and the backtest use today's large companies (`data/universe.py`). The stats file itself says this "flatters results".
- **Tip Check can be fooled.** The phrase lists only catch wording they contain. Registration needs your own imported copy of SEBI's register, and a real number may still be copied by a scammer.
- **Single user per server.** Accounts switch off while `ACCESS_CODES` is set, because a shared server would share one account (android/README).
- **Things that go stale:**
  - `pattern_stats.json` (generated 2026-11-17);
  - the built-in company list;
  - the dated SEBI facts in lessons;
  - the feed list.

## 9. The short version to share

Belfort is a free, open-source app that helps Indian retail traders learn the stock market safely, and it runs entirely on their own computer. It has four parts: a Research report on any NSE stock, a game-style Learn course, a Practice account with virtual points, and a cleaned-up News feed. On top of those, Tip Check takes a forwarded WhatsApp tip and lists its red flags. Every judgement comes from fixed, published rules over numbers the app computes itself, so the same data always gives the same answer, with its source and date shown. The labels only say whether a rule's conditions are met, never buy or sell, because Belfort is built to stay within SEBI's rules on advice and education. Practice replays real daily prices against your paper orders and scores your predictions so that honest confidence is rewarded. An optional AI assistant explains what's on screen using your own key, and its replies are filtered for promise-style wording. The code is covered by 393 offline tests and checked by CI on Windows and Linux, and the app ships as a single Windows exe plus a lightweight Android companion.
