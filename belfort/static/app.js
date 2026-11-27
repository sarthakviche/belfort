"use strict";
const $ = (id) => document.getElementById(id);
/* Charts never take the mouse wheel, so scrolling over one scrolls the page. Drag to pan; pinch or drag an axis to zoom. */
const CHART_POINTER = {
  handleScroll: { mouseWheel: false, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false },
  handleScale: { mouseWheel: false, pinch: true, axisPressedMouseMove: true, axisDoubleClickReset: true },
};
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const inr = (x, d = 2) => (x == null ? "n/a" : "₹" + Number(x).toLocaleString("en-IN", { minimumFractionDigits: d, maximumFractionDigits: d }));
const num = (x, d = 2) => (x == null ? "n/a" : Number(x).toLocaleString("en-IN", { maximumFractionDigits: d }));
const pct = (x, d = 1) => (x == null ? "n/a" : (x * 100).toFixed(d) + "%");
const signed = (x, d = 1) => (x == null ? '<span class="muted">n/a</span>' : `<span class="${x >= 0 ? "up" : "down"}">${x >= 0 ? "+" : ""}${Number(x).toFixed(d)}%</span>`);
const missing = (why) => `<span class="missing">Not available: ${esc(why || "no reason given")}</span>`;
const src = (o) => (o && o.source ? `<div class="src">Source: ${esc(o.source)}${o.as_of ? " · as of " + esc(o.as_of) : ""}</div>` : "");
const chip = (cls, text) => `<span class="chip c-${cls}">${esc(text)}</span>`;
const compact = (x) => (x == null ? "n/a" : x >= 1e7 ? (x / 1e7).toFixed(2) + " cr" : x >= 1e5 ? (x / 1e5).toFixed(2) + " lakh" : num(x, 0));

const S = { report: null, symbol: null, style: localStorage.getItem("style") || "swing", tab: null, list: "large", screens: null,
  chat: [], cfg: null, view: "home", chatCtx: null };

