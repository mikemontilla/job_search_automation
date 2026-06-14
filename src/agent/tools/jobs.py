from src.agent.config import APPLICATIONS_DIR, DATA_DIR

APPLICATION_DATA_DIR = DATA_DIR / "application_data"


def list_job_offers() -> list[dict]:
    offers = []
    idx = 1

    for directory in [APPLICATIONS_DIR, APPLICATION_DATA_DIR]:
        if not directory.exists():
            continue
        for folder in sorted(directory.iterdir()):
            if not folder.is_dir() or folder.name.startswith("."):
                continue
            jd_file = folder / "job_description.md"
            offers.append({
                "id": str(idx),
                "slug": folder.name,
                "folder": str(folder),
                "has_description": jd_file.exists(),
            })
            idx += 1

    return offers


def load_job_description(job_id: str) -> str:
    offers = list_job_offers()

    # Match by numeric index or slug
    match = None
    for offer in offers:
        if offer["id"] == job_id or offer["slug"] == job_id:
            match = offer
            break

    if not match:
        return f"Job offer '{job_id}' not found. Use list_job_offers to see available offers."

    jd_file = match["folder"] + "/job_description.md"
    from pathlib import Path
    path = Path(jd_file)
    if not path.exists():
        return f"No job_description.md found in '{match['slug']}'. Create the file and add the job description."

    return path.read_text(encoding="utf-8")
