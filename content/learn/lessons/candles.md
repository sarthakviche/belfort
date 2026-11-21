---
title: Candles: one session in one shape
minutes: 6
objectives: Read open, high, low and close from a candle | Tell a strong close from a weak one | Know why one candle alone means little
---
Each **candle** on a daily chart is one trading session squeezed into one shape. It shows four prices:

- **Open**: the first trade of the day.
- **High** and **Low**: the furthest price went up and down.
- **Close**: the last price of the day, the one most traders watch.

The thick part is the **body**, between open and close. In Belfort, a body is green when the close is above the open and red when it is below. The thin lines above and below are the **wicks**: prices that traded but did not hold.

## What a candle tells you

| Shape | What happened in the session |
|---|---|
| Long green body, small wicks | Buyers were in control from open to close |
| Long red body, small wicks | Sellers were in control all day |
| Long lower wick, close near the high | Price fell, then buyers pushed it back up |
| Long upper wick, close near the low | Price rose, then sellers pushed it back down |
| Tiny body, wicks both sides | Indecision: neither side won |

## The honest part

One candle is one day of noise. Books give dozens of named candle patterns, but on liquid stocks most of them predict very little on their own. Candles matter **in context**: a strong close at a support level in an uptrend means more than the same candle in the middle of nowhere. The next lessons build that context.

Here is a real chart from at least 30 days ago. Find one day where price fell during the session but closed near its high.

::chart HDFCBANK 90

::try replay

```quiz
[
  {"q": "Which price does the thick body of a candle span?", "options": ["High to low", "Open to close", "Yesterday's close to today's close"], "answer": 1, "why": "The body runs from the open to the close. Wicks show the high and low."},
  {"q": "A candle has a long lower wick and closes near its high. What happened?", "options": ["Price rose all day", "Price fell during the session, then buyers pushed it back up", "Nothing traded"], "answer": 1, "why": "The lower wick shows prices that traded but did not hold; the close near the high shows buyers took over."},
  {"q": "How much should you rely on a single candle pattern?", "options": ["Fully: named patterns are reliable", "Little on its own; it matters in the context of trend and levels", "Never look at candles"], "answer": 1, "why": "On liquid stocks, single candles predict little alone. Context gives them meaning."}
]
```
