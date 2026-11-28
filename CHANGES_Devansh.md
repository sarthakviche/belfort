# Changes for Devansh to review

This file covers every change made to **Belfort** (github.com/sarthakviche/belfort, the hackathon project) since 26 Nov 2026. The separate Belfort AI repo has not been touched.

- **Branches.** Nothing goes to `main`.
  - `fix/report-and-news-ui`: PR #29, open and unmerged.
  - `feat/report-redesign-and-logic`: pushed, with no PR yet. It is built on top of the PR #29 branch.
- **Commits** are made under DevanshNarlawar06 only, with no AI attribution.
- **Each section** says what changed, why, and where in the code. Mark anything that's wrong, extra or not needed, and I'll change it and push again.

Status key: ✅ committed and pushed · 🔄 in progress · ⏳ planned

---

## 1. Report and chart display fixes ✅ (PR #29, commit b5fecac)

**Problem:** report lists showed broken bullets, pattern labels on the chart piled on top of each other, and the mouse wheel over the chart zoomed it instead of scrolling the page.

**Fix:**
- **Lists:** they use a small yellow dot. See `ul.plain` in `belfort/static/style.css`.
- **Pattern markers:** each pattern now shows one name, at its last point. Its other points are plain dots. A name is dropped when another one on the same side is within 12 bars. See `patternMarkers()` in `belfort/static/app.js`.
- **Mouse wheel:** it now scrolls the page, not the chart. Drag to pan, pinch or drag the axis to zoom, and double-click the axis to reset. This is the `CHART_POINTER` setting, used by every chart in the app.
- **Right edge:** the chart leaves 14 empty bars on the right, so the last candle and price labels are not cut off.

## 2. Sidebar: "Open files" is now "Recent stocks" ✅ (PR #29, commit b867495)

- The sidebar list is the stocks you opened most recently, so it is named that way now.
- The empty state reads "No stocks yet. Search a company to see its report here."

## 3. News: stock first, what happened, then the link ✅ (PR #29, commit 9a408f3)

**Problem:** News was only headline, photo and a link out.

**Now each story card shows, in order:**
1. A strip of the stocks it names: full company name, last close when Belfort has it, and a link to Belfort's report.
2. The headline.
3. "What happened": the publisher's own summary, shown only when it is at least 40 characters.
4. "Explain in plain words": the existing assistant button.
5. "Read the full story on {source} ↗".

**Also new:**
- A **"Stocks in the news"** panel lists the companies in today's stories. Clicking one filters the feed to that stock.

**Compliance fixes:**
- Broker calls such as "(Buy)", "(Sell)" or "broker's call" are now hidden along with other stock tips.
- "BSE" is no longer tagged as the company BSE Ltd when a story means the exchange or the Sensex.

**Code:**
- `belfort/news/feeds.py`: `TIP_RE`, `EXCHANGE_MENTION` and `companies()`.
- `belfort/news/router.py`
- `belfort/data/symbols.py`: `known_close()`.
- `belfort/static/verticals.js`: `storyCard`, `stockStrip`, `stocksInNews`.
- Tests are in `tests/test_verticals.py`.

## 4. Large caps showed 48 companies, not 50 ✅ (commit 3c63437)

**Why it was 48:** the Nifty 50 list was typed into the code by hand and had gone out of date. Some members had been replaced (for example, Tata Motors split, so it is now TMPV), and a few new members were missing.

**Fix:**
- Belfort now reads NSE Indices' official Nifty 50 file and caches it for a week.
- If that file can't be fetched, it falls back to a built-in copy that matches NSE's list of 26 Nov 2026 and says so on screen.
- A file with fewer than 45 or more than 50 members, or one that isn't a CSV, is rejected.
- The screen's description names the source and lists any company with no price data.

**Code:**
- `belfort/research/screens.py`: `nifty_members()` and `NIFTY_AS_OF`.
- `belfort/data/providers.py`: `nifty50()`.
- `belfort/data/universe.py`: adds TMPV and a Hospitals sector.
- Tests are in `tests/test_nifty.py`.

## 5. Support and resistance logic rechecked ✅ (commit 9872f4c)

I found three problems:

