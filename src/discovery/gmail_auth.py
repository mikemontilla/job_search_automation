"""Read-only Gmail OAuth — used to fetch LinkedIn/Indeed job-alert emails.

First run requires interactive consent in a real browser (`authenticate()`),
so it must be triggered by the user via `python -m src.discovery email-auth`,
not from an automated/headless context. After that, the cached token in
`config/gmail_token.json` is reused (and silently refreshed) by every
subsequent pipeline run.
"""
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.agent.config import CONFIG_DIR

logger = logging.getLogger("discovery")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_SECRET_PATH = CONFIG_DIR / "gmail_client_secret.json"
TOKEN_PATH = CONFIG_DIR / "gmail_token.json"


class GmailAuthError(RuntimeError):
    pass


def authenticate() -> None:
    """Run the interactive OAuth consent flow and cache the resulting token.

    Opens a local browser tab; the user logs in and grants read-only Gmail
    access. Must be run by a human once — there is nothing to automate here.
    """
    if not CLIENT_SECRET_PATH.exists():
        raise GmailAuthError(
            f"Missing {CLIENT_SECRET_PATH}. Download the OAuth client secret "
            "from Google Cloud Console (Desktop app credential) and save it there."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    logger.info("Gmail OAuth token saved to %s", TOKEN_PATH)


def get_service():
    """Return an authenticated Gmail API client, refreshing the token if needed."""
    if not TOKEN_PATH.exists():
        raise GmailAuthError(
            "No Gmail token found. Run: python -m src.discovery email-auth"
        )
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise GmailAuthError(
                "Gmail token is invalid/expired and has no refresh token. "
                "Re-run: python -m src.discovery email-auth"
            )
    return build("gmail", "v1", credentials=creds)
