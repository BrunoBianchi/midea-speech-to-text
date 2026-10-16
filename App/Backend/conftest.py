"""Pytest bootstrap: make the backend package importable as ``app``.

Adds the ``App/Backend`` directory (this file's directory) to ``sys.path`` so
tests can ``import app`` without an installed package.
"""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
