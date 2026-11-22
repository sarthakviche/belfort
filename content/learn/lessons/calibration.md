---
title: Calibration: are your 70% calls right 70% of the time?
minutes: 6
objectives: Explain what it means to be well calibrated | Work out a Brier score for one prediction | Read the Calibration panel on Belfort's Predict page
---
Every trade is a forecast with a confidence attached, even if you never say the number. **Calibration** asks whether that confidence is honest: of all the calls you made at 70%, did about 70% come true?

## Why it matters

An overconfident trader sizes too big and ignores warning signs. An underconfident one passes on reasonable plans. Neither can be fixed without measuring, because everyone believes their confidence is about right.

## How Belfort's Predict page works

You pick a stock, a direction (up or down), a horizon (1 week, 2 weeks, 4 weeks or 3 months) and a confidence between 50% and 99%. Belfort records the last close. After the horizon, it checks whether the close was higher or lower and scores the call.

## The Brier score

For one call, the **Brier score** is the squared distance between your confidence and what happened:

- If right: (1 − confidence)²
- If wrong: confidence²

| Confidence | Right | Wrong |
|---|---|---|
| 50% | 0.25 | 0.25 |
| 70% | 0.09 | 0.49 |
| 90% | 0.01 | 0.81 |

Lower is better. A 50% call always scores 0.25, a coin flip. A 90% call gains little when right and costs a lot when wrong. Practice points follow the same shape: 100 × (1 − 4 × Brier), so a 50% call scores 0 and a confident wrong call loses more than a confident right call gains. The points are for practice only.

## Reading the Calibration panel

Once some calls have played out, Belfort groups them by stated confidence (50–60%, 60–70% and so on) and draws two bars for each group: what you said and how often it came true. If your 80–90% group came true only 55% of the time, you are overconfident at that level. The "Well calibrated" badge needs an average Brier score under 0.20 over 20 or more calls.

## Getting better

- Make many small calls, not a few big ones.
- Write a reason with each call, then compare reasons for the ones that failed.
- If high-confidence calls keep missing, use lower numbers until the bars match.

::try predict

```quiz
[
  {"q": "You make a call at 80% confidence and it comes true. What is its Brier score?", "options": ["0.04", "0.20", "0.64"], "answer": 0, "why": "(1 − 0.8)² = 0.2² = 0.04."},
  {"q": "Twenty calls made at about 70% confidence came true 12 times. What does that suggest?", "options": ["Well calibrated", "Overconfident at that level", "Underconfident at that level"], "answer": 1, "why": "12 of 20 is 60%, below the 70% stated, so the confidence was too high."},
  {"q": "Why does a 50% call score 0 practice points whether right or wrong?", "options": ["It says you have no view either way", "It is a bug", "50% calls are not allowed"], "answer": 0, "why": "50% means no edge in either direction, so it neither earns nor loses points."}
]
```
