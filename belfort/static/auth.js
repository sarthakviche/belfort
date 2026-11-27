"use strict";
/* Accounts and sync (T43). Its own file: app.js and index.html only load it. Does nothing when the app has no
   account service set up (cfg.accounts false), so Belfort stays local only. Uses app.js helpers: $, esc, api. */
(function () {
  const CHOICE = "belfortAccountChoice";   // "local" once the user chose to continue without an account
  const A = { state: null, lastSettings: "" };
  const MASCOT = "img/mascot/mascot-suit.gif";
  const store = { get: (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } },
                  set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* private window */ } } };

  const post = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}) });
  const when = (iso) => {
    if (!iso) return "not yet";
    const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
    return s < 60 ? "just now" : s < 3600 ? `${Math.round(s / 60)} min ago` : new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
  };

  /* ---------- settings that follow the account (never the AI key) ---------- */
  function settingsDoc() {
    let ai = {}; try { ai = JSON.parse(store.get("belfortAI")) || {}; } catch (e) { ai = {}; }
    const d = { style: store.get("style"), capital: store.get("capital"), risk: store.get("risk"), language: store.get("belfortLang"),
      aiProvider: ai.provider, aiModel: ai.model, aiBase: ai.base };
    Object.keys(d).forEach((k) => { if (d[k] == null || d[k] === "") delete d[k]; });
    return d;
  }
  function applySettings(d) {
    if (!d) return;
    [["style", "style"], ["capital", "capital"], ["risk", "risk"], ["language", "belfortLang"]].forEach(([k, ls]) => { if (d[k] != null) store.set(ls, d[k]); });
    if (d.aiProvider || d.aiModel || d.aiBase) {
      let ai = {}; try { ai = JSON.parse(store.get("belfortAI")) || {}; } catch (e) { ai = {}; }
      if (d.aiProvider && d.aiProvider !== ai.provider) delete ai.key;   // a key belongs to one provider; it never syncs
      Object.assign(ai, { provider: d.aiProvider || ai.provider, model: d.aiModel || ai.model, base: d.aiBase || ai.base });
      store.set("belfortAI", JSON.stringify(ai));
    }
  }
  async function pushSettings() {
    if (!A.state || !A.state.user) return;
    const doc = JSON.stringify(settingsDoc());
    if (doc === A.lastSettings) return;
    try { await api("/api/sync/settings", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ settings: JSON.parse(doc) }) }); A.lastSettings = doc; }
    catch (e) { /* tried again in 30 seconds */ }
  }

  /* ---------- the full-screen sign-in ---------- */
  function gate(mode) {
    let el = $("auth-gate");
    if (!el) { el = document.createElement("div"); el.id = "auth-gate"; el.className = "auth-gate"; el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true"); document.body.append(el); }
    const signUp = mode === "signup";
    el.innerHTML = `
      <div class="auth-card">
        <img class="auth-mascot" src="${MASCOT}" alt="" width="120" height="120">
        <div class="auth-word">Belfort</div>
        <p class="auth-sub">${signUp ? "Create an account so your practice and learning follow you to your phone." : "Sign in to carry your practice and learning between Windows and Android."}</p>
        <form id="auth-form" class="auth-form">
          <label>Email<input name="email" type="email" autocomplete="email" required></label>
          <label>Password<input name="password" type="password" autocomplete="${signUp ? "new-password" : "current-password"}" minlength="6" required></label>
          <p class="auth-msg" id="auth-msg" role="status"></p>
          <button type="submit" class="btn auth-main">${signUp ? "Create account" : "Sign in"}</button>
        </form>
        <button type="button" class="btn ghost auth-google" id="auth-google"><span class="g">G</span>Continue with Google</button>
        <button type="button" class="linkish auth-switch" id="auth-switch">${signUp ? "Have an account? Sign in" : "New here? Create an account"}</button>
        <button type="button" class="auth-local" id="auth-local">Continue without an account</button>
        <details class="auth-privacy"><summary>What an account stores</summary><p>${esc(A.state.privacy)}</p></details>
      </div>`;
    el.hidden = false;
    $("auth-switch").onclick = () => gate(signUp ? "signin" : "signup");
    $("auth-local").onclick = () => { store.set(CHOICE, "local"); el.hidden = true; };
    $("auth-google").onclick = google;
    $("auth-form").onsubmit = async (e) => {
      e.preventDefault();
      const f = e.target, msg = $("auth-msg"), btn = f.querySelector("button");
      btn.disabled = true; msg.className = "auth-msg"; msg.textContent = signUp ? "Creating your account…" : "Signing in…";
      try {
        const r = await post(signUp ? "/api/auth/signup" : "/api/auth/signin", { email: f.email.value, password: f.password.value });
        if (r.confirm) { msg.textContent = "Check your email and open the confirmation link, then sign in here."; btn.disabled = false; return; }
        await done(r);
      } catch (err) { msg.className = "auth-msg err"; msg.textContent = err.message; btn.disabled = false; }
    };
    setTimeout(() => { const i = el.querySelector("input"); if (i) i.focus(); }, 50);
  }

  async function google() {
    const msg = $("auth-msg");
    try {
      const { url } = await api("/api/auth/google");
      const w = window.open(url, "_blank", "noopener");
      if (!w) { location.href = url; return; }
      msg.className = "auth-msg"; msg.textContent = "Finish signing in with Google in your browser. This window updates by itself.";
      const started = Date.now();
      const tick = setInterval(async () => {
        if (Date.now() - started > 180000) { clearInterval(tick); msg.textContent = "Google sign-in timed out. Try again."; return; }
        try { const s = await api("/api/auth/state"); if (s.user) { clearInterval(tick); location.reload(); } } catch (e) { /* keep waiting */ }
      }, 2000);
    } catch (err) { msg.className = "auth-msg err"; msg.textContent = err.message; }
  }

  async function done(r) {
    if (r.offer_import) return offerImport();
    location.reload();
  }

  function offerImport() {
    const el = $("auth-gate") || (gate("signin"), $("auth-gate"));
    el.hidden = false;
    el.innerHTML = `<div class="auth-card">
        <img class="auth-mascot" src="${MASCOT}" alt="" width="120" height="120">
        <div class="auth-word">Welcome</div>
        <p class="auth-sub">This computer has practice trades or lessons from before you signed in. Bring them into your new account?</p>
        <p class="auth-msg" id="auth-msg" role="status"></p>
        <button type="button" class="btn auth-main" id="auth-import">Bring them in</button>
        <button type="button" class="auth-local" id="auth-fresh">Start the account empty</button>
        <p class="src">Either way, the data on this computer stays where it is when you sign out.</p>
      </div>`;
    $("auth-import").onclick = async () => {
      $("auth-msg").textContent = "Copying and syncing…";
      try { await post("/api/auth/import-local"); location.replace("/"); }
      catch (err) { $("auth-msg").className = "auth-msg err"; $("auth-msg").textContent = err.message; }
    };
    $("auth-fresh").onclick = async () => { try { await post("/api/sync"); } catch (e) { /* first sync can wait */ } location.replace("/"); };
  }

  /* ---------- the account menu in the header ---------- */
  function menu() {
    const top = document.querySelector("header.top");
    if (!top) return;
    let wrap = $("acct");
    if (!wrap) { wrap = document.createElement("div"); wrap.id = "acct"; wrap.className = "acct"; top.insertBefore(wrap, top.querySelector(".pill")); }
    const u = A.state.user;
    if (!u) {
      wrap.innerHTML = `<button type="button" class="btn ghost sm" id="acct-in">Sign in</button>`;
      $("acct-in").onclick = () => gate("signin");
      return;
    }
    const initial = (u.email || "?").trim()[0].toUpperCase();
    wrap.innerHTML = `<button type="button" class="acct-btn" id="acct-btn" aria-haspopup="true" aria-expanded="false" title="${esc(u.email)}"><span>${esc(initial)}</span></button>
      <div class="acct-menu" id="acct-menu" hidden role="menu">
        <div class="acct-email">${esc(u.email)}</div>
        <div class="acct-sync" id="acct-sync">Last synced: ${esc(when(A.state.last_synced))}</div>
        <button type="button" role="menuitem" id="acct-now">Sync now</button>
        <button type="button" role="menuitem" id="acct-out">Sign out</button>
        <button type="button" role="menuitem" class="danger" id="acct-del">Delete account…</button>
      </div>`;
    const m = $("acct-menu"), b = $("acct-btn");
    b.onclick = (e) => { e.stopPropagation(); m.hidden = !m.hidden; b.setAttribute("aria-expanded", String(!m.hidden)); };
    document.addEventListener("click", (e) => { if (!wrap.contains(e.target)) { m.hidden = true; b.setAttribute("aria-expanded", "false"); } });
    $("acct-now").onclick = async () => {
      $("acct-sync").textContent = "Syncing…";
      try {
        await pushSettings();
        const r = await post("/api/sync");
        A.state.last_synced = r.last_synced;
        const pulled = Object.values(r.kinds).includes("pulled");
        $("acct-sync").textContent = `Last synced: ${when(r.last_synced)}` + (pulled ? " · updated from your account" : "");
        if (pulled) setTimeout(() => location.reload(), 900);
      } catch (err) { $("acct-sync").textContent = err.message; }
    };
    $("acct-out").onclick = async () => { await post("/api/auth/signout"); store.set(CHOICE, "local"); location.replace("/"); };
    $("acct-del").onclick = async () => {
      if (!confirm("Delete your Belfort account and everything synced to it? This cannot be undone. Data on this computer stays.")) return;
      try { await post("/api/auth/delete"); location.replace("/"); } catch (err) { $("acct-sync").textContent = err.message; }
    };
  }

  /* ---------- start ---------- */
  (async function init() {
    let cfg;
    try { cfg = await (await fetch("/api/config")).json(); } catch (e) { return; }
    if (!cfg.accounts) return;
    try { A.state = await api("/api/auth/state"); } catch (e) { return; }
    menu();
    const params = new URLSearchParams(location.search);
    if (A.state.user) {
      if (params.get("import") === "1") return offerImport();
      if (params.has("signedin")) history.replaceState(null, "", "/" + location.hash);
      try { const r = await api("/api/sync/settings"); if (r.settings && Object.keys(r.settings).length) applySettings(r.settings); } catch (e) { /* offline */ }
      A.lastSettings = JSON.stringify(settingsDoc());
      setInterval(pushSettings, 30000);
      document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") pushSettings(); });
    } else if (store.get(CHOICE) !== "local") {
      gate("signin");
    }
  })();
})();
