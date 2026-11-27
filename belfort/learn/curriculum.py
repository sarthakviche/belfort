"""Learn vertical: the syllabus, lessons written in Markdown, quizzes and local progress.

Content lives in content/learn so contributors can add lessons without touching Python:
  syllabus.json          tracks -> modules -> lessons (id, title, minutes, status)
  lessons/<id>.md        front matter, Markdown body, optional ```quiz``` block (JSON list)
  lessons/<lang>/<id>.md the same lesson translated (same structure and quiz answers); used when the learner's
                         language is <lang>, else the English file (T50)

Directives inside a lesson body:
  ::chart SYMBOL BARS    a real chart of SYMBOL, ending at least EDU_LAG_DAYS ago (SEBI education norms)
  ::try KIND             a button into the app: replay, paper, predict, research
"""

import html
import json
import random
import re
from datetime import date, timedelta

from ..core import db, i18n
from ..settings import CONTENT_DIR, EDU_LAG_DAYS, STAGES

LEARN = CONTENT_DIR / "learn"
ID_RE = re.compile(r"^[a-z0-9-]{1,60}$")
QUESTION_TYPES = ("mc", "tf", "order", "number")


class LearnError(Exception):
    """A Learn problem. `key` and `vars` let the router say it in the learner's language (server.* catalogue keys)."""

    def __init__(self, message: str, key: str | None = None, **vars):
        super().__init__(message)
        self.key = key
        self.vars = vars


def syllabus() -> dict:
    return json.loads((LEARN / "syllabus.json").read_text(encoding="utf-8"))


def _lesson_index() -> dict[str, dict]:
    idx = {}
    for t in syllabus()["tracks"]:
        for m in t["modules"]:
            for i, lesson_info in enumerate(m["lessons"]):
                idx[lesson_info["id"]] = {
                    **lesson_info,
                    "track": t["id"],
                    "track_title": t["title"],
                    "module": m["id"],
                    "module_title": m["title"],
                    "stage": m.get("stage", "beginner"),
                    "order": i,
                }
    return idx


def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<i>\1</i>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def render_markdown(md: str) -> str:
    """A small, safe Markdown subset: headings, paragraphs, lists, callouts, tables and Belfort directives."""
    out, para, lst, table = [], [], None, []

    def flush():
        nonlocal lst, table
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para.clear()
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + f"</{tag}>")
            lst = None
        if table:
            head, *body = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table if not re.match(r"^\|?\s*:?-", r)]
            out.append(
                '<div class="scroll"><table><thead><tr>'
                + "".join(f"<th>{_inline(c)}</th>" for c in head)
                + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in body)
                + "</tbody></table></div>"
            )
            table = []

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.startswith("|"):
            if para or lst:
                flush()
            table.append(line)
            continue
        if table:
            flush()
        if m := re.match(r"^(#{2,4})\s+(.*)", line):
            flush()
            n = len(m.group(1)) + 1
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif m := re.match(r"^::chart\s+([A-Z0-9&\-]+)(?:\s+(\d+))?", line):
            flush()
            out.append(
                f'<div class="lesson-chart" data-symbol="{html.escape(m.group(1))}" data-bars="{m.group(2) or 120}"></div>'
            )
        elif m := re.match(r"^::try\s+(replay|paper|predict|research)", line):
            flush()
            out.append(
                f'<button type="button" class="try" data-try="{m.group(1)}">{html.escape(i18n.tr(i18n.current(), "lesson.try"))}</button>'
            )
        elif line.startswith("> "):
            flush()
            out.append(f'<div class="note plain">{_inline(line[2:])}</div>')
        elif m := re.match(r"^\s*[-*]\s+(.*)", line):
            if para:
                flush()
            if not lst or lst[0] != "ul":
                flush()
                lst = ("ul", [])
            lst[1].append(m.group(1))
        elif m := re.match(r"^\s*\d+[.)]\s+(.*)", line):
            if para:
                flush()
            if not lst or lst[0] != "ol":
                flush()
                lst = ("ol", [])
            lst[1].append(m.group(1))
        else:
            if lst:
                flush()
            para.append(line.strip())
    flush()
    return "\n".join(out)


