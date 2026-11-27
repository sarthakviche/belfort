# Changelog

All notable changes to Belfort. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Learn is now a path. Lessons sit on a winding map in three stages (Beginner, Intermediate, Advanced) with a checkpoint at the end of each module and a stage test at the end of each stage. A new learner sees Beginner only: later stages show their titles with a lock, and the app refuses their lessons and quizzes until you pass the previous stage test at 80% or more, or test out of Beginner with a 12-question placement test. Each lesson is a short run of cards (one per heading) followed by exercises with instant feedback. Exercises can be multiple choice, true or false, put in order, or a number answer with a tolerance, all graded on the server. You earn XP (10 per lesson, 5 more for no mistakes, 20 for a checkpoint or stage test), pick a daily goal of 10, 20 or 50 XP, keep a streak (one freeze earned every 7 days, up to two held, used automatically on a missed day), and have 5 hearts a day: a wrong answer costs one, and a Weak spots review of past mistakes refills them. XP, hearts and streaks are virtual and cannot be redeemed or bought. The mascot reacts to answers, and confetti marks a finished module or stage (still when your system asks for reduced motion).
- Learn: the Taxes and records module. Short and long-term capital gains on shares (the 12-month rule, STCG and LTCG rates, the yearly exemption, STT, a worked example, set-off and 8-year carry-forward of losses) and Contract notes, P&L statements and filing (what to keep, ITR-2 against ITR-3, intraday and F&O as business income). Glossary adds STCG, LTCG and ITR. Thirty-five of 38 lessons are now written.
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
- README shortened to the essentials; project details moved to `docs/ABOUT.md`.
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
