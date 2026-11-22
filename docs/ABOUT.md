# About Belfort

Everything about the project in one place: what it does, what works today, what is left, how it is built and where its data comes from. For setup and how to contribute, see [CONTRIBUTING.md](../CONTRIBUTING.md).

## What Belfort is

An app for beginner and intermediate traders who want to swing or positional trade NSE stocks properly. It has four parts:

| Part | What a user does there |
|---|---|
| **Learn** | Works through a short, practical syllabus. Five-to-eight-minute lessons, a quiz after each, streaks, and a button into the practice tools. Topics are screened: if it does not change a trading decision or protect your money, it is not taught. |
| **Practice** | Trades a **paper account** with virtual points; logs **predictions** ("JIOFIN higher in 4 weeks, 65% sure") scored for honest confidence; and drills on a **chart-replay trainer** that hides the company and the future. |
| **Research** | Opens a report on any NSE stock: a fixed rule's checklist, support and resistance, patterns with their measured reliability, a business check against peers, and a position size. |
| **News** | Reads market headlines from public feeds and the RBI, sorted and tagged, with a hover definition for every term and an "Explain this" button. |

**Ask Belfort**, the explainer chat, works across all four with the user's own AI key (Gemini, or any OpenAI-compatible service, including a local Ollama model). It runs entirely on the user's computer: no Belfort server, no account.

## What works today

| Area | Built | Notes |
|---|---|---|
| **Research** | Fuzzy company search (names, initials, nicknames, typos), per-stock report, three screens, pattern reliability backtest, position sizing | Carried over from the earlier Belfort AI project. Labels are now descriptive: "Conditions met", "Partly met", "Rule excludes". |
| **Learn** | Syllabus of 3 tracks, 12 modules, 38 lessons; **33 lessons written** with quizzes; quiz grading on the server; progress and streaks; example charts | Lesson charts only use prices at least 30 days old (SEBI education norm from July 2026). |
| **Practice: paper account** | Stock picker by company name (no symbol needed), order ticket with last close, mini chart, stop idea and "Size it", market and limit orders, required stop, optional target, raised and trailing stops, partial exits, open-risk total and size warnings, end-of-day fills, gaps, costs, exits, trade reviews with setup and mistake tags, journal analytics (R distribution, by setup, holding time and mistake, habits), win rate, average R, equity curve with largest drawdown, CSV and JSON export with backup restore | Long only. Virtual points, never redeemable. |
| **Practice: predictions** | Log a call with direction, horizon and confidence; auto-resolution; Brier score, points, calibration chart, badges | |
| **Practice: chart replay** | Random hidden past chart, plan a stop and target, animated reveal, R result, running record | |
| **News** | Six RSS sources, de-duplication, categories, company tags, hover definitions, "Explain this", tip-style headlines hidden | Headlines and feed descriptions only; links out. |
| **Assistant** | Bring-your-own-key chat with Gemini or OpenAI-compatible providers; context-aware (report, lesson, story); wording filter; clear errors that never echo the key | |
| **Platform** | FastAPI app, SQLite store with migrations, static front end, Windows launcher, 138 offline tests at 79% coverage, lint, format and audit checks, CI on Windows and Linux | |
| **Docs** | Architecture, syllabus method, compliance, competitor landscape, roadmap | In this folder. |

## What is yet to build

The full plan is in [ROADMAP.md](ROADMAP.md); the work ready to pick up today is in [TASKS.md](TASKS.md). The headlines:

- **Decisions:** brand name, download location and code signing; a securities lawyer's review.
- **Learn:** 5 of 38 lessons, replay drills linked to lessons, a content checker in CI, Hindi.
- **Research:** editable rule thresholds, watchlists, market context.
- **News:** wider company tagging, NSE announcements, events calendar.
- **Platform:** browser tests, accessibility pass, offline assets, Windows installer and release workflow.

Known limitations are listed in [STATUS.md](STATUS.md).

## How it is built

A modular monolith: FastAPI and plain HTML, CSS and JavaScript with no build step, SQLite for practice records, and content (lessons, syllabus, feeds) as plain files. See [ARCHITECTURE.md](ARCHITECTURE.md).

```
belfort/    research/  learn/  practice/  news/  assistant/  core/  data/  static/
content/    learn/syllabus.json   learn/lessons/*.md   news/feeds.json
docs/       ARCHITECTURE  CONVENTIONS  SYLLABUS  COMPLIANCE  LANDSCAPE  ROADMAP
            TASKS  STATUS  CONVENTIONS
tests/      138 tests, no network needed
```

## Data

Prices and company figures come from Yahoo Finance (through `yfinance`) and NSE's public end-of-day archive files, fetched by the user's own machine. Everything is **end-of-day, not live**, and every figure shows its source and date. These sources are unofficial and not licensed for a paid product; see the roadmap.

## Important

Belfort is an educational and research tool. It is **not investment advice** and not a recommendation to buy, sell or hold any security, and its authors are not SEBI-registered research analysts or investment advisers. Practice points have no money value. Belfort never places orders.
