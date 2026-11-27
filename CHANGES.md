# Changes log (Belfort 2 sprint)

A running log of every change made in the Belfort 2 sprint, newest first. `CHANGELOG.md` stays the user-facing release notes; this file records what was done, by whom, on which branch, and why.

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

## 2026-11-28 — T45 dictionary search

### Decisions
- **Own router and module.** `belfort/assistant/glossary_router.py` (`/api/glossary/search`, `/ask`, `/web-search`) and the pure ranking in `belfort/core/glossary_search.py`; `assistant/chat.py` and `core/glossary.py` are untouched. `ask()` is called in `general` mode, so the existing compliance filter applies.
- **Web search from pywebview.** The desktop window does not open new browser windows, so inside it the page asks the backend (`POST /api/glossary/web-search`, loopback only) to call `webbrowser.open`; in a normal browser it uses `window.open`. The URL is `https://www.google.com/search?q=<term> stock market meaning`, URL-encoded.
- **Ranking.** Exact term, exact phrase, prefix, word prefix, substring, difflib closeness (0.75 cutoff), then a whole word in the explanation. Empty query returns the full glossary for browsing by category.
- **Old drawer.** The sidebar Dictionary button now opens the new page; the old drawer markup is left in place, unused.
- **Privacy.** Nothing about a query leaves the computer except on the user's own click on Ask Belfort (their AI provider) or Search the web (their browser).

### Changes
- New: `belfort/static/dictionary.js`, `dictionary.css`, `tests/test_dictionary.py`.
- Touched: `belfort/main.py` (router), `belfort/static/index.html` (nav item, section, links), `belfort/static/app.js` (view list, button, start hash), `CHANGELOG.md`, `docs/STATUS.md`, `docs/TASKS.md`.
