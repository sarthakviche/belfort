"""Refresh Belfort's local copy of SEBI's adviser and research-analyst registers.

SEBI publishes the registers as web pages, without a download. Save the lists from SEBI's site (Intermediaries, then
Recognised intermediaries: Investment Advisers and Research Analysts) as CSV, with at least a name column and a
registration-number column, then run:

    .venv\\Scripts\\python -m belfort.tipcheck.register advisers.csv analysts.csv --as-of 2026-11-27

The snapshot is written to the data folder (never to git) and merged with what is already there.
"""

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path

from .. import settings
from .sources import REGISTER_FILE

NUMBER_RE = re.compile(r"\bIN[AH]\d{9}\b")


def read_csv(path: Path) -> dict[str, dict]:
    """Number to {"name", "kind"} from one saved register list."""
    out = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        number_col = next((c for c in cols if "regist" in c.lower()), None)
        name_col = next((c for c in cols if "name" in c.lower()), None)
        if not number_col or not name_col:
            raise SystemExit(f"{path}: needs a registration-number column and a name column; found {cols}")
        for row in reader:
            m = NUMBER_RE.search((row.get(number_col) or "").upper().replace(" ", ""))
            if m:
                n = m.group(0)
                out[n] = {"name": (row.get(name_col) or "").strip(), "kind": "adviser" if n.startswith("INA") else "analyst"}
    return out


def write(entries: dict[str, dict], as_of: str) -> Path:
    path = settings.DATA_DIR / REGISTER_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    old = {}
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8")).get("entries", {})
    old.update(entries)
    path.write_text(json.dumps({"as_of": as_of, "entries": old}, ensure_ascii=False, indent=0), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Import SEBI adviser and analyst lists saved as CSV.")
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--as-of", default=date.today().isoformat(), help="date the lists were saved (YYYY-MM-DD)")
    a = p.parse_args(argv)
    entries = {}
    for f in a.files:
        entries.update(read_csv(f))
    path = write(entries, a.as_of)
    print(f"{len(entries)} registrations saved to {path}")


if __name__ == "__main__":
    main()
