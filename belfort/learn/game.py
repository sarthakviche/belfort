"""The Learn game on top of the pure rules in engine.py: a thin SQLite layer for profile, lessons, tests and weak spots.

Everything is scoped by `user_id` (core/users.py). XP, hearts and streaks are virtual and never redeemable.
Locked stages are enforced here, on the server, so a page cannot read or grade a lesson it has not unlocked.
"""

import json
import random
import sqlite3
import uuid
from datetime import date

from ..core import db
from ..core.users import LOCAL_USER
from ..settings import (
    CHECKPOINT_QUESTIONS,
    DAILY_GOALS,
    HEARTS_MAX,
    LESSON_PASS_RATIO,
    PLACEMENT_QUESTIONS,
    STAGE_PASS_RATIO,
    STAGE_TEST_QUESTIONS,
    STAGES,
    WEAK_SPOTS_QUESTIONS,
    XP_TEST,
    XP_WEAK_SPOTS,
)
from . import curriculum, engine
from .curriculum import LearnError
from .engine import Profile

TEST_KINDS = ("checkpoint", "stage", "placement")


class LockedError(LearnError):
    """The stage this belongs to is not unlocked yet."""


class NoHeartsError(LearnError):
    """No hearts left today."""


class NotReadyError(LearnError):
    """The learner has not done what this needs yet."""


def _today() -> str:
    return date.today().isoformat()


# ---------------- loading and saving ----------------


def _load(con: sqlite3.Connection, user: str, today: str) -> tuple[Profile, bool]:
    """The learner's profile with today's hearts, and whether the placement offer was already handled."""
    row = con.execute("SELECT * FROM learn_profile WHERE user_id=?", (user,)).fetchone()
    if row is None:
        con.execute("INSERT INTO learn_profile (user_id, hearts_day) VALUES (?, ?)", (user, today))
        row = con.execute("SELECT * FROM learn_profile WHERE user_id=?", (user,)).fetchone()
    profile = Profile(
        xp_total=row["xp_total"],
        goal=row["goal"],
        hearts=row["hearts"],
        hearts_day=row["hearts_day"],
        streak=row["streak"],
        last_goal_day=row["last_goal_day"],
        freezes=row["freezes"],
    )
    refilled = engine.refill_hearts(profile, today)
    if refilled != profile:
        _save(con, user, refilled)
    return refilled, bool(row["placement_seen"])


def _save(con: sqlite3.Connection, user: str, p: Profile):
    con.execute(
        "UPDATE learn_profile SET xp_total=?, goal=?, hearts=?, hearts_day=?, streak=?, last_goal_day=?, freezes=? "
        "WHERE user_id=?",
        (p.xp_total, p.goal, p.hearts, p.hearts_day, p.streak, p.last_goal_day, p.freezes, user),
    )


def _xp_today(con: sqlite3.Connection, user: str, today: str) -> int:
    row = con.execute("SELECT xp FROM learn_xp_days WHERE user_id=? AND day=?", (user, today)).fetchone()
    return row["xp"] if row else 0


def _give_xp(con: sqlite3.Connection, user: str, profile: Profile, xp: int, today: str) -> Profile:
    before = _xp_today(con, user, today)
    con.execute(
        "INSERT INTO learn_xp_days (user_id, day, xp) VALUES (?,?,?) ON CONFLICT(user_id, day) DO UPDATE SET xp=xp+?",
        (user, today, xp, xp),
    )
    updated = engine.award_xp(profile, before, xp, today)
    _save(con, user, updated)
    return updated


def _done_scores(con: sqlite3.Connection, user: str) -> dict[str, float]:
    """Best quiz score per completed lesson. Lessons finished before the game existed (lesson_progress) count as done
    for the local user."""
    scores: dict[str, float] = {}
    if user == LOCAL_USER:
        for r in con.execute("SELECT lesson_id, quiz_score FROM lesson_progress"):
            scores[r["lesson_id"]] = r["quiz_score"] or 0.0
    for r in con.execute("SELECT lesson_id, best_score FROM learn_lessons WHERE user_id=?", (user,)):
        scores[r["lesson_id"]] = max(scores.get(r["lesson_id"], 0.0), r["best_score"])
    return scores


