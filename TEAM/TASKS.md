# Tasks

> Temporary file for the founders. When a task starts, put your name in **Owner** and set **Status** to `In progress`. When it merges, move it to Done with the PR link. We can move these to GitHub Issues later.

**Size:** S is under half a day, M is one to two days, L is three days or more.
**Status:** `Ready` (can start now), `Blocked` (waiting on something named), `In progress`, `Done`.

## Start here

### T01 · Run Belfort and fix what you trip over
- **Owner:** Devansh · **Size:** S · **Area:** platform · **Status:** Ready
- **Why:** A fresh pair of eyes on setup finds the gaps the author cannot see.
- **Do:** Follow [ONBOARDING.md](ONBOARDING.md) on your machine. Fix any step that is wrong or unclear in ONBOARDING.md or README.md.
- **Done when:** A PR with the fixes (or a note that nothing needed fixing), tests green.

### T02 · Try Ask Belfort with a real key
- **Owner:** Devansh · **Size:** S · **Area:** assistant · **Status:** Ready
- **Why:** The chat has only been tested with simulated replies.
- **Do:** Use a free Gemini key, and if you can, a local Ollama (`OpenAI-compatible`, base URL `http://localhost:11434/v1`). Ask about a report, a lesson and a news story ("Explain this"). Check errors when the key is wrong.
- **Files:** `belfort/assistant/chat.py`, `belfort/static/app.js` (chat), `verticals.js` (Settings).
- **Done when:** All three contexts work with at least one provider, error messages are clear, and anything broken is fixed or written up as a new task.

## Learn (content)

### T03 · Write two chart lessons: moving averages, volume
- **Owner:** — · **Size:** M · **Area:** learn · **Status:** Ready
- **Do:** Write `moving-averages` and `volume` (module "Reading a price chart"). Follow CONTRIBUTING.md "Writing a lesson" and the screening test in docs/SYLLABUS.md. Each needs a `::chart`, a `::try` and three quiz questions.
- **Done when:** Both lessons show in the app, tests pass, and the other founder has read them.

### T04 · Write two risk lessons: R multiples, losing streaks
- **Owner:** — · **Size:** M · **Area:** learn · **Status:** Ready
- **Do:** `r-multiples` and `risk-of-ruin` (module "Risk comes first"). Tie them to the Practice stats (average R, win rate).
- **Done when:** As T03.

### T05 · Write "Market hours, circuits and gaps"
- **Owner:** — · **Size:** S · **Area:** learn · **Status:** Ready
- **Do:** `circuits-and-sessions`. Check the current NSE session times and circuit rules at the source and cite them.
- **Done when:** As T03.

### T06 · Content checker in CI
- **Owner:** — · **Size:** S · **Area:** learn, platform · **Status:** Ready
- **Why:** As lessons grow, mistakes should fail the build, not reach users.
- **Do:** A script `scripts/check_content.py` that checks every lesson: front matter present, quiz has at least 3 valid questions, every `::chart` symbol is an NSE-style symbol, every syllabus lesson without `planned` has a file. Run it in `.github/workflows/ci.yml`.
- **Done when:** CI fails on a deliberately broken lesson and passes on main.

## Practice

### T07 · Position-size helper in the order form
- **Owner:** — · **Size:** M · **Area:** practice · **Status:** Ready
- **Why:** The 1% rule is the most important lesson; the order form should make it easy.
- **Do:** Add a "Size it" button to the paper order form: risk % input, fetch the last close for the symbol, compute shares = (account value × risk %) ÷ (entry − stop), rounded down, fill the quantity. Reuse `research/analysis/sizing.py` through a small endpoint such as `GET /api/practice/size`.
- **Files:** `belfort/practice/router.py`, `service.py`, `static/verticals.js`, tests.
- **Done when:** Tests cover the endpoint; quantity never risks more than the limit.

### T08 · Faster portfolio: cache bars and settle in the background
- **Owner:** — · **Size:** M · **Area:** practice · **Status:** Ready
- **Why:** Every portfolio load fetches bars for each open symbol, which gets slow with many trades.
- **Do:** Cache daily bars per symbol until the next market close; settle once per new trading day; keep `engine.py` untouched.
- **Done when:** A portfolio with 20 symbols loads in under a second on the second visit; tests pass.

### T09 · Replay: send hidden bars only after the decision
- **Owner:** — · **Size:** M · **Area:** practice · **Status:** Ready
- **Why:** Today the browser receives the future bars up front, so anyone can peek.
- **Do:** Keep the replay session server-side (an id plus the window); `/replay/new` returns only the visible bars; `/replay/score` returns the rest.
- **Done when:** The hidden bars are not in any response before the decision; tests updated.

## Platform

### T10 · Browser smoke tests
- **Owner:** — · **Size:** M · **Area:** platform · **Status:** Ready
- **Do:** Playwright tests that open each section with network sources faked: open a report, pass a quiz, place a paper trade, switch news categories. Add to CI.
- **Done when:** CI runs them headless and they pass.

### T11 · Mobile layout pass for Learn, Practice and News
- **Owner:** — · **Size:** S · **Area:** front end · **Status:** Ready
- **Do:** Check every new screen at 375px and 768px wide. Fix overflow, tables (stack or scroll), and form layout.
- **Done when:** Screenshots of each screen at both widths attached to the PR.

### T12 · Windows installer spike
- **Owner:** — · **Size:** L · **Area:** platform · **Status:** Ready
- **Do:** Package `run_desktop.py` with PyInstaller (or a better option you find) so Belfort installs without Python. Report size, start time and antivirus warnings.
- **Done when:** An installer that runs on a clean Windows machine, plus a short write-up.

## Research and News

### T13 · Editable rule profiles
- **Owner:** — · **Size:** L · **Area:** research · **Status:** Blocked on D1 (pricing decision changes how much of Research we keep)
- **Do:** Read rule thresholds from a user file (`data/rules.json`, defaults from `settings.py`), show the active profile in the report, and test that changes take effect.

### T14 · Company tags for every NSE stock in news
- **Owner:** — · **Size:** M · **Area:** news · **Status:** Ready
- **Why:** Tags only cover about 130 built-in stocks.
- **Do:** Build aliases from NSE's full listed-company file; add tests for false positives (common words, short names).
- **Done when:** A day of real headlines tags more companies without wrong tags in a manual check of 50 stories.

## Decisions (for both founders, not code)

| ID | Decision | Why it matters | Status |
|---|---|---|---|
| D1 | Pricing and licence | Charging for per-stock Research labels may need SEBI research-analyst registration (see docs/COMPLIANCE.md). Free, paid, or paid for Learn and Practice only? | Open |
| D2 | Name and brand | The app still shows the "Belfort AI" wordmark in the sidebar. Keep, drop "AI", or rename? | Open |
| D3 | Securities lawyer review | Before any user outside the two of us sees it | Open |
| D4 | Licensed data | Yahoo and NSE archive data are unofficial; a paid product needs a licensed feed or user-keyed broker data | Open |
| D5 | Ownership and roles | Who owns which part, and the founders' agreement | Open |

## Done

- v0.1 foundation (see README "What is built").
