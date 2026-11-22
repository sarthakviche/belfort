"""scripts/ci/check_content.py: passes on the real content, fails loudly on broken lessons."""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_content", ROOT / "scripts" / "ci" / "check_content.py")
check_content = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_content)


@pytest.fixture
def learn(tmp_path):
    """A copy of content/learn that a test can break."""
    target = tmp_path / "learn"
    shutil.copytree(ROOT / "content" / "learn", target)
    return target


def _rewrite(path: Path, old: str, new: str):
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_real_content_passes():
    assert check_content.check(ROOT / "content" / "learn") == []
    assert check_content.main([]) == 0


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("title: Support and resistance\n", "", "front matter is missing title"),
        ("minutes: 8\n", "minutes: eight\n", "minutes must be a whole number"),
        ("::chart ICICIBANK 200", "::chart NOTASTOCK 200", "symbol NOTASTOCK is not in the company list"),
        ("::chart ICICIBANK 200", "::chart ICICIBANK", "write charts as ::chart SYMBOL BARS"),
        ("Levels describe where", "This is a sure shot. Levels describe where", "banned wording"),
        ("```quiz", "```quiz\n[{]\n```\n```ignored", "not valid JSON"),
        ("minutes: 8\n", "minutes: 40\n", "does not fit 40 minutes"),
    ],
)
def test_broken_lesson_fails_with_a_clear_message(learn, capsys, old, new, expected):
    _rewrite(learn / "lessons" / "support-resistance.md", old, new)
    problems = check_content.check(learn)
    assert any(expected in p and "support-resistance.md" in p for p in problems), problems
    assert check_content.main(["--root", str(learn)]) == 1
    assert "Content check failed" in capsys.readouterr().out


def test_quiz_needs_three_valid_questions(learn):
    path = learn / "lessons" / "trend.md"
    text = path.read_text(encoding="utf-8")
    start, end = text.index("```quiz") + len("```quiz"), text.rindex("```")
    quiz = json.loads(text[start:end])
    quiz[0]["answer"] = 9
    del quiz[1]["why"]
    path.write_text(text[:start] + "\n" + json.dumps(quiz[:2]) + "\n" + text[end:], encoding="utf-8")
    problems = " ".join(check_content.check(learn))
    assert "at least 3 questions" in problems and "answer that is not one of its options" in problems and "has no why" in problems


def test_syllabus_and_files_must_match(learn):
    (learn / "lessons" / "stray-lesson.md").write_text("---\ntitle: x\n---\n", encoding="utf-8")
    (learn / "lessons" / "candles.md").unlink()
    syllabus = json.loads((learn / "syllabus.json").read_text(encoding="utf-8"))
    lessons = [entry for t in syllabus["tracks"] for m in t["modules"] for entry in m["lessons"]]
    planned = next(entry for entry in lessons if entry.get("status") == "planned")
    (learn / "lessons" / f"{planned['id']}.md").write_text(
        (learn / "lessons" / "trend.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    problems = " ".join(check_content.check(learn))
    assert "candles is not marked planned but lessons/candles.md does not exist" in problems
    assert "stray-lesson.md is not in syllabus.json" in problems
    assert f'{planned["id"]} has a file; remove "status": "planned"' in problems
