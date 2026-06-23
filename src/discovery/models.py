import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from urllib.parse import urlsplit, urlunsplit


class OfferStatus(str, Enum):
    NEW = "new"           # freshly discovered, not yet looked at
    REVIEWED = "reviewed"  # user has read it but taken no action
    APPLYING = "applying"  # user started an application process
    DISCARDED = "discarded"  # user deleted it (soft delete, keeps the id so it isn't re-ingested)


# Structured fields extracted from each offer (requirement 2.1).
# List-typed fields are stored as JSON text in SQLite.
LIST_FIELDS = {"responsibilities", "skills_required", "skills_nice", "languages_required", "pros", "cons"}
JSON_FIELDS = LIST_FIELDS | {"breakdown"}


def canonical_url(url: str) -> str:
    """Normalize a URL so the same offer always hashes to the same id.

    Drops query string and fragment (tracking params), lowercases the host,
    and strips a trailing slash from the path.
    """
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def make_id(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()[:16]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Offer:
    id: str
    source_url: str
    source_type: str = "manual"
    fetched_at: str = field(default_factory=_now)
    published_date: str | None = None
    status: str = OfferStatus.NEW.value
    score: int | None = None
    recommended: bool = False
    breakdown: dict = field(default_factory=dict)
    rationale: str | None = None
    raw_text: str | None = None

    # Structured fields (requirement 2.1)
    title: str | None = None
    company: str | None = None
    location: str | None = None
    work_mode: str | None = None        # remote / hybrid / on-site
    department: str | None = None
    summary: str | None = None
    responsibilities: list = field(default_factory=list)
    role_objectives: str | None = None
    years_experience: str | None = None
    education_level: str | None = None
    skills_required: list = field(default_factory=list)
    skills_nice: list = field(default_factory=list)
    languages_required: list = field(default_factory=list)
    contract_type: str | None = None
    hr_contact: str | None = None
    pros: list = field(default_factory=list)
    cons: list = field(default_factory=list)

    @classmethod
    def new(cls, source_url: str, source_type: str = "manual", raw_text: str | None = None) -> "Offer":
        return cls(
            id=make_id(source_url),
            source_url=source_url.strip(),
            source_type=source_type,
            raw_text=raw_text,
        )

    def apply_scoring(self, data: dict, threshold: int) -> None:
        """Merge the AI extract+score result into this offer."""
        for key, value in data.items():
            if not hasattr(self, key):
                continue
            if key in LIST_FIELDS and isinstance(value, str):
                value = [value] if value.strip() else []
            setattr(self, key, value)
        if self.score is not None:
            self.recommended = self.score >= threshold

    def to_dict(self) -> dict:
        return asdict(self)
