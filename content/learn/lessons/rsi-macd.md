---
title: RSI and MACD: momentum, not prophecy
minutes: 7
objectives: Explain what RSI and MACD are built from | Read the momentum line in Belfort's report | Know why neither indicator decides Belfort's label
---
**Momentum** is how fast price has been moving and in which direction. RSI and MACD are the two most common ways to measure it. Both are calculated from past closing prices only, so they describe what has happened, quickly and in one number.

## RSI: the Relative Strength Index

RSI compares the size of recent up-days with recent down-days, usually over 14 days, and scales the result from 0 to 100.

| RSI(14) | What it says about the last few weeks | Belfort's wording |
|---|---|---|
| 70 or above | Gains have been much larger than losses | Stretched to the upside |
| 30 to 70 | A mix of up and down days | In the middle of its range |
| 30 or below | Losses have been much larger than gains | Weak |

Many people call RSI above 70 "overbought" and expect a fall. In a strong uptrend RSI can stay above 70 for weeks, and in a downtrend it can sit below 30. A high reading describes a fast rise; it does not say the rise is over.

## MACD

**MACD** subtracts a slower average of price from a faster one: the 12-day exponential average minus the 26-day one. When the fast average pulls away above the slow one, MACD rises. A 9-day average of MACD itself is called the **signal line**.

- MACD **above** its signal line: recent momentum has been picking up.
- MACD **below** its signal line: recent momentum has been fading.

Because it is built from moving averages, MACD lags. A cross often comes after much of a move has already happened.

## How Belfort uses them

The report's momentum line reads like this: "RSI(14) is 64 (in the middle of its range); MACD is above its signal line." That is context. Neither number is part of the checks behind the label. Trend, entry area, stretch, stop distance, room to resistance, results dates and the business check decide the label, because those connect to a stop and a size.

## A sensible way to use momentum

- Treat a very high RSI like the "not stretched" check: the stock has run fast, so a nearby stop is hard to find.
- Treat a MACD cross as a description of the last few weeks, not a signal to act.
- Never use either one without a plan for the stop.

::try research

```quiz
[
  {"q": "RSI(14) has been above 70 for three weeks while the stock makes higher highs. What does that tell you?", "options": ["A fall must start now", "Gains have been much larger than losses recently", "The company's profits rose"], "answer": 1, "why": "RSI only compares recent up and down moves. In strong uptrends it can stay above 70 for a long time."},
  {"q": "What is MACD built from?", "options": ["Volume and delivery", "The difference between a 12-day and a 26-day average of price", "Quarterly profits"], "answer": 1, "why": "MACD is the fast exponential average minus the slow one; its 9-day average is the signal line."},
  {"q": "Does RSI or MACD change Belfort's label?", "options": ["Yes, RSI above 70 excludes the trade", "No, they are shown as context only", "Only MACD does"], "answer": 1, "why": "The label comes from checks that connect to a stop and a size. Momentum is shown for context."},
  {"type": "number", "q": "A stock's 12-day exponential average is ₹505 and its 26-day exponential average is ₹498. What is its MACD?", "answer": 7, "tolerance": 0, "unit": "₹", "why": "MACD is the 12-day average minus the 26-day one: 505 − 498 = 7."},
  {"type": "tf", "q": "An RSI reading above 70 means the rise is over and a fall is coming.", "answer": false, "why": "In a strong uptrend RSI can stay above 70 for weeks. A high reading describes a fast rise; it does not say the rise is over."}
]
```
