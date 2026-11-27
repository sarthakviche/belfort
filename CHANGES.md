# Changes log (Belfort 2 sprint)

A running log of every change made in the Belfort 2 sprint, newest first. `CHANGELOG.md` stays the user-facing release notes; this file records what was done, by whom, on which branch, and why.

## 2026-11-28 — T42 gamified Learn

Branch `feat/T42-gamified-learn`, built on the sprint plan in #30.

### What changed
- **Engine (pure, no I/O):** `belfort/learn/engine.py` holds XP, the daily goal and streak with freezes, hearts, stage unlock rules, test sampling and the path builder. Dates are passed in. `belfort/learn/game.py` is the thin SQLite layer around it; `belfort/learn/router.py` gains `/path`, `/lessons/{id}/check`, `/tests/{kind}/{key}`, `/sessions/{id}/grade`, `/weak-spots`, `/goal` and `/placement/dismiss`. Thresholds are named constants in `belfort/settings.py`.
- **Exercise types:** `curriculum.py` validates and grades `mc`, `tf`, `order` and `number`. The public quiz payload has no answers; `order` items are shuffled on the server; grading is server side.
- **Locks:** the API returns 403 with a friendly sentence for the content, check and quiz of a lesson in a locked stage, and for starting a checkpoint or stage test there. Beginner is always open.
- **Database:** migration 7 adds `learn_profile`, `learn_xp_days`, `learn_lessons`, `learn_tests`, `learn_weak` and `learn_sessions`, each with `user_id` (default `local`).
- **UI:** new `belfort/static/learn-game.js` and `learn-game.css` (path, lesson cards, exercises, results, confetti) and two still mascot PNGs for reduced motion. Only `index.html` changed (a link and a script tag).

### Decisions
- **Stage order:** stage comes from each module's `stage`; inside a stage, syllabus order. Safety is in the file under the Advanced track but is shown in Beginner.
- **Planned lessons** show as "coming soon" nodes and are not counted toward stage progress or the stage test, so unwritten Safety and Taxes lessons do not block anyone.
- **Stage test and checkpoints** open once every written lesson in the module or stage is done. Checkpoint: up to 8 questions from the module. Stage test: up to 12 from the stage. Both sample evenly across lessons. Pass mark 80%; 20 XP only on the first pass.
- **Placement test** is 12 questions from Beginner, offered on first open, and unlocks Intermediate only. Advanced always needs the Intermediate stage test.
- **Lessons in an unlocked stage are all open** (order is not forced); the first not-done node is highlighted as next. Once a stage test is passed, leftover checkpoints in that stage are not highlighted.
- **A lesson completes at 60%** (as before). Tests are graded all at once with no hearts lost; hearts are lost only on instant-feedback answers inside lessons. If hearts reach zero mid-lesson the run ends without XP.
- **XP:** 10 for a first completion, +5 for no mistakes, 5 for replaying a done lesson, 5 for a Weak spots review. Streak counts days the daily goal was met; a missed day spends a freeze if one is held; one freeze is earned at each multiple of 7 days, up to two.
- **Hearts:** 5 a day, refilled lazily when the date changes. With none left a new lesson cannot be started; a Weak spots review (up to 8 questions you missed) refills them when finished, whatever the score.
- **Test sessions:** a checkpoint, stage test, placement test or review is a server-side session of question references, graded once, so a page cannot grade a hand-picked easy subset.
- **Old progress counts:** rows in `lesson_progress` are treated as done for the local user, and finished lessons are still written there for the local user.
- **Order exercises** use tap-to-order (no drag), which also works on touch screens.
- **Hooks into other files:** the old Learn loader in `verticals.js` is left in place; `learn-game.js` loads after it, replaces `onView.learn` and makes `renderSyllabus` a no-op.
- **Tests:** an existing test now looks for a planned lesson in the Beginner stage, because planned lessons in locked stages answer 403 before 404.
## 2026-11-28 — T21 taxes and records lessons (Sarthak's agent)

### Changes
- `content/learn/lessons/capital-gains.md` and `records.md`: the two Taxes and records lessons, each with a quiz and a Sources line. Facts checked: STCG 20%, LTCG 12.5% above 1.25 lakh and the 12-month rule (Budget 2024, effective 23 July 2024, unchanged in Budget 2026 reporting), STT on delivery trades, loss set-off and 8-year carry-forward (Income Tax Department), intraday as speculative and F&O as non-speculative business income, ITR-2 against ITR-3.
- Left out because sources disagreed or could not be verified: tax audit turnover thresholds, exact reassessment time limits (the lesson says to check the current rule), exact STT percentages (the lesson points to the official sites).
- `content/learn/syllabus.json`: removed `planned` from both lessons. `belfort/core/glossary.py`: added STCG, LTCG, ITR.
- `CHANGELOG.md`, `docs/STATUS.md`, `docs/ABOUT.md`, `docs/TASKS.md`: 35 of 38 lessons written; T21 Done.
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
