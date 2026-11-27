---
title: Market, limit and stop-loss orders
minutes: 7
objectives: Choose between a market and a limit order | Know what a stop-loss order does and does not protect | Understand how Belfort's practice account fills orders
---
An **order** is an instruction to your broker. Three kinds cover almost everything a swing or positional trader needs.

## Market order

Buy or sell **now**, at whatever price is available. You are certain to get filled, but not certain of the price. In a busy large-cap stock the difference is tiny. In a thinly traded small company it can be large.

## Limit order

Buy **at this price or lower** (or sell at this price or higher). You control the price, but the order may never fill if the market does not come to you.

| | Market order | Limit order |
|---|---|---|
| Fill | Almost certain | Only if price reaches your limit |
| Price | Whatever is available | Your price or better |
| Good for | Liquid stocks, getting out fast | Planned entries near support |

## Stop-loss order

A **stop-loss** is an exit order that waits below the price. If price falls to your stop, it triggers and sells. It turns "I will sell if I am wrong" into something that happens without you watching the screen.

Two warnings:

1. A stop does **not promise your price**. If a stock closes at ₹500 and opens next morning at ₹460 on bad news, a stop at ₹480 fills near ₹460. This is called a **gap**.
2. A stop placed too close gets hit by ordinary daily wiggles. The stop-loss lesson shows how to place it using the chart and the stock's normal range (ATR).

## How Belfort's practice account fills orders

Belfort uses **end-of-day** prices, so practice orders behave like orders placed after the close:

- A market order fills at the **next session's open**.
- A limit order fills on the first later session whose low reaches your limit. It expires after five sessions.
- Your stop and target are checked every session. If the open jumps past your stop, the exit is at the open, exactly like a real gap.

::try paper

```quiz
[
  {"q": "You want to buy only if the price comes down to ₹1,240. Which order fits?", "options": ["Market order", "Limit order at ₹1,240", "Stop-loss order at ₹1,240"], "answer": 1, "why": "A limit buy fills at your price or lower, and only if the market gets there."},
  {"q": "Your stop is at ₹480. The stock closes at ₹500 and opens at ₹460 the next day. Roughly where does the stop fill?", "options": ["₹480 exactly", "Near ₹460", "It does not fill"], "answer": 1, "why": "A gap jumps past the stop, so it fills at the first available price, near ₹460."},
  {"q": "In Belfort's practice account, when does a market order placed today fill?", "options": ["Instantly at today's close", "At the next session's open", "At the end of the week"], "answer": 1, "why": "Practice uses end-of-day data, so orders fill at the next session's open."},
  {"type": "number", "q": "You hold 100 shares bought at ₹500 with a stop at ₹480. Bad news makes the stock open at ₹460 and the stop exits at the open. What is the loss in rupees?", "answer": 4000, "tolerance": 0, "unit": "₹", "why": "A stop does not promise your price. The exit is at the open of ₹460, so the loss is (500 − 460) × 100 = ₹4,000, not ₹2,000."},
  {"type": "tf", "q": "A stop-loss order always exits you at exactly your stop price.", "answer": false, "why": "If a stock gaps past the stop, the order fills near the new price, not at the stop."}
]
```
