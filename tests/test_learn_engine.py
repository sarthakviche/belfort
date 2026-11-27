"""The Learn game rules: pure functions, dates passed in, no database and no clock."""

import random

from belfort.learn import engine
from belfort.learn.engine import Profile
from belfort.settings import HEARTS_MAX


def test_hearts_refill_on_a_new_day_only():
    p = Profile(hearts=2, hearts_day="2026-11-27")
    assert engine.refill_hearts(p, "2026-11-27").hearts == 2
    assert engine.refill_hearts(p, "2026-11-28").hearts == HEARTS_MAX
    assert engine.refill_hearts(Profile(hearts=0), "2026-11-28").hearts_day == "2026-11-28"


def test_a_wrong_answer_costs_a_heart_and_never_goes_below_zero():
    p = Profile(hearts=1)
    p = engine.lose_heart(p)
    assert p.hearts == 0 and not engine.can_start_lesson(p)
    assert engine.lose_heart(p).hearts == 0
    assert engine.restore_hearts(p, "2026-11-27").hearts == HEARTS_MAX


def test_lesson_xp_is_ten_plus_five_for_no_mistakes_and_less_on_replay():
    assert engine.lesson_xp(True, 1) == 10
    assert engine.lesson_xp(True, 0) == 15
    assert engine.lesson_xp(False, 0) == engine.lesson_xp(False, 3) == 5


def test_streak_starts_when_the_daily_goal_is_first_reached():
    p = Profile(goal=20)
    p = engine.award_xp(p, 0, 15, "2026-11-27")
    assert p.xp_total == 15 and p.streak == 0  # goal not reached yet
    p = engine.award_xp(p, 15, 10, "2026-11-27")
    assert p.xp_total == 25 and p.streak == 1 and p.last_goal_day == "2026-11-27"
    again = engine.award_xp(p, 25, 10, "2026-11-27")
    assert again.streak == 1  # more XP the same day does not count twice


def test_streak_grows_on_consecutive_days_and_resets_after_a_gap():
    p = Profile(goal=10, streak=3, last_goal_day="2026-11-26")
    assert engine.award_xp(p, 0, 10, "2026-11-27").streak == 4
    assert engine.award_xp(p, 0, 10, "2026-11-29").streak == 1  # one missed day, no freeze held


def test_a_freeze_is_spent_automatically_for_a_missed_day():
    p = Profile(goal=10, streak=5, last_goal_day="2026-11-25", freezes=1)
    after = engine.award_xp(p, 0, 10, "2026-11-27")  # 26th missed
    assert after.streak == 6 and after.freezes == 0
    two_missed = Profile(goal=10, streak=5, last_goal_day="2026-11-24", freezes=1)
    assert engine.award_xp(two_missed, 0, 10, "2026-11-27").streak == 1  # one freeze cannot cover two days


def test_a_freeze_is_earned_every_seven_days_up_to_two():
    p = Profile(goal=10, streak=6, last_goal_day="2026-11-26", freezes=0)
    p = engine.award_xp(p, 0, 10, "2026-11-27")
    assert p.streak == 7 and p.freezes == 1
    p = Profile(goal=10, streak=13, last_goal_day="2026-11-26", freezes=2)
    assert engine.award_xp(p, 0, 10, "2026-11-27").freezes == 2  # capped at two held


def test_streak_shown_today_stays_alive_while_freezes_cover_the_gap():
    p = Profile(streak=4, last_goal_day="2026-11-26", freezes=0)
    assert engine.streak_now(p, "2026-11-26") == 4
    assert engine.streak_now(p, "2026-11-27") == 4 and engine.streak_at_risk(p, "2026-11-27")
    assert engine.streak_now(p, "2026-11-28") == 0  # a day was missed and no freeze held
    assert engine.streak_now(Profile(streak=4, last_goal_day="2026-11-26", freezes=1), "2026-11-28") == 4
    assert engine.streak_now(Profile(), "2026-11-28") == 0