/* ---------- sidebar: index, recent stocks, breadcrumb ---------- */
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
    : '<div class="files-empty">No stocks yet. Search a company to see its report here.</div>';
}
/* ---------- views: research (home, report), learn, practice, news ---------- */
const VIEWS = ["home", "report", "learn", "practice", "news"];
const VIEW_NAME = { home: "Research", report: "Research", learn: "Learn", practice: "Practice", news: "News" };
const onView = {};   // verticals.js registers a loader per view
function setCrumb(extra) {
  const v = S.view, tail = v === "report" && S.report ? S.report.name : extra;
  $("crumb").innerHTML = `Belfort / ${tail ? `${esc(VIEW_NAME[v])} / <b>${esc(tail)}</b>` : `<b>${esc(VIEW_NAME[v])}</b>`}`;
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
  return Object.assign(code ? { "X-Access-Code": code } : {}, extra || {});
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
    const code = prompt("Enter your access code");
    if (!code) throw new Error("An access code is required.");
    localStorage.setItem("accessCode", code.trim());
    r = await fetch(path, Object.assign({}, opts, { headers: headers(opts && opts.headers) }));
    if (r.status === 401) { localStorage.removeItem("accessCode"); throw new Error("That access code was not accepted."); }
  }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Check the values you entered.");
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
    .map((g) => `<dt>${esc(g.term)}</dt><dd>${esc(g.meaning)}</dd>`).join("")}</dl>`).join("") || '<p class="missing">No term matches.</p>';
}

/* ---------- search (the picker itself lives in stock-picker.js) ---------- */
$("q").addEventListener("stock-pick", (e) => { load(e.detail.symbol); $("q").value = ""; $("q").blur(); });

/* ---------- home: stock lists ---------- */
async function loadScreens() {
  try {
    const d = await api("/api/screens");
    if (d.status === "ready") { S.screens = d; renderLists(); return; }
    $("list-body").innerHTML = `<p class="missing">${esc(d.message || "Preparing the lists…")}</p>`;
    if (d.status === "building") setTimeout(loadScreens, 4000);
  } catch (e) { $("list-body").innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
}
function renderLists() {
  const d = S.screens, L = d.lists;
  if (!L[S.list]) S.list = Object.keys(L)[0];
  $("list-tabs").innerHTML = Object.keys(L).map((k) => `<button type="button" data-k="${k}" class="card-list ${k === S.list ? "on" : ""}"><span class="eyebrow">List</span>
    <span class="n">${L[k].rows.length}</span><span class="t">${esc(L[k].title)}</span><span class="s">${esc(L[k].subtitle)}</span></button>`).join("");
  const cur = L[S.list];
  $("list-criteria").innerHTML = `<b>${esc(cur.subtitle)}.</b> ${esc(cur.criteria)}`;
  $("list-body").innerHTML = cur.rows.length ? `<table class="rows"><thead><tr><th>Company</th><th class="num">Price</th><th class="num">1 day</th><th class="num">1 month</th>
      <th class="num">3 months</th><th class="num">From 1-yr high</th><th>Trend</th><th class="num">P/E</th><th>Why it is on this list</th></tr></thead><tbody>
    ${cur.rows.map((r) => `<tr tabindex="0" data-sym="${esc(r.symbol)}"><td><div class="co"><div class="tick">${esc(r.symbol.slice(0, 2))}</div><div><div class="sym">${esc(r.symbol)}</div><div class="nm">${esc(r.name)}</div></div></div></td>
      <td class="num">${inr(r.close)}</td><td class="num">${signed(r.chg_1d, 2)}</td><td class="num">${signed(r.chg_1m)}</td><td class="num">${signed(r.chg_3m)}</td>
      <td class="num">${r.from_high}%</td><td>${chip(r.trend, r.trend + (r.phase === "early" ? " · new" : ""))}</td><td class="num">${r.pe ? num(r.pe, 1) : "n/a"}</td>
      <td class="why">${esc(r.why)}</td></tr>`).join("")}</tbody></table>`
    : '<p class="missing">No stock in the built-in list meets every criterion today. That is a normal result for a strict screen.</p>';
  $("list-src").textContent = `${d.note} Source: ${d.source}, prices as of ${d.as_of}; built ${d.generated}. ${d.coverage}`;
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
  status("Fetching prices and company figures, then computing…");
  try {
    const d = await api("/api/analyze?" + q);
    if (id !== reqId) return;
    // Same stock in the same view (a style, capital, risk or stop change): keep the reader where they were.
    const sameStock = S.view === "report" && S.report && S.report.symbol === d.symbol;
    if (!sameStock) S.tab = null;
    S.report = d; S.symbol = d.symbol; $("q").value = "";
    localStorage.setItem("capital", $("capital").value); localStorage.setItem("risk", $("risk").value); localStorage.setItem("style", S.style);
    S.view = "report"; VIEWS.forEach((v) => { $(v).hidden = v !== "report"; });
    render(d, sameStock); status(""); rememberFile(d); setCrumb(); $("side").classList.remove("open");
  } catch (e) { if (id === reqId) status(e.message || "Something went wrong.", true); }
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
const TABS = [["overview", "Why this label", "The rule behind the verdict, one condition at a time."], ["levels", "Levels and patterns", "Support, resistance, Fibonacci and detected shapes."],
  ["business", "Business", "Returns, debt, growth and how it compares with peers."], ["risks", "What would make me wrong", "Concerns ranked by severity, and upcoming events."],
  ["patterns", "Pattern reliability", "How often each pattern actually worked."], ["sources", "Sources", "Where every number came from, and as of when."]];
const svgIcon = (k, extra = "") => `<svg ${extra} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[k]}</svg>`;

function dossier(d) {
  $("folders").innerHTML = TABS.map(([k, t, sub], i) => `<button type="button" class="folder ${i === 0 ? "hot" : ""}" data-tab="${k}">
    <div class="sheet b"></div><div class="sheet c"></div><div class="sheet">${ART[k]}</div>
    <div class="front">${svgIcon(k, 'class="ic"')}<div class="go"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M7 17L17 7M8 7h9v9"/></svg></div>
    <h3>${t}</h3><p>${sub}</p></div></button>`).join("");
  $("tabs").innerHTML = TABS.map(([k, t]) => `<button type="button" data-tab="${k}" class="${k === S.tab ? "on" : ""}">${t}</button>`).join("");
  const open = !!S.tab;
  $("folders").hidden = open; $("dview").hidden = !open;
  if (open) pane(d);
}
function openTab(k) { S.tab = k; dossier(S.report); $("dossier").scrollIntoView({ behavior: "smooth", block: "start" }); }
$("folders").addEventListener("click", (e) => { const b = e.target.closest("button[data-tab]"); if (b) openTab(b.dataset.tab); });
$("tabs").addEventListener("click", (e) => { const b = e.target.closest("button[data-tab]"); if (b) { S.tab = b.dataset.tab; dossier(S.report); } });
$("dback").addEventListener("click", () => { S.tab = null; dossier(S.report); $("dossier").scrollIntoView({ behavior: "smooth", block: "start" }); });

/* A new stock opens at the top. Re-rendering the same stock (switching swing and positional, or changing capital, risk
   or stop) keeps the scroll position, so the reader stays at the chart or section they were looking at. */
function render(d, keepScroll = false) {
  const y = scrollY;
  document.querySelectorAll("#style-seg button").forEach((b) => b.classList.toggle("on", b.dataset.style === d.style.key));
  quote(d); companyCard(d); verdictCard(d); calc(d); agreeCard(d); dossier(d); drawChart(d);
  scrollTo({ top: keepScroll ? y : 0, behavior: "instant" });
}

function quote(d) {
  const q = d.quote, p = d.price, pos = Math.max(0, Math.min(100, (p.close - q.low_52w) / (q.high_52w - q.low_52w) * 100));
  const st = (k, v) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div></div>`;
  $("quote").innerHTML = `
    <div class="id"><div class="nm">${esc(d.name)}</div><div class="meta">${chip("plain", "NSE: " + d.symbol)}${d.sector ? chip("plain", d.sector) : ""}</div></div>
    <div><span class="px">${inr(p.close)}</span><span class="chg ${p.change_pct >= 0 ? "up" : "down"}">${p.change_pct >= 0 ? "+" : ""}${p.change_pct}%</span>
      <div class="asof">Close of ${esc(d.as_of)} · end-of-day data, not live</div></div>
    <div class="stats">${st("Open", num(q.open))}${st("High", num(q.high))}${st("Low", num(q.low))}${st("Prev close", num(q.prev_close))}${st("Volume", compact(q.volume))}
      ${st("1 week", signed(q.ret_1w))}${st("1 month", signed(q.ret_1m))}${st("3 months", signed(q.ret_3m))}${st("1 year", signed(q.ret_1y))}
      <div class="stat range"><div class="k">52-week range</div><div class="track"><span class="dot" style="left:${pos}%"></span></div>
        <div class="ends"><span>${num(q.low_52w)}</span><span>${num(q.high_52w)}</span></div></div></div>`;
}

/* What the company does, before any chart: the source's own description, then the business read, its strengths and
   weaknesses, and a few headline numbers from the latest year. */
