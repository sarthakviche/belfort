---
title: Market hours, circuits and gaps
minutes: 5
objectives: Know when NSE's equity sessions open and close | Explain stock price bands and market-wide circuit breakers | See why a stop can fill worse than its price after a gap
---
An end-of-day trader does not watch the screen all day, but the timetable still decides when an order can fill.

## The trading day on NSE

| Session | Time (IST) |
|---|---|
| Pre-open order entry | 9:00 to 9:08 |
| Normal market | 9:15 to 15:30 |
| Closing session | 15:40 to 16:00 |

The opening price comes out of the **pre-open session**, where orders are collected and matched at one price. That is the open Belfort's paper account fills market orders at.

## Price bands on single stocks

Most stocks have a daily **price band** of 2%, 5%, 10% or 20% either way. Once price reaches it, trading continues only inside the band, so a stock can sit at its upper or lower **circuit** with few sellers or buyers. Stocks that have futures and options have no fixed band.

## Circuits for the whole market

If the Nifty 50 or the Sensex moves 10%, 15% or 20% in a day, trading halts across the market. A 10% move before 1 pm halts trading for 45 minutes; a 20% move closes the market for the day.

## Why this matters for your stop

A stop only works while the stock is trading. If bad news arrives overnight, the next open can be far below your stop: a **gap**. Your exit is then the open, not the stop price. Belfort's paper account fills exactly like this, so you see the real cost of gaps.

Sources: NSE market timings (updated 11 November 2026), NSE circuit breakers and NSE price bands pages, read 22 November 2026.

::try paper

```quiz
[
  {"q": "When does NSE's normal equity market session run?", "options": ["9:00 to 15:00", "9:15 to 15:30", "10:00 to 16:00"], "answer": 1, "why": "Normal market hours are 9:15 to 15:30 IST, after the pre-open session."},
  {"q": "A stock with a 10% price band rises 10% by noon. What happens?", "options": ["Trading stops for the whole market", "It can only trade inside the band for the rest of the day", "The band doubles"], "answer": 1, "why": "A price band caps the day's move for that stock; it does not halt the market."},
  {"q": "Your stop is at 95. The stock closes at 97, then opens at 90 after bad news. Where does a stop order exit?", "options": ["At 95", "Near the open of 90", "It does not exit"], "answer": 1, "why": "Price never traded between 97 and 90, so the first available price is the open. That is a gap."}
]
```
