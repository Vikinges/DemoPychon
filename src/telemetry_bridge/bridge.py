"""The bridge: one source in, two sinks out at different rates.

* Every frame is logged to Parquet (full rate).
* Frames are broadcast to WebSocket clients at a capped display rate
  (default 60 Hz) by dropping intermediate samples — a 360 Hz source does not
  flood a browser, but nothing is lost from the log.

The rate split is the whole point of the job: hard-realtime log, soft-realtime
UI, neither one blocking the other.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from .mock_source import MockTelemetrySource
from .parquet_logger import ParquetLogger
from .ws_server import WsBroadcaster


class TelemetryBridge:
    def __init__(
        self,
        source: MockTelemetrySource,
        parquet_path: str | Path,
        broadcaster: Optional[WsBroadcaster] = None,
        display_hz: float = 60.0,
    ) -> None:
        self.source = source
        self.parquet_path = Path(parquet_path)
        self.broadcaster = broadcaster
        self.display_interval = 1.0 / display_hz if display_hz > 0 else 0.0
        self.frames_logged = 0
        self.frames_broadcast = 0

    async def run(self, duration: float) -> None:
        last_sent = -1e9
        with ParquetLogger(self.parquet_path) as logger:
            async for frame in self.source.stream(duration=duration):
                logger.log(frame)              # full-rate log
                self.frames_logged += 1
                if self.broadcaster is not None and (
                    frame.t - last_sent >= self.display_interval
                ):
                    await self.broadcaster.broadcast(frame)   # capped display rate
                    self.frames_broadcast += 1
                    last_sent = frame.t