function companyCard(d) {
  const p = d.profile || {}, f = d.fundamental, el = $("company");
  const site = p.website ? p.website.replace(/^https?:\/\//, "").replace(/\/$/, "") : "";
  const facts = [p.industry && esc(p.industry), p.employees && `${Number(p.employees).toLocaleString("en-IN")} employees`,
    p.website && `<a href="${esc(p.website)}" target="_blank" rel="noopener noreferrer">${esc(site)} ↗</a>`].filter(Boolean);
  let biz = `<p>${missing(f.missing_reason || "Business figures not available.")}</p>`;
  if (f.available) {
    const kind = { constructive: "ok", cautious: "no" }[f.verdict] || "plain";
    const latest = (name) => { const r = f.table.rows.find((x) => x.metric === name); return r ? r.values[r.values.length - 1] : null; };
    /* Headline numbers from the latest year, each with the comparison that gives it meaning: last year's value, or
       the sector's peer median. Rows the source did not return (banks have no operating margin) are left out. */
    const row = (name) => f.table.rows.find((x) => x.metric === name);
    const prev = (name) => { const r = row(name); return r && r.values.length > 1 ? r.values[r.values.length - 2] : null; };
    const peer = f.peers && f.peers.available ? f.peers : null, yr = f.table.periods[f.table.periods.length - 2];
    const was = (name, d, u = "") => prev(name) == null ? "" : `${esc(yr)}: ${num(prev(name), d)}${u}`;
    const kv = [
      ["Sales", latest("Sales (₹ cr)"), (v) => inr(v, 0) + " cr", latest("Sales growth %") == null ? "" : `${latest("Sales growth %") >= 0 ? "up" : "down"} ${num(Math.abs(latest("Sales growth %")), 1)}% on the year`],
      ["Net profit", latest("Net profit (₹ cr)"), (v) => inr(v, 0) + " cr", prev("Net profit (₹ cr)") ? `${esc(yr)}: ${inr(prev("Net profit (₹ cr)"), 0)} cr` : ""],
      ["Net margin", latest("Net margin %"), (v) => num(v, 1) + "%", was("Net margin %", 1, "%")],
      ["Operating margin", latest("Operating margin %"), (v) => num(v, 1) + "%", was("Operating margin %", 1, "%")],
      ["Return on equity", latest("Return on equity %"), (v) => num(v, 1) + "%", peer && peer.median_roe_pct != null ? `${esc(peer.sector)} median ${num(peer.median_roe_pct, 1)}%` : was("Return on equity %", 1, "%")],
      ["Debt to equity", latest("Debt to equity"), (v) => num(v, 2), was("Debt to equity", 2)],
      ["P/E", f.valuation.pe, (v) => num(v, 1), peer && peer.median_pe != null ? `${esc(peer.sector)} median ${num(peer.median_pe, 1)}` : ""],
      ["Price to book", f.valuation.price_to_book, (v) => num(v, 2), ""],
      ["Market value", f.valuation.market_cap_cr, (v) => inr(v, 0) + " cr", ""],
    ].filter((x) => x[1] != null)
      .map(([k, v, fmt, note]) => `<div class="stat"><div class="k">${k}</div><div class="v">${fmt(v)}</div>${note ? `<div class="n">${note}</div>` : ""}</div>`).join("");
    const top = (xs, empty) => xs.length ? `<ul class="plain">${xs.slice(0, 3).map((x) => `<li><b>${esc(x.title)}.</b> ${esc(x.detail)}</li>`).join("")}</ul>` : `<p class="muted">${empty}</p>`;
    biz = `<div class="biz-head">${chip(kind, "Business read: " + f.verdict)}<span class="muted">${esc(f.table.periods[f.table.periods.length - 1] || "")} figures · ${esc(f.source)}</span></div>
      <div class="kstats">${kv}</div>
      <div class="two"><div><h4>Strengths</h4>${top(f.pros, "No strength met the thresholds.")}</div><div><h4>Weaknesses</h4>${top(f.cons, "No weakness was flagged by the checks that ran.")}</div></div>
      <p class="muted">Latest quarter: ${quarterText(f.quarter)}${f.quarter.stale_note ? ` <span class="missing">${esc(f.quarter.stale_note)}</span>` : ""}</p>`;
  }
  el.innerHTML = `<div class="eyebrow">What the company does</div>
    <p class="profile">${p.available ? esc(p.summary) : missing(p.missing_reason || "No company description from the source.")}</p>
    ${facts.length ? `<p class="muted facts">${facts.join(" · ")}</p>` : ""}${biz}
    <div class="src">The full business table, peers and valuation are in the dossier below.</div>`;
  glossify(el);
}

/* The verdict with a navigator over the rule's checks. The first unmet check opens first; each shows what the numbers
   say and, for an unmet check, the context behind it. Navigating never changes the label. */
let checkAt = 0;
function verdictCard(d) {
  const v = d.verdict, cs = v.checks;
  const firstFail = cs.findIndex((c) => !c.passed);
  checkAt = firstFail >= 0 ? firstFail : 0;
  $("verdict").innerHTML = `<h3>${esc(d.style.name)} view · ${esc(d.style.holds)}</h3>
    <div class="badge ${badgeClass(v.label_key)}">${esc(v.label)}</div>
    <p>${esc(v.summary)}</p>
    ${cs.length ? `<div class="checknav"><div class="steps" role="tablist" aria-label="Rule checks">${cs.map((c, i) => `<button type="button" role="tab" data-check="${i}" class="${c.passed ? "ok" : "no"}" title="${esc(c.name)}" aria-label="Check ${i + 1}: ${esc(c.name)}, ${c.passed ? "met" : "not met"}">${i + 1}</button>`).join("")}</div>
      <p class="muted">Yellow is met, red is not. Select a number to read that check.</p><div id="check-view"></div></div>` : ""}
    ${v.context && v.context.facts.length ? `<div class="note plain"><b>What else the numbers show</b><ul class="plain">${v.context.facts.map((f) => `<li>${esc(f)}</li>`).join("")}</ul><span class="muted">${esc(v.context.note)}</span></div>` : ""}
    <div class="two"><div class="note ${v.label_key === "excluded" ? "bad" : ""}"><b>Main risk</b>${esc(v.main_risk)}</div>
      <div class="note plain"><b>The view is wrong if</b>${esc(v.invalidation.text)}</div></div>
    <div class="src">A fixed, published rule produces this label from the numbers on this page. It states which conditions hold. It is not a recommendation to buy, sell or hold.</div>`;
  if (cs.length) showCheck(d);
  glossify($("verdict"));
}

function showCheck(d) {
  const cs = d.verdict.checks, c = cs[checkAt];
  document.querySelectorAll("#verdict .steps button").forEach((b, i) => { b.classList.toggle("on", i === checkAt); b.setAttribute("aria-selected", String(i === checkAt)); });
  $("check-view").innerHTML = `<div class="check ${c.passed ? "ok" : "no"}">
      <div class="check-head"><span class="muted">Check ${checkAt + 1} of ${cs.length}</span>${chip(c.passed ? "ok" : "no", c.passed ? "met" : "not met")}</div>
      <h4>${esc(c.name)}</h4><p>${esc(c.detail)}</p>
      ${c.context ? `<div class="ctx"><b>Context</b>${esc(c.context)}</div>` : ""}
      <div class="check-nav"><button type="button" data-step="-1" ${checkAt === 0 ? "disabled" : ""}>← Previous</button><button type="button" data-step="1" ${checkAt === cs.length - 1 ? "disabled" : ""}>Next →</button></div></div>`;
  glossify($("check-view"));
}

$("verdict").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-check], button[data-step]");
  if (!b || !S.report) return;
  const n = S.report.verdict.checks.length;
  checkAt = b.dataset.check != null ? Number(b.dataset.check) : Math.min(n - 1, Math.max(0, checkAt + Number(b.dataset.step)));
  showCheck(S.report);
});

