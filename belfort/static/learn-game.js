"use strict";
/* Gamified Learn (T42): the stage path, lesson cards, exercises, hearts, XP, streak and mascot.
   Loaded after verticals.js so it takes over the Learn view. It uses the helpers from app.js and verticals.js
   ($, esc, api, post, status, glossify, setCrumb, openChat, drawLessonChart) and the endpoints under /api/learn.
   XP, hearts and streaks are virtual: nothing here can be redeemed or bought. */

const LG = { path: null, run: null, goalMenu: false };
const LG_CALM = window.matchMedia("(prefers-reduced-motion: reduce)");
const LG_DX = [0, 40, 64, 40, 0, -40, -64, -40];
const LG_BLURB = {
  beginner: "How the market works, reading charts, risk first, and staying safe from tips and scams.",
  intermediate: "Setups, the business check, indicators, the journal, and taxes and records.",
  advanced: "Market context, running several trades, and the psychology of discipline.",
};
const LG_ICON = { lesson: "★", checkpoint: "⚑", stage_test: "🏆" };

/* ---------- small helpers ---------- */
function lgMascot(kind, cls) {
  const file = kind === "shrug" ? "mascot-shrug" : "mascot-suit";
  // With reduced motion the animated GIF is replaced by a still of its final frame.
  return `<img class="lg-mascot ${cls || ""}" src="img/mascot/${file}${LG_CALM.matches ? "-still.png" : ".gif"}" alt="">`;
}
function lgCountUp(el, to) {
  if (LG_CALM.matches || to === 0) { el.textContent = "+" + to; return; }
  const t0 = performance.now(), dur = 900;
  const tick = (t) => {
    const k = Math.min(1, (t - t0) / dur);
    el.textContent = "+" + Math.round(to * (1 - Math.pow(1 - k, 3)));
    if (k < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
function lgConfetti() {
  if (LG_CALM.matches) return;
  const c = document.createElement("canvas");
  c.className = "lg-confetti"; c.width = innerWidth; c.height = innerHeight;
  document.body.appendChild(c);
  const g = c.getContext("2d"), colors = ["#facc15", "#22c55e", "#f4f4f2", "#ffe27a", "#ef4444"];
  const bits = Array.from({ length: 150 }, () => ({
    x: innerWidth / 2 + (Math.random() - 0.5) * 160, y: innerHeight * 0.55,
    vx: (Math.random() - 0.5) * 16, vy: -Math.random() * 17 - 5, s: 5 + Math.random() * 6,
    r: Math.random() * 6.28, vr: (Math.random() - 0.5) * 0.4, c: colors[(Math.random() * colors.length) | 0],
  }));
  const t0 = performance.now();
  (function frame(t) {
    g.clearRect(0, 0, c.width, c.height);
    bits.forEach((b) => {
      b.vy += 0.45; b.x += b.vx; b.y += b.vy; b.r += b.vr;
      g.save(); g.translate(b.x, b.y); g.rotate(b.r); g.fillStyle = b.c; g.fillRect(-b.s / 2, -b.s / 4, b.s, b.s / 2); g.restore();
    });
    if (t - t0 < 2800) requestAnimationFrame(frame); else c.remove();
  })(t0);
}
const lgHeartsHtml = (p) => `<span class="lg-pill lg-hearts ${p.hearts === 0 ? "empty" : ""}" title="Hearts: a wrong answer costs one. They refill every day." id="lg-hearts"><i>♥</i>${p.hearts}</span>`;
function lgRing(p, size) {
  const r = 15, c = 2 * Math.PI * r, k = Math.min(1, p.xp_today / p.goal);
  return `<svg class="lg-ring ${p.goal_met ? "met" : ""}" width="${size}" height="${size}" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="${r}" class="bg"/><circle cx="18" cy="18" r="${r}" class="fg" stroke-dasharray="${(c * k).toFixed(1)} ${c.toFixed(1)}" transform="rotate(-90 18 18)"/></svg>`;
}
function lgBar(p) {
  return `<div class="lg-bar" role="group" aria-label="Your Learn numbers">
    <span class="lg-pill lg-streak ${p.streak ? "on" : ""}" title="Days in a row with your daily goal met. A freeze saves one missed day."><i>🔥</i>${p.streak}${p.freezes ? `<small title="Streak freezes held">❄${p.freezes}</small>` : ""}</span>
    <span class="lg-pill lg-xp" title="XP: virtual points for finishing lessons. Not redeemable for anything."><i>⚡</i>${p.xp_total} XP</span>
    ${lgHeartsHtml(p)}
    <button type="button" class="lg-pill lg-goal" id="lg-goal" title="Daily goal: ${p.xp_today} of ${p.goal} XP today. Click to change.">${lgRing(p, 26)}<span>${p.xp_today}/${p.goal}</span></button>
    ${p.weak_spots ? `<button type="button" class="btn ghost sm lg-weak ${p.hearts === 0 ? "urgent" : ""}" id="lg-weak">Weak spots (${p.weak_spots})</button>` : ""}
    ${LG.goalMenu ? `<div class="lg-goalmenu" role="menu"><b>Daily goal</b>${LG.path.goals.map((g) => `<button type="button" class="btn ${g === p.goal ? "" : "ghost"} sm" data-goal="${g}">${g} XP</button>`).join("")}</div>` : ""}
  </div>`;
}

/* ---------- the path ---------- */
onView.learn = async (opts) => {
  if (opts && opts.lesson) return lgOpenLesson(opts.lesson);
  lgShowPath();
};

async function lgShowPath(scrollToNext) {
  LG.run = null;
  document.querySelector("#learn .intro").hidden = true;
  $("learn-stats").hidden = true; $("lesson").hidden = true; $("learn-body").hidden = false;
  setCrumb();
  try {
    LG.path = await api("/api/learn/path");
    lgRenderPath();
    if (scrollToNext) document.querySelector(".lg-node.next")?.scrollIntoView({ block: "center", behavior: LG_CALM.matches ? "auto" : "smooth" });
  } catch (e) {
    $("learn-body").innerHTML = `<div class="lg-empty">${lgMascot("shrug", "big")}<p>${esc(e.message)}</p></div>`;
    }
}

function lgNode(n, i) {
  const dx = LG_DX[i % LG_DX.length];
  const lockedLike = n.state === "locked";
  const icon = n.state === "locked" ? "🔒" : n.state === "done" && n.kind === "lesson" ? "✓" : n.state === "done" ? "✓" : LG_ICON[n.kind];
  const label = n.kind === "lesson" ? `${esc(n.title)}${n.minutes ? `<span>${n.minutes} min</span>` : ""}` : esc(n.title);
  const note = n.state === "soon" ? "<span>Coming soon</span>" : "";
  return `<div class="lg-row ${n.kind}" style="--dx:${dx}px; --i:${i}">
    ${n.state === "next" ? '<span class="lg-start">Start</span>' : ""}
    <button type="button" class="lg-node ${n.state} ${n.kind}" data-node="${esc(n.kind)}:${esc(n.id)}" data-state="${n.state}" aria-label="${esc(n.title)}, ${lockedLike ? "locked" : n.state}">
      ${icon}${n.perfect ? '<b class="lg-crown" title="Perfect quiz">👑</b>' : ""}
    </button>
    <div class="lg-label ${n.state}">${label}${note}</div>
  </div>`;
}

function lgRenderPath() {
  const d = LG.path, p = d.profile;
  const stageHtml = d.stages.map((s, si) => {
    let i = 0;
    const pct = s.lessons_total ? Math.round((100 * s.lessons_done) / s.lessons_total) : 0;
    const lockNote = s.unlocked ? "" : `<p class="lg-lock-note">🔒 Locked. Pass the ${esc(d.stages[si - 1].title)} stage test with 80% or more${si === 1 ? ", or test out of Beginner" : ""} to open it.</p>`;
    const testOut = si === 1 && !s.unlocked ? `<button type="button" class="btn ghost sm" data-placement="1">Test out of Beginner</button>` : "";
    return `<section class="lg-stage ${s.key} ${s.unlocked ? "open" : "locked"}">
      <header class="lg-stage-head">
        <div><div class="eyebrow">Stage ${si + 1}</div><h2>${esc(s.title)}</h2><p>${esc(LG_BLURB[s.key])}</p>${lockNote}${testOut}</div>
        <div class="lg-stage-prog" aria-label="${s.lessons_done} of ${s.lessons_total} lessons done"><b>${s.lessons_done}<small>/${s.lessons_total}</small></b><div class="lg-meter"><i style="width:${pct}%"></i></div></div>
      </header>
      <div class="lg-path">
        ${s.modules.map((m) => `<div class="lg-module"><div class="lg-module-label">${esc(m.title)}</div>${m.nodes.map((n) => lgNode(n, i++)).join("")}</div>`).join("")}
        <div class="lg-module"><div class="lg-module-label">Stage test</div>${lgNode(s.test, i++)}</div>
      </div>
    </section>`;
  }).join("");
  const banner = d.placement_offered ? `<div class="lg-banner">${lgMascot("suit", "med")}<div><b>Already know the basics?</b><p>Test out of Beginner: 12 questions from the Beginner lessons. Score 80% or more and Intermediate opens.</p>
      <div class="row"><button type="button" class="btn" data-placement="1">Test out of Beginner</button><button type="button" class="btn ghost" id="lg-dismiss">Start from the beginning</button></div></div></div>` : "";
  const hello = d.lessons_done === 0 ? `<p class="lg-hello">Pick the glowing circle to start your first lesson. Five hearts a day: a wrong answer costs one.</p>` : "";
  $("learn-body").innerHTML = `<div class="lg">${lgBar(p)}${banner}${hello}<div class="lg-stages">${stageHtml}</div>
    <p class="src">XP, hearts and streaks are virtual: they cannot be redeemed or bought. Learning content is educational and is not a recommendation to buy, sell or hold anything.</p></div>`;
}

$("learn-body").addEventListener("click", async (e) => {
  const t = e.target;
  if (t.closest("#lg-goal")) { LG.goalMenu = !LG.goalMenu; return lgRenderPath(); }
  const g = t.closest("button[data-goal]");
  if (g) {
    try { await api("/api/learn/goal", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ goal: +g.dataset.goal }) }); } catch (err) { status(err.message, true); }
    LG.goalMenu = false; return lgShowPath();
  }
  if (t.closest("#lg-weak")) return lgStartWeak();
  if (t.closest("#lg-dismiss")) { await post("/api/learn/placement/dismiss"); return lgShowPath(); }
  if (t.closest("button[data-placement]")) return lgStartTest("placement", "beginner");
  const b = t.closest("button[data-node]");
  if (!b) return;
  const [kind, id] = b.dataset.node.split(":");
  const state = b.dataset.state;
  if (state === "locked" || state === "waiting" || state === "soon") {
    b.classList.remove("shake"); void b.offsetWidth; b.classList.add("shake");
    const msg = state === "locked" ? "Locked. Finish the stage before it, or test out of Beginner, to open this."
      : state === "soon" ? "Coming soon. This lesson is on the syllabus but has not been written yet."
        : kind === "stage_test" ? "Finish every lesson in this stage to open its test." : "Finish the lessons in this module to open its checkpoint.";
    return status(msg, state === "locked");
  }
  if (kind === "lesson") return lgOpenLesson(id);
  if (kind === "checkpoint") return lgStartTest("checkpoint", id);
  if (kind === "stage_test") return lgStartTest("stage", id);
});

