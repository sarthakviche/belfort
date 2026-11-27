"""The Large caps list uses NSE's current Nifty 50, falling back to a dated built-in copy. No network."""

import pytest

from belfort.data import providers
from belfort.research import screens
from belfort.research.analysis import pipeline


class FakeResponse:
    def __init__(self, text, status=200):
        self.text, self.status_code = text, status


def _csv(symbols):
    rows = "\n".join(f"Company {s} Ltd.,Services,{s},EQ,INE000000000" for s in symbols)
    return "Company Name,Industry,Symbol,Series,ISIN Code\n" + rows + "\n"


@pytest.fixture
def no_cache(monkeypatch):
    monkeypatch.setattr(providers, "cached", lambda key, ttl, fn: fn())


def test_nifty50_reads_the_official_constituent_file(monkeypatch, no_cache):
    syms = [f"S{i}" for i in range(50)]
    monkeypatch.setattr(providers.httpx, "get", lambda *a, **k: FakeResponse(_csv(syms)))
    assert providers.NseArchiveProvider().nifty50() == syms


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(_csv(["TCS", "INFY", "ITC"])),  # far too few members: a broken or partial file
        FakeResponse("<html>Access denied</html>"),
        FakeResponse(_csv([f"S{i}" for i in range(50)]), status=503),
    ],
)
def test_nifty50_returns_none_for_a_bad_file(monkeypatch, no_cache, response):
    monkeypatch.setattr(providers.httpx, "get", lambda *a, **k: response)
    assert providers.NseArchiveProvider().nifty50() is None


def test_nifty50_returns_none_when_offline(monkeypatch, no_cache):
    def boom(*a, **k):
        raise providers.httpx.ConnectError("offline")

    monkeypatch.setattr(providers.httpx, "get", boom)
    assert providers.NseArchiveProvider().nifty50() is None


def test_large_caps_fall_back_to_the_dated_builtin_list(monkeypatch):
    monkeypatch.setattr(pipeline.nse, "nifty50", lambda: None)
    members, source = screens.nifty_members()
    assert members == screens.NIFTY and len(members) == 50
    assert screens.NIFTY_AS_OF in source and "could not be fetched" in source


def test_large_caps_prefer_the_live_list(monkeypatch):
    monkeypatch.setattr(pipeline.nse, "nifty50", lambda: ["TCS", "INFY"])
    assert screens.nifty_members() == (["TCS", "INFY"], "NSE Indices' current Nifty 50 list")


def test_builtin_nifty_list_has_fifty_unique_symbols():
    assert len(screens.NIFTY) == len(set(screens.NIFTY)) == 50


def test_screens_cache_is_rebuilt_after_a_code_change(monkeypatch):
    calls = []
    monkeypatch.setattr(screens, "cached", lambda key, ttl, fn, derived=False: calls.append(derived) or {"lists": {}})
    screens._run()
    assert calls == [True]
