---
title: Thinking in R: results as multiples of risk
minutes: 6
objectives: Express any trade's result as a multiple of its planned risk | Read the Win rate and Average R cards in Practice | See why a low win rate can still add up when winners are larger than losers
---
Rupee results are hard to compare. A ₹3,000 gain on a trade that risked ₹1,000 is a very different result from ₹3,000 on a trade that risked ₹10,000. Traders solve this by measuring every result in **R**: one R is the amount you planned to lose if the stop was hit.

## Working it out

**R multiple = profit or loss ÷ planned risk**

- Entry ₹500, stop ₹480, 100 shares. Planned risk: ₹20 × 100 = ₹2,000, so 1R = ₹2,000.
- Sold at ₹540: profit ₹4,000, which is **+2R**.
- Stopped out at ₹480: loss ₹2,000, which is **−1R**.
- Gapped down and sold at ₹470: loss ₹3,000, which is **−1.5R**. A gap can make a loss bigger than 1R.

## Two numbers that belong together

| Practice card | What it counts |
|---|---|
| Win rate | The share of closed trades that made money |
| Average R | The average result per closed trade, in R |

Neither number means much alone. Ten trades with a 40% win rate, where winners average +2.5R and losers −1R, add up to 4 × 2.5 − 6 × 1 = +4R, so the average is +0.4R. Ten trades with a 70% win rate, where winners average +0.3R and losers −1.2R, add up to 2.1 − 3.6 = −1.5R.

That is why Belfort's Practice account and journal show results in R. A positive Average R over many trades means your plans made more than they lost; a few trades say very little either way.

## What R does for you

- It removes position size from the picture, so a small account and a large one can compare plans.
- It shows whether you respect your stops: losses far beyond −1R mean exits drifted.
- It is the unit the next lesson uses to think about losing streaks.

::try paper

```quiz
[
  {"q": "You risk ₹1,500 on a trade and close it with a ₹4,500 profit. What is the result in R?", "options": ["+1.5R", "+3R", "+4.5R"], "answer": 1, "why": "₹4,500 ÷ ₹1,500 = 3, so the trade made +3R."},
  {"q": "Your stop was ₹480 but the stock opened at ₹470 and you sold there. Entry was ₹500. What happened in R?", "options": ["Exactly −1R", "A loss larger than −1R", "A gain"], "answer": 1, "why": "The planned loss per share was ₹20; the real loss was ₹30, so the result is −1.5R. Gaps make losses bigger than planned."},
  {"q": "A trader wins 40% of trades. Winners average +2.5R and losers −1R. What is the average result per trade?", "options": ["−0.2R", "+0.4R", "+1.5R"], "answer": 1, "why": "Per ten trades: 4 × 2.5 = +10R and 6 × −1 = −6R, so +4R in total, or +0.4R per trade."},
  {"type": "number", "q": "Entry ₹250, stop ₹240, 100 shares. You exit at ₹275. What is the result in R?", "answer": 2.5, "tolerance": 0.01, "unit": "R", "why": "Planned risk is ₹10 × 100 = ₹1,000. Profit is ₹25 × 100 = ₹2,500, so +2.5R."},
  {"type": "number", "q": "Ten trades: 5 winners at +2R each and 5 losers at −1R each. What is the Average R?", "answer": 0.5, "tolerance": 0.01, "unit": "R", "why": "5 × 2 − 5 × 1 = +5R over 10 trades, an average of +0.5R."},
  {"type": "tf", "q": "A positive Average R over a handful of trades proves your plan works.", "answer": false, "why": "A few trades say very little either way. Average R matters over many trades."}
]
```