/* ---------- starting a run ---------- */
function lgShowPlayer() {
  document.querySelector("#learn .intro").hidden = true; $("learn-stats").hidden = true; $("learn-body").hidden = true;
  $("lesson").hidden = false; scrollTo(0, 0);
}
async function lgOpenLesson(id) {
  try {
    const d = await api("/api/learn/lessons/" + encodeURIComponent(id));
    S.chatCtx = { view: "learn", mode: "lesson", text: `${d.title}\n${d.text}` };
    LG.run = { kind: "lesson", id, title: d.title, meta: d, cards: d.cards, qs: d.quiz, answers: [], i: 0, phase: "cards", mistakes: 0, hearts: LG.path ? LG.path.profile.hearts : 5, checked: null };
    if (!LG.run.cards.length) LG.run.phase = LG.run.qs.length ? "quiz" : "result";
    setCrumb(d.title); lgShowPlayer(); lgRenderRun();
  } catch (e) {
    if (/hearts/i.test(e.message)) return lgOutOfHearts();
    status(e.message, true);
    if (!LG.path) lgShowPath();
  }
}
async function lgStartTest(kind, key) {
  try {
    const d = await api(`/api/learn/tests/${kind}/${encodeURIComponent(key)}`);
    LG.run = { kind, key, title: d.title, session: d.session, passPercent: d.pass_percent, cards: [], qs: d.questions, answers: [], i: 0, phase: "quiz", hearts: LG.path.profile.hearts, checked: null };
    setCrumb(d.title); lgShowPlayer(); lgRenderRun();
  } catch (e) { status(e.message, true); }
}
async function lgStartWeak() {
  try {
    const d = await api("/api/learn/weak-spots");
    if (!d.session) { lgShowPlayer(); return lgEmpty("No weak spots", "Nothing to review right now. Questions you miss in lessons show up here."); }
    LG.run = { kind: "weak", title: d.title, session: d.session, cards: [], qs: d.questions, answers: [], i: 0, phase: "quiz", hearts: LG.path.profile.hearts, checked: null };
    setCrumb("Weak spots"); lgShowPlayer(); lgRenderRun();
  } catch (e) { status(e.message, true); }
}
function lgEmpty(title, text, extra) {
  $("lesson").innerHTML = `<div class="lg-run"><div class="lg-empty">${lgMascot("shrug", "big")}<h2>${esc(title)}</h2><p>${esc(text)}</p>${extra || ""}<button type="button" class="btn" id="lg-leave">Back to the path</button></div></div>`;
}
function lgOutOfHearts() {
  lgShowPlayer();
  const weak = LG.path && LG.path.profile.weak_spots;
  lgEmpty("You are out of hearts", "Hearts refill every day. You can refill them now by finishing a Weak spots review.",
    weak ? '<button type="button" class="btn ghost" id="lg-weak-go">Weak spots review</button>' : "");
}

