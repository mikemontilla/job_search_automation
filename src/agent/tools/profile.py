import re
from src.agent.config import PROFILE_FILES, SECTION_HEADINGS


def read_profile(language: str, section_key: str | None = None) -> str:
    path = PROFILE_FILES[language]
    content = path.read_text(encoding="utf-8")

    if section_key is None:
        return content

    heading = SECTION_HEADINGS[section_key][language]
    match = re.search(
        rf"(## {re.escape(heading)}.*?)(?=\n## |\Z)",
        content,
        re.DOTALL,
    )
    if not match:
        return f"Section '{heading}' not found in {language} profile."

    return match.group(1).strip()


def update_profile_section(language: str, section_key: str, new_content: str) -> dict:
    path = PROFILE_FILES[language]
    content = path.read_text(encoding="utf-8")
    heading = SECTION_HEADINGS[section_key][language]

    pattern = rf"(## {re.escape(heading)}.*?)(?=\n## |\Z)"
    if not re.search(pattern, content, re.DOTALL):
        return {"success": False, "error": f"Section '{heading}' not found in {language} profile."}

    updated = re.sub(pattern, new_content.strip(), content, flags=re.DOTALL)
    if not updated.endswith("\n"):
        updated += "\n"
    path.write_text(updated, encoding="utf-8")

    return {"success": True, "section": heading, "language": language}