1. **Levels crept upward.** Swing points were grouped by comparing each new point with the group's running average. A group could slowly climb and merge prices more than 1 ATR apart; one measured level spanned 1.24 ATR. Now a group closes as soon as the next point is more than 0.75 ATR above the group's lowest point, so a level is always a tight zone.
2. **Same lookback for both styles.** Swing and positional both looked back one year. Now swing uses about 1 year (260 bars) and positional about 2 years (500 bars).
3. **All levels treated alike.** A single swing high was treated the same as a level tested five times. Each level now has a strength:
   - strong: 3 or more touches
   - moderate: 2 touches
   - single: 1 touch

   Each level also has a zone, its low and high.

**Smaller fixes in the same commit:**
- **Ratios near a limit:** the report printed "1.5 times" even when the true value was 1.45 and the check had failed. Ratios that would round across the limit now show two decimals (`ratio_text()` in `verdict.py`).
- **Quarterly results:** these are now honest about the data.
  - When the year-ago quarter is missing, the comparison is with the previous quarter, and the page says so.
  - When the source's newest quarter is more than 200 days old, the page says the source is behind and points to NSE/BSE. HDFC Bank's newest quarter in Yahoo is Jun 2025.
- **Company profile:** the API now returns a short description of what the company does, cut at whole sentences up to 420 characters, plus industry, website and employee count. The page doesn't show it yet; it will sit at the top in the redesign (section 8).

**Code:**
- `belfort/research/analysis/structure.py`: `find_levels`, `level_strength`.
- `pipeline.py`: `company_profile`.
- `fundamentals.py`: `quarter_trend`.
- `verdict.py`
- `settings.py`
- Tests are in `tests/test_engine.py`.

## 6. Context for failed checks (the HDFC example) ✅ (commit 8bd2d9b)

**Your point:** HDFC Bank traded sideways for months, then broke out with a decent quarter. The check "price far above its 20-day average" fails. It should stay failed, but the report should also explain why the number looks like that.

**What it does now.** A failed check stays failed, and the label never changes. Each failed check gets a **Context** note built only from measured facts: prices, dates, number of sessions and percentages. It contains no predictions and no advice.

**How a move and a sideways range are found (`belfort/research/analysis/context.py`, `recent_move()`):**
- **The move:** it starts at the lowest low of the last 40 sessions. It counts only if price is at least 8% above that low.
- **The sideways range before it:** the longest stretch of at least 20 sessions ending where the move starts, with a high-to-low range of 15% or less. The search goes back up to 400 sessions.
- **A range today:** the same test, applied to the stretch ending at today.

**What each failed check now explains:**

| Check | Context added |
|---|---|
| Price is not stretched | The range (prices, dates, sessions), the size of the move since, and why it still fails: the top of the range is X% below today's price, more than the 8% stop the swing rule allows |
| Room to the next resistance | Whether the nearest level is a single swing high (the weakest kind) and when it was last tested; the next tested level above and its reward-to-risk ratio |
| Entry area | The rule's entry areas in rupees: up to support + 1.5 ATR; the pullback band at the 20-day average; a close above the 20-day high on 1.5× volume |
| Stop distance | What the stop is based on, and a normal day's range (ATR) as a share of price |
| Trend is up | The move so far and what the rule counts as an uptrend |
| Results window | The latest quarter's sales and profit change, and a note when the source is behind |

**HDFC Bank today (live data):**
- **Not stretched, FAIL, context:** "Before this move, price traded between ₹669.20 and ₹761.35 (a 13.8% range) for 68 sessions, 22 Jul to 28 Oct 2026. It then rose 28.8% in 19 sessions and is now above the top of that range… The check still fails: the top of the range is 13.2% below today's price, more than the 8% stop the swing rule allows."
- **Room to resistance, FAIL, context:** "₹905.00 is a single swing high, the weakest kind of level, last tested on 27 Jan 2026. The next tested level above is ₹977.30 (2 swing points), 3.90 times the stop distance away."

**New box on the verdict card, "What else the numbers show":**
- the business read (strengths and concerns count)
- the latest quarter
- the chart move (range, then move)

It ends with: "Context explains the numbers behind each check. It does not change the label."

**Where it shows:** the Context notes appear under each failed check in "Why this label". The navigator in section 8 will make them easier to step through.

