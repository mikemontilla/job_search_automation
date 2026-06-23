from src.agent.config import LINKEDIN_DIR

_SNAPSHOT_RELPATH = "snapshot.md"


def resolve_file(relpath: str):
    """Resolve relpath inside data/linkedin/, guarding against path traversal. Returns None if outside or missing."""
    base = LINKEDIN_DIR.resolve()
    path = (base / relpath).resolve()
    if not path.is_relative_to(base) or not path.exists():
        return None
    return path


def write_doc(relpath: str, content_md: str):
    """Write a markdown doc inside data/linkedin/, creating parent dirs as needed."""
    base = LINKEDIN_DIR.resolve()
    path = (base / relpath).resolve()
    if not path.is_relative_to(base):
        raise ValueError(f"Path '{relpath}' escapes the LinkedIn data folder")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content_md, encoding="utf-8")
    return path


def read_snapshot() -> str | None:
    path = resolve_file(_SNAPSHOT_RELPATH)
    return path.read_text(encoding="utf-8") if path else None


def write_snapshot(content_md: str):
    return write_doc(_SNAPSHOT_RELPATH, content_md)


def write_recommendation(section: str, content_md: str):
    return write_doc(f"recommendations/{section}.md", content_md)


def write_post(slug: str, content_md: str):
    return write_doc(f"posts/{slug}.md", content_md)


def file_inventory() -> dict:
    """List the snapshot, recommendations, and post drafts already saved."""
    snapshot_path = LINKEDIN_DIR / _SNAPSHOT_RELPATH
    rec_dir, posts_dir = LINKEDIN_DIR / "recommendations", LINKEDIN_DIR / "posts"
    recommendations = sorted(
        p.relative_to(LINKEDIN_DIR).as_posix() for p in rec_dir.glob("*.md")
    ) if rec_dir.exists() else []
    posts = sorted(
        p.relative_to(LINKEDIN_DIR).as_posix() for p in posts_dir.glob("*.md")
    ) if posts_dir.exists() else []
    return {
        "snapshot": snapshot_path.exists(),
        "recommendations": recommendations,
        "posts": posts,
    }
