from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator

from .frame import TelemetryFrame
from .parquet_logger import read_session


class ReplaySource:
    """Re-streams a recorded Parquet session, honouring the original frame
    timing (optionally sped up). Same interface as MockTelemetrySource, so it
    drops straight into TelemetryBridge."""

    def __init__(self, path: str | Path, speed: float = 1.0) -> None:
        self.path = Path(path)
        self.speed = max(1e-6, speed)

    async def stream(self, duration: float | None = None) -> AsyncIterator[TelemetryFrame]:
        loop = asyncio.get_event_loop()
        start = loop.time()
        t0 = None
        for frame in read_session(self.path):
            if t0 is None:
                t0 = frame.t
            rel = (frame.t - t0) / self.speed
            if duration is not None and rel >= duration:
                return
            wait = (start + rel) - loop.time()
            if wait > 0:
                await asyncio.sleep(wait)
            yield frame