def test_stage_unlock_rules():
    assert engine.unlocked_stages({}) == ["beginner"]
    assert engine.unlocked_stages({"stage:beginner": 0.79}) == ["beginner"]
    assert engine.unlocked_stages({"stage:beginner": 0.8}) == ["beginner", "intermediate"]
    assert engine.unlocked_stages({"placement:beginner": 0.9}) == ["beginner", "intermediate"]
    # Advanced needs the Intermediate stage test; the Beginner placement test does not open it.
    assert engine.unlocked_stages({"placement:beginner": 1.0}) == ["beginner", "intermediate"]
    both = {"placement:beginner": 1.0, "stage:intermediate": 0.85}
    assert engine.unlocked_stages(both) == ["beginner", "intermediate", "advanced"]
    assert engine.unlocked_stages({"stage:intermediate": 1.0}) == ["beginner"]  # cannot skip a stage


def test_pass_mark_is_eighty_percent():
    assert engine.passed(0.8) and engine.passed(10 / 12 + 0.001)
    assert not engine.passed(9 / 12)  # 75%


def test_sample_refs_spreads_across_lessons_and_never_repeats():
    refs = engine.sample_refs({"a": 5, "b": 5, "c": 5}, 6, random.Random(1))
    assert len(refs) == len(set(refs)) == 6
    assert {r.split(":")[0] for r in refs} == {"a", "b", "c"}
    assert len(engine.sample_refs({"a": 2}, 10, random.Random(1))) == 2  # fewer questions than asked for
    assert engine.parse_ref("position-sizing:3") == ("position-sizing", 3)


MODULES = [
    {"id": "m1", "title": "One", "why": "", "stage": "beginner", "lessons": [
        {"id": "a", "title": "A", "written": True}, {"id": "b", "title": "B", "written": True},
        {"id": "s", "title": "Soon", "written": False}]},
    {"id": "m2", "title": "Two", "why": "", "stage": "intermediate", "lessons": [{"id": "c", "title": "C", "written": True}]},
    {"id": "m3", "title": "Three", "why": "", "stage": "advanced", "lessons": []},
]  # fmt: skip


def _states(stages, stage):
    s = next(x for x in stages if x["key"] == stage)
    return [(n["id"], n["state"]) for m in s["modules"] for n in m["nodes"]] + [("test", s["test"]["state"])]


def test_new_learner_path_has_one_next_node_and_locked_later_stages():
    stages = engine.build_path(MODULES, set(), set(), ["beginner"], set())
    assert _states(stages, "beginner") == [("a", "next"), ("b", "open"), ("s", "soon"), ("m1", "waiting"), ("test", "waiting")]
    assert _states(stages, "intermediate") == [("c", "locked"), ("m2", "locked"), ("test", "locked")]
    assert stages[1]["unlocked"] is False and stages[0]["lessons_total"] == 2  # soon lessons are not counted


def test_path_moves_the_next_marker_and_opens_checkpoint_then_stage_test():
    stages = engine.build_path(MODULES, {"a", "b"}, {"a"}, ["beginner"], set())
    nodes = {n["id"]: n for m in stages[0]["modules"] for n in m["nodes"]}
    assert nodes["a"]["perfect"] is True and nodes["b"]["perfect"] is False
    assert nodes["m1"]["state"] == "next"  # checkpoint is the next thing to do
    assert stages[0]["test"]["state"] == "open"
    stages = engine.build_path(MODULES, {"a", "b"}, set(), ["beginner"], {"checkpoint:m1"})
    assert stages[0]["test"]["state"] == "next"
    stages = engine.build_path(MODULES, {"a", "b"}, set(), ["beginner", "intermediate"], {"checkpoint:m1", "stage:beginner"})
    assert stages[0]["test"]["state"] == "done"
    assert _states(stages, "intermediate")[0] == ("c", "next")


def test_a_module_with_no_written_lessons_shows_coming_soon():
    stages = engine.build_path(MODULES, set(), set(), ["beginner", "intermediate", "advanced"], set())
    assert _states(stages, "advanced") == [("m3", "soon"), ("test", "waiting")]
