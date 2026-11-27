"use strict";
/* Languages (T50). Loaded first. The catalogues are belfort/static/i18n/<lang>.json: flat keys with dot namespaces,
   {name} placeholders, English is the source of truth and the fallback for any missing key (docs/ARCHITECTURE.md, "Languages").

   t(key, vars, fallback)   translate; T is the same function (use T inside code that has a local variable named t)
   setLanguage(lang)        switch without a reload; re-applies data-i18n markup and fires "belfort:language" on document
   data-i18n, data-i18n-html, data-i18n-placeholder, data-i18n-aria, data-i18n-title   static markup
   formatNumber, formatMoney   Indian grouping (1,00,000) with Latin digits in every language
   I18N.ready               promise: the catalogues for the saved language are loaded */
const I18N = (() => {
  const LANGS = [["en", "English"], ["hi", "हिन्दी"], ["mr", "मराठी"], ["bn", "বাংলা"], ["ta", "தமிழ்"], ["te", "తెలుగు"], ["gu", "ગુજરાતી"], ["kn", "ಕನ್ನಡ"]];
  const NAMES = Object.fromEntries(LANGS);
  const KEY = "belfort.lang";
  const cats = {};
  let lang = "en";

  const store = {
    get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } },
    set(v) { try { localStorage.setItem(KEY, v); } catch (e) { /* private mode: the choice lasts until the window closes */ } },
  };
  async function load(l) {
    if (cats[l]) return cats[l];
    try { const r = await fetch(`i18n/${l}.json`); cats[l] = r.ok ? await r.json() : {}; } catch (e) { cats[l] = {}; }
    return cats[l];
  }
  const norm = (c) => { const b = String(c || "").toLowerCase().split(/[-_]/)[0]; return NAMES[b] ? b : "en"; };

  function lookup(key) {
    const own = cats[lang] && cats[lang][key];
    return typeof own === "string" ? own : cats.en && typeof cats.en[key] === "string" ? cats.en[key] : null;
  }
  function t(key, vars, fallback) {
    let k = key;
    if (vars && vars.n === 1 && lookup(key + "_one") != null) k = key + "_one";
    let s = lookup(k);
    if (s == null) s = fallback != null ? fallback : key;
    return vars ? s.replace(/\{(\w+)\}/g, (m, n) => (vars[n] != null ? vars[n] : m)) : s;
  }

  const fmts = {};
  function formatNumber(x, o) {
    const min = (o && o.min) || 0, max = o && o.max != null ? o.max : 2, k = min + "-" + max;
    fmts[k] = fmts[k] || new Intl.NumberFormat("en-IN", { minimumFractionDigits: min, maximumFractionDigits: Math.max(min, max), numberingSystem: "latn" });
    return fmts[k].format(Number(x));
  }
  const formatMoney = (x, d = 2) => "₹" + formatNumber(x, { min: d, max: d });

  function applyStatic(root) {
    const r = root || document;
    r.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    r.querySelectorAll("[data-i18n-html]").forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
    r.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.setAttribute("placeholder", t(el.dataset.i18nPlaceholder)); });
    r.querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
    r.querySelectorAll("[data-i18n-title]").forEach((el) => { el.setAttribute("title", t(el.dataset.i18nTitle)); });
  }
  function setDocument() {
    document.documentElement.lang = lang;
    document.documentElement.dir = "ltr";   // every supported language is written left to right
    document.documentElement.dataset.lang = lang;
  }
  async function setLanguage(next, opts) {
    next = norm(next);
    await Promise.all([load("en"), load(next)]);
    lang = next; setDocument(); applyStatic();
    store.set(lang);
    if (!(opts && opts.quiet)) { try { fetch("/api/settings/language", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ language: lang }) }); } catch (e) { /* offline is fine */ } }
    document.dispatchEvent(new CustomEvent("belfort:language", { detail: { lang } }));
    return lang;
  }
  /* A row of language chips, each language in its own script. Used by the intro and Settings. */
  function chips(box, onPick) {
    const draw = () => {
      box.innerHTML = LANGS.map(([c, n]) => `<button type="button" class="lang-chip${c === lang ? " on" : ""}" data-lang="${c}" lang="${c}" aria-pressed="${c === lang}">${n}</button>`).join("");
    };
    draw();
    box.addEventListener("click", (e) => { const b = e.target.closest("button[data-lang]"); if (b) { setLanguage(b.dataset.lang); if (onPick) onPick(b.dataset.lang); } });
    document.addEventListener("belfort:language", draw);
  }

  async function init() {
    let want = store.get();
    if (!want) { try { const r = await fetch("/api/settings/language"); if (r.ok) want = (await r.json()).language; } catch (e) { /* default */ } }
    await Promise.all([load("en"), load(norm(want))]);
    lang = norm(want); setDocument(); applyStatic();
  }
  const ready = init();
  return { t, T: t, setLanguage, chips, formatNumber, formatMoney, applyStatic, ready, LANGS, get lang() { return lang; }, name: (c) => NAMES[c] || c };
})();
const t = I18N.t, T = I18N.t, formatNumber = I18N.formatNumber, formatMoney = I18N.formatMoney, setLanguage = I18N.setLanguage;
