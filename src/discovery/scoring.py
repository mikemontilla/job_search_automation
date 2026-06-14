import os

import anthropic
from dotenv import load_dotenv

from src.agent.tools.profile import read_profile
from src.discovery.config import MODEL, MAX_TOKENS, PROFILE_LANGUAGE

load_dotenv()

_SYSTEM = (
    "You are a precise job-offer analyst. Given the raw text of a single job "
    "posting and a candidate's professional profile, you (1) extract structured "
    "fields exactly as written in the posting and (2) score how well the offer "
    "matches the candidate. Never invent facts: if a field is absent from the "
    "posting, return null or an empty list. Base the score only on evidence in "
    "the posting versus the profile."
)

# Forced single tool call → guarantees structured JSON output.
_ANALYSIS_TOOL = {
    "name": "record_offer_analysis",
    "description": "Record the extracted fields and the compatibility analysis of a job offer.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": ["string", "null"], "description": "Job title."},
            "company": {"type": ["string", "null"]},
            "location": {"type": ["string", "null"], "description": "City, country."},
            "work_mode": {
                "type": ["string", "null"],
                "description": "One of: remote, hybrid, on-site, or null if unknown.",
            },
            "department": {"type": ["string", "null"], "description": "Team or department."},
            "summary": {"type": ["string", "null"], "description": "2-3 sentence role summary."},
            "responsibilities": {"type": "array", "items": {"type": "string"}},
            "role_objectives": {
                "type": ["string", "null"],
                "description": "What the role is expected to achieve.",
            },
            "years_experience": {
                "type": ["string", "null"],
                "description": "Min/preferred years of experience as stated.",
            },
            "education_level": {"type": ["string", "null"]},
            "skills_required": {"type": "array", "items": {"type": "string"}},
            "skills_nice": {"type": "array", "items": {"type": "string"}},
            "languages_required": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Languages and level, e.g. 'French B2'.",
            },
            "contract_type": {
                "type": ["string", "null"],
                "description": "CDI, CDD, stage, freelance, full-time, etc.",
            },
            "hr_contact": {"type": ["string", "null"]},
            "pros": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "2-4 concrete reasons why this offer is a strong match for the candidate. "
                    "Be specific: cite the matching skill, technology, domain or experience level. "
                    "Example: 'Python advanced level matches the required Python expertise'."
                ),
            },
            "cons": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "2-4 concrete gaps or weak points between the offer requirements and "
                    "the candidate's profile. Be honest and specific. "
                    "Example: 'No ROS2 experience in profile, listed as required skill'."
                ),
            },
            "breakdown": {
                "type": "object",
                "description": "Per-dimension match scores, each 0-100.",
                "properties": {
                    "skills": {"type": "integer"},
                    "experience_level": {"type": "integer"},
                    "languages": {"type": "integer"},
                    "domain_sector": {"type": "integer"},
                    "location_contract": {"type": "integer"},
                },
                "required": [
                    "skills", "experience_level", "languages",
                    "domain_sector", "location_contract",
                ],
            },
            "score": {
                "type": "integer",
                "description": "Overall compatibility 0-100 (holistic, not just the average).",
            },
            "rationale": {
                "type": "string",
                "description": "One short paragraph justifying the score.",
            },
        },
        "required": ["score", "breakdown", "rationale", "pros", "cons"],
    },
}

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def analyze_offer(raw_text: str, profile: str | None = None) -> dict:
    """Single AI call: extract structured fields + compatibility score.

    Returns a dict ready to merge into an Offer via apply_scoring().
    """
    if profile is None:
        profile = read_profile(PROFILE_LANGUAGE)

    user_message = (
        "## Candidate profile\n"
        f"{profile}\n\n"
        "## Job offer (raw text)\n"
        f"{raw_text[:18000]}\n\n"
        "Extract the fields and score the match. Call record_offer_analysis."
    )

    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=_SYSTEM,
        tools=[_ANALYSIS_TOOL],
        tool_choice={"type": "tool", "name": "record_offer_analysis"},
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "record_offer_analysis":
            return dict(block.input)

    raise RuntimeError("Model did not return a record_offer_analysis tool call.")
