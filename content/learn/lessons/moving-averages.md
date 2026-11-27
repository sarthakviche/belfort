---
title: Moving averages without the mystery
minutes: 6
objectives: Calculate a simple moving average by hand | Read price against the 20, 50 and 200-day averages | Know what a moving average cannot tell you
---
A **moving average** is the average closing price over the last few sessions, recalculated every day. The 20-day average is the sum of the last 20 closes divided by 20. Tomorrow the oldest close drops out and the newest one comes in, so the line moves.

## Why traders use them

A single day's price is noisy. The average smooths that noise into a line that shows the direction of the last few weeks or months:

| Average | Roughly covers | Used for |
|---|---|---|
| 20-day | One month | Swing trades |
| 50-day | One quarter | Swing and positional trades |
| 200-day | About ten months | Positional trades and the long-term trend |

## What Belfort reads from them

- **Price above a rising average:** recent closes are higher than older ones. Combined with higher highs and higher lows, this is an established uptrend.
- **Fast average above slow average** (20 above 50, or 50 above 200): the shorter-term trend agrees with the longer one.
- **Price below a falling average:** the opposite, and Belfort's rule excludes the trade.

## What averages cannot do

An average is built only from past closes, so it always lags. It turns after price has turned. A crossover of two averages is not a forecast; it is a summary of what already happened. Treat averages as a way to describe the trend, then plan the entry, stop and size from swing points and your risk.

In this past chart, estimate where the 50-day average would run. Is price mostly above it or below it?

::chart RELIANCE 220

::try research

```quiz
[
  {"q": "The last five closes are 100, 102, 101, 104 and 103. What is the 5-day simple moving average?", "options": ["102", "103", "104"], "answer": 0, "why": "100 + 102 + 101 + 104 + 103 = 510, and 510 divided by 5 is 102."},
  {"q": "Why does a moving average lag behind price?", "options": ["It is calculated from past closes only", "Exchanges delay it", "It uses tomorrow's price"], "answer": 0, "why": "Each value is an average of earlier closes, so it changes direction after price does."},
  {"q": "Price is above a rising 50-day average and makes higher highs and higher lows. How does Belfort describe this?", "options": ["A downtrend", "An established uptrend", "A sure sign it will keep rising"], "answer": 1, "why": "Those conditions describe an established uptrend. They describe the past, not a promise about the future."},
  {"type": "number", "q": "The last 20 closes of a stock add up to ₹10,400. What is the 20-day moving average?", "answer": 520, "tolerance": 0, "unit": "₹", "why": "The average is the sum of the closes divided by 20: 10,400 ÷ 20 = ₹520."},
  {"type": "tf", "q": "A crossover of two moving averages is a forecast of where price goes next.", "answer": false, "why": "Averages use only past closes, so a crossover summarises what already happened."}
]
```
