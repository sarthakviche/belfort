"""Disk cache: raw downloads survive a code update; results Belfort builds are rebuilt after one. No network."""

from belfort.data import cache


def _count(value):
    calls = []

    def fn():
        calls.append(1)
        return value

    return fn, calls


def test_raw_entries_are_reused_until_they_expire():
    fn, calls = _count("raw")
    assert cache.cached("t-raw", 60, fn) == "raw"
    assert cache.cached("t-raw", 60, fn) == "raw"
    assert len(calls) == 1


def test_derived_entries_are_rebuilt_when_the_code_changes(monkeypatch):
    fn, calls = _count("built")
    monkeypatch.setattr(cache, "code_fingerprint", lambda: "aaa")
    cache.cached("t-derived", 60, fn, derived=True)
    cache.cached("t-derived", 60, fn, derived=True)
    assert len(calls) == 1
    monkeypatch.setattr(cache, "code_fingerprint", lambda: "bbb")  # an update changed the code
    cache.cached("t-derived", 60, fn, derived=True)
    assert len(calls) == 2


def test_raw_entries_ignore_the_code_fingerprint(monkeypatch):
    fn, calls = _count("raw")
    monkeypatch.setattr(cache, "code_fingerprint", lambda: "aaa")
    cache.cached("t-raw2", 60, fn)
    monkeypatch.setattr(cache, "code_fingerprint", lambda: "bbb")
    cache.cached("t-raw2", 60, fn)
    assert len(calls) == 1


def test_fingerprint_is_stable_and_short():
    cache.code_fingerprint.cache_clear()
    a = cache.code_fingerprint()
    cache.code_fingerprint.cache_clear()
    assert a == cache.code_fingerprint() and len(a) == 12


def test_fingerprint_falls_back_to_the_version_without_source(monkeypatch, tmp_path):
    monkeypatch.setattr(cache, "PACKAGE_DIR", tmp_path)  # the packaged app has no .py files on disk
    cache.code_fingerprint.cache_clear()
    try:
        assert cache.code_fingerprint() == f"v{cache.VERSION}"
    finally:
        cache.code_fingerprint.cache_clear()
