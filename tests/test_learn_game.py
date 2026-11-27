"""The Learn game through the API, on a small synthetic syllabus (all four exercise types) and a temporary database."""

import json

import pytest
from fastapi.testclient import TestClient

from belfort.core import db
from belfort.learn import curriculum, game
from belfort.main import app

SYLLABUS = {
    "title": "t",
    "tracks": [
        {
            "id": "t1",
            "title": "T",
            "modules": [
                {
                    "id": "m-adv",
                    "title": "Adv module",
                    "stage": "advanced",
                    "why": "",
                    "lessons": [{"id": "adv-one", "title": "Adv one", "minutes": 5}],
                },
                {
                    "id": "m-beg",
                    "title": "Beg module",
                    "stage": "beginner",
                    "why": "",
                    "lessons": [
                        {"id": "beg-one", "title": "Beg one", "minutes": 5},
                        {"id": "beg-two", "title": "Beg two", "minutes": 5},
                        {"id": "beg-soon", "title": "Soon", "minutes": 5, "status": "planned"},
                    ],
                },
                {
                    "id": "m-int",
                    "title": "Int module",
                    "stage": "intermediate",
                    "why": "",
                    "lessons": [{"id": "int-one", "title": "Int one", "minutes": 5}],
                },
            ],
        }
    ],
}

QUIZ_ONE = [
    {"q": "Pick the second", "options": ["a", "b", "c"], "answer": 1, "why": "Because b is second."},
    {"type": "tf", "q": "A stop-loss limits the loss on a trade.", "answer": True, "why": "That is its job."},
    {"type": "order", "q": "Order the steps", "items": ["Plan", "Enter", "Exit", "Review"], "why": "Plan first."},
    {
        "type": "number",
        "q": "Risk 2000 over a 20 stop. Shares?",
        "answer": 100,
        "tolerance": 1,
        "unit": "shares",
        "why": "2000/20.",
    },
]
QUIZ_TWO = [
    {"q": "Pick the first", "options": ["a", "b"], "answer": 0, "why": "a is first."},
    {"type": "tf", "q": "Gaps can jump past a stop.", "answer": True, "why": "They can."},
    {"q": "Pick the third", "options": ["a", "b", "c"], "answer": 2, "why": "c."},
]


def _lesson(title: str, quiz: list) -> str:
    return (
        f"---\ntitle: {title}\nminutes: 5\nobjectives: Know it | Use it\n---\n"
        "The intro before any heading.\n\n## First idea\n\nSome text.\n\n## Second idea\n\nMore text.\n\n"
        f"```quiz\n{json.dumps(quiz)}\n```\n"
    )


@pytest.fixture
def client(fresh_db, tmp_path, monkeypatch):
    """A test client over a synthetic syllabus. `client.today` can be moved to simulate another day."""
    root = tmp_path / "learn"
    (root / "lessons").mkdir(parents=True)
    (root / "syllabus.json").write_text(json.dumps(SYLLABUS), encoding="utf-8")
    for lid in ("beg-one", "int-one", "adv-one"):
        (root / "lessons" / f"{lid}.md").write_text(_lesson(lid, QUIZ_ONE), encoding="utf-8")
    (root / "lessons" / "beg-two.md").write_text(_lesson("beg-two", QUIZ_TWO), encoding="utf-8")
    monkeypatch.setattr(curriculum, "LEARN", root)
    state = {"today": "2026-11-27"}
    monkeypatch.setattr(game, "_today", lambda: state["today"])
    c = TestClient(app)
    c.state = state
    return c


def _correct(q: dict, quiz: list) -> object:
    """The right answer for a public question, looked up in the source quiz."""
    src = next(x for x in quiz if x["q"] == q["q"])
    return src["items"] if src.get("type") == "order" else src["answer"]


def _answers(lesson: dict, quiz: list) -> list:
    return [_correct(q, quiz) for q in lesson["quiz"]]


def _finish(c, lesson_id: str, quiz: list, wrong: int = 0) -> dict:
    les = c.get(f"/api/learn/lessons/{lesson_id}").json()
    answers = _answers(les, quiz)
    for i in range(wrong):
        answers[i] = None
    return c.post(f"/api/learn/lessons/{lesson_id}/quiz", json={"answers": answers}).json()


