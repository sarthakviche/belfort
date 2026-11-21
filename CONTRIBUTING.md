# How we work

Belfort is a private repository shared by Sarthak and Devansh. This is our working agreement. Change it when it stops helping.

## Flow

1. **Pick a task** from [TEAM/TASKS.md](TEAM/TASKS.md). Put your name in its `Owner` field in the same commit as your first change, so we never both start the same thing.
2. **Branch from `main`:** `<name>/<task-id>-<short-title>`, for example `devansh/T03-moving-averages-lesson`.
3. **Keep commits small** and messages in the imperative: "Add volume lesson", "Fix limit order expiry".
4. **Open a pull request** into `main` using the template. The other founder reviews. Merge when CI is green and one of us has approved. Nobody pushes straight to `main` except for typo-level fixes.
5. **Tick the task** in TASKS.md (move it to Done with the PR link) as part of the PR.

## Ground rules

1. **Read [docs/COMPLIANCE.md](docs/COMPLIANCE.md).** No buy, sell or hold advice, no price predictions, no promises of returns, no real money or prizes. A test scans pages and lessons for promise wording.
2. **Tests stay offline.** Replace every network source with synthetic data, as the existing tests do. `python -m pytest -q` must pass before review.
3. **Thresholds live in `belfort/settings.py`.** A rule that uses a number names it there.
4. **Show sources.** Any new number on screen carries its source and as-of date, or is shown as missing with the reason.
5. **Plain English.** Short sentences. New terms go in `belfort/core/glossary.py` so they get hover explanations.
6. **No secrets in git.** Keys live in `.env` (ignored) or in the browser's Settings.

## Writing a lesson

1. Create `content/learn/lessons/<id>.md` with front matter: `title`, `minutes`, `objectives` (separated by `|`).
2. Write the body in Markdown. Use `::chart SYMBOL BARS` for a past chart (always at least 30 days old) and `::try replay|paper|predict|research` for the hands-on step.
3. End with a ```quiz block: a JSON list of three or more questions, each with `q`, `options`, `answer` (index) and `why`.
4. Remove `"status": "planned"` for the lesson in `content/learn/syllabus.json`.
5. Run the tests: they check format, quiz and wording. Then read it in the app.

See [docs/SYLLABUS.md](docs/SYLLABUS.md) for what belongs in a lesson.
