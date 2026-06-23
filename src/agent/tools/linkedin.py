"""Read/write bridge for LinkedIn profile optimization (src/linkedin/).

Reuses the .md profile (source of truth, Phase 1) and discovery's
target_keywords() (token-free market aggregation, Phase 2) so the agent can
draft recommendations and post material — it never browses or logs into
LinkedIn itself; Miguel pastes/imports his profile and reports back anything
that needs research.
"""
from src.agent.tools.profile import read_profile
from src.linkedin import keywords, service


def load_linkedin_profile(language: str = "en") -> dict:
    return {
        "profile": read_profile(language),
        "snapshot": service.read_snapshot(),
        "files": service.file_inventory(),
        "target_keywords": keywords.target_keywords(),
    }


def save_linkedin_snapshot(content_md: str) -> dict:
    path = service.write_snapshot(content_md)
    return {"path": str(path)}


def save_linkedin_recommendation(section: str, content_md: str) -> dict:
    path = service.write_recommendation(section, content_md)
    return {"path": str(path)}


def read_linkedin_file(relpath: str) -> str:
    path = service.resolve_file(relpath)
    if not path or not path.is_file():
        return f"No file '{relpath}' found in data/linkedin/."
    return path.read_text(encoding="utf-8")


def save_linkedin_post(slug: str, content_md: str) -> dict:
    path = service.write_post(slug, content_md)
    return {"path": str(path)}


def list_linkedin_posts() -> list[str]:
    return service.file_inventory()["posts"]
