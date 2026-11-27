"use strict";
(function () {
  const $ = (id) => document.getElementById(id);
  const N = window.BelfortNative;
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // hand-off from the system splash: the candles draw in, then the start screen fades up
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  setTimeout(() => { $("loader").classList.add("done"); $("main").hidden = false; }, reduce ? 300 : 1700);

  const msg = decodeURIComponent((location.hash || "").slice(1));
  if (msg) $("msg").textContent = msg;
  if (N && N.server()) $("server").value = N.server();

  $("connect").addEventListener("submit", (e) => {
    e.preventDefault();
    let u = $("server").value.trim();
    if (!/^https?:\/\//.test(u)) u = "http://" + u;
    if (!/:\d+/.test(u.replace(/^https?:\/\//, ""))) u += ":8766";
    if (N) N.connect(u); else location.href = u;
  });

  if (window.TipCheckOffline && window.TipCheckOffline.ready) {
    $("offline").hidden = false;
    $("check").addEventListener("click", () => {
      const r = window.TipCheckOffline.check($("tip").value);
      if (!r) return;
      if (N) N.haptic(r.flags ? "reject" : "confirm");
      $("out").innerHTML = `<div class="flags">
        <div><span class="count ${r.flags ? "bad" : "ok"}">${r.flags}</span> ${r.flags === 1 ? "red flag" : "red flags"} in the text</div>
        ${r.findings.map((f) => `<div class="flag ${f.status === "flag" ? "red" : f.status === "clear" ? "green" : ""}">
          <b>${esc(f.title)}</b><p>${esc(f.detail)}</p>
          ${f.evidence.length ? `<div class="quotes">${f.evidence.map((q) => `<q>${esc(q)}</q>`).join("")}</div>` : ""}</div>`).join("")}
        <p class="small">Belfort reports red flags found and not found. It cannot tell you whether a trade will work.</p></div>`;
    });
  }
})();
