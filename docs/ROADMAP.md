# Roadmap

Belfort is free and open source under the MIT licence. Priority one is a Windows 1.0 that anyone can install. Dates are targets, not promises. Day-to-day work items live in [docs/TASKS.md](../docs/TASKS.md).

## v0.1: foundation (done, November 2026)

- [x] New repository with a modular layout: `research`, `learn`, `practice`, `news`, `assistant`, `core`
- [x] Research report and screens carried over from Belfort AI, with descriptive labels and neutral screen names
- [x] Learn: screened syllabus (3 tracks, 12 modules, 38 lessons planned), 8 lessons written, quizzes, progress, streaks, lagged example charts
- [x] Practice: paper account with end-of-day fills, stops, targets, costs and trade reviews; prediction journal with Brier scoring, calibration and badges; chart-replay trainer
- [x] News: RSS from five publishers and the RBI, categories, company tags, hover definitions, "Explain this", tip-style headlines hidden
- [x] Bring-your-own-key assistant: Gemini or any OpenAI-compatible service, including a local Ollama
- [x] Compliance principles in code and in docs; 68 tests; CI workflow; contributor templates

## v0.2: first release (target: mid-December 2026)

- [ ] Decide licence and pricing (see the note in COMPLIANCE.md)
- [ ] Securities lawyer review of COMPLIANCE.md and the app wording
- [ ] Windows installer (no Python needed) and a release on GitHub Releases
- [ ] Finish the Foundations track (6 planned lessons) and add replay drills linked to lessons
- [ ] Position-size helper inside the practice order form
- [ ] User-editable rule profiles for Research (thresholds read from a file, shown in the report)
- [ ] README screenshots, landing page on GitHub Pages, "good first issue" list, GitHub Discussions on

## v0.3: Learn depth (January 2027)

- [ ] Practitioner track lessons (setups, business check, indicators, journal)
- [ ] Module checkpoints and a printable progress summary
- [ ] Lesson content linter in CI (quiz shape, wording, lagged charts)
- [ ] Translation support, Hindi first

## v0.4: Practice depth (February 2027)

- [ ] Trailing stops and partial exits
- [ ] Journal analytics: mistake tags, R distribution, performance by setup
- [ ] Total open risk across positions
- [ ] Export and import of the journal (CSV, JSON)

## v0.5: Research and News (March 2027)

- [ ] Watchlists and local alerts on rule conditions (shown only inside the app)
- [ ] Market context panel: index trend, breadth, sector strength
- [ ] NSE corporate announcements and an events calendar (results, RBI policy)
- [ ] News for the stock on screen inside its report

## v1.0: stable (mid-2027)

- [ ] macOS and Linux packages
- [ ] Stable data-provider plugin API with user-keyed broker data
- [ ] Accessibility audit and browser smoke tests
- [ ] Documentation site

## Not planned

See "Things the project will not build" in [COMPLIANCE.md](COMPLIANCE.md).