function calc(d) {
  const s = d.sizing;
  $("calc-out").innerHTML = `${s.error ? `<div class="note bad"><b>Note</b>${esc(s.error)}</div>` : ""}
    <div class="kv"><div class="big"><div class="k">Shares at your risk limit</div><div class="v">${num(s.quantity, 0)}</div>
        <div class="n">${inr(s.risk_amount)} at risk, of ${inr(s.risk_budget)} allowed (${s.risk_pct}% of ${inr(s.capital, 0)})</div></div>
      <div><div class="k">Entry</div><div class="v">${inr(s.entry)}</div><div class="n">${esc(s.entry_basis)}</div></div>
      <div><div class="k">Stop-loss</div><div class="v">${inr(s.stop)}</div><div class="n">${s.stop_pct == null ? "" : s.stop_pct + "% below entry"}</div></div>
      <div><div class="k">Loss per share</div><div class="v">${inr(s.risk_per_share)}</div><div class="n">if the stop is hit</div></div>
      <div><div class="k">Money invested</div><div class="v">${inr(s.position_value, 0)}</div><div class="n">${s.position_pct}% of capital</div></div></div>
    <p class="hint" style="margin-top:10px">Stop basis: ${esc(s.stop_basis)}. Shares are rounded down, so the loss never exceeds your limit${s.capped_by_capital ? "; here the size is limited by your capital" : ""}.
      A gap on news can jump past a stop, so the real loss can be larger.</p>`;
  glossify($("calc"));
}

function agreeCard(d) {
  const a = d.verdict.agreement, cls = { agree: "good", conflict: "bad" }[a.state] || "plain";
  $("agree").innerHTML = `<h3>Chart versus business</h3><div class="note ${cls}"><b>${esc(a.state)}</b>${esc(a.text)}</div>
    <div class="src">Chart trend: ${esc(d.technical.trend.direction)} · Business read: ${esc(d.fundamental.verdict || "not available")}. The business side can lower the label, never raise it.</div>`;
  glossify($("agree"));
}

function pane(d) {
  const el = $("pane");
  levelCharts.forEach((c) => c.remove());
  levelCharts = [];
  el.innerHTML = ({ overview, levels, business, risks, patterns: patternStats, sources })[S.tab](d);
  glossify(el);
  if (S.tab === "levels") drawLevelCharts(d);
}

function overview(d) {
  const t = d.technical, v = d.verdict;
  return `<h4>The rule behind the label</h4>
    <div class="scroll"><table><thead><tr><th>Condition</th><th>Met?</th><th>What the numbers say</th></tr></thead><tbody>
      ${v.checks.length ? v.checks.map((c) => `<tr><td>${esc(c.name)}</td><td>${chip(c.passed ? "ok" : "no", c.passed ? "yes" : "no")}</td><td>${esc(c.detail)}${c.context ? `<div class="ctx"><b>Context</b>${esc(c.context)}</div>` : ""}</td></tr>`).join("")
        : `<tr><td colspan="3" class="missing">${esc(v.reasons[0] || "")}</td></tr>`}</tbody></table></div>
    <div class="src">“Conditions met” needs every condition. A downtrend or a serious business concern gives “Rule excludes”. Anything else is “Partly met”. Chart patterns are not part of the rule.</div>
    <h4>What the chart is doing</h4>
    <ul class="plain">${t.text.map((x) => `<li>${esc(x)}</li>`).join("")}<li>${esc(t.style_text)}</li></ul>
    <div class="src">Source: ${esc(d.price.source)} · as of ${esc(d.as_of)} · ${d.bars} daily bars</div>`;
}

function levels(d) {
  const t = d.technical;
  const lv = (rows, kind) => rows.length ? rows.map((l) => `<tr><td>${kind}</td><td class="num">${inr(l.price)}</td><td class="num">${l.distance_pct}%</td>
      <td class="num">${l.touches}</td><td>${esc(l.dates.join(", "))}</td></tr>`).join("") : `<tr><td>${kind}</td><td colspan="4" class="missing">none found in ${d.style.key === "swing" ? "the last year" : "the last 2 years"} of swings</td></tr>`;
  const pats = t.patterns.length ? t.patterns.map((p) => `<tr><td><b>${esc(p.name)}</b><div class="src">${esc(p.note)}</div></td><td>${esc(p.direction)}</td>
      <td>${esc(p.status)}${p.confirm_date ? `<div class="src">${esc(p.confirm_date)}</div>` : ""}</td><td class="num">${p.score.toFixed(2)}</td>
      <td class="num">${p.target == null ? "n/a" : inr(p.target)}</td><td class="num">${p.invalidation == null ? "n/a" : inr(p.invalidation)}</td>
      <td class="no-gloss">${p.points.map((q) => `${esc(q.role)}: ${inr(q.price)} on ${esc(q.date)}`).join("<br>")}</td></tr>`).join("")
    : `<tr><td colspan="7" class="missing">No pattern detected on the current chart.</td></tr>`;
  const fib = t.fib ? `<p>${fibText(t.fib, t.trend.close)}</p><div class="mini-chart" id="fib-chart"></div>
      <div class="src">Fibonacci levels are fixed fractions of the swing, drawn as lines. They are a common reference, not a forecast, and are not part of the rule.</div>`
    : `<p>${missing("too little history for a swing")}</p>`;
  return `<h4>Support and resistance</h4>
    <div class="scroll"><table><thead><tr><th>Type</th><th class="num">Price</th><th class="num">Distance</th><th class="num">Touches</th><th>Swing dates used</th></tr></thead>
      <tbody>${lv(t.levels.resistances.slice().reverse(), "Resistance")}${lv(t.levels.supports, "Support")}</tbody></table></div>
    <h4>Patterns detected</h4>
    <div class="scroll"><table><thead><tr><th>Pattern</th><th>Bias</th><th>Status</th><th class="num">Fit score</th><th class="num">Measured target</th><th class="num">Fails at</th><th>Exact bars used</th></tr></thead>
      <tbody>${pats}</tbody></table></div>
    <div class="src">The fit score (0 to 1) says how closely the shape matches its definition. It is not a chance of profit. A measured target is a textbook projection, not a forecast.</div>
    <h4>Fibonacci retracements</h4>${fib}
    <h4>Momentum and daily range</h4>${momentumHtml(d)}
    <div class="src">Source: ${esc(d.price.source)} · as of ${esc(d.as_of)}</div>`;
}

