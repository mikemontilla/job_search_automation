import json
from datetime import date
from src.agent.config import SESSION_LOG


def load_session() -> tuple[list, str | None]:
    """Returns (messages, last_note)."""
    if not SESSION_LOG.exists():
        return [], None
    data = json.loads(SESSION_LOG.read_text(encoding="utf-8"))
    return [], data.get("last_note")


def save_session_note(note: str) -> dict:
    data = {}
    if SESSION_LOG.exists():
        data = json.loads(SESSION_LOG.read_text(encoding="utf-8"))

    data["last_note"] = note[:200]
    data["last_updated"] = date.today().isoformat()

    if "recent_cvs" not in data:
        data["recent_cvs"] = []

    SESSION_LOG.parent.mkdir(parents=True, exist_ok=True)
    SESSION_LOG.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"saved": True}


def add_recent_cv(slug: str, language: str, path: str) -> None:
    data = {}
    if SESSION_LOG.exists():
        data = json.loads(SESSION_LOG.read_text(encoding="utf-8"))

    recent = data.get("recent_cvs", [])
    recent.insert(0, {"slug": slug, "language": language, "path": path, "date": date.today().isoformat()})
    data["recent_cvs"] = recent[:10]

    SESSION_LOG.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