def _test_scores(con: sqlite3.Connection, user: str) -> tuple[dict[str, float], set[str]]:
    scores, passed = {}, set()
    for r in con.execute("SELECT kind, key, best_score, passed FROM learn_tests WHERE user_id=?", (user,)):
        k = engine.score_key(r["kind"], r["key"])
        scores[k] = r["best_score"]
        if r["passed"]:
            passed.add(k)
    return scores, passed


def _summary(con: sqlite3.Connection, user: str, profile: Profile, today: str) -> dict:
    xp_today = _xp_today(con, user, today)
    weak = con.execute("SELECT COUNT(*) AS n FROM learn_weak WHERE user_id=?", (user,)).fetchone()["n"]
    return {
        "xp_total": profile.xp_total,
        "xp_today": xp_today,
        "goal": profile.goal,
        "goal_met": xp_today >= profile.goal,
        "hearts": profile.hearts,
        "hearts_max": HEARTS_MAX,
        "streak": engine.streak_now(profile, today),
        "streak_at_risk": engine.streak_at_risk(profile, today),
        "freezes": profile.freezes,
        "weak_spots": weak,
    }


def _unlocked(con: sqlite3.Connection, user: str) -> list[str]:
    scores, _ = _test_scores(con, user)
    return engine.unlocked_stages(scores)


def _lock_message(stage: str) -> str:
    before = STAGES[STAGES.index(stage) - 1]
    msg = f"The {stage.capitalize()} stage is locked. Pass the {before.capitalize()} stage test with {round(STAGE_PASS_RATIO * 100)}% or more"
    if before == STAGES[0]:
        msg += ", or test out of Beginner with the placement test,"
    return msg + f" to open it. Finish the {before.capitalize()} stage first."


# ---------------- the path ----------------


def path(user: str) -> dict:
    """Everything the Learn page draws: the learner's numbers, the stages with their nodes, and the placement offer."""
    today = _today()
    with db.connect() as con:
        profile, placement_seen = _load(con, user, today)
        scores = _done_scores(con, user)
        _, tests_passed = _test_scores(con, user)
        unlocked = _unlocked(con, user)
        summary = _summary(con, user, profile, today)
    modules = curriculum.stage_modules()
    stages = engine.build_path(modules, set(scores), {k for k, v in scores.items() if v >= 0.999}, unlocked, tests_passed)
    nxt = next(
        (
            {"kind": n["kind"], "id": n["id"], "title": n["title"]}
            for s in stages
            for n in [x for m in s["modules"] for x in m["nodes"]] + [s["test"]]
            if n["state"] == "next"
        ),
        None,
    )
    written = [x for m in modules for x in m["lessons"] if x["written"]]
    return {
        "profile": summary,
        "stages": stages,
        "next": nxt,
        "placement_offered": not placement_seen and STAGES[1] not in unlocked,
        "goals": list(DAILY_GOALS),
        "lessons_done": sum(1 for x in written if x["id"] in scores),
        "lessons_written": len(written),
    }


# ---------------- locks ----------------


def ensure_open(user: str, lesson_id: str):
    """Raise LockedError unless the lesson's stage is unlocked for this learner."""
    stage = curriculum.lesson_info(lesson_id)["stage"]
    with db.connect() as con:
        _load(con, user, _today())
        if stage not in _unlocked(con, user):
            raise LockedError(_lock_message(stage))


