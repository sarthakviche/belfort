"use strict";
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const inr = (x, d = 2) => (x == null ? T("common.na") : formatMoney(x, d));
const num = (x, d = 2) => (x == null ? T("common.na") : formatNumber(x, { max: d }));
const pct = (x, d = 1) => (x == null ? T("common.na") : (x * 100).toFixed(d) + "%");
const signed = (x, d = 1) => (x == null ? `<span class="muted">${T("common.na")}</span>` : `<span class="${x >= 0 ? "up" : "down"}">${x >= 0 ? "+" : ""}${Number(x).toFixed(d)}%</span>`);
const missing = (why) => `<span class="missing">${T("common.not_available", { why: esc(why || T("common.no_reason")) })}</span>`;
const src = (o) => (o && o.source ? `<div class="src">${T("common.source", { source: esc(o.source) })}${o.as_of ? T("common.as_of", { date: esc(o.as_of) }) : ""}</div>` : "");
const chip = (cls, text) => `<span class="chip c-${cls}">${esc(text)}</span>`;
const compact = (x) => (x == null ? T("common.na") : x >= 1e7 ? (x / 1e7).toFixed(2) + " " + T("common.cr") : x >= 1e5 ? (x / 1e5).toFixed(2) + " " + T("common.lakh") : num(x, 0));

const S = { report: null, symbol: null, style: localStorage.getItem("style") || "swing", tab: null, list: "large", screens: null,
  chat: [], cfg: null, view: "home", chatCtx: null };

/* ---------- sidebar: index, open files, breadcrumb ---------- */
const FILES_KEY = "belfortFiles";
const readFiles = () => { try { return JSON.parse(localStorage.getItem(FILES_KEY)) || []; } catch (e) { return []; } };
function rememberFile(d) {
  const f = readFiles().filter((x) => x.symbol !== d.symbol);
  f.unshift({ symbol: d.symbol, name: d.name, close: d.price.close, chg: d.price.change_pct, label: d.verdict.label });
  localStorage.setItem(FILES_KEY, JSON.stringify(f.slice(0, 6)));
  renderFiles();
}
function renderFiles() {
  const f = readFiles(), box = $("files");
  $("files-clear").hidden = !f.length;
  box.innerHTML = f.length ? f.map((x) => `<button type="button" class="file ${x.symbol === S.symbol && !$("report").hidden ? "on" : ""}" data-sym="${esc(x.symbol)}">
      <div><b>${esc(x.symbol)}</b><span>${esc(x.name)}</span></div>
      <div class="px">${inr(x.close)}<i class="${x.chg >= 0 ? "up" : "down"}">${x.chg >= 0 ? "▲" : "▼"} ${Math.abs(x.chg)}%</i></div></button>`).join("")
    : `<div class="files-empty">${T("files.empty")}</div>`;
}
/* ---------- views: research (home, report), learn, practice, news ---------- */
const VIEWS = ["home", "report", "learn", "practice", "news", "dictionary"];
const viewName = (v) => T("nav." + (v === "report" ? "research" : v));
const onView = {};   // verticals.js registers a loader per view
function setCrumb(extra) {
  const v = S.view, tail = v === "report" && S.report ? S.report.name : extra;
  $("crumb").innerHTML = `Belfort / ${tail ? `${esc(viewName(v))} / <b>${esc(tail)}</b>` : `<b>${esc(viewName(v))}</b>`}`;
  document.querySelectorAll(".index .ix").forEach((b) => b.classList.toggle("on", b.dataset.view === (v === "report" ? "home" : v)));
}
function go(view, opts) {
  S.view = view;
  VIEWS.forEach((v) => { $(v).hidden = v !== view; });
  status(""); setCrumb(); renderFiles(); $("side").classList.remove("open");
  if (!(opts && opts.keepScroll)) scrollTo(0, 0);
  if (view !== "report" && location.hash !== "#" + view) history.replaceState(null, "", view === "home" ? location.pathname : "#" + view);
  if (onView[view]) onView[view](opts || {});
}
function showHome() { go("home"); }
document.querySelector(".index").addEventListener("click", (e) => { const b = e.target.closest("button[data-view]"); if (b) go(b.dataset.view); });
$("files").addEventListener("click", (e) => { const b = e.target.closest("button[data-sym]"); if (b) { $("side").classList.remove("open"); load(b.dataset.sym); } });
$("files-clear").addEventListener("click", () => { localStorage.removeItem(FILES_KEY); renderFiles(); });
$("menu").addEventListener("click", () => $("side").classList.toggle("open"));
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) { e.preventDefault(); $("q").focus(); }
});
let chart = null, reqId = 0;

function headers(extra) {
  const code = localStorage.getItem("accessCode");
  return Object.assign({ "X-Belfort-Lang": I18N.lang }, code ? { "X-Access-Code": code } : {}, extra || {});
}
const aiSettings = () => { try { return JSON.parse(localStorage.getItem("belfortAI")) || {}; } catch (e) { return {}; } };
function aiHeaders() {
  const a = aiSettings(), h = {};
  if (a.provider) h["X-AI-Provider"] = a.provider;
  if (a.key) h["X-AI-Key"] = a.key;
  if (a.model) h["X-AI-Model"] = a.model;
  if (a.base) h["X-AI-Base"] = a.base;
  return h;
}
const aiReady = () => { const a = aiSettings(); return !!(a.key || (a.provider === "openai" && /localhost|127\.0\.0\.1/.test(a.base || "")) || (S.cfg && S.cfg.chat_env_ready)); };
async function api(path, opts) {
  let r = await fetch(path, Object.assign({}, opts, { headers: headers(opts && opts.headers) }));
  if (r.status === 401) {
    const code = prompt(T("err.access_prompt"));
    if (!code) throw new Error(T("err.access_required"));
    localStorage.setItem("accessCode", code.trim());
    r = await fetch(path, Object.assign({}, opts, { headers: headers(opts && opts.headers) }));
    if (r.status === 401) { localStorage.removeItem("accessCode"); throw new Error(T("err.access_rejected")); }
  }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) { const err = new Error(typeof data.detail === "string" ? data.detail : T("err.check_values")); err.key = r.headers.get("X-Error-Key") || ""; err.status = r.status; throw err; }
  return data;
}
function status(text, err) { const el = $("status"); el.className = "status" + (err ? " err" : ""); el.textContent = text || ""; }

