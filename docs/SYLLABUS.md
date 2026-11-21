# How the syllabus is chosen

Belfort teaches the practical skills of swing and positional trading in Indian cash equities, and leaves out the rest. The syllabus itself lives in [`content/learn/syllabus.json`](../content/learn/syllabus.json); this page explains how topics get in.

## The screening test

A topic enters the syllabus only if it passes the **decision test** or the **safety test**, and then also the practice and order tests.

| Test | Question | Example in | Example out |
|---|---|---|---|
| **Decision** | Does it change a decision a swing or positional trader makes in a normal week: what to study, where to enter, where the stop goes, how much to buy, when to exit? | Position sizing; support and resistance | CAPM and beta |
| **Evidence** | Is there measurable evidence it helps, or can Belfort show the evidence? Folklore is taught only as "what people believe and what the data says". | Chart patterns, with the backtest | Elliott waves as a method |
| **Practice** | Can the learner try it inside Belfort within five minutes? Every lesson ends with a replay, a paper trade, a prediction or a report. | Stop placement, then a replay drill | Reading an annual report end to end |
| **Safety** | Does it protect the learner's money or rights (costs, tax, scams, regulation), even if it is not a trading decision? | Tip-group scams; checking SEBI registration | |
| **Order** | Is everything it depends on taught earlier? | Trend before setups | |

## Shape of the course

| Track | Level | Modules |
|---|---|---|
| Foundations | Beginner | How the market works for you · Reading a price chart · Risk comes first |
| Practitioner | Intermediate | Setups · A business sanity check in ten minutes · Indicators and patterns, honestly · The journal and the review |
| Advanced | Advanced | Market context · Running several trades · Psychology and discipline · Taxes and records · Scams, tips and your rights |

38 lessons are planned; 8 are written in v0.1 (the first two modules of Foundations, plus the two core risk lessons). Each lesson is five to eight minutes, states its objectives, ends with something to try in Belfort and three quiz questions, and is marked complete at 60%.

## Left out on purpose

Futures and options, intraday scalping, valuation theory (DCF, CAPM), academic portfolio theory, accounting standards in depth, Elliott waves and other unproven methods, crypto and forex. The reasons are listed in the syllabus file and shown in the app under "How this syllabus was chosen".

## Rules for lesson content

- Plain English, short sentences, every term in the dictionary so it gets a hover explanation.
- No buy, sell or hold advice, no predictions, no promises (enforced by a test).
- A chart of a named stock uses `::chart SYMBOL BARS`, which only serves prices at least 30 days old (SEBI's July 2026 norm for educational use of price data).
- Figures that change (tax rates, charges) are described, with a pointer to the current source, rather than hard-coded.
