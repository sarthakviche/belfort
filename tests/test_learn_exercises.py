"""Every written lesson carries the new exercise types, and each item is well formed (T49)."""

from belfort.core import compliance
from belfort.learn import curriculum as c


def _written():
    for f in sorted((c.LEARN / "lessons").glob("*.md")):
        yield f.stem, c.questions(f.stem)


def test_every_lesson_has_two_kinds_of_new_exercise():
    seen = 0
    for lid, qs in _written():
        new = [q for q in qs if q["type"] != "mc"]
        assert len(new) >= 2, lid
        assert len({q["type"] for q in new}) >= 2, lid
        seen += 1
    assert seen == 38


def test_exercises_have_a_reason_and_clean_wording():
    for lid, qs in _written():
        for q in qs:
            assert q["why"].strip(), (lid, q["q"])
            assert not compliance.find_banned(q["q"] + " " + q["why"]), (lid, q["q"])
            if q["type"] == "number":
                assert q["tolerance"] >= 0
