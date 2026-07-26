from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass(slots=True)
class TelemetryFrame:
    """One telemetry sample. Same shape whether it comes from a sim's shared
    memory or a CAN/serial adapter."""

    t: float
    lap: int
    lap_time: float
    speed_kmh: float
    rpm: float
    gear: int
    throttle: float      # 0..1
    brake: float         # 0..1
    steering: float      # -1 left .. 1 right

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def now(**kwargs: Any) -> "TelemetryFrame":
        kwargs.setdefault("t", time.perf_counter())
        return TelemetryFrame(**kwargs)
