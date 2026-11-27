/* Startup loader (T46). Used by splash.html (the Windows app shows it before the server is up)
   and as an overlay in index.html until the first data load finishes (minimum 1.2 s, then a fade).
   Events: `belfort:app-ready` (fired by app.js) hides the overlay; `belfort:splash-done` fires when it starts to fade. */
(function () {
  "use strict";
  // [open, close, high, low] in a 280 x 150 box, y grows downward. Close above open = green.
  const CANDLES = [[104, 92, 88, 108], [92, 78, 74, 96], [78, 86, 72, 90], [86, 66, 62, 90], [66, 72, 58, 76], [72, 50, 46, 76], [50, 38, 32, 54]];
  const MIN_OVERLAY_MS = 1200, SAFETY_MS = 9000;
  const reduced = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);

  function markup(mascotSrc) {
    const step = 36, x0 = 22;
    const candles = CANDLES.map((c, i) => {
      const [o, cl, hi, lo] = c, up = cl < o, cx = x0 + i * step;
      return `<g class="${up ? "up" : "down"}" style="--i:${i}"><line class="wick" x1="${cx}" x2="${cx}" y1="${hi}" y2="${lo}"/>` +
        `<rect class="body" x="${cx - 8}" y="${Math.min(o, cl)}" width="16" height="${Math.abs(o - cl)}" rx="1.5"/></g>`;
    }).join("");
    return `<div class="sp-stage"><svg class="sp-candles" viewBox="0 0 280 150" aria-hidden="true">${candles}` +
      `<line class="level" x1="6" x2="274" y1="116" y2="116"/></svg>` +
      `<img class="sp-mascot" src="${mascotSrc}" alt="" width="200" height="200"></div><div class="sp-word">Belfort</div>`;
  }

  function mount(el, mascotSrc) {
    el.classList.add("splash");
    el.setAttribute("role", "status");
    el.setAttribute("aria-busy", "true");
    el.setAttribute("aria-label", typeof T === "function" ? T("splash.loading", null, "Loading Belfort") : "Loading Belfort");
    el.innerHTML = markup(mascotSrc || "img/mascot/mascot-suit.gif");
    return el;
  }

  window.BelfortSplash = { reduced, mount, minMs: reduced ? 0 : 2300 };

  const el = document.getElementById("splash");
  if (!el) return;
  if (el.dataset.page === "desktop") { // splash.html: just play, the launcher navigates away when ready
    document.documentElement.classList.add("splash-page");
    mount(el);
    return;
  }

  // In-app overlay.
  if (/[?&]splash=0\b/.test(location.search)) { // the desktop app already showed the loader
    el.classList.add("gone");
    document.addEventListener("DOMContentLoaded", () => document.dispatchEvent(new CustomEvent("belfort:splash-done")));
    return;
  }
  el.classList.add("quick");
  mount(el);
  const t0 = performance.now();
  let hidden = false;
  function hide() {
    if (hidden) return;
    hidden = true;
    const wait = Math.max(0, (reduced ? 0 : MIN_OVERLAY_MS) - (performance.now() - t0));
    setTimeout(() => {
      el.setAttribute("aria-busy", "false");
      el.classList.add("fade");
      document.dispatchEvent(new CustomEvent("belfort:splash-done"));
      setTimeout(() => el.classList.add("gone"), 400);
    }, wait);
  }
  document.addEventListener("belfort:app-ready", hide);
  setTimeout(hide, SAFETY_MS); // never trap the user behind the loader
})();