/* ---- Charts in the Levels section ---- */
let levelCharts = [];
const fmtDate = (s) => new Date(s + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });

function fibText(f, close) {
  const move = f.direction === "up"
    ? `the rise from ${inr(f.low)} on ${fmtDate(f.low_date)} to ${inr(f.high)} on ${fmtDate(f.high_date)}`
    : `the fall from ${inr(f.high)} on ${fmtDate(f.high_date)} to ${inr(f.low)} on ${fmtDate(f.low_date)}`;
  const lv = f.levels.map((l) => ({ ...l, pct: (l.ratio * 100).toFixed(1) + "%" })).sort((a, b) => a.price - b.price);
  const below = lv.filter((l) => l.price <= close).pop(), above = lv.find((l) => l.price > close);
  const where = below && above ? `between the ${below.pct} (${inr(below.price)}) and ${above.pct} (${inr(above.price)}) levels`
    : below ? `above every level; the nearest is ${below.pct} at ${inr(below.price)}` : `below every level; the nearest is ${above.pct} at ${inr(above.price)}`;
  return `Levels for ${move}. Today's close of ${inr(close)} is ${where}.`;
}

function momentumHtml(d) {
  const t = d.technical, m = t.momentum, r = m.rsi, close = t.trend.close;
  const rsiRead = r >= 70 ? "above 70: over the last 14 sessions, gains have been much larger than losses"
    : r <= 30 ? "below 30: over the last 14 sessions, losses have been much larger than gains" : "between 30 and 70: neither gains nor losses have dominated the last 14 sessions";
  const macdRead = m.macd >= m.macd_signal ? "above its signal line: MACD has risen above its own 9-day average"
    : "below its signal line: MACD has fallen below its own 9-day average";
  return `<div class="mom"><div class="mom-head"><b>RSI(14)</b> ${num(r, 1)} · ${rsiRead}.</div><div class="mini-chart short" id="rsi-chart"></div></div>
    <div class="mom"><div class="mom-head"><b>MACD(12,26,9)</b> ${num(m.macd, 2)}, signal ${num(m.macd_signal, 2)} · ${macdRead}.</div>
      <div class="legend"><span><i style="background:#facc15"></i>MACD</span><span><i style="background:#f4f4f2"></i>signal</span><span><i style="background:#16c47f"></i>difference</span></div>
      <div class="mini-chart short" id="macd-chart"></div></div>
    <div class="mom"><div class="mom-head"><b>ATR(14)</b> ${inr(t.atr)} · a normal day's range is ${num((t.atr / close) * 100, 1)}% of the price. The rule's stop and stretch checks are measured in ATRs.</div>
      <div class="mini-chart short" id="atr-chart"></div></div>
    <div class="src">Last year of daily values. These describe what price has done; they are not part of the rule and do not predict a move.</div>`;
}

function miniChart(el, height) {
  if (!el || !window.LightweightCharts) return null;
  el.innerHTML = "";
  const c = LightweightCharts.createChart(el, { autoSize: true, layout: { background: { color: "transparent" }, textColor: "#8b8b90", fontFamily: "Inter, sans-serif" },
    grid: { vertLines: { color: "rgba(255,255,255,.03)" }, horzLines: { color: "rgba(255,255,255,.05)" } }, rightPriceScale: { borderColor: "rgba(255,255,255,.08)" },
    timeScale: { borderColor: "rgba(255,255,255,.08)" }, crosshair: { mode: LightweightCharts.CrosshairMode.Normal }, handleScroll: false, handleScale: false });
  levelCharts.push(c);
  return c;
}

