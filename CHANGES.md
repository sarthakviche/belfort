# Changes log (Belfort 2 sprint)

A running log of every change made in the Belfort 2 sprint, newest first. `CHANGELOG.md` stays the user-facing release notes; this file records what was done, by whom, on which branch, and why.

## 2026-11-28 — T44 Tip Check (Devansh's agent, branch `feat/T44-tip-check`)

### Decisions
- **Nine checks, in a fixed order:**
  1. SEBI registration
  2. Promised returns
  3. A price target with a deadline
  4. Pressure to hurry
  5. Claimed insider or secret information
  6. Requests for money or a move to a private group (added: this is where most tip scams take the money)
  7. NSE surveillance lists
  8. Pump pattern
  9. What the stock did the last time it looked like this

  The first eight count as red flags. The ninth is context only. Status per card: flag (red), clear (green), not checked (grey), context (yellow).
- **Surveillance data comes from NSE's daily `REG1_IND<ddmmyy>.csv`** on nsearchives (the host the app already uses). It has one column per measure: GSM, long- and short-term ASM, ESM, NSE's own flags for stocks named in unsolicited SMS and social-media tips, and insolvency. A value of 100 means "not under the measure"; any other value is the stage. Checked against the live file of 27 Nov 2026 (3,599 symbols).
- **SEBI registers:** SEBI has no download and no API, and its site refused scripted requests. So numbers get an offline shape check (INA or INH plus nine digits; INZ broker and INP portfolio-manager numbers are flagged as the wrong kind). They are compared with a local copy the user imports with `python -m belfort.tipcheck.register <saved lists>` (kept in the data folder, never in git). A match is reported as "in the copy of <date>, confirm the sender really is them", never as proof. Claims that SEBI "approved" a tip are always a flag.
- **Pump pattern** = at least two of three signals:
  - a session in the last 5 with volume at least 5× its 50-session average
  - a rise of at least 30% in 20 sessions or 60% in 60
  - a market value under ₹5,000 crore

  All thresholds are in `settings.py`.
- **"Last time"** uses only bars at least 30 days old, for both the episode and its outcome (20 and 60 sessions later, and the lowest close). It always ends with "This is what happened once before, not what will happen now."
- **Languages:** the tip's wording is matched from `belfort/tipcheck/phrases.json`, split by flag and language (`en`, `hinglish`, `hi`), so adding a language is a data change. Overlapping matches merge into one quote ("100% sure shot"). Every sentence Belfort shows is in `belfort/tipcheck/strings.py`, ready for T50's catalogues.
- **Compliance:** the tip's own words (which include banned phrases such as "sure shot") are shown only as quoted evidence in `<q data-quoted-tip>`. Belfort's wording is tested free of banned phrases. Every result says Belfort can't tell whether a trade will work and never calls a stock good, safe, or one to buy or sell. `compliance.py` and `chat.py` are unchanged.
- **Screenshots:** they're read by a new `belfort/assistant/vision.py` with the user's own key (Gemini or any OpenAI-compatible model). It only transcribes, and the text is put in the box for the user to see before the rules run.
- **Speed:** the stock checks run in parallel with an eight-second budget; a slow source shows as "not checked". A live check of a SUZLON tip took 1.3 s.

### Changes
- New `belfort/tipcheck/`: `rules.py` (pure checks), `phrases.json`, `strings.py`, `sources.py`, `register.py`, `service.py`, `router.py` (`POST /api/tipcheck`, `POST /api/tipcheck/image`).
- New `belfort/assistant/vision.py`.
- `belfort/settings.py`: the `TIP_*` thresholds.
- `belfort/main.py`: mounts the router.
- New `belfort/static/tipcheck.js` and `tipcheck.css`. `index.html` gets one nav item, one section, a stylesheet and a script tag; `app.js` gets the view name only. They add:
  - a "Paste a tip" box on the Research home
  - the Tip Check page with paste, upload, drop or paste-in screenshots
  - flag cards that flip in one by one (none under reduced motion)
  - a three-step risk meter
  - the mascot shrugging when flags are found
  - a stock picker to correct the stock
  - next steps with links to SEBI and SCORES, and the Safety lessons (shown as "coming soon" until T22 lands)
  - a 9:16 share card through the share sheet (or a download), and "Copy as text"
- Tests: `tests/test_tipcheck.py` (31 offline tests), with fixtures `tests/fixtures/reg1_ind_sample.csv` (NSE's real column header, made-up rows) and `tests/fixtures/sebi_register_sample.csv`.
- Docs: CHANGELOG, `docs/ARCHITECTURE.md`, `docs/STATUS.md`.

### Checked
- `ruff check`, `ruff format --check`, and `pytest --cov`: all pass, coverage 81.9%.
- In the running app (port 8766, live NSE and Yahoo data):
  - an English and Hinglish SUZLON tip gave 6 red flags in 8 checks, with SUZLON's 30 Nov 2023 volume spike shown as context
  - a Hindi (Devanagari) IRFC tip gave 4 red flags
  - a tip with no stock named offered the picker; picking Yes Bank re-ran the checks
  - the share card was generated and inspected
  - the page was checked at 375 px wide with no sideways scroll

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
- **Agent coordination** happens in `conversations.md` on the `collab` branch. The Android app (T48) is built on Devansh's machine.

### Changes
- `docs/TASKS.md`: Phase 6 with tasks T42 to T49 and the shared contracts (current user, stages, exercise types, new UI in its own files).
- `content/learn/syllabus.json`: every module has a `stage`.
- `belfort/core/users.py`: `current_user_id()` stub that returns `"local"` until T43.
- `belfort/static/img/mascot/`: the two mascot GIFs.
