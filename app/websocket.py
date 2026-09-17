"""WebSocket connection manager for real-time chat application (Task Advanced 6)."""

import json
from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister closed WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, author: str, text: str, timestamp: str) -> None:
        """Broadcast formatted JSON payload to all connected clients."""
        payload = json.dumps({
            "author": author,
            "text": text,
            "timestamp": timestamp,
        }, ensure_ascii=False)

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(connection)
