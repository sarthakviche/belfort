# Changelog

All notable changes to Belfort. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Stock picker: find any NSE company by typing part of its name, its initials, a common nickname ("sbi", "l&t", "jio") or a near miss ("hdcf bank"). Used in the sidebar search, the paper order form and the prediction form, with recent picks and the last close. No symbol needed.
- Production engineering setup: Ruff lint and format, coverage threshold, pinned dependencies, dependency audit, Windows and Linux CI, commit and PR policy checks, pre-commit hooks, Dependabot, code owners, conventions guide.

### Changed
- Ask Belfort: errors now say what to do (wrong key, unknown model, rate limit, provider outage, slow answer, local model not running) and never show your key back to you.
- Renamed single-letter and uppercase local variables in the research engine to descriptive names; no behaviour change.

## [0.1.0] - 2026-11-21

### Added
- Learn: screened syllabus (3 tracks, 12 modules, 38 lessons planned), 8 lessons with quizzes, progress, streaks, lagged example charts.
- Practice: paper account with end-of-day fills, stops, targets, costs and reviews; prediction journal with Brier scoring and calibration; chart-replay trainer.
- News: RSS from five publishers and the RBI, categories, company tags, hover definitions, "Explain this", tip-style headlines hidden.
- Research: per-stock report and screens from Belfort AI, with descriptive labels.
- Bring-your-own-key assistant for Gemini and OpenAI-compatible providers.
