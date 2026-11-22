# Instructions for AI coding assistants in this repository

Belfort is a private pre-release, Windows-first desktop app (FastAPI backend + static HTML/CSS/JS front end + SQLite) with four parts: Research, Learn, Practice, News, plus a bring-your-own-key assistant. Read `README.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` and `docs/COMPLIANCE.md` before changing code.

## Hard rules

1. **No AI attribution, ever.** Do not add `Co-Authored-By` trailers for any AI, "Generated with Claude Code" footers, or similar lines to commits, PR titles or PR bodies. Commits are made under the human developer's own git identity. CI rejects attribution, and so does the commit-msg hook.
2. **Compliance.** Never write buy, sell or hold advice, price predictions or promises of returns into the app, lessons or docs. Practice uses virtual points only: never anything redeemable, no prizes, no paid entry. Learning content that shows a named stock's chart uses `::chart` (prices at least 30 days old). Changes to `belfort/core/compliance.py` or `docs/COMPLIANCE.md` need Sarthak's approval.
3. **Work from the task list.** Tasks live in `TEAM/TASKS.md`. One task per branch and per PR. Set the task's Owner and Status when you start, and move it to Done with the PR link in the same PR that finishes it.
4. **Conventions.** Follow `docs/CONVENTIONS.md` for names, branches (`feat/T03-stock-picker`), Conventional Commit messages and PR titles (`feat(practice): add stock picker (T03)`).
5. **Tests stay offline.** Fake every network source. Add tests with every behaviour change.

## Commands (Windows, from the repo root)

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\pre-commit install --hook-type pre-commit --hook-type commit-msg
.venv\Scripts\ruff check . ; .venv\Scripts\ruff format .
.venv\Scripts\python -m pytest --cov
.venv\Scripts\python -m uvicorn belfort.main:app --port 8765 --reload
```

## Definition of done for every task

- `ruff check .`, `ruff format --check .` and `pytest --cov` pass locally (coverage must not drop below the threshold in `pyproject.toml`).
- The change was exercised in the running app, not only in tests, and the PR says how.
- `CHANGELOG.md` has a line under Unreleased for anything a user would notice.
- Docs updated where behaviour changed (README "What is built", `TEAM/STATUS.md`, architecture).
- The PR passes every CI job before merge. Squash merge; delete the branch.