**Settings:** `RUN_LOOKBACK_BARS 40`, `RUN_MIN_PCT 8`, `BASE_MIN_BARS 20`, `BASE_MAX_BARS 400`, `BASE_MAX_RANGE_PCT 15`.

**Tests:** `tests/test_context.py`. These include a test that no context text contains buy, sell, target, "will rise", "will fall" or recommend.

## 7. Longer chart history and a weekly chart ✅ (commit 32f4f24)

**Why the chart looked short:** Belfort fetches 5 years of prices, but only sent the chart the last 320 daily bars (swing) or 560 (positional). That is about 1.3 and 2.2 years.

**Now:**
- **Full history:** the chart gets every daily bar, about 5 years and ~1,240 bars.
- **Daily / Weekly switch:**
  - Weekly bars end on Friday and are dated by the week's last trading day.
  - They have 10 and 40-week averages, which are roughly the 50 and 200-day averages.
- **Opening view:**
  - Daily opens on the same recent window as before.
  - Weekly opens on about 3 years.
  - You can drag back through all 5 years.
- **Legend:** it says "5.0 years of history · drag to scroll".
- **Markers:** support, resistance and stop lines show on both charts. Pattern markers only show on daily, because patterns are found on daily bars.
- **Payload size:** prices are rounded to paise to keep the report small, 326 KB.

**Code:**
- `pipeline.py`: `chart_data`, `weekly_bars`.
- `index.html`: the switch.
- `app.js`: `drawChart`.
- Tests are in `tests/test_chart.py`.

## 8. Report redesign ✅ (commit 018c03c)

**New order, top to bottom:**
1. **Name and price:** unchanged.
2. **What the company does** (new card, `companyCard()` in `app.js`):
   - the company's own description from the source, cut at whole sentences;
   - industry, employee count and website link;
   - "Business read: constructive / neutral / cautious";
   - headline numbers from the latest year: sales growth, operating margin, return on equity, debt to equity, P/E, market value;
   - the top 3 strengths and weaknesses;
   - the latest quarter, with the stale-source note when it applies.

   The full table, peers and valuation stay in the dossier.
3. **The chart:** swing or positional, daily or weekly. It is now full width.
4. **The verdict with a check navigator** (`verdictCard()` and `showCheck()`):
   - Numbered buttons 1–7 (1–6 for positional). A yellow bar means met and red means not met.
   - It opens on the **first failed check**.
   - Each check shows its name, met or not met, the numbers, and the Context note when it failed.
   - Previous and Next buttons step through the checks.
   - Below that: "What else the numbers show", then Main risk and "The view is wrong if" side by side.
5. **Side column:**
   - "Chart versus business".
   - **Plan a trade (optional)**, collapsed by default. It says: "Your capital and risk only decide how many shares fit your loss limit if the stop is hit. They never change the label or the checks."
6. **Dossier:** unchanged.

**Also:**
- The duplicated "5 of 7 conditions met" line is gone.
- The report has extra bottom space, so the floating "Ask a question" button doesn't cover the last lines.

**Checked in the app** on HDFCBANK, in both swing and positional:
- the navigator steps correctly and opens on "Price is not stretched" with its context;
- Plan a trade opens and calculates.

## 9. Logic audit 🔄 (findings below; two text fixes done, rule changes need your OK)

I ran the rule on all 50 Nifty stocks in both styles with today's data (26 Nov 2026) and counted how each check behaves. A check that fails on nearly every stock tells the reader very little.

### What the rule does today

| | Swing (7 checks) | Positional (6 checks) |
|---|---|---|
| Conditions met | 5 | 1 |
| Partly met | 37 | 39 |
| Rule excludes | 8 | 10 |
| **Room to the next resistance fails** | **42 of 50** | **46 of 50** |
| Price is not stretched fails | 5 | **24** |
| Entry area passes but stretched fails (contradictory) | 5 | **19** |
| Nearest resistance is a single swing high | 19 | 14 |
| Nearest support is a single swing low | 14 | 20 |

### Finding A: "Room to the next resistance" almost never passes (needs your decision)

**What happens.** The check takes the nearest swing high above price, however minor, and compares its distance with the stop distance.

**Why it fails so often.**
- The nearest "resistance" sits a median **0.76 ATR** above price, less than one normal day's move.
- For about half the stocks, the reward-to-risk is below 0.5.
- These are mostly small swing highs from the last few weeks, not real ceilings.

