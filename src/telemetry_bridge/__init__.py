"""Async telemetry bridge — capture a real-time telemetry stream, fan it out to a
WebSocket at a display rate while logging every frame to Parquet at full rate.

Demo project: sim-racing style telemetry (speed, rpm, throttle, brake, steering,
gear, lap time). The source is a mock generator so the whole pipeline runs with
no game or hardware attached.
"""

from .frame import TelemetryFrame
from .mock_source import MockTelemetrySource
from .parquet_logger import ParquetLogger
from .bridge import TelemetryBridge

__all__ = ["TelemetryFrame", "MockTelemetrySource", "ParquetLogger", "TelemetryBridge"]
__version__ = "0.1.0"
