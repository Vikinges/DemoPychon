"""A deterministic mock telemetry source.

Yields TelemetryFrame samples at a requested rate. Values follow a smooth,
lap-like curve (accelerate down a straight, brake into a corner, repeat) so the
downstream WebSocket/Parquet paths get realistic-looking data with no game
attached. Seeded, so tests are reproducible.
"""
from __future__ import annotations

import asyncio
import math
import random
from typing import AsyncIterator

from .frame import TelemetryFrame


class MockTelemetrySource:
    def __init__(self, hz: float = 360.0, lap_seconds: float = 8.0, seed: int = 42) -> None:
        if hz <= 0:
            raise ValueError("hz must be positive")
        self.hz = hz
        self.period = 1.0 / hz
        self.lap_seconds = lap_seconds
        self._rng = random.Random(seed)

    def sample(self, t: float) -> TelemetryFrame:
        """Pure function: telemetry state at time ``t`` seconds. No I/O, easy to test."""
        phase = (t % self.lap_seconds) / self.lap_seconds       # 0..1 around the lap
        lap = int(t // self.lap_seconds) + 1
        lap_time = t % self.lap_seconds

        # Throttle high on the straight, off under braking into the corner.
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
        """Async-yield frames at ~hz. Stops after ``duration`` seconds if given."""
        t = 0.0
        n = 0
        start = asyncio.get_event_loop().time()
        while duration is None or t < duration:
            yield self.sample(t)
            n += 1
            t = n * self.period
            # keep wall-clock roughly in step with simulated time
            target = start + t
            sleep = target - asyncio.get_event_loop().time()
            if sleep > 0:
                await asyncio.sleep(sleep)
