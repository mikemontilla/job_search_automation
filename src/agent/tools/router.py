from src.agent.tools.profile import read_profile, update_profile_section


def _list_job_offers():
    from src.agent.tools.jobs import list_job_offers
    return list_job_offers()


def _load_job_description(job_id):
    from src.agent.tools.jobs import load_job_description
    return load_job_description(job_id)


def _generate_cv_pdf(language, job_slug, cv_data, accent_color=None):
    from src.agent.tools.cv_gen import generate_cv_pdf
    return generate_cv_pdf(language, job_slug, cv_data, accent_color)


def _save_session_note(note):
    from src.agent.session import save_session_note
    return save_session_note(note)


TOOL_HANDLERS = {
    "read_profile": lambda args: read_profile(
        args["language"], args.get("section_key")
    ),
    "update_profile_section": lambda args: update_profile_section(
        args["language"], args["section_key"], args["new_content"]
    ),
    "list_job_offers": lambda args: _list_job_offers(),
    "load_job_description": lambda args: _load_job_description(args["job_id"]),
    "generate_cv_pdf": lambda args: _generate_cv_pdf(
        args["language"], args["job_slug"], args["cv_data"], args.get("accent_color")
    ),
    "save_session_note": lambda args: _save_session_note(args["note"]),
}


def dispatch(tool_name: str, tool_input: dict):
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return handler(tool_input)
