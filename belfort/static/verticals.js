"use strict";
/* Learn, Practice, News and Settings. Uses the helpers defined in app.js ($, esc, api, inr, num, glossify, go, ...). */

const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? u : "#");
const ago = (iso) => {
  if (!iso) return "";
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (m < 1) return T("time.just_now");
  if (m < 60) return T("time.min_ago", { n: m });
  if (m < 1440) return T("time.h_ago", { n: Math.round(m / 60) });
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
};
const pctTxt = (x, d = 0) => (x == null ? T("common.na") : (x * 100).toFixed(d) + "%");
const stat = (k, v, n, on) => `<div class="card-list stat-card ${on ? "on" : ""}"><span class="eyebrow">${esc(k)}</span><span class="n">${v}</span>${n ? `<span class="s">${esc(n)}</span>` : ""}</div>`;
const post = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });

function candleChart(el, candles, opts) {
  if (!window.LightweightCharts) { el.innerHTML = `<p class="missing">${T("chart.lib_missing_short")}</p>`; return null; }
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
/* The path, lessons and exercises live in learn-game.js (T42). This file keeps the lesson chart and the "Try it" buttons. */
$("lesson").addEventListener("click", (e) => {
  const t = e.target.closest("button[data-try]");
  if (t) { const k = t.dataset.try; if (k === "research") { go("home"); $("q").focus(); } else { P.tab = k === "predict" ? "predict" : k === "replay" ? "replay" : "paper"; go("practice"); } }
});

async function drawLessonChart(el) {
  el.innerHTML = `<p class="hint">${T("learn.loading_chart")}</p>`;
  try {
    const d = await api(`/api/learn/example?symbol=${encodeURIComponent(el.dataset.symbol)}&bars=${el.dataset.bars}`);
    el.innerHTML = `<div class="lc"></div><div class="src">${T("learn.chart_caption", { symbol: esc(d.symbol), ends: esc(d.ends) })} ${esc(d.note)}</div>`;
    candleChart(el.querySelector(".lc"), d.candles);
  } catch (e) { el.innerHTML = `<p class="missing">${T("learn.chart_failed", { why: esc(e.message) })}</p>`; }
}

/* ======================= PRACTICE ======================= */
const P = { tab: "paper", pf: null, pred: null, replay: null };

onView.practice = () => { renderPracticeTabs(); loadPractice(); };
function renderPracticeTabs() { document.querySelectorAll("#practice-tabs button").forEach((b) => b.classList.toggle("on", b.dataset.p === P.tab)); }
$("practice-tabs").addEventListener("click", (e) => { const b = e.target.closest("button[data-p]"); if (b) { P.tab = b.dataset.p; status(""); renderPracticeTabs(); loadPractice(); } });

async function loadPractice() {
  const body = $("practice-body");
  body.innerHTML = `<p class="hint">${T("common.loading")}</p>`;
  try {
    if (P.tab === "paper") {
      P.pf = await api("/api/practice/portfolio"); P.an = await api("/api/practice/analytics"); P.eq = await api("/api/practice/equity");
      renderPaper(); drawEquity();
    }
    else if (P.tab === "predict") { P.pred = await api("/api/practice/predictions"); renderPredict(); }
    else renderReplayIntro();
  } catch (e) { body.innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
}

function renderPaper() {
  const d = P.pf, st = d.stats;
  const tr = (cells) => `<tr>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`;
  const rTxt = (r) => (r == null ? T("common.na") : `<span class="${r >= 0 ? "up" : "down"}">${r >= 0 ? "+" : ""}${r}R</span>`);
  $("practice-body").innerHTML = `
    <div class="cards">${stat(T("pr.account_value"), num(d.equity, 0), T("pr.since_start", { pct: (d.return_pct >= 0 ? "+" : "") + d.return_pct }), true)}
      ${stat(T("pr.available"), num(d.available, 0), d.reserved ? T("pr.held", { n: num(d.reserved, 0) }) : T("pr.ready"))}
      ${stat(T("pr.win_rate"), st.win_rate == null ? T("common.na") : pctTxt(st.win_rate), T("pr.closed_trades", { n: st.closed }))}
      ${stat(T("pr.avg_r"), st.avg_r == null ? T("common.na") : (st.avg_r >= 0 ? "+" : "") + st.avg_r, T("pr.avg_r_sub"))}
      ${stat(T("pr.open_risk"), d.risk.total_pct == null ? T("common.na") : `<span class="${d.risk.over_limit ? "down" : ""}">${d.risk.total_pct}%</span>`, T("pr.open_risk_sub", { points: num(d.risk.total_points, 0), limit: d.risk.limit_pct }))}</div>
    <div class="layout practice-layout">
      <div class="col-main">
        <div class="panel glass"><h3>${T("pr.open_positions")}</h3>${d.open.length ? `<div class="scroll"><table><thead><tr><th>${T("pr.col_stock")}</th><th class="num">${T("pr.col_qty")}</th><th class="num">${T("pr.col_entry")}</th><th class="num">${T("pr.col_last")}</th><th class="num">${T("pr.col_stop")}</th><th class="num">${T("pr.col_target")}</th><th class="num">${T("pr.col_pnl")}</th><th class="num">${T("pr.col_now")}</th><th></th></tr></thead><tbody>
          ${d.open.map((t) => tr([`<b>${esc(t.symbol)}</b><div class="src">${esc(t.thesis)}</div>`, num(t.qty, 0), inr(t.entry_price), inr(t.last), stopCell(t), t.target ? inr(t.target) : T("common.na"),
            `<span class="${t.pnl >= 0 ? "up" : "down"}">${num(t.pnl, 0)}</span>`, rTxt(t.open_r),
            t.close_requested_on ? `<span class="hint">${T("pr.exit_next_open")}</span>` : `<div class="row-actions"><button type="button" class="btn ghost sm" data-manage="${t.id}">${T("pr.manage")}</button><button type="button" class="btn ghost sm" data-close="${t.id}">${T("pr.exit")}</button></div>`])
            + (t.close_requested_on ? "" : manageRow(t))).join("")}</tbody></table></div>`
          : `<p class="missing">${T("pr.no_open")}</p>`}</div>
        ${d.pending.length ? `<div class="panel glass"><h3>${T("pr.waiting")}</h3><div class="scroll"><table><thead><tr><th>${T("pr.col_stock")}</th><th>${T("pr.col_order")}</th><th class="num">${T("pr.col_qty")}</th><th class="num">${T("pr.col_stop")}</th><th>${T("pr.col_placed")}</th><th></th></tr></thead><tbody>
          ${d.pending.map((t) => tr([`<b>${esc(t.symbol)}</b>`, t.entry_type === "limit" ? T("pr.limit_at", { price: inr(t.limit_price) }) : T("pr.market_next"), num(t.qty, 0), inr(t.stop), esc(t.placed_on),
            `<button type="button" class="btn ghost sm" data-close="${t.id}">${T("common.cancel")}</button>`])).join("")}</tbody></table></div></div>` : ""}
        ${equityPanel()}
        ${journalPanel()}
        <div class="panel glass"><h3>${T("pr.closed_title")}</h3>${d.closed.length ? d.closed.map((t) => `<div class="closed">
            <div class="closed-head"><b>${esc(t.symbol)}</b><span>${esc(t.entry_date)} → ${esc(t.exit_date)}</span><span>${inr(t.entry_price)} → ${inr(t.exit_price)}</span>
              <span class="${t.pnl >= 0 ? "up" : "down"}">${T("pr.points", { n: num(t.pnl, 0) })}</span>${rTxt(t.r)}<span class="chip c-plain">${esc(t.exit_reason)}</span></div>
            <div class="src">${T("pr.why_took", { thesis: esc(t.thesis) })}</div>
            <div class="review"><input data-review="${t.id}" value="${esc(t.review)}" placeholder="${T("pr.review_ph")}" maxlength="600"><button type="button" class="btn ghost sm" data-save-review="${t.id}">${T("common.save")}</button></div>
            ${tagEditor(t)}
          </div>`).join("") : `<p class="missing">${T("pr.no_closed")}</p>`}</div>
      </div>
      <aside class="col-side">
        <form class="panel glass glow" id="order-form"><h3>${T("pr.new_trade")}</h3>
          <p class="hint">${T("pr.new_hint")}</p>
          <div class="fields">
            <label class="wide">${T("pr.stock")}<input name="symbol" required maxlength="80" placeholder="${T("pr.stock_ph")}" data-stock-picker></label>
            <div class="wide ticket" id="ticket" hidden></div>
            <label>${T("pr.qty")}<input name="qty" type="number" min="1" step="1" required></label>
            <label>${T("pr.setup")}<select name="setup"><option value="">${T("pr.not_tagged")}</option>${Object.entries(P.an ? P.an.setups : {}).map(([k, v]) => `<option value="${esc(k)}">${esc(v)}</option>`).join("")}</select></label>
            <label>${T("pr.order")}<select name="entry_type"><option value="market">${T("pr.order_market")}</option><option value="limit">${T("pr.order_limit")}</option></select></label>
            <label class="wide limit-only" hidden>${T("pr.limit_price")}<input name="limit_price" type="number" min="0" step="0.05"></label>
            <label>${T("pr.stop_loss")}<input name="stop" type="number" min="0" step="0.05" required></label>
            <label>${T("pr.target_opt")}<input name="target" type="number" min="0" step="0.05"></label>
            <label>${T("pr.risk_pct")}<input id="risk-pct" type="number" min="0.1" max="10" step="0.1" value="1"></label>
            <div class="size-row"><button type="button" class="btn ghost sm" id="size-it">${T("pr.size_it")}</button></div>
            <p class="wide hint" id="order-risk"></p>
            <label class="wide">${T("pr.how_sure")} <output id="conf-out">60%</output><input name="confidence" type="range" min="50" max="95" value="60"></label>
            <label class="wide">${T("pr.why_trade")}<textarea name="thesis" rows="3" maxlength="600" required placeholder="${T("pr.thesis_ph")}"></textarea></label>
          </div>
          <div class="row"><button type="submit" class="btn">${T("pr.place")}</button></div>
          <p class="hint" id="order-msg"></p>
          <p class="src">${T("pr.order_src")}</p>
        </form>
        <div class="panel glass"><h3>${T("pr.how_works")}</h3><p class="hint">${esc(d.note)}</p><p class="hint">${esc(st.expectancy_note)}</p></div>
      </aside>
    </div>`;
  glossify(document.querySelector("#practice-body .cards")); glossify(document.querySelector("#practice-body aside .panel:last-child"));
}
/* ---- order ticket: quote, mini chart, stop idea, sizing ---- */
async function loadTicket(symbol) {
  const box = $("ticket"); if (!box) return;
  box.hidden = false; box.innerHTML = `<p class="hint">${T("pr.loading_close")}</p>`; P.quote = null;
  try {
    const q = await api("/api/practice/quote?symbol=" + encodeURIComponent(symbol));
    P.quote = q;
    box.innerHTML = `<div class="ticket-head"><b>${inr(q.last_close)}</b> ${signed(q.change_pct, 2)} <span class="src">${T("pr.close_of", { date: esc(q.as_of) })}</span></div>
      <div class="ticket-chart" id="ticket-chart"></div>
      <p class="src">${q.support ? T("pr.support_near", { price: inr(q.support.price), n: q.support.touches }) : T("pr.no_support")}
        ${T("pr.stop_idea", { price: inr(q.suggested_stop), basis: esc(q.stop_basis) })} <button type="button" class="linkish" id="use-stop">${T("pr.use_stop")}</button></p>
      <p class="src">${esc(q.note)} ${T("common.source", { source: esc(q.source) })}.</p>`;
    const c = candleChart($("ticket-chart"), q.candles, { locked: true });
    if (c && q.support) c.series.createPriceLine({ price: q.support.price, color: "#16c47f", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: T("chart.support") });
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
  if (stop >= entry) { out.innerHTML = `<span class="down">${T("pr.stop_below", { entry: inr(entry) })}</span>`; return; }
  const risk = qty * (entry - stop), equity = P.pf ? P.pf.equity : 0, share = equity > 0 ? (risk / equity) * 100 : null;
  const max = P.pf ? P.pf.risk.trade_limit_pct : 2, limit = P.pf ? P.pf.risk.limit_pct : 6;
  const after = equity > 0 && P.pf ? ((P.pf.risk.total_points + risk) / equity) * 100 : null;
  out.innerHTML = T("pr.risks_points", { risk: num(risk, 0), used: num(qty * entry, 0), share: share == null ? "" : T("pr.of_account", { cls: share > max ? "down" : "", pct: share.toFixed(2) }) })
    + (after == null ? "" : T("pr.open_after", { cls: after > limit ? "down" : "", pct: after.toFixed(2), limit }))
    + (share != null && share > max ? T("pr.over_trade", { max }) : "")
    + (after != null && after > limit ? T("pr.over_total", { limit }) : "");
}
async function sizeIt() {
  const f = $("order-form"), sym = f.querySelector('input[type="hidden"][name="symbol"]');
  const msg = $("order-msg"); msg.textContent = "";
  if (!sym || !sym.value) { msg.textContent = T("pr.pick_stock"); return; }
  if (!+f.stop.value) { msg.textContent = T("pr.set_stop"); return; }
  const entry = ticketEntry();
  try {
    const s = await api(`/api/practice/size?symbol=${encodeURIComponent(sym.value)}&stop=${+f.stop.value}&risk_pct=${+$("risk-pct").value || 1}${entry ? "&entry=" + entry : ""}`);
    f.qty.value = s.quantity || "";
    if (s.message) msg.textContent = s.message;
    else if (s.capped_by_points) msg.textContent = T("pr.capped");
    updateRisk();
  } catch (e) { msg.textContent = e.message; }
}
$("practice-body").addEventListener("stock-pick", (e) => { if (e.target.closest("#order-form")) loadTicket(e.detail.symbol); });
/* ---- journal analytics: tags on closed trades, R distribution, results by setup and holding time, habits ---- */
function tagEditor(t) {
  if (!P.an) return "";
  const setups = Object.entries(P.an.setups).map(([k, v]) => `<option value="${esc(k)}" ${t.setup === k ? "selected" : ""}>${esc(v)}</option>`).join("");
  const boxes = Object.entries(P.an.mistakes).map(([k, v]) => `<label class="tag"><input type="checkbox" data-mistake="${esc(k)}" ${(t.mistakes || []).includes(k) ? "checked" : ""}>${esc(v)}</label>`).join("");
  return `<div class="tags" data-tags="${t.id}"><select data-setup><option value="">${T("pr.setup_not_tagged")}</option>${setups}</select>${boxes}<button type="button" class="btn ghost sm" data-save-tags="${t.id}">${T("pr.save_tags")}</button></div>`;
}
function equityPanel() {
  const e = P.eq;
  if (!e) return "";
  const dd = e.drawdown;
  const ddText = dd.points > 0 ? T("pr.drawdown", { points: num(dd.points, 0), pct: dd.pct, from: dd.peak_day === "start" ? T("pr.the_start") : esc(dd.peak_day), to: esc(dd.trough_day) }) : T("pr.no_drawdown");
  return `<div class="panel glass"><h3>${T("pr.equity_title")}</h3>
    ${e.points.length >= 2 ? '<div class="equity-chart" id="equity-chart"></div>' : `<p class="hint">${T("pr.equity_wait")}</p>`}
    <p class="hint">${ddText}</p><p class="src">${esc(e.note)}</p></div>`;
}
function drawEquity() {
  const el = $("equity-chart");
  if (!el || !window.LightweightCharts) return;
  const c = LightweightCharts.createChart(el, { autoSize: true, layout: { background: { color: "transparent" }, textColor: "#8b8b90", fontFamily: "Inter, sans-serif" },
    grid: { vertLines: { color: "rgba(255,255,255,.04)" }, horzLines: { color: "rgba(255,255,255,.05)" } }, rightPriceScale: { borderColor: "rgba(255,255,255,.08)" },
    timeScale: { borderColor: "rgba(255,255,255,.08)" }, handleScroll: false, handleScale: false });
  const s = c.addLineSeries({ color: "#facc15", lineWidth: 2, priceFormat: { type: "price", precision: 0, minMove: 1 } });
  s.setData(P.eq.points.map((p) => ({ time: p.day, value: p.equity })));
  s.createPriceLine({ price: P.eq.start_points, color: "#8b8b90", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: T("chart.start") });
  c.timeScale().fitContent();
}
function journalPanel() {
  const a = P.an;
  if (!a || !a.closed) return "";
  const max = Math.max(1, ...a.r_distribution.map((b) => b.count));
  const bars = a.r_distribution.map((b) => `<div class="rbar"><span class="rl">${esc(b.label)}</span><span class="rt"><i class="${b.high != null && b.high <= 0 ? "neg" : "pos"}" style="width:${(b.count / max) * 100}%"></i></span><span class="rc">${b.count}</span></div>`).join("");
  const row = (g, name) => `<tr><td>${esc(name)}</td><td class="num">${g.count}</td><td class="num">${g.win_rate == null ? T("common.na") : pctTxt(g.win_rate)}</td><td class="num">${g.avg_r == null ? T("common.na") : (g.avg_r >= 0 ? "+" : "") + g.avg_r + "R"}</td></tr>`;
  const table = (title, rows) => `<div><h4>${esc(title)}</h4><table><thead><tr><th></th><th class="num">${T("pr.trades")}</th><th class="num">${T("pr.win_rate")}</th><th class="num">${T("pr.average_r")}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  const list = (items, empty) => (items.length ? `<ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : `<p class="hint">${esc(empty)}</p>`);
  return `<div class="panel glass journal"><h3>${T("pr.journal")}</h3>
    <div class="habits"><div><h4>${T("pr.worked")}</h4>${list(a.habits.best, T("pr.min_group", { n: a.habits.min_group }))}</div>
      <div><h4>${T("pr.cost")}</h4>${list(a.habits.worst, T("pr.no_mistake"))}</div></div>
    <h4>${T("pr.results_r")}</h4><div class="rdist">${bars}</div>
    <div class="jtables">${table(T("pr.by_setup"), a.by_setup.map((g) => row(g, g.label)).join(""))}
      ${table(T("pr.by_holding"), a.by_holding.filter((g) => g.count).map((g) => row(g, g.label)).join(""))}
      ${table(T("pr.by_mistake"), a.by_mistake.filter((g) => g.count).map((g) => row(g, g.label)).join(""))}</div>
    <p class="src">${esc(a.note)}</p></div>`;
}

/* ---- managing an open position: raise the stop, trail it, sell part ---- */
function stopCell(t) {
  const raised = t.current_stop > t.stop;
  const trail = t.trail_kind ? `<div class="src">${T(t.trail_kind === "pct" ? "pr.trailing_pct" : "pr.trailing_atr", { v: t.trail_value })}</div>` : "";
  return `${inr(t.current_stop)}${raised ? `<div class="src">${T("pr.raised_from", { price: inr(t.stop) })}</div>` : ""}${trail}`;
}
function manageRow(t) {
  return `<tr class="manage-row" id="manage-${t.id}" hidden><td colspan="9"><div class="manage">
    <label>${T("pr.raise_to")}<span class="inline"><input type="number" step="0.05" min="${t.current_stop}" data-raise-input="${t.id}" placeholder="${T("pr.above", { price: num(t.current_stop) })}"><button type="button" class="btn ghost sm" data-raise="${t.id}">${T("pr.raise")}</button></span></label>
    <label>${T("pr.trailing_stop")}<span class="inline"><select data-trail-kind="${t.id}"><option value="pct" ${t.trail_kind === "pct" ? "selected" : ""}>${T("pr.pct_below")}</option><option value="atr" ${t.trail_kind === "atr" ? "selected" : ""}>${T("pr.atr_below")}</option></select>
      <input type="number" step="0.1" min="0.5" data-trail-value="${t.id}" value="${t.trail_value || ""}" placeholder="${T("pr.trail_ph")}"><button type="button" class="btn ghost sm" data-trail="${t.id}">${T("pr.set")}</button>
      ${t.trail_kind ? `<button type="button" class="btn ghost sm" data-trail-off="${t.id}">${T("pr.off")}</button>` : ""}</span></label>
    <label>${T("pr.sell_part")}<span class="inline"><input type="number" step="1" min="1" max="${t.qty - 1}" data-sell-input="${t.id}" placeholder="${T("pr.range_ph", { n: t.qty - 1 })}"><button type="button" class="btn ghost sm" data-sell="${t.id}">${T("pr.sell_next")}</button></span></label>
    <p class="hint">${T("pr.manage_hint", { price: inr(t.stop) })}</p>
  </div></td></tr>`;
}
async function manage(path, body) {
  try { status((await post(path, body)).message); loadPractice(); } catch (err) { status(err.message, true); }
}

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
    try { await post(`/api/practice/trades/${r.dataset.saveReview}/review`, { review: v }); r.textContent = T("common.saved"); } catch (err) { status(err.message, true); } return; }
  const dir = e.target.closest("button[data-dir]");
  if (dir) { document.querySelectorAll("button[data-dir]").forEach((b) => b.classList.toggle("on", b === dir)); return; }
  const st = e.target.closest("button[data-save-tags]");
  if (st) {
    const box = document.querySelector(`[data-tags="${st.dataset.saveTags}"]`);
    const mistakes = [...box.querySelectorAll("input[data-mistake]:checked")].map((x) => x.dataset.mistake);
    return manage(`/api/practice/trades/${st.dataset.saveTags}/tags`, { setup: box.querySelector("[data-setup]").value || null, mistakes });
  }
  const m = e.target.closest("button[data-manage]");
  if (m) { const row = $("manage-" + m.dataset.manage); row.hidden = !row.hidden; return; }
  const mb = e.target.closest("button[data-raise],button[data-trail],button[data-trail-off],button[data-sell]");
  if (mb) {
    const d = mb.dataset, q = (sel) => document.querySelector(sel);
    if (d.raise) return manage(`/api/practice/trades/${d.raise}/stop`, { stop: +q(`[data-raise-input="${d.raise}"]`).value });
    if (d.trail) return manage(`/api/practice/trades/${d.trail}/trail`, { kind: q(`[data-trail-kind="${d.trail}"]`).value, value: +q(`[data-trail-value="${d.trail}"]`).value });
    if (d.trailOff) return manage(`/api/practice/trades/${d.trailOff}/trail`, { kind: "off" });
    if (d.sell) return manage(`/api/practice/trades/${d.sell}/sell`, { qty: +q(`[data-sell-input="${d.sell}"]`).value });
  }
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
        setup: val("setup"), entry_type: val("entry_type"), limit_price: val("limit_price") ? +val("limit_price") : null, confidence: +val("confidence") / 100, thesis: val("thesis") || "" });
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
  const row = (p) => `<tr><td><b>${esc(p.symbol)}</b><div class="src">${esc(p.reason || T("pr.no_reason"))}</div></td><td>${chip(p.direction === "up" ? "up" : "down", T("trend." + p.direction, null, p.direction))}</td>
    <td class="num">${Math.round(p.confidence * 100)}%</td><td>${T("pr.sessions_from", { n: p.horizon_days, date: esc(p.ref_date) })}</td><td class="num">${inr(p.ref_close)}</td>
    ${p.status === "resolved" ? `<td class="num">${inr(p.outcome_close)}</td><td>${p.correct ? chip("ok", T("pr.came_true")) : chip("no", T("pr.did_not"))}</td><td class="num">${p.brier}</td><td class="num"><b class="${p.score >= 0 ? "up" : "down"}">${p.score > 0 ? "+" : ""}${p.score}</b></td>` : ""}</tr>`;
  const cal = d.calibration.length ? `<div class="calib">${d.calibration.map((c) => `<div class="cb"><div class="bars"><i style="height:${c.stated * 100}%" title="${T("pr.stated")}"></i><i class="act" style="height:${c.actual * 100}%" title="${T("pr.came_true")}"></i></div>
      <b>${esc(c.range)}</b><span>${T("pr.calls", { n: c.count })}</span></div>`).join("")}</div><p class="src">${T("pr.calib_note")}</p>`
    : `<p class="missing">${T("pr.calib_wait")}</p>`;
  $("practice-body").innerHTML = `
    <div class="cards">${stat(T("pr.forecast_score"), (d.score > 0 ? "+" : "") + d.score, T("pr.forecast_sub"), true)}
      ${stat(T("pr.brier"), d.avg_brier == null ? T("common.na") : d.avg_brier, T("pr.brier_sub"))}
      ${stat(T("pr.came_true_card"), d.hit_rate == null ? T("common.na") : pctTxt(d.hit_rate), T("pr.resolved_open", { resolved: d.resolved.length, open: d.open.length }))}
      ${stat(T("pr.badges"), d.badges.length, d.badges.map((b) => b.name).join(", ") || T("pr.none_yet"))}</div>
    <div class="layout practice-layout">
      <div class="col-main">
        <div class="panel glass"><h3>${T("pr.calibration")}</h3>${cal}</div>
        <div class="panel glass"><h3>${T("pr.open_preds")}</h3>${d.open.length ? `<div class="scroll"><table><thead><tr><th>${T("pr.col_stock")}</th><th>${T("pr.col_call")}</th><th class="num">${T("pr.col_conf")}</th><th>${T("pr.col_resolves")}</th><th class="num">${T("pr.col_from")}</th></tr></thead><tbody>${d.open.map(row).join("")}</tbody></table></div>` : `<p class="missing">${T("pr.no_open_preds")}</p>`}</div>
        <div class="panel glass"><h3>${T("pr.resolved")}</h3>${d.resolved.length ? `<div class="scroll"><table><thead><tr><th>${T("pr.col_stock")}</th><th>${T("pr.col_call")}</th><th class="num">${T("pr.col_conf")}</th><th>${T("pr.col_window")}</th><th class="num">${T("pr.col_from")}</th><th class="num">${T("pr.col_to")}</th><th>${T("pr.col_result")}</th><th class="num">${T("pr.col_brier")}</th><th class="num">${T("pr.col_points")}</th></tr></thead><tbody>${d.resolved.map(row).join("")}</tbody></table></div>` : `<p class="missing">${T("pr.none_resolved")}</p>`}</div>
      </div>
      <aside class="col-side">
        <form class="panel glass glow" id="predict-form"><h3>${T("pr.make_call")}</h3>
          <p class="hint">${T("pr.call_hint")}</p>
          <div class="fields">
            <label class="wide">${T("pr.stock")}<input name="psymbol" required maxlength="80" placeholder="${T("pr.call_stock_ph")}" data-stock-picker></label>
            <div class="wide seg dir"><button type="button" data-dir="up" class="on">${T("pr.higher")}</button><button type="button" data-dir="down">${T("pr.lower")}</button></div>
            <label class="wide">${T("pr.after")}<select name="horizon">${d.horizons.map((h) => `<option ${h === "4 weeks" ? "selected" : ""}>${esc(h)}</option>`).join("")}</select></label>
            <label class="wide">${T("pr.confidence")} <output id="pconf-out">60%</output><input name="pconf" type="range" min="50" max="95" value="60"></label>
            <label class="wide">${T("pr.your_reason")}<textarea name="reason" rows="3" maxlength="600" placeholder="${T("pr.reason_ph")}"></textarea></label>
          </div>
          <div class="row"><button type="submit" class="btn">${T("pr.log")}</button></div><p class="hint" id="predict-msg"></p>
        </form>
        <div class="panel glass"><h3>${T("pr.scoring")}</h3><p class="hint">${esc(d.note)}</p></div>
      </aside>
    </div>`;
  glossify(document.querySelector("#practice-body .cards")); glossify(document.querySelector("#practice-body aside .panel:last-child"));
}