def _path_states(c) -> dict:
    stages = c.get("/api/learn/path").json()["stages"]
    return {n["id"]: n["state"] for s in stages for m in s["modules"] for n in m["nodes"]} | {
        f"test-{s['key']}": s["test"]["state"] for s in stages
    }


# ---------------- exercise types ----------------


def test_validator_accepts_the_four_types_and_rejects_bad_ones():
    for q in QUIZ_ONE:
        assert curriculum.normalize_question(q)["type"] in curriculum.QUESTION_TYPES
    bad = [
        {"type": "tf", "q": "x", "answer": "yes"},
        {"type": "order", "q": "x", "items": ["only"]},
        {"type": "order", "q": "x", "items": ["a", "a"]},
        {"type": "number", "q": "x", "answer": "5"},
        {"type": "number", "q": "x", "answer": 5, "tolerance": -1},
        {"type": "mc", "q": "x", "options": ["a", "b"], "answer": 2},
        {"type": "mystery", "q": "x"},
        {"q": ""},
    ]
    for q in bad:
        with pytest.raises(curriculum.LearnError):
            curriculum.normalize_question(q)


def test_public_questions_never_contain_answers_and_orders_are_shuffled():
    for src in QUIZ_ONE:
        pub = curriculum.public_question(curriculum.normalize_question(src))
        assert "answer" not in pub and "why" not in pub
    order = curriculum.normalize_question(QUIZ_ONE[2])
    for seed in range(20):
        import random

        assert curriculum.public_question(order, random.Random(seed))["items"] != order["items"]
    assert curriculum.public_question(curriculum.normalize_question(QUIZ_ONE[3]))["unit"] == "shares"


def test_each_type_is_graded_on_the_server():
    mc, tf, order, number = (curriculum.normalize_question(q) for q in QUIZ_ONE)
    assert curriculum.check_answer(mc, 1)["correct"] and not curriculum.check_answer(mc, 0)["correct"]
    assert not curriculum.check_answer(mc, True)["correct"]  # a boolean is not an option index
    assert curriculum.check_answer(tf, True)["correct"] and not curriculum.check_answer(tf, "true")["correct"]
    assert curriculum.check_answer(order, ["Plan", "Enter", "Exit", "Review"])["correct"]
    assert not curriculum.check_answer(order, ["Enter", "Plan", "Exit", "Review"])["correct"]
    assert curriculum.check_answer(number, 101)["correct"] and curriculum.check_answer(number, "99")["correct"]
    assert not curriculum.check_answer(number, 105)["correct"] and not curriculum.check_answer(number, "abc")["correct"]
    assert curriculum.check_answer(number, 100)["unit"] == "shares"


def test_lesson_is_split_into_cards_at_each_heading():
    cards = curriculum.split_cards("Intro text.\n\n## One\n\nBody one.\n\n## Two\n\nBody two.", "The title")
    assert [c["title"] for c in cards] == ["The title", "One", "Two"]
    assert "Intro text." in cards[0]["html"] and "<h3>One</h3>" in cards[1]["html"]
    assert [c["title"] for c in curriculum.split_cards("## Only\n\ntext", "T")] == ["Only"]  # no intro, no empty card


def test_real_content_has_valid_stages_and_questions():
    mods = curriculum.stage_modules()
    stage_of = {m["id"]: m["stage"] for m in mods}
    assert set(stage_of.values()) == {"beginner", "intermediate", "advanced"}
    assert stage_of["safety"] == "beginner" and stage_of["taxes-records"] == "intermediate"
    assert [m["stage"] for m in mods] == sorted((m["stage"] for m in mods), key=("beginner", "intermediate", "advanced").index)
    for m in mods:
        for x in m["lessons"]:
            if x["written"]:
                assert len(curriculum.questions(x["id"])) >= 3
                assert curriculum.lesson(x["id"])["cards"]


# ---------------- locks ----------------


def test_new_learner_sees_beginner_open_and_later_stages_locked(client):
    states = _path_states(client)
    assert states["beg-one"] == "next" and states["beg-two"] == "open" and states["beg-soon"] == "soon"
    assert states["int-one"] == "locked" and states["adv-one"] == "locked"
    path = client.get("/api/learn/path").json()
    assert [s["title"] for s in path["stages"]] == ["Beginner", "Intermediate", "Advanced"]
    assert path["profile"]["hearts"] == 5 and path["profile"]["goal"] == 20 and path["placement_offered"] is True
    locked_titles = [n["title"] for s in path["stages"][1:] for m in s["modules"] for n in m["nodes"] if n["kind"] == "lesson"]
    assert "Int one" in locked_titles  # locked lessons still show their title


