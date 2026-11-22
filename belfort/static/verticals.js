"use strict";
/* Learn, Practice, News and Settings. Uses the helpers defined in app.js ($, esc, api, inr, num, glossify, go, ...). */

const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? u : "#");
const ago = (iso) => {
  if (!iso) return "";
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (m < 1) return "just now";
  if (m < 60) return m + " min ago";
  if (m < 1440) return Math.round(m / 60) + " h ago";
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
};
const pctTxt = (x, d = 0) => (x == null ? "n/a" : (x * 100).toFixed(d) + "%");
const stat = (k, v, n, on) => `<div class="card-list stat-card ${on ? "on" : ""}"><span class="eyebrow">${esc(k)}</span><span class="n">${v}</span>${n ? `<span class="s">${esc(n)}</span>` : ""}</div>`;
const post = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });

function candleChart(el, candles, opts) {
  if (!window.LightweightCharts) { el.innerHTML = '<p class="missing">The chart library could not be loaded (it needs an internet connection).</p>'; return null; }
  el.innerHTML = "";
  const c = LightweightCharts.createChart(el, { autoSize: true, layout: { background: { color: "transparent" }, textColor: "#8b8b90", fontFamily: "Inter, sans-serif" },
    grid: { vertLines: { color: "rgba(255,255,255,.04)" }, horzLines: { color: "rgba(255,255,255,.05)" } }, rightPriceScale: { borderColor: "rgba(255,255,255,.08)" },
    timeScale: { borderColor: "rgba(255,255,255,.08)", visible: !(opts && opts.hideTime) }, crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    handleScroll: !(opts && opts.locked), handleScale: !(opts && opts.locked) });
  const s = c.addCandlestickSeries({ upColor: "#16c47f", downColor: "#ef4444", borderVisible: false, wickUpColor: "#16c47f", wickDownColor: "#ef4444" });
  s.setData(candles);
  c.timeScale().fitContent();
  return { chart: c, series: s };
}

/* ======================= LEARN ======================= */
const L = { data: null, lesson: null };

