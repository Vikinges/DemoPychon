"""Run the telemetry bridge as a script.

    python run_demo.py --seconds 10 --out session.parquet

Starts a WebSocket server on ws://127.0.0.1:8765 (connect a browser or
`websocat` to watch ~60 Hz frames), while logging every frame at full rate to a
Parquet file. Prints a small summary at the end.
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from telemetry_bridge import MockTelemetrySource, TelemetryBridge
from telemetry_bridge.ws_server import WsBroadcaster


async def main() -> None:
    ap = argparse.ArgumentParser(description="Sim telemetry -> WebSocket + Parquet bridge")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--source-hz", type=float, default=360.0)
    ap.add_argument("--display-hz", type=float, default=60.0)
    ap.add_argument("--out", type=Path, default=Path("session.parquet"))
    ap.add_argument("--no-ws", action="store_true", help="log only, skip WebSocket server")
    args = ap.parse_args()

    source = MockTelemetrySource(hz=args.source_hz)
    broadcaster = None
    if not args.no_ws:
        broadcaster = WsBroadcaster()
        await broadcaster.start()
        print(f"WebSocket: ws://{broadcaster.host}:{broadcaster.port}  (display {args.display_hz:.0f} Hz)")

    bridge = TelemetryBridge(source, args.out, broadcaster, display_hz=args.display_hz)
    print(f"Logging {args.source_hz:.0f} Hz to {args.out} for {args.seconds:.0f}s ...")
    await bridge.run(duration=args.seconds)
    if broadcaster is not None:
        await broadcaster.stop()

    print(f"done: logged {bridge.frames_logged} frames, "
          f"broadcast {bridge.frames_broadcast} -> {args.out}")


if __name__ == "__main__":
    asyncio.run(main())