def test_locked_lessons_are_refused_by_the_api_not_just_hidden(client):
    r = client.get("/api/learn/lessons/int-one")
    assert r.status_code == 403 and "locked" in r.json()["detail"] and "placement" in r.json()["detail"]
    assert client.get("/api/learn/lessons/adv-one").status_code == 403
    assert client.post("/api/learn/lessons/int-one/quiz", json={"answers": [1, True, [], 1]}).status_code == 403
    assert client.post("/api/learn/lessons/int-one/check", json={"index": 0, "answer": 1}).status_code == 403
    assert client.get("/api/learn/tests/stage/intermediate").status_code == 403
    assert client.get("/api/learn/tests/checkpoint/m-int").status_code == 403
    assert client.get("/api/learn/lessons/beg-soon").status_code == 404  # on the syllabus but not written
    assert client.get("/api/learn/lessons/nope").status_code == 404


def test_lesson_payload_has_cards_and_no_answers(client):
    d = client.get("/api/learn/lessons/beg-one").json()
    assert [c["title"] for c in d["cards"]] == ["Beg one", "First idea", "Second idea"]
    assert [q["type"] for q in d["quiz"]] == ["mc", "tf", "order", "number"]
    assert all("answer" not in q and "why" not in q for q in d["quiz"])


# ---------------- lesson flow, hearts, XP ----------------


def test_check_reveals_the_answer_and_a_wrong_answer_costs_a_heart(client):
    ok = client.post("/api/learn/lessons/beg-one/check", json={"index": 0, "answer": 1}).json()
    assert ok["correct"] and ok["hearts"] == 5
    bad = client.post("/api/learn/lessons/beg-one/check", json={"index": 0, "answer": 2}).json()
    assert not bad["correct"] and bad["answer"] == 1 and bad["why"] == "Because b is second." and bad["hearts"] == 4
    assert client.post("/api/learn/lessons/beg-one/check", json={"index": 9, "answer": 0}).status_code == 404
    assert client.get("/api/learn/path").json()["profile"]["hearts"] == 4


def test_completing_a_lesson_awards_xp_and_marks_it_done(client):
    r = _finish(client, "beg-one", QUIZ_ONE)
    assert r["passed"] and r["perfect"] and r["xp_earned"] == 15 and r["score"] == 1
    assert r["profile"]["xp_total"] == 15 and r["profile"]["xp_today"] == 15 and not r["profile"]["goal_met"]
    states = _path_states(client)
    assert states["beg-one"] == "done" and states["beg-two"] == "next"
    nodes = {n["id"]: n for s in client.get("/api/learn/path").json()["stages"] for m in s["modules"] for n in m["nodes"]}
    assert nodes["beg-one"]["perfect"] is True  # crown


def test_a_lesson_with_a_mistake_earns_ten_and_a_failed_one_earns_nothing(client):
    r = _finish(client, "beg-one", QUIZ_ONE, wrong=1)
    assert r["passed"] and not r["perfect"] and r["xp_earned"] == 10  # 3 of 4 is 75%, above the 60% mark
    failed = _finish(client, "beg-two", QUIZ_TWO, wrong=2)
    assert not failed["passed"] and failed["xp_earned"] == 0 and "Not yet" in failed["message"]
    assert _path_states(client)["beg-two"] != "done"


def test_replaying_a_done_lesson_earns_the_small_replay_xp(client):
    _finish(client, "beg-one", QUIZ_ONE)
    again = _finish(client, "beg-one", QUIZ_ONE)
    assert again["xp_earned"] == 5 and again["profile"]["xp_total"] == 20