onView.learn = async (opts) => {
  if (opts.lesson) return openLesson(opts.lesson);
  $("lesson").hidden = true; $("learn-body").hidden = false; $("learn-stats").hidden = false;
  document.querySelector("#learn .intro").hidden = false;
  try { L.data = await api("/api/learn/syllabus"); renderSyllabus(); } catch (e) { $("learn-body").innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
};

function renderSyllabus() {
  const d = L.data, syl = d.syllabus;
  const total = syl.tracks.reduce((a, t) => a + t.modules.reduce((b, m) => b + m.lessons.length, 0), 0);
  $("learn-stats").innerHTML = stat("Lessons done", `${d.completed}<small>/${d.available}</small>`, `${d.available} written of ${total} on the syllabus`, true)
    + stat("Learning streak", d.streak_days, d.streak_days === 1 ? "day in a row" : "days in a row")
    + stat("Tracks", syl.tracks.length, "Foundations, Practitioner, Advanced");
  const lessonRow = (l) => l.written
    ? `<button type="button" class="lrow ${l.done ? "done" : ""}" data-lesson="${esc(l.id)}"><span class="tick">${l.done ? "✓" : ""}</span><span class="lt">${esc(l.title)}</span><span class="lm">${l.minutes} min</span></button>`
    : `<div class="lrow planned"><span class="tick"></span><span class="lt">${esc(l.title)}</span><span class="lm">planned</span></div>`;
  $("learn-body").innerHTML = syl.tracks.map((t, ti) => `
    <div class="track">
      <div class="track-head"><span class="no">0${ti + 1}</span><div><div class="eyebrow">${esc(t.level)}</div><h2>${esc(t.title)}</h2><p>${esc(t.summary)}</p></div></div>
      <div class="modules">${t.modules.map((m) => `<div class="panel glass module"><h3>${esc(m.title)}</h3><p class="hint">${esc(m.why)}</p>
        <div class="lrows">${m.lessons.map(lessonRow).join("")}</div></div>`).join("")}</div>
    </div>`).join("") + `
    <details class="panel glass screening"><summary><b>How this syllabus was chosen</b><span class="hint"> · the five tests every topic must pass, and what we left out on purpose</span></summary>
      <p>${esc(syl.promise)}</p>
      <ol class="plain">${syl.screening_test.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>
      <h4>Left out on purpose</h4>
      <div class="scroll"><table><thead><tr><th>Topic</th><th>Why it is not here</th></tr></thead><tbody>
        ${syl.skipped.map((x) => `<tr><td><b>${esc(x.topic)}</b></td><td>${esc(x.why)}</td></tr>`).join("")}</tbody></table></div>
      <p class="src">Planned lessons are open for contributors: see CONTRIBUTING.md in the repository.</p>
    </details>`;
  glossify($("learn-body"));
}
$("learn-body").addEventListener("click", (e) => { const b = e.target.closest("button[data-lesson]"); if (b) openLesson(b.dataset.lesson); });

async function openLesson(id) {
  try {
    const d = await api("/api/learn/lessons/" + encodeURIComponent(id));
    L.lesson = d;
    S.chatCtx = { view: "learn", mode: "lesson", text: `${d.title}\n${d.text}` };
    document.querySelector("#learn .intro").hidden = true; $("learn-stats").hidden = true; $("learn-body").hidden = true;
    const el = $("lesson"); el.hidden = false;
    el.innerHTML = `<button type="button" class="back" id="lesson-back"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M15 6l-6 6 6 6"/></svg>Syllabus</button>
      <article class="lesson">
        <div class="eyebrow">${esc(d.track_title)} · ${esc(d.module_title)} · ${d.minutes} min</div>
        <h1 class="lesson-title">${esc(d.title)}</h1>
        ${d.objectives.length ? `<div class="note plain"><b>By the end you can</b><ul class="plain">${d.objectives.map((o) => `<li>${esc(o)}</li>`).join("")}</ul></div>` : ""}
        <div class="lesson-body">${d.html}</div>
        ${d.quiz.length ? `<form class="panel glass quiz" id="quiz"><h3>Check yourself</h3>${d.quiz.map((q, i) => `<fieldset data-q="${i}"><legend>${i + 1}. ${esc(q.q)}</legend>
          ${q.options.map((o, j) => `<label class="opt"><input type="radio" name="q${i}" value="${j}"><span>${esc(o)}</span></label>`).join("")}<div class="why" hidden></div></fieldset>`).join("")}
          <div class="row"><button type="submit" class="btn">Check answers</button><span class="hint" id="quiz-msg"></span></div></form>` : ""}
        <div class="lesson-nav">${d.prev ? `<button type="button" class="btn ghost" data-lesson="${esc(d.prev)}">← Previous</button>` : "<span></span>"}
          <button type="button" class="btn ghost" id="lesson-ask">Ask about this lesson</button>
          ${d.next ? `<button type="button" class="btn" data-lesson="${esc(d.next)}">Next lesson →</button>` : "<span></span>"}</div>
      </article>`;
    setCrumb(d.title);
    if (location.hash !== "#learn") history.replaceState(null, "", "#learn");
    glossify(el.querySelector(".lesson-body"));
    el.querySelectorAll(".lesson-chart").forEach(drawLessonChart);
    scrollTo(0, 0);
  } catch (e) { status(e.message, true); }
}
$("lesson").addEventListener("click", (e) => {
  if (e.target.closest("#lesson-back")) return onView.learn({});
  if (e.target.closest("#lesson-ask")) return openChat("Explain the main idea of this lesson with a new example.");
  const n = e.target.closest("button[data-lesson]"); if (n) return openLesson(n.dataset.lesson);
  const t = e.target.closest("button[data-try]");
  if (t) { const k = t.dataset.try; if (k === "research") { go("home"); $("q").focus(); } else { P.tab = k === "predict" ? "predict" : k === "replay" ? "replay" : "paper"; go("practice"); } }
});
$("lesson").addEventListener("submit", async (e) => {
  if (e.target.id !== "quiz") return;
  e.preventDefault();
  const f = e.target, n = L.lesson.quiz.length;
  const answers = [...Array(n).keys()].map((i) => { const c = f.querySelector(`input[name=q${i}]:checked`); return c ? +c.value : -1; });
  if (answers.includes(-1)) { $("quiz-msg").textContent = "Answer every question first."; return; }
  try {
    const r = await post(`/api/learn/lessons/${encodeURIComponent(L.lesson.id)}/quiz`, { answers });
    r.results.forEach((x, i) => {
      const fs = f.querySelector(`fieldset[data-q="${i}"]`);
      fs.classList.toggle("right", x.correct); fs.classList.toggle("wrong", !x.correct);
      fs.querySelectorAll("label.opt").forEach((lab, j) => lab.classList.toggle("answer", j === x.answer));
      const w = fs.querySelector(".why"); w.hidden = false; w.textContent = (x.correct ? "Right. " : "Not quite. ") + x.why;
    });
    $("quiz-msg").textContent = `${Math.round(r.score * 100)}% · ${r.message}`;
  } catch (err) { $("quiz-msg").textContent = err.message; }
});

async function drawLessonChart(el) {
  el.innerHTML = '<p class="hint">Loading a past chart…</p>';
  try {
    const d = await api(`/api/learn/example?symbol=${encodeURIComponent(el.dataset.symbol)}&bars=${el.dataset.bars}`);
    el.innerHTML = `<div class="lc"></div><div class="src">${esc(d.symbol)}, daily candles ending ${esc(d.ends)}. ${esc(d.note)}</div>`;
    candleChart(el.querySelector(".lc"), d.candles);
  } catch (e) { el.innerHTML = `<p class="missing">The example chart could not be loaded: ${esc(e.message)}</p>`; }
}

/* ======================= PRACTICE ======================= */
const P = { tab: "paper", pf: null, pred: null, replay: null };

onView.practice = () => { renderPracticeTabs(); loadPractice(); };
function renderPracticeTabs() { document.querySelectorAll("#practice-tabs button").forEach((b) => b.classList.toggle("on", b.dataset.p === P.tab)); }
$("practice-tabs").addEventListener("click", (e) => { const b = e.target.closest("button[data-p]"); if (b) { P.tab = b.dataset.p; status(""); renderPracticeTabs(); loadPractice(); } });

async function loadPractice() {
  const body = $("practice-body");
  body.innerHTML = '<p class="hint">Loading…</p>';
  try {
    if (P.tab === "paper") { P.pf = await api("/api/practice/portfolio"); renderPaper(); }
    else if (P.tab === "predict") { P.pred = await api("/api/practice/predictions"); renderPredict(); }
    else renderReplayIntro();
  } catch (e) { body.innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
}

function renderPaper() {
  const d = P.pf, st = d.stats;
  const tr = (cells) => `<tr>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`;
  const rTxt = (r) => (r == null ? "n/a" : `<span class="${r >= 0 ? "up" : "down"}">${r >= 0 ? "+" : ""}${r}R</span>`);
  $("practice-body").innerHTML = `
    <div class="cards">${stat("Account value", num(d.equity, 0), `${d.return_pct >= 0 ? "+" : ""}${d.return_pct}% since start`, true)}
      ${stat("Available points", num(d.available, 0), d.reserved ? `${num(d.reserved, 0)} held for pending orders` : "ready to use")}
      ${stat("Win rate", st.win_rate == null ? "n/a" : pctTxt(st.win_rate), `${st.closed} closed trades`)}
      ${stat("Average R", st.avg_r == null ? "n/a" : (st.avg_r >= 0 ? "+" : "") + st.avg_r, "result per trade, in units of risk")}</div>
    <div class="layout practice-layout">
      <div class="col-main">
        <div class="panel glass"><h3>Open positions</h3>${d.open.length ? `<div class="scroll"><table><thead><tr><th>Stock</th><th class="num">Qty</th><th class="num">Entry</th><th class="num">Last close</th><th class="num">Stop</th><th class="num">Target</th><th class="num">P&amp;L</th><th class="num">Now</th><th></th></tr></thead><tbody>
          ${d.open.map((t) => tr([`<b>${esc(t.symbol)}</b><div class="src">${esc(t.thesis)}</div>`, num(t.qty, 0), inr(t.entry_price), inr(t.last), inr(t.stop), t.target ? inr(t.target) : "n/a",
            `<span class="${t.pnl >= 0 ? "up" : "down"}">${num(t.pnl, 0)}</span>`, rTxt(t.open_r),
            t.close_requested_on ? '<span class="hint">exit at next open</span>' : `<button type="button" class="btn ghost sm" data-close="${t.id}">Exit</button>`])).join("")}</tbody></table></div>`
          : '<p class="missing">No open positions.</p>'}</div>
        ${d.pending.length ? `<div class="panel glass"><h3>Waiting to fill</h3><div class="scroll"><table><thead><tr><th>Stock</th><th>Order</th><th class="num">Qty</th><th class="num">Stop</th><th>Placed</th><th></th></tr></thead><tbody>
          ${d.pending.map((t) => tr([`<b>${esc(t.symbol)}</b>`, t.entry_type === "limit" ? "limit " + inr(t.limit_price) : "market, next open", num(t.qty, 0), inr(t.stop), esc(t.placed_on),
            `<button type="button" class="btn ghost sm" data-close="${t.id}">Cancel</button>`])).join("")}</tbody></table></div></div>` : ""}
        <div class="panel glass"><h3>Closed trades and reviews</h3>${d.closed.length ? d.closed.map((t) => `<div class="closed">
            <div class="closed-head"><b>${esc(t.symbol)}</b><span>${esc(t.entry_date)} → ${esc(t.exit_date)}</span><span>${inr(t.entry_price)} → ${inr(t.exit_price)}</span>
              <span class="${t.pnl >= 0 ? "up" : "down"}">${num(t.pnl, 0)} points</span>${rTxt(t.r)}<span class="chip c-plain">${esc(t.exit_reason)}</span></div>
            <div class="src">Why you took it: ${esc(t.thesis)}</div>
            <div class="review"><input data-review="${t.id}" value="${esc(t.review)}" placeholder="What did you learn? Did you follow your plan?" maxlength="600"><button type="button" class="btn ghost sm" data-save-review="${t.id}">Save</button></div>
          </div>`).join("") : '<p class="missing">No closed trades yet. The review is where most of the learning happens.</p>'}</div>
      </div>
      <aside class="col-side">
        <form class="panel glass glow" id="order-form"><h3>New practice trade</h3>
          <p class="hint">Long only, end-of-day fills. Decide the stop before you buy; it is required.</p>
          <div class="fields">
            <label class="wide">Stock<input name="symbol" required maxlength="80" placeholder="Type a company, e.g. HDFC Bank" data-stock-picker></label>
            <div class="wide ticket" id="ticket" hidden></div>
            <label>Quantity<input name="qty" type="number" min="1" step="1" required></label>
            <label>Order<select name="entry_type"><option value="market">Market, next open</option><option value="limit">Limit</option></select></label>
            <label class="wide limit-only" hidden>Limit price (₹)<input name="limit_price" type="number" min="0" step="0.05"></label>
            <label>Stop-loss (₹)<input name="stop" type="number" min="0" step="0.05" required></label>
            <label>Target (₹, optional)<input name="target" type="number" min="0" step="0.05"></label>
            <label>Risk per trade (%)<input id="risk-pct" type="number" min="0.1" max="10" step="0.1" value="1"></label>
            <div class="size-row"><button type="button" class="btn ghost sm" id="size-it">Size it</button></div>
            <p class="wide hint" id="order-risk"></p>
            <label class="wide">How sure are you? <output id="conf-out">60%</output><input name="confidence" type="range" min="50" max="95" value="60"></label>
            <label class="wide">Why this trade?<textarea name="thesis" rows="3" maxlength="600" required placeholder="e.g. Pullback to the 20-day average in an uptrend; stop below the last swing low."></textarea></label>
          </div>
          <div class="row"><button type="submit" class="btn">Place practice order</button></div>
          <p class="hint" id="order-msg"></p>
          <p class="src">Pick a stock to see its last close and a stop idea. "Size it" fills the quantity so the trade risks no more than your chosen share of the account.</p>
        </form>
        <div class="panel glass"><h3>How practice works</h3><p class="hint">${esc(d.note)}</p><p class="hint">${esc(st.expectancy_note)}</p></div>
      </aside>
    </div>`;
  glossify(document.querySelector("#practice-body .cards")); glossify(document.querySelector("#practice-body aside .panel:last-child"));
}
/* ---- order ticket: quote, mini chart, stop idea, sizing ---- */
async function loadTicket(symbol) {
  const box = $("ticket"); if (!box) return;
  box.hidden = false; box.innerHTML = '<p class="hint">Loading the last close…</p>'; P.quote = null;
  try {
    const q = await api("/api/practice/quote?symbol=" + encodeURIComponent(symbol));
    P.quote = q;
    box.innerHTML = `<div class="ticket-head"><b>${inr(q.last_close)}</b> ${signed(q.change_pct, 2)} <span class="src">close of ${esc(q.as_of)}, end of day</span></div>
      <div class="ticket-chart" id="ticket-chart"></div>
      <p class="src">${q.support ? `Nearest support ${inr(q.support.price)} (${q.support.touches} touch${q.support.touches === 1 ? "" : "es"}). ` : "No support level below the last close. "}
        Stop idea ${inr(q.suggested_stop)}: ${esc(q.stop_basis)}. <button type="button" class="linkish" id="use-stop">Use this stop</button></p>
      <p class="src">${esc(q.note)} Source: ${esc(q.source)}.</p>`;
    const c = candleChart($("ticket-chart"), q.candles, { locked: true });
    if (c && q.support) c.series.createPriceLine({ price: q.support.price, color: "#16c47f", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: "support" });
    $("risk-pct").value = q.default_risk_pct;
    updateRisk();
  } catch (e) { box.innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
}
function ticketEntry() {
  const f = $("order-form"); if (!f) return null;
  return f.entry_type.value === "limit" && +f.limit_price.value > 0 ? +f.limit_price.value : P.quote ? P.quote.last_close : null;
}
function updateRisk() {
  const f = $("order-form"), out = $("order-risk"); if (!f || !out) return;
  const entry = ticketEntry(), qty = +f.qty.value, stop = +f.stop.value;
  if (!entry || !qty || !stop) { out.textContent = ""; return; }
  if (stop >= entry) { out.innerHTML = `<span class="down">The stop must be below the entry (about ${inr(entry)}).</span>`; return; }
  const risk = qty * (entry - stop), share = P.pf && P.pf.equity > 0 ? (risk / P.pf.equity) * 100 : null;
  const max = P.quote ? P.quote.max_risk_pct : 2;
  out.innerHTML = `This order risks <b>${num(risk, 0)} points</b>${share == null ? "" : `, <b class="${share > max ? "down" : ""}">${share.toFixed(2)}%</b> of the account`}, and uses ${num(qty * entry, 0)} points.`
    + (share != null && share > max ? ` <span class="down">That is more than ${max}% on one trade.</span>` : "");
}
async function sizeIt() {
  const f = $("order-form"), sym = f.querySelector('input[type="hidden"][name="symbol"]');
  const msg = $("order-msg"); msg.textContent = "";
  if (!sym || !sym.value) { msg.textContent = "Pick a stock first."; return; }
  if (!+f.stop.value) { msg.textContent = "Set the stop first: the size depends on how far away it is."; return; }
  const entry = ticketEntry();
  try {
    const s = await api(`/api/practice/size?symbol=${encodeURIComponent(sym.value)}&stop=${+f.stop.value}&risk_pct=${+$("risk-pct").value || 1}${entry ? "&entry=" + entry : ""}`);
    f.qty.value = s.quantity || "";
    if (s.message) msg.textContent = s.message;
    else if (s.capped_by_points) msg.textContent = "Capped by the points you have available.";
    updateRisk();
  } catch (e) { msg.textContent = e.message; }
}
$("practice-body").addEventListener("stock-pick", (e) => { if (e.target.closest("#order-form")) loadTicket(e.detail.symbol); });
$("practice-body").addEventListener("input", (e) => {
  if (e.target.closest("#order-form") && ["qty", "stop", "limit_price", "entry_type"].includes(e.target.name)) updateRisk();
  if (e.target.name === "confidence") $("conf-out").textContent = e.target.value + "%";
  if (e.target.name === "pconf") $("pconf-out").textContent = e.target.value + "%";
  if (e.target.name === "entry_type") document.querySelector(".limit-only").hidden = e.target.value !== "limit";
});
$("practice-body").addEventListener("change", (e) => { if (e.target.name === "entry_type") document.querySelector(".limit-only").hidden = e.target.value !== "limit"; });
$("practice-body").addEventListener("click", async (e) => {
  const c = e.target.closest("button[data-close]");
  if (c) { try { status((await post(`/api/practice/trades/${c.dataset.close}/close`)).message); loadPractice(); } catch (err) { status(err.message, true); } return; }
  const r = e.target.closest("button[data-save-review]");
  if (r) { const v = document.querySelector(`input[data-review="${r.dataset.saveReview}"]`).value;
    try { await post(`/api/practice/trades/${r.dataset.saveReview}/review`, { review: v }); r.textContent = "Saved"; } catch (err) { status(err.message, true); } return; }
  const dir = e.target.closest("button[data-dir]");
  if (dir) { document.querySelectorAll("button[data-dir]").forEach((b) => b.classList.toggle("on", b === dir)); return; }
  if (e.target.closest("#use-stop") && P.quote) { $("order-form").stop.value = P.quote.suggested_stop; updateRisk(); return; }
  if (e.target.closest("#size-it")) return sizeIt();
  if (e.target.closest("#replay-start")) return replayStart();
  if (e.target.closest("#replay-long")) return replayDecide("long");
  if (e.target.closest("#replay-skip")) return replayDecide("skip");
});
$("practice-body").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target), val = (k) => (f.get(k) === "" || f.get(k) == null ? null : f.get(k));
  try {
    if (e.target.id === "order-form") {
      const r = await post("/api/practice/trades", { symbol: val("symbol"), qty: +val("qty"), stop: +val("stop"), target: val("target") ? +val("target") : null,
        entry_type: val("entry_type"), limit_price: val("limit_price") ? +val("limit_price") : null, confidence: +val("confidence") / 100, thesis: val("thesis") || "" });
      status(r.message); loadPractice();
    } else if (e.target.id === "predict-form") {
      const d = document.querySelector("button[data-dir].on");
      const r = await post("/api/practice/predictions", { symbol: val("psymbol"), direction: d ? d.dataset.dir : "up", horizon: val("horizon"),
        confidence: +val("pconf") / 100, reason: val("reason") || "" });
      status(r.message); loadPractice();
    }
  } catch (err) { const m = document.querySelector(e.target.id === "order-form" ? "#order-msg" : "#predict-msg"); if (m) m.textContent = err.message; }
});

