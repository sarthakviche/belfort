<div align="center">

<img src="belfort/static/img/logo.png" alt="Belfort" width="88" height="88">

# Belfort

**Learn, practise and research Indian stocks in one app.**
*The practice room, not the tip line.*

![Status](https://img.shields.io/badge/licence-MIT-facc15?style=flat-square&labelColor=0e0e10)
![Version](https://img.shields.io/badge/version-0.1-8b8b90?style=flat-square&labelColor=0e0e10)
![Tests](https://img.shields.io/badge/tests-138%20passing-facc15?style=flat-square&labelColor=0e0e10)
![Python](https://img.shields.io/badge/python-3.12-8b8b90?style=flat-square&labelColor=0e0e10)

</div>

Belfort is **free and open source** (MIT). It runs on your own computer: no account, no server, no tips. Windows is the first-class platform; a one-click installer is on the [roadmap](docs/ROADMAP.md).

**Want to help?** Read [CONTRIBUTING.md](CONTRIBUTING.md) and pick a `Ready` task from [docs/TASKS.md](docs/TASKS.md). Lessons are a great first contribution.

---

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
| **Docs** | Architecture, syllabus method, compliance, competitor landscape, roadmap | In [docs/](docs). |

## What is yet to build

The full plan is in [docs/ROADMAP.md](docs/ROADMAP.md); the work ready to pick up today is in [docs/TASKS.md](docs/TASKS.md). The headlines:

- **Decisions:** brand name, download location and code signing; a securities lawyer's review.
- **Learn:** 5 of 38 lessons, replay drills linked to lessons, a content checker in CI, Hindi.
- **Research:** editable rule thresholds, watchlists, market context.
- **News:** wider company tagging, NSE announcements, events calendar.
- **Platform:** browser tests, accessibility pass, offline assets, Windows installer and release workflow.

Known limitations are listed in [docs/STATUS.md](docs/STATUS.md).

## Run it

**Windows:** install [Python 3.12](https://www.python.org/downloads/) and double-click `run.bat`. The first run installs everything and opens Belfort in its own window.

**Any platform:**

```bash
python -m venv .venv          # must be Python 3.12; on Windows, `py -3.12 -m venv .venv` picks it
.venv/Scripts/python -m pip install -r requirements.txt     # macOS/Linux: .venv/bin/python
.venv/Scripts/python -m uvicorn belfort.main:app --port 8765 --reload
.venv/Scripts/python -m pytest -q
```

Open <http://localhost:8765>. Optional settings are in [`.env.example`](.env.example).

## How it is built

A modular monolith: FastAPI and plain HTML, CSS and JavaScript with no build step, SQLite for practice records, and content (lessons, syllabus, feeds) as plain files. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

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

## Licence

[MIT](LICENSE). Free to use, change and share, including commercially, with the copyright notice kept. Please keep Belfort's compliance principles if you build on it: no tips, no real-money games.
