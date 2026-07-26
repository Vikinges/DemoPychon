import pyarrow.parquet as pq
import pytest

from telemetry_bridge import MockTelemetrySource, ParquetLogger, TelemetryBridge
from telemetry_bridge.replay import ReplaySource


@pytest.mark.asyncio
async def test_replay_reproduces_logged_session(tmp_path):
    src = MockTelemetrySource(hz=120.0)
    rec = tmp_path / "rec.parquet"
    with ParquetLogger(rec, batch_size=32) as log:
        for i in range(120):
            log.log(src.sample(i / 120.0))

    out = tmp_path / "replayed.parquet"
    bridge = TelemetryBridge(ReplaySource(rec, speed=50.0), out, broadcaster=None, display_hz=0)
    await bridge.run(duration=None)

    assert pq.read_table(out).num_rows == pq.read_table(rec).num_rows == 120