/* ---------- the player ---------- */
function lgRenderRun() {
  const r = LG.run, el = $("lesson");
  const total = r.cards.length + r.qs.length;
  const doneN = r.phase === "cards" ? r.i : r.phase === "quiz" ? r.cards.length + r.i : total;
  const top = `<div class="lg-top"><button type="button" class="lg-x" id="lg-leave" aria-label="Leave">✕</button>
    <div class="lg-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round((100 * doneN) / Math.max(1, total))}"><i style="width:${(100 * doneN) / Math.max(1, total)}%"></i></div>
    ${r.kind === "lesson" ? lgHeartsHtml({ hearts: r.hearts }) : ""}
    ${r.kind === "lesson" ? '<button type="button" class="btn ghost sm" id="lg-ask">Ask</button>' : ""}</div>`;
  if (r.phase === "cards") {
    const c = r.cards[r.i], first = r.i === 0, last = r.i === r.cards.length - 1;
    const intro = first && r.kind === "lesson" ? `<div class="eyebrow">${esc(r.meta.track_title)} · ${esc(r.meta.module_title)} · ${r.meta.minutes} min</div><h1 class="lesson-title">${esc(r.title)}</h1>
      ${r.meta.objectives.length ? `<div class="note plain"><b>By the end you can</b><ul class="plain">${r.meta.objectives.map((o) => `<li>${esc(o)}</li>`).join("")}</ul></div>` : ""}` : "";
    el.innerHTML = `<div class="lg-run">${top}<div class="lg-card" data-card="${r.i}">${intro}<div class="lesson-body">${c.html}</div></div>
      <div class="lg-foot"><span class="hint">Card ${r.i + 1} of ${r.cards.length}</span><button type="button" class="btn" id="lg-next">${last ? (r.qs.length ? "Start the exercises" : "Finish") : "Continue"}</button></div></div>`;
    glossify(el.querySelector(".lesson-body"));
    el.querySelectorAll(".lg-card .lesson-chart").forEach(drawLessonChart);
    scrollTo(0, 0);
  } else if (r.phase === "quiz") {
    lgRenderQuestion(top);
  } else if (r.phase === "grading") {
    el.innerHTML = `<div class="lg-run">${top}<div class="lg-empty"><p>Checking your answers…</p></div></div>`;
  }
}

