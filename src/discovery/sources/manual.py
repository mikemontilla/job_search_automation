from typing import Iterable

from src.discovery.sources.base import RawOffer, Source


class ManualSource(Source):
    """A user-pasted public job URL (requirement 2.5).

    The text is left to the pipeline to fetch so the dedup check can run
    before any network/AI work when the offer is already known.
    """

    def __init__(self, url: str):
        self.url = url.strip()

    def collect(self) -> Iterable[RawOffer]:
        if self.url:
            yield RawOffer(source_url=self.url, source_type="manual")
