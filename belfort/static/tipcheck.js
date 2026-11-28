"use strict";
/* Tip Check (T44): paste or screenshot a stock tip and see its red flags.
   Lives in its own file; app.js only lists the view. Uses app.js helpers: $, esc, api, go, onView, aiReady, aiHeaders. */
(function () {
  const TC = { text: "", symbol: null, last: null, busy: false };
  const MASCOT = { suit: "img/mascot/mascot-suit.gif", shrug: "img/mascot/mascot-shrug.gif" };
  const ICON = { flag: "!", clear: "✓", unknown: "?", info: "i" };
  const STATUS_WORD = { flag: "Red flag", clear: "Clear", unknown: "Not checked", info: "For context" };
  const reduceMotion = () => window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- the view ---------- */
  const view = $("tipcheck");
  view.innerHTML = `
    <div class="tc-hero">
      <div class="intro">
        <div class="eyebrow">Tip Check</div>
        <h1>Got a stock tip? <em>Check it</em> before you act.</h1>
        <p>Paste a message from WhatsApp, Telegram or Instagram, or add a screenshot. In about ten seconds Belfort shows the red flags it finds: SEBI registration, promised returns, pressure to hurry, NSE's surveillance lists and pump patterns in the price. English, Hindi and Hinglish all work.</p>
      </div>
      <img class="tc-mascot-hero" src="${MASCOT.suit}" alt="" width="132" height="132">
    </div>
    <form class="panel glass tc-form" id="tc-form">
      <label class="tc-label" for="tc-text">The tip</label>
      <textarea id="tc-text" rows="6" maxlength="10000" placeholder="Paste the message here, for example: XYZ target 2 din mein, jaldi entry lo, join our VIP group…"></textarea>
      <div class="tc-drop" id="tc-drop" hidden><img id="tc-thumb" alt="Your screenshot"><span id="tc-drop-msg"></span></div>
      <div class="tc-actions">
        <button type="submit" class="btn" id="tc-go">Check this tip</button>
        <label class="btn ghost tc-file">Add a screenshot<input type="file" id="tc-file" accept="image/png,image/jpeg,image/webp" hidden></label>
        <span class="tc-hint">You can also paste or drop a screenshot here. Screenshots are read with your own AI key; text needs no key.</span>
      </div>
    </form>
    <div id="tc-out" aria-live="polite"></div>`;

  /* ---------- the box on the Research home ---------- */
  const intro = document.querySelector("#home .intro");
  if (intro) {
    const box = document.createElement("form");
    box.className = "panel tc-home";
    box.innerHTML = `<div class="tc-home-text"><div class="eyebrow">New · Tip Check</div><b>Got a tip on WhatsApp or Telegram?</b><span>Paste it and see its red flags in ten seconds.</span></div>
      <textarea rows="2" maxlength="10000" placeholder="Paste a tip…" aria-label="Paste a stock tip"></textarea>
      <button type="submit" class="btn">Check it</button>`;
    box.addEventListener("submit", (e) => { e.preventDefault(); const t = box.querySelector("textarea").value.trim(); go("tipcheck", t ? { text: t } : {}); });
    intro.after(box);
  }

  onView.tipcheck = (opts) => {
    if (opts.text) { $("tc-text").value = opts.text; run(); }
    else if (!TC.last) $("tc-text").focus();
  };

  /* ---------- checking ---------- */
  $("tc-form").addEventListener("submit", (e) => { e.preventDefault(); TC.symbol = null; run(); });

  async function run(symbol) {
    const text = $("tc-text").value.trim();
    if (!text) { $("tc-out").innerHTML = `<p class="tc-note">Paste the tip's text, or add a screenshot.</p>`; return; }
    if (TC.busy) return;
    TC.busy = true; TC.text = text; $("tc-go").disabled = true;
    $("tc-out").innerHTML = `<div class="tc-wait"><span class="tc-spin"></span>Checking the tip: wording, registration, NSE's lists and the price history…</div>`;
    try {
      const d = await api("/api/tipcheck", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text, symbol: symbol || null }) });
      TC.last = d; render(d);
    } catch (err) {
      $("tc-out").innerHTML = `<p class="tc-note err">${esc(err.message)}</p>`;
    } finally { TC.busy = false; $("tc-go").disabled = false; }
  }

  function card(f, i) {
    const quotes = (f.evidence || []).length
      ? `<div class="tc-quotes">${f.evidence.map((q) => `<q class="tc-quote" data-quoted-tip>${esc(q)}</q>`).join("")}</div>` : "";
    return `<article class="tc-card s-${esc(f.status)}" style="--i:${i}">
      <div class="tc-badge" aria-hidden="true">${ICON[f.status] || "·"}</div>
      <div class="tc-body">
        <div class="tc-card-head"><h3>${esc(f.title)}</h3><span class="tc-status">${STATUS_WORD[f.status] || ""}</span></div>
        <p>${esc(f.detail)}</p>${quotes}
      </div></article>`;
  }

  /* the tip as the user received it, with every flagged phrase underlined */
  function bubble(text, phrases) {
    const ranges = [];
    phrases.forEach((p) => {
      const re = new RegExp(p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\s+/g, "\\s+"), "giu");
      for (const m of text.matchAll(re)) if (m[0]) ranges.push([m.index, m.index + m[0].length]);
    });
    ranges.sort((a, b) => a[0] - b[0]);
    let html = "", at = 0;
    ranges.forEach(([s, e]) => {
      if (s < at) return;
      html += esc(text.slice(at, s)) + `<mark class="tc-hit">${esc(text.slice(s, e))}</mark>`; at = e;
    });
    return html + esc(text.slice(at));
  }

  function meter(d) {
    const steps = [["low", "No red flags"], ["some", "Some"], ["many", "Many"]];
    return `<div class="tc-meter lvl-${esc(d.level)}" role="img" aria-label="${esc(d.level_text)}">
      ${steps.map(([k, label]) => `<div class="tc-seg ${k === d.level ? "on" : ""}"><span></span><small>${label}</small></div>`).join("")}</div>`;
  }

  function render(d) {
    const flagged = d.flags > 0;
    const stock = d.symbol
      ? `Checked as <b>${esc(d.symbol)}</b>${d.name ? ` (${esc(d.name)})` : ""}.`
      : "No NSE stock was recognised in the tip.";
    const lessons = d.lessons.map((l) => l.available
      ? `<button type="button" class="btn ghost sm" data-tc-lesson="${esc(l.id)}">${esc(l.title)}</button>`
      : `<span class="tc-soon">${esc(l.title)} <i>(lesson coming soon)</i></span>`).join("");
    const links = (s) => s.links.map((l) => ` <a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)}</a>`).join(" ·");
    $("tc-out").innerHTML = `
      <section class="tc-result">
        ${d.lead ? `<div class="tc-lead" role="alert"><span class="tc-badge">!</span><b>${esc(d.lead)}</b></div>` : ""}
        <div class="panel glass tc-summary ${flagged ? "has-flags" : ""}">
          <img class="tc-mascot" src="${flagged ? MASCOT.shrug : MASCOT.suit}" alt="" width="110" height="110">
          <div class="tc-sum-main">
            <div class="eyebrow">${esc(d.level_text)}</div>
            <div class="tc-count"><b>${d.flags}</b><span>${d.flags === 1 ? "red flag" : "red flags"} in ${d.checked} checks</span></div>
            ${meter(d)}
            <p class="tc-limits">${esc(d.limits)}</p>
          </div>
          <div class="tc-sum-side">
            <button type="button" class="btn" id="tc-share">Share the result</button>
            <button type="button" class="btn ghost sm" id="tc-copy">Copy as text</button>
          </div>
        </div>
        <div class="tc-stock panel">
          <span>${stock}</span>
          <label class="tc-pick">${d.symbol ? "Not the right stock?" : "Which stock is it about?"}
            <input id="tc-symbol" placeholder="Type a company" maxlength="80" data-stock-picker></label>
        </div>
        <figure class="tc-msg"><figcaption>The tip you checked</figcaption>
          <blockquote class="tc-bubble" data-quoted-tip>${bubble(TC.text, d.findings.filter((f) => f.status === "flag").flatMap((f) => f.evidence))}</blockquote></figure>
        <div class="tc-cards">${d.findings.map(card).join("")}</div>
        <div class="panel glass tc-web" id="tc-web">
          <h3>What the web says <span class="tc-ai">AI</span></h3>
          <p class="tc-web-intro">Gemini searches Google for SEBI and NSE actions, scam reports and news about this stock and the sender, with your own key.
            The red-flag count above comes from Belfort's rules only. Pressing the button sends the tip's text to Google.</p>
          <button type="button" class="btn" id="tc-web-btn">Search the web with AI</button>
          <div id="tc-web-out" aria-live="polite"></div>
        </div>
        <div class="panel glass tc-next">
          <h3>What to do next</h3>
          <ol>${d.next_steps.map((s) => `<li>${esc(s.text)}${links(s)}</li>`).join("")}</ol>
          <p class="tc-learn">${esc(d.learn_intro)} ${lessons}</p>
          ${d.register_as_of ? "" : `<p class="src">Belfort has no copy of SEBI's register on this computer yet, so registration numbers are checked for shape only.</p>`}
        </div>
      </section>`;
    if (reduceMotion()) $("tc-out").querySelectorAll(".tc-card").forEach((c) => c.classList.add("still"));
    $("tc-share").addEventListener("click", () => share(d));
    $("tc-copy").addEventListener("click", () => copy(d));
    $("tc-web-btn").addEventListener("click", () => webCheck(d));
    $("tc-symbol").addEventListener("stock-pick", (e) => run(e.detail.symbol));
    $("tc-out").querySelectorAll("[data-tc-lesson]").forEach((b) => b.addEventListener("click", () => go("learn", { lesson: b.dataset.tcLesson })));
    $("tc-out").scrollIntoView({ behavior: reduceMotion() ? "auto" : "smooth", block: "start" });
  }

  /* ---------- the web check (T53): Gemini with Google Search, the user's own key ---------- */
  function webAnswer(text) {
    const lines = text.split(/[\r\n]+/).map((l) => l.trim()).filter(Boolean);
    const items = lines.filter((l) => /^[-*•]\s+/.test(l)).map((l) => `<li>${esc(l.replace(/^[-*•]\s+/, "").replace(/\*\*/g, ""))}</li>`);
    const rest = lines.filter((l) => !/^[-*•]\s+/.test(l)).map((l) => `<p>${esc(l.replace(/\*\*/g, ""))}</p>`);
    return (items.length ? `<ul>${items.join("")}</ul>` : "") + rest.join("");
  }
  async function webCheck(d) {
    const out = $("tc-web-out"), btn = $("tc-web-btn");
    if (!aiReady()) {
      out.innerHTML = `<p class="tc-note err">The web check needs your own Gemini key (free from Google AI Studio). <button type="button" class="linkish" id="tc-web-keys">Open Settings</button></p>`;
      $("tc-web-keys").addEventListener("click", () => $("settings-btn").click());
      return;
    }
    btn.disabled = true;
    out.innerHTML = `<div class="tc-wait"><span class="tc-spin"></span>Searching the web with Gemini. This can take up to half a minute…</div>`;
    try {
      const r = await api("/api/tipcheck/web", { method: "POST", headers: Object.assign({ "Content-Type": "application/json" }, aiHeaders()), body: JSON.stringify({ text: TC.text, symbol: d.symbol }) });
      const srcs = r.sources.length
        ? `<div class="tc-web-src"><b>Sources Google returned</b><ol>${r.sources.map((s) => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></li>`).join("")}</ol></div>`
        : `<p class="src">Google returned no source links for this answer, so treat it with extra care.</p>`;
      out.innerHTML = `<div class="tc-web-answer">${webAnswer(r.answer)}</div>${srcs}
        <p class="src">${esc(r.label)} (${esc(r.model)}). AI can miss things or get them wrong: open the sources before you rely on anything here.</p>`;
      btn.textContent = "Search again";
    } catch (err) {
      out.innerHTML = `<p class="tc-note err">${esc(err.message)}</p>`;
    }
    btn.disabled = false;
  }

  /* ---------- screenshots ---------- */
  function readImage(file) {
    if (!file || !/^image\/(png|jpeg|webp)$/.test(file.type)) { dropMsg("Use a PNG, JPEG or WebP screenshot.", true); return; }
    if (file.size > 5e6) { dropMsg("That image is too large. Use a screenshot under 5 MB.", true); return; }
    const fr = new FileReader();
    fr.onload = () => sendImage(fr.result);
    fr.readAsDataURL(file);
  }
  function dropMsg(text, err, src) {
    const box = $("tc-drop"); box.hidden = false;
    if (src !== undefined) { $("tc-thumb").src = src; $("tc-thumb").hidden = !src; }
    $("tc-drop-msg").innerHTML = text; $("tc-drop-msg").className = err ? "err" : "";
  }
  async function sendImage(dataUrl) {
    if (!aiReady()) {
      dropMsg(`Reading a screenshot needs your own AI key (a free Gemini key works). <button type="button" class="linkish" id="tc-keys">Open Settings</button>, or paste the text instead.`, true, dataUrl);
      $("tc-keys").addEventListener("click", () => $("settings-btn").click());
      return;
    }
    dropMsg("Reading the screenshot with your AI key…", false, dataUrl);
    try {
      const r = await api("/api/tipcheck/image", { method: "POST", headers: Object.assign({ "Content-Type": "application/json" }, aiHeaders()), body: JSON.stringify({ image: dataUrl }) });
      $("tc-text").value = r.text;
      dropMsg("Text read from the screenshot. Check it above, then the tip is checked below.", false);
      run();
    } catch (err) { dropMsg(esc(err.message), true); }
  }
  $("tc-file").addEventListener("change", (e) => { readImage(e.target.files[0]); e.target.value = ""; });
  $("tc-text").addEventListener("paste", (e) => {
    const item = [...(e.clipboardData || {}).items || []].find((x) => x.type.startsWith("image/"));
    if (item) { e.preventDefault(); readImage(item.getAsFile()); }
  });
  const form = $("tc-form");
  form.addEventListener("dragover", (e) => { e.preventDefault(); form.classList.add("drag"); });
  form.addEventListener("dragleave", () => form.classList.remove("drag"));
  form.addEventListener("drop", (e) => { e.preventDefault(); form.classList.remove("drag"); if (e.dataTransfer.files[0]) readImage(e.dataTransfer.files[0]); });

  /* ---------- sharing: a 9:16 card ---------- */
  function textSummary(d) {
    const lines = d.findings.filter((f) => f.status === "flag").map((f) => "✕ " + f.title);
    return `${d.share_line}\n${lines.join("\n")}\n\n${d.limits}\nBelfort is free and open source.`;
  }
  async function copy(d) {
    try { await navigator.clipboard.writeText(textSummary(d)); $("tc-copy").textContent = "Copied"; }
    catch (e) { $("tc-copy").textContent = "Could not copy"; }
    setTimeout(() => { if ($("tc-copy")) $("tc-copy").textContent = "Copy as text"; }, 1800);
  }
  const loadImg = (src) => new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => ok(null); i.src = src; });
  function wrap(ctx, text, x, y, maxW, lh) {
    const words = text.split(" "); let line = "";
    for (const w of words) {
      const test = line ? line + " " + w : w;
      if (ctx.measureText(test).width > maxW && line) { ctx.fillText(line, x, y); y += lh; line = w; } else line = test;
    }
    if (line) ctx.fillText(line, x, y);
    return y + lh;
  }
  async function cardImage(d) {
    const W = 1080, H = 1920, c = document.createElement("canvas"); c.width = W; c.height = H;
    const x = c.getContext("2d");
    try { await document.fonts.load('120px "Instrument Serif"'); await document.fonts.load('600 40px "Inter"'); } catch (e) { /* system fonts are fine */ }
    x.fillStyle = "#050506"; x.fillRect(0, 0, W, H);
    // candles along the top, green and red, from a fixed pattern scaled into a band
    const moves = [1, 1, -1, 1, 1, 1, -1, 1, 1, 1, 1, -1, -1, -1, -1, -1];
    const bodies = []; let lvl = 0;
    moves.forEach((m, i) => { const h = 40 + ((i * 37) % 50); bodies.push([lvl, lvl + m * h]); lvl += m * h * (m > 0 ? 0.8 : 0.9); });
    const all = bodies.flat(), lo = Math.min(...all), hi = Math.max(...all), y0 = 140, y1 = 400;
    const ys = (v) => y1 - ((v - lo) / (hi - lo || 1)) * (y1 - y0);
    bodies.forEach(([o, cl], i) => {
      const cx = 80 + i * 62, top = ys(Math.max(o, cl)), bot = ys(Math.min(o, cl));
      x.strokeStyle = x.fillStyle = cl >= o ? "#22c55e" : "#ef4444";
      x.globalAlpha = 0.9; x.lineWidth = 4;
      x.beginPath(); x.moveTo(cx, top - 20); x.lineTo(cx, bot + 20); x.stroke();
      x.fillRect(cx - 17, top, 34, Math.max(6, bot - top));
    });
    x.globalAlpha = 1;
    // the mascot on a soft yellow glow, so the black suit shows on black
    const glow = x.createRadialGradient(880, 640, 20, 880, 640, 230);
    glow.addColorStop(0, "rgba(250,204,21,.38)"); glow.addColorStop(1, "rgba(250,204,21,0)");
    x.fillStyle = glow; x.fillRect(640, 400, 480, 480);
    const mascot = await loadImg(d.flags ? MASCOT.shrug : MASCOT.suit);
    if (mascot) x.drawImage(mascot, 700, 400, 360, 360);
    x.fillStyle = "#facc15"; x.font = '64px "Instrument Serif", Georgia, serif'; x.fillText("Belfort", 70, 520);
    x.fillStyle = "#f4f4f2"; x.font = '88px "Instrument Serif", Georgia, serif';
    wrap(x, "I checked this tip on Belfort.", 70, 650, 600, 96);
    x.font = '340px "Instrument Serif", Georgia, serif'; x.fillStyle = d.flags ? "#ef4444" : "#22c55e";
    const nW = x.measureText(String(d.flags)).width;
    x.fillText(String(d.flags), 60, 1110);
    x.font = '600 54px "Inter", sans-serif'; x.fillStyle = "#f4f4f2";
    x.fillText(d.flags === 1 ? "red flag" : "red flags", 60 + nW + 30, 1100);
    let y = 1230;
    x.font = '500 40px "Inter", sans-serif';
    d.findings.filter((f) => f.status !== "info").forEach((f) => {
      x.fillStyle = f.status === "flag" ? "#ef4444" : f.status === "clear" ? "#22c55e" : "#8b8b90";
      x.fillText(f.status === "flag" ? "✕" : f.status === "clear" ? "✓" : "–", 70, y);
      x.fillStyle = f.status === "unknown" ? "#8b8b90" : "#f4f4f2";
      x.fillText(f.title + (f.status === "unknown" ? " (not checked)" : ""), 130, y); y += 64;
    });
    x.strokeStyle = "rgba(255,255,255,.15)"; x.lineWidth = 2;
    x.beginPath(); x.moveTo(70, H - 210); x.lineTo(W - 70, H - 210); x.stroke();
    x.fillStyle = "#8b8b90"; x.font = '400 30px "Inter", sans-serif';
    wrap(x, "Belfort reports red flags found and not found. It never says a stock is one to buy or sell. Free and open source.", 70, H - 150, W - 140, 42);
    return new Promise((ok) => c.toBlob(ok, "image/png"));
  }
  async function share(d) {
    const btn = $("tc-share"); btn.disabled = true; btn.textContent = "Making the card…";
    try {
      const blob = await cardImage(d), file = new File([blob], "belfort-tip-check.png", { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], text: d.share_line });
      } else {
        const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = file.name;
        document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
      }
    } catch (e) { /* the user closed the share sheet */ }
    btn.disabled = false; btn.textContent = "Share the result";
  }
})();
