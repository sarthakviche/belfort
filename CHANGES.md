# Changes log (Belfort 2 sprint)

A running log of every change made in the Belfort 2 sprint, newest first. `CHANGELOG.md` stays the user-facing release notes; this file records what was done, by whom, on which branch, and why.

## 2026-11-28 — T46 startup loader and intro

Branch `feat/T46-startup-loader`.

### Decisions
- The Windows launcher loads `belfort/static/splash.html` from disk straight away, starts the server in a thread and, once the server answers and 2.3 s have passed, calls `window.load_url(app_url)`. The URL carries `?splash=0` so the app does not play the loader a second time.
- In a browser, `index.html` carries the same loader as an overlay at half duration (`--k: .5`), shown for at least 1.2 s and until `app.js` fires `belfort:app-ready`; a 9 s safety timer removes it regardless.
- The intro runs after `belfort:splash-done`, is remembered in `localStorage` (`belfort.intro.seen`, in try/catch) and fires `belfort:intro-done` (detail `{action}`) for T43 to hook its sign-in screen. There is no server-side settings store, so there is no server flag.
- The quote lives in `INTRO_QUOTE` in `intro.js`. System serif fonts (Instrument Serif where the app already loads it, then Georgia).

### Changes
- New: `belfort/static/splash.html`, `splash.css`, `splash.js`, `intro.css`, `intro.js`, `tests/test_desktop.py`.
- `run_desktop.py`: `splash_url`, `app_url`, `navigate_when_ready`; the window opens on the loader.
- `belfort/static/index.html` (loader div and four includes) and `app.js` (one event after init).

## 2026-11-27 — sprint set-up (Sarthak's agent)

### Decisions
- **Accounts replace offline-only.** Supabase Auth plus one `user_state` table with row-level security. Desktop and Android sign in to the same project, and the paper account, journal and Learn progress sync as whole JSON documents (the T10 backup format), last write wins. "Continue without an account" keeps today's local mode. (T43)
- **Hook feature: Tip Check.** Paste or screenshot a stock tip and see its red flags in ten seconds: SEBI registration, promised returns, urgency, NSE surveillance lists and a pump-and-dump price and volume check. Chosen because it protects a real person from a real loss and fits every compliance rule: it reports red flags, never a buy or sell view. (T44)
- **Learn becomes a path in three stages.** Beginner = Foundations plus Scams, tips and your rights (scam safety belongs at the start). Intermediate = Practitioner plus Taxes and records. Advanced = Market context, Running several trades, Psychology. Locked stages show titles only; the API refuses their content. (T42)
- **Mascot:** the headless suit with the yellow tie, from `design assets/mascot gifs/`, copied to `belfort/static/img/mascot/` (`mascot-suit.gif`, `mascot-shrug.gif`).
- **Quote** for the intro and landing page: "Risk comes from not knowing what you're doing." (Warren Buffett). It lives in one constant so it can be swapped.
- **Look:** neon green and red candles drawing on black (from the intro inspiration), large editorial serif type for the quote, Belfort yellow (#facc15) for the accent.
- **Inspiration videos and images** in `design assets/intro animation inspos/` stay out of git: they are third-party downloads, for reference only.
- **Work split (equal):** Devansh's side takes T48 Android, T43 accounts and sync, T44 Tip Check (technical architecture and market-domain data). Sarthak's side takes T42 gamified Learn, T45 dictionary, T46 loader, T47 landing site, T21 and T22 lessons, T49 exercises (design, UI and content).
- **Agent coordination** happens in `conversations.md` on the `collab` branch. The Android app (T48) is built on Devansh's machine.

### Changes
- `docs/TASKS.md`: Phase 6 with tasks T42 to T49 and the shared contracts (current user, stages, exercise types, new UI in its own files).
- `content/learn/syllabus.json`: every module has a `stage`.
- `belfort/core/users.py`: `current_user_id()` stub that returns `"local"` until T43.
- `belfort/static/img/mascot/`: the two mascot GIFs.
