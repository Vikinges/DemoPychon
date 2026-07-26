"""Minimal async WebSocket broadcaster.

Holds a set of connected clients and pushes each JSON-encoded frame to all of
them. A dead/slow client is dropped rather than allowed to block the others.
Kept transport-agnostic: the bridge calls ``broadcast()``; how many clients are
attached is irrelevant to the logging path.
"""
from __future__ import annotations

import json
from typing import Any, Set

import websockets

from .frame import TelemetryFrame


class WsBroadcaster:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self._clients: Set[Any] = set()
        self._server = None

    async def _handler(self, ws: Any) -> None:
        self._clients.add(ws)
        try:
            await ws.wait_closed()
        finally:
            self._clients.discard(ws)

    async def start(self) -> None:
        self._server = await websockets.serve(self._handler, self.host, self.port)

    async def broadcast(self, frame: TelemetryFrame) -> None:
        if not self._clients:
            return
        payload = json.dumps(frame.to_dict(), separators=(",", ":"))
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
