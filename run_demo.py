"""Telemetry bridge runner.

    python run_demo.py --seconds 30                 # live mock + dashboard
    python run_demo.py --seconds 10 --no-ws         # log only
    python run_demo.py --replay session.parquet     # replay a recording

Serves a live dashboard at http://127.0.0.1:8080 and a WebSocket feed at
ws://127.0.0.1:8765, while logging every frame at full rate to Parquet.
"""
from __future__ import annotations

import argparse
import asyncio
import functools
import http.server
import socketserver
import threading
from pathlib import Path

from telemetry_bridge import MockTelemetrySource, TelemetryBridge
from telemetry_bridge.replay import ReplaySource
from telemetry_bridge.ws_server import WsBroadcaster

DASHBOARD_DIR = Path(__file__).parent / "dashboard"


def _serve_dashboard(port: int = 8080) -> None:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DASHBOARD_DIR))
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()


async def main() -> None:
    ap = argparse.ArgumentParser(description="Sim telemetry -> WebSocket + Parquet bridge")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--source-hz", type=float, default=360.0)
    ap.add_argument("--display-hz", type=float, default=60.0)
    ap.add_argument("--out", type=Path, default=Path("session.parquet"))
    ap.add_argument("--replay", type=Path, help="replay a recorded .parquet session")
    ap.add_argument("--speed", type=float, default=1.0, help="replay speed multiplier")
    ap.add_argument("--no-ws", action="store_true", help="log only, no WebSocket/dashboard")
    args = ap.parse_args()

    source = ReplaySource(args.replay, speed=args.speed) if args.replay else \
        MockTelemetrySource(hz=args.source_hz)

    broadcaster = None
    if not args.no_ws:
        broadcaster = WsBroadcaster()
        await broadcaster.start()
        _serve_dashboard()
        print("Dashboard : http://127.0.0.1:8080")
        print(f"WebSocket : ws://{broadcaster.host}:{broadcaster.port}  ({args.display_hz:.0f} Hz)")

    bridge = TelemetryBridge(source, args.out, broadcaster, display_hz=args.display_hz)
    mode = f"replay {args.replay}" if args.replay else f"mock {args.source_hz:.0f} Hz"
    print(f"Running   : {mode} -> {args.out}")
    await bridge.run(duration=None if args.replay else args.seconds)
    if broadcaster is not None:
        await broadcaster.stop()
    print(f"Done      : logged {bridge.frames_logged}, broadcast {bridge.frames_broadcast}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nstopped")