function drawLevelCharts(d) {
  const t = d.technical, m = d.chart.momentum, f = t.fib;
  const plain = { priceLineVisible: false, lastValueVisible: true, crosshairMarkerVisible: false };
  if (f) {
    const c = miniChart($("fib-chart"));
    if (c) {
      const first = [f.low_date, f.high_date].sort()[0], i = Math.max(0, d.chart.candles.findIndex((x) => x.time >= first) - 15);
      const bars = d.chart.candles.slice(i);
      const s = c.addCandlestickSeries({ upColor: "#16c47f", downColor: "#ef4444", borderVisible: false, wickUpColor: "#16c47f", wickDownColor: "#ef4444", priceLineVisible: false });
      s.setData(bars);
      /* One label per line, on the line itself (ratio and price), so the right axis keeps only the price scale and
         today's close. Swing high and low are solid; the retracement levels dashed, from light to strong yellow. */
      const line = (price, title, color, style, width = 1) =>
        s.createPriceLine({ price, color, lineWidth: width, lineStyle: style, axisLabelVisible: false, title, lineVisible: true });
      line(f.high, `swing high ${num(f.high, 2)}`, "rgba(244,244,242,.55)", 0);
      line(f.low, `swing low ${num(f.low, 2)}`, "rgba(244,244,242,.55)", 0);
      const shade = { 0.236: ".45", 0.382: ".6", 0.5: ".75", 0.618: ".9", 0.786: ".6" };
      f.levels.forEach((l) => line(l.price, `${(l.ratio * 100).toFixed(1)}%  ${num(l.price, 2)}`, `rgba(250,204,21,${shade[l.ratio] || ".7"})`, 2));
      s.priceScale().applyOptions({ scaleMargins: { top: 0.06, bottom: 0.06 } });
      s.setMarkers([{ time: f.high_date, position: "aboveBar", color: "#f4f4f2", shape: "circle", size: 0.6 },
        { time: f.low_date, position: "belowBar", color: "#f4f4f2", shape: "circle", size: 0.6 }].sort((a, b) => (a.time < b.time ? -1 : 1)));
      // Labels at the left end of each line, placed from the chart's own price scale and kept in place on resize.
      const el = $("fib-chart"), marks = [
        { price: f.high, text: `swing high ${inr(f.high)}`, cls: "edge" }, { price: f.low, text: `swing low ${inr(f.low)}`, cls: "edge" },
        ...f.levels.map((l) => ({ price: l.price, text: `${(l.ratio * 100).toFixed(1)}%  ${inr(l.price)}`, cls: "" }))];
      const place = () => {
        el.querySelectorAll(".fib-label").forEach((n) => n.remove());
        marks.forEach((m) => {
          const y = s.priceToCoordinate(m.price);
          if (y == null) return;
          const n = document.createElement("span");
          n.className = `fib-label ${m.cls}`; n.textContent = m.text; n.style.top = `${y}px`;
          el.appendChild(n);
        });
      };
      requestAnimationFrame(place);
      new ResizeObserver(() => requestAnimationFrame(place)).observe(el);
      c.timeScale().fitContent();
    }
  }
  if (!m) return;
  const rc = miniChart($("rsi-chart"));
  if (rc) {
    const s = rc.addLineSeries({ color: "#facc15", lineWidth: 2, ...plain });
    s.setData(m.rsi);
    [[70, "70"], [30, "30"]].forEach(([p, title]) => s.createPriceLine({ price: p, color: "rgba(244,244,242,.35)", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title }));
    s.applyOptions({ autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }) });
    rc.timeScale().fitContent();
  }
  const mc = miniChart($("macd-chart"));
  if (mc) {
    mc.addHistogramSeries({ priceLineVisible: false, lastValueVisible: false })
      .setData(m.hist.map((x) => ({ ...x, color: x.value >= 0 ? "rgba(22,196,127,.5)" : "rgba(239,68,68,.5)" })));
    mc.addLineSeries({ color: "#facc15", lineWidth: 2, ...plain }).setData(m.macd);
    mc.addLineSeries({ color: "#f4f4f2", lineWidth: 1, ...plain }).setData(m.signal);
    mc.timeScale().fitContent();
  }
  const ac = miniChart($("atr-chart"));
  if (ac) {
    ac.addLineSeries({ color: "#8b8b90", lineWidth: 2, ...plain, priceFormat: { type: "price", precision: 2, minMove: 0.01 } }).setData(m.atr);
    ac.timeScale().fitContent();
  }
}

function quarterText(q) {
  if (!q.available) return missing(q.missing_reason);
  const vs = q.basis === "year" ? "the same quarter a year earlier" : `the quarter before (${esc(q.compared_with)}; the year-ago quarter is missing from the source)`;
  const move = (x) => `${x >= 0 ? "up" : "down"} ${Math.abs(x)}%`;
  return `${esc(q.quarter)}: sales ${move(q.sales_growth_pct)} on ${vs}${q.profit_growth_pct == null ? "" : `, profit ${move(q.profit_growth_pct)}`}.`;
}

function business(d) {
  const f = d.fundamental;
  if (!f.available) return `<p>${missing(f.missing_reason)}</p><p>The label is capped at Watch when the business check cannot run.</p>${src(f)}`;
  const cls = { constructive: "good", neutral: "plain", cautious: "bad" }[f.verdict];
  const li = (xs, empty) => xs.length ? `<ul class="plain">${xs.map((x) => `<li><b>${esc(x.title)}.</b> ${esc(x.detail)}</li>`).join("")}</ul>` : `<p class="missing">${empty}</p>`;
  const tbl = f.table, val = f.valuation, p = f.peers, q = f.quarter;
  const peers = p.available ? `<div class="scroll"><table><thead><tr><th>Peer (${esc(p.sector)})</th><th class="num">P/E</th><th class="num">Return on equity %</th><th class="num">Debt to equity</th></tr></thead><tbody>
      ${p.rows.map((r) => `<tr><td>${esc(r.symbol)}</td><td class="num">${num(r.pe, 1)}</td><td class="num">${num(r.roe_pct, 1)}</td><td class="num">${num(r.debt_to_equity, 2)}</td></tr>`).join("")}
      <tr><td><b>Peer median</b></td><td class="num"><b>${num(p.median_pe, 1)}</b></td><td class="num"><b>${num(p.median_roe_pct, 1)}</b></td><td></td></tr>
      <tr><td><b>${esc(d.symbol)}</b></td><td class="num"><b>${val.pe == null ? "n/a" : num(val.pe, 1)}</b></td><td></td><td></td></tr></tbody></table></div>${src(p)}` : `<p>${missing(p.missing_reason)}</p>`;
  return `<div class="note ${cls}"><b>Business read</b>${esc(f.text)}</div>
    ${(f.notes || []).map((n) => `<p class="src">${esc(n)}</p>`).join("")}
    <div class="two"><div><h4>Strengths</h4>${li(f.pros, "No strength met the thresholds.")}</div>
      <div><h4>Weaknesses</h4>${li(f.cons, "No weakness was flagged by the checks that ran.")}</div></div>
    <h4>Compared with its own history</h4>
    <div class="scroll"><table><thead><tr><th>Figure</th>${tbl.periods.map((x) => `<th class="num">${esc(x)}</th>`).join("")}</tr></thead><tbody>
      ${tbl.rows.map((r) => `<tr><td>${esc(r.metric)}</td>${r.values.map((x) => `<td class="num">${x == null ? '<span class="missing">missing</span>' : num(x, 2)}</td>`).join("")}</tr>`).join("")}
    </tbody></table></div>
    <div class="src">${esc(f.history_note)} “missing” means the source did not return that figure. Source: ${esc(f.source)} · latest year ends ${esc(f.as_of)}</div>
    <h4>Latest quarter</h4>
    <p>${quarterText(q)}</p>${q.stale_note ? `<p class="missing">${esc(q.stale_note)}</p>` : ""}
    <h4>Valuation and peers</h4>
    <p>P/E: ${val.pe == null ? missing(val.missing_reason) : "<b>" + num(val.pe, 1) + "</b>"} · Market value: ${val.market_cap_cr == null ? "n/a" : inr(val.market_cap_cr, 0) + " cr"}</p>
    ${peers}`;
}

