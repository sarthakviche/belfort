"""Wording rules shared by every vertical.

Belfort describes, measures and teaches. It never tells anyone to buy, sell or hold, never promises returns,
and never offers anything of money value for predictions. See docs/COMPLIANCE.md.
"""

BANNED_PHRASES = [
    "guaranteed",
    "guarantee",
    "sure shot",
    "sure-shot",
    "buy now",
    "sell now",
    "strong buy",
    "strong sell",
    "will definitely",
    "can't lose",
    "cannot lose",
    "risk-free",
    "risk free",
    "multibagger",
    "target hit guaranteed",
    "jackpot",
    "double your money",
]

DISCLAIMER = (
    "Belfort is free, open-source software for learning and research. It is not investment advice or a recommendation "
    "to buy, sell or hold any security, and its authors are not SEBI-registered research analysts or investment advisers. "
    "Labels state whether fixed, published rules are met; they do not predict returns. Practice uses virtual points with "
    "no money value. Markets carry risk and you can lose money. Belfort never places orders."
)

AI_NOTICE = (
    "Answers come from the AI provider you chose, using your own key. The assistant explains; it does not give "
    "buy or sell advice, and it can be wrong."
)


def find_banned(text: str) -> list[str]:
    low = (text or "").lower()
    return [p for p in BANNED_PHRASES if p in low]