**Proposal (changes labels, so not done yet).** Pick one of these:
1. **(Recommended)** Ignore levels within 1 ATR of price and single-touch levels when choosing the target. Use the nearest level tested at least twice. The Context note already names that level. On HDFC this would give 3.90× instead of 1.45×.
2. Keep the check as it is, but show it as information rather than a condition.

### Finding B: positional "not stretched" uses the swing limit (needs your decision)

**What happens.**
- Both styles use the same limit: at most 3 ATR above the fast average.
- Positional's fast average is the 50-day, which naturally sits further from price than the 20-day.
- Its median distance is 2.86 ATR, so about half of all stocks fail.

**Proposal.**
- Scale the limit to the average's length, for example 5 ATR for the 50-day.
- Or measure the distance in percent rather than in ATR.

### Finding C: entry "breakout" and "stretched" contradict each other (needs your decision)

**What happens.**
- The entry check passes on a close above the 20-day (or 55-day) high on 1.5× volume.
- After a long run, though, the 20-day high is just last week's high. HDFC's breakout level was set only 2 days earlier, after a 28.8% rise.
- So the rule says "sensible entry area" and "stretched" at the same time. This happens on 19 of 50 positional stocks.

**Proposal.** Count a breakout only when the level it clears is older than a few sessions (for example, the high was set at least 10 sessions ago), or when it clears a sideways range from section 6.

### Finding D: support used for the stop is often a single swing low (information)

- For 14 swing and 20 positional stocks, the nearest support has been touched only once.
- The stop sits half an ATR under it.
- This is not wrong, but the Context note for "Stop distance" now says what the stop is based on.
- **Possible follow-up:** prefer a support tested at least twice when one is within the stop limit.

### Finding E: quarterly data from Yahoo is thin (information)

- For 28 of 50 stocks, Yahoo does not have the year-ago quarter, so the comparison falls back to the previous quarter. The page says so.
- For HDFC Bank, the source's newest quarter is Jun 2025, and the page says the data is behind.
- A real fix needs NSE results filings or another provider. That is a bigger task, worth considering for Belfort AI.

### Fixed now (no label changes) ✅
1. **Lookback wording.** Texts said "in the last year of swings" for both styles, but positional looks back 2 years. They now say "the last 2 years" for positional. This uses `level_span()` in `settings.py`, in `explain.py` and `verdict.py`.
2. **Forecast wording.** The failed "not stretched" check said "After a fast run like this, a pullback is common". That reads as a forecast. It now states a fact: "A stop under recent support sits far below the price, so the loss if it is hit is large."

## 10. Browser showed the old page after updates ✅

**What you saw:** "No files open. Search a company to start its dossier." That text was replaced in section 2, so your browser was still running an old copy of `app.js`.

**Why:**
- The server sent `Last-Modified` but no `Cache-Control` for the page files.
- So the browser guessed how long its copy stayed fresh and reused it without asking the server.
- Every user updating Belfort would hit the same problem.

**Fix:**
- Page files (`index.html`, `app.js`, `style.css` and the rest) are now sent with `Cache-Control: no-cache`.
- The browser still keeps its copy, but it asks the server (by ETag) before each use, and gets the new file when it has changed.
- This is the `AppFiles` class in `belfort/main.py`. Tests are in `tests/test_app.py`.

**One-time step:** a copy already cached before this fix may last until you press **Ctrl+F5** once on http://localhost:8766.

**Localhost stopping:** the preview servers I start are stopped by the desktop app when my turn ends. That stop is not a bug. Run the server from your own terminal to keep it up.

## 11. Empty company card, and more business numbers ✅

**What you saw:** the "What the company does" box was empty.

**Why:** your browser loaded the new page layout, with the empty box, but still ran its old `app.js` from before section 10's fix. That old script has no code to fill the box. The API was returning the description all along.

**Fix:**
- `index.html` now links its files with a version tag (`app.js?v=2026-11-26`, and the same for the others).
- A copy cached before the fix is no longer used, so no Ctrl+F5 is needed.
- After this, section 10's `no-cache` keeps them current.

**More fundamentals in the card:** you said the business side was too thin. The card now shows up to nine numbers, each with something to compare against:

