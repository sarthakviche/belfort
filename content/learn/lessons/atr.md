---
title: ATR: how far a stock normally moves
minutes: 5
objectives: Work out a day's true range | Read ATR as a stock's normal daily movement in rupees | See where Belfort uses ATR for stops, entries and trailing
---
Two stocks both trade at ₹500. One usually moves ₹4 a day, the other ₹20. A ₹10 stop is wide for the first and inside the daily noise of the second. **ATR**, the average true range, measures that normal daily movement so you can size stops to the stock.

## True range

For each day, the **true range** is the largest of three distances:

1. Today's high minus today's low.
2. Today's high minus yesterday's close.
3. Yesterday's close minus today's low.

The second and third catch gaps: if a stock closed at ₹500 and today traded between ₹515 and ₹525, the day's range is ₹10 but the true range is ₹25.

**ATR** is a smoothed average of the true range, usually over 14 days. Belfort uses 14.

## Where Belfort uses it

| Place | How ATR is used |
|---|---|
| Suggested stop | Half an ATR below the nearest support; if there is none, 1.5 ATR (swing) or 3 ATR (positional) below the close |
| Entry area | Within 1 ATR above the fast average, or 1.5 ATR of support |
| Not stretched | No more than 3 ATR above the fast average |
| Trailing stop in Practice | 0.5 to 6 ATR below each close |

## What ATR does not tell you

ATR has no direction. A high ATR means the stock moves a lot, up or down. It also changes: ATR usually rises after big news and falls in quiet spells, so a stop that fit last month may be too tight today.

::try research

```quiz
[
  {"q": "Yesterday's close was ₹200. Today's high is ₹204 and low is ₹190. What is today's true range?", "options": ["₹4", "₹10", "₹14"], "answer": 2, "why": "High minus low is ₹14, which is larger than ₹4 (high minus close) and ₹10 (close minus low)."},
  {"q": "With no support nearby, where does Belfort suggest a swing stop if ATR is ₹12 and the close is ₹400?", "options": ["₹382", "₹388", "₹364"], "answer": 0, "why": "1.5 × ₹12 = ₹18 below the close: ₹400 − ₹18 = ₹382."},
  {"q": "What does a rising ATR tell you?", "options": ["The price will rise", "The stock is moving more each day, in either direction", "The company is growing"], "answer": 1, "why": "ATR measures the size of daily moves, not their direction."}
]
```
