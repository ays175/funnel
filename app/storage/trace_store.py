from __future__ import annotations

import json
import sqlite3
from pathlib import Path


class TraceStore:
    def __init__(self, db_url: str) -> None:
        self.db_path = self._parse_db_url(db_url)
        self._init_db()

    def _parse_db_url(self, db_url: str) -> Path:
        if db_url.startswith("sqlite:///"):
            path = db_url.replace("sqlite:///", "", 1)
            return Path(path)
        if db_url.startswith("sqlite://"):
            path = db_url.replace("sqlite://", "", 1)
            return Path(path)
        raise ValueError(f"Unsupported TRACE_DB_URL: {db_url}")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY,
                    raw_query TEXT NOT NULL,
                    domain_pack TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_request(self, request_id: str, raw_query: str, domain_pack: str, created_at: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO requests (request_id, raw_query, domain_pack, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (request_id, raw_query, domain_pack, created_at),
            )
            conn.commit()

    def get_request(self, request_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT request_id, raw_query, domain_pack, created_at FROM requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "request_id": row[0],
            "raw_query": row[1],
            "domain_pack": row[2],
            "created_at": row[3],
        }

    def add_event(self, request_id: str, event_type: str, data: dict, created_at: str) -> None:
        payload = json.dumps(data)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO events (request_id, event_type, data_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (request_id, event_type, payload, created_at),
            )
            conn.commit()

    def list_events(self, request_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT event_type, data_json, created_at
                FROM events
                WHERE request_id = ?
                ORDER BY id ASC
                """,
                (request_id,),
            ).fetchall()
        events: list[dict] = []
        for event_type, data_json, created_at in rows:
            events.append(
                {
                    "event_type": event_type,
                    "data": json.loads(data_json),
                    "timestamp": created_at,
                }
            )
        return events