def _is_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def normalize_question(q: dict) -> dict:
    """Validate one exercise and return it with an explicit type (mc, tf, order or number)."""
    if not isinstance(q, dict) or not isinstance(q.get("q"), str) or not q["q"].strip():
        raise LearnError("A quiz question is malformed.")
    kind = q.get("type", "mc")
    if kind not in QUESTION_TYPES:
        raise LearnError(f"Unknown exercise type: {kind}.")
    out = {"type": kind, "q": q["q"], "why": str(q.get("why", ""))}
    if kind == "mc":
        options, answer = q.get("options"), q.get("answer")
        if not (isinstance(options, list) and len(options) >= 2 and _is_number(answer) and 0 <= answer < len(options)):
            raise LearnError("A quiz question is malformed.")
        out.update(options=[str(o) for o in options], answer=int(answer))
    elif kind == "tf":
        if not isinstance(q.get("answer"), bool):
            raise LearnError("A true/false question needs answer: true or false.")
        out["answer"] = q["answer"]
    elif kind == "order":
        items = q.get("items")
        if not (isinstance(items, list) and len(items) >= 2 and len({str(i) for i in items}) == len(items)):
            raise LearnError("An ordering question needs at least two different items.")
        out["items"] = [str(i) for i in items]
    else:
        tolerance = q.get("tolerance", 0)
        if not _is_number(q.get("answer")) or not _is_number(tolerance) or tolerance < 0:
            raise LearnError("A number question needs a numeric answer and a tolerance of zero or more.")
        out.update(answer=q["answer"], tolerance=tolerance, unit=str(q.get("unit", "")))
    return out


def public_question(q: dict, rng: random.Random | None = None) -> dict:
    """The version of a normalized question that is safe to send to the page: never the answer."""
    out = {"type": q["type"], "q": q["q"]}
    if q["type"] == "mc":
        out["options"] = q["options"]
    elif q["type"] == "order":
        rng = rng or random.Random()
        items = list(q["items"])
        for _ in range(10):
            rng.shuffle(items)
            if items != q["items"]:
                break
        else:
            items = items[1:] + items[:1]
        out["items"] = items
    elif q["type"] == "number" and q.get("unit"):
        out["unit"] = q["unit"]
    return out


def check_answer(q: dict, answer) -> dict:
    """Grade one answer on the server. Returns correct, the right answer to reveal, and the explanation."""
    kind = q["type"]
    if kind == "mc":
        ok = _is_number(answer) and answer == q["answer"]
    elif kind == "tf":
        ok = isinstance(answer, bool) and answer == q["answer"]
    elif kind == "order":
        ok = isinstance(answer, list) and [str(a) for a in answer] == q["items"]
    else:
        try:
            ok = abs(float(answer) - q["answer"]) <= q["tolerance"] + 1e-9
        except (TypeError, ValueError):
            ok = False
    reveal = {"correct": bool(ok), "answer": q["items"] if kind == "order" else q["answer"], "why": q["why"]}
    if kind == "number" and q.get("unit"):
        reveal["unit"] = q["unit"]
    return reveal


def grade_answers(quiz: list[dict], answers: list) -> dict:
    """Grade a whole quiz at once: per-question results and the score from 0 to 1."""
    results = [check_answer(q, answers[i] if i < len(answers) else None) for i, q in enumerate(quiz)]
    score = sum(r["correct"] for r in results) / len(results) if results else 1.0
    return {"results": results, "score": round(score, 3)}


def split_cards(body: str, intro_title: str) -> list[dict]:
    """Split Markdown at each '## ' heading into cards. Text before the first heading is card one."""
    chunks: list[tuple[str, list[str]]] = [(intro_title, [])]
    for line in body.splitlines():
        if line.startswith("## "):
            chunks.append((line[3:].strip(), [line]))
        else:
            chunks[-1][1].append(line)
    cards = []
    for title, lines in chunks:
        md = "\n".join(lines).strip()
        if md:
            cards.append({"title": title, "html": render_markdown(md)})
    return cards


def parse_lesson(text: str) -> dict:
    meta, body = {}, text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    quiz = []
    m = re.search(r"```quiz\s*(.*?)```", body, re.S)
    if m:
        quiz = [normalize_question(q) for q in json.loads(m.group(1))]
        body = body[: m.start()] + body[m.end() :]
    meta["objectives"] = [x.strip() for x in meta.get("objectives", "").split("|") if x.strip()]
    return {"meta": meta, "html": render_markdown(body.strip()), "quiz": quiz, "text": body.strip(), "body": body.strip()}


def lesson_file(lesson_id: str, lang: str | None = None):
    """The file to serve: the translation for `lang` (default: this request's language) if there is one, else English."""
    lang = i18n.normalize(lang or i18n.current())
    if lang != i18n.DEFAULT:
        f = LEARN / "lessons" / lang / f"{lesson_id}.md"
        if f.exists():
            return f
    return LEARN / "lessons" / f"{lesson_id}.md"


