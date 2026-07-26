"""Buffered full-rate Parquet logger.

Frames are appended to an in-memory buffer and flushed to a Parquet file in
row-group batches, so logging at a few hundred Hz doesn't stall the event loop
or thrash the disk. Columnar Parquet keeps a full session small and fast to
re-open in pandas / DuckDB for analysis.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import pyarrow as pa
import pyarrow.parquet as pq

from .frame import TelemetryFrame

_SCHEMA = pa.schema([
    ("t", pa.float64()), ("lap", pa.int32()), ("lap_time", pa.float64()),
    ("speed_kmh", pa.float64()), ("rpm", pa.float64()), ("gear", pa.int32()),
    ("throttle", pa.float64()), ("brake", pa.float64()), ("steering", pa.float64()),
])


class ParquetLogger:
    def __init__(self, path: str | Path, batch_size: int = 512) -> None:
        self.path = Path(path)
        self.batch_size = batch_size
        self._buf: List[TelemetryFrame] = []
        self._writer: pq.ParquetWriter | None = None
        self.rows_written = 0

    def __enter__(self) -> "ParquetLogger":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._writer = pq.ParquetWriter(self.path, _SCHEMA)
        return self

    def log(self, frame: TelemetryFrame) -> None:
        self._buf.append(frame)
        if len(self._buf) >= self.batch_size:
            self._flush()

    def _flush(self) -> None:
        if not self._buf or self._writer is None:
            return
        cols = {name: [getattr(f, name) for f in self._buf] for name in _SCHEMA.names}
        table = pa.table(cols, schema=_SCHEMA)
        self._writer.write_table(table)
        self.rows_written += len(self._buf)
        self._buf.clear()

    def close(self) -> None:
        self._flush()
        if self._writer is not None:
            self._writer.close()
            self._writer = None

    def __exit__(self, *exc) -> None:
        self.close()
