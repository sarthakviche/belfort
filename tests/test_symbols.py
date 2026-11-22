"""The fuzzy stock picker's search index (belfort/data/symbols.py). Offline: a fixture listing stands in for NSE."""

import csv
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from belfort import settings
from belfort.data import symbols
from belfort.main import app
from belfort.research.analysis import pipeline

FIXTURE = Path(__file__).parent / "fixtures" / "equity_listing.csv"


@pytest.fixture(scope="module")
def listing():
    with FIXTURE.open(encoding="utf-8") as f:
        return [(r["SYMBOL"], r["NAME OF COMPANY"]) for r in csv.DictReader(f)]


@pytest.fixture
def find(listing, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(symbols, "_closes", None)

    def run(query, limit=None):
        return [r["symbol"] for r in symbols.search(listing, query, limit)]

    return run


def test_search_two_letters_lists_every_hdfc_company(find):
    hits = find("hd")
    assert {"HDFCBANK", "HDFCLIFE", "HDFCAMC"} <= set(hits)
    assert hits[:3] == ["HDFCBANK", "HDFCLIFE", "HDFCAMC"]  # well-known companies before smaller ones


def test_search_full_name_and_typo_find_hdfc_bank(find):
    assert find("hdfc bank")[0] == "HDFCBANK"
    assert find("HDFC Bank Ltd")[0] == "HDFCBANK"
    assert find("hdcf bank")[0] == "HDFCBANK"


@pytest.mark.parametrize(
    ("query", "symbol"),
    [
        ("reliance", "RELIANCE"),
        ("relaince", "RELIANCE"),
        ("jio", "JIOFIN"),
        ("sbi", "SBIN"),
        ("l&t", "LT"),
        ("infy", "INFY"),
        ("infosys", "INFY"),
        ("m&m", "M&M"),
        ("mahindra", "M&M"),
        ("hul", "HINDUNILVR"),
        ("tcs", "TCS"),
        ("tcs.ns", "TCS"),
        ("asian paint", "ASIANPAINT"),
    ],
)
def test_search_puts_the_intended_company_first(find, query, symbol):
    assert find(query)[0] == symbol


def test_search_empty_or_unknown_query_returns_nothing(find):
    assert find("") == [] and find("   ") == [] and find("!!") == []
    assert find("zzqqxx") == []
    assert find("NOSUCHSYMBOL") == []


def test_search_respects_the_limit_and_returns_name_and_sector(listing, find):
    assert len(find("a", limit=3)) <= 3
    row = symbols.search(listing, "hdfc bank")[0]
    assert row["name"] == "HDFC Bank" and row["sector"] == "Banks"
    assert "last_close" not in row  # nothing fetched yet


def test_search_shows_the_last_close_once_one_was_fetched(listing, find):
    symbols.remember_close("TCS", 3201.456, "2026-11-20")
    symbols.remember_close("TCS", 3000.0, "2026-11-01")  # an older close never replaces a newer one
    row = symbols.search(listing, "tcs")[0]
    assert row["last_close"] == 3201.46 and row["as_of"] == "2026-11-20"


def test_search_falls_back_to_the_builtin_list_without_the_nse_file(find, tmp_path):
    hits = [r["symbol"] for r in symbols.search([], "hdfc")]
    assert {"HDFCBANK", "HDFCLIFE", "HDFCAMC"} <= set(hits)
    assert symbols.search([], "jio")[0]["symbol"] == "JIOFIN"


def test_every_alias_points_at_a_builtin_company():
    builtin = {s for s, _ in symbols.builtin_companies()}
    assert set(symbols.load_aliases().values()) <= builtin


def test_search_is_fast_on_a_full_size_listing(listing):
    big = listing + [(f"CO{i:04d}", f"Company Number {i} Industries Limited") for i in range(2600)]
    index = symbols.SymbolIndex(big)
    started = time.perf_counter()
    for query in ("hd", "hdcf bank", "relaince", "zzzzzz", "mahindra"):
        index.search(query, settings.SEARCH_LIMIT)
    assert (time.perf_counter() - started) / 5 < 0.1  # 30 ms on a laptop; generous for shared CI runners


def test_search_endpoint_uses_the_index(monkeypatch, listing):
    class Nse:
        def listed(self):
            return listing

        def search(self, query, limit=None):
            return symbols.search(self.listed(), query, limit)

    monkeypatch.setattr(pipeline, "nse", Nse())
    results = TestClient(app).get("/api/search", params={"q": "hdcf bank"}).json()["results"]
    assert results[0]["symbol"] == "HDFCBANK" and results[0]["name"] == "HDFC Bank"
