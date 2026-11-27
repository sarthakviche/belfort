# Changes log (Belfort 2 sprint)

A running log of every change made in the Belfort 2 sprint, newest first. `CHANGELOG.md` stays the user-facing release notes; this file records what was done, by whom, on which branch, and why.

## 2026-11-28 — T43 Accounts and sync (Devansh's agent, branch `feat/T43-accounts-sync`)

### Decisions
- **Supabase Auth** (email and password, Google with PKCE). The provider sits behind `belfort/core/auth.py` only.
- **One SQLite file per signed-in user** (`users/<id>.db`), chosen in the single `db._path()` hook, instead of a `user_id` filter in every query.
  - No cross-user leaks through a forgotten filter.
  - No changes to practice or learn queries.
  - T42's new tables are scoped for free.
  - The contract's `user_id` columns stay valid (inside a file every row is the file's user).
- **Sync:** whole documents per kind (`practice` = the T10 backup, `learn` = lesson progress plus `LEARN_PARTS` for T42's game state, `settings` = whitelisted interface choices, never an AI key).
  - Last write wins, with the server clock (a trigger sets `updated_at`).
  - On a new computer, the account copy wins.
  - The losing copy is saved in `sync-backups/`.
- **When it syncs:** on sign-in, every 60 seconds while signed in (`SYNC_INTERVAL_SECONDS`), on Sync now, and on app shutdown.
- **New account:** if this computer has local data, the user is asked whether to bring it in.
- **Shared mode:** accounts switch off when `ACCESS_CODES` is set (one app = one user).
- **Privacy:** the DPDP Act notice is on the sign-in screen, and the account can be deleted from the menu (`delete_my_account()` SQL function, the caller only).

### Changes
- **New:**
  - `belfort/core/auth.py`, `sync.py` and `accounts_router.py`
  - `supabase/migrations/20261128000000_user_state.sql`
  - `belfort/static/auth.js` and `auth.css`
  - `docs/ACCOUNTS.md` (setup, design, payload shapes for Android)
- **Changed:**
  - `users.py`: only the body of `current_user_id`
  - `db.py`: `path_for()` and `_path()`
  - `main.py`: router, a lifespan for background sync, and `accounts` in `/api/config`
  - `settings.py`: `SYNC_INTERVAL_SECONDS`
  - `index.html`: one stylesheet and one script tag
  - `.env.example`, CHANGELOG, ARCHITECTURE, STATUS
- **Tests:** `tests/test_accounts.py`, 23 tests against an in-memory fake Supabase. They cover:
  - sign-up, sign-in and sign-out, plus error wording
  - token refresh: refused, and offline
  - Google PKCE
  - per-user scoping and path safety
  - first push, a second computer pulling the same paper account
  - both conflict directions, with backups
  - `LEARN_PARTS`, import of local data, every API route, and background sync

### Checked
- `ruff check`, `ruff format --check`, `pytest --cov` (80.8%).
- In the running app (port 8767) against a local fake of the Supabase API:
  - the first-launch sign-in screen
  - create an account, then the header menu, then Sync now ("just now")
  - sign out (the menu shows "Sign in", no screen again)
  - Google: authorize, then `/auth/callback`, then signed in and back on the app
  - no console errors
- Not yet checked against a real Supabase project, because none exists yet.

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
- **Multi-language (T50):** English first, with Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati and Kannada. Interface strings in shared catalogues for desktop and Android; Beginner lessons in Hindi first; Ask Belfort, Tip Check and the dictionary answer in the chosen language. Tip Check reads Hinglish tips. Owned by Sarthak's side, starting after T42 to avoid editing every screen twice.
- **COMPLIANCE.md rule 7 amended** (raised by Devansh's agent): local-first with optional accounts; only the user's own practice, learning and settings documents sync; DPDP Act 2023 privacy notice and in-app account deletion required; legal sign-off is D3. Needs Sarthak's approval at review, per CLAUDE.md.
- **Database migrations:** 7 = Devansh's optional stop-loss (`feat/report-redesign-and-logic`), 8 = T42 Learn game tables, 9 = T43 user_id columns. Whoever merges second renumbers; migrations are appended, never edited after merge.
- **Agent coordination** happens in `conversations.md` on the `collab` branch. The Android app (T48) is built on Devansh's machine.

### Changes
- `docs/TASKS.md`: Phase 6 with tasks T42 to T49 and the shared contracts (current user, stages, exercise types, new UI in its own files).
- `content/learn/syllabus.json`: every module has a `stage`.
- `belfort/core/users.py`: `current_user_id()` stub that returns `"local"` until T43.
- `belfort/static/img/mascot/`: the two mascot GIFs.