function renderReplayIntro() {
  $("practice-body").innerHTML = `<div class="layout practice-layout"><div class="col-main"><div class="panel chart-panel"><div id="replay-chart" class="chart replay-empty">
      <div><h2>${T("rp.title")}</h2><p class="hint">${T("rp.intro")}</p>
      <button type="button" class="btn" id="replay-start">${T("rp.start")}</button></div></div></div></div>
    <aside class="col-side"><div class="panel glass" id="replay-side"><h3>${T("rp.record")}</h3><p class="hint">${T("common.loading")}</p></div></aside></div>`;
  api("/api/practice/replay/stats").then(replayStats).catch(() => {});
}
function replayStats(s) {
  const el = $("replay-side"); if (!el) return;
  el.innerHTML = `<h3>${T("rp.record")}</h3><div class="kv"><div><div class="k">${T("rp.charts")}</div><div class="v">${s.count}</div></div><div><div class="k">${T("rp.taken")}</div><div class="v">${s.taken}</div></div>
    <div class="big"><div class="k">${T("rp.avg")}</div><div class="v">${s.avg_r == null ? T("common.na") : (s.avg_r >= 0 ? "+" : "") + s.avg_r}</div><div class="n">${T("rp.avg_note")}</div></div></div>`;
  glossify(el);
}
async function replayStart() {
  try {
    const d = await api("/api/practice/replay/new");
    P.replay = d;
    const seen = d.candles, last = seen[seen.length - 1].close;  // only the visible bars ever reach the page
    const lows = seen.slice(-20).map((c) => c.low), lo = Math.min(...lows);
    document.querySelector("#practice-body .col-main").innerHTML = `<div class="panel chart-panel"><div class="chart-head"><div><b>${T("rp.mystery")}</b> <span class="hint">· ${T("rp.shown", { n: d.visible, price: inr(last) })}</span></div></div><div id="replay-chart" class="chart"></div></div>
      <div class="panel glass"><p class="hint">${esc(d.note)}</p></div>`;
    $("replay-side").innerHTML = `<h3>${T("rp.plan")}</h3><p class="hint">${T("rp.plan_hint", { price: inr(last) })}</p>
      <div class="fields"><label>${T("rp.stop")}<input id="rp-stop" type="number" step="0.05" value="${(lo * 0.995).toFixed(2)}"></label><label>${T("rp.target")}<input id="rp-target" type="number" step="0.05" value="${(last + 2 * (last - lo * 0.995)).toFixed(2)}"></label></div>
      <div class="row"><button type="button" class="btn" id="replay-long">${T("rp.buy")}</button><button type="button" class="btn ghost" id="replay-skip">${T("rp.skip")}</button></div>
      <p class="src">${T("rp.defaults")}</p>`;
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
    v.series.createPriceLine({ price: stop, color: "#8b8b90", lineWidth: 1, lineStyle: 0, axisLabelVisible: true, title: T("chart.stop") });
    if (target) v.series.createPriceLine({ price: target, color: "#facc15", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: T("chart.target") });
  }
  const hidden = res.hidden || [];
  let i = 0;
  const timer = setInterval(() => {
    if (!v || i >= hidden.length) {
      clearInterval(timer);
      if (v) { v.chart.applyOptions({ timeScale: { visible: true } }); v.chart.timeScale().fitContent(); }
      const cls = res.outcome === "target" ? "good" : res.outcome === "stop" ? "bad" : "plain";
      replayStats(res.stats);
      $("replay-side").insertAdjacentHTML("beforeend", `<div class="note ${cls}"><b>${esc(res.outcome === "skipped" ? T("rp.skipped") : res.r == null ? T("rp.result") : (res.r >= 0 ? "+" : "") + res.r + "R")}</b>${esc(res.text)}</div>
        <p class="hint">${T("rp.was", { symbol: esc(res.symbol), from: esc(res.start_date), to: esc(res.end_date) })}</p>
        <div class="row"><button type="button" class="btn" id="replay-start">${T("rp.next")}</button></div>`);
      glossify($("replay-side"));
      return;
    }
    v.series.update({ ...hidden[i] }); i += 1;
  }, 45);
}

