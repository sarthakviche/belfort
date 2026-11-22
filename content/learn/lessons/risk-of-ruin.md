---
title: Losing streaks and risk of ruin
minutes: 6
objectives: Estimate how often losing streaks happen | Work out what a streak costs at different risk levels | Choose a risk per trade you can survive
---
Every trader has losing streaks, including those whose plans make money over time. The real question is not whether a streak will come but whether your account can live through it. **Risk of ruin** is the chance of losing so much that you can no longer trade your plan.

## Streaks are normal

Suppose half of your trades win and half lose, and each trade is independent of the last. Over 100 trades, the chance of seeing at least one run of losses in a row is roughly:

| Losses in a row | Chance in 100 trades (50% win rate) | Chance in 100 trades (40% win rate) |
|---|---|---|
| 5 | About 81% | About 98% |
| 6 | About 55% | About 87% |
| 8 | About 17% | About 49% |
| 10 | About 4% | About 21% |

So a run of five or six losses is close to expected, not a sign that something broke. Check the Win rate card in Practice and read the right column if yours is nearer 40%.

## What ten losses cost

Each loss takes its percentage of what is left. After ten losses of 1R each in a row:

| Risk per trade | Account lost | Gain needed to get back |
|---|---|---|
| 1% | 9.6% | 10.6% |
| 2% | 18.3% | 22.4% |
| 5% | 40.1% | 67.0% |
| 10% | 65.1% | 186.8% |

The last column is the trap. Losses and recoveries are not symmetric: the deeper the hole, the larger the gain needed to climb out, and the harder it is to keep following your rules.

## Keeping ruin unlikely

- Keep risk per trade small, around 1%, so a normal streak stays a dent.
- Count all open trades: Belfort's Open risk card adds them up and warns above 6%.
- Watch the equity curve and its largest drawdown in Practice; it shows your streaks as they happened.
- Judge a plan by Average R over many trades, never by the last few.

::try paper

```quiz
[
  {"q": "A plan wins half of its trades. Over 100 trades, how unusual is a run of five losses in a row?", "options": ["Very rare, under 5%", "Common, about 80%", "Impossible if the plan is good"], "answer": 1, "why": "With a 50% win rate, at least one five-loss streak shows up in about 81% of 100-trade runs."},
  {"q": "Ten losses in a row at 2% risk each leave about how much of the account?", "options": ["About 80%", "About 98%", "About 50%"], "answer": 0, "why": "Each loss takes 2% of what is left: 0.98 to the power 10 is about 0.82, so roughly 18% is lost."},
  {"q": "An account falls 40%. What gain does it need to get back to where it started?", "options": ["40%", "About 67%", "100%"], "answer": 1, "why": "60 must grow to 100, which is a gain of 40 ÷ 60, about 67%."}
]
```
