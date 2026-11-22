"""Check the Learn content before it ships. Run from the repository root:

    python scripts/ci/check_content.py            # checks content/learn
    python scripts/ci/check_content.py --root DIR  # checks another content folder (used by the tests)

Every lesson file must have front matter (title, minutes, objectives), a quiz of at least three valid questions,
known ::chart symbols and ::try targets, no banned wording, and a length that roughly matches its minutes. Every
syllabus lesson that is not marked planned must have a file, and every file must be in the syllabus and not planned.
Exit code 1 lists every problem found.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from belfort import settings  # noqa: E402
from belfort.core.compliance import find_banned  # noqa: E402

TRY_TARGETS = {"replay", "paper", "predict", "research"}
DIRECTIVE_RE = re.compile(r"^::(\w+)\s*(.*)$", re.M)
QUIZ_RE = re.compile(r"```quiz\s*(.*?)```", re.S)


def known_symbols() -> set[str]:
    """Symbols a lesson chart may use: the built-in company list plus the test listing fixture."""
    names = json.loads((ROOT / "content" / "symbols" / "companies.json").read_text(encoding="utf-8"))["companies"]
    symbols = {c["symbol"] for c in names}
    fixture = ROOT / "tests" / "fixtures" / "equity_listing.csv"
    if fixture.exists():
        with fixture.open(encoding="utf-8") as f:
            symbols |= {row["SYMBOL"].strip() for row in csv.DictReader(f)}
    return symbols


def _front_matter(text: str) -> tuple[dict, str] | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, parts[2]


def check_lesson(path: Path, symbols: set[str]) -> list[str]:
    """Problems in one lesson file, as sentences that name the file."""
    name, problems = path.name, []
    text = path.read_text(encoding="utf-8")
    parsed = _front_matter(text)
    if parsed is None:
        return [f"{name}: no front matter (a --- block with title, minutes and objectives)."]
    meta, body = parsed
    for key in ("title", "minutes", "objectives"):
        if not meta.get(key):
            problems.append(f"{name}: front matter is missing {key}.")
    minutes = int(meta["minutes"]) if meta.get("minutes", "").isdigit() else None
    if meta.get("minutes") and minutes is None:
        problems.append(f"{name}: minutes must be a whole number.")
    if meta.get("objectives") and len([o for o in meta["objectives"].split("|") if o.strip()]) < 2:
        problems.append(f"{name}: list at least two objectives, separated by |.")

    quiz_match = QUIZ_RE.search(body)
    if not quiz_match:
        problems.append(f"{name}: no ```quiz block.")
    else:
        try:
            quiz = json.loads(quiz_match.group(1))
        except json.JSONDecodeError as e:
            quiz = None
            problems.append(f"{name}: the quiz is not valid JSON ({e.msg}, line {e.lineno}).")
        if quiz is not None:
            if not isinstance(quiz, list) or len(quiz) < settings.CONTENT_MIN_QUIZ_QUESTIONS:
                problems.append(f"{name}: the quiz needs at least {settings.CONTENT_MIN_QUIZ_QUESTIONS} questions.")
            for i, q in enumerate(quiz if isinstance(quiz, list) else [], start=1):
                options = q.get("options") if isinstance(q, dict) else None
                if not isinstance(q, dict) or not q.get("q") or not isinstance(options, list) or len(options) < 2:
                    problems.append(f"{name}: quiz question {i} needs q and at least two options.")
                elif not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < len(options):
                    problems.append(f"{name}: quiz question {i} has an answer that is not one of its options.")
                elif not q.get("why"):
                    problems.append(f"{name}: quiz question {i} has no why (the explanation shown after answering).")
        body = body[: quiz_match.start()] + body[quiz_match.end() :]

    for kind, args in DIRECTIVE_RE.findall(body):
        parts = args.split()
        if kind == "chart":
            if len(parts) != 2 or not parts[1].isdigit():
                problems.append(f"{name}: write charts as ::chart SYMBOL BARS, not '::chart {args}'.")
            elif parts[0] not in symbols:
                problems.append(f"{name}: ::chart symbol {parts[0]} is not in the company list.")
        elif kind == "try" and (not parts or parts[0] not in TRY_TARGETS):
            problems.append(f"{name}: ::try must be one of {', '.join(sorted(TRY_TARGETS))}.")

    for phrase in find_banned(text):
        problems.append(f"{name}: banned wording '{phrase}'.")

    if minutes:
        words = len(re.findall(r"\w+", DIRECTIVE_RE.sub("", body)))
        low, high = settings.CONTENT_WORDS_PER_MINUTE
        if not low * minutes <= words <= high * minutes:
            problems.append(
                f"{name}: {words} words does not fit {minutes} minutes (expected {low * minutes} to {high * minutes}). "
                "Change minutes or the length."
            )
    return problems


def check_syllabus(learn_dir: Path) -> list[str]:
    """Files and syllabus entries must match: written lessons have files, planned ones do not."""
    syllabus = json.loads((learn_dir / "syllabus.json").read_text(encoding="utf-8"))
    entries = {
        lesson["id"]: lesson for track in syllabus["tracks"] for module in track["modules"] for lesson in module["lessons"]
    }
    files = {p.stem for p in (learn_dir / "lessons").glob("*.md")}
    problems = []
    for lesson_id, entry in entries.items():
        planned = entry.get("status") == "planned"
        if not planned and lesson_id not in files:
            problems.append(f"syllabus.json: {lesson_id} is not marked planned but lessons/{lesson_id}.md does not exist.")
        if planned and lesson_id in files:
            problems.append(f'syllabus.json: {lesson_id} has a file; remove "status": "planned" for it.')
    for stem in sorted(files - set(entries)):
        problems.append(f"lessons/{stem}.md is not in syllabus.json.")
    return problems


def check(learn_dir: Path) -> list[str]:
    symbols = known_symbols()
    problems = check_syllabus(learn_dir)
    for path in sorted((learn_dir / "lessons").glob("*.md")):
        problems += check_lesson(path, symbols)
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT / "content" / "learn", help="the content/learn folder to check")
    args = parser.parse_args(argv)
    problems = check(args.root)
    lessons = len(list((args.root / "lessons").glob("*.md")))
    if problems:
        print(f"Content check failed: {len(problems)} problem(s) in {lessons} lessons.")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"Content check passed: {lessons} lessons.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
