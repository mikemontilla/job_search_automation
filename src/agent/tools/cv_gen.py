import base64
import json
import re
import shutil
from pathlib import Path
from src.agent.config import CV_TEMPLATE_DIR, APPLICATIONS_DIR
from src.agent.session import add_recent_cv

TEMPLATE_FILES = ["support.js", "image-slot.js"]
UPLOADS_DIR = CV_TEMPLATE_DIR / "uploads"


def _photo_to_data_url(photo_filename: str) -> str | None:
    path = UPLOADS_DIR / photo_filename
    if not path.exists():
        return None
    suffix = path.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


def _build_standalone_html(cv_data: dict) -> str:
    """Return template HTML with profile data and photo inlined — no fetch() needed."""
    template = (CV_TEMPLATE_DIR / "CV Template.dc.html").read_text(encoding="utf-8")

    # Embed photo as base64 so it loads without a server
    data = dict(cv_data)
    photo_filename = data.get("photo", "")
    if photo_filename and not photo_filename.startswith("data:"):
        data_url = _photo_to_data_url(photo_filename)
        if data_url:
            data["photo"] = data_url

    inline = f"const __PROFILE__ = {json.dumps(data, ensure_ascii=False)};"

    # Replace fetch block with a resolved Promise using inlined data
    fetch_pattern = r"fetch\('./profile\.json'\)\s*\.then\(\(r\)\s*=>\s*r\.json\(\)\)"
    patched = re.sub(fetch_pattern, "Promise.resolve(__PROFILE__)", template)

    # Inject inline data just before </body>
    patched = patched.replace("</body>", f"<script>{inline}</script>\n</body>")
    return patched


def generate_cv_json(language: str, job_slug: str, cv_data: dict) -> dict:
    output_dir = APPLICATIONS_DIR / job_slug / language
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy JS support files
    for filename in TEMPLATE_FILES:
        src = CV_TEMPLATE_DIR / filename
        dst = output_dir / filename
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    # Write profile.json as reference
    json_path = output_dir / "profile.json"
    json_path.write_text(json.dumps(cv_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write standalone HTML with data and photo inlined
    html_path = output_dir / "cv.html"
    html_path.write_text(_build_standalone_html(cv_data), encoding="utf-8")

    add_recent_cv(job_slug, language, str(json_path))

    return {
        "success": True,
        "folder": str(output_dir),
        "html_path": str(html_path),
        "instruction": f"Open '{html_path}' in your browser and print to PDF (Legal size, no margins).",
    }


def list_available_photos() -> list[str]:
    """Return filenames of all photos available in the uploads folder."""
    if not UPLOADS_DIR.exists():
        return []
    return [f.name for f in sorted(UPLOADS_DIR.iterdir()) if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
