from src.agent.tools.profile import read_profile, update_profile_section


def _list_job_offers():
    from src.agent.tools.jobs import list_job_offers
    return list_job_offers()


def _load_job_description(job_id):
    from src.agent.tools.jobs import load_job_description
    return load_job_description(job_id)


def _generate_cv_json(language, job_slug, cv_data):
    from src.agent.tools.cv_gen import generate_cv_json
    return generate_cv_json(language, job_slug, cv_data)


def _save_session_note(note):
    from src.agent.session import save_session_note
    return save_session_note(note)


def _list_discovered_offers(status, recommended_only, limit):
    from src.agent.tools.discovery import list_discovered_offers
    return list_discovered_offers(status, recommended_only, limit)


def _load_discovered_offer(offer_id):
    from src.agent.tools.discovery import load_discovered_offer
    return load_discovered_offer(offer_id)


def _run_job_search():
    from src.agent.tools.discovery import run_job_search
    return run_job_search()


TOOL_HANDLERS = {
    "read_profile": lambda args: read_profile(
        args["language"], args.get("section_key")
    ),
    "update_profile_section": lambda args: update_profile_section(
        args["language"], args["section_key"], args["new_content"]
    ),
    "list_job_offers": lambda args: _list_job_offers(),
    "load_job_description": lambda args: _load_job_description(args["job_id"]),
    "generate_cv_json": lambda args: _generate_cv_json(
        args["language"], args["job_slug"], args["cv_data"]
    ),
    "save_session_note": lambda args: _save_session_note(args["note"]),
    "list_discovered_offers": lambda args: _list_discovered_offers(
        args.get("status"), args.get("recommended_only", False), args.get("limit", 20)
    ),
    "load_discovered_offer": lambda args: _load_discovered_offer(args["offer_id"]),
    "run_job_search": lambda args: _run_job_search(),
}


def dispatch(tool_name: str, tool_input: dict):
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return handler(tool_input)
