---
title: Win rate is not the score: expectancy
minutes: 7
objectives: Calculate expectancy from win rate, average win and average loss | Explain why many trades are needed before expectancy means anything | Read expectancy as Average R on Belfort's Practice page
---
New traders chase a high win rate. Professionals watch **expectancy**: the average result per trade over many trades. A plan that wins 35% of the time can be sound; one that wins 80% can slowly empty an account.

## The formula

**Expectancy = (win rate × average win) − (loss rate × average loss)**

Measured in R, it is the same number Belfort shows as **Average R** on the Practice page.

| Plan | Win rate | Average win | Average loss | Expectancy |
|---|---|---|---|---|
| A | 35% | +2.5R | −1R | 0.35 × 2.5 − 0.65 × 1 = **+0.23R** |
| B | 80% | +0.3R | −1.5R | 0.80 × 0.3 − 0.20 × 1.5 = **−0.06R** |
| C | 50% | +1.2R | −1R | 0.50 × 1.2 − 0.50 × 1 = **+0.10R** |

Plan B wins four trades in five and still loses over time, because each loss wipes out five wins.

## Where expectancy comes from

Only two levers exist: how often you win, and how big wins are compared with losses. Cutting losses at the stop keeps the average loss near 1R. Letting winners reach their target or trail keeps the average win up. Habits like moving the stop or exiting early push expectancy down, which is why the journal tags them.

## How many trades it takes

A handful of trades says almost nothing. With a 40% win rate, a run of five or six losses is common, and a few lucky winners can make a poor plan look good. Treat Average R over 10 trades as a rough hint and over 50 or more as something worth acting on. Belfort's journal waits for at least 3 trades in a group before showing it, and even then the numbers move a lot with each new trade.

## Costs count

Practice charges about 0.05% each way to stand in for brokerage and taxes. Small expectancy can disappear after costs, especially on short trades with tight targets.

## Using it

- Check Average R and win rate together on the Practice page.
- Use the journal panel to see which setups and habits raise or lower it.
- Judge a change in your plan by the expectancy over many trades afterwards, not by the next trade.

::try paper

```quiz
[
  {"q": "Win rate 40%, average win +2R, average loss −1R. What is the expectancy?", "options": ["+0.2R", "+0.8R", "−0.2R"], "answer": 0, "why": "0.40 × 2 − 0.60 × 1 = 0.8 − 0.6 = +0.2R per trade."},
  {"q": "A plan wins 80% of trades but averages +0.3R on wins and −1.5R on losses. Over time it…", "options": ["Makes money because it wins often", "Loses a little per trade on average", "Breaks even exactly"], "answer": 1, "why": "0.8 × 0.3 − 0.2 × 1.5 = 0.24 − 0.30 = −0.06R per trade."},
  {"q": "After 6 trades your Average R is +1.1. What should you conclude?", "options": ["The plan is proven", "It is too few trades to say much", "Double the risk per trade"], "answer": 1, "why": "Six trades can be lucky or unlucky. Expectancy needs many trades before it is reliable."},
  {"type": "number", "q": "A plan wins 40% of the time with an average win of +2R and an average loss of −1R. What is its expectancy in R?", "answer": 0.2, "tolerance": 0.005, "unit": "R", "why": "0.40 × 2 − 0.60 × 1 = 0.8 − 0.6 = +0.2R."},
  {"type": "number", "q": "A plan wins 60% of the time with an average win of +0.5R and an average loss of −1.5R. What is its expectancy in R?", "answer": -0.3, "tolerance": 0.005, "unit": "R", "why": "0.60 × 0.5 − 0.40 × 1.5 = 0.3 − 0.6 = −0.3R. A high win rate does not make a plan work."},
  {"type": "tf", "q": "A plan that wins 80% of its trades is bound to make money over time.", "answer": false, "why": "Plan B in the lesson wins four trades in five and still loses, because each loss wipes out five wins."}
]
```
