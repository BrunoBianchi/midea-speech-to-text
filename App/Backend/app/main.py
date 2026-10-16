"""FastAPI application entrypoint (skeleton).

Exposes a minimal app with a health route so the container and the Gateway
readiness probe have something to talk to. Ingestion/upload routes, SSE
emission and callbacks are implemented in later tasks.
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Midea Speech-to-Text API", version="0.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness/readiness placeholder consulted by the Gateway."""
    return {"status": "ok"}
