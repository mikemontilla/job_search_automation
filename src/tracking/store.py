import json
import sqlite3
from dataclasses import fields as dataclass_fields
from datetime import datetime, timezone

from src.discovery.config import DB_PATH
from src.tracking.models import Application, ApplicationEvent, JSON_FIELDS

APPLICATION_COLUMNS = [f.name for f in dataclass_fields(Application)]
EVENT_COLUMNS = [f.name for f in dataclass_fields(ApplicationEvent)]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id                TEXT PRIMARY KEY,
    offer_id          TEXT,
    title             TEXT,
    company           TEXT,
    location          TEXT,
    source_url        TEXT,
    stage             TEXT DEFAULT 'interested',
    cv_languages      TEXT,
    hr_contact        TEXT,
    applied_date      TEXT,
    next_action       TEXT,
    next_action_date  TEXT,
    notes             TEXT,
    created_at        TEXT,
    updated_at        TEXT
);

CREATE TABLE IF NOT EXISTS application_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id  TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    title           TEXT,
    detail          TEXT,
    event_date      TEXT,
    created_at      TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);
"""

# Columns added after the initial schema — applied via ALTER TABLE for existing DBs.
_MIGRATIONS: list[str] = []


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cur = conn.execute("PRAGMA table_info(applications)")
    existing = {row["name"] for row in cur.fetchall()}
    for stmt in _MIGRATIONS:
        col = stmt.split()[-2]
        if col not in existing:
            conn.execute(stmt)


def init_schema() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)
        _migrate(conn)


def _serialize_application(app: Application) -> dict:
    row = app.to_dict()
    for key in JSON_FIELDS:
        row[key] = json.dumps(row.get(key), ensure_ascii=False)
    return row


def _deserialize_application(row: sqlite3.Row) -> Application:
    data = dict(row)
    for key in JSON_FIELDS:
        raw = data.get(key)
        data[key] = json.loads(raw) if raw else ([] if key == "cv_languages" else {})
    return Application(**data)


def _deserialize_event(row: sqlite3.Row) -> ApplicationEvent:
    return ApplicationEvent(**dict(row))


def upsert(application: Application) -> None:
    application.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row = _serialize_application(application)
    placeholders = ", ".join(f":{c}" for c in APPLICATION_COLUMNS)
    columns = ", ".join(APPLICATION_COLUMNS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in APPLICATION_COLUMNS if c != "id")
    sql = (
        f"INSERT INTO applications ({columns}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}"
    )
    with _connect() as conn:
        conn.execute(sql, row)


def get(application_id: str) -> Application | None:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM applications WHERE id = ?", (application_id,))
        row = cur.fetchone()
        return _deserialize_application(row) if row else None


def list_applications(stage: str | None = None) -> list[Application]:
    clauses, params = [], []
    if stage:
        clauses.append("stage = ?")
        params.append(stage)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connect() as conn:
        cur = conn.execute(
            f"SELECT * FROM applications {where} ORDER BY updated_at DESC", params
        )
        return [_deserialize_application(r) for r in cur.fetchall()]


def set_stage(application_id: str, stage: str) -> bool:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE applications SET stage = ?, updated_at = ? WHERE id = ?",
            (stage, now, application_id),
        )
        return cur.rowcount > 0


def add_event(event: ApplicationEvent) -> int:
    columns = [c for c in EVENT_COLUMNS if c != "id"]
    placeholders = ", ".join(f":{c}" for c in columns)
    sql = f"INSERT INTO application_events ({', '.join(columns)}) VALUES ({placeholders})"
    with _connect() as conn:
        cur = conn.execute(sql, event.to_dict())
        return cur.lastrowid


def list_events(application_id: str) -> list[ApplicationEvent]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM application_events WHERE application_id = ? ORDER BY created_at",
            (application_id,),
        )
        return [_deserialize_event(r) for r in cur.fetchall()]
