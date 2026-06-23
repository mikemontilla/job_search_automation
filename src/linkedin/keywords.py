"""Token-free aggregation of in-demand skills/keywords from discovery offers.

Gives LinkedIn optimization a real picture of "what the target market asks for"
without spending any AI tokens — it's a frequency count over data discovery
already collected and scored.
"""
import re
from collections import Counter

from src.discovery import store as discovery_store
from src.discovery.models import OfferStatus

_STOPWORDS = {
    # EN
    "the", "and", "for", "with", "of", "in", "on", "to", "or", "at", "a", "an",
    # FR
    "le", "la", "les", "de", "des", "du", "et", "en", "un", "une", "pour", "dans", "au", "aux",
}


def _normalize(term: str) -> str:
    return term.strip().lower()


def _tokenize_title(title: str | None) -> list[str]:
    words = re.split(r"[^\w]+", title or "", flags=re.UNICODE)
    return [w for w in words if len(w) >= 3 and w.lower() not in _STOPWORDS and not w.isdigit()]


def _as_list(value) -> list:
    """Guard against offers where the AI extraction stored a bare string instead of a list."""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def target_keywords(scope: str = "recommended", limit: int = 30) -> list[dict]:
    """Rank skills and title terms by frequency across discovery offers.

    scope:
      "recommended" (default) — offers the AI scored as a good match, plus any offer
                                 Miguel actually applied to (status=applying), even if it
                                 scored low — both are real signals of the target market
      "all" — every non-discarded offer
    """
    offers = discovery_store.list_offers()
    if scope != "all":
        offers = [o for o in offers if o.recommended or o.status == OfferStatus.APPLYING.value]

    counts: Counter = Counter()
    display: dict[str, str] = {}

    def _add(term: str) -> None:
        term = (term or "").strip()
        if not term:
            return
        key = _normalize(term)
        counts[key] += 1
        display.setdefault(key, term)

    for offer in offers:
        for skill in _as_list(offer.skills_required) + _as_list(offer.skills_nice):
            _add(skill)
        for word in _tokenize_title(offer.title):
            _add(word)

    return [{"keyword": display[key], "count": n} for key, n in counts.most_common(limit)]
