import logging
import re
from typing import Iterable

from src.discovery.config import FETCH_TIMEOUT
from src.discovery.fetch import _UA, FetchError, goto_and_settle
from src.discovery.sources.base import RawOffer, Source

logger = logging.getLogger("discovery")

# Used only when a source has no explicit link_selector: keeps anchors that
# look like an individual job-detail page rather than a nav/filter link.
_DEFAULT_LINK_PATTERN = re.compile(r"/(job|jobs|details|posting|vacancy)/", re.I)


class CareerPageSource(Source):
    """A pre-filtered company search/listing page that lists many offers at once.

    Each entry under discovery_config.yaml -> sources[] is one such page —
    the URL already has the user's keyword/location filters applied. This
    source only extracts individual offer links; the pipeline fetches and
    scores each one separately (and skips it for free if already known).

    Career pages vary too much in markup to scrape generically, so each
    source can set `link_selector` (a CSS selector matching the `<a>` tags
    that link to a single offer). Without one, a best-effort URL pattern
    is used instead — works for some sites, but a configured selector is
    much more reliable.
    """

    def __init__(self, name: str, url: str, link_selector: str | None = None):
        self.name = name
        self.url = url.strip()
        self.link_selector = link_selector

    def collect(self) -> Iterable[RawOffer]:
        try:
            links = self._extract_links()
        except FetchError as exc:
            logger.warning("career_page source '%s' failed: %s", self.name, exc)
            return
        except Exception as exc:  # noqa: BLE001 - never let one bad source kill the run
            logger.warning("career_page source '%s' failed unexpectedly: %s", self.name, exc)
            return

        logger.info("career_page '%s': found %d offer link(s)", self.name, len(links))
        for href in links:
            yield RawOffer(source_url=href, source_type="career_page")

    def _extract_links(self) -> list[str]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise FetchError(
                "Playwright not installed. Run: playwright install chromium"
            ) from exc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(user_agent=_UA)
                goto_and_settle(page, self.url, FETCH_TIMEOUT)
                selector = self.link_selector or "a"
                # `e.href` (not getAttribute) so relative paths resolve to absolute URLs.
                hrefs = page.eval_on_selector_all(selector, "els => els.map(e => e.href)")
            finally:
                browser.close()

        seen: set[str] = set()
        links: list[str] = []
        for href in hrefs:
            if not href or href in seen:
                continue
            if self.link_selector or _DEFAULT_LINK_PATTERN.search(href):
                seen.add(href)
                links.append(href)
        return links