function risks(d) {
  const f = d.fundamental, x = d.extras, v = d.verdict, cs = f.concerns || [];
  const dl = x.delivery, bd = x.bulk_deals, er = x.earnings;
  return `<div class="note bad"><b>Price that invalidates the view</b>${esc(v.invalidation.text)} If that happens the reason for the trade is gone. Exit; do not widen the stop.</div>
    <h4>Concerns, most serious first</h4>
    ${cs.length ? `<div class="scroll"><table><thead><tr><th>Severity</th><th>Concern</th><th>Figure behind it</th><th>Period</th></tr></thead><tbody>
      ${cs.map((c) => `<tr><td>${chip(c.severity, c.severity === "info" ? "not checked" : c.severity)}</td><td>${esc(c.title)}</td><td>${esc(c.detail)}</td><td>${esc(c.period || "")}</td></tr>`).join("")}
    </tbody></table></div>` : `<p>${missing(f.missing_reason || "the business check did not run")}</p>`}
    <h4>Events and market activity</h4>
    <ul class="plain">
      <li><b>Next results:</b> ${er.available ? `${esc(er.date)}, about ${er.trading_days_away} trading days away. Prices often gap on results.${src(er)}` : missing(er.missing_reason)}</li>
      <li><b>Delivery:</b> ${dl.available ? `${dl.latest.delivery_pct}% of traded shares were taken for delivery on ${esc(dl.latest.date)}; ${dl.rows.length}-session average ${dl.average_pct}%.${src(dl)}` : missing(dl.missing_reason)}</li>
      <li><b>Bulk deals:</b> ${bd.available ? (bd.deals.length ? bd.deals.map((b) => `${esc(b.client)} ${esc(b.side)} ${num(b.quantity, 0)} shares at ${inr(b.price)} on ${esc(b.date)}`).join("; ") : "none for this stock in the latest file.") + src(bd) : missing(bd.missing_reason)}</li>
      <li><b>Order book depth:</b> ${missing(x.order_book.missing_reason)}</li>
      <li><b>Promoter pledge:</b> ${missing(x.pledge.missing_reason)}</li>
      <li><b>Corporate announcements:</b> ${missing(x.announcements.missing_reason)}</li>
    </ul>`;
}

function patternStats(d) {
  const s = d.pattern_stats;
  if (!s || s.available === false) return `<p>${missing(s && s.missing_reason)}</p>`;
  const syn = s.synthetic || {}, hist = (s.historical || {})[d.style.key] || {};
  return `<p>${esc(s.headline)}</p>
    <div class="scroll"><table><thead><tr><th>Pattern</th><th class="num">Found in textbook examples</th><th class="num">Seen in random charts</th>
      <th class="num">Real signals</th><th class="num">Reached target first</th><th class="num">Random-entry baseline</th><th class="num">Hit stop first</th></tr></thead><tbody>
      ${Object.keys(syn).map((n) => { const a = syn[n], h = hist[n];
        return `<tr><td>${esc(n)}</td><td class="num">${pct(a.hit_rate, 0)}</td><td class="num">${pct(a.false_positive_rate, 1)}</td>
          ${h ? `<td class="num">${h.signals}${h.small_sample ? "*" : ""}</td><td class="num">${pct(h.reached_target_first, 0)}</td><td class="num">${pct(h.baseline_target_first, 0)}</td><td class="num">${pct(h.hit_invalidation_first, 0)}</td>`
            : `<td class="num">0</td><td colspan="3" class="missing">no confirmed signal in the test period</td>`}</tr>`; }).join("")}
    </tbody></table></div>
    <div class="src">Columns 2 and 3: ${esc(s.synthetic_note)}<br>Columns 4 to 7 (${esc(d.style.name)} settings): ${esc(s.historical_note)}<br>* fewer than 30 signals, too few to trust.
      Generated ${esc(s.generated)} from ${esc(s.source)}.</div>`;
}

function sources(d) {
  return `<div class="scroll"><table><thead><tr><th>What</th><th>Source</th><th>As of</th><th>Note</th></tr></thead><tbody>
    ${d.sources.map((s) => `<tr><td>${esc(s.item)}</td><td>${s.source === "not available" ? '<span class="missing">not available</span>' : esc(s.source)}</td><td>${esc(s.as_of || "")}</td><td>${esc(s.note || "")}</td></tr>`).join("")}
  </tbody></table></div>`;
}

/* The chart shows the whole history the source returned (about five years). Daily opens on the recent months the
   style looks at; Weekly opens on about three years. Drag the chart or the time axis to see more. Pattern markers are
   found on daily bars, so they only appear on the daily chart. */
