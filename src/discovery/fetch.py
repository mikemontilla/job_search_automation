import html
import re

import httpx

from src.discovery.config import FETCH_TIMEOUT

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# If the extracted text is shorter than this, the page is probably JS-rendered
# and we retry with a real browser. Keep the threshold low — a JS shell page
# can still return a few hundred chars of boilerplate that isn't job content.
_MIN_TEXT_LEN = 200


class FetchError(RuntimeError):
    pass


def _html_to_text(raw_html: str) -> str:
    # Drop scripts/styles/noscript, then strip tags and collapse whitespace.
    cleaned = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", raw_html)
    cleaned = re.sub(r"(?is)<br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", cleaned)
    text = re.sub(r"(?s)<[^>]+>", " ", cleaned)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*", "\n\n", text)
    return text.strip()


def _fetch_httpx(url: str, timeout: int) -> str:
    try:
        resp = httpx.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": _UA, "Accept-Language": "en,fr;q=0.8,es;q=0.6"},
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise FetchError(f"httpx fetch failed: {exc}") from exc
    return _html_to_text(resp.text)


def _fetch_playwright(url: str, timeout: int) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        raise FetchError(
            "Playwright not installed. Run: playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=_UA)
            page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            # Wait until the network goes quiet — critical for JS-heavy SPAs (Workday,
            # Greenhouse, etc.) that fetch job data via XHR after the initial page load.
            try:
                page.wait_for_load_state("networkidle", timeout=10_000)
            except Exception:
                # Long-polling or WebSocket pages never reach networkidle; fall back
                # to a fixed wait so we at least capture what's rendered so far.
                page.wait_for_timeout(3000)
            content = page.content()
        finally:
            browser.close()
    return _html_to_text(content)


def fetch(url: str, timeout: int | None = None) -> str:
    """Return readable plain text for a job-offer URL.

    Tries a plain HTTP request first; if the page yields too little text
    (JS-rendered or blocked), retries with a headless browser.
    """
    timeout = timeout or FETCH_TIMEOUT
    text = ""
    try:
        text = _fetch_httpx(url, timeout)
    except FetchError:
        text = ""

    if len(text) < _MIN_TEXT_LEN:
        try:
            browser_text = _fetch_playwright(url, timeout)
            if len(browser_text) > len(text):
                text = browser_text
        except FetchError:
            pass

    if not text:
        raise FetchError(f"Could not extract any text from {url}")
    return text