| Number | Shown beside it |
|---|---|
| Sales | change on the year |
| Net profit | last year's figure |
| Net margin, operating margin | last year's figure |
| Return on equity | the sector's peer median (falls back to last year) |
| Debt to equity | last year's figure |
| P/E | the sector's peer median |
| Price to book, market value | — |

Rows the source does not have are left out. For example, banks have no operating margin or debt to equity.

**Data caveat (worth checking):**
- Yahoo gives HDFC Bank a return on equity of 8.6% for FY2026.
- HDFC Bank's own reported figure is higher. The 2023 merger with HDFC Ltd roughly doubled its equity, and Yahoo's calculation may not match the bank's.
- This is a source issue, not a calculation bug. It is another reason for the NSE filings idea in section 9, finding E.

## 12. Fibonacci and momentum as charts ✅

**Before:** the Levels section of the dossier printed one long line of numbers for Fibonacci levels and another for RSI, MACD and ATR.

**Now:**
- **Fibonacci chart**
  - It shows price over the swing, with the swing high and low marked and each level (23.6% to 78.6%) drawn as a yellow line.
  - The levels are also listed as small tags under the chart.
  - It has one sentence in date order, for example: "Levels for the fall from ₹1,017.50 on 1 Dec 2025 to ₹669.20 on 28 Oct 2026. Today's close of ₹862.00 is between the 50.0% (₹843.35) and 61.8% (₹884.45) levels."
  - The old text listed the later date first ("between ₹669.20 (2026-10-28) and ₹1,017.50 (2025-12-01)"), which was confusing.
- **RSI(14) chart:** the last year, with lines at 70 and 30, and a factual reading, e.g. "above 70: over the last 14 sessions, gains have been much larger than losses".
- **MACD(12,26,9) chart:** the MACD line, the signal line, and a green or red histogram, with whether MACD is above or below its signal line.
- **ATR(14) chart:** the last year, plus "a normal day's range is 2.5% of the price", and a note that the rule's stop and stretch checks are measured in ATRs.
- **Wording:** each chart says it describes what price has done, is not part of the rule, and does not predict a move.

**Also:** the levels table said "none found in the last year of swings" for positional too. It now says "the last 2 years" for positional.

**Code:**
- `pipeline.momentum_series()`: sends 250 days of RSI, MACD, signal, histogram and ATR in `chart.momentum`. Setting: `MOMENTUM_CHART_BARS = 250`.
- `app.js`: `fibText`, `momentumHtml`, `drawLevelCharts`.
- Test: the series' last values match the numbers the report already showed.

**Checked in the app** on HDFC Bank, swing and positional.

## 13. Large caps still showed 48 ✅

**What you saw:** "48 · Companies from the built-in Nifty 50 list". That is the text from before section 4.

**Why:**
- Belfort builds the home-page lists once and saves them in its on-disk cache for 6 hours, under the key `screens:v4:<date>`.
- Today's copy was built this morning, before the section 4 fix.
- The cache is on disk, so restarting the server kept serving it.

**Fix:**
- The key now includes `SCREENS_CACHE_VERSION = 5` (`belfort/research/screens.py`), so the lists were rebuilt.
- A comment says to raise the version whenever the lists change.
- A test checks that the key carries the version.

**Checked:** the server now returns 50 companies, "The companies in the Nifty 50 index", read from NSE Indices' current list.

## 14. Results built by Belfort refresh after every update ✅

**Your question:** wouldn't restarting the whole front end and back end be better?

**Answer:** a restart would not have fixed the last two problems.
- The 48-company list lived in the on-disk cache, which survives restarts.
- The empty company box was an old script cached in your browser.

Wiping the whole cache on every start would also throw away 5 years of prices for every stock, company figures and news. The first load would be slow, and refetching everything risks Yahoo or NSE blocking us.

**What changed instead (`belfort/data/cache.py`):**
- **Raw downloads** (prices, company figures, results dates, NSE files) stay cached and expire by time only, as before. Their content doesn't depend on our code.
- **Results Belfort builds from them** are now cached with `derived=True`. Their key includes a fingerprint, a 12-character hash of every `.py` file in `belfort/`, so any code change makes them rebuild on first use. That covers:
  - the home lists (`screens.py`);
  - the tagged news feed (`news/feeds.py`);
  - the news company-name aliases.