def translated_title(lesson_id: str, lang: str | None = None) -> str | None:
    """The lesson's title in the requested language, or None when there is no translation."""
    f = lesson_file(lesson_id, lang)
    if f.parent.name == "lessons":
        return None
    return parse_lesson(f.read_text(encoding="utf-8"))["meta"].get("title")


def available_languages(lesson_id: str) -> list[str]:
    """Languages other than English that have a translated file for this lesson."""
    return [c for c in i18n.LANGUAGES if c != i18n.DEFAULT and (LEARN / "lessons" / c / f"{lesson_id}.md").exists()]


def is_written(lesson_id: str) -> bool:
    """Whether the lesson file exists (a lesson can be on the syllabus before it is written)."""
    return bool(ID_RE.match(lesson_id or "")) and (LEARN / "lessons" / f"{lesson_id}.md").exists()


def lesson_info(lesson_id: str) -> dict:
    """Syllabus facts about a lesson (track, module, stage) without reading the file."""
    info = _lesson_index().get(lesson_id) if ID_RE.match(lesson_id or "") else None
    if not info:
        raise LearnError("No such lesson.", "server.no_lesson")
    return info


def questions(lesson_id: str) -> list[dict]:
    """The normalized exercises of a written lesson, answers included. Server side only."""
    if not is_written(lesson_id):
        raise LearnError("No such lesson.", "server.no_lesson")
    return parse_lesson(lesson_file(lesson_id).read_text(encoding="utf-8"))["quiz"]


def stage_modules() -> list[dict]:
    """Every module in path order: stage (beginner, intermediate, advanced), then syllabus order."""
    mods = []
    for t in syllabus()["tracks"]:
        for m in t["modules"]:
            mods.append(
                {
                    "id": m["id"],
                    "title": m["title"],
                    "why": m.get("why", ""),
                    "stage": m.get("stage", "beginner"),
                    "track": t["id"],
                    "lessons": [
                        {**x, "title": translated_title(x["id"]) or x["title"], "written": is_written(x["id"])}
                        for x in m["lessons"]
                    ],
                }
            )
    mods.sort(key=lambda m: STAGES.index(m["stage"]))  # stable: syllabus order is kept inside a stage
    return mods


def lesson(lesson_id: str) -> dict:
    if not ID_RE.match(lesson_id or ""):
        raise LearnError("No such lesson.", "server.no_lesson")
    idx = _lesson_index()
    info = idx.get(lesson_id)
    f = LEARN / "lessons" / f"{lesson_id}.md"
    if not info or not f.exists():
        raise LearnError(
            "This lesson has not been written yet. It is on the syllabus; contributions are welcome.", "server.not_written"
        )
    f = lesson_file(lesson_id)
    translated = f.parent.name != "lessons"
    data = parse_lesson(f.read_text(encoding="utf-8"))
    order = [k for k, v in idx.items() if (LEARN / "lessons" / f"{k}.md").exists()]
    i = order.index(lesson_id)
    rng = random.Random()
    return {
        "id": lesson_id,
        **info,
        "title": data["meta"].get("title") or info["title"],
        "lang": i18n.current() if translated else i18n.DEFAULT,
        "translated": translated,
        "translation_status": data["meta"].get("translation") if translated else None,
        "translations": available_languages(lesson_id),
        "objectives": data["meta"]["objectives"],
        "html": data["html"],
        "cards": split_cards(data["body"], info["title"]),
        "quiz": [public_question(q, rng) for q in data["quiz"]],
        "prev": order[i - 1] if i > 0 else None,
        "next": order[i + 1] if i + 1 < len(order) else None,
        "text": data["text"][:6000],
        "edu_lag_days": EDU_LAG_DAYS,
    }


def progress() -> dict:
    with db.connect() as con:
        done = {r["lesson_id"]: r for r in db.rows(con.execute("SELECT * FROM lesson_progress"))}
        days = {r["day"] for r in db.rows(con.execute("SELECT day FROM activity"))}
    streak, d = 0, date.today()
    if d.isoformat() not in days:
        d -= timedelta(days=1)
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)
    syl = syllabus()
    ready_total = 0
    for t in syl["tracks"]:
        for m in t["modules"]:
            for lesson_info in m["lessons"]:
                lesson_info["written"] = (LEARN / "lessons" / f"{lesson_info['id']}.md").exists()
                lesson_info["done"] = lesson_info["id"] in done
                ready_total += lesson_info["written"]
    return {"syllabus": syl, "completed": len(done), "available": ready_total, "streak_days": streak}