function renderPredict() {
  const d = P.pred;
  const row = (p) => `<tr><td><b>${esc(p.symbol)}</b><div class="src">${esc(p.reason || "no reason written")}</div></td><td>${chip(p.direction === "up" ? "up" : "down", p.direction)}</td>
    <td class="num">${Math.round(p.confidence * 100)}%</td><td>${p.horizon_days} sessions from ${esc(p.ref_date)}</td><td class="num">${inr(p.ref_close)}</td>
    ${p.status === "resolved" ? `<td class="num">${inr(p.outcome_close)}</td><td>${p.correct ? chip("ok", "came true") : chip("no", "did not")}</td><td class="num">${p.brier}</td><td class="num"><b class="${p.score >= 0 ? "up" : "down"}">${p.score > 0 ? "+" : ""}${p.score}</b></td>` : ""}</tr>`;
  const cal = d.calibration.length ? `<div class="calib">${d.calibration.map((c) => `<div class="cb"><div class="bars"><i style="height:${c.stated * 100}%" title="stated"></i><i class="act" style="height:${c.actual * 100}%" title="came true"></i></div>
      <b>${esc(c.range)}</b><span>${c.count} call${c.count > 1 ? "s" : ""}</span></div>`).join("")}</div><p class="src">Grey: the confidence you stated. Yellow: how often those calls came true. Well calibrated means the bars match.</p>`
    : '<p class="missing">Calibration appears once some predictions have played out.</p>';
  $("practice-body").innerHTML = `
    <div class="cards">${stat("Forecast score", (d.score > 0 ? "+" : "") + d.score, "practice points from resolved calls", true)}
      ${stat("Brier score", d.avg_brier == null ? "n/a" : d.avg_brier, "lower is better; 0.25 is a coin flip")}
      ${stat("Came true", d.hit_rate == null ? "n/a" : pctTxt(d.hit_rate), `${d.resolved.length} resolved, ${d.open.length} open`)}
      ${stat("Badges", d.badges.length, d.badges.map((b) => b.name).join(", ") || "none yet")}</div>
    <div class="layout practice-layout">
      <div class="col-main">
        <div class="panel glass"><h3>Calibration</h3>${cal}</div>
        <div class="panel glass"><h3>Open predictions</h3>${d.open.length ? `<div class="scroll"><table><thead><tr><th>Stock</th><th>Call</th><th class="num">Confidence</th><th>Resolves after</th><th class="num">From</th></tr></thead><tbody>${d.open.map(row).join("")}</tbody></table></div>` : '<p class="missing">No open predictions.</p>'}</div>
        <div class="panel glass"><h3>Resolved</h3>${d.resolved.length ? `<div class="scroll"><table><thead><tr><th>Stock</th><th>Call</th><th class="num">Confidence</th><th>Window</th><th class="num">From</th><th class="num">To</th><th>Result</th><th class="num">Brier</th><th class="num">Points</th></tr></thead><tbody>${d.resolved.map(row).join("")}</tbody></table></div>` : '<p class="missing">Nothing has resolved yet. A 4-week call resolves after 20 sessions.</p>'}</div>
      </div>
      <aside class="col-side">
        <form class="panel glass glow" id="predict-form"><h3>Make a call</h3>
          <p class="hint">Say which way a stock will close after a set time, and how sure you are. You are scored on honesty, not boldness.</p>
          <div class="fields">
            <label class="wide">Stock<input name="psymbol" required maxlength="80" placeholder="Type a company, e.g. Jio Financial" data-stock-picker></label>
            <div class="wide seg dir"><button type="button" data-dir="up" class="on">Higher</button><button type="button" data-dir="down">Lower</button></div>
            <label class="wide">After<select name="horizon">${d.horizons.map((h) => `<option ${h === "4 weeks" ? "selected" : ""}>${esc(h)}</option>`).join("")}</select></label>
            <label class="wide">Confidence <output id="pconf-out">60%</output><input name="pconf" type="range" min="50" max="95" value="60"></label>
            <label class="wide">Your reason<textarea name="reason" rows="3" maxlength="600" placeholder="What do you see on the chart or in the business?"></textarea></label>
          </div>
          <div class="row"><button type="submit" class="btn">Log prediction</button></div><p class="hint" id="predict-msg"></p>
        </form>
        <div class="panel glass"><h3>Scoring</h3><p class="hint">${esc(d.note)}</p></div>
      </aside>
    </div>`;
  glossify(document.querySelector("#practice-body .cards")); glossify(document.querySelector("#practice-body aside .panel:last-child"));
}

