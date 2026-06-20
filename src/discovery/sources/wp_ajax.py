import logging
from typing import Iterable

import httpx

from src.discovery.config import FETCH_TIMEOUT
from src.discovery.fetch import _UA, FetchError
from src.discovery.sources.base import RawOffer, Source

logger = logging.getLogger("discovery")


class WpAjaxJsonSource(Source):
    """A WordPress admin-ajax.php endpoint that returns job offers as JSON.

    Some career sites (e.g. those built on Zoho Recruit, like Serma's) filter
    job listings server-side via a POST to `wp-admin/admin-ajax.php` instead
    of changing the page URL. Calling that endpoint directly with the right
    `payload` does the filtering for free (no Playwright, no wasted AI calls
    scoring offers that don't match the keyword/company/contract filters).

    `id_field` is the key in each post holding the numeric/string job id;
    `detail_url_template` builds the public offer URL from it (`{id}`
    placeholder). `posts_path` is the list of keys to walk from the JSON root
    down to the list of post dicts.
    """

    def __init__(
        self,
        name: str,
        ajax_url: str,
        payload: dict,
        detail_url_template: str,
        id_field: str = "id",
        posts_path: tuple[str, ...] = ("data", "posts"),
    ):
        self.name = name
        self.ajax_url = ajax_url.strip()
        self.payload = payload
        self.detail_url_template = detail_url_template
        self.id_field = id_field
        self.posts_path = posts_path

    def collect(self) -> Iterable[RawOffer]:
        try:
            posts = self._fetch_posts()
        except FetchError as exc:
            logger.warning("wp_ajax source '%s' failed: %s", self.name, exc)
            return
        except Exception as exc:  # noqa: BLE001 - never let one bad source kill the run
            logger.warning("wp_ajax source '%s' failed unexpectedly: %s", self.name, exc)
            return

        logger.info("wp_ajax '%s': found %d offer(s)", self.name, len(posts))
        for post in posts:
            post_id = post.get(self.id_field)
            if not post_id:
                continue
            url = self.detail_url_template.format(id=post_id)
            yield RawOffer(source_url=url, source_type="career_page")

    def _fetch_posts(self) -> list[dict]:
        try:
            resp = httpx.post(
                self.ajax_url,
                data=self.payload,
                headers={"User-Agent": _UA},
                timeout=FETCH_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise FetchError(f"wp_ajax request failed: {exc}") from exc
        except ValueError as exc:
            raise FetchError(f"wp_ajax response was not JSON: {exc}") from exc

        node = data
        for key in self.posts_path:
            if not isinstance(node, dict) or key not in node:
                raise FetchError(f"wp_ajax response missing path {self.posts_path}")
            node = node[key]
        if not isinstance(node, list):
            raise FetchError(f"wp_ajax response path {self.posts_path} is not a list")
        return node