function lgQuestionBody(q) {
  if (q.type === "tf") return `<div class="lg-opts tf"><button type="button" class="lg-opt" data-v="true">True</button><button type="button" class="lg-opt" data-v="false">False</button></div>`;
  if (q.type === "order") return `<p class="hint">Tap the items in the right order. Tap one in your answer to take it back.</p><div class="lg-line" id="lg-line" aria-label="Your order"></div><div class="lg-bank" id="lg-bank"></div>`;
  if (q.type === "number") return `<div class="lg-num"><input id="lg-num" type="number" step="any" inputmode="decimal" autocomplete="off" aria-label="Your answer">${q.unit ? `<span>${esc(q.unit)}</span>` : ""}</div>`;
  return `<div class="lg-opts">${q.options.map((o, j) => `<button type="button" class="lg-opt" data-v="${j}"><kbd>${j + 1}</kbd><span>${esc(o)}</span></button>`).join("")}</div>`;
}
function lgRenderQuestion(top) {
  const r = LG.run, q = r.qs[r.i], el = $("lesson");
  r.sel = q.type === "order" ? [] : null; r.checked = null;
  el.innerHTML = `<div class="lg-run">${top}<div class="lg-q"><div class="eyebrow">${esc(r.kind === "weak" ? "Weak spots" : r.title)} · ${r.i + 1} of ${r.qs.length}</div>
    <h2 class="lg-qtext">${esc(q.q)}</h2>${lgQuestionBody(q)}</div>
    <div class="lg-foot" id="lg-foot"><button type="button" class="btn" id="lg-check" disabled>${r.kind === "lesson" ? "Check" : "Next"}</button></div></div>`;
  if (q.type === "order") lgDrawOrder();
  if (q.type === "number") $("lg-num").focus();
}
function lgDrawOrder() {
  const r = LG.run, q = r.qs[r.i];
  const bank = q.items.filter((x) => !r.sel.includes(x));
  $("lg-line").innerHTML = r.sel.map((x, k) => `<button type="button" class="lg-chip placed" data-put="${esc(x)}"><i>${k + 1}</i>${esc(x)}</button>`).join("") || '<span class="hint">Your order appears here</span>';
  $("lg-bank").innerHTML = bank.map((x) => `<button type="button" class="lg-chip" data-take="${esc(x)}">${esc(x)}</button>`).join("");
  $("lg-check").disabled = r.sel.length !== q.items.length;
}
function lgCurrentAnswer() {
  const r = LG.run, q = r.qs[r.i];
  if (q.type === "order") return r.sel.length === q.items.length ? r.sel.slice() : undefined;
  if (q.type === "number") { const v = $("lg-num").value.trim(); return v === "" || isNaN(+v) ? undefined : +v; }
  return r.sel === null ? undefined : r.sel;
}
function lgFormatAnswer(q, a, unit) {
  if (q.type === "mc") return q.options[a];
  if (q.type === "tf") return a ? "True" : "False";
  if (q.type === "order") return a.join("  →  ");
  return a + (unit ? " " + unit : "");
}

