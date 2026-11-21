---
title: Where the stop goes, and why it never moves down
minutes: 7
objectives: Place a stop where the trade idea is proved wrong | Use ATR to avoid stops that are too tight | Know the one rule about moving stops
---
A stop-loss is not a number you pick to feel safe. It is the price at which **your reason for the trade is gone**.

## Place it at the invalidation

Ask: what would prove me wrong? For a trade bought near support in an uptrend, the answer is "price closes below that support". So the stop goes just **below the support zone**, not at an arbitrary 5%.

## Give it room: ATR

Every stock wiggles. **ATR** (average true range) measures how far a stock normally moves in a day. A stop closer than about one ATR from your entry is likely to be hit by ordinary noise even when your idea is right. Belfort suggests a stop below the nearest support, with an ATR-based fallback when there is no clear level.

If the sensible stop is far away, the position must be smaller (see the sizing lesson). If it is so far that the trade no longer makes sense, skip the trade. Belfort's research rule caps the stop at 8% for swing trades and 15% for positional ones.

## The one rule

**Never move a stop down.** Moving the stop lower after entry means accepting a bigger loss than you planned, on a trade that is already going wrong. You may move it **up** as the trade works (a trailing stop), never down.

## When the stop is hit

Exit. A stop-out is not a failure; it is the plan working. A small planned loss is the cost of finding out you were wrong. The failure is the unplanned large loss that comes from removing the stop.

Practise it: in the replay trainer, set your stop below the nearest support before you see what happens next.

::try replay

```quiz
[
  {"q": "Where does the stop belong on a trade bought near support?", "options": ["Exactly 5% below entry", "Just below the support zone, where the idea is proved wrong", "Above the entry"], "answer": 1, "why": "The stop goes where the trade's reason is invalidated."},
  {"q": "A stock's ATR is ₹12. Your stop is ₹4 below entry. What is the likely problem?", "options": ["The stop is too wide", "Ordinary daily noise will probably hit it", "Nothing"], "answer": 1, "why": "A stop much tighter than one ATR is usually hit by normal movement."},
  {"q": "Price is falling toward your stop. What does the plan say?", "options": ["Move the stop lower to give it room", "Leave the stop; exit if it is hit", "Buy more to average down"], "answer": 1, "why": "Never move a stop down. Exiting at the planned stop keeps the loss small."}
]
```