/* ======================= NEWS ======================= */
const N = { data: null, cat: "All", tips: false };
const newsCat = (c) => (c === "All" ? T("nw.all") : T("nwcat." + c, null, c));
onView.news = (opts) => loadNews(opts.refresh);
async function loadNews(refresh) {
  $("news-body").innerHTML = `<p class="hint">${T("nw.gathering")}</p>`;
  try { N.data = await api("/api/news" + (refresh ? "?refresh=true" : "")); renderNews(); }
  catch (e) { $("news-body").innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
}
function storyCard(s, big) {
  const img = s.image ? `<div class="ni"><img src="${esc(safeUrl(s.image))}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentNode.remove()"></div>` : "";
  return `<article class="story ${big ? "lead" : ""} ${s.image ? "" : "noimg"}" data-id="${esc(s.id)}">${img}
    <div class="sb"><div class="meta"><span class="chip c-plain">${esc(s.category)}</span>${s.tip ? `<span class="chip c-medium">${T("nw.tip_label")}</span>` : ""}<span>${esc(s.source)}</span><span>${esc(ago(s.published))}</span></div>
      <h3 class="st"><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a></h3>
      ${s.summary ? `<p class="ss">${esc(s.summary)}</p>` : ""}
      <div class="sf">${(s.symbols || []).map((x) => `<button type="button" class="tkr" data-sym="${esc(x)}">${esc(x)}</button>`).join("")}
        <span class="sp"></span><button type="button" class="linkish" data-explain="${esc(s.id)}">${T("nw.explain")}</button>
        <a class="linkish" href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${T("nw.read_source")}</a></div></div></article>`;
}
function renderNews() {
  const d = N.data, cats = ["All"].concat(d.categories.filter((c) => d.stories.some((s) => s.category === c)));
  if (!cats.includes(N.cat)) N.cat = "All";
  $("news-cats").innerHTML = cats.map((c) => `<button type="button" data-cat="${esc(c)}" class="${c === N.cat ? "on" : ""}">${esc(newsCat(c))}</button>`).join("");
  const inCat = d.stories.filter((s) => N.cat === "All" || s.category === N.cat);
  const hiddenTips = inCat.filter((s) => s.tip).length;
  const xs = inCat.filter((s) => N.tips || !s.tip);
  const official = xs.filter((s) => s.kind === "official"), pub = xs.filter((s) => s.kind !== "official");
  if (!xs.length) { $("news-body").innerHTML = `<p class="missing">${T("nw.empty")}</p>`; }
  else {
    const lead = pub.find((s) => s.image) || pub[0];
    const rest = pub.filter((s) => s !== lead);
    $("news-body").innerHTML = `<div class="news-grid">
      <div class="news-main">${lead ? storyCard(lead, true) : ""}<div class="stories">${rest.slice(0, 40).map((s) => storyCard(s)).join("")}</div></div>
      <aside class="news-side"><div class="panel glass"><h3>${T("nw.official")}</h3>${official.length ? official.slice(0, 12).map((s) => `<div class="brief">
          <span class="hint">${esc(s.source)} · ${esc(ago(s.published))}</span><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a>
          <button type="button" class="linkish" data-explain="${esc(s.id)}">${T("nw.explain")}</button></div>`).join("") : `<p class="missing">${T("nw.no_official")}</p>`}</div>
        ${hiddenTips ? `<div class="panel glass"><h3>${T("nw.tips_hidden")}</h3><p class="hint">${T("nw.tips_text", { n: hiddenTips })}</p>
          <div class="row"><button type="button" class="btn ghost sm" id="tips-toggle">${N.tips ? T("nw.hide_again") : T("nw.show_labelled")}</button></div></div>` : ""}
        <div class="panel glass"><h3>${T("nw.reading")}</h3><ul class="plain"><li>${T("nw.r1")}</li>
          <li>${T("nw.r2")}</li><li>${T("nw.r3")}</li></ul></div></aside></div>`;
    glossify($("news-body"));
  }
  const bad = d.sources.filter((s) => s.error);
  $("news-src").textContent = T("nw.src", { note: d.note, sources: d.sources.map((s) => `${s.name} (${s.count})`).join(", "), bad: bad.length ? T("nw.bad", { names: bad.map((s) => s.name).join(", ") }) : "", ago: ago(d.generated) });
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
    openChat(T("nw.explain_prompt"));
  }
});

