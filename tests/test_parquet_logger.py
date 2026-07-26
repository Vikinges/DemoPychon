import pyarrow.parquet as pq

from telemetry_bridge import MockTelemetrySource, ParquetLogger


def test_logger_writes_all_rows(tmp_path):
    src = MockTelemetrySource()
    out = tmp_path / "s.parquet"
    with ParquetLogger(out, batch_size=64) as logger:
        for i in range(500):
            logger.log(src.sample(i * 0.01))
    assert logger.rows_written == 500
    table = pq.read_table(out)
    assert table.num_rows == 500
    assert set(table.column_names) >= {"t", "speed_kmh", "rpm", "throttle", "brake", "steering"}


def test_roundtrip_values_preserved(tmp_path):
    src = MockTelemetrySource(seed=3)
    frame = src.sample(1.23)
    out = tmp_path / "one.parquet"
    with ParquetLogger(out, batch_size=1) as logger:
        logger.log(frame)
    row = pq.read_table(out).to_pylist()[0]
    assert abs(row["speed_kmh"] - frame.speed_kmh) < 1e-9
    assert row["gear"] == frame.gear