- **Packaged `Belfort.exe`:** it has no `.py` files on disk, so it uses the version number (`v0.1.0`) instead.
- **No manual version numbers:** this replaces the `SCREENS_CACHE_VERSION` number from section 13, so nobody has to remember to raise it.
- **Not affected:** research reports aren't cached, so they always run the current code.

**Tests:** `tests/test_cache.py` covers:
- raw entries are reused;
- derived entries rebuild when the fingerprint changes, and raw ones don't;
- the fingerprint is stable;
- the version fallback works.

**Note on a flaky test:** `test_search_is_fast_on_a_full_size_listing` sometimes fails during the full run with coverage on this PC (139 ms per search against a 100 ms limit). It passes every time on its own. Search code isn't touched by this change. It's a timing test that is sensitive to how busy the machine is.

## 15. Header broke with long company names ✅

**What you saw (Power Grid):**
- Open, high, low and the other figures were stacked in a narrow column on the right.
- The name and price sat far down the page, with a large empty space above them.

**Why:**
- The day's figures shared one row with the name and price and only got whatever width was left.
- A long name in the large serif font left almost nothing.
- So the figures shrank to one per line, and the whole row grew tall.

**Fix (`style.css`, `.stats`):** the figures always get their own full-width row under the name and price, with a thin divider line above them.

**Checked** on Power Grid at your screen width (about 1900px): the header is one compact block, 154px tall. Also checked at the narrow pane width and at phone width (375px); no sideways scrolling.

## 16. Switching swing and positional jumped to the top ✅

**What you saw:** when you changed Positional to Swing while looking at the chart, the page went back to the top.

**Why:**
- Switching style reloads the report, and `render()` always scrolled to the top.
- Changing your capital, risk or stop in "Plan a trade" did the same.

**Fix (`app.js`, `load()` and `render()`):**
- When the report being re-drawn is the **same stock**, the page keeps its scroll position. That covers style, capital, risk and stop changes.
- The position is restored instantly, so the page doesn't visibly slide (the site otherwise uses smooth scrolling).
- Opening a **different stock** still starts at the top.

**Checked in the app** on HDFC Bank, scrolled 1200px down:
- Positional, then Swing, then a capital change: still at 1200px each time.
- Opening TCS: back at the top.

## 17. Stop-loss optional in Practice, and a cleaner Fibonacci chart ✅

### Stop-loss is now optional

The order form said "Decide the stop before you buy; it is required." It now reads "Stop-loss (₹, optional)", with a hint that a stop is recommended.

**How a trade without a stop is handled:**
- **Open risk.** The whole position value counts as risk, because nothing limits the loss. The 2% per-trade and 6% total warnings still work. The Open risk card says how many positions have no stop.
- **Placing the order.** It is accepted with a first warning: "No stop-loss: nothing limits the loss on this trade, so its whole value counts as risk, and it has no R in your journal. You can add a stop once it is open." The live preview on the form says the same before you place it.
- **Settlement.** Nothing closes the trade on a fall. Target, "Exit", and a stop or trailing stop added later all still work.
- **R and the journal.** The trade has no R. Win rate and average R leave it out, the same way they already left out trades without R.
- **Manage.** "Raise stop" becomes "Set a stop" for these trades. The stop column shows "none – whole position at risk", or "added after entry" once you set one.
- **Unchanged:** "Size it" still needs a stop, because it sizes by the distance to the stop. Chart replay still asks for a stop, because it is scored in R.
- **Database.** Migration 7 rebuilds the trades table so the stop can be empty. Every existing trade, with all its fields, is copied across.
- **Backups.** Backups without a stop are accepted.

**Code:**
- `core/db.py`: migration 7.
- `practice/engine.py`: settlement and `r_multiple`.
- `practice/service.py`: `current_stop`, `raise_stop`, open risk, `place_trade`.
- `practice/router.py`, `practice/backup.py`.
- `static/verticals.js`.
- `docs/ABOUT.md`.
- **Tests:** `tests/test_optional_stop.py`, 8 tests:
  - no stop means no exit on a fall;
  - a stop added later applies from the next session;
  - a trailing stop works with no initial stop;
  - no stop means no R;
  - the API accepts an order with a warning;
  - open risk counts the whole value;
  - a stop can be set later;
  - the migration keeps old trades.

