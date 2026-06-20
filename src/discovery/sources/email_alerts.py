import base64
import html as html_lib
import logging
import re
from typing import Iterable

from src.discovery import gmail_auth
from src.discovery.sources.base import RawOffer, Source

logger = logging.getLogger("discovery")

# Alert emails link the same job from several spots (logo, title, "View job"
# button), each with its own tracking params — without normalizing to a
# canonical URL first, dedup would treat them as different offers and waste
# an AI scoring call per duplicate.
_LINKEDIN_JOB_ID = re.compile(r"/jobs/view/(\d+)")
_INDEED_JOB_KEY = re.compile(r"[?&]jk=([a-zA-Z0-9]+)")


def _canonicalize(url: str) -> str:
    url = html_lib.unescape(url)
    if "linkedin.com" in url:
        m = _LINKEDIN_JOB_ID.search(url)
        if m:
            return f"https://www.linkedin.com/jobs/view/{m.group(1)}/"
    if "indeed.com" in url:
        m = _INDEED_JOB_KEY.search(url)
        if m:
            return f"https://www.indeed.com/viewjob?jk={m.group(1)}"
    return url

# Job-alert emails are full of unrelated links (header nav, footer, unsubscribe,
# "view profile", tracking pixels...). These patterns keep only links that
# actually point at an individual job posting on a known alert sender.
_DEFAULT_LINK_PATTERNS = [
    r"https?://[^\s\"'<>]*linkedin\.com/comm/jobs/view/[^\s\"'<>]*",
    r"https?://[^\s\"'<>]*linkedin\.com/jobs/view/[^\s\"'<>]*",
    r"https?://[^\s\"'<>]*indeed\.com/(?:rc/clk|viewjob|pagead)[^\s\"'<>]*",
]

_DEFAULT_SENDERS = [
    "jobs-noreply@linkedin.com",
    "jobalerts-noreply@linkedin.com",
    "alert@indeed.com",
    "indeedapply@indeed.com",
]


class EmailAlertsSource(Source):
    """Job offers found inside LinkedIn/Indeed job-alert emails in Gmail.

    Searches recent mail from the configured `senders`, extracts links that
    match `link_patterns` out of the HTML body, and yields each as a
    RawOffer — the pipeline's normal fetch (following redirects) resolves
    each tracking link down to the actual job-posting page.

    Read-only by design (`gmail.readonly` scope): this never marks messages
    as read or modifies the mailbox.
    """

    def __init__(
        self,
        senders: list[str] | None = None,
        link_patterns: list[str] | None = None,
        lookback_days: int = 14,
        max_results: int = 20,
    ):
        self.senders = senders or _DEFAULT_SENDERS
        self.patterns = [re.compile(p, re.I) for p in (link_patterns or _DEFAULT_LINK_PATTERNS)]
        self.lookback_days = lookback_days
        self.max_results = max_results

    def collect(self) -> Iterable[RawOffer]:
        try:
            service = gmail_auth.get_service()
        except gmail_auth.GmailAuthError as exc:
            logger.warning("email_alerts source disabled: %s", exc)
            return

        query = self._build_query()
        try:
            resp = service.users().messages().list(
                userId="me", q=query, maxResults=self.max_results,
            ).execute()
        except Exception as exc:  # noqa: BLE001 - never let Gmail API errors kill the run
            logger.warning("email_alerts: failed to list messages: %s", exc)
            return

        messages = resp.get("messages", [])
        logger.info("email_alerts: %d message(s) matched query %r", len(messages), query)

        seen: set[str] = set()
        for msg_meta in messages:
            try:
                links = self._extract_links(service, msg_meta["id"])
            except Exception as exc:  # noqa: BLE001
                logger.warning("email_alerts: failed to read message %s: %s", msg_meta["id"], exc)
                continue
            for link in links:
                if link in seen:
                    continue
                seen.add(link)
                yield RawOffer(source_url=link, source_type="email_alert")

    def _build_query(self) -> str:
        from_clause = " OR ".join(f"from:{s}" for s in self.senders)
        return f"({from_clause}) newer_than:{self.lookback_days}d"

    def _extract_links(self, service, message_id: str) -> list[str]:
        msg = service.users().messages().get(
            userId="me", id=message_id, format="full",
        ).execute()
        html = self._find_html_body(msg.get("payload", {}))
        if not html:
            return []
        links: list[str] = []
        for pattern in self.patterns:
            links.extend(_canonicalize(link) for link in pattern.findall(html))
        return links

    def _find_html_body(self, payload: dict) -> str:
        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data")
        if mime_type == "text/html" and body_data:
            return self._decode(body_data)

        for part in payload.get("parts", []):
            html = self._find_html_body(part)
            if html:
                return html
        return ""

    @staticmethod
    def _decode(data: str) -> str:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
