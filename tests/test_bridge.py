import asyncio
import json

import pyarrow.parquet as pq
import pytest
import websockets

from telemetry_bridge import MockTelemetrySource, TelemetryBridge
from telemetry_bridge.ws_server import WsBroadcaster


@pytest.mark.asyncio
async def test_bridge_logs_full_rate_and_caps_broadcast(tmp_path):
    # 200 Hz source, 50 Hz display -> log gets ~4x the frames the socket does
    src = MockTelemetrySource(hz=200.0)
    out = tmp_path / "b.parquet"
    bridge = TelemetryBridge(src, out, broadcaster=None, display_hz=50.0)
    await bridge.run(duration=0.2)

    assert bridge.frames_logged > bridge.frames_broadcast * 0  # logged at least some
    rows = pq.read_table(out).num_rows
    assert rows == bridge.frames_logged
    assert rows >= 25  # ~40 frames expected in 0.2s @200Hz


@pytest.mark.asyncio
async def test_ws_client_receives_json_frames(tmp_path):
    src = MockTelemetrySource(hz=120.0)
    bc = WsBroadcaster(port=8799)
    await bc.start()
    received = []

    async def client():
        async with websockets.connect("ws://127.0.0.1:8799") as ws:
            try:
                while True:
                    received.append(json.loads(await asyncio.wait_for(ws.recv(), timeout=1.0)))
            except (asyncio.TimeoutError, websockets.ConnectionClosed):
                pass

    task = asyncio.create_task(client())
    await asyncio.sleep(0.2)  # let the client connect
    bridge = TelemetryBridge(src, tmp_path / "c.parquet", broadcaster=bc, display_hz=60.0)
    await bridge.run(duration=0.4)
    await asyncio.sleep(0.1)
    task.cancel()
    await bc.stop()

    assert len(received) > 0
    assert {"speed_kmh", "rpm", "throttle"} <= received[0].keys()
