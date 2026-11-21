# Onboarding: Devansh

> Temporary file for the founders. Delete or move to the wiki before any public release.

Welcome. This page gets you from clone to your first pull request in about an hour.

## 1. Run it (15 minutes)

```powershell
git clone https://github.com/sarthakviche/belfort.git
cd belfort
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m uvicorn belfort.main:app --port 8765 --reload
```

Open <http://localhost:8765>. You need Python 3.12 and an internet connection (prices and news are fetched live; the tests are not).

Optional: open **Settings** in the sidebar and paste a free Gemini key from <https://aistudio.google.com/apikey> to try **Ask Belfort**.

## 2. Click through it (15 minutes)

| Do this | You are looking at |
|---|---|
| Research: search `TCS`, switch Swing and Positional, open each dossier folder | `belfort/research/` and `static/app.js` |
| Learn: open "Support and resistance", take the quiz | `content/learn/`, `belfort/learn/curriculum.py`, `static/verticals.js` |
| Practice: place a paper trade, log a prediction, play one replay | `belfort/practice/engine.py` (rules), `service.py` (accounts) |
| News: switch categories, hover an underlined word, show hidden tips | `belfort/news/feeds.py` |

## 3. Read these, in order (20 minutes)

1. [README.md](../README.md): what is built and what is not.
2. [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md): how the pieces fit, with a diagram.
3. [docs/COMPLIANCE.md](../docs/COMPLIANCE.md): the rules we design around. This shapes almost every feature decision.
4. [docs/SYLLABUS.md](../docs/SYLLABUS.md): how we choose what to teach.
5. [CONTRIBUTING.md](../CONTRIBUTING.md): our branch, PR and review flow.

## 4. Map of the code

| Folder | What lives there | Size |
|---|---|---|
| `belfort/main.py` | App factory: mounts five routers and the static front end | small |
| `belfort/settings.py` | Every threshold and preset | small |
| `belfort/core/` | Banned wording and disclaimer, the dictionary, SQLite and migrations | small |
| `belfort/data/` | Yahoo and NSE providers, the shared `market.bars()` and `market.lagged()`, disk cache | medium |
| `belfort/research/` | The rule engine and report from Belfort AI | large |
| `belfort/learn/` | Syllabus loader, Markdown renderer, quizzes, progress | medium |
| `belfort/practice/` | `engine.py` is pure and fully tested; `service.py` talks to the DB and data | medium |
| `belfort/news/` | RSS reader, categories, company tags, tip filter | small |
| `belfort/assistant/` | Bring-your-own-key provider adapter | small |
| `belfort/static/` | `index.html`, `app.js` (shell and research), `verticals.js` (the other three), `style.css` | large |
| `content/` | Lessons, syllabus, news feeds as plain files | grows |
| `tests/` | 68 offline tests; `conftest.py` gives every run its own empty data folder | |

## 5. Habits that matter here

- Run `pytest -q` before every push. Tests never touch the network.
- Any number a rule uses goes in `settings.py`.
- Any number on screen shows its source and date.
- Words like "buy now", "guaranteed" or "multibagger" fail the tests on purpose.
- Commit as yourself. No AI tool attribution lines in commits or PRs.

## 6. Your first week

Start with **T01** and **T02** in [TASKS.md](TASKS.md). They are small, touch most of the codebase, and end in a merged PR. Then take any task marked `Ready`.
