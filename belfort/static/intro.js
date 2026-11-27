/* First-open intro (T46). Shown once, after the loader. Change the quote here and nowhere else. */
(function () {
  "use strict";
  const INTRO_QUOTE = { text: "Risk comes from not knowing what you’re doing.", by: "Warren Buffett" };
  const SEEN_KEY = "belfort.intro.seen";
  window.BELFORT_INTRO_QUOTE = INTRO_QUOTE;

  function seen() { try { return localStorage.getItem(SEEN_KEY) === "1"; } catch (e) { return false; } }
  function remember() { try { localStorage.setItem(SEEN_KEY, "1"); } catch (e) { /* private mode: the intro may show again */ } }
  // T43 hooks in here: continue to the sign-in screen (or the app) when this fires.
  function done(action) { document.dispatchEvent(new CustomEvent("belfort:intro-done", { detail: { action } })); }

  function show() {
    const root = document.createElement("div");
    root.className = "intro-screen";
    root.setAttribute("role", "dialog");
    root.setAttribute("aria-modal", "true");
    const q = document.createElement("blockquote");
    q.className = "intro-quote";
    const by = document.createElement("div"); by.className = "intro-by";
    const langs = document.createElement("div"); langs.className = "intro-langs"; langs.setAttribute("role", "group");
    const go = document.createElement("button"); go.type = "button"; go.className = "intro-go";
    const skip = document.createElement("button"); skip.type = "button"; skip.className = "intro-skip";
    // Words, labels and the quote are drawn from the catalogue, so choosing a language below redraws them at once.
    function paint(animate) {
      const words = T("intro.quote", null, INTRO_QUOTE.text).split(/\s+/);
      root.setAttribute("aria-label", T("intro.aria", null, "Welcome to Belfort"));
      root.style.setProperty("--total", animate ? words.length : 0);
      q.textContent = "";
      words.forEach((w, i) => { const s = document.createElement("span"); s.className = "w"; s.style.setProperty("--n", animate ? i : 0); s.textContent = w; q.appendChild(s); });
      by.textContent = "— " + T("intro.by", null, INTRO_QUOTE.by);
      langs.setAttribute("aria-label", T("intro.langs", null, "Choose your language"));
      go.textContent = T("intro.start", null, "Start learning");
      skip.textContent = T("intro.skip", null, "Skip");
    }
    paint(true);
    I18N.chips(langs);
    document.addEventListener("belfort:language", () => paint(false));
    root.append(skip, q, by, langs, go);
    document.body.appendChild(root);
    requestAnimationFrame(() => root.classList.add("in"));
    go.focus({ preventScroll: true });

    let closed = false;
    function close(action) {
      if (closed) return;
      closed = true;
      remember();
      document.removeEventListener("keydown", onKey, true);
      root.classList.add("out");
      setTimeout(() => root.remove(), 400);
      if (action === "learn" && typeof window.go === "function") window.go("learn");
      done(action);
    }
    function onKey(e) { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close("skip"); } }
    document.addEventListener("keydown", onKey, true);
    go.addEventListener("click", () => close("learn"));
    skip.addEventListener("click", () => close("skip"));
  }

  document.addEventListener("belfort:splash-done", () => { I18N.ready.then(() => { if (seen()) done("seen"); else show(); }); }, { once: true });
})();
