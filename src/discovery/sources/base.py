from dataclasses import dataclass
from typing import Iterable, Protocol


@dataclass
class RawOffer:
    """The minimum a source must produce: where the offer lives and its text.

    `raw_text` may be None, in which case the pipeline fetches it from the URL.
    """
    source_url: str
    source_type: str
    raw_text: str | None = None


class Source(Protocol):
    """A source yields raw offers. Implementations live alongside this file."""

    def collect(self) -> Iterable[RawOffer]:
        ...
