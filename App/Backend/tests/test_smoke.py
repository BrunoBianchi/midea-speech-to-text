"""Smoke test for the Python test framework and shared contracts (Task 1)."""

from app.contracts import Lane, RoutingKey, SseEvent, State, Status


def test_pytest_runs():
    assert True


def test_shared_contracts_load():
    assert RoutingKey.AUDIO.value == "routingKey.audio"
    assert RoutingKey.TRANSCRIPT.value == "routingKey.transcript"
    assert RoutingKey.AI.value == "routingKey.AI"

    assert {s.value for s in Status} == {
        "RECEIVED",
        "NOISE",
        "TRANSCRIPT",
        "AI",
        "DONE",
        "FAILED",
    }
    assert {l.value for l in Lane} == {"NOISE", "TRANSCRIPT", "AI"}
    assert {s.value for s in State} == {
        "QUEUED",
        "PROCESSING",
        "SUCCESS",
        "FAILED",
    }
    assert {e.value for e in SseEvent} == {
        "NOISE_DONE",
        "TRANSCRIPT_DONE",
        "AI_DONE",
        "FAILED",
    }
