# Compliance principles

Belfort is free, open-source software for learning and research. These principles keep it on the right side of the rules. They are design rules, not legal advice; maintainers should get a review from a securities lawyer before major releases.

## What the rules are based on (as of November 2026)

| Rule | What it means for Belfort |
|---|---|
| SEBI (Research Analysts) Regulations, 2014, as amended in December 2024, and SEBI's January 2025 guidelines and FAQs | Research services **for consideration** about named securities need registration. General commentary and statistical summaries are outside the definition of a research report. Belfort runs on the user's machine and states which published rule conditions hold. It must not be sold or hosted as a per-stock research service without registration. |
| SEBI circular on sharing real-time price data (May 2024) | Gamified virtual-trading platforms using live prices, especially with real money, were stopped. Belfort uses end-of-day data, has no live feed, and has no money or prizes. |
| SEBI norms on price data for education (circular of 8 May 2026, effective 1 July 2026) | Price data used for education must lag by at least 30 days. Every chart inside a lesson or the replay trainer is served through `market.lagged(..., EDU_LAG_DAYS=30)`. |
| SEBI rules on finfluencers and education (October 2024, January 2025) | Educational content must not name a stock in a way that suggests its future price, or act as a tip. Lessons use old charts to teach a concept, never to suggest what a stock will do. Project marketing follows the same rule. |
| Promotion and Regulation of Online Gaming Act, 2025 (rules in force from May 2026) | Online money games are banned. Belfort's points cannot be bought, sold, won or redeemed, and there are no entry fees or prizes. |
| Data terms (Yahoo, NSE, publishers) | Data is fetched by each user's own machine for personal use. Belfort does not redistribute prices or full articles; news shows only feed-provided headlines and descriptions with a link to the source. |

> **Keep it free and local.** Most of the protection above comes from Belfort being free and local. If Belfort ever charges money, the per-stock Research labels are the part most likely to need a SEBI-registered research analyst or a redesign. Learn, Practice and News are lower risk. Decide pricing with a securities lawyer, before launch.

## Rules in code

1. **Labels describe; they do not advise.** "Conditions met", "Partly met", "Rule excludes", "Insufficient data". Each comes with the full checklist and its numbers.
2. **Banned wording.** `core/compliance.py` lists promise and tip phrases. Tests scan every page, lesson and dictionary entry for them, and the assistant's replies are filtered at run time.
3. **No stock tips relayed.** News headlines that pass on someone's buy or sell call or price target are hidden by default and labelled when shown.
4. **Practice is points only.** Starting points are fixed, resets are free, and nothing is redeemable. There are no leaderboards of live calls, which could turn predictions into tips.
5. **Lagged data in education.** See above.
6. **Bring your own AI key.** Belfort holds no keys and has no AI account. The assistant explains what is on screen and is instructed never to give advice or predictions.
7. **Local-first, accounts optional.** Without an account Belfort stays local-only. With one (Supabase, T43), only the user's own practice and learning documents and non-secret settings sync to the project's database, protected by row-level security. No prices, no research output and no telemetry are sent. Accounts store personal data (an email address), so India's Digital Personal Data Protection Act 2023 applies: the sign-in screen and the docs carry a short privacy notice (what is stored, why, and how to delete it), and an account can be deleted from inside the app. Legal sign-off on that notice is decision D3. `ACCESS_CODES` exists only for sharing on a private network, knowingly.

## Things the project will not build

- Real-money contests, prizes, cash rewards or paid entry for practice or predictions.
- Alerts, Telegram or WhatsApp bots, or public feeds that push named-stock calls.
- A paid hosted version of the per-stock research report without proper SEBI registration.
- Order placement or automated trading.
