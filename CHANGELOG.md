# Changelog

All notable changes to Belfort. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
- Practice: the portfolio opens much faster on repeat visits. Daily prices are kept until the next end-of-day release, and the paper account settles once per trading day instead of on every view.
- Ask Belfort: errors now say what to do (wrong key, unknown model, rate limit, provider outage, slow answer, local model not running) and never show your key back to you.
- Renamed single-letter and uppercase local variables in the research engine to descriptive names; no behaviour change.

### Fixed
- Chart replay: the company and the future bars stay inside Belfort until you decide, and the reveal shows the correct end date instead of "[object Object]".

## [0.1.0] - 2026-11-21

### Added
- Learn: screened syllabus (3 tracks, 12 modules, 38 lessons planned), 8 lessons with quizzes, progress, streaks, lagged example charts.
- Practice: paper account with end-of-day fills, stops, targets, costs and reviews; prediction journal with Brier scoring and calibration; chart-replay trainer.
- News: RSS from five publishers and the RBI, categories, company tags, hover definitions, "Explain this", tip-style headlines hidden.
- Research: per-stock report and screens from Belfort AI, with descriptive labels.
- Bring-your-own-key assistant for Gemini and OpenAI-compatible providers.
