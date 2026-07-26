# telemetry-bridge-demo

A small, self-contained **async telemetry bridge** in Python: take a real-time
telemetry stream and fan it out to **two sinks at two different rates** —

- a **WebSocket** feed capped at a display rate (default **60 Hz**) for a live UI, and
- a **Parquet** log that captures **every** frame at the full source rate (default 360 Hz)

— without either sink blocking the other. The data source here is a **mock
sim-racing generator** (speed, rpm, gear, throttle, brake, steering, lap time),
so the whole pipeline runs with **no game or hardware attached**.

The point of the design is the rate split: a hard-realtime log and a
soft-realtime UI, decoupled. A real adapter (iRacing / AC / ACC shared memory,
or a CAN/serial bridge) would drop into `mock_source.py`'s place and feed the
same `TelemetryFrame` shape downstream.

## Run it

```bash
pip install -r requirements.txt

# log-only, writes session.parquet
python run_demo.py --seconds 10 --no-ws

# with the live WebSocket server on ws://127.0.0.1:8765
python run_demo.py --seconds 30
```

Then point a browser or `websocat ws://127.0.0.1:8765` at it to watch ~60 Hz
JSON frames while the full 360 Hz stream lands in `session.parquet`.

## Tests

```bash
pip install -r requirements.txt
pytest -q
```

Covers the pure-function sampler (deterministic, physical channel ranges),
the Parquet logger (all rows written, values round-trip), and the bridge
(full-rate log vs capped broadcast, real WebSocket client receives JSON).

## Layout

```
src/telemetry_bridge/
  frame.py           TelemetryFrame dataclass (one sample)
  mock_source.py     deterministic mock source; sample(t) is pure + testable
  parquet_logger.py  buffered, batched full-rate Parquet writer
  ws_server.py       async WebSocket broadcaster (drops dead clients)
  bridge.py          one source in -> Parquet (full rate) + WS (capped)
run_demo.py          CLI entry point
tests/               pytest + pytest-asyncio
```

## Design notes

- **`sample(t)` is a pure function of time** — no I/O — so channel behaviour is
  unit-tested without the event loop.
- **Parquet writes are batched** (row groups) so logging at hundreds of Hz
  doesn't stall the loop or thrash the disk; a full session stays small and
  re-opens instantly in pandas / DuckDB.
- **The broadcaster is isolated from the log**: a slow or dead WebSocket client
  is dropped and never delays a logged frame.

MIT licensed. Built as a focused demo of async real-time streaming + columnar
logging in Python.
