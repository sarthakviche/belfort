"use strict";
/* Stock picker: type part of a company's name and pick it from a list. Nobody should need to know an NSE symbol.
   Attach by adding data-stock-picker to an <input>. Inputs added later are picked up automatically.
   - Inside a form: the visible field shows the company name, and a hidden field with the input's original name
     carries the symbol, so the form submits the symbol.
   - Every pick fires a bubbling "stock-pick" event with { symbol, name } in event.detail.
   Needs $, esc, inr and api from app.js. */
const PICKS_KEY = "belfortRecentPicks";
const PICKS_MAX = 6;
const PICKER_DELAY_MS = 120;

const StockPicker = (() => {
  let uid = 0;
  const readRecent = () => { try { return JSON.parse(localStorage.getItem(PICKS_KEY)) || []; } catch (e) { return []; } };
  function saveRecent(row) {
    try {
      const rest = readRecent().filter((r) => r.symbol !== row.symbol);
      localStorage.setItem(PICKS_KEY, JSON.stringify([{ symbol: row.symbol, name: row.name, sector: row.sector || null }, ...rest].slice(0, PICKS_MAX)));
    } catch (e) { /* recent picks are a convenience */ }
  }

  function rowHtml(r, i, active, id) {
    const meta = [esc(r.symbol), r.sector ? esc(r.sector) : "", r.last_close != null ? `${inr(r.last_close)} <i>${esc(r.as_of || "")}</i>` : ""].filter(Boolean).join(" · ");
    return `<div role="option" id="${id}-${i}" data-i="${i}" class="${i === active ? "on" : ""}" aria-selected="${i === active}"><b>${esc(r.name)}</b><span>${meta}</span></div>`;
  }

  function attach(input) {
    if (input.dataset.pickerReady) return;
    input.dataset.pickerReady = "1";
    const id = `stock-picker-${++uid}`;
    let rows = [], active = -1, timer = null, seq = 0, showingRecent = false;

    let hidden = null;
    if (input.name) {  // a form field: the form gets the symbol, the person sees the name
      hidden = document.createElement("input");
      hidden.type = "hidden"; hidden.name = input.name;
      input.removeAttribute("name");
      input.insertAdjacentElement("afterend", hidden);
    }
    let host = input.parentElement;
    if (getComputedStyle(host).position === "static") {
      const wrap = document.createElement("span");
      wrap.className = "picker";
      input.insertAdjacentElement("beforebegin", wrap);
      wrap.appendChild(input);
      if (hidden) wrap.appendChild(hidden);
      host = wrap;
    }
    const box = document.createElement("div");
    box.className = "suggest"; box.id = id; box.hidden = true; box.setAttribute("role", "listbox");
    host.appendChild(box);
    input.setAttribute("role", "combobox"); input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-controls", id); input.setAttribute("aria-expanded", "false"); input.autocomplete = "off";

    function render() {
      if (!rows.length) { box.hidden = true; input.setAttribute("aria-expanded", "false"); input.removeAttribute("aria-activedescendant"); return; }
      box.innerHTML = (showingRecent ? `<p class="suggest-head">${T("picker.recent")}</p>` : "") + rows.map((r, i) => rowHtml(r, i, active, id)).join("");
      box.hidden = false; input.setAttribute("aria-expanded", "true");
      if (active >= 0) input.setAttribute("aria-activedescendant", `${id}-${active}`); else input.removeAttribute("aria-activedescendant");
    }
    function showRecent() { rows = readRecent(); active = -1; showingRecent = true; render(); }
    function choose(r) {
      input.value = r.name || r.symbol;
      if (hidden) hidden.value = r.symbol;
      if (r.name) saveRecent(r);
      rows = []; render();
      input.dispatchEvent(new CustomEvent("stock-pick", { detail: { symbol: r.symbol, name: r.name || r.symbol }, bubbles: true }));
    }
    async function lookup(q) {
      const mine = ++seq;
      try {
        const found = (await api("/api/search?q=" + encodeURIComponent(q))).results;
        if (mine !== seq) return;  // a newer keystroke won
        rows = found; active = rows.length ? 0 : -1; showingRecent = false; render();
      } catch (e) { /* suggestions are optional */ }
    }

    input.addEventListener("input", () => {
      clearTimeout(timer);
      if (hidden) hidden.value = "";
      const q = input.value.trim();
      if (!q) { seq++; showRecent(); return; }
      timer = setTimeout(() => lookup(q), PICKER_DELAY_MS);
    });
    input.addEventListener("focus", () => { if (!input.value.trim()) showRecent(); });
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        if (!rows.length) { if (!input.value.trim()) showRecent(); return; }
        e.preventDefault();
        active = (active + (e.key === "ArrowDown" ? 1 : -1) + rows.length) % rows.length; render();
      } else if (e.key === "Enter") {
        if (!box.hidden && rows.length) { e.preventDefault(); choose(rows[active >= 0 ? active : 0]); }
        else if (!hidden && input.value.trim()) { e.preventDefault(); choose({ symbol: input.value.trim(), name: "" }); }
      } else if (e.key === "Escape") {
        if (!box.hidden) { e.preventDefault(); rows = []; render(); }
      }
    });
    box.addEventListener("mousedown", (e) => { const d = e.target.closest("div[data-i]"); if (d) { e.preventDefault(); choose(rows[+d.dataset.i]); } });
    input.addEventListener("blur", () => setTimeout(() => { rows = []; render(); }, 150));
    if (input.form) {
      input.form.addEventListener("submit", () => {  // typed but never picked: take the best match, else the text as typed
        if (hidden && !hidden.value && input.value.trim()) hidden.value = rows.length && !showingRecent ? rows[0].symbol : input.value.trim();
      }, true);
    }
  }

  const attachAll = (root) => (root || document).querySelectorAll("input[data-stock-picker]").forEach(attach);
  new MutationObserver(() => attachAll()).observe(document.body, { childList: true, subtree: true });
  attachAll();
  return { attach, attachAll };
})();
