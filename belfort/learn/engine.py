"""The rules of the Learn game, with no I/O: XP, daily goal and streak with freezes, hearts, stage unlocks, the path.

Every function takes the date as an ISO string (`YYYY-MM-DD`) from its caller and returns new values, so each rule
is tested without a clock or a database. XP, hearts and streaks are virtual and are never redeemable or bought.
"""

import random
from dataclasses import dataclass, replace
from datetime import date

from ..settings import (
    HEARTS_MAX,
    STAGE_PASS_RATIO,
    STAGES,
    STREAK_FREEZE_EVERY,
    STREAK_FREEZE_MAX,
    XP_LESSON,
    XP_LESSON_NO_MISTAKES,
    XP_LESSON_REPEAT,
)


@dataclass(frozen=True)
class Profile:
    """One learner's game state."""

    xp_total: int = 0
    goal: int = 20
    hearts: int = HEARTS_MAX
    hearts_day: str | None = None
    streak: int = 0
    last_goal_day: str | None = None
    freezes: int = 0


def _days_between(earlier: str, later: str) -> int:
    return (date.fromisoformat(later) - date.fromisoformat(earlier)).days


# ---------------- hearts ----------------


def refill_hearts(profile: Profile, today: str) -> Profile:
    """Hearts reset to the maximum on a new day."""
    if profile.hearts_day == today:
        return profile
    return replace(profile, hearts=HEARTS_MAX, hearts_day=today)


def lose_heart(profile: Profile) -> Profile:
    """A wrong answer costs one heart, never below zero."""
    return replace(profile, hearts=max(0, profile.hearts - 1))


def restore_hearts(profile: Profile, today: str) -> Profile:
    """Finishing a Weak spots review fills the hearts back to the maximum."""
    return replace(profile, hearts=HEARTS_MAX, hearts_day=today)


def can_start_lesson(profile: Profile) -> bool:
    return profile.hearts > 0


# ---------------- XP ----------------


def lesson_xp(first_time: bool, mistakes: int) -> int:
    """10 XP for a first completion, plus 5 for no mistakes. A replay earns a small fixed amount."""
    if not first_time:
        return XP_LESSON_REPEAT
    return XP_LESSON + (XP_LESSON_NO_MISTAKES if mistakes == 0 else 0)


def award_xp(profile: Profile, xp_today_before: int, xp: int, today: str) -> Profile:
    """Add XP. The first time today's XP reaches the daily goal, the streak moves on (or uses freezes)."""
    updated = replace(profile, xp_total=profile.xp_total + xp)
    reached = xp_today_before < profile.goal <= xp_today_before + xp
    if not reached or profile.last_goal_day == today:
        return updated
    streak, freezes, last = updated.streak, updated.freezes, updated.last_goal_day
    if last is None:
        streak = 1
    else:
        missed = _days_between(last, today) - 1
        if missed <= 0:
            streak += 1
        elif missed <= freezes:
            freezes -= missed  # a freeze is spent for every missed day, automatically
            streak += 1
        else:
            streak = 1
    if streak % STREAK_FREEZE_EVERY == 0 and freezes < STREAK_FREEZE_MAX:
        freezes += 1
    return replace(updated, streak=streak, freezes=freezes, last_goal_day=today)


def streak_now(profile: Profile, today: str) -> int:
    """The streak to show today: still alive if yesterday counted, or if freezes cover every missed day."""
    if profile.last_goal_day is None:
        return 0
    missed = _days_between(profile.last_goal_day, today) - 1
    return profile.streak if missed <= max(0, profile.freezes) else 0


def streak_at_risk(profile: Profile, today: str) -> bool:
    """Today's goal is not met yet and the streak would be lost without it."""
    return profile.last_goal_day is not None and profile.last_goal_day != today and streak_now(profile, today) > 0


# ---------------- stages and tests ----------------


def score_key(kind: str, key: str) -> str:
    return f"{kind}:{key}"


def passed(score: float, ratio: float = STAGE_PASS_RATIO) -> bool:
    """A score of 0 to 1 against the pass mark."""
    return score + 1e-9 >= ratio


