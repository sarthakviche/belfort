# Changes log (Belfort 2 sprint)

A running log of every change made in the Belfort 2 sprint, newest first. `CHANGELOG.md` stays the user-facing release notes; this file records what was done, by whom, on which branch, and why.

## 2026-11-28 — T22 scams, tips and your rights lessons (Sarthak's agent)

### Changes
- `content/learn/lessons/tip-scams.md`, `check-registration.md`, `myths.md`: the three Safety lessons, each with a quiz and a Sources line. They describe SEBI's January 2022 interim order on a Telegram tip channel, the May 2026 interim order on social-media pump-and-dump, and SEBI's October 2026 warning on invitation-only WhatsApp groups; how to search SEBI's registered intermediaries, SEBI Check, SCORES and NSE complaints; and six myths mapped to earlier lessons.
- Wording avoids the banned promise phrases, which the content test scans for, so "promised returns" and "buy at once" stand in for the usual scam phrases.
- Left out because unverified: a "Know your broker" NSE page (not found), helpline numbers, the exact SCORES stage-by-stage flow, the August 2024 SEBI circular text. The SCORES one-year limit and 21-day reply time come from secondary summaries and are hedged in the lesson. The statement that SEBI studies found most individual traders lose money is from memory and is flagged in the lesson's Sources line.
- Tip Check (T44) is referred to in words only; it may not have shipped when this merges.
- `content/learn/syllabus.json`: removed `planned` from the three lessons. `belfort/core/glossary.py`: added Pump and dump, Investment adviser, Research analyst, SCORES.
- `CHANGELOG.md`, `docs/STATUS.md`, `docs/ABOUT.md`, `docs/TASKS.md`: 36 of 38 on this branch alone (38 of 38 once T21 merges too; the count lines will need a trivial merge fix).

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
