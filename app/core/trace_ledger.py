from __future__ import annotations

from datetime import datetime, timezone

from app.storage.trace_store import TraceStore


class TraceLedger:
    def __init__(self, store: TraceStore) -> None:
        self.store = store

    def append(self, request_id: str, event_type: str, data: dict) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        event = {
            "event_type": event_type,
            "data": data,
            "timestamp": timestamp,
        }
        self.store.add_event(request_id, event_type, data, timestamp)
        return event

    def list_events(self, request_id: str) -> list[dict]:
        return self.store.list_events(request_id)
