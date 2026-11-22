# Status and known limitations

> What works today and what does not. Last updated 22 November 2026. Update it in any PR that changes what is true here.

## Verified

- 81 automated tests pass offline, with 74% coverage (`python -m pytest --cov`); Ruff lint and format are clean. CI runs the tests on Windows and Linux.
- The contributor setup was followed on a clean clone on Windows 11 with Python 3.12.4 on 22 November 2026: setup, hooks, tests and the app all worked.
- Each section was clicked through in a browser against live data on 21 November 2026: a research report, a lesson with its example chart and quiz, a paper order, a chart replay, the news page with tip filtering.

## Not verified yet

- **Ask Belfort with a real AI key.** Error paths were checked live on 22 November 2026 (wrong Gemini key, wrong OpenAI key, local Ollama not running) and now say what to do. A successful answer from a real provider for a report, a lesson and a news story is still untested (T02).
- **Small windows and keyboard-only use** (T32).
- **The Windows desktop launcher** (`run.bat`, `run_desktop.py`) was carried over from Belfort AI with renamed paths but not re-run. It is replaced by T36.
- **Platforms.** Launching for Windows only; macOS and Linux are not targets for 1.0.

## Known limitations

| Area | Limitation | Task |
|---|---|---|
| Practice | Long only, one account, end-of-day fills | |
| Learn | 11 of 38 lessons written | T14 to T22 |
| News | Company tags cover only about 130 built-in stocks; the tip filter is a pattern list and will miss some phrasing | T28 |
| Research | Rule thresholds can be changed only in code | T25 |
| Front end | No browser tests; JavaScript is checked only by syntax check and clicking through | T31 |
| Packaging | Needs Python; data is stored next to the code; fonts and the chart library load from CDNs | T35 to T38 |
| Data | Yahoo Finance and NSE archive files are unofficial and can change or block access | D4 |
| Brand | The sidebar still says "Belfort AI" | D2, T41 |

## Where things came from

The Research engine, front-end shell and design came from the private Belfort AI repository (`sarthakviche/belfort-ai`), which stays as it is. Everything else was written for this repository.
