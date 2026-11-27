"""Small disk cache with a time-to-live. Stores only data this app fetched itself.

Two kinds of entries:
- Raw downloads (prices, company figures, exchange files). Their content does not depend on Belfort's code, so they
  are kept across updates and only expire by time.
- Results Belfort builds from them (`derived=True`: the home lists, the tagged news feed). Their key carries a
  fingerprint of Belfort's code, so after any update they are rebuilt instead of serving what the old code produced.
  The cache is on disk and outlives a restart, which is why a restart alone does not refresh them.
"""

import hashlib
import pickle
import time
from functools import lru_cache
from pathlib import Path

from ..settings import CACHE_DIR, VERSION

PACKAGE_DIR = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def code_fingerprint() -> str:
    """A short hash of every Python file in the belfort package, or the version number when the source files are not
    on disk (the packaged Windows app). Computed once per process."""
    h = hashlib.sha1(VERSION.encode())
    files = sorted(PACKAGE_DIR.rglob("*.py"))
    for f in files:
        try:
            h.update(f.relative_to(PACKAGE_DIR).as_posix().encode())
            h.update(f.read_bytes())
        except OSError:
            continue
    return h.hexdigest()[:12] if files else f"v{VERSION}"


def cached(key: str, ttl_seconds: float, fn, derived: bool = False):
    if derived:
        key = f"code-{code_fingerprint()}:{key}"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / (hashlib.sha1(key.encode()).hexdigest() + ".pkl")
    if path.exists() and time.time() - path.stat().st_mtime < ttl_seconds:
        try:
            return pickle.loads(path.read_bytes())
        except Exception:
            pass
    value = fn()
    try:
        path.write_bytes(pickle.dumps(value))
    except Exception:
        pass
    return value
