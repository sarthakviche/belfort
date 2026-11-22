"""Commit and pull request policy, used by CI and by the local commit-msg hook.

Rules:
  1. Subjects follow Conventional Commits: type(scope)?: summary   e.g. "feat(practice): add stock picker (T03)"
  2. No AI-tool attribution anywhere: no "Co-Authored-By" lines for AI assistants, no "Generated with ..." footers.

Usage:
  python scripts/ci/check_commit_policy.py --message-file .git/COMMIT_EDITMSG    (commit-msg hook)
  python scripts/ci/check_commit_policy.py --range origin/main..HEAD              (CI: every commit in a PR)
  python scripts/ci/check_commit_policy.py --pr-title "..." --pr-body-file body.md (CI: the PR itself)
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert", "content")
SUBJECT_RE = re.compile(rf"^({'|'.join(TYPES)})(\([a-z0-9-]+\))?!?: \S.{{0,98}}$")
ATTRIBUTION_RE = re.compile(
    r"(co-authored-by:.*(claude|anthropic|copilot|chatgpt|openai|gemini|cursor|codeium|devin)"
    r"|generated (with|by) .*(claude|copilot|chatgpt|ai\b|cursor)"
    r"|noreply@anthropic\.com)",
    re.IGNORECASE,
)
ALLOWED_AUTOMATIC = ("Merge ", "Revert ", "fixup! ", "squash! ")


def check_subject(subject: str, where: str) -> list[str]:
    if subject.startswith(ALLOWED_AUTOMATIC):
        return []
    if SUBJECT_RE.match(subject):
        return []
    return [
        f"{where}: subject must follow Conventional Commits, e.g. 'feat(practice): add stock picker (T03)'. "
        f"Allowed types: {', '.join(TYPES)}. Got: {subject!r}"
    ]


def check_attribution(text: str, where: str) -> list[str]:
    hits = [m.group(0) for m in ATTRIBUTION_RE.finditer(text)]
    return [f"{where}: remove AI-tool attribution ({h!r}). Commits go out under the author's own name only." for h in hits]


def check_message(message: str, where: str) -> list[str]:
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    subject = lines[0].strip() if lines else ""
    return check_subject(subject, where) + check_attribution("\n".join(lines), where)


def commits_in(rev_range: str) -> list[tuple[str, str]]:
    out = subprocess.run(
        ["git", "log", "--format=%H%x00%B%x01", rev_range], capture_output=True, text=True, check=True, encoding="utf-8"
    ).stdout
    commits = []
    for chunk in out.split("\x01"):
        if "\x00" in chunk:
            sha, body = chunk.strip("\n").split("\x00", 1)
            commits.append((sha.strip()[:10], body))
    return commits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--message-file")
    ap.add_argument("--range")
    ap.add_argument("--pr-title")
    ap.add_argument("--pr-body-file")
    args = ap.parse_args(argv)

    errors: list[str] = []
    if args.message_file:
        errors += check_message(Path(args.message_file).read_text(encoding="utf-8"), "commit message")
    if args.range:
        for sha, body in commits_in(args.range):
            errors += check_message(body, f"commit {sha}")
    if args.pr_title is not None:
        errors += check_subject(args.pr_title.strip(), "PR title")
    if args.pr_body_file:
        errors += check_attribution(Path(args.pr_body_file).read_text(encoding="utf-8"), "PR description")

    for e in errors:
        print(f"::error::{e}" if "GITHUB_ACTIONS" in os.environ else e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
