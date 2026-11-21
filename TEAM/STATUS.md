# Status and known limitations

> Temporary file for the founders. Last updated 21 November 2026.

## Verified

- 68 automated tests pass, offline (`python -m pytest -q`).
- Each section was clicked through in a browser against live data on 21 November 2026: a research report, a lesson with its example chart and quiz, a paper order, a chart replay, the news page with tip filtering.

## Not verified yet

- **Ask Belfort with a real AI key.** Only simulated replies have been tested (task T02).
- **Phones and tablets.** The new screens were checked only at desktop width (task T11).
- **macOS and Linux.** Developed and run on Windows only.
- **The Windows desktop launcher** (`run.bat`, `run_desktop.py`) was carried over from Belfort AI with renamed paths but not re-run.

## Known limitations

| Area | Limitation | Task |
|---|---|---|
| Data | Yahoo Finance and NSE archive files are unofficial sources and can change or block access. Statements cover about four years. | D4 |
| Practice | Each portfolio load fetches bars for every open symbol. | T08 |
| Practice | The replay trainer sends hidden bars to the browser before the decision. | T09 |
| Practice | Long only, one account, end-of-day fills, no trailing stops. | Roadmap v0.4 |
| Learn | 8 of 38 lessons written. | T03 to T05 |
| News | Company tags cover only about 130 built-in stocks. The tip filter is a list of patterns and will miss some phrasing. | T14 |
| Research | Rule thresholds can be changed only in code. | T13 |
| Front end | No browser tests; JavaScript is checked only by clicking through. | T10 |
| Brand | The sidebar still says "Belfort AI". | D2 |

## Where things came from

The Research engine, front-end shell and design came from the private Belfort AI repository (`sarthakviche/belfort-ai`), which stays as it is. Everything else was written for this repository.