def ensure_can_start(user: str, lesson_id: str):
    """Out of hearts: only lessons already completed can still be opened (to reread)."""
    with db.connect() as con:
        profile, _ = _load(con, user, _today())
        if profile.hearts == 0 and lesson_id not in _done_scores(con, user):
            raise NoHeartsError(
                "You are out of hearts for today. Finish a Weak spots review to refill them, or come back tomorrow."
            )


# ---------------- lessons ----------------


def check_question(user: str, lesson_id: str, index: int, answer) -> dict:
    """Grade one exercise now. A wrong answer costs a heart and is remembered for the Weak spots review."""
    ensure_open(user, lesson_id)
    quiz = curriculum.questions(lesson_id)
    if not 0 <= index < len(quiz):
        raise LearnError("No such question.")
    today = _today()
    with db.connect() as con:
        profile, _ = _load(con, user, today)
        if not engine.can_start_lesson(profile):
            raise NoHeartsError("You are out of hearts for today. Finish a Weak spots review to refill them.")
        result = curriculum.check_answer(quiz[index], answer)
        if result["correct"]:
            con.execute("DELETE FROM learn_weak WHERE user_id=? AND lesson_id=? AND q_index=?", (user, lesson_id, index))
        else:
            profile = engine.lose_heart(profile)
            _save(con, user, profile)
            con.execute(
                "INSERT INTO learn_weak (user_id, lesson_id, q_index, last_wrong) VALUES (?,?,?,?) "
                "ON CONFLICT(user_id, lesson_id, q_index) DO UPDATE SET wrong_count=wrong_count+1, last_wrong=?",
                (user, lesson_id, index, today, today),
            )
    return {**result, "hearts": profile.hearts, "hearts_max": HEARTS_MAX, "out_of_hearts": profile.hearts == 0}


def complete_lesson(user: str, lesson_id: str, answers: list) -> dict:
    """Grade the whole quiz, mark the lesson done at 60% or more, and award XP."""
    ensure_open(user, lesson_id)
    quiz = curriculum.questions(lesson_id)
    graded = curriculum.grade_answers(quiz, answers)
    score = graded["score"]
    mistakes = sum(not r["correct"] for r in graded["results"])
    ok = score + 1e-9 >= LESSON_PASS_RATIO
    today = _today()
    xp_earned = 0
    with db.connect() as con:
        profile, _ = _load(con, user, today)
        if profile.hearts == 0:
            raise NoHeartsError("You ran out of hearts. Finish a Weak spots review to refill them and try again.")
        before = _summary(con, user, profile, today)
        if ok:
            first = lesson_id not in _done_scores(con, user)
            xp_earned = engine.lesson_xp(first, mistakes)
            con.execute(
                "INSERT INTO learn_lessons (user_id, lesson_id, completed_on, best_score) VALUES (?,?,?,?) "
                "ON CONFLICT(user_id, lesson_id) DO UPDATE SET best_score=MAX(best_score, excluded.best_score)",
                (user, lesson_id, today, score),
            )
            if user == LOCAL_USER:  # keep the original progress table meaningful for exports and older code
                con.execute(
                    "INSERT INTO lesson_progress (lesson_id, completed_on, quiz_score) VALUES (?,?,?) "
                    "ON CONFLICT(lesson_id) DO UPDATE SET quiz_score=MAX(quiz_score, excluded.quiz_score)",
                    (lesson_id, today, score),
                )
            profile = _give_xp(con, user, profile, xp_earned, today)
        after = _summary(con, user, profile, today)
    if ok and user == LOCAL_USER:
        db.touch_activity("learn")
    return {
        **graded,
        "passed": ok,
        "perfect": mistakes == 0,
        "xp_earned": xp_earned,
        "goal_reached_now": after["goal_met"] and not before["goal_met"],
        "profile": after,
        "message": "Lesson complete."
        if ok
        else f"Not yet: {round(LESSON_PASS_RATIO * 100)}% marks the lesson complete. Reread and try again.",
    }


# ---------------- tests: checkpoint, stage test, placement, weak spots ----------------


