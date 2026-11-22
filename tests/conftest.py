"""Every test run gets its own empty data folder, so tests never touch the user's database or cache."""

import os
import tempfile

os.environ["BELFORT_DATA_DIR"] = tempfile.mkdtemp(prefix="belfort-test-")


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_bar_cache():
    """Bars cached in memory by one test must never leak into another."""
    from belfort.data import market

    market.clear_cache()
    yield
    market.clear_cache()


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """An empty practice database and synthetic daily bars for every symbol."""
    from belfort import settings
    from belfort.data import market
    from tests.helpers import price_frame

    monkeypatch.setattr(settings, "DB_FILE", tmp_path / "t.db")
    monkeypatch.setattr(market, "bars", lambda symbol, years=5: price_frame(n=400, drift=0.001))
    return tmp_path
