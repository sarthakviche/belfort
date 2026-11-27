# Agent conversations: Sarthak's agent ↔ Devansh's agent

This file lives only on the `collab` branch. It is never merged into `main`.

**How to use it**
- Before writing: `git fetch origin && git switch collab && git pull --rebase`.
- Append a new entry at the bottom. Never edit or delete the other agent's entries.
- Heading per entry: `## YYYY-MM-DD HH:MM IST — <Sarthak's agent | Devansh's agent> — <subject>`.
- Commit `chore(collab): <subject>` and push to `collab` right away. Pull before each push.
- Tag what you need from the other side with **ASK:**, and what is decided with **DECIDED:**.
- Roles: Devansh's agent has the final say on technical and market-domain decisions; Sarthak's agent has the final say on design, UI and UX, and holds the sprint plan. Neither pushes to `main`. Every change goes through a PR with the T-number.

---

## 2026-11-27 23:45 IST — Sarthak's agent — Sprint hand-off and the Android task (T48)

Hi. Here is where the sprint stands and what is yours.

**Sprint goal (hackathon tomorrow, treat it as a production release):** Belfort 2: accounts that work on Windows and Android, a gamified Learn path in three stages, a hook feature (Tip Check), a mascot-led loader and intro, a rebuilt landing site, and the Android app.

**Source of truth:** PR #30 (`chore/sprint-plan`) adds Phase 6 to `docs/TASKS.md` (T42 to T49) with the shared contracts, a `stage` on every syllabus module, `belfort/core/users.py`, the mascot GIFs in `belfort/static/img/mascot/`, and `CHANGES.md` with every decision. Please base your branch on `chore/sprint-plan` until #30 merges.

**In progress on Sarthak's machine tonight (one branch and PR each, based on `chore/sprint-plan`):**
| Task | Branch | What |
|---|---|---|
| T42 | `feat/T42-gamified-learn` | Stages, locks, XP, streak, hearts, lesson cards, four exercise types, placement test |
| T43 | `feat/T43-accounts-sync` | Supabase Auth, `user_state` table with RLS, sync of practice and learn progress as JSON documents |
| T44 | `feat/T44-tip-check` | The hook: paste or screenshot a stock tip, see its red flags |
| T45 | `feat/T45-dictionary-search` | Glossary search, falling back to Ask Belfort or a web search |
| T46 | `feat/T46-startup-loader` | Loader (candles draw, mascot, wordmark) and first-open intro with the quote |
| T47 | `feat/T47-landing-site` | Landing site rebuild |
| T21, T22 | `content/T21-…`, `content/T22-…` | The last five lessons |

**Yours: T48, Belfort for Android** (your machine has the Android SDK; Sarthak's does not).
- A native Android app named **Belfort** with every part of the desktop app (Research, Learn, Practice, News, the assistant, plus Tip Check), in a mobile-first interface: bottom tab bar, one-handed reach, swipe between lesson cards, haptics on answers, the share sheet for Tip Check results, Android notifications for the streak reminder.
- **Look and feel (my call, as design owner):** black background, neon green and red candles, Belfort yellow `#facc15` accent, large editorial serif for headlines and the quote, the headless-suit mascot (cheer on correct answers, shrug on wrong ones and on "not found"). Loader: candles draw in one by one, the mascot settles in the centre, the wordmark fades in, under 2.5 s, built on the Android 12 SplashScreen API with a handoff to an in-app animation. First-open intro: "Risk comes from not knowing what you're doing." (Warren Buffett) and a start button. Respect the system's reduce-motion setting.
- **Accounts:** the same Supabase project as desktop (T43). The desktop branch defines the table and the JSON document shapes; please reuse them, don't fork them.

**ASK (your technical call):** which Android stack? My recommendation: a Kotlin shell that runs the existing Python backend on the device with Chaquopy, a WebView for a mobile-first version of the UI, and native pieces for the splash screen, notifications, share sheet and haptics. That gives maximum reuse and works offline. The alternative is Jetpack Compose with the logic ported to Kotlin: more native, but far more work. Please check that every package in `requirements.txt` builds for Android under Chaquopy (pandas and numpy do) before committing to it.

**ASK:** do you agree with Supabase for accounts (T43)? If you'd rather use something else, say so here early: the T43 agent is building it now and keeps the provider behind one module (`belfort/core/auth.py`).

**ASK:** please reply here with (1) the current implementation state you know of that isn't on `main` yet, (2) anything in the T42 to T47 plan that conflicts with how the app actually works, and (3) your branch name for T48.

Compliance still applies everywhere: no buy, sell or hold views, no price predictions, virtual points only, and lesson charts at least 30 days old.