def _pools(lesson_ids: list[str]) -> dict[str, int]:
    return {lid: n for lid in lesson_ids if (n := len(curriculum.questions(lid)))}


def _public(refs: list[str]) -> list[dict]:
    rng = random.Random()
    return [curriculum.public_question(curriculum.questions(lid)[i], rng) for lid, i in map(engine.parse_ref, refs)]


def _new_session(con: sqlite3.Connection, user: str, kind: str, key: str, refs: list[str]) -> str:
    sid = uuid.uuid4().hex
    con.execute(
        "INSERT INTO learn_sessions (id, user_id, kind, key, refs) VALUES (?,?,?,?,?)", (sid, user, kind, key, json.dumps(refs))
    )
    con.execute("DELETE FROM learn_sessions WHERE created < datetime('now', '-1 day')")
    return sid


def start_test(user: str, kind: str, key: str) -> dict:
    """Start a checkpoint (key = module id), a stage test (key = stage) or the placement test (key = beginner)."""
    if kind not in TEST_KINDS:
        raise LearnError("No such test.")
    modules = curriculum.stage_modules()
    today = _today()
    with db.connect() as con:
        _load(con, user, today)
        unlocked = _unlocked(con, user)
        done = set(_done_scores(con, user))
        if kind == "checkpoint":
            mod = next((m for m in modules if m["id"] == key), None)
            if not mod:
                raise LearnError("No such module.")
            if mod["stage"] not in unlocked:
                raise LockedError(_lock_message(mod["stage"]))
            lessons = [x["id"] for x in mod["lessons"] if x["written"]]
            title, count = f"Checkpoint: {mod['title']}", CHECKPOINT_QUESTIONS
        elif kind == "stage":
            if key not in STAGES:
                raise LearnError("No such stage.")
            if key not in unlocked:
                raise LockedError(_lock_message(key))
            lessons = [x["id"] for m in modules if m["stage"] == key for x in m["lessons"] if x["written"]]
            title, count = f"{key.capitalize()} stage test", STAGE_TEST_QUESTIONS
        else:
            if key != STAGES[0]:
                raise LearnError("The placement test is for the Beginner stage.")
            if STAGES[1] in unlocked:
                raise NotReadyError("Intermediate is already unlocked.")
            lessons = [x["id"] for m in modules if m["stage"] == key for x in m["lessons"] if x["written"]]
            title, count = "Test out of Beginner", PLACEMENT_QUESTIONS
        if kind != "placement" and not all(lid in done for lid in lessons):
            raise NotReadyError("Finish all the lessons first, then take this test.")
        refs = engine.sample_refs(_pools(lessons), count, random.Random())
        if not refs:
            raise LearnError("There are no questions for this test yet.")
        sid = _new_session(con, user, kind, key, refs)
        if kind == "placement":
            con.execute("UPDATE learn_profile SET placement_seen=1 WHERE user_id=?", (user,))
    return {
        "session": sid,
        "kind": kind,
        "key": key,
        "title": title,
        "pass_percent": round(STAGE_PASS_RATIO * 100),
        "questions": _public(refs),
    }


def weak_spots(user: str) -> dict:
    """A short review of questions the learner got wrong before. Finishing it refills hearts."""
    today = _today()
    with db.connect() as con:
        _load(con, user, today)
        unlocked = _unlocked(con, user)
        rows = con.execute(
            "SELECT lesson_id, q_index FROM learn_weak WHERE user_id=? ORDER BY last_wrong DESC, wrong_count DESC", (user,)
        ).fetchall()
        refs = []
        for r in rows:
            try:
                stage_ok = curriculum.lesson_info(r["lesson_id"])["stage"] in unlocked
                exists = r["q_index"] < len(curriculum.questions(r["lesson_id"]))
            except LearnError:
                stage_ok = exists = False
            if stage_ok and exists:
                refs.append(f"{r['lesson_id']}:{r['q_index']}")
            if len(refs) >= WEAK_SPOTS_QUESTIONS:
                break
        if not refs:
            return {"session": None, "questions": [], "title": "Weak spots"}
        sid = _new_session(con, user, "weak", "weak-spots", refs)
    return {"session": sid, "kind": "weak", "key": "weak-spots", "title": "Weak spots", "questions": _public(refs)}


