---
title: Chart patterns and what the backtest shows
minutes: 8
objectives: Name the patterns Belfort's detectors look for | Read the pattern table in the research report | Explain why a pattern must beat a random-entry baseline before it means anything
---
Double tops, head and shoulders, triangles, cup and handle: chart patterns fill trading books, each with a "measured target". The question that matters is simple. When the pattern appears on real charts, does price reach the target more often than it would from a random day?

## How Belfort tested its own detectors

Belfort finds eight classic patterns automatically. To see whether they add anything, the app was tested in two ways, and the results appear at the bottom of every research report.

1. **Textbook shapes:** 200 computer-drawn examples of each pattern with noise added, plus 600 random charts with no pattern. This shows whether the code finds the shape, and how often it "sees" one in noise.
2. **Real history:** every newly confirmed pattern on 47 large NSE stocks from November 2021 to November 2026, followed until price reached the measured target, hit the invalidation price, or the holding window ended. The **baseline** takes random entry days in the same stocks with the same target and stop distances.

## What the swing test found (30 sessions)

| Pattern | Signals | Reached target first | Random-entry baseline |
|---|---|---|---|
| Double bottom (W) | 148 | 62% | 57% |
| Double top | 147 | 36% | 43% |
| Cup and handle | 168 | 8% | 14% |
| Head and shoulders | 77 | 17% | 13% |
| Inverse head and shoulders | 56 | 32% | 32% |
| Ascending triangle | 34 | 32% | 30% |
| Descending triangle | 39 | 18% | 22% |
| Symmetrical triangle | 42 | 19% | 14% |

## How to read it

- No pattern beats the baseline by a clear margin on a large sample. Several do worse than random days.
- The double bottom's high figure comes with a close target: its median reward-to-risk was 0.63, so reaching the target often still paid little against the stop.
- Samples under 30 signals are marked with a star in the report as too few to trust.
- The test leaves out costs and slippage, and it uses today's large companies, which flatters the results. Past results do not predict future ones.

That is why patterns are **not** used in Belfort's label. The report still draws them, because traders talk about them and you should recognise them, but a pattern name is never treated as an edge by itself.

## What to do with a pattern

Use it to describe the chart and to find levels: the neckline of a head and shoulders or the top of a triangle is often a support or resistance level. Then plan the trade like any other, with a stop, a size and room to the next level.

::try research

```quiz
[
  {"q": "What is the random-entry baseline in Belfort's pattern test?", "options": ["Random days in the same stocks with the same target and stop distances", "The Nifty 50's return", "A pattern drawn by hand"], "answer": 0, "why": "The baseline asks how often the same target would be reached from an ordinary day. A useful pattern must clearly beat it."},
  {"q": "In the swing test, cup and handle reached its target first 8% of the time against a 14% baseline. What does that suggest?", "options": ["It is a strong signal", "It did worse than random entry days in this test", "It cannot be measured"], "answer": 1, "why": "8% is below the 14% that random days achieved with the same target and stop."},
  {"q": "Why does Belfort leave chart patterns out of its label?", "options": ["They are hard to draw", "Its own backtest found no clear edge over random entries", "SEBI bans them"], "answer": 1, "why": "On a large sample, no pattern clearly beat the random-entry baseline, so a pattern name alone is not treated as evidence."}
]
```
