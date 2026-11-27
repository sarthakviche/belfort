---
title: Writing your own trading rules
minutes: 6
objectives: Write a one-page set of trading rules | Make each rule specific enough to check | Review and change rules on a schedule, not in the moment
---
Everything in this syllabus comes together here. Your **trading rules** are a short written document that says what you trade, when you enter, how much you risk, how you exit, and when you stop. If you cannot check a rule with a yes or no, it is a wish rather than a rule.

## A one-page template

| Section | Example rule |
|---|---|
| What I trade | NSE stocks in Belfort's company list; no stocks with results due within 5 trading days |
| Market filter | New trades only while the Nifty 50 is in an uptrend or sideways |
| Setups | Pullback or breakout, with every price check in the research report met |
| Entry | Within 1 ATR of the planned level; never more than 3 ATR above the 20-day average |
| Stop | Placed before entry, below support; only ever raised |
| Size | 1% of capital per trade; 6% total open risk; at most two trades per sector |
| Exits | Half at +2R, trail the rest at 2 ATR; time stop after 15 sessions with no progress |
| Drawdown | Halve risk at 10% from peak; stop new trades for a week at 15% |
| Review | Every weekend: journal tags and Average R; rule changes only on the first weekend of the month |

Your rules will differ. The point is that each line can be checked.

## Specific beats clever

"Do not chase" is hard to check. "Enter within 1 ATR of the planned level" is easy. Vague rules get bent; specific ones either hold or are visibly broken, which the journal then records.

## Changing rules

Rules should change, but slowly and on evidence. Change one thing at a time, on a set review date, and only after enough trades to see a pattern: dozens, not three. Never change a rule during a trade or straight after a loss.

## Practise them first

Run your rules in Belfort's paper account for a few months before risking real money. Tag every trade, watch the equity curve and Average R, and see whether you can actually follow what you wrote. A rule you cannot follow on paper will not survive a real loss.

::try paper

```quiz
[
  {"q": "Which of these is a checkable rule?", "options": ["Be patient with entries", "Enter within 1 ATR of the planned level", "Only take good trades"], "answer": 1, "why": "It can be answered yes or no for every trade. The others are wishes."},
  {"q": "When is the right time to change a rule?", "options": ["Straight after a loss", "On a set review date, based on many trades", "During an open trade"], "answer": 1, "why": "Changes made on a schedule and with evidence avoid reacting to one result."},
  {"q": "Why run new rules on paper first?", "options": ["To see whether you can actually follow them", "Paper trades are more profitable", "Rules only work on paper"], "answer": 0, "why": "Following rules is the hard part. Paper trading shows whether you can, before real money is at stake."},
  {"type": "number", "q": "With 1% risk per trade and a 6% limit on total open risk, what is the most trades you can hold open at full 1% risk?", "answer": 6, "tolerance": 0, "unit": "trades", "why": "6% ÷ 1% = 6 trades. The example rules also cap trades per sector at two."},
  {"type": "tf", "q": "The best time to change a rule is straight after a loss, while the lesson is fresh.", "answer": false, "why": "Never change a rule during a trade or straight after a loss. Change one thing at a time, on a set review date."}
]
```
