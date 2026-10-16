"""Re-export of the shared cross-language contracts for the backend.

The canonical module lives in ``App/shared/contracts.py`` (loaded from
``App/shared/contracts.json``). This thin bridge adds ``App/shared`` to
``sys.path`` and re-exports the contracts so backend code can simply do::

    from app.contracts import RoutingKey, Status, Lane, State, SseEvent
"""

from __future__ import annotations

import sys
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parents[2] / "shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from contracts import (  # noqa: E402  (path injected above)
    VALID_ROUTING_KEYS,
    Lane,
    RoutingKey,
    SseEvent,
    State,
    Status,
    is_valid_routing_key,
)

__all__ = [
    "RoutingKey",
    "Status",
    "Lane",
    "State",
    "SseEvent",
    "VALID_ROUTING_KEYS",
    "is_valid_routing_key",
]
