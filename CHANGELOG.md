# Changelog

All notable changes to Belfort. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
