import re
import unicodedata

from src.agent.config import APPLICATIONS_DIR
from src.discovery import store as discovery_store
from src.discovery.models import OfferStatus
from src.tracking import store
from src.tracking.models import Application, ApplicationEvent, ApplicationStage, EventType

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(company: str | None, title: str | None) -> str:
    raw = f"{company or 'unknown'}-{title or 'role'}"
    normalized = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_RE.sub("-", normalized.lower()).strip("-")
    return slug or "application"


def _unique_slug(base: str) -> str:
    slug = base
    suffix = 2
    while store.get(slug) is not None or (APPLICATIONS_DIR / slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def promote_offer(offer_id: str) -> Application:
    """Create an Application from a discovered offer, seed its folder, and mark the offer as applying."""
    offer = discovery_store.get(offer_id)
    if not offer:
        raise ValueError(f"No discovered offer found with id '{offer_id}'")

    slug = _unique_slug(_slugify(offer.company, offer.title))

    folder = APPLICATIONS_DIR / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "prep").mkdir(exist_ok=True)
    (folder / "research").mkdir(exist_ok=True)
    (folder / "job_description.md").write_text(offer.raw_text or "", encoding="utf-8")

    application = Application.new(
        slug,
        offer_id=offer.id,
        title=offer.title,
        company=offer.company,
        location=offer.location,
        source_url=offer.source_url,
        stage=ApplicationStage.INTERESTED.value,
    )
    store.upsert(application)

    discovery_store.set_status(offer.id, OfferStatus.APPLYING.value)

    store.add_event(ApplicationEvent(
        application_id=slug,
        event_type=EventType.STAGE_CHANGE.value,
        title="Application created",
        detail=f"Promoted from discovered offer {offer.id}",
    ))

    return application