/* ---------- dictionary: hover explanations ---------- */
const GL = { re: null, map: {}, list: [] };
function buildGloss(list) {
  const alts = [];
  list.forEach((g, i) => g.match.forEach((m) => { GL.map[m.toLowerCase()] = i; alts.push(m); }));
  alts.sort((a, b) => b.length - a.length);
  GL.re = new RegExp("(?<![A-Za-z])(" + alts.map((a) => a.replace(/[.*+?^${}()|[\]\\\/]/g, "\\$&")).join("|") + ")(?![A-Za-z])", "gi");
  GL.list = list;
}
function glossify(root) {
  if (!GL.re || !root) return;
  const seen = new Set(), nodes = [];
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: (n) =>
    (n.parentElement.closest(".term,button,input,select,textarea,a,.no-gloss,th") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT) });
  while (w.nextNode()) nodes.push(w.currentNode);
  nodes.forEach((node) => {
    const text = node.nodeValue; let m, last = 0, frag = null; GL.re.lastIndex = 0;
    while ((m = GL.re.exec(text))) {
      const i = GL.map[m[1].toLowerCase()];
      if (i == null || seen.has(i)) continue;
      seen.add(i);
      frag = frag || document.createDocumentFragment();
      frag.append(text.slice(last, m.index));
      const s = document.createElement("span");
      s.className = "term"; s.tabIndex = 0; s.dataset.i = i; s.textContent = m[1];
      frag.append(s); last = m.index + m[1].length;
    }
    if (frag) { frag.append(text.slice(last)); node.replaceWith(frag); }
  });
}
function showTip(el) {
  const g = GL.list[+el.dataset.i]; if (!g) return;
  const tip = $("tip");
  tip.innerHTML = `<b>${esc(g.term)}</b>${esc(g.meaning)}`;
  tip.hidden = false;
  const r = el.getBoundingClientRect(), tw = tip.offsetWidth, th = tip.offsetHeight;
  let x = Math.min(Math.max(8, r.left), innerWidth - tw - 8), y = r.bottom + 6;
  if (y + th > innerHeight - 8) y = r.top - th - 6;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}
const hideTip = () => { $("tip").hidden = true; };
document.addEventListener("mouseover", (e) => { const t = e.target.closest && e.target.closest(".term"); if (t) showTip(t); });
document.addEventListener("mouseout", (e) => { if (e.target.closest && e.target.closest(".term")) hideTip(); });
document.addEventListener("focusin", (e) => { const t = e.target.closest && e.target.closest(".term"); if (t) showTip(t); });
document.addEventListener("focusout", hideTip);
document.addEventListener("click", (e) => { const t = e.target.closest && e.target.closest(".term"); if (t) showTip(t); else hideTip(); });
window.addEventListener("scroll", hideTip, true);

function renderDict(filter) {
  const f = (filter || "").toLowerCase(), groups = {};
  GL.list.filter((g) => !f || g.term.toLowerCase().includes(f) || g.meaning.toLowerCase().includes(f))
    .forEach((g) => { (groups[g.group] = groups[g.group] || []).push(g); });
  $("dict-list").innerHTML = Object.keys(groups).map((k) => `<h3>${esc(k)}</h3><dl>${groups[k]
    .map((g) => `<dt>${esc(g.term)}</dt><dd>${esc(g.meaning)}</dd>`).join("")}</dl>`).join("") || `<p class="missing">${T("dict.none")}</p>`;
}

/* ---------- search (the picker itself lives in stock-picker.js) ---------- */
$("q").addEventListener("stock-pick", (e) => { load(e.detail.symbol); $("q").value = ""; $("q").blur(); });

