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

## 8. Report redesign ✅ (commit after 32f4f24, see git log)

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

## 9. Logic audit ⏳ (after the redesign)

I'll look for other places where the logic says something misleading, and write up what I find here before changing anything. Candidates:
- A single swing high used as the resistance target.
- How a "breakout" is defined: it currently uses the 20-day high, which on HDFC was only 2 days old.
- Whether swing and positional are consistent with each other.

---

## Open items for you
- **PR #29:** open, CI green, not merged. Merge it when you're happy with it.
- **`feat/report-redesign-and-logic`:** contains PR #29's commits plus sections 4–7. I'll open a PR for it once you've read this file.
- **Changelog:** `CHANGELOG.md` has a line for every user-visible change above.
