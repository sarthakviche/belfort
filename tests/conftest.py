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