def test_reaching_the_daily_goal_starts_a_streak_and_a_missed_day_resets_it(client):
    client.put("/api/learn/goal", json={"goal": 10})
    first = _finish(client, "beg-one", QUIZ_ONE)
    assert first["goal_reached_now"] and first["profile"]["streak"] == 1
    client.state["today"] = "2026-11-28"
    p = client.get("/api/learn/path").json()["profile"]
    assert p["streak"] == 1 and p["streak_at_risk"] and p["xp_today"] == 0
    assert _finish(client, "beg-two", QUIZ_TWO)["profile"]["streak"] == 2
    client.state["today"] = "2026-12-01"
    assert client.get("/api/learn/path").json()["profile"]["streak"] == 0


def test_goal_must_be_one_of_the_presets(client):
    assert client.put("/api/learn/goal", json={"goal": 50}).json()["goal"] == 50
    assert client.put("/api/learn/goal", json={"goal": 7}).status_code == 400


def test_lessons_finished_before_the_game_existed_still_count_as_done(client):
    with db.connect() as con:
        con.execute("INSERT INTO lesson_progress (lesson_id, completed_on, quiz_score) VALUES ('beg-one','2026-01-01',1.0)")
    assert _path_states(client)["beg-one"] == "done"


def test_progress_is_kept_per_user(client, monkeypatch):
    _finish(client, "beg-one", QUIZ_ONE)
    monkeypatch.setattr("belfort.learn.router.current_user_id", lambda request=None: "someone-else")
    p = client.get("/api/learn/path").json()
    assert p["profile"]["xp_total"] == 0 and _path_states(client)["beg-one"] == "next"


# ---------------- hearts and weak spots ----------------


def _drain_hearts(client):
    for _ in range(5):
        client.post("/api/learn/lessons/beg-one/check", json={"index": 0, "answer": 0})


def test_with_no_hearts_a_new_lesson_cannot_start_but_weak_spots_refills_them(client):
    _drain_hearts(client)
    assert client.get("/api/learn/path").json()["profile"]["hearts"] == 0
    r = client.get("/api/learn/lessons/beg-two")
    assert r.status_code == 403 and "hearts" in r.json()["detail"]
    assert client.post("/api/learn/lessons/beg-one/check", json={"index": 0, "answer": 1}).status_code == 403
    assert client.post("/api/learn/lessons/beg-one/quiz", json={"answers": [1, True, [], 100]}).status_code == 403

    review = client.get("/api/learn/weak-spots").json()
    assert review["session"] and len(review["questions"]) == 1  # the one question missed, however often
    assert all("answer" not in q for q in review["questions"])
    graded = client.post(f"/api/learn/sessions/{review['session']}/grade", json={"answers": [1]}).json()
    assert graded["results"][0]["correct"] and graded["profile"]["hearts"] == 5 and graded["profile"]["weak_spots"] == 0
    assert client.get("/api/learn/lessons/beg-two").status_code == 200
    assert client.get("/api/learn/weak-spots").json()["session"] is None  # nothing left to review


def test_weak_spots_refill_hearts_even_when_still_wrong(client):
    _drain_hearts(client)
    review = client.get("/api/learn/weak-spots").json()
    graded = client.post(f"/api/learn/sessions/{review['session']}/grade", json={"answers": [0]}).json()
    assert not graded["results"][0]["correct"] and graded["profile"]["hearts"] == 5 and graded["profile"]["weak_spots"] == 1


def test_a_session_can_only_be_graded_once(client):
    _drain_hearts(client)
    sid = client.get("/api/learn/weak-spots").json()["session"]
    assert client.post(f"/api/learn/sessions/{sid}/grade", json={"answers": [1]}).status_code == 200
    assert client.post(f"/api/learn/sessions/{sid}/grade", json={"answers": [1]}).status_code == 404


def test_hearts_reset_the_next_day(client):
    client.post("/api/learn/lessons/beg-one/check", json={"index": 0, "answer": 0})
    assert client.get("/api/learn/path").json()["profile"]["hearts"] == 4
    client.state["today"] = "2026-11-28"
    assert client.get("/api/learn/path").json()["profile"]["hearts"] == 5


def test_answering_a_weak_spot_correctly_in_a_lesson_clears_it(client):
    client.post("/api/learn/lessons/beg-one/check", json={"index": 0, "answer": 0})
    assert client.get("/api/learn/path").json()["profile"]["weak_spots"] == 1
    client.post("/api/learn/lessons/beg-one/check", json={"index": 0, "answer": 1})
    assert client.get("/api/learn/path").json()["profile"]["weak_spots"] == 0


