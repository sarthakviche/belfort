<div align="center">

<img src="belfort/static/img/logo.png" alt="Belfort" width="88" height="88">

# Belfort

**Learn, practise and research Indian stocks in one app.**
*The practice room, not the tip line.*

![Status](https://img.shields.io/badge/status-private%20pre--release-facc15?style=flat-square&labelColor=0e0e10)
![Version](https://img.shields.io/badge/version-0.1-8b8b90?style=flat-square&labelColor=0e0e10)
![Tests](https://img.shields.io/badge/tests-81%20passing-facc15?style=flat-square&labelColor=0e0e10)
![Python](https://img.shields.io/badge/python-3.12-8b8b90?style=flat-square&labelColor=0e0e10)

</div>

> **Private pre-release.** This repository is shared only by its two founders, Sarthak and Devansh. Belfort is not published, not free to use, and has no licence yet (see [LICENSE](LICENSE)). Pricing and licence are decided before the first release; read the pricing note in [docs/COMPLIANCE.md](docs/COMPLIANCE.md) first, because charging changes the SEBI picture.

**Devansh, start here:** [TEAM/ONBOARDING.md](TEAM/ONBOARDING.md), then pick a task from [TEAM/TASKS.md](TEAM/TASKS.md).

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

## What is built (v0.1)

| Area | Built | Notes |
|---|---|---|
| **Research** | Fuzzy company search (names, initials, nicknames, typos), per-stock report, three screens, pattern reliability backtest, position sizing | Carried over from the earlier Belfort AI project. Labels are now descriptive: "Conditions met", "Partly met", "Rule excludes". |
| **Learn** | Syllabus of 3 tracks, 12 modules, 38 lessons; **8 lessons written** with quizzes; quiz grading on the server; progress and streaks; example charts | Lesson charts only use prices at least 30 days old (SEBI education norm from July 2026). |
| **Practice: paper account** | Stock picker by company name (no symbol needed), order ticket with last close, mini chart, stop idea and "Size it", market and limit orders, required stop, optional target, raised and trailing stops, partial exits, end-of-day fills, gaps, costs, exits, trade reviews, win rate, average R | Long only. Virtual points, never redeemable. |
| **Practice: predictions** | Log a call with direction, horizon and confidence; auto-resolution; Brier score, points, calibration chart, badges | |
| **Practice: chart replay** | Random hidden past chart, plan a stop and target, animated reveal, R result, running record | |
| **News** | Six RSS sources, de-duplication, categories, company tags, hover definitions, "Explain this", tip-style headlines hidden | Headlines and feed descriptions only; links out. |
| **Assistant** | Bring-your-own-key chat with Gemini or OpenAI-compatible providers; context-aware (report, lesson, story); wording filter | Not yet tried with a real key, only with simulated replies in tests. |
| **Platform** | FastAPI app, SQLite store with migrations, static front end, Windows launcher, 81 offline tests, lint, format and coverage checks, CI on Windows and Linux | |
| **Docs** | Architecture, syllabus method, compliance, competitor landscape, roadmap | In [docs/](docs). |

## What is yet to build

The full plan is in [docs/ROADMAP.md](docs/ROADMAP.md); the work ready to pick up today is in [TEAM/TASKS.md](TEAM/TASKS.md). The headlines:

- **Decisions:** licence, pricing and brand name; a securities lawyer's review.
- **Learn:** 30 of 38 lessons, replay drills linked to lessons, a content checker in CI, Hindi.
- **Practice:** position-size helper in the order form, faster settlement, trailing stops, journal analytics, export.
- **Research:** editable rule thresholds, watchlists, market context.
- **News:** wider company tagging, NSE announcements, events calendar.
- **Platform:** browser tests, mobile layout pass, Windows installer, macOS and Linux.

Known limitations are listed in [TEAM/STATUS.md](TEAM/STATUS.md).

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
TEAM/       ONBOARDING  TASKS  STATUS  START_PROMPT   (temporary, for the founders)
tests/      81 tests, no network needed
```

## Data

Prices and company figures come from Yahoo Finance (through `yfinance`) and NSE's public end-of-day archive files, fetched by the user's own machine. Everything is **end-of-day, not live**, and every figure shows its source and date. These sources are unofficial and not licensed for a paid product; see the roadmap.

## Important

Belfort is an educational and research tool. It is **not investment advice** and not a recommendation to buy, sell or hold any security, and its authors are not SEBI-registered research analysts or investment advisers. Practice points have no money value. Belfort never places orders.

## Licence

None yet: all rights reserved, private pre-release. See [LICENSE](LICENSE).