def unlocked_stages(scores: dict[str, float]) -> list[str]:
    """Beginner is always open. A stage opens when the stage test of the one before it (or, for Intermediate, the
    placement test) was passed. `scores` maps 'stage:<stage>' and 'placement:<stage>' to the best score."""
    open_stages = [STAGES[0]]
    for before, after in zip(STAGES, STAGES[1:], strict=False):
        best = max(scores.get(score_key("stage", before), 0.0), scores.get(score_key("placement", before), 0.0))
        if passed(best):
            open_stages.append(after)
        else:
            break
    return open_stages


def sample_refs(pools: dict[str, int], n: int, rng: random.Random) -> list[str]:
    """Pick up to n question refs ('lesson-id:index') spread across lessons: take one at a time from each lesson in
    turn, so no lesson dominates. `pools` maps lesson id to how many questions it has."""
    queues = []
    for lesson_id, count in pools.items():
        order = list(range(count))
        rng.shuffle(order)
        queues.append([f"{lesson_id}:{i}" for i in order])
    rng.shuffle(queues)
    picked: list[str] = []
    while len(picked) < n and any(queues):
        for q in queues:
            if q and len(picked) < n:
                picked.append(q.pop())
    rng.shuffle(picked)
    return picked


def parse_ref(ref: str) -> tuple[str, int]:
    lesson_id, _, index = ref.rpartition(":")
    return lesson_id, int(index)


# ---------------- the path ----------------


def build_path(
    modules: list[dict],
    done: set[str],
    perfect: set[str],
    unlocked: list[str],
    tests_passed: set[str],
) -> list[dict]:
    """The nodes the page draws, in order: stages, their modules, and per module its lessons and checkpoint, then the
    stage test. Node states: done, next, open, waiting (not available yet), locked (stage locked), soon (not written).

    `modules` come from curriculum.stage_modules(); `tests_passed` holds 'checkpoint:<module>' and 'stage:<stage>'.
    """
    stages = []
    next_taken = False
    for stage in STAGES:
        is_open = stage in unlocked
        stage_modules = [m for m in modules if m["stage"] == stage]
        out_modules, lesson_total, lesson_done = [], 0, 0
        all_written_done = True
        for m in stage_modules:
            nodes = []
            written = [x for x in m["lessons"] if x["written"]]
            for x in m["lessons"]:
                node = {"kind": "lesson", "id": x["id"], "title": x["title"], "minutes": x.get("minutes")}
                if not x["written"]:
                    node["state"] = "soon"
                elif not is_open:
                    node["state"] = "locked"
                elif x["id"] in done:
                    node["state"] = "done"
                    node["perfect"] = x["id"] in perfect
                else:
                    node["state"] = "open"
                nodes.append(node)
                if x["written"]:
                    lesson_total += 1
                    lesson_done += x["id"] in done
                    all_written_done = all_written_done and x["id"] in done
            module_done = bool(written) and all(x["id"] in done for x in written)
            checkpoint = {"kind": "checkpoint", "id": m["id"], "title": f"Checkpoint: {m['title']}"}
            if not written:
                checkpoint["state"] = "soon"
            elif not is_open:
                checkpoint["state"] = "locked"
            elif score_key("checkpoint", m["id"]) in tests_passed:
                checkpoint["state"] = "done"
            else:
                checkpoint["state"] = "open" if module_done else "waiting"
            nodes.append(checkpoint)
            out_modules.append({"id": m["id"], "title": m["title"], "why": m["why"], "nodes": nodes})
        test = {"kind": "stage_test", "id": stage, "title": f"{stage.capitalize()} stage test"}
        if not is_open:
            test["state"] = "locked"
        elif score_key("stage", stage) in tests_passed:
            test["state"] = "done"
        else:
            test["state"] = "open" if lesson_total and all_written_done else "waiting"
        stages.append(
            {
                "key": stage,
                "title": stage.capitalize(),
                "unlocked": is_open,
                "lessons_done": lesson_done,
                "lessons_total": lesson_total,
                "modules": out_modules,
                "test": test,
            }
        )
    # Highlight the first available node that is not done, across all open stages.
    for stage in stages:
        if not stage["unlocked"] or next_taken or stage["test"]["state"] == "done":
            continue  # a stage whose test is passed is finished: leftover optional nodes are not "next"
        for node in [n for m in stage["modules"] for n in m["nodes"]] + [stage["test"]]:
            if node["state"] == "open":
                node["state"] = "next"
                next_taken = True
                break
    return stages
