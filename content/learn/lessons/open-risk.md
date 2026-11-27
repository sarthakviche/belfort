---
title: Total open risk and correlation
minutes: 7
objectives: Add up the risk across all open trades and pending orders | Explain why correlated trades behave like one bigger trade | Read the Open risk card and warnings in Belfort's Practice account
---
Risking 1% per trade is only half the rule. Five open trades at 1% each put 5% of the account at risk at once, and if the market falls hard they can all hit their stops in the same week. **Total open risk** is the sum of what you would lose if every open trade hit its stop today.

## Adding it up

For each open trade: **(last close − current stop) × shares**. Add the same for pending orders, using their expected entry and stop. That is how far the account's value would fall from today if every stop were hit.

| Trade | Shares | Price | Stop | Risk |
|---|---|---|---|---|
| A | 100 | ₹520 | ₹500 | ₹2,000 |
| B | 50 | ₹1,240 | ₹1,200 | ₹2,000 |
| C | 200 | ₹312 | ₹300 (raised to entry) | ₹2,400 |
| Total | | | | ₹6,400 |

On ₹2,00,000 of capital, that is 3.2% open risk. Trade C's stop sits at its entry, so hitting it would give back ₹2,400 of open gain but lose none of your starting capital. Belfort still counts it, because those points would come off the account's value today.

## Belfort's limits in Practice

The paper account shows an **Open risk** card and warns you when an order would push past either limit:

- **One trade above 2%** of the account.
- **All open trades and pending orders together above 6%.**

The warnings do not block the order; they make you decide on purpose.

## Correlation

Trades in the same sector, or all depending on the same driver, tend to move together. Three bank stocks at 1% each are closer to one 3% bet on banks than to three separate 1% bets. When the sector falls, the stops tend to go together, and a gap can take all three at once.

Ways to keep correlation in check:

- Limit how many open trades come from one sector, for example two.
- Count correlated trades as one when you check the 6% limit.
- Prefer setups from different sectors when you already hold several in one.

## Raising stops frees risk

Raising a stop shrinks the distance to it, so the trade's open risk falls. Once the stop is at entry or above, the trade can no longer lose capital, only give back gains. Many traders then let it count less towards their limit, which makes room for a new trade.

::try paper

```quiz
[
  {"q": "You hold 100 shares at ₹410 with a stop at ₹395, and 40 shares at ₹980 with a stop at ₹955. What is the total open risk?", "options": ["₹1,500", "₹2,500", "₹3,000"], "answer": 1, "why": "100 × ₹15 = ₹1,500 and 40 × ₹25 = ₹1,000, so ₹2,500 in total."},
  {"q": "What does Belfort's Practice account do when total open risk would pass 6%?", "options": ["Blocks the order", "Warns you before you place it", "Nothing"], "answer": 1, "why": "It warns so you decide on purpose. The order is not blocked."},
  {"q": "Why can three trades in one sector be riskier than three in different sectors?", "options": ["They tend to fall together", "Sectors have no link to prices", "Exchanges charge more"], "answer": 0, "why": "Shared drivers make their stops more likely to be hit at the same time, like one larger trade."},
  {"type": "number", "q": "A trade has 80 shares, a last close of ₹250 and a stop at ₹235. How much open risk does it add?", "answer": 1200, "tolerance": 0, "unit": "₹", "why": "(250 − 235) × 80 = ₹15 × 80 = ₹1,200."},
  {"type": "number", "q": "Your trades have a total open risk of ₹9,000 on capital of ₹3,00,000. What is the open risk as a percentage of the account?", "answer": 3, "tolerance": 0, "unit": "%", "why": "9,000 ÷ 3,00,000 = 3%, under Belfort's 6% warning for all open trades together."},
  {"type": "tf", "q": "Three bank stocks at 1% risk each are three separate 1% bets.", "answer": false, "why": "They tend to move together, so they are closer to one 3% bet on banks. Their stops can go together."}
]
```
