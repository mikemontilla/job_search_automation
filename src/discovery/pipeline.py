import logging

from src.discovery import run_status, store
from src.discovery.config import EMAIL, SCORE_THRESHOLD, SOURCES
from src.discovery.fetch import fetch, FetchError
from src.discovery.models import Offer, make_id
from src.discovery.scoring import analyze_offer
from src.discovery.sources.base import RawOffer, Source
from src.discovery.sources.career_page import CareerPageSource
from src.discovery.sources.email_alerts import EmailAlertsSource
from src.discovery.sources.manual import ManualSource
from src.discovery.sources.wp_ajax import WpAjaxJsonSource

logger = logging.getLogger("discovery")


def process_raw_offer(raw: RawOffer) -> str:
    """Process one raw offer. Returns one of: added, skipped, error.

    The dedup guard runs BEFORE any fetch or AI call so already-seen offers
    cost nothing (requirement 4).
    """
    offer_id = make_id(raw.source_url)

    if store.exists(offer_id):
        logger.info("skip (already seen, no AI call): %s", raw.source_url)
        run_status.report("skipped", f"Already known: {raw.source_url}")
        return "skipped"

    text = raw.raw_text
    if not text:
        try:
            text = fetch(raw.source_url)
        except FetchError as exc:
            logger.warning("fetch failed for %s: %s", raw.source_url, exc)
            run_status.report("error", f"Fetch failed: {raw.source_url}")
            return "error"

    offer = Offer.new(raw.source_url, source_type=raw.source_type, raw_text=text)
    try:
        analysis = analyze_offer(text)
    except Exception as exc:  # noqa: BLE001 - surface any AI/parse failure as an error count
        logger.warning("scoring failed for %s: %s", raw.source_url, exc)
        run_status.report("error", f"Analysis failed: {raw.source_url}")
        return "error"

    offer.apply_scoring(analysis, SCORE_THRESHOLD)
    store.upsert(offer)
    logger.info(
        "added: %s — %s @ %s (score %s)",
        offer.id, offer.title, offer.company, offer.score,
    )
    run_status.report("added", f"{offer.title or '(untitled)'} @ {offer.company or '—'} (score {offer.score})")
    return "added"


def process_source(source: Source) -> dict:
    init_summary = {"added": 0, "skipped": 0, "error": 0}
    store.init_schema()
    run_status.set_source(getattr(source, "name", source.__class__.__name__))
    for raw in source.collect():
        result = process_raw_offer(raw)
        init_summary[result] += 1
    return init_summary


def ingest_url(url: str) -> dict:
    """Ingest a single user-pasted URL (used by the web UI and CLI)."""
    return process_source(ManualSource(url))


def run() -> dict:
    """Run every configured source: career pages, wp_ajax, and (if enabled) email alerts."""
    store.init_schema()
    total = {"added": 0, "skipped": 0, "error": 0}
    sources = _configured_sources()
    if EMAIL.get("enabled"):
        sources.append(EmailAlertsSource(
            senders=EMAIL.get("senders"),
            link_patterns=EMAIL.get("link_patterns"),
            lookback_days=EMAIL.get("lookback_days", 14),
            max_results=EMAIL.get("max_results", 20),
        ))
    if not sources:
        logger.info("No automatic sources configured in discovery_config.yaml yet.")

    run_status.start()
    try:
        for source in sources:
            summary = process_source(source)
            for key in total:
                total[key] += summary[key]
    finally:
        run_status.finish()
    return total


def _configured_sources() -> list[Source]:
    sources: list[Source] = []
    for entry in SOURCES:
        if not isinstance(entry, dict):
            logger.warning("Skipping malformed source entry: %r", entry)
            continue
        kind = entry.get("type", "career_page")
        if kind == "wp_ajax":
            if not entry.get("ajax_url") or not entry.get("detail_url_template"):
                logger.warning("Skipping malformed wp_ajax source entry: %r", entry)
                continue
            sources.append(WpAjaxJsonSource(
                name=entry.get("name", entry["ajax_url"]),
                ajax_url=entry["ajax_url"],
                payload=entry.get("payload", {}),
                detail_url_template=entry["detail_url_template"],
                id_field=entry.get("id_field", "id"),
            ))
        elif kind == "career_page":
            if not entry.get("url"):
                logger.warning("Skipping malformed source entry: %r", entry)
                continue
            sources.append(CareerPageSource(
                name=entry.get("name", entry["url"]),
                url=entry["url"],
                link_selector=entry.get("link_selector"),
            ))
        else:
            logger.warning("Unknown source type %r in entry: %r", kind, entry)
    return sources
