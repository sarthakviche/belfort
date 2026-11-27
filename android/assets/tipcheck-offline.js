"use strict";
/* Tip Check's text rules, run on the phone with no computer and no internet (T48).
   The phrases are Belfort's own belfort/tipcheck/phrases.json, copied in by build_apk.py as phrases.js, so the
   phone and the desktop flag the same wording. Stock checks (NSE lists, prices) need the computer. */
window.TipCheckOffline = (function () {
  const data = window.TIP_PHRASES || null;
  const CHECKS = [
    ["promises", "Promised returns", "The tip promises a return or claims there is no risk. SEBI does not allow anyone to promise returns.", "No promise of returns found."],
    ["target_days", "A price target with a deadline", "The tip names a price target with a short deadline. A deadline is there to rush you.", "No price target with a deadline found."],
    ["urgency", "Pressure to act fast", "The tip pushes you to act now. Real research leaves you time to check it.", "No pressure-to-act wording found."],
    ["secrecy", "Insider or secret information", "The tip claims secret, insider or operator knowledge. That is usually bait.", "No claims of insider information found."],
    ["money_ask", "Asks for money or a private group", "The tip asks for money, payment details or a move to a private or paid group.", "No request for money or a private group found."],
  ];
  const norm = (t) => (t || "").normalize("NFKC").replace(/[’‘]/g, "'").replace(/[“”]/g, '"').replace(/\s+/g, " ").trim().toLowerCase();
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  function pattern(p) {
    if (p.startsWith("re:")) { try { return new RegExp(p.slice(3), "giu"); } catch (e) { return null; } }
    if (/^[\x00-\x7f]*$/.test(p)) return new RegExp("(?<![\\p{L}\\p{N}_])" + esc(p.toLowerCase()) + "(?![\\p{L}\\p{N}_])", "giu");
    return new RegExp(esc(p), "gu");
  }
  const compiled = {};
  function rules(flag) {
    if (!compiled[flag]) compiled[flag] = Object.values(data[flag] || {}).flat().map(pattern).filter(Boolean);
    return compiled[flag];
  }
  function find(flag, text) {
    const n = norm(text), spans = [];
    rules(flag).forEach((re) => { re.lastIndex = 0; for (const m of n.matchAll(re)) if (m[0]) spans.push([m.index, m.index + m[0].length]); });
    spans.sort((a, b) => a[0] - b[0]);
    const merged = [];
    spans.forEach(([s, e]) => { const last = merged[merged.length - 1]; if (last && s < last[1]) last[1] = Math.max(last[1], e); else merged.push([s, e]); });
    return [...new Set(merged.map(([s, e]) => n.slice(s, e).trim()))].slice(0, 5);
  }
  function registration(text) {
    const nums = [...new Set([...(text || "").normalize("NFKC").matchAll(/\b(IN[AHZP])[\s:\-]*(\d{5,13})\b/gi)].map((m) => m[1].toUpperCase() + m[2]))];
    const claims = find("authority", text), approved = find("approval_claim", text);
    const lines = []; let red = false;
    if (approved.length) { lines.push("The tip claims SEBI approved it. SEBI never approves a tip, a stock or a scheme."); red = true; }
    if (!nums.length) { lines.push(claims.length ? "It says it is SEBI registered but gives no number to check." : "No SEBI registration number. Registered advisers (INA…) and analysts (INH…) must show theirs."); red = true; }
    nums.forEach((n) => {
      if (n.length !== 12) { lines.push(`${n} is not a valid SEBI number (three letters and nine digits).`); red = true; }
      else if (/^IN[ZP]/.test(n)) { lines.push(`${n} is a broker's or portfolio manager's number, not an adviser's.`); red = true; }
      else lines.push(`${n} has the right shape. Check it yourself on SEBI's site; scammers copy real numbers.`);
    });
    return { id: "registration", title: "SEBI registration", status: red ? "flag" : "unknown", detail: lines.join(" "), evidence: [...new Set(nums.concat(claims, approved))] };
  }
  function check(text) {
    if (!data) return null;
    const out = [registration(text)];
    CHECKS.forEach(([id, title, flagText, clearText]) => {
      const ev = find(id, text);
      out.push({ id, title, status: ev.length ? "flag" : "clear", detail: ev.length ? flagText : clearText, evidence: ev });
    });
    return { findings: out, flags: out.filter((f) => f.status === "flag").length };
  }
  return { ready: !!data, check };
})();
