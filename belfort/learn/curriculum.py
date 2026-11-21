"""Learn vertical: the syllabus, lessons written in Markdown, quizzes and local progress.

Content lives in content/learn so contributors can add lessons without touching Python:
  syllabus.json          tracks -> modules -> lessons (id, title, minutes, status)
  lessons/<id>.md        front matter, Markdown body, optional ```quiz``` block (JSON list)

Directives inside a lesson body:
  ::chart SYMBOL BARS    a real chart of SYMBOL, ending at least EDU_LAG_DAYS ago (SEBI education norms)
  ::try KIND             a button into the app: replay, paper, predict, research
"""
import html
import json
import re
from datetime import date, timedelta

from ..core import db
from ..settings import CONTENT_DIR, EDU_LAG_DAYS

LEARN = CONTENT_DIR / "learn"
ID_RE = re.compile(r"^[a-z0-9-]{1,60}$")


class LearnError(Exception):
    pass


def syllabus() -> dict:
    return json.loads((LEARN / "syllabus.json").read_text(encoding="utf-8"))


def _lesson_index() -> dict[str, dict]:
    idx = {}
    for t in syllabus()["tracks"]:
        for m in t["modules"]:
            for i, l in enumerate(m["lessons"]):
                idx[l["id"]] = {**l, "track": t["id"], "track_title": t["title"], "module": m["id"], "module_title": m["title"],
                                "order": i}
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
            out.append('<div class="scroll"><table><thead><tr>' + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table></div>")
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
            out.append(f'<div class="lesson-chart" data-symbol="{html.escape(m.group(1))}" data-bars="{m.group(2) or 120}"></div>')
        elif m := re.match(r"^::try\s+(replay|paper|predict|research)", line):
            flush()
            out.append(f'<button type="button" class="try" data-try="{m.group(1)}">Try it in Belfort →</button>')
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
        quiz = json.loads(m.group(1))
        body = body[:m.start()] + body[m.end():]
    for q in quiz:
        if not (q.get("q") and len(q.get("options", [])) >= 2 and 0 <= q.get("answer", -1) < len(q["options"])):
            raise LearnError("A quiz question is malformed.")
    meta["objectives"] = [x.strip() for x in meta.get("objectives", "").split("|") if x.strip()]
    return {"meta": meta, "html": render_markdown(body.strip()), "quiz": quiz, "text": body.strip()}


def lesson(lesson_id: str) -> dict:
    if not ID_RE.match(lesson_id or ""):
        raise LearnError("No such lesson.")
    idx = _lesson_index()
    info = idx.get(lesson_id)
    f = LEARN / "lessons" / f"{lesson_id}.md"
    if not info or not f.exists():
        raise LearnError("This lesson has not been written yet. It is on the syllabus; contributions are welcome.")
    data = parse_lesson(f.read_text(encoding="utf-8"))
    order = [k for k, v in idx.items() if (LEARN / "lessons" / f"{k}.md").exists()]
    i = order.index(lesson_id)
    quiz_public = [{"q": q["q"], "options": q["options"]} for q in data["quiz"]]
    return {"id": lesson_id, **info, "objectives": data["meta"]["objectives"], "html": data["html"], "quiz": quiz_public,
            "prev": order[i - 1] if i > 0 else None, "next": order[i + 1] if i + 1 < len(order) else None,
            "text": data["text"][:6000], "edu_lag_days": EDU_LAG_DAYS}


def grade(lesson_id: str, answers: list[int]) -> dict:
    if not ID_RE.match(lesson_id or ""):
        raise LearnError("No such lesson.")
    f = LEARN / "lessons" / f"{lesson_id}.md"
    if not f.exists():
        raise LearnError("No such lesson.")
    quiz = parse_lesson(f.read_text(encoding="utf-8"))["quiz"]
    results = [{"correct": i < len(answers) and answers[i] == q["answer"], "answer": q["answer"], "why": q.get("why", "")}
               for i, q in enumerate(quiz)]
    score = sum(r["correct"] for r in results) / len(results) if results else 1.0
    passed = score >= 0.6
    if passed:
        with db.connect() as con:
            con.execute("INSERT INTO lesson_progress (lesson_id, completed_on, quiz_score) VALUES (?,?,?) "
                        "ON CONFLICT(lesson_id) DO UPDATE SET quiz_score=MAX(quiz_score, excluded.quiz_score)",
                        (lesson_id, date.today().isoformat(), round(score, 3)))
        db.touch_activity("learn")
    return {"score": round(score, 3), "passed": passed, "results": results,
            "message": "Lesson complete." if passed else "Not yet: 60% marks the lesson complete. Reread and try again."}


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
            for l in m["lessons"]:
                l["written"] = (LEARN / "lessons" / f"{l['id']}.md").exists()
                l["done"] = l["id"] in done
                ready_total += l["written"]
    return {"syllabus": syl, "completed": len(done), "available": ready_total, "streak_days": streak}