async function lgCheck() {
  const r = LG.run, q = r.qs[r.i], ans = lgCurrentAnswer();
  if (ans === undefined) return;
  r.answers[r.i] = ans;
  if (r.kind !== "lesson") return lgAdvance();       // tests and reviews are graded at the end
  $("lg-check").disabled = true;
  let res;
  try { res = await post(`/api/learn/lessons/${encodeURIComponent(r.id)}/check`, { index: r.i, answer: ans }); }
  catch (e) { status(e.message, true); if (/hearts/i.test(e.message)) return lgOutOfHearts(); $("lg-check").disabled = false; return; }
  r.checked = res; r.hearts = res.hearts;
  if (!res.correct) r.mistakes++;
  const sel = document.querySelectorAll(".lg-opt");
  sel.forEach((b) => {
    b.disabled = true;
    const v = b.dataset.v;
    const isRight = q.type === "mc" ? +v === res.answer : q.type === "tf" ? (v === "true") === res.answer : false;
    const isChosen = q.type === "mc" ? +v === ans : q.type === "tf" ? (v === "true") === ans : false;
    if (isRight) b.classList.add("right"); else if (isChosen) b.classList.add("wrong");
  });
  document.querySelectorAll(".lg-chip, #lg-num").forEach((x) => { x.disabled = true; });
  const fb = res.correct ? "good" : "bad";
  const hearts = document.getElementById("lg-hearts");
  if (!res.correct && hearts) { hearts.innerHTML = `<i class="break">♥</i>${res.hearts}`; hearts.classList.toggle("empty", res.hearts === 0); }
  $("lg-foot").className = "lg-foot " + fb;
  $("lg-foot").innerHTML = `<div class="lg-fb ${fb}" role="status">${lgMascot(res.correct ? "suit" : "shrug", "mini")}
    <div><b>${res.correct ? lgPraise() : "Not quite"}</b>
    ${res.correct ? "" : `<div class="lg-correct">Correct answer: ${esc(lgFormatAnswer(q, res.answer, res.unit))}</div>`}
    ${res.why ? `<p>${esc(res.why)}</p>` : ""}${res.out_of_hearts ? "<p><b>No hearts left.</b> You can refill them with a Weak spots review.</p>" : ""}</div></div>
    <button type="button" class="btn ${res.correct ? "" : "danger"}" id="lg-next">Continue</button>`;
  $("lg-next").focus();
}
const lgPraise = () => ["Correct!", "Right on.", "Nice work.", "Exactly."][(Math.random() * 4) | 0];

