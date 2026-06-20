from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum


class ApplicationStage(str, Enum):
    INTERESTED = "interested"
    APPLIED = "applied"
    SCREENING = "screening"
    TECHNICAL = "technical"
    FINAL = "final"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class EventType(str, Enum):
    STAGE_CHANGE = "stage_change"
    NOTE = "note"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_DONE = "interview_done"
    DOCUMENT_ADDED = "document_added"


# List/dict-typed fields are stored as JSON text in SQLite.
JSON_FIELDS = {"cv_languages", "hr_contact"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Application:
    id: str  # slug, matches the applications/<slug>/ folder name
    offer_id: str | None = None  # FK to discovery offers.id, NULL if added manually
    title: str | None = None
    company: str | None = None
    location: str | None = None
    source_url: str | None = None
    stage: str = ApplicationStage.INTERESTED.value
    cv_languages: list = field(default_factory=list)
    hr_contact: dict = field(default_factory=dict)
    applied_date: str | None = None
    next_action: str | None = None
    next_action_date: str | None = None
    notes: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    @classmethod
    def new(cls, slug: str, **kwargs) -> "Application":
        return cls(id=slug, **kwargs)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ApplicationEvent:
    application_id: str
    event_type: str
    title: str | None = None
    detail: str | None = None
    event_date: str | None = None
    id: int | None = None
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)