**Worth deciding:** the Learn lessons teach "decide the stop before you buy". The app still recommends a stop, but it no longer enforces one.

### Fibonacci chart

**Before:** each level had two boxes on the right axis (ratio and price). Big "high" and "low" arrows stretched the price scale, so the candles were squashed.

**Now:**
- **Labels.** Each line has one small label at its left end, e.g. "38.2% ₹794.28" and "swing high ₹871.60". The right axis shows only the price scale and today's close.
- **Swing points.** The swing high and low are small dots.
- **Lines.** The levels are dashed yellow lines, stronger toward 61.8%.
- **Size.** The candles use the full chart height, and the chart is taller.
- **Tags.** The row of level tags under the chart was removed, since the lines are now labelled.

**Checked in the app** on HDFC Bank.

---

## 18. Every open pull request merged, except three that wait for Sarthak ✅

You gave me authority to merge pull requests. For each one I:
1. brought it up to date with main and resolved the conflicts;
2. ran ruff and the tests locally;
3. waited for all five CI jobs to pass;
4. squash-merged it and deleted its branch.

**Merged:** #29, #40, #39 (Tip Check), #37 (Learn game), #38 (exercises), #35 and #36 (tax and safety lessons), #33 (dictionary), #32 (loader and intro), #41 (languages), #31 (README and site), #34 (landing page) and #43 (Android).

**Main now:**
- 352 tests pass.
- Checked in the app: all six sections open, Tip Check answers, and switching to Hindi works.

**Fixes made while merging:**
- **Languages (#41).**
  - The 16 Hindi Beginner lessons were missing the 40 new exercises. I added Hindi versions, with the same answers.
  - I added the fact corrections from the safety lessons: @valid UPI handles, cybercrime.gov.in and helpline 1930, SEBI's dated loss figures.
  - The redesigned report, the optional stop and "Stocks in the news" stay in English for now.
- **Loader (#32).** On Windows the loader could end a few milliseconds early, which failed a test. It now waits until the minimum time has fully passed.
- **Android (#43).** I took the docs/COMPLIANCE.md change out, because it needs Sarthak's approval. It is still proposed in #42.
- **Task list.** Tip Check (T44) is now marked Done. Android (T48) stays In progress until it runs on a phone.

**Not merged, waiting for Sarthak:**
- **#42 accounts.** Needs his approval of the compliance rule-7 change.
- **#30 sprint plan.** Carries the same compliance change.
- **#19 content checker.** Changes his CI files and has conflicts.

---

## 19. Dictionary offers Ask Belfort when only a close spelling matches ✅

**What you saw:** typing "swing trade index" in the Dictionary showed one card, "Swing trade", and no way to ask Gemini.

**Why:** the search counts a close spelling as a match ("swing trade index" is 78% like "swing trade", and the cut-off is 75%). The page only showed Ask Belfort and Search the web when there were zero matches.

**What changed:**
- **Search API** (`belfort/core/glossary_search.py`, `belfort/assistant/glossary_router.py`): a new `close_only` flag. It is true when the best match is only a close spelling or a word inside an explanation, not the term itself, its start or part of it.
- **Dictionary page** (`dictionary.js`, `dictionary.css`): with `close_only`, the results still show, followed by "Not quite what you meant? Ask Belfort about “…”, or search the web." and both buttons.
- **Languages:** the new line is in all eight catalogues (machine drafts).
- **Tests:** two new tests; 354 pass, coverage 85.5%.
- **Checked in the app:** "swing trade index" shows the card and the Ask box; "swing trade" shows only the card.

**Note:** Ask Belfort needs your Gemini key saved in Settings. Without one it explains how to add it instead of calling Gemini.

---

## Open items for you
- **Sarthak:** approve or change the rule-7 amendment so #42 (accounts) can merge, and decide on #30 and #19.
- **Hindi lessons:** machine drafts; someone fluent should read them before release.
- **Translations:** the new report, Practice's optional stop and "Stocks in the news" need catalogue keys.
- **Android:** install the APK on a phone or emulator (platform-tools are not on this machine).
- **Folder:** the empty `D:\belfort-wt` folder left from earlier worktrees can be deleted.
