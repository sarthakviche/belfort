"""Export and import of the practice journal (belfort/practice/backup.py)."""

import copy

import pytest
from fastapi.testclient import TestClient

from belfort.main import app
from belfort.practice import backup, service


def _some_practice(c):
    c.post(
        "/api/practice/trades",
        json={"symbol": "TCS", "qty": 3, "stop": 1, "thesis": "Backup round trip trade.", "setup": "pullback"},
    )
    c.post("/api/practice/predictions", json={"symbol": "INFY", "direction": "up", "horizon": "4 weeks", "confidence": 0.6})
    new = c.get("/api/practice/replay/new").json()
    c.post("/api/practice/replay/score", json={"id": new["id"], "decision": "skip"})


def test_csv_exports_have_headers_and_rows(fresh_db):
    c = TestClient(app)
    _some_practice(c)
    trades = c.get("/api/practice/export/trades.csv")
    assert trades.status_code == 200 and trades.headers["content-type"].startswith("text/csv")
    assert "attachment" in trades.headers["content-disposition"]
    lines = trades.text.strip().splitlines()
    assert lines[0].startswith("id,account_id,symbol,qty") and "TCS" in lines[1] and len(lines) == 2
    assert "INFY" in c.get("/api/practice/export/predictions.csv").text
    assert c.get("/api/practice/export/replays.csv").text.count("\n") == 2
    assert c.get("/api/practice/export/accounts.csv").status_code == 404


def test_backup_round_trip_restores_everything(fresh_db):
    c = TestClient(app)
    _some_practice(c)
    saved = c.get("/api/practice/export/backup.json").json()
    assert saved["format"] == backup.BACKUP_FORMAT and len(saved["trades"]) == 1 and len(saved["accounts"]) == 1
    c.post("/api/practice/reset")
    assert service.portfolio()["pending"] == []
    restored = c.post("/api/practice/import", json=saved)
    assert restored.status_code == 200 and restored.json()["trades"] == 1 and "Backup restored" in restored.json()["message"]
    again = c.get("/api/practice/export/backup.json").json()
    assert (
        again["trades"] == saved["trades"]
        and again["predictions"] == saved["predictions"]
        and again["replays"] == saved["replays"]
    )


def _broken(saved, change):
    data = copy.deepcopy(saved)
    change(data)
    return data


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (lambda d: d.update(format="something-else"), "not a Belfort practice backup"),
        (lambda d: d.update(version=99), "version 99"),
        (lambda d: d["trades"][0].pop("symbol"), "missing symbol"),
        (lambda d: d["trades"][0].update(hack="x"), "unknown fields: hack"),
        (lambda d: d["trades"][0].update(qty=0), "invalid quantity"),
        (lambda d: d["trades"][0].update(account_id=999), "belong to its practice account"),
        (lambda d: d.update(predictions="nope"), "no predictions list"),
    ],
)
def test_import_rejects_a_bad_backup_and_changes_nothing(fresh_db, change, expected):
    c = TestClient(app)
    _some_practice(c)
    saved = c.get("/api/practice/export/backup.json").json()
    r = c.post("/api/practice/import", json=_broken(saved, change))
    assert r.status_code == 400 and expected in r.json()["detail"]
    assert c.get("/api/practice/export/backup.json").json()["trades"] == saved["trades"]  # untouched