function renderReplayIntro() {
  $("practice-body").innerHTML = `<div class="layout practice-layout"><div class="col-main"><div class="panel chart-panel"><div id="replay-chart" class="chart replay-empty">
      <div><h2>Chart replay</h2><p class="hint">Belfort picks a real past chart at random and hides the company and the future. Plan a trade on what you can see: buy with a stop and target, or skip. Then watch the next 60 sessions play out. Many repetitions in an hour, instead of one result a month.</p>
      <button type="button" class="btn" id="replay-start">Start a chart</button></div></div></div></div>
    <aside class="col-side"><div class="panel glass" id="replay-side"><h3>Your replay record</h3><p class="hint">Loading…</p></div></aside></div>`;
  api("/api/practice/replay/stats").then(replayStats).catch(() => {});
}
function replayStats(s) {
  const el = $("replay-side"); if (!el) return;
  el.innerHTML = `<h3>Your replay record</h3><div class="kv"><div><div class="k">Charts</div><div class="v">${s.count}</div></div><div><div class="k">Trades taken</div><div class="v">${s.taken}</div></div>
    <div class="big"><div class="k">Average R on trades taken</div><div class="v">${s.avg_r == null ? "n/a" : (s.avg_r >= 0 ? "+" : "") + s.avg_r}</div><div class="n">A positive average over many charts means your plans made more than they lost.</div></div></div>`;
  glossify(el);
}
async function replayStart() {
  try {
    const d = await api("/api/practice/replay/new");
    P.replay = d;
    const seen = d.candles, last = seen[seen.length - 1].close;  // only the visible bars ever reach the page
    const lows = seen.slice(-20).map((c) => c.low), lo = Math.min(...lows);
    document.querySelector("#practice-body .col-main").innerHTML = `<div class="panel chart-panel"><div class="chart-head"><div><b>Mystery stock</b> <span class="hint">· ${d.visible} sessions shown · last close ${inr(last)}</span></div></div><div id="replay-chart" class="chart"></div></div>
      <div class="panel glass"><p class="hint">${esc(d.note)}</p></div>`;
    $("replay-side").innerHTML = `<h3>Your plan</h3><p class="hint">Entry is the last close shown, ${inr(last)}. Put the stop where the idea is wrong.</p>
      <div class="fields"><label>Stop (₹)<input id="rp-stop" type="number" step="0.05" value="${(lo * 0.995).toFixed(2)}"></label><label>Target (₹)<input id="rp-target" type="number" step="0.05" value="${(last + 2 * (last - lo * 0.995)).toFixed(2)}"></label></div>
      <div class="row"><button type="button" class="btn" id="replay-long">Buy with this plan</button><button type="button" class="btn ghost" id="replay-skip">Skip</button></div>
      <p class="src">The default stop sits just under the lowest low of the last 20 sessions, and the target at twice the risk. Change both.</p>`;
    const c = candleChart($("replay-chart"), seen, { hideTime: true });
    P.replay.view = c;
  } catch (e) { status(e.message, true); }
}
async function replayDecide(decision) {
  const d = P.replay; if (!d) return;
  const stop = +$("rp-stop").value, target = +$("rp-target").value;
  let res;
  try { res = await post("/api/practice/replay/score", { id: d.id, decision, stop, target }); }
  catch (e) { status(e.message, true); return; }
  document.querySelectorAll("#replay-long,#replay-skip").forEach((b) => { b.disabled = true; });
  const v = d.view;
  if (v && decision === "long") {
    v.series.createPriceLine({ price: stop, color: "#8b8b90", lineWidth: 1, lineStyle: 0, axisLabelVisible: true, title: "stop" });
    if (target) v.series.createPriceLine({ price: target, color: "#facc15", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: "target" });
  }
  const hidden = res.hidden || [];
  let i = 0;
  const timer = setInterval(() => {
    if (!v || i >= hidden.length) {
      clearInterval(timer);
      if (v) { v.chart.applyOptions({ timeScale: { visible: true } }); v.chart.timeScale().fitContent(); }
      const cls = res.outcome === "target" ? "good" : res.outcome === "stop" ? "bad" : "plain";
      replayStats(res.stats);
      $("replay-side").insertAdjacentHTML("beforeend", `<div class="note ${cls}"><b>${esc(res.outcome === "skipped" ? "Skipped" : res.r == null ? "Result" : (res.r >= 0 ? "+" : "") + res.r + "R")}</b>${esc(res.text)}</div>
        <p class="hint">The chart was <b>${esc(res.symbol)}</b>, ${esc(res.start_date)} to ${esc(res.end_date)}.</p>
        <div class="row"><button type="button" class="btn" id="replay-start">Next chart</button></div>`);
      glossify($("replay-side"));
      return;
    }
    v.series.update({ ...hidden[i] }); i += 1;
  }, 45);
}