async function lgAdvance() {
  const r = LG.run;
  if (r.checked && r.checked.out_of_hearts) return lgOutOfHearts();
  if (r.i + 1 < r.qs.length) { r.i++; return lgRenderRun(); }
  r.phase = "grading"; lgRenderRun();
  try {
    const res = r.kind === "lesson"
      ? await post(`/api/learn/lessons/${encodeURIComponent(r.id)}/quiz`, { answers: r.answers })
      : await post(`/api/learn/sessions/${encodeURIComponent(r.session)}/grade`, { answers: r.answers });
    lgResults(res);
  } catch (e) {
    if (/hearts/i.test(e.message)) return lgOutOfHearts();
    status(e.message, true); lgShowPath();
  }
}

function lgResults(res) {
  const r = LG.run, el = $("lesson"), p = res.profile;
  const n = res.results.length, right = res.results.filter((x) => x.correct).length;
  const pct = Math.round(res.score * 100);
  let head, sub, win = res.passed;
  if (r.kind === "weak") { win = true; head = "Review done"; sub = "Your hearts are back to full."; }
  else if (r.kind === "lesson") { head = res.passed ? (res.perfect ? "Perfect lesson!" : "Lesson complete") : "Not quite yet"; sub = res.passed ? "" : res.message; }
  else if (r.kind === "placement") { head = res.passed ? "You tested out of Beginner" : "Not this time"; sub = res.passed ? "Intermediate is open." : `You need ${res.pass_percent}% to test out. The Beginner lessons are the way in.`; }
  else { head = res.passed ? (r.kind === "stage" ? "Stage complete!" : "Module complete!") : "Not quite yet"; sub = res.passed ? "" : `You need ${res.pass_percent}% to pass. Review the lessons and try again.`; }
  if (res.unlocked_stage) sub = `${res.unlocked_stage.charAt(0).toUpperCase() + res.unlocked_stage.slice(1)} is unlocked.`;
  const breakdown = r.kind === "lesson" ? "" : `<ol class="lg-review">${res.results.map((x, i) => `<li class="${x.correct ? "ok" : "no"}"><b>${esc(r.qs[i].q)}</b>${x.correct ? "" : `<div class="lg-correct">Correct answer: ${esc(lgFormatAnswer(r.qs[i], x.answer, x.unit))}</div>`}${x.why ? `<p>${esc(x.why)}</p>` : ""}</li>`).join("")}</ol>`;
  const retry = !win && r.kind !== "weak" ? `<button type="button" class="btn ghost" id="lg-retry">${r.kind === "lesson" ? "Try the lesson again" : "Try again"}</button>` : "";
  el.innerHTML = `<div class="lg-run lg-result">
    ${lgMascot(win ? "suit" : "shrug", "big")}
    <h1>${esc(head)}</h1>${sub ? `<p class="lg-sub">${esc(sub)}</p>` : ""}
    <div class="lg-tiles">
      ${res.xp_earned || r.kind === "lesson" || r.kind === "weak" ? `<div class="lg-tile xp"><span class="eyebrow">XP earned</span><b id="lg-xp">+0</b></div>` : ""}
      <div class="lg-tile"><span class="eyebrow">Correct</span><b>${right}<small>/${n}</small></b><span class="hint">${pct}%</span></div>
      <div class="lg-tile"><span class="eyebrow">Daily goal</span><div class="lg-goalwrap">${lgRing(p, 54)}<b>${p.xp_today}<small>/${p.goal}</small></b></div>${res.goal_reached_now ? '<span class="hint good">Goal reached!</span>' : ""}</div>
      <div class="lg-tile"><span class="eyebrow">Streak</span><b>🔥 ${p.streak}</b>${p.freezes ? `<span class="hint">❄ ${p.freezes} freeze${p.freezes > 1 ? "s" : ""}</span>` : ""}</div>
    </div>
    ${breakdown}
    <div class="row lg-actions">${retry}<button type="button" class="btn" id="lg-done">Continue</button></div>
  </div>`;
  const xp = document.getElementById("lg-xp"); if (xp) lgCountUp(xp, res.xp_earned);
  if (res.unlocked_stage || (res.passed && (r.kind === "checkpoint" || r.kind === "stage"))) lgConfetti();
  else if (r.kind === "lesson" && res.perfect) lgConfetti();
  scrollTo(0, 0);
  r.phase = "result";
}

