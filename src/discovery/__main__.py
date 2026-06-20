import argparse
import logging

from src.discovery import pipeline, store
from src.discovery.config import WEB_HOST, WEB_PORT


def _cmd_run(_args) -> None:
    summary = pipeline.run()
    print(f"Pipeline finished: {summary}")


def _cmd_ingest(args) -> None:
    summary = pipeline.ingest_url(args.url)
    print(f"Ingest finished: {summary}")


def _cmd_web(_args) -> None:
    import uvicorn

    store.init_schema()
    print(f"Serving Job Discovery UI at http://{WEB_HOST}:{WEB_PORT}")
    uvicorn.run("src.discovery.web.app:app", host=WEB_HOST, port=WEB_PORT)


def _cmd_email_auth(_args) -> None:
    from src.discovery import gmail_auth

    gmail_auth.authenticate()
    print("Gmail read-only access authorized. Token cached for future runs.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(prog="python -m src.discovery")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Run the discovery pipeline over all configured sources")

    ingest = sub.add_parser("ingest", help="Fetch + score a single job-offer URL")
    ingest.add_argument("url", help="Public job-offer URL")

    sub.add_parser("web", help="Serve the review web UI")

    sub.add_parser("email-auth", help="One-time interactive Gmail OAuth consent (read-only)")

    args = parser.parse_args()
    {
        "run": _cmd_run,
        "ingest": _cmd_ingest,
        "web": _cmd_web,
        "email-auth": _cmd_email_auth,
    }[args.command](args)


if __name__ == "__main__":
    main()
