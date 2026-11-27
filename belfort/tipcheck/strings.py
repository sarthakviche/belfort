"""Every sentence Tip Check shows, in one place, so the interface can be translated (T50) without touching the rules.

Placeholders in braces are filled by the rules. Keep Belfort's own wording here free of promise and tip phrases: the
banned-wording tests scan these strings. The tip's own words never appear here; they are quoted back as evidence.
"""

EN = {
    # --- check titles ---
    "registration.title": "SEBI registration",
    "promises.title": "Promised returns",
    "target_days.title": "A price target with a deadline",
    "urgency.title": "Pressure to act fast",
    "secrecy.title": "Insider or secret information",
    "money_ask.title": "Asks for money or a private group",
    "surveillance.title": "NSE surveillance lists",
    "pump.title": "Pump pattern in price and volume",
    "history.title": "The last time this stock looked like this",
    # --- registration ---
    "registration.none": "The tip gives no SEBI registration number. Registered advisers (INA…) and research analysts "
    "(INH…) must show their number on every message about a stock.",
    "registration.claimed_none": "The tip says it is SEBI registered but gives no registration number to check.",
    "registration.approval": "The tip claims SEBI (or an exchange) approved it. SEBI registers advisers; it never approves "
    "a tip, a stock or a scheme.",
    "registration.malformed": "{number} is not a valid SEBI number. Adviser and analyst numbers are three letters and "
    "nine digits, for example INH000000000.",
    "registration.wrong_kind": "{number} is a {kind} number, not an adviser's or research analyst's. Only those two may "
    "advise on a stock.",
    "registration.not_found": "{number} is not in Belfort's copy of SEBI's register (from {as_of}).",
    "registration.found": "{number} is in Belfort's copy of SEBI's register (from {as_of}) as {name}. Scammers copy real "
    "numbers, so confirm that the sender really is {name}.",
    "registration.no_register": "{number} has the right shape, but Belfort has no copy of SEBI's register to compare it "
    "with. Check it yourself on SEBI's site.",
    "kind.INZ": "stock broker's",
    "kind.INP": "portfolio manager's",
    # --- phrase checks ---
    "promises.flag": "The tip promises a return or claims there is no risk. SEBI does not allow anyone to promise returns, "
    "and no one can know them in advance.",
    "promises.clear": "No promise of returns found in the text.",
    "target_days.flag": "The tip names a price target with a short deadline. Nobody knows where a price will be in a few "
    "days; a deadline is there to rush you.",
    "target_days.clear": "No price target with a deadline found.",
    "urgency.flag": "The tip pushes you to act now. Real research leaves you time to check it.",
    "urgency.clear": "No pressure-to-act wording found.",
    "secrecy.flag": "The tip claims secret, insider or 'operator' knowledge. Trading on real inside information is a "
    "crime; claimed inside information is usually bait.",
    "secrecy.clear": "No claims of insider or secret information found.",
    "money_ask.flag": "The tip asks for money, payment details or a move to a private or paid group. That is where most "
    "tip scams take their money.",
    "money_ask.clear": "No request for money or a private group found.",
    # --- surveillance ---
    "surveillance.flag": "NSE has put {symbol} under: {measures} (NSE file of {as_of}). NSE adds stocks to these lists "
    "when their price or trading looks unusual, to protect investors.",
    "surveillance.clear": "{symbol} is not on NSE's ASM, GSM or ESM lists, and NSE has not flagged it for SMS or social "
    "media tips (NSE file of {as_of}).",
    "surveillance.lead.sms": "NSE itself has flagged {symbol} as a stock named in unsolicited SMS tips.",
    "surveillance.lead.social": "NSE itself has flagged {symbol} as a stock named in social media tips.",
    "surveillance.no_symbol": "No NSE stock was recognised in the tip, so the lists could not be checked. Pick the stock "
    "to check it.",
    "surveillance.not_listed": "{symbol} is not in NSE's surveillance file of {as_of}, so it could not be checked.",
    "surveillance.unavailable": "NSE's surveillance file could not be loaded just now. Try again later.",
    "measure.gsm": "Graded Surveillance Measure (GSM) stage {stage}",
    "measure.asm_long": "Long-term Additional Surveillance Measure (ASM) stage {stage}",
    "measure.asm_short": "Short-term Additional Surveillance Measure (ASM) stage {stage}",
    "measure.esm": "Enhanced Surveillance Measure (ESM) stage {stage}",
    "measure.sms": "NSE's flag for stocks named in unsolicited SMS tips",
    "measure.social": "NSE's flag for stocks named in social media tips",
    "measure.irp": "insolvency resolution",
    # --- pump ---
    "pump.flag": "{symbol} shows a pump pattern: {facts}.",
    "pump.clear": "No pump pattern in {symbol}'s recent sessions: {facts}.",
    "pump.no_data": "Recent prices for {symbol} could not be loaded, so the pattern could not be checked.",
    "pump.no_symbol": "No NSE stock was recognised in the tip, so its prices could not be checked.",
    "pump.spike": "volume reached {ratio}× its 50-session average on {day}",
    "pump.no_spike": "highest recent volume {ratio}× its 50-session average",
    "pump.runup": "price up {pct}% in the last {bars} sessions",
    "pump.no_runup": "price change {pct}% over the last {bars} sessions",
    "pump.small": "a small company worth about ₹{crore} crore",
    "pump.large": "a company worth about ₹{crore} crore",
    "pump.size_unknown": "company size unknown",
    # --- history ---
    "history.found": "On {day}, {symbol}'s volume was {ratio}× its 50-session average after a {runup}% rise in "
    "{bars} sessions. {after}",
    "history.after": "{n} sessions later its close was {pct}% {direction} that day's close",
    "history.low": "the lowest close in those {n} sessions was {pct}% below it",
    "history.higher": "above",
    "history.lower": "below",
    "history.none": "No session like that in {symbol}'s history Belfort has (up to {lag} days ago).",
    "history.no_data": "Not enough price history to look back.",
    "history.note": "This is what happened once before, not what will happen now.",
    # --- summary ---
    "level.low": "No red flags found",
    "level.some": "Some red flags",
    "level.many": "Many red flags",
    "summary.flags": "{n} red flag found|{n} red flags found",
    "summary.none": "No red flags found. That does not make the tip safe: Belfort can only check what is written.",
    "summary.limits": "Belfort reports red flags found and not found. It cannot tell you whether a trade will work, and "
    "it never says a stock is good, safe, or one to buy or sell.",
    "share.line": "I checked this tip on Belfort: {n} red flag.|I checked this tip on Belfort: {n} red flags.",
    # --- next steps ---
    "next.verify": "Check the sender's registration yourself on SEBI's site (Intermediaries, then Recognised "
    "intermediaries: Investment Advisers or Research Analysts).",
    "next.report": "Report a tip that promises returns or asks for money on SEBI SCORES, and the number or group to "
    "the chat app.",
    "next.never": "Never share an OTP, your trading login, or pay a 'fee' to join a tips group.",
    "next.learn": "Learn how these scams work:",
    "lesson.tip-scams": "How tip scams work",
    "lesson.check-registration": "Check a registration",
    "lesson.myths": "Market myths",
    "link.advisers": "SEBI's list of investment advisers",
    "link.analysts": "SEBI's list of research analysts",
    "link.scores": "SEBI SCORES",
    # --- errors ---
    "error.empty": "Paste the tip's text, or add a screenshot.",
    "error.image_type": "Use a PNG, JPEG or WebP screenshot.",
    "error.image_size": "That image is too large. Use a screenshot under 5 MB.",
    "error.image_empty": "No text could be read from that image. Paste the text instead.",
}

SEBI_REGISTER_URL = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=14"
SEBI_ADVISER_URL = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"
SCORES_URL = "https://scores.sebi.gov.in/"


def t(key: str, **values) -> str:
    """The sentence for `key`, filled in. Plural forms are written 'one|many' and picked by `n`."""
    text = EN[key]
    if "|" in text:
        one, many = text.split("|", 1)
        text = one if values.get("n") == 1 else many
    return text.format(**values) if values else text
