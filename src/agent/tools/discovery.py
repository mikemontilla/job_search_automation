"""Read-only bridge into the discovery pipeline's SQLite store (src/discovery/).

Discovery is a separate, deterministic pipeline (search, fetch, score) that
writes to data/discovery.db. The conversational agent only reads from it here
to reference a discovered offer when generating a CV or prepping an interview
— it never re-implements scoring or fetching.
"""
from src.discovery import pipeline, store

# Fields useful for skimming a list of offers; the full Offer has many more
# (raw_text, breakdown, pros/cons...) that only matter once one is selected.
_LIST_FIELDS = ["id", "title", "company", "location", "contract_type", "score", "status", "source_url"]


def list_discovered_offers(
    status: str | None = None,
    recommended_only: bool = False,
    limit: int = 20,
) -> list[dict]:
    offers = store.list_offers(status=status, recommended_only=recommended_only)
    return [
        {field: getattr(offer, field) for field in _LIST_FIELDS}
        for offer in offers[:limit]
    ]


def load_discovered_offer(offer_id: str) -> dict | str:
    offer = store.get(offer_id)
    if not offer:
        return f"No discovered offer found with id '{offer_id}'. Use list_discovered_offers to see available ids."
    return offer.to_dict()


def run_job_search() -> dict:
    """Trigger the discovery pipeline over all configured sources right now."""
    return pipeline.run()
