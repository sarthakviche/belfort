/* Dictionary view (T45): ranked search over the glossary, browse by category, and a fallback for missing terms:
   ask the user's own assistant, or search the web in the system browser. Uses globals from app.js: $, esc, api, go, onView. */
const DX = { cat: "All", seq: 0, timer: null, cats: [] };
const dxBody = () => $("dx-body"), dxQ = () => $("dx-q");

const dxCard = (g) => `<article class="dx-card"><div class="dx-top"><h3>${esc(g.term)}</h3><span class="chip dx-chip">${esc(g.group)}</span></div><p>${esc(g.meaning)}</p></article>`;

function dxBrowse(list) {
  const cats = DX.cats.length ? DX.cats : [...new Set(list.map((g) => g.group))];
  DX.cats = cats;
  $("dx-cats").hidden = false;
  $("dx-cats").innerHTML = ["All", ...cats].map((c) => `<button type="button" data-cat="${esc(c)}" class="${c === DX.cat ? "on" : ""}">${esc(c === "All" ? T("dx.all") : c)}</button>`).join("");
  const shown = DX.cat === "All" ? list : list.filter((g) => g.group === DX.cat);
  dxBody().innerHTML = `<div class="dx-list dx-fade">${shown.map(dxCard).join("")}</div>`;
}

/* The Ask Belfort and web-search buttons, with the box the answer goes into. */
function dxAskBlock() {
  return `<div class="dx-actions"><button type="button" class="btn" id="dx-ask">${T("dx.ask")}</button><button type="button" class="btn ghost" id="dx-web">${T("dx.web")}</button></div>
    <div id="dx-ai" class="dx-ai" aria-live="polite"></div>`;
}

function dxNoMatch(term, webUrl) {
  const t = esc(term);
  dxBody().innerHTML = `<div class="dx-empty dx-fade">
    <img src="img/mascot/mascot-shrug.gif" alt="" width="140" height="140">
    <h3>${T("dx.not_found", { term: t })}</h3>
    <p>${T("dx.not_found_text")}</p>
    ${dxAskBlock()}</div>`;
  dxBody().dataset.term = term; dxBody().dataset.web = webUrl || "";
}

/* Matches that are only close spellings: the typed term is probably missing, so offer Ask Belfort under them. */
function dxCloseOnly(term, d) {
  dxBody().innerHTML = `<div class="dx-count">${T("dx.matches", { n: d.count })}</div><div class="dx-list dx-fade">${d.results.map(dxCard).join("")}</div>
    <div class="dx-close dx-fade"><p>${T("dx.not_quite", { term: esc(term) })}</p>${dxAskBlock()}</div>`;
  dxBody().dataset.term = term; dxBody().dataset.web = d.web_url || "";
}

async function dxSearch() {
  const q = dxQ().value.trim(), my = ++DX.seq;
  try {
    const d = await api("/api/glossary/search?q=" + encodeURIComponent(q) + (q ? "" : "&limit=500"));
    if (my !== DX.seq) return;
    if (!q) return dxBrowse(d.results);
    $("dx-cats").hidden = true;
    if (!d.results.length) return dxNoMatch(q, d.web_url);
    if (d.close_only) return dxCloseOnly(q, d);
    dxBody().innerHTML = `<div class="dx-count">${T("dx.matches", { n: d.count })}</div><div class="dx-list dx-fade">${d.results.map(dxCard).join("")}</div>`;
  } catch (e) { if (my === DX.seq) dxBody().innerHTML = `<p class="missing">${esc(e.message)}</p>`; }
}

async function dxAsk() {
  const term = dxBody().dataset.term, box = $("dx-ai"), btn = $("dx-ask");
  if (!aiReady()) {
    box.innerHTML = `<div class="dx-note">${T("dx.need_key", { settings: `<button type="button" class="linkish" id="dx-open-settings">${T("tool.settings")}</button>` })}</div>`;
    return;
  }
  btn.disabled = true; box.innerHTML = `<div class="dx-note">${T("dx.asking")}</div>`;
  try {
    const r = await api("/api/glossary/ask", { method: "POST", headers: Object.assign({ "Content-Type": "application/json" }, aiHeaders()), body: JSON.stringify({ term }) });
    box.innerHTML = `<div class="dx-answer dx-fade"><span class="chip dx-chip">${esc(T("dx.ai_label"))}</span><p>${esc(r.answer)}</p><div class="src">${T("dx.ai_note")}</div></div>`;
  } catch (e) {
    box.innerHTML = `<div class="dx-note err">${T("dx.web_instead", { why: esc(e.message) })}</div>`;
  } finally { btn.disabled = false; }
}

async function dxWeb() {
  const term = dxBody().dataset.term, url = dxBody().dataset.web;
  // The desktop window (pywebview) does not open new browser windows, so the app asks its own backend to.
  if (window.pywebview) {
    try { const r = await api("/api/glossary/web-search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ term }) }); if (r.opened) return; } catch (e) { /* fall through */ }
  }
  window.open(url, "_blank", "noopener,noreferrer");
}

dxQ().addEventListener("input", () => { clearTimeout(DX.timer); DX.timer = setTimeout(dxSearch, 120); });
$("dx-cats").addEventListener("click", (e) => { const b = e.target.closest("button[data-cat]"); if (b) { DX.cat = b.dataset.cat; dxSearch(); } });
dxBody().addEventListener("click", (e) => {
  if (e.target.closest("#dx-ask")) dxAsk();
  else if (e.target.closest("#dx-web")) dxWeb();
  else if (e.target.closest("#dx-open-settings")) $("settings-btn").click();
});
// "/" jumps to this search box while the Dictionary is open (elsewhere it keeps focusing the company search).
window.addEventListener("keydown", (e) => {
  if (e.key === "/" && S.view === "dictionary" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
    e.preventDefault(); e.stopImmediatePropagation(); dxQ().focus(); dxQ().select();
  }
}, true);
onView.dictionary = (opts) => { dxSearch(); if (!(opts && opts.keepLesson)) dxQ().focus(); };
/* app.js may already have opened #dictionary while this file was still loading: draw it now. */
if (S.view === "dictionary") onView.dictionary({});
