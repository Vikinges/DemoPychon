import asyncio
import math

import pytest

from telemetry_bridge import MockTelemetrySource, TelemetryFrame


def test_sample_is_pure_and_deterministic():
    a = MockTelemetrySource(seed=1)
    b = MockTelemetrySource(seed=1)
    assert a.sample(2.5) == b.sample(2.5)          # same seed -> same value
    assert isinstance(a.sample(0.0), TelemetryFrame)


def test_channel_ranges_are_physical():
    src = MockTelemetrySource(seed=7)
    for i in range(500):
        f = src.sample(i * 0.01)
        assert 0.0 <= f.throttle <= 1.0
        assert 0.0 <= f.brake <= 1.0
        assert -1.0 <= f.steering <= 1.0
        assert f.speed_kmh >= 0.0
        assert 1 <= f.gear <= 6
        assert f.lap >= 1


def test_lap_counter_advances():
    src = MockTelemetrySource(lap_seconds=5.0)
    assert src.sample(1.0).lap == 1
    assert src.sample(6.0).lap == 2
    assert src.sample(11.0).lap == 3


def test_rejects_bad_hz():
    with pytest.raises(ValueError):
        MockTelemetrySource(hz=0)


@pytest.mark.asyncio
async def test_stream_yields_at_rate():
    src = MockTelemetrySource(hz=200.0)
    frames = [f async for f in src.stream(duration=0.1)]
    # ~20 frames in 0.1s at 200 Hz; allow slack for scheduling
    assert 15 <= len(frames) <= 25
    assert all(isinstance(f, TelemetryFrame) for f in frames)