/* ---------- events inside the player ---------- */
$("lesson").addEventListener("click", async (e) => {
  if (!LG.run && !e.target.closest("#lg-leave")) return;
  const t = e.target, r = LG.run;
  if (t.closest("#lg-leave")) {
    if (r && r.phase === "quiz" && r.i > 0 && !confirm("Leave now? Your progress in this run will be lost.")) return;
    return lgShowPath();
  }
  if (t.closest("#lg-done")) return lgShowPath(true);
  if (t.closest("#lg-weak-go")) return lgStartWeak();
  if (t.closest("#lg-ask")) return openChat("Explain the main idea of this lesson with a new example.");
  if (t.closest("#lg-retry")) return r.kind === "lesson" ? lgOpenLesson(r.id) : lgStartTest(r.kind, r.key);
  if (!r) return;
  if (t.closest("#lg-next")) {
    if (r.phase === "cards") {
      if (r.i + 1 < r.cards.length) { r.i++; return lgRenderRun(); }
      if (r.qs.length) { r.phase = "quiz"; r.i = 0; return lgRenderRun(); }
      return lgAdvance();
    }
    return lgAdvance();
  }
  if (t.closest("#lg-check")) return lgCheck();
  const opt = t.closest(".lg-opt");
  if (opt && !r.checked) {
    r.sel = r.qs[r.i].type === "tf" ? opt.dataset.v === "true" : +opt.dataset.v;
    document.querySelectorAll(".lg-opt").forEach((b) => b.classList.toggle("picked", b === opt));
    $("lg-check").disabled = false;
    return;
  }
  const take = t.closest("[data-take]"), put = t.closest("[data-put]");
  if (take && !r.checked) { r.sel.push(take.dataset.take); return lgDrawOrder(); }
  if (put && !r.checked) { r.sel.splice(r.sel.indexOf(put.dataset.put), 1); return lgDrawOrder(); }
});
$("lesson").addEventListener("input", (e) => {
  if (e.target.id === "lg-num" && LG.run) $("lg-check").disabled = lgCurrentAnswer() === undefined;
});
document.addEventListener("keydown", (e) => {
  const r = LG.run;
  if (!r || $("lesson").hidden || S.view !== "learn" || /^(TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) return;
  if (e.key === "Enter") {
    if (document.activeElement.tagName === "BUTTON") return;   // the focused button handles Enter itself
    const b = $("lg-next") || $("lg-done") || (document.getElementById("lg-check") && !document.getElementById("lg-check").disabled ? $("lg-check") : null);
    if (b) { e.preventDefault(); b.click(); }
  } else if (r.phase === "quiz" && !r.checked && r.qs[r.i].type === "mc" && /^[1-9]$/.test(e.key)) {
    document.querySelectorAll(".lg-opt")[+e.key - 1]?.click();
  }
});

/* The old syllabus list from verticals.js is replaced by the path; make its late render (if any) a no-op. */
renderSyllabus = () => {};

/* app.js may already have opened #learn with the old loader while this file was still loading: draw the path now. */
if (S.view === "learn") onView.learn({});
