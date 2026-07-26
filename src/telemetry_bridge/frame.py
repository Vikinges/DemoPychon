"""A single telemetry sample."""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass(slots=True)
class TelemetryFrame:
    """One telemetry sample from the car/sim at a single instant.

    Field set mirrors what a sim-racing shared-memory feed exposes; a real
    adapter (iRacing, AC/ACC, or a CAN/serial bridge) would fill the same shape.
    """

    t: float              # monotonic-ish timestamp, seconds
    lap: int              # current lap number
    lap_time: float       # seconds into the current lap
    speed_kmh: float
    rpm: float
    gear: int             # -1 = reverse, 0 = neutral, 1..n
    throttle: float       # 0.0 .. 1.0
    brake: float          # 0.0 .. 1.0
    steering: float       # -1.0 (full left) .. 1.0 (full right)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def now(**kwargs: Any) -> "TelemetryFrame":
        kwargs.setdefault("t", time.perf_counter())
        return TelemetryFrame(**kwargs)