/* ======================= SETTINGS ======================= */
function fillSettings() {
  const a = aiSettings();
  $("ai-provider").value = a.provider || "gemini"; $("ai-key").value = a.key || ""; $("ai-model").value = a.model || ""; $("ai-base").value = a.base || "";
  $("ai-base-wrap").hidden = $("ai-provider").value !== "openai";
  $("about").textContent = T("set.about", { version: S.cfg ? S.cfg.version : "", disclaimer: S.cfg ? T("disclaimer", null, S.cfg.disclaimer) : "" });
}
$("settings-btn").addEventListener("click", () => { fillSettings(); $("settings").hidden = false; $("side").classList.remove("open"); });
$("settings-x").addEventListener("click", () => { $("settings").hidden = true; });
$("ai-provider").addEventListener("change", () => { $("ai-base-wrap").hidden = $("ai-provider").value !== "openai"; });
$("ai-save").addEventListener("click", () => {
  const a = { provider: $("ai-provider").value, key: $("ai-key").value.trim(), model: $("ai-model").value.trim(), base: $("ai-base").value.trim() };
  localStorage.setItem("belfortAI", JSON.stringify(a)); $("ai-msg").textContent = T("set.saved");
  $("chat-log").innerHTML = "";
});
$("ai-clear").addEventListener("click", () => { localStorage.removeItem("belfortAI"); fillSettings(); $("ai-msg").textContent = T("set.key_removed"); $("chat-log").innerHTML = ""; });
$("backup-file").addEventListener("change", async (e) => {
  const file = e.target.files[0]; e.target.value = "";
  if (!file) return;
  const msg = $("backup-msg");
  if (!confirm(T("set.confirm_restore"))) return;
  try {
    const data = JSON.parse(await file.text());
    msg.textContent = (await post("/api/practice/import", data)).message;
    if (S.view === "practice") loadPractice();
  } catch (err) { msg.textContent = err instanceof SyntaxError ? T("set.bad_json") : err.message; }
});
$("paper-reset").addEventListener("click", async () => {
  if (!confirm(T("set.confirm_reset"))) return;
  try { status((await post("/api/practice/reset")).message); if (S.view === "practice") loadPractice(); } catch (e) { status(e.message, true); }
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("settings").hidden = true; });
