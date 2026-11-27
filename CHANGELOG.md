# Changelog

All notable changes to Belfort. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Windows app: `scripts\build_windows.ps1` builds a single `Belfort.exe` (no Python needed). It keeps user data in `%LOCALAPPDATA%\Belfort`, uses port 8766 (or a free port if that is taken) so it can run next to the older Belfort AI, and bundles the chart library so charts work offline.
- Learn: the Running several trades and Psychology modules. Total open risk and correlation (matching the Practice Open risk card and its 2% and 6% warnings), Drawdown rules: when to stop trading (with the equity curve), FOMO, revenge trading and overconfidence (each bias linked to a journal mistake tag), and Writing your own trading rules. Thirty-three of 38 lessons are now written.
- Learn: the Market context module. Index trend and market breadth, Sector strength and rotation, and FII and DII flows, RBI policy and the event calendar. Glossary adds Market breadth. Twenty-nine of 38 lessons are now written.
- Learn: the Journal module. What to write before and after every trade (using the Practice order form, review box and mistake tags), Win rate is not the score: expectancy (read as Average R), and Calibration (the Brier score and the Calibration panel on the Predict page). Twenty-six of 38 lessons are now written.
- Learn: the Indicators and patterns module. ATR: how far a stock normally moves; RSI and MACD: momentum, not prophecy; and Chart patterns and what the backtest shows, which walks through Belfort's own pattern backtest against a random-entry baseline. Twenty-three of 38 lessons are now written.
- Learn: the Business check module. The five numbers that matter (sales growth, operating margin, return on equity, debt to equity, cash from operations), P/E only means something against peers, and Red flags: debt, pledges, falling cash flow. Each lesson uses the same thresholds and wording as the research report's business section. Twenty of 38 lessons are now written.
- Learn: the Setups module. The pullback in an uptrend and Breakouts and why volume matters, matching the checks in the research report; Exits (targets, trailing stops, time stops, and the Practice tools for each); and Results dates and holding through events (SEBI's 45 and 60-day deadlines, Belfort's 5-day swing check). Glossary adds Trailing stop and Time stop. Seventeen of 38 lessons are now written.
- Learn: two lessons on risk. Thinking in R (results as multiples of planned risk, read alongside the Win rate and Average R cards in Practice) and Losing streaks and risk of ruin (how often streaks happen and what they cost at different risk levels). Glossary adds Drawdown and Risk of ruin. Thirteen of 38 lessons are now written.
- Learn: three new lessons. Market hours, circuits and gaps (NSE session times, price bands and market-wide circuit breakers, cited from NSE); Moving averages without the mystery; and Volume: is anyone behind the move? Eleven of 38 lessons are now written.
- Practice equity curve: the paper account's value at the end of each trading day you open Belfort, drawn against the starting points, with the largest drawdown so far.
- Practice data export: download trades, predictions and replays as CSV, or one JSON backup, from Settings, and restore a backup later. A file that is not a valid backup is refused and nothing changes.
- Open-source release preparation: MIT licence, public README, contributing guide for outside contributors, Code of Conduct, security policy with private reporting; the task board and status page moved to `docs/`.
- Practice journal analytics: tag each trade's setup and, in the review, the mistakes you made (moved the stop, no plan, chased, sized too big, exited early). A Your journal panel shows your results in R, by setup, by holding time and by mistake, and lists what has worked and what has cost you once a pattern has at least 3 trades.
- Practice: an Open risk card shows how many points you would lose if every stop were hit, as a share of the account. The order form warns before you place an order that risks more than 2% on its own or pushes open risk above 6%.
- Practice: manage an open position. Raise its stop (it never moves down), set a trailing stop as a percentage or an ATR multiple below each close, or sell part of it at the next open. R is still measured against the original stop.
- Practice order ticket: picking a stock shows its last close and date, the day's change, a 3-month chart with the nearest support, and a stop idea you can use or change. "Size it" fills the quantity from your risk per trade, and the form shows the points at risk and their share of the account before you place the order.
- Stock picker: find any NSE company by typing part of its name, its initials, a common nickname ("sbi", "l&t", "jio") or a near miss ("hdcf bank"). Used in the sidebar search, the paper order form and the prediction form, with recent picks and the last close. No symbol needed.
- Production engineering setup: Ruff lint and format, coverage threshold, pinned dependencies, dependency audit, Windows and Linux CI, commit and PR policy checks, pre-commit hooks, Dependabot, code owners, conventions guide.