/* ---------- home: stock lists ---------- */
async function loadScreens() {
  try {
    const d = await api("/api/screens");
    if (d.status === "ready") { S.screens = d; renderLists(); return; }
    $("list-body").innerHTML = `<p class="missing">${esc(d.message || T("home.preparing"))}</p>`;
    if (d.status === "building") setTimeout(loadScreens, 4000);
  } catch (e) { $("list-body").innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
}
function renderLists() {
  const d = S.screens, L = d.lists;
  if (!L[S.list]) S.list = Object.keys(L)[0];
  $("list-tabs").innerHTML = Object.keys(L).map((k) => `<button type="button" data-k="${k}" class="card-list ${k === S.list ? "on" : ""}"><span class="eyebrow">${T("home.list")}</span>
    <span class="n">${L[k].rows.length}</span><span class="t">${esc(L[k].title)}</span><span class="s">${esc(L[k].subtitle)}</span></button>`).join("");
  const cur = L[S.list];
  $("list-criteria").innerHTML = `<b>${esc(cur.subtitle)}.</b> ${esc(cur.criteria)}`;
  $("list-body").innerHTML = cur.rows.length ? `<table class="rows"><thead><tr><th>${T("home.col_company")}</th><th class="num">${T("home.col_price")}</th><th class="num">${T("home.col_1d")}</th><th class="num">${T("home.col_1m")}</th>
      <th class="num">${T("home.col_3m")}</th><th class="num">${T("home.col_high")}</th><th>${T("home.col_trend")}</th><th class="num">${T("home.col_pe")}</th><th>${T("home.col_why")}</th></tr></thead><tbody>
    ${cur.rows.map((r) => `<tr tabindex="0" data-sym="${esc(r.symbol)}"><td><div class="co"><div class="tick">${esc(r.symbol.slice(0, 2))}</div><div><div class="sym">${esc(r.symbol)}</div><div class="nm">${esc(r.name)}</div></div></div></td>
      <td class="num">${inr(r.close)}</td><td class="num">${signed(r.chg_1d, 2)}</td><td class="num">${signed(r.chg_1m)}</td><td class="num">${signed(r.chg_3m)}</td>
      <td class="num">${r.from_high}%</td><td>${chip(r.trend, T("trend." + r.trend, null, r.trend) + (r.phase === "early" ? " · " + T("home.new") : ""))}</td><td class="num">${r.pe ? num(r.pe, 1) : T("common.na")}</td>
      <td class="why">${esc(r.why)}</td></tr>`).join("")}</tbody></table>`
    : `<p class="missing">${T("home.empty")}</p>`;
  $("list-src").textContent = T("home.list_src", { note: d.note, source: d.source, as_of: d.as_of, generated: d.generated, coverage: d.coverage });
  glossify($("list-criteria")); glossify($("list-body"));
}
$("list-tabs").addEventListener("click", (e) => { const b = e.target.closest("button[data-k]"); if (b) { S.list = b.dataset.k; renderLists(); } });
$("nav-ask").addEventListener("click", () => { $("side").classList.remove("open"); openChat(); });
window.addEventListener("hashchange", () => { const v = location.hash.slice(1) || "home"; if (VIEWS.includes(v) && v !== S.view && v !== "report") go(v); });
$("list-body").addEventListener("click", (e) => { const tr = e.target.closest("tr[data-sym]"); if (tr && !e.target.closest(".term")) load(tr.dataset.sym); });
$("list-body").addEventListener("keydown", (e) => { const tr = e.target.closest("tr[data-sym]"); if (tr && e.key === "Enter") load(tr.dataset.sym); });
$("home-link").addEventListener("click", (e) => { e.preventDefault(); showHome(); });

/* ---------- analysis ---------- */
async function load(symbol) {
  S.symbol = symbol;
  const id = ++reqId;
  const q = new URLSearchParams({ symbol, style: S.style, capital: $("capital").value || 100000, risk_pct: $("risk").value || 1 });
  if ($("stop").value) q.set("stop", $("stop").value);
  status(T("status.fetching"));
  try {
    const d = await api("/api/analyze?" + q);
    if (id !== reqId) return;
    if (S.report && S.report.symbol !== d.symbol) S.tab = null;
    S.report = d; S.symbol = d.symbol; $("q").value = "";
    localStorage.setItem("capital", $("capital").value); localStorage.setItem("risk", $("risk").value); localStorage.setItem("style", S.style);
    S.view = "report"; VIEWS.forEach((v) => { $(v).hidden = v !== "report"; });
    render(d); status(""); rememberFile(d); setCrumb(); $("side").classList.remove("open");
  } catch (e) { if (id === reqId) status(e.message || T("err.generic"), true); }
}
const reload = () => { if (S.symbol) load(S.symbol); };
$("style-seg").addEventListener("click", (e) => { const b = e.target.closest("button[data-style]"); if (b && b.dataset.style !== S.style) { S.style = b.dataset.style; $("stop").value = ""; reload(); } });
["capital", "risk", "stop"].forEach((id) => $(id).addEventListener("change", reload));

const badgeClass = (k) => ({ met: "b-valid", partial: "b-watch", excluded: "b-avoid" }[k] || "b-none");
/* the six report sections, shown as glass folders */
const ICONS = {
  overview: '<path d="M5 12l4 4L19 7"/>', levels: '<path d="M4 6h16M4 12h10M4 18h13"/>', business: '<path d="M4 20V9l8-5 8 5v11M9 20v-6h6v6"/>',
  risks: '<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>', patterns: '<path d="M3 17l5-6 4 3 5-8 4 4"/>', sources: '<path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/>' };
const dotGrid = (() => { let o = ""; for (let r = 0; r < 5; r++) for (let c = 0; c < 13; c++) o += `<circle cx="${8 + c * 14}" cy="${12 + r * 14}" r="3" fill="${(r * 13 + c) % 3 === 0 && c > r ? "#facc15" : "#c4c4be"}"/>`; return `<svg viewBox="0 0 190 80">${o}</svg>`; })();
const ART = {
  overview: dotGrid,
  levels: '<svg viewBox="0 0 190 80"><g fill="#c4c4be"><rect x="0" y="6" width="150" height="9" rx="4.5"/><rect x="0" y="26" width="110" height="9" rx="4.5"/><rect x="0" y="46" width="130" height="9" rx="4.5"/></g><rect x="0" y="66" width="70" height="9" rx="4.5" fill="#facc15"/></svg>',
  business: '<svg viewBox="0 0 190 80"><g fill="#c4c4be"><rect x="8" y="42" width="22" height="38" rx="5"/><rect x="40" y="30" width="22" height="50" rx="5"/><rect x="72" y="20" width="22" height="60" rx="5"/><rect x="104" y="10" width="22" height="70" rx="5"/></g><rect x="136" y="0" width="22" height="80" rx="5" fill="#facc15"/></svg>',
  risks: '<svg viewBox="0 0 190 80"><path d="M0 60 C25 20 45 70 70 40 S110 10 130 38 S170 60 190 18" fill="none" stroke="#9a9a94" stroke-width="3"/><path d="M0 60 C25 20 45 70 70 40 S110 10 130 38 S170 60 190 18 V80 H0Z" fill="#facc15" opacity=".28"/></svg>',
  patterns: '<svg viewBox="0 0 190 80"><g fill="#c4c4be"><rect x="0" y="40" width="26" height="40" rx="4"/><rect x="36" y="22" width="26" height="58" rx="4"/><rect x="108" y="48" width="26" height="32" rx="4"/><rect x="144" y="34" width="26" height="46" rx="4"/></g><rect x="72" y="6" width="26" height="74" rx="4" fill="#facc15"/></svg>',
  sources: '<svg viewBox="0 0 190 80"><g fill="#c4c4be"><rect x="0" y="4" width="120" height="8" rx="4"/><rect x="0" y="22" width="170" height="8" rx="4"/><rect x="0" y="40" width="150" height="8" rx="4"/></g><rect x="0" y="58" width="90" height="8" rx="4" fill="#facc15"/></svg>' };
const TAB_KEYS = ["overview", "levels", "business", "risks", "patterns", "sources"];
const tabs = () => TAB_KEYS.map((k) => [k, T("tab." + k), T("tab." + k + "_sub")]);
const svgIcon = (k, extra = "") => `<svg ${extra} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[k]}</svg>`;

function dossier(d) {
  $("folders").innerHTML = tabs().map(([k, t, sub], i) => `<button type="button" class="folder ${i === 0 ? "hot" : ""}" data-tab="${k}">
    <div class="sheet b"></div><div class="sheet c"></div><div class="sheet">${ART[k]}</div>
    <div class="front">${svgIcon(k, 'class="ic"')}<div class="go"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M7 17L17 7M8 7h9v9"/></svg></div>
    <h3>${t}</h3><p>${sub}</p></div></button>`).join("");
  $("tabs").innerHTML = tabs().map(([k, t]) => `<button type="button" data-tab="${k}" class="${k === S.tab ? "on" : ""}">${t}</button>`).join("");
  const open = !!S.tab;
  $("folders").hidden = open; $("dview").hidden = !open;
  if (open) pane(d);
}
function openTab(k) { S.tab = k; dossier(S.report); $("dossier").scrollIntoView({ behavior: "smooth", block: "start" }); }
$("folders").addEventListener("click", (e) => { const b = e.target.closest("button[data-tab]"); if (b) openTab(b.dataset.tab); });
$("tabs").addEventListener("click", (e) => { const b = e.target.closest("button[data-tab]"); if (b) { S.tab = b.dataset.tab; dossier(S.report); } });
$("dback").addEventListener("click", () => { S.tab = null; dossier(S.report); $("dossier").scrollIntoView({ behavior: "smooth", block: "start" }); });

function render(d) {
  document.querySelectorAll("#style-seg button").forEach((b) => b.classList.toggle("on", b.dataset.style === d.style.key));
  quote(d); verdictCard(d); calc(d); agreeCard(d); dossier(d); drawChart(d);
  scrollTo(0, 0);
}

function quote(d) {
  const q = d.quote, p = d.price, pos = Math.max(0, Math.min(100, (p.close - q.low_52w) / (q.high_52w - q.low_52w) * 100));
  const st = (k, v) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div></div>`;
  $("quote").innerHTML = `
    <div class="id"><div class="nm">${esc(d.name)}</div><div class="meta">${chip("plain", "NSE: " + d.symbol)}${d.sector ? chip("plain", d.sector) : ""}</div></div>
    <div><span class="px">${inr(p.close)}</span><span class="chg ${p.change_pct >= 0 ? "up" : "down"}">${p.change_pct >= 0 ? "+" : ""}${p.change_pct}%</span>
      <div class="asof">${T("quote.close_of", { date: esc(d.as_of) })}</div></div>
    <div class="stats">${st(T("quote.open"), num(q.open))}${st(T("quote.high"), num(q.high))}${st(T("quote.low"), num(q.low))}${st(T("quote.prev"), num(q.prev_close))}${st(T("quote.volume"), compact(q.volume))}
      ${st(T("quote.1w"), signed(q.ret_1w))}${st(T("quote.1m"), signed(q.ret_1m))}${st(T("quote.3m"), signed(q.ret_3m))}${st(T("quote.1y"), signed(q.ret_1y))}
      <div class="stat range"><div class="k">${T("quote.range")}</div><div class="track"><span class="dot" style="left:${pos}%"></span></div>
        <div class="ends"><span>${num(q.low_52w)}</span><span>${num(q.high_52w)}</span></div></div></div>`;
}

function verdictCard(d) {
  const v = d.verdict, met = v.checks.filter((c) => c.passed).length;
  $("verdict").innerHTML = `<h3>${esc(T("verdict.view", { style: T("style." + d.style.key, null, d.style.name), holds: T("style." + d.style.key + "_days", null, d.style.holds) }))}</h3>
    <div class="badge ${badgeClass(v.label_key)}">${esc(T("verdict.label." + v.label_key, null, v.label))}</div>
    ${v.checks.length ? `<div class="meter">${v.checks.map((c) => `<i class="${c.passed ? "on" : ""}"></i>`).join("")}</div>` : ""}
    <p>${esc(v.summary)}</p>
    ${v.checks.length ? `<p class="muted">${T("verdict.conditions_met", { met, total: v.checks.length })}</p>` : ""}
    <div class="note ${v.label_key === "excluded" ? "bad" : ""}"><b>${T("verdict.main_risk")}</b>${esc(v.main_risk)}</div>
    <div class="note plain"><b>${T("verdict.wrong_if")}</b>${esc(v.invalidation.text)}</div>
    <div class="src">${T("verdict.note")}</div>`;
  glossify($("verdict"));
}

function calc(d) {
  const s = d.sizing;
  $("calc-out").innerHTML = `${s.error ? `<div class="note bad"><b>${T("calc.note")}</b>${esc(s.error)}</div>` : ""}
    <div class="kv"><div class="big"><div class="k">${T("calc.shares")}</div><div class="v">${num(s.quantity, 0)}</div>
        <div class="n">${T("calc.at_risk", { risk: inr(s.risk_amount), budget: inr(s.risk_budget), pct: s.risk_pct, capital: inr(s.capital, 0) })}</div></div>
      <div><div class="k">${T("calc.entry")}</div><div class="v">${inr(s.entry)}</div><div class="n">${esc(s.entry_basis)}</div></div>
      <div><div class="k">${T("calc.stop_loss")}</div><div class="v">${inr(s.stop)}</div><div class="n">${s.stop_pct == null ? "" : T("calc.below_entry", { pct: s.stop_pct })}</div></div>
      <div><div class="k">${T("calc.loss_share")}</div><div class="v">${inr(s.risk_per_share)}</div><div class="n">${T("calc.if_hit")}</div></div>
      <div><div class="k">${T("calc.invested")}</div><div class="v">${inr(s.position_value, 0)}</div><div class="n">${T("calc.pct_capital", { pct: s.position_pct })}</div></div></div>
    <p class="hint" style="margin-top:10px">${T("calc.basis", { basis: esc(s.stop_basis), capped: s.capped_by_capital ? T("calc.capped") : "" })}</p>`;
  glossify($("calc"));
}

function agreeCard(d) {
  const a = d.verdict.agreement, cls = { agree: "good", conflict: "bad" }[a.state] || "plain";
  $("agree").innerHTML = `<h3>${T("agree.title")}</h3><div class="note ${cls}"><b>${esc(T("agree.state." + a.state, null, a.state))}</b>${esc(a.text)}</div>
    <div class="src">${T("agree.src", { trend: esc(T("trend." + d.technical.trend.direction, null, d.technical.trend.direction)), business: esc(d.fundamental.verdict || T("agree.na")) })}</div>`;
  glossify($("agree"));
}

function pane(d) {
  const el = $("pane");
  el.innerHTML = ({ overview, levels, business, risks, patterns: patternStats, sources })[S.tab](d);
  glossify(el);
}

function overview(d) {
  const t = d.technical, v = d.verdict;
  return `<h4>${T("overview.rule")}</h4>
    <div class="scroll"><table><thead><tr><th>${T("overview.condition")}</th><th>${T("overview.met")}</th><th>${T("overview.numbers")}</th></tr></thead><tbody>
      ${v.checks.length ? v.checks.map((c) => `<tr><td>${esc(c.name)}</td><td>${chip(c.passed ? "ok" : "no", c.passed ? T("common.yes") : T("common.no"))}</td><td>${esc(c.detail)}</td></tr>`).join("")
        : `<tr><td colspan="3" class="missing">${esc(v.reasons[0] || "")}</td></tr>`}</tbody></table></div>
    <div class="src">${T("overview.explain")}</div>
    <h4>${T("overview.chart_doing")}</h4>
    <ul class="plain">${t.text.map((x) => `<li>${esc(x)}</li>`).join("")}<li>${esc(t.style_text)}</li></ul>
    <div class="src">${T("overview.source", { source: esc(d.price.source), date: esc(d.as_of), bars: d.bars })}</div>`;
}

function levels(d) {
  const t = d.technical;
  const lv = (rows, kind) => rows.length ? rows.map((l) => `<tr><td>${kind}</td><td class="num">${inr(l.price)}</td><td class="num">${l.distance_pct}%</td>
      <td class="num">${l.touches}</td><td>${esc(l.dates.join(", "))}</td></tr>`).join("") : `<tr><td>${kind}</td><td colspan="4" class="missing">${T("common.none_found")}</td></tr>`;
  const pats = t.patterns.length ? t.patterns.map((p) => `<tr><td><b>${esc(p.name)}</b><div class="src">${esc(p.note)}</div></td><td>${esc(p.direction)}</td>
      <td>${esc(p.status)}${p.confirm_date ? `<div class="src">${esc(p.confirm_date)}</div>` : ""}</td><td class="num">${p.score.toFixed(2)}</td>
      <td class="num">${p.target == null ? "n/a" : inr(p.target)}</td><td class="num">${p.invalidation == null ? "n/a" : inr(p.invalidation)}</td>
      <td class="no-gloss">${p.points.map((q) => T("levels.on", { role: esc(q.role), price: inr(q.price), date: esc(q.date) })).join("<br>")}</td></tr>`).join("")
    : `<tr><td colspan="7" class="missing">${T("levels.no_pattern")}</td></tr>`;
  const fib = t.fib ? `<p>${T("levels.fib_text", { direction: esc(t.fib.direction), low: inr(t.fib.low), low_date: esc(t.fib.low_date), high: inr(t.fib.high), high_date: esc(t.fib.high_date) })}
      ${t.fib.levels.map((l) => `${(l.ratio * 100).toFixed(1)}% = ${inr(l.price)}`).join(" · ")}</p>` : `<p>${missing(T("levels.fib_missing"))}</p>`;
  return `<h4>${T("levels.sr")}</h4>
    <div class="scroll"><table><thead><tr><th>${T("levels.type")}</th><th class="num">${T("levels.price")}</th><th class="num">${T("levels.distance")}</th><th class="num">${T("levels.touches")}</th><th>${T("levels.swing_dates")}</th></tr></thead>
      <tbody>${lv(t.levels.resistances.slice().reverse(), T("levels.resistance"))}${lv(t.levels.supports, T("levels.support"))}</tbody></table></div>
    <h4>${T("levels.patterns")}</h4>
    <div class="scroll"><table><thead><tr><th>${T("levels.pattern")}</th><th>${T("levels.bias")}</th><th>${T("levels.status")}</th><th class="num">${T("levels.fit")}</th><th class="num">${T("levels.target")}</th><th class="num">${T("levels.fails")}</th><th>${T("levels.bars_used")}</th></tr></thead>
      <tbody>${pats}</tbody></table></div>
    <div class="src">${T("levels.fit_note")}</div>
    <h4>${T("levels.fib")}</h4>${fib}
    <h4>${T("levels.momentum")}</h4>
    <p>${T("levels.momentum_text", { rsi: t.momentum.rsi.toFixed(1), macd: t.momentum.macd.toFixed(2), signal: t.momentum.macd_signal.toFixed(2), atr: inr(t.atr) })}</p>
    <div class="src">${T("common.source", { source: esc(d.price.source) })}${T("common.as_of", { date: esc(d.as_of) })}</div>`;
}

function business(d) {
  const f = d.fundamental;
  if (!f.available) return `<p>${missing(f.missing_reason)}</p><p>${T("business.capped")}</p>${src(f)}`;
  const cls = { constructive: "good", neutral: "plain", cautious: "bad" }[f.verdict];
  const li = (xs, empty) => xs.length ? `<ul class="plain">${xs.map((x) => `<li><b>${esc(x.title)}.</b> ${esc(x.detail)}</li>`).join("")}</ul>` : `<p class="missing">${empty}</p>`;
  const tbl = f.table, val = f.valuation, p = f.peers, q = f.quarter;
  const peers = p.available ? `<div class="scroll"><table><thead><tr><th>${T("business.peer", { sector: esc(p.sector) })}</th><th class="num">${T("business.pe")}</th><th class="num">${T("business.roe")}</th><th class="num">${T("business.de")}</th></tr></thead><tbody>
      ${p.rows.map((r) => `<tr><td>${esc(r.symbol)}</td><td class="num">${num(r.pe, 1)}</td><td class="num">${num(r.roe_pct, 1)}</td><td class="num">${num(r.debt_to_equity, 2)}</td></tr>`).join("")}
      <tr><td><b>${T("business.median")}</b></td><td class="num"><b>${num(p.median_pe, 1)}</b></td><td class="num"><b>${num(p.median_roe_pct, 1)}</b></td><td></td></tr>
      <tr><td><b>${esc(d.symbol)}</b></td><td class="num"><b>${val.pe == null ? T("common.na") : num(val.pe, 1)}</b></td><td></td><td></td></tr></tbody></table></div>${src(p)}` : `<p>${missing(p.missing_reason)}</p>`;
  return `<div class="note ${cls}"><b>${T("business.read")}</b>${esc(f.text)}</div>
    ${(f.notes || []).map((n) => `<p class="src">${esc(n)}</p>`).join("")}
    <div class="two"><div><h4>${T("business.strengths")}</h4>${li(f.pros, T("business.no_strength"))}</div>
      <div><h4>${T("business.weaknesses")}</h4>${li(f.cons, T("business.no_weakness"))}</div></div>
    <h4>${T("business.history")}</h4>
    <div class="scroll"><table><thead><tr><th>${T("business.figure")}</th>${tbl.periods.map((x) => `<th class="num">${esc(x)}</th>`).join("")}</tr></thead><tbody>
      ${tbl.rows.map((r) => `<tr><td>${esc(r.metric)}</td>${r.values.map((x) => `<td class="num">${x == null ? '<span class="missing">${T("common.missing")}</span>' : num(x, 2)}</td>`).join("")}</tr>`).join("")}
    </tbody></table></div>
    <div class="src">${T("business.history_note", { note: esc(f.history_note), source: esc(f.source), date: esc(f.as_of) })}</div>
    <h4>${T("business.quarter")}</h4>
    <p>${q.available ? T("business.quarter_text", { quarter: esc(q.quarter), sdir: T(q.sales_growth_pct >= 0 ? "business.up" : "business.down"), sales: Math.abs(q.sales_growth_pct), profit: q.profit_growth_pct == null ? "" : T("business.quarter_profit", { pdir: T(q.profit_growth_pct >= 0 ? "business.up" : "business.down"), profit: Math.abs(q.profit_growth_pct) }) }).replace("{profit}", "") : missing(q.missing_reason)}</p>
    <h4>${T("business.valuation")}</h4>
    <p>${T("business.pe")}: ${val.pe == null ? missing(val.missing_reason) : "<b>" + num(val.pe, 1) + "</b>"} · ${T("business.market_value")}: ${val.market_cap_cr == null ? T("common.na") : inr(val.market_cap_cr, 0) + " " + T("common.cr")}</p>
    ${peers}`;
}

function risks(d) {
  const f = d.fundamental, x = d.extras, v = d.verdict, cs = f.concerns || [];
  const dl = x.delivery, bd = x.bulk_deals, er = x.earnings;
  return `<div class="note bad"><b>${T("risks.invalid")}</b>${T("risks.invalid_text", { text: esc(v.invalidation.text) })}</div>
    <h4>${T("risks.concerns")}</h4>
    ${cs.length ? `<div class="scroll"><table><thead><tr><th>${T("risks.severity")}</th><th>${T("risks.concern")}</th><th>${T("risks.figure")}</th><th>${T("risks.period")}</th></tr></thead><tbody>
      ${cs.map((c) => `<tr><td>${chip(c.severity, c.severity === "info" ? T("common.not_checked") : T("sev." + c.severity, null, c.severity))}</td><td>${esc(c.title)}</td><td>${esc(c.detail)}</td><td>${esc(c.period || "")}</td></tr>`).join("")}
    </tbody></table></div>` : `<p>${missing(f.missing_reason || T("risks.not_run"))}</p>`}
    <h4>${T("risks.events")}</h4>
    <ul class="plain">
      <li><b>${T("risks.next_results")}</b> ${er.available ? `${T("risks.results_text", { date: esc(er.date), days: er.trading_days_away })}${src(er)}` : missing(er.missing_reason)}</li>
      <li><b>${T("risks.delivery")}</b> ${dl.available ? `${T("risks.delivery_text", { pct: dl.latest.delivery_pct, date: esc(dl.latest.date), n: dl.rows.length, avg: dl.average_pct })}${src(dl)}` : missing(dl.missing_reason)}</li>
      <li><b>${T("risks.bulk")}</b> ${bd.available ? (bd.deals.length ? bd.deals.map((b) => T("risks.bulk_line", { client: esc(b.client), side: esc(b.side), qty: num(b.quantity, 0), price: inr(b.price), date: esc(b.date) })).join("; ") : T("risks.bulk_none")) + src(bd) : missing(bd.missing_reason)}</li>
      <li><b>${T("risks.depth")}</b> ${missing(x.order_book.missing_reason)}</li>
      <li><b>${T("risks.pledge")}</b> ${missing(x.pledge.missing_reason)}</li>
      <li><b>${T("risks.announcements")}</b> ${missing(x.announcements.missing_reason)}</li>
    </ul>`;
}

function patternStats(d) {
  const s = d.pattern_stats;
  if (!s || s.available === false) return `<p>${missing(s && s.missing_reason)}</p>`;
  const syn = s.synthetic || {}, hist = (s.historical || {})[d.style.key] || {};
  return `<p>${esc(s.headline)}</p>
    <div class="scroll"><table><thead><tr><th>${T("levels.pattern")}</th><th class="num">${T("patterns.textbook")}</th><th class="num">${T("patterns.random")}</th>
      <th class="num">${T("patterns.signals")}</th><th class="num">${T("patterns.target_first")}</th><th class="num">${T("patterns.baseline")}</th><th class="num">${T("patterns.stop_first")}</th></tr></thead><tbody>
      ${Object.keys(syn).map((n) => { const a = syn[n], h = hist[n];
        return `<tr><td>${esc(n)}</td><td class="num">${pct(a.hit_rate, 0)}</td><td class="num">${pct(a.false_positive_rate, 1)}</td>
          ${h ? `<td class="num">${h.signals}${h.small_sample ? "*" : ""}</td><td class="num">${pct(h.reached_target_first, 0)}</td><td class="num">${pct(h.baseline_target_first, 0)}</td><td class="num">${pct(h.hit_invalidation_first, 0)}</td>`
            : `<td class="num">0</td><td colspan="3" class="missing">${T("patterns.no_signal")}</td>`}</tr>`; }).join("")}
    </tbody></table></div>
    <div class="src">${T("patterns.foot", { synthetic: esc(s.synthetic_note), style: esc(T("style." + d.style.key, null, d.style.name)), historical: esc(s.historical_note), generated: esc(s.generated), source: esc(s.source) })}</div>`;
}

function sources(d) {
  return `<div class="scroll"><table><thead><tr><th>${T("sources.what")}</th><th>${T("sources.source")}</th><th>${T("sources.as_of")}</th><th>${T("sources.note")}</th></tr></thead><tbody>
    ${d.sources.map((s) => `<tr><td>${esc(s.item)}</td><td>${s.source === "not available" ? '<span class="missing">${T("sources.not_available")}</span>' : esc(s.source)}</td><td>${esc(s.as_of || "")}</td><td>${esc(s.note || "")}</td></tr>`).join("")}
  </tbody></table></div>`;
}

function drawChart(d) {
  const el = $("chart"), t = d.technical;
  if (chart) { chart.remove(); chart = null; }
  $("legend").innerHTML = `<span><i style="background:#facc15"></i>${T("chart.avg", { n: t.trend.fast_n })}</span><span><i style="background:#f4f4f2"></i>${T("chart.avg", { n: t.trend.slow_n })}</span>
    <span><i style="background:#16c47f"></i>${T("chart.support")}</span><span><i style="background:#ef4444"></i>${T("chart.resistance")}</span><span><i style="background:#8b8b90"></i>${T("chart.stop")}</span>`;
  if (!window.LightweightCharts) { el.innerHTML = `<p class="missing">${T("chart.lib_missing")}</p>`; return; }
  el.innerHTML = "";
  chart = LightweightCharts.createChart(el, { autoSize: true, layout: { background: { color: "transparent" }, textColor: "#8b8b90", fontFamily: "Inter, sans-serif" },
    grid: { vertLines: { color: "rgba(255,255,255,.04)" }, horzLines: { color: "rgba(255,255,255,.05)" } }, rightPriceScale: { borderColor: "rgba(255,255,255,.08)" }, timeScale: { borderColor: "rgba(255,255,255,.08)" },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal } });
  const candles = chart.addCandlestickSeries({ upColor: "#16c47f", downColor: "#ef4444", borderVisible: false, wickUpColor: "#16c47f", wickDownColor: "#ef4444" });
  candles.setData(d.chart.candles);
  const vol = chart.addHistogramSeries({ priceFormat: { type: "volume" }, priceScaleId: "vol", lastValueVisible: false, priceLineVisible: false });
  chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.84, bottom: 0 } });
  vol.setData(d.chart.volume.map((v, i) => ({ time: v.time, value: v.value, color: d.chart.candles[i].close >= d.chart.candles[i].open ? "rgba(22,196,127,.35)" : "rgba(239,68,68,.35)" })));
  chart.addLineSeries({ color: "#facc15", lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }).setData(d.chart.fast);
  chart.addLineSeries({ color: "#f4f4f2", lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }).setData(d.chart.slow);
  const line = (price, color, title, style) => candles.createPriceLine({ price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: true, title });
  t.levels.supports.slice(0, 2).forEach((l) => line(l.price, "#16c47f", T("chart.support"), 2));
  t.levels.resistances.slice(0, 2).forEach((l) => line(l.price, "#ef4444", T("chart.resistance"), 2));
  line(d.sizing.stop, "#8b8b90", T("chart.stop"), 0);
  const first = d.chart.first_date, marks = [];
  t.patterns.filter((p) => !p.name.includes("trend line")).forEach((p) => p.points.forEach((q) => {
    if (q.date >= first) marks.push({ time: q.date, position: "aboveBar", color: p.direction === "bearish" ? "#ef4444" : p.direction === "bullish" ? "#16c47f" : "#facc15", shape: "circle", text: q.role });
  }));
  marks.sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0));
  candles.setMarkers(marks);
  const n = d.chart.candles.length, show = d.style.key === "swing" ? 130 : 260;
  chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, n - show), to: n + 5 });
}

/* ---------- chat ---------- */
function chatContext() {
  if (S.chatCtx && S.chatCtx.view === S.view) return S.chatCtx;
  if (S.view === "report" && S.report) return { mode: "report", text: reportContext() };
  return { mode: "general", text: "" };
}
function reportContext() {
  const d = S.report; if (!d) return "";
  const v = d.verdict, f = d.fundamental;
  return [`${d.name} (${d.symbol}), ${d.style.name} view, close ₹${d.price.close} on ${d.as_of}.`,
    `Label: ${v.label}. ${v.summary}`, `Main risk: ${v.main_risk}`, `Invalidation: ${v.invalidation.text}`,
    "Rule checks: " + v.checks.map((c) => `${c.name}: ${c.passed ? "met" : "NOT met"} (${c.detail})`).join(" | "),
    "Position size: " + d.sizing.text, "Chart: " + d.technical.text.join(" "),
    "Business: " + (f.text || ""), "Strengths: " + (f.pros || []).map((p) => p.title + " - " + p.detail).join(" | "),
    "Concerns: " + (f.concerns || []).map((c) => `[${c.severity}] ${c.title} - ${c.detail}`).join(" | "),
    "Chart versus business: " + v.agreement.text].join("\n").slice(0, 7500);
}
function chatLine(role, text) { const m = document.createElement("div"); m.className = "msg " + role; m.textContent = text; $("chat-log").append(m); $("chat-log").scrollTop = 1e9; return m; }
function openChat(prefill) {
  $("chat").hidden = false; $("chat-fab").hidden = true;
  const ready = aiReady();
  if (!$("chat-log").children.length || !ready) {
    $("chat-log").innerHTML = "";
    chatLine("sys", ready ? T("chat.welcome") : T("chat.need_key"));
  }
  $("chat-in").disabled = !ready;
  if (ready) { if (prefill) $("chat-in").value = prefill; $("chat-in").focus(); }
}
$("chat-fab").addEventListener("click", () => openChat());
$("chat-x").addEventListener("click", () => { $("chat").hidden = true; $("chat-fab").hidden = false; });
$("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = $("chat-in").value.trim(); if (!q) return;
  $("chat-in").value = ""; chatLine("user", q);
  const wait = chatLine("model", T("chat.thinking"));
  try {
    const ctx = chatContext();
    const r = await api("/api/chat", { method: "POST", headers: Object.assign({ "Content-Type": "application/json" }, aiHeaders()),
      body: JSON.stringify({ question: q, history: S.chat.slice(-6), context: ctx.text, mode: ctx.mode }) });
    wait.textContent = r.answer; S.chat.push({ role: "user", text: q }, { role: "model", text: r.answer });
  } catch (err) { wait.className = "msg sys"; wait.textContent = err.message; }
  $("chat-log").scrollTop = 1e9;
});

/* ---------- dictionary drawer ---------- */
$("dict-btn").addEventListener("click", () => { $("side").classList.remove("open"); go("dictionary"); });
$("dict-x").addEventListener("click", () => { $("dict").hidden = true; });
$("dict-q").addEventListener("input", () => renderDict($("dict-q").value));
document.addEventListener("keydown", (e) => { if (e.key === "Escape") { $("dict").hidden = true; hideTip(); } });

/* ---------- start ---------- */
(async function init() {
  await I18N.ready;
  I18N.chips($("lang-chips"));
  fillLangSelect();
  $("capital").value = localStorage.getItem("capital") || 100000;
  $("risk").value = localStorage.getItem("risk") || 1;
  try {
    S.cfg = await (await fetch("/api/config")).json();
    $("disclaimer").textContent = T("disclaimer", null, S.cfg.disclaimer);
    buildGloss(S.cfg.glossary);
    glossify(document.querySelector(".intro")); glossify(document.querySelector("#calc .hint"));
  } catch (e) { /* the page still works without the dictionary */ }
  renderFiles(); setCrumb();
  loadScreens();
  const start = location.hash.slice(1);
  if (["learn", "practice", "news", "dictionary"].includes(start)) go(start);
  document.dispatchEvent(new CustomEvent("belfort:app-ready")); // lets the startup loader fade (splash.js)
})();

/* ---------- language (T50): the header picker, and re-rendering when it changes ---------- */
function fillLangSelect() {
  const sel = $("lang-select");
  sel.innerHTML = I18N.LANGS.map(([c, n]) => `<option value="${c}" lang="${c}">${n}</option>`).join("");
  sel.value = I18N.lang;
}
$("lang-select").addEventListener("change", (e) => I18N.setLanguage(e.target.value));
document.addEventListener("belfort:language", () => {
  $("lang-select").value = I18N.lang;
  if (S.cfg) $("disclaimer").textContent = T("disclaimer", null, S.cfg.disclaimer);
  setCrumb(); renderFiles();
  if (S.screens) renderLists();
  if (S.view === "report" && S.report) { render(S.report); scrollTo(0, 0); }
  else if (S.view !== "home" && onView[S.view]) onView[S.view]({ keepLesson: true });
  if (!$("settings").hidden) fillSettings();
  if (!$("chat").hidden && !$("chat-log").children.length) openChat();
});
