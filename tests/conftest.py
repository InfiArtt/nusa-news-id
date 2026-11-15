"""Pytest setup: install the NVDA fakes and make the add-on importable as the package ``nusaNewsID``."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "tests"))
sys.path.insert(0, str(_ROOT / "addon" / "globalPlugins"))

import nvda_mocks  # noqa: E402, F401