### Changed
- Research Levels section: Fibonacci retracements are drawn on a price chart of the swing (swing high and low marked, each level as a line) with a sentence saying which levels today's close sits between. RSI, MACD (with signal line and histogram) and ATR are shown as charts of the last year, each with a one-line plain reading, instead of a line of numbers.
- Research company card: nine headline numbers (sales, net profit, net margin, operating margin, return on equity, debt to equity, P/E, price to book, market value), each with last year's figure or the sector's peer median beside it. Numbers the source does not have for a company are left out.
- Research report layout: what the company does now comes first, under the name (the company's own description, industry, employees, website, the business read, headline numbers, top strengths and weaknesses, and the latest quarter), then the chart, then the verdict. The verdict has a numbered navigator over the rule's checks (yellow met, red not met) that opens on the first unmet check and steps through each with its numbers and context. Position size moved into a collapsed "Plan a trade" box that says it never changes the label. The repeated conditions count is gone and the floating Ask button no longer covers the end of the report.
- Research chart: shows the whole price history the source returns (about five years) instead of the last 15 to 27 months, and a Daily / Weekly switch adds weekly bars with 10 and 40-week averages. Daily still opens on recent months; drag to scroll back. Pattern markers show on the daily chart only.
- Research report: a failed rule check now carries a Context note with the facts behind it, and the check stays failed. After a long sideways range and a fast move up, "Price is not stretched" names the range, its dates, the size of the move and why the check still fails; "Room to the next resistance" says when the nearest level is a single swing high and how far the next tested level is; the entry, stop and results checks show the rupee entry areas, the stop basis and the latest quarter. The verdict card adds "What else the numbers show": the business read, the latest quarter and the recent chart move.
- Sidebar: "Open files" is now "Recent stocks", the stocks you opened most recently.
- News: each story now leads with the stocks it names (full name, last close when Belfort has it, and a link to Belfort's report), then the publisher's own summary under "What happened", then a link to read the full story at the source. A new "Stocks in the news" panel lists the companies in today's stories and filters to one. Broker "(Buy)" calls are hidden with the other stock tips, and "BSE" is no longer tagged as the company when a story means the exchange or its indices.
- README shortened to the essentials; project details moved to `docs/ABOUT.md`.
- Practice: the portfolio opens much faster on repeat visits. Daily prices are kept until the next end-of-day release, and the paper account settles once per trading day instead of on every view.
- Ask Belfort: errors now say what to do (wrong key, unknown model, rate limit, provider outage, slow answer, local model not running) and never show your key back to you.
- Renamed single-letter and uppercase local variables in the research engine to descriptive names; no behaviour change.

### Fixed
- After an update, the home lists and the tagged news feed are rebuilt instead of serving what the previous version produced. Results Belfort builds are cached under a fingerprint of its code; downloaded prices, company figures and exchange files stay cached as before.
- Large caps could still show 48 companies and the old "built-in Nifty 50 list" text for up to six hours after updating, because the built lists are cached on disk under a fixed key. The key now carries a version that is raised whenever the lists change.
- A browser holding the page from before the cache fix could load the new layout with the old script, leaving the company card empty. The page now links its files with a version tag so they are fetched fresh.
- After an update the browser kept showing the old page (old text such as "No files open", old layout) because the page files had no cache instruction. They are now sent with `Cache-Control: no-cache`, so the browser checks for a newer file each time.
- Research report: positional texts said "in the last year of swings" though positional levels look back two years; the failed "not stretched" check no longer says a pullback "is common" and states the stop distance instead.
- Research report: the Business strengths and weaknesses lists no longer break into narrow columns where a term is underlined; chart patterns are named once each (bullish below the bars, bearish above) instead of piling up point labels; scrolling with the mouse over a chart scrolls the page instead of zooming the chart (drag to pan, pinch or drag an axis to zoom).
- Chart replay: the company and the future bars stay inside Belfort until you decide, and the reveal shows the correct end date instead of "[object Object]".

## [0.1.0] - 2026-11-21

### Added
- Learn: screened syllabus (3 tracks, 12 modules, 38 lessons planned), 8 lessons with quizzes, progress, streaks, lagged example charts.
- Practice: paper account with end-of-day fills, stops, targets, costs and reviews; prediction journal with Brier scoring and calibration; chart-replay trainer.
- News: RSS from five publishers and the RBI, categories, company tags, hover definitions, "Explain this", tip-style headlines hidden.
- Research: per-stock report and screens from Belfort AI, with descriptive labels.
- Bring-your-own-key assistant for Gemini and OpenAI-compatible providers.
