"""Every test run gets its own empty data folder, so tests never touch the user's database or cache."""
import os
import tempfile

os.environ["BELFORT_DATA_DIR"] = tempfile.mkdtemp(prefix="belfort-test-")
