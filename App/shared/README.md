# App/shared — Cross-language contracts

Single source of truth for contracts shared between the Node.js **Gateway**
(`App/Gateway`) and the Python **Backend/workers** (`App/Backend`).

## Source of truth

`contracts.json` holds the canonical values. The language modules load from it
so the two sides can never drift:

- `contracts.js` — CommonJS module for the Node.js Gateway/workers.
- `contracts.py` — Python module exposing `str`-backed `Enum`s.

When a value changes, edit **`contracts.json` only**; both modules pick it up.

## Contracts

- **Routing keys** (closed set): `routingKey.audio`, `routingKey.transcript`, `routingKey.AI`.
- **`status`** (`call_jobs`): `RECEIVED | NOISE | TRANSCRIPT | AI | DONE | FAILED`.
- **`lane`**: `NOISE | TRANSCRIPT | AI`.
- **`state`** (`workflow_states`): `QUEUED | PROCESSING | SUCCESS | FAILED`.
- **SSE events**: `NOISE_DONE | TRANSCRIPT_DONE | AI_DONE | FAILED`.