/* ======================= NEWS ======================= */
const N = { data: null, cat: "All", tips: false };
onView.news = (opts) => loadNews(opts.refresh);
async function loadNews(refresh) {
  $("news-body").innerHTML = '<p class="hint">Gathering headlines…</p>';
  try { N.data = await api("/api/news" + (refresh ? "?refresh=true" : "")); renderNews(); }
  catch (e) { $("news-body").innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
}
function storyCard(s, big) {
  const img = s.image ? `<div class="ni"><img src="${esc(safeUrl(s.image))}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentNode.remove()"></div>` : "";
  return `<article class="story ${big ? "lead" : ""} ${s.image ? "" : "noimg"}" data-id="${esc(s.id)}">${img}
    <div class="sb"><div class="meta"><span class="chip c-plain">${esc(s.category)}</span>${s.tip ? '<span class="chip c-medium">publisher\'s stock call</span>' : ""}<span>${esc(s.source)}</span><span>${esc(ago(s.published))}</span></div>
      <h3 class="st"><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a></h3>
      ${s.summary ? `<p class="ss">${esc(s.summary)}</p>` : ""}
      <div class="sf">${(s.symbols || []).map((x) => `<button type="button" class="tkr" data-sym="${esc(x)}">${esc(x)}</button>`).join("")}
        <span class="sp"></span><button type="button" class="linkish" data-explain="${esc(s.id)}">Explain this</button>
        <a class="linkish" href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">Read at source ↗</a></div></div></article>`;
}
function renderNews() {
  const d = N.data, cats = ["All"].concat(d.categories.filter((c) => d.stories.some((s) => s.category === c)));
  if (!cats.includes(N.cat)) N.cat = "All";
  $("news-cats").innerHTML = cats.map((c) => `<button type="button" data-cat="${esc(c)}" class="${c === N.cat ? "on" : ""}">${esc(c)}</button>`).join("");
  const inCat = d.stories.filter((s) => N.cat === "All" || s.category === N.cat);
  const hiddenTips = inCat.filter((s) => s.tip).length;
  const xs = inCat.filter((s) => N.tips || !s.tip);
  const official = xs.filter((s) => s.kind === "official"), pub = xs.filter((s) => s.kind !== "official");
  if (!xs.length) { $("news-body").innerHTML = '<p class="missing">No stories in this section right now. The feeds may be unreachable; try Refresh.</p>'; }
  else {
    const lead = pub.find((s) => s.image) || pub[0];
    const rest = pub.filter((s) => s !== lead);
    $("news-body").innerHTML = `<div class="news-grid">
      <div class="news-main">${lead ? storyCard(lead, true) : ""}<div class="stories">${rest.slice(0, 40).map((s) => storyCard(s)).join("")}</div></div>
      <aside class="news-side"><div class="panel glass"><h3>From the regulator and the RBI</h3>${official.length ? official.slice(0, 12).map((s) => `<div class="brief">
          <span class="hint">${esc(s.source)} · ${esc(ago(s.published))}</span><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a>
          <button type="button" class="linkish" data-explain="${esc(s.id)}">Explain this</button></div>`).join("") : '<p class="missing">No official releases in this section.</p>'}</div>
        ${hiddenTips ? `<div class="panel glass"><h3>Stock tips hidden</h3><p class="hint">${hiddenTips} headline${hiddenTips > 1 ? "s" : ""} in this section pass on a buy or sell call or a price target from a publisher or brokerage. Belfort hides them by default: they are someone else's opinion, not news, and not Belfort's view.</p>
          <div class="row"><button type="button" class="btn ghost sm" id="tips-toggle">${N.tips ? "Hide them again" : "Show them, labelled"}</button></div></div>` : ""}
        <div class="panel glass"><h3>Reading the news well</h3><ul class="plain"><li>A headline is one fact, not a forecast. Ask what changed and for whom.</li>
          <li>Big moves on news often reverse. Your stop matters more than the story.</li><li>Check the date: old news is already in the price.</li></ul></div></aside></div>`;
    glossify($("news-body"));
  }
  const bad = d.sources.filter((s) => s.error);
  $("news-src").textContent = `${d.note} Sources: ${d.sources.map((s) => `${s.name} (${s.count})`).join(", ")}.${bad.length ? " Not reachable now: " + bad.map((s) => s.name).join(", ") + "." : ""} Updated ${ago(d.generated)}.`;
}
$("news-cats").addEventListener("click", (e) => { const b = e.target.closest("button[data-cat]"); if (b) { N.cat = b.dataset.cat; renderNews(); } });
$("news-refresh").addEventListener("click", () => loadNews(true));
$("news-body").addEventListener("click", (e) => {
  if (e.target.closest("#tips-toggle")) { N.tips = !N.tips; return renderNews(); }
  const t = e.target.closest("button[data-sym]"); if (t) return load(t.dataset.sym);
  const x = e.target.closest("button[data-explain]");
  if (x) {
    const s = N.data.stories.find((y) => y.id === x.dataset.explain); if (!s) return;
    S.chatCtx = { view: "news", mode: "news", text: `Source: ${s.source}, ${s.published || ""}\nHeadline: ${s.title}\nDescription: ${s.summary || "(none)"}` };
    $("chat-log").innerHTML = ""; S.chat = [];
    openChat("Explain this story in plain words for a beginner, and define the key terms.");
  }
});

/* ======================= SETTINGS ======================= */
function fillSettings() {
  const a = aiSettings();
  $("ai-provider").value = a.provider || "gemini"; $("ai-key").value = a.key || ""; $("ai-model").value = a.model || ""; $("ai-base").value = a.base || "";
  $("ai-base-wrap").hidden = $("ai-provider").value !== "openai";
  $("about").textContent = `Belfort ${S.cfg ? S.cfg.version : ""}. Private pre-release build. ${S.cfg ? S.cfg.disclaimer : ""}`;
}
$("settings-btn").addEventListener("click", () => { fillSettings(); $("settings").hidden = false; $("side").classList.remove("open"); });
$("settings-x").addEventListener("click", () => { $("settings").hidden = true; });
$("ai-provider").addEventListener("change", () => { $("ai-base-wrap").hidden = $("ai-provider").value !== "openai"; });
$("ai-save").addEventListener("click", () => {
  const a = { provider: $("ai-provider").value, key: $("ai-key").value.trim(), model: $("ai-model").value.trim(), base: $("ai-base").value.trim() };
  localStorage.setItem("belfortAI", JSON.stringify(a)); $("ai-msg").textContent = "Saved in this browser.";
  $("chat-log").innerHTML = "";
});
$("ai-clear").addEventListener("click", () => { localStorage.removeItem("belfortAI"); fillSettings(); $("ai-msg").textContent = "Key removed."; $("chat-log").innerHTML = ""; });
$("paper-reset").addEventListener("click", async () => {
  if (!confirm("Delete all practice trades and start again with fresh points?")) return;
  try { status((await post("/api/practice/reset")).message); if (S.view === "practice") loadPractice(); } catch (e) { status(e.message, true); }
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("settings").hidden = true; });
