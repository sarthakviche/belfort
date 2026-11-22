# Conventions

How we name things, write code and ship. CI enforces what it can (Ruff lint and format, tests, coverage, commit policy); review enforces the rest.

## Naming

### Python (PEP 8, enforced by Ruff's `N` rules)

| Thing | Style | Example |
|---|---|---|
| Package, module, file | `snake_case` | `belfort/practice/engine.py` |
| Function, method, variable, argument | `snake_case`, a verb for functions | `settle_trade()`, `risk_per_share` |
| Class, dataclass, exception | `PascalCase`; exceptions end in `Error` | `Provider`, `PracticeError` |
| Module constant | `UPPER_SNAKE_CASE` | `EDU_LAG_DAYS`, `PAPER_START_POINTS` |
| Private helper | leading underscore | `_last_closes()` |
| Boolean | reads as a yes/no question | `is_open`, `has_target`, `passed` |
| Units in the name when not obvious | suffix | `stop_pct`, `ttl_seconds`, `horizon_days`, `market_cap_cr` |

- No single-letter names except loop indices (`i`, `j`), coordinates and well-known math (`df` for a DataFrame is fine).
- No abbreviations a newcomer has to guess. `qty`, `pct`, `atr`, `eod` are fine; `tmp2`, `res_x` are not.
- Money: rupee amounts are `float` until display; format with `₹` only in the UI or in generated sentences. Practice money is `points`, never `rupees` or `cash` in user-facing text.
- Dates cross boundaries (JSON, DB) as ISO strings `YYYY-MM-DD`.
- Every threshold a rule uses is a named constant in `belfort/settings.py`.
- Public functions have type hints and a one-line docstring saying what, not how.

### JavaScript (front end, no build step)

| Thing | Style | Example |
|---|---|---|
| File | `kebab-case.js` | `stock-picker.js` |
| Function, variable | `camelCase` | `renderPortfolio()`, `chatContext` |
| Constant | `UPPER_SNAKE_CASE` | `FILES_KEY`, `VIEWS` |
| DOM id, CSS class, `data-*` attribute | `kebab-case` | `#order-form`, `.lesson-chart`, `data-lesson` |
| localStorage key | `belfort` + `PascalCase` | `belfortAI`, `belfortFiles` |

- Escape every value you put in HTML with `esc()`. Links go through `safeUrl()`.
- Use the existing helpers (`api`, `post`, `inr`, `num`, `glossify`) instead of re-writing them.

### API and data

| Thing | Style | Example |
|---|---|---|
| Route | `/api/<vertical>/<resource>`, plural nouns, `kebab-case` | `/api/practice/trades`, `/api/practice/replay/new` |
| JSON keys | `snake_case` | `entry_price`, `label_key` |
| Errors | HTTP status + `{"detail": "a sentence the user can act on"}` | `400 {"detail": "The stop must be below the entry price."}` |
| SQLite table | plural `snake_case` | `trades`, `lesson_progress` |
| SQLite column | `snake_case`; dates as ISO text | `placed_on`, `exit_reason` |
| Migration | append a new entry to `MIGRATIONS`; never edit an old one | |
| Lesson id, feed id | `kebab-case` | `position-sizing`, `et-markets` |
| Environment variable | `UPPER_SNAKE_CASE`, new ones prefixed `BELFORT_` | `BELFORT_DATA_DIR` |

### Tests

- File `tests/test_<area>.py`; test `test_<unit>_<expected_behaviour>`, e.g. `test_gap_below_stop_exits_at_open_not_stop`.
- Tests never touch the network. Fake providers as `tests/test_app.py` and `tests/test_verticals.py` do.

## Git and GitHub

### Branches

`<type>/<task-id>-<short-kebab-title>`, branched from `main`, for example:

```
feat/T03-stock-picker
content/T12-setups-lessons
fix/T09-replay-hidden-bars
ci/T30-release-workflow
```

### Commits and PR titles: Conventional Commits

```
<type>(<scope>): <summary in the imperative, lower case, no full stop> (<task-id>)
```

- **Types:** `feat` new capability · `fix` bug fix · `content` lessons, syllabus, feeds · `docs` · `refactor` · `perf` · `test` · `build` dependencies or packaging · `ci` · `style` formatting only · `chore` · `revert`
- **Scopes:** `research`, `learn`, `practice`, `news`, `assistant`, `core`, `data`, `ui`, `installer`, `deps`
- **Breaking change:** `!` after the type, plus a `BREAKING CHANGE:` line in the body.
- Example: `feat(practice): add fuzzy stock picker to the order form (T03)`
- **No AI attribution.** Never add `Co-Authored-By` lines for AI tools or "Generated with" footers. The commit-msg hook and CI reject them.

### Pull requests

- One task per PR. Keep it under about 400 changed lines of code where possible (lessons excepted); split larger tasks.
- Fill the template, including **How I verified it**.
- **Squash merge** only. The PR title becomes the commit on `main`, so it must be a valid Conventional Commit.
- The branch is deleted after merge.

### Versions and releases

- [Semantic Versioning](https://semver.org): `MAJOR.MINOR.PATCH`. Before 1.0, a minor bump may break things.
- The version lives in two places that must match: `pyproject.toml` and `belfort/settings.py::VERSION`.
- Every user-visible change adds a line under `Unreleased` in [CHANGELOG.md](../CHANGELOG.md) in the same PR.
- A release is a tag `vX.Y.Z` on `main`; the release workflow (task T39) builds the Windows installer from that tag.
