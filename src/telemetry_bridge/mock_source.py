from __future__ import annotations

import asyncio
import math
import random
from typing import AsyncIterator

from .frame import TelemetryFrame


class MockTelemetrySource:
    """Deterministic stand-in for a live sim feed. `sample(t)` is a pure function
    of time, so the channel behaviour is unit-testable without an event loop or a
    game running. Swap this class for a real iRacing/AC/ACC adapter that yields
    the same TelemetryFrame."""

    def __init__(self, hz: float = 360.0, lap_seconds: float = 8.0, seed: int = 42) -> None:
        if hz <= 0:
            raise ValueError("hz must be positive")
        self.hz = hz
        self.period = 1.0 / hz
        self.lap_seconds = lap_seconds
        self._rng = random.Random(seed)

    def sample(self, t: float) -> TelemetryFrame:
        phase = (t % self.lap_seconds) / self.lap_seconds
        lap = int(t // self.lap_seconds) + 1
        lap_time = t % self.lap_seconds

        # Throttle down the straight, off under braking into the corner.
        throttle = max(0.0, math.cos(phase * 2 * math.pi)) ** 0.5
        brake = max(0.0, -math.cos(phase * 2 * math.pi)) ** 0.8
        speed = 60 + 200 * throttle - 40 * brake
        speed = max(0.0, speed + self._rng.uniform(-1.5, 1.5))
        rpm = 1500 + speed * 35 + self._rng.uniform(-50, 50)
        gear = min(6, max(1, int(speed // 40) + 1))
        steering = math.sin(phase * 2 * math.pi) * 0.9 + self._rng.uniform(-0.02, 0.02)

        return TelemetryFrame(
            t=t, lap=lap, lap_time=round(lap_time, 4),
            speed_kmh=round(speed, 2), rpm=round(rpm, 1), gear=gear,
            throttle=round(throttle, 4), brake=round(brake, 4),
            steering=round(max(-1.0, min(1.0, steering)), 4),
        )

    async def stream(self, duration: float | None = None) -> AsyncIterator[TelemetryFrame]:
        """Yield frames at ~hz, pacing to wall clock. Runs until `duration`."""
        loop = asyncio.get_event_loop()
        start = loop.time()
        n = 0
        while True:
            t = n * self.period
            if duration is not None and t >= duration:
                return
            yield self.sample(t)
            n += 1
            sleep = (start + n * self.period) - loop.time()
            if sleep > 0:
                await asyncio.sleep(sleep)
