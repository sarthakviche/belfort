# Onboarding: Devansh

> Temporary file for the founders. Delete or move to the wiki before any public release.

Welcome. This page gets you from clone to your first pull request in about an hour.

## 1. Run it (15 minutes)

```powershell
git clone https://github.com/sarthakviche/belfort.git
cd belfort
git config user.name "Your Name"            # commits go out under your own name
git config user.email "you@example.com"     # an email verified on your GitHub account
py -3.12 -m venv .venv                      # the py launcher picks 3.12 even if another Python is the default
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\pre-commit install --hook-type pre-commit --hook-type commit-msg
.venv\Scripts\python -m pytest --cov
.venv\Scripts\python -m uvicorn belfort.main:app --port 8765 --reload
```

Every test should pass, with coverage above the threshold in `pyproject.toml`. Open <http://localhost:8765>. You need Python 3.12 (exactly 3.12, as in CI), Node.js for the JavaScript syntax check, the GitHub CLI (`gh`) for pull requests, and an internet connection (prices and news are fetched live; the tests are not).

Before every push, run the same checks CI runs (from Git Bash or WSL for the loop; in PowerShell use `Get-ChildItem belfort\static\*.js | % { node --check $_ }`):

```bash
.venv/Scripts/ruff check . && .venv/Scripts/ruff format --check .
for f in belfort/static/*.js; do node --check "$f"; done
.venv/Scripts/python -m pytest --cov
```

The pre-commit hooks format and lint every commit and reject commit messages that are not Conventional Commits or that carry AI-tool attribution. Read [docs/CONVENTIONS.md](../docs/CONVENTIONS.md) before your first commit.

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
5. [CONTRIBUTING.md](../CONTRIBUTING.md): roles, and the branch, PR, CI and merge flow you own.
6. [docs/CONVENTIONS.md](../docs/CONVENTIONS.md): naming, Conventional Commits, versions.
7. [CLAUDE.md](../CLAUDE.md): the rules any AI assistant you use must follow here.

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
| `tests/` | Offline tests; `conftest.py` gives every run its own empty data folder | |

## 5. Habits that matter here

- Run `pytest -q` before every push. Tests never touch the network.
- Any number a rule uses goes in `settings.py`.
- Any number on screen shows its source and date.
- Words like "buy now", "guaranteed" or "multibagger" fail the tests on purpose.
- Commit as yourself. No AI tool attribution lines in commits or PRs.

## 6. Your first week

Start with **T01** and **T02** in [TASKS.md](TASKS.md). They are small, touch most of the codebase, and end in a merged PR. Then **T03, the stock picker**, which is the most visible fix in the app. After that, work through the phases in order: the goal is Belfort 1.0 as a Windows installer (T40).

If you use an AI coding assistant, paste the prompt in [START_PROMPT.md](START_PROMPT.md) into it.
