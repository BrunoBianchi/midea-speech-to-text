"""Shared cross-language contracts for the Python backend and workers.

Values are loaded from ``contracts.json``, the single source of truth shared
with the Node.js side (``contracts.js``). Do NOT hardcode values here; edit
``contracts.json`` so both languages stay in sync.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

_CONTRACTS_PATH = Path(__file__).resolve().parent / "contracts.json"

with _CONTRACTS_PATH.open(encoding="utf-8") as _fh:
    _CONTRACTS = json.load(_fh)


class RoutingKey(str, Enum):
    """Closed set of routing keys for the direct-exchange."""

    AUDIO = _CONTRACTS["routingKeys"]["AUDIO"]
    TRANSCRIPT = _CONTRACTS["routingKeys"]["TRANSCRIPT"]
    AI = _CONTRACTS["routingKeys"]["AI"]


class Status(str, Enum):
    """``call_jobs.status`` enum."""

    RECEIVED = _CONTRACTS["status"]["RECEIVED"]
    NOISE = _CONTRACTS["status"]["NOISE"]
    TRANSCRIPT = _CONTRACTS["status"]["TRANSCRIPT"]
    AI = _CONTRACTS["status"]["AI"]
    DONE = _CONTRACTS["status"]["DONE"]
    FAILED = _CONTRACTS["status"]["FAILED"]


class Lane(str, Enum):
    """Lane enum."""

    NOISE = _CONTRACTS["lane"]["NOISE"]
    TRANSCRIPT = _CONTRACTS["lane"]["TRANSCRIPT"]
    AI = _CONTRACTS["lane"]["AI"]


class State(str, Enum):
    """``workflow_states.state`` enum."""

    QUEUED = _CONTRACTS["state"]["QUEUED"]
    PROCESSING = _CONTRACTS["state"]["PROCESSING"]
    SUCCESS = _CONTRACTS["state"]["SUCCESS"]
    FAILED = _CONTRACTS["state"]["FAILED"]


class SseEvent(str, Enum):
    """SSE progress/result events relayed to the dashboard."""

    NOISE_DONE = _CONTRACTS["sseEvents"]["NOISE_DONE"]
    TRANSCRIPT_DONE = _CONTRACTS["sseEvents"]["TRANSCRIPT_DONE"]
    AI_DONE = _CONTRACTS["sseEvents"]["AI_DONE"]
    FAILED = _CONTRACTS["sseEvents"]["FAILED"]


#: Set of valid routing-key values, for membership checks.
VALID_ROUTING_KEYS = frozenset(rk.value for rk in RoutingKey)


def is_valid_routing_key(routing_key: str) -> bool:
    """Return ``True`` when ``routing_key`` belongs to the closed set."""
    return routing_key in VALID_ROUTING_KEYS


__all__ = [
    "RoutingKey",
    "Status",
    "Lane",
    "State",
    "SseEvent",
    "VALID_ROUTING_KEYS",
    "is_valid_routing_key",
]
