from asyncio import Lock
from fastapi import WebSocket

from .schemas import EventEnvelope


class ConnectionManager:
    def __init__(self) -> None:
        self._active: list[WebSocket] = []
        self._lock = Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._active.append(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self._active:
                self._active.remove(ws)

    async def broadcast(self, event: str, data: dict) -> None:
        async with self._lock:
            sockets = list(self._active)
        if not sockets:
            return
        payload = EventEnvelope(event=event, data=data).model_dump_json()
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:  # pylint: disable=broad-exception-caught
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    @property
    def client_count(self) -> int:
        return len(self._active)
