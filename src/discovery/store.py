import json
import sqlite3
from dataclasses import fields as dataclass_fields

from src.discovery.config import DB_PATH
from src.discovery.models import Offer, OfferStatus, JSON_FIELDS

# Column order is derived from the Offer dataclass so schema and model stay in sync.
COLUMNS = [f.name for f in dataclass_fields(Offer)]

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS offers (
    id              TEXT PRIMARY KEY,
    source_url      TEXT NOT NULL,
    source_type     TEXT,
    fetched_at      TEXT,
    published_date  TEXT,
    status          TEXT DEFAULT '{OfferStatus.NEW.value}',
    score           INTEGER,
    recommended     INTEGER DEFAULT 0,
    breakdown       TEXT,
    rationale       TEXT,
    raw_text        TEXT,
    title           TEXT,
    company         TEXT,
    location        TEXT,
    work_mode       TEXT,
    department      TEXT,
    summary         TEXT,
    responsibilities TEXT,
    role_objectives TEXT,
    years_experience TEXT,
    education_level TEXT,
    skills_required TEXT,
    skills_nice     TEXT,
    languages_required TEXT,
    contract_type   TEXT,
    hr_contact      TEXT,
    pros            TEXT,
    cons            TEXT
);
"""

# Columns added after the initial schema — applied via ALTER TABLE for existing DBs.
_MIGRATIONS = [
    "ALTER TABLE offers ADD COLUMN pros TEXT",
    "ALTER TABLE offers ADD COLUMN cons TEXT",
]


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    cur = conn.execute("PRAGMA table_info(offers)")
    existing = {row["name"] for row in cur.fetchall()}
    for stmt in _MIGRATIONS:
        col = stmt.split()[-2]  # e.g. "pros" from "ALTER TABLE offers ADD COLUMN pros TEXT"
        if col not in existing:
            conn.execute(stmt)


def init_schema() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)
        _migrate(conn)


def _serialize(offer: Offer) -> dict:
    row = offer.to_dict()
    for key in JSON_FIELDS:
        row[key] = json.dumps(row.get(key), ensure_ascii=False)
    row["recommended"] = 1 if row["recommended"] else 0
    return row


def _deserialize(row: sqlite3.Row) -> Offer:
    data = dict(row)
    for key in JSON_FIELDS:
        raw = data.get(key)
        data[key] = json.loads(raw) if raw else ([] if key != "breakdown" else {})
    data["recommended"] = bool(data["recommended"])
    return Offer(**data)


def exists(offer_id: str) -> bool:
    """True if the id is already known (in any status, including discarded)."""
    with _connect() as conn:
        cur = conn.execute("SELECT 1 FROM offers WHERE id = ? LIMIT 1", (offer_id,))
        return cur.fetchone() is not None


def upsert(offer: Offer) -> None:
    row = _serialize(offer)
    placeholders = ", ".join(f":{c}" for c in COLUMNS)
    columns = ", ".join(COLUMNS)
    updates = ", ".join(f"{c}=excluded.{c}" for c in COLUMNS if c != "id")
    sql = (
        f"INSERT INTO offers ({columns}) VALUES ({placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}"
    )
    with _connect() as conn:
        conn.execute(sql, row)


def get(offer_id: str) -> Offer | None:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM offers WHERE id = ?", (offer_id,))
        row = cur.fetchone()
        return _deserialize(row) if row else None


def list_offers(
    status: str | None = None,
    recommended_only: bool = False,
    include_discarded: bool = False,
    sort: str = "score",
) -> list[Offer]:
    clauses = []
    params: list = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    elif not include_discarded:
        clauses.append("status != ?")
        params.append(OfferStatus.DISCARDED.value)
    if recommended_only:
        clauses.append("recommended = 1")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order = "score DESC" if sort == "score" else "fetched_at DESC"
    # Keep NULL scores last when sorting by score.
    if sort == "score":
        order = "score IS NULL, score DESC, fetched_at DESC"

    with _connect() as conn:
        cur = conn.execute(f"SELECT * FROM offers {where} ORDER BY {order}", params)
        return [_deserialize(r) for r in cur.fetchall()]


def set_status(offer_id: str, status: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE offers SET status = ? WHERE id = ?", (status, offer_id)
        )
        return cur.rowcount > 0


def delete(offer_id: str) -> bool:
    """Soft delete: keep the row so the offer isn't re-ingested on the next run."""
    return set_status(offer_id, OfferStatus.DISCARDED.value)


def counts_by_status() -> dict:
    with _connect() as conn:
        cur = conn.execute("SELECT status, COUNT(*) AS n FROM offers GROUP BY status")
        return {r["status"]: r["n"] for r in cur.fetchall()}