# ---------------- checkpoints, stage tests, placement ----------------


def _grade_test(client, test: dict, wrong: int = 0) -> dict:
    quizzes = {q["q"]: q for q in QUIZ_ONE + QUIZ_TWO}
    answers = [_correct(q, list(quizzes.values())) for q in test["questions"]]
    for i in range(wrong):
        answers[i] = None
    return client.post(f"/api/learn/sessions/{test['session']}/grade", json={"answers": answers}).json()


def test_checkpoint_and_stage_test_need_the_lessons_then_award_xp_once(client):
    assert client.get("/api/learn/tests/checkpoint/m-beg").status_code == 409
    _finish(client, "beg-one", QUIZ_ONE)
    _finish(client, "beg-two", QUIZ_TWO)
    assert _path_states(client)["m-beg"] == "next"
    cp = client.get("/api/learn/tests/checkpoint/m-beg").json()
    assert len(cp["questions"]) == 7 and all("answer" not in q for q in cp["questions"])
    done = _grade_test(client, cp)
    assert done["passed"] and done["xp_earned"] == 20 and done["unlocked_stage"] is None
    assert _path_states(client)["m-beg"] == "done" and _path_states(client)["test-beginner"] == "next"
    again = _grade_test(client, client.get("/api/learn/tests/checkpoint/m-beg").json())
    assert again["xp_earned"] == 0  # the 20 XP is for the first pass only


def test_passing_the_stage_test_at_eighty_percent_unlocks_the_next_stage(client):
    _finish(client, "beg-one", QUIZ_ONE)
    _finish(client, "beg-two", QUIZ_TWO)
    test = client.get("/api/learn/tests/stage/beginner").json()
    assert len(test["questions"]) == 7
    failed = _grade_test(client, test, wrong=2)  # 5 of 7 is 71%
    assert not failed["passed"] and failed["xp_earned"] == 0 and failed["unlocked_stage"] is None
    assert client.get("/api/learn/lessons/int-one").status_code == 403
    passed = _grade_test(client, client.get("/api/learn/tests/stage/beginner").json(), wrong=1)  # 6 of 7 is 86%
    assert passed["passed"] and passed["unlocked_stage"] == "intermediate" and passed["xp_earned"] == 20
    assert client.get("/api/learn/lessons/int-one").status_code == 200
    assert client.get("/api/learn/lessons/adv-one").status_code == 403  # Advanced still needs the Intermediate test
    assert _path_states(client)["int-one"] == "next"


def test_placement_test_unlocks_intermediate_without_doing_beginner(client):
    assert client.get("/api/learn/path").json()["placement_offered"] is True
    test = client.get("/api/learn/tests/placement/beginner").json()
    assert test["title"] == "Test out of Beginner" and len(test["questions"]) == 7  # all the questions there are
    assert client.get("/api/learn/path").json()["placement_offered"] is False  # taking it uses up the offer
    result = _grade_test(client, test)
    assert result["passed"] and result["unlocked_stage"] == "intermediate" and result["xp_earned"] == 0
    assert client.get("/api/learn/lessons/int-one").status_code == 200
    assert client.get("/api/learn/tests/placement/beginner").status_code == 409  # already unlocked


def test_a_failed_placement_test_unlocks_nothing(client):
    test = client.get("/api/learn/tests/placement/beginner").json()
    result = _grade_test(client, test, wrong=3)
    assert not result["passed"] and result["unlocked_stage"] is None
    assert client.get("/api/learn/lessons/int-one").status_code == 403


def test_placement_offer_can_be_dismissed(client):
    assert client.post("/api/learn/placement/dismiss").json() == {"ok": True}
    assert client.get("/api/learn/path").json()["placement_offered"] is False
    assert client.get("/api/learn/tests/placement/other").status_code == 404
    assert client.get("/api/learn/tests/nope/beginner").status_code == 404


def test_wrong_session_or_user_cannot_grade(client, monkeypatch):
    sid = client.get("/api/learn/tests/placement/beginner").json()["session"]
    monkeypatch.setattr("belfort.learn.router.current_user_id", lambda request=None: "someone-else")
    assert client.post(f"/api/learn/sessions/{sid}/grade", json={"answers": []}).status_code == 404
