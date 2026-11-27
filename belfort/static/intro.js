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
    const words = INTRO_QUOTE.text.split(/\s+/);
    const root = document.createElement("div");
    root.className = "intro-screen";
    root.setAttribute("role", "dialog");
    root.setAttribute("aria-modal", "true");
    root.setAttribute("aria-label", "Welcome to Belfort");
    root.style.setProperty("--total", words.length);
    const q = document.createElement("blockquote");
    q.className = "intro-quote";
    words.forEach((w, i) => { const s = document.createElement("span"); s.className = "w"; s.style.setProperty("--n", i); s.textContent = w; q.appendChild(s); });
    const by = document.createElement("div"); by.className = "intro-by"; by.textContent = "— " + INTRO_QUOTE.by;
    const go = document.createElement("button"); go.type = "button"; go.className = "intro-go"; go.textContent = "Start learning";
    const skip = document.createElement("button"); skip.type = "button"; skip.className = "intro-skip"; skip.textContent = "Skip";
    root.append(skip, q, by, go);
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

  document.addEventListener("belfort:splash-done", () => { if (seen()) done("seen"); else show(); }, { once: true });
})();
