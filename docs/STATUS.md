# Status and known limitations

> What works today and what does not. Last updated 28 November 2026. Update it in any PR that changes what is true here.

## Verified

- 191 automated tests pass offline, with 83% coverage (`python -m pytest --cov`); Ruff lint and format are clean. CI runs the tests on Windows and Linux.
- The contributor setup was followed on a clean clone on Windows 11 with Python 3.12.4 on 22 November 2026: setup, hooks, tests and the app all worked.
- The gamified Learn path (T42) was clicked through in the built-in browser on 28 November 2026: the path, a lesson as cards with every exercise type, a wrong answer losing a heart, a locked lesson refused with 403, the placement test unlocking Intermediate, a checkpoint with its review screen, and the out-of-hearts screen. Reduced-motion behaviour was reviewed in code only; it was not tried with the system setting on.
- Each section was clicked through in a browser against live data on 21 November 2026: a research report, a lesson with its example chart and quiz, a paper order, a chart replay, the news page with tip filtering.

## Not verified yet

- **Dictionary fallbacks in the Windows window.** "Ask Belfort" with a real key and "Search the web" from inside the pywebview window (it asks the backend to open the system browser) were exercised only with a faked provider and in a normal browser (T45).

- **Ask Belfort with a real AI key.** Error paths were checked live on 22 November 2026 (wrong Gemini key, wrong OpenAI key, local Ollama not running) and now say what to do. A successful answer from a real provider for a report, a lesson and a news story is still untested (T02).
- **Small windows and keyboard-only use** (T32).
- **The Windows desktop launcher** (`run.bat`, `run_desktop.py`) was carried over from Belfort AI with renamed paths but not re-run. It is replaced by T36. T46 changed it to show a loader first (`belfort/static/splash.html`) and load the app when the server answers; that flow was exercised in the browser, not in the pywebview window.
- **Platforms.** Launching for Windows only; macOS and Linux are not targets for 1.0.

## Known limitations

| Area | Limitation | Task |
|---|---|---|
| Practice | Long only, one account, end-of-day fills | |
| Learn | 36 of 38 lessons written. Existing lessons only have multiple-choice exercises; the true or false, order and number types work but wait for content | T21 to T22, T49 |
| Learn | Stage progress is per local user; XP, hearts and streaks use the device's date. Moving between devices waits for accounts | T43 |
| News | Company tags cover only about 130 built-in stocks; the tip filter is a pattern list and will miss some phrasing | T28 |
| Research | Rule thresholds can be changed only in code | T25 |
| Front end | No browser tests; JavaScript is checked only by syntax check and clicking through | T31 |
| Packaging | `Belfort.exe` builds and runs (single file, unsigned, no installer or uninstaller yet); fonts still load from Google Fonts | T36, T38, T39, D7 |
| Data | Yahoo Finance and NSE archive files are unofficial and can change or block access | D4 |
| Brand | The sidebar still says "Belfort AI" | D2, T41 |

## Where things came from

The Research engine, front-end shell and design came from the private Belfort AI repository (`sarthakviche/belfort-ai`), which stays as it is. Everything else was written for this repository.