let chartFrame = "daily";
function drawChart(d) {
  const el = $("chart"), t = d.technical, weekly = chartFrame === "weekly", s = weekly ? d.chart.weekly : d.chart;
  const unit = weekly ? "week" : "day";
  if (chart) { chart.remove(); chart = null; }
  document.querySelectorAll("#frame-seg button").forEach((b) => b.classList.toggle("on", b.dataset.frame === chartFrame));
  $("legend").innerHTML = `<span><i style="background:#facc15"></i>${s.fast_n}-${unit} average</span><span><i style="background:#f4f4f2"></i>${s.slow_n}-${unit} average</span>
    <span><i style="background:#16c47f"></i>support</span><span><i style="background:#ef4444"></i>resistance</span><span><i style="background:#8b8b90"></i>stop</span>
    <span class="muted">${d.chart.years} years of history · drag to scroll${weekly ? " · patterns show on Daily" : ""}</span>`;
  if (!window.LightweightCharts) { el.innerHTML = '<p class="missing">The chart library could not be loaded (it needs an internet connection). All numbers on this page are unaffected.</p>'; return; }
  el.innerHTML = "";
  chart = LightweightCharts.createChart(el, { autoSize: true, layout: { background: { color: "transparent" }, textColor: "#8b8b90", fontFamily: "Inter, sans-serif" },
    grid: { vertLines: { color: "rgba(255,255,255,.04)" }, horzLines: { color: "rgba(255,255,255,.05)" } }, rightPriceScale: { borderColor: "rgba(255,255,255,.08)" }, timeScale: { borderColor: "rgba(255,255,255,.08)" },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal }, ...CHART_POINTER });
  const candles = chart.addCandlestickSeries({ upColor: "#16c47f", downColor: "#ef4444", borderVisible: false, wickUpColor: "#16c47f", wickDownColor: "#ef4444" });
  candles.setData(s.candles);
  const vol = chart.addHistogramSeries({ priceFormat: { type: "volume" }, priceScaleId: "vol", lastValueVisible: false, priceLineVisible: false });
  chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.84, bottom: 0 } });
  vol.setData(s.volume.map((v, i) => ({ time: v.time, value: v.value, color: s.candles[i].close >= s.candles[i].open ? "rgba(22,196,127,.35)" : "rgba(239,68,68,.35)" })));
  chart.addLineSeries({ color: "#facc15", lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }).setData(s.fast);
  chart.addLineSeries({ color: "#f4f4f2", lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false }).setData(s.slow);
  const line = (price, color, title, style) => candles.createPriceLine({ price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: true, title });
  t.levels.supports.slice(0, 2).forEach((l) => line(l.price, "#16c47f", "support", 2));
  t.levels.resistances.slice(0, 2).forEach((l) => line(l.price, "#ef4444", "resistance", 2));
  line(d.sizing.stop, "#8b8b90", "stop", 0);
  if (!weekly) candles.setMarkers(patternMarkers(t.patterns, s.candles, s.first_date));
  const n = s.candles.length, show = weekly ? 156 : d.style.key === "swing" ? 130 : 260;
  chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, n - show), to: n + (weekly ? 4 : 14) });
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("#frame-seg button");
  if (!b || b.dataset.frame === chartFrame) return;
  chartFrame = b.dataset.frame;
  if (S.report) drawChart(S.report);
});

/* Pattern markers: one name per pattern at its last point, other points as plain dots. Bullish patterns sit below the
   bars and the rest above, and a name is dropped when another one on the same side is within LABEL_GAP bars, so labels
   never pile up. Each point's role (first peak, neckline...) stays in the Levels and patterns section. */
const LABEL_GAP = 12;
function patternMarkers(patterns, candles, first) {
  const index = new Map(candles.map((c, i) => [c.time, i])), marks = [], labelled = { aboveBar: [], belowBar: [] };
  const shown = patterns.filter((p) => !p.name.includes("trend line")).map((p) => ({ p, pts: p.points.filter((q) => q.date >= first && index.has(q.date)) }))
    .filter((x) => x.pts.length).sort((a, b) => index.get(b.pts[b.pts.length - 1].date) - index.get(a.pts[a.pts.length - 1].date));
  shown.forEach(({ p, pts }) => {
    const position = p.direction === "bullish" ? "belowBar" : "aboveBar";
    const color = p.direction === "bearish" ? "#ef4444" : p.direction === "bullish" ? "#16c47f" : "#facc15";
    const at = index.get(pts[pts.length - 1].date), free = labelled[position].every((i) => Math.abs(i - at) >= LABEL_GAP);
    if (free) labelled[position].push(at);
    pts.forEach((q, i) => marks.push({ time: q.date, position, color, shape: "circle", size: 0.6, text: free && i === pts.length - 1 ? p.name : "" }));
  });
  return marks.sort((a, b) => index.get(a.time) - index.get(b.time));
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
    chatLine("sys", ready ? "Ask what a term means, why a stock got its label, what a news story is about, or how position sizing works."
      : "Ask Belfort needs your own AI key. Open Settings in the sidebar, choose a provider and paste a key. Everything else in Belfort works without one.");
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
  const wait = chatLine("model", "Thinking…");
  try {
    const ctx = chatContext();
    const r = await api("/api/chat", { method: "POST", headers: Object.assign({ "Content-Type": "application/json" }, aiHeaders()),
      body: JSON.stringify({ question: q, history: S.chat.slice(-6), context: ctx.text, mode: ctx.mode }) });
    wait.textContent = r.answer; S.chat.push({ role: "user", text: q }, { role: "model", text: r.answer });
  } catch (err) { wait.className = "msg sys"; wait.textContent = err.message; }
  $("chat-log").scrollTop = 1e9;
});

/* ---------- dictionary drawer ---------- */
$("dict-btn").addEventListener("click", () => { $("dict").hidden = false; renderDict(""); $("dict-q").value = ""; $("dict-q").focus(); });
$("dict-x").addEventListener("click", () => { $("dict").hidden = true; });
$("dict-q").addEventListener("input", () => renderDict($("dict-q").value));
document.addEventListener("keydown", (e) => { if (e.key === "Escape") { $("dict").hidden = true; hideTip(); } });

/* ---------- start ---------- */
(async function init() {
  $("capital").value = localStorage.getItem("capital") || 100000;
  $("risk").value = localStorage.getItem("risk") || 1;
  try {
    S.cfg = await (await fetch("/api/config")).json();
    $("disclaimer").textContent = S.cfg.disclaimer;
    buildGloss(S.cfg.glossary);
    glossify(document.querySelector(".intro")); glossify(document.querySelector("#calc .hint"));
  } catch (e) { /* the page still works without the dictionary */ }
  renderFiles(); setCrumb();
  loadScreens();
  const start = location.hash.slice(1);
  if (["learn", "practice", "news"].includes(start)) go(start);
})();
