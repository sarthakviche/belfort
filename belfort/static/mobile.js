"use strict";
/* Phones (T48): a bottom tab bar instead of the sidebar, and the bridge to the Android app's native pieces.
   Its own file; app.js is not changed. On a desktop-width window nothing here is visible.
   Inside the Android app, window.BelfortNative exists (android/src/.../Bridge.java) and gives:
     haptic(kind)            "tap" | "confirm" | "reject"
     share(text, dataUrl)    the Android share sheet, with an optional PNG
     remindDaily(hour)       a daily streak reminder notification ("" to cancel with hour -1)
   Other code calls window.belfortHaptic(kind); it does nothing outside the app. */
(function () {
  const N = window.BelfortNative;
  const inApp = !!N;
  document.documentElement.classList.toggle("in-app", inApp);
  window.belfortHaptic = (kind) => { try { if (N) N.haptic(kind || "tap"); } catch (e) { /* no haptics */ } };

  /* The share sheet: pages call navigator.share as usual; in the app it goes to Android's own sheet. */
  if (inApp) {
    navigator.canShare = () => true;
    navigator.share = (data) => new Promise((ok, fail) => {
      const text = [data.text, data.url].filter(Boolean).join("\n");
      const file = (data.files || [])[0];
      if (!file) { N.share(text, ""); ok(); return; }
      const fr = new FileReader();
      fr.onload = () => { N.share(text, String(fr.result)); ok(); };
      fr.onerror = () => fail(fr.error);
      fr.readAsDataURL(file);
    });
  }

  /* Bottom tab bar, built from the sidebar's own buttons so every view keeps working the same way. */
  const ORDER = ["learn", "tipcheck", "practice", "home", "news"];
  const LABEL = { home: "Research", learn: "Learn", tipcheck: "Tip Check", practice: "Practice", news: "News" };
  const ICON = {
    home: '<path d="M4 19V9m5 10V5m5 14v-7m5 7V8"/>',
    learn: '<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M7 9v5c0 1.5 2.5 3 5 3s5-1.5 5-3V9"/>',
    tipcheck: '<path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6l8-3z"/><path d="M12 8v5m0 3v.5"/>',
    practice: '<path d="M4 18l5-6 4 3 7-9"/><path d="M15 6h5v5"/>',
    news: '<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M8 9h8M8 13h8M8 17h5"/>',
  };
  function build() {
    const source = [...document.querySelectorAll(".index .ix[data-view]")];
    if (!source.length || document.querySelector(".tabbar")) return;
    const views = ORDER.filter((v) => source.some((b) => b.dataset.view === v));
    const bar = document.createElement("nav");
    bar.className = "tabbar"; bar.setAttribute("aria-label", "Main");
    bar.innerHTML = views.map((v) => `<button type="button" data-tab="${v}" aria-label="${LABEL[v]}">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[v]}</svg>
      <span>${LABEL[v]}</span></button>`).join("");
    bar.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-tab]"); if (!b) return;
      window.belfortHaptic("tap");
      const original = source.find((s) => s.dataset.view === b.dataset.tab);
      if (original) original.click();
    });
    document.body.append(bar);
    const sync = () => {
      const on = document.querySelector(".index .ix.on");
      bar.querySelectorAll("button").forEach((b) => b.classList.toggle("on", !!on && b.dataset.tab === on.dataset.view));
    };
    new MutationObserver(sync).observe(document.querySelector(".index"), { subtree: true, attributes: true, attributeFilter: ["class"] });
    sync();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build); else build();

  /* Haptics on results: a Tip Check result, and right or wrong quiz answers, wherever they appear. */
  if (inApp) {
    new MutationObserver((records) => {
      for (const r of records) for (const n of r.addedNodes) {
        if (!(n instanceof Element)) continue;
        const tc = n.matches(".tc-result") ? n : n.querySelector && n.querySelector(".tc-result");
        if (tc) window.belfortHaptic(tc.querySelector(".has-flags") ? "reject" : "confirm");
        if (n.matches(".correct, .q-right") || (n.querySelector && n.querySelector(".correct, .q-right"))) window.belfortHaptic("confirm");
        if (n.matches(".wrong, .q-wrong") || (n.querySelector && n.querySelector(".wrong, .q-wrong"))) window.belfortHaptic("reject");
      }
    }).observe(document.body, { childList: true, subtree: true });
  }
})();
