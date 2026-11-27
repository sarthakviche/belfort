---
title: Exits: targets, trailing stops and time stops
minutes: 8
objectives: Compare a fixed target, a trailing stop and a time stop | Use Belfort's raise-stop, trailing-stop and sell-part tools in Practice | Write the exit into the plan before entering
---
Entries get most of the attention, but the exit decides the result. A plan that says "I will see how it goes" usually ends with winners cut short and losers held. Decide the exit before you enter, then let the plan make the decision.

## Three ways to exit a winner

| Exit | How it works | Strength | Weakness |
|---|---|---|---|
| Fixed target | Sell at a price set in advance, often the next resistance | Simple; locks in a planned result | Caps the trades that keep running |
| Trailing stop | Raise the stop as price rises, by a percentage or a number of ATRs below the close | Lets winners run; protects gains | Gives back some profit before it triggers |
| Time stop | Exit if the trade has not moved after a set number of sessions | Frees capital and attention | A slow trade may move right after you leave |

The protective stop handles losers in all three. These exits only decide what happens when the trade goes your way, or nowhere.

## Trailing by percentage or by ATR

- **Percentage:** a 10% trail on a ₹500 close puts the stop at ₹450. Raise it as closes rise; never lower it.
- **ATR:** a 2 ATR trail with ATR ₹12 puts the stop ₹24 below the close. This adapts to how much the stock normally moves.

A tight trail exits sooner and gives back less, but noise shakes you out more often. A loose trail stays in longer and gives back more. There is no right setting, only one you choose in advance and keep.

## Combining them

Many traders sell part of the position at a first target and trail the rest. For example, sell half at +2R and trail the other half with a 2 ATR stop. The first half locks in a result; the second half keeps the chance of a larger move.

## Doing it in Practice

Belfort's paper account has the tools on each open trade under **Manage**:

- **Raise stop:** move the stop up to a new price. The account refuses a lower stop.
- **Trailing stop:** set a percentage (1 to 25) or an ATR multiple (0.5 to 6). From the next close, the stop follows price up.
- **Sell part:** close some of the shares at the next open and keep the rest.

Exits fill at the next session's prices, including gaps, so you see what each style really costs.

## Time stops by hand

Practice has no automatic time stop. Write the number of sessions in your journal note, and use Sell when the trade has done nothing by then.

::try paper

```quiz
[
  {"q": "You trail a stop at 2 ATR. ATR is ₹15 and today's close is ₹620. Where is the stop, if it was lower before?", "options": ["₹590", "₹605", "₹650"], "answer": 0, "why": "2 × ₹15 = ₹30 below the close: ₹620 − ₹30 = ₹590."},
  {"q": "What is the main weakness of a fixed target?", "options": ["It never locks in profit", "It caps the trades that keep running", "It raises the risk on every trade"], "answer": 1, "why": "Selling everything at a set price means a trade that keeps going has no part left in it."},
  {"q": "Price falls after you set a trailing stop. What happens to the stop?", "options": ["It moves down with price", "It stays where it is", "It is removed"], "answer": 1, "why": "A trailing stop only moves up. When price falls, it stays put until price reaches it."},
  {"type": "number", "q": "A trade closes at ₹600 and ATR is ₹15. Where does a 2 ATR trailing stop sit?", "answer": 570, "tolerance": 0, "unit": "₹", "why": "2 × ₹15 = ₹30 below the close of ₹600 gives ₹570."},
  {"type": "tf", "q": "When a stock becomes more volatile, you may lower a trailing stop to give the trade room.", "answer": false, "why": "A stop is raised as closes rise and never lowered. The Practice account refuses a lower stop."},
  {"type": "tf", "q": "Belfort's Practice account has an automatic time stop.", "answer": false, "why": "Practice has none. Write the number of sessions in your journal note and use Sell when the trade has done nothing by then."}
]
```