def grade_session(user: str, session_id: str, answers: list) -> dict:
    """Grade a test or review. Each session can be graded once."""
    today = _today()
    with db.connect() as con:
        row = con.execute("SELECT * FROM learn_sessions WHERE id=? AND user_id=?", (session_id, user)).fetchone()
        if row is None:
            raise LearnError("This test has already been graded or has expired. Start it again.")
        con.execute("DELETE FROM learn_sessions WHERE id=?", (session_id,))
        refs, kind, key = json.loads(row["refs"]), row["kind"], row["key"]
        quiz = [curriculum.questions(lid)[i] for lid, i in map(engine.parse_ref, refs)]
        graded = curriculum.grade_answers(quiz, answers)
        score = graded["score"]
        ok = engine.passed(score)
        profile, _ = _load(con, user, today)
        before_unlocked = _unlocked(con, user)
        before = _summary(con, user, profile, today)
        xp_earned = 0
        if kind == "weak":
            for (lid, i), r in zip(map(engine.parse_ref, refs), graded["results"], strict=True):
                if r["correct"]:
                    con.execute("DELETE FROM learn_weak WHERE user_id=? AND lesson_id=? AND q_index=?", (user, lid, i))
            profile = engine.restore_hearts(profile, today)
            xp_earned = XP_WEAK_SPOTS
            profile = _give_xp(con, user, profile, xp_earned, today)
        else:
            prior = con.execute(
                "SELECT best_score, passed, xp_awarded FROM learn_tests WHERE user_id=? AND kind=? AND key=?", (user, kind, key)
            ).fetchone()
            first_pass = ok and not (prior and prior["xp_awarded"])
            if kind != "placement" and first_pass:
                xp_earned = XP_TEST
            con.execute(
                "INSERT INTO learn_tests (user_id, kind, key, best_score, passed, xp_awarded) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(user_id, kind, key) DO UPDATE SET best_score=MAX(best_score, excluded.best_score), "
                "passed=MAX(passed, excluded.passed), xp_awarded=MAX(xp_awarded, excluded.xp_awarded)",
                (user, kind, key, score, int(ok), int(xp_earned > 0)),
            )
            if xp_earned:
                profile = _give_xp(con, user, profile, xp_earned, today)
        after_unlocked = _unlocked(con, user)
        after = _summary(con, user, profile, today)
    if xp_earned and user == LOCAL_USER:
        db.touch_activity("learn")
    newly = [s for s in after_unlocked if s not in before_unlocked]
    return {
        **graded,
        "kind": kind,
        "key": key,
        "passed": ok,
        "pass_percent": round(STAGE_PASS_RATIO * 100),
        "xp_earned": xp_earned,
        "goal_reached_now": after["goal_met"] and not before["goal_met"],
        "unlocked_stage": newly[0] if newly else None,
        "profile": after,
    }


# ---------------- settings ----------------


def set_goal(user: str, goal: int) -> dict:
    if goal not in DAILY_GOALS:
        raise LearnError(f"Pick a daily goal of {', '.join(map(str, DAILY_GOALS))} XP.")
    today = _today()
    with db.connect() as con:
        _load(con, user, today)
        con.execute("UPDATE learn_profile SET goal=? WHERE user_id=?", (goal, user))
        profile, _ = _load(con, user, today)
        return _summary(con, user, profile, today)


def dismiss_placement(user: str):
    with db.connect() as con:
        _load(con, user, _today())
        con.execute("UPDATE learn_profile SET placement_seen=1 WHERE user_id=?", (user,))
