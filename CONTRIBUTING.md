# How we work

Belfort is a private repository shared by Sarthak and Devansh. This is our working agreement; change it by PR when it stops helping. Naming and Git rules are in [docs/CONVENTIONS.md](docs/CONVENTIONS.md).

## Roles

- **Devansh** builds the remaining app from [TEAM/TASKS.md](TEAM/TASKS.md). He owns each task end to end: build it, verify it, and **integrate it into `main`** once CI is green.
- **Sarthak** owns product decisions (the D-items in TASKS.md) and must approve changes to compliance, licence and CI files (see `.github/CODEOWNERS`). He reviews other PRs when he can; review is not a blocker for them.

## Flow for every task

1. **Pick** the next `Ready` task in TASKS.md. In your first commit, set its Owner and Status to `In progress`.
2. **Branch** from an up-to-date `main`: `feat/T03-stock-picker` (see conventions).
3. **Build** in small Conventional Commits. The pre-commit hooks format, lint and check messages.
4. **Verify** before opening the PR: lint, format, tests with coverage, and the feature in the running app. Write down what you checked.
5. **Open a PR** with the template. Request Sarthak's review if the PR touches a code-owned path or a product decision.
6. **CI must be green**: lint, tests on Windows and Linux, dependency audit, commit and PR policy.
7. **Merge** with "Squash and merge". The PR title is the commit message on `main`. Delete the branch.
8. **After merge**: pull `main`, run the app once, and confirm the task is marked Done with the PR link.

If `main` breaks, fixing it comes before any new task.

## Ground rules

1. **Compliance first.** Read [docs/COMPLIANCE.md](docs/COMPLIANCE.md). No buy, sell or hold advice, no price predictions, no promises of returns, no real money or prizes.
2. **Tests stay offline.** Fake every network source. Coverage must not drop below the threshold in `pyproject.toml`.
3. **Thresholds live in `belfort/settings.py`.**
4. **Show sources.** Any number on screen carries its source and as-of date, or is shown as missing with the reason.
5. **Plain English.** New terms go in `belfort/core/glossary.py` so they get hover explanations.
6. **No secrets in git.** Keys live in `.env` (ignored) or in the browser's Settings.
7. **No AI attribution** in commits or PRs, whatever tools you use.

## Writing a lesson

1. Create `content/learn/lessons/<id>.md` with front matter: `title`, `minutes`, `objectives` (separated by `|`).
2. Write the body in Markdown. Use `::chart SYMBOL BARS` for a past chart (always at least 30 days old) and `::try replay|paper|predict|research` for the hands-on step.
3. End with a ```quiz block: a JSON list of three or more questions, each with `q`, `options`, `answer` (index) and `why`.
4. Remove `"status": "planned"` for the lesson in `content/learn/syllabus.json`.
5. Run the tests (they check format, quiz and wording), then read the lesson in the app.

See [docs/SYLLABUS.md](docs/SYLLABUS.md) for what belongs in a lesson.

## Releasing (from v0.2 on)

1. Move the `Unreleased` entries in CHANGELOG.md under a new version heading; bump the version in `pyproject.toml` and `belfort/settings.py`. Merge that as `chore(release): vX.Y.Z`.
2. Tag `main`: `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. The release workflow builds and smoke-tests the Windows installer and attaches it to a GitHub Release (task T39).
