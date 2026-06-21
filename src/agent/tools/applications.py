"""Read/write bridge into the tracking store (src/tracking/) for interview prep & strategy.

Tracking is a deterministic store (applications/<slug>/ folder + applications/
application_events tables) that the conversational agent reads from and writes
prep material into — it never re-implements promotion or scoring logic.
"""
from src.tracking import service, store
from src.tracking.models import ApplicationEvent

_LIST_FIELDS = ["id", "title", "company", "location", "stage", "next_action", "next_action_date", "updated_at"]


def list_applications(stage: str | None = None) -> list[dict]:
    applications = store.list_applications(stage=stage)
    return [{field: getattr(app, field) for field in _LIST_FIELDS} for app in applications]


def load_application(app_id: str) -> dict | str:
    application = store.get(app_id)
    if not application:
        return f"No application found with id '{app_id}'. Use list_applications to see available ids."

    files = service.file_inventory(app_id)
    job_description = ""
    jd_path = service.resolve_file(app_id, "job_description.md")
    if jd_path:
        job_description = jd_path.read_text(encoding="utf-8")

    result = {
        "application": application.to_dict(),
        "files": files,
        "job_description": job_description,
        "events": [e.to_dict() for e in store.list_events(app_id)],
        "discovered_offer": None,
    }

    if application.offer_id:
        from src.agent.tools.discovery import load_discovered_offer
        result["discovered_offer"] = load_discovered_offer(application.offer_id)

    return result


def read_application_file(app_id: str, relpath: str) -> str:
    path = service.resolve_file(app_id, relpath)
    if not path or not path.is_file():
        return f"No file '{relpath}' found for application '{app_id}'."
    return path.read_text(encoding="utf-8")


def save_prep_document(app_id: str, kind: str, content_md: str) -> dict | str:
    application = store.get(app_id)
    if not application:
        return f"No application found with id '{app_id}'."
    path = service.write_doc(app_id, f"prep/{kind}.md", content_md)
    store.add_event(ApplicationEvent(
        application_id=app_id,
        event_type="document_added",
        title=f"Prep document saved: {kind}",
    ))
    return {"path": str(path)}


def save_interviewer_research(app_id: str, slug: str, content_md: str) -> dict | str:
    application = store.get(app_id)
    if not application:
        return f"No application found with id '{app_id}'."
    path = service.write_doc(app_id, f"research/interviewer_{slug}.md", content_md)
    store.add_event(ApplicationEvent(
        application_id=app_id,
        event_type="document_added",
        title=f"Interviewer research saved: {slug}",
    ))
    return {"path": str(path)}


def update_application(
    app_id: str,
    stage: str | None = None,
    hr_contact: dict | None = None,
    notes: str | None = None,
    next_action: str | None = None,
    next_action_date: str | None = None,
) -> dict | str:
    application = store.get(app_id)
    if not application:
        return f"No application found with id '{app_id}'."

    if stage is not None:
        application.stage = stage
    if hr_contact is not None:
        application.hr_contact = hr_contact
    if notes is not None:
        application.notes = notes
    if next_action is not None:
        application.next_action = next_action
    if next_action_date is not None:
        application.next_action_date = next_action_date

    store.upsert(application)
    return application.to_dict()


def log_application_event(
    app_id: str,
    event_type: str,
    title: str | None = None,
    detail: str | None = None,
    event_date: str | None = None,
) -> dict | str:
    application = store.get(app_id)
    if not application:
        return f"No application found with id '{app_id}'."

    event = ApplicationEvent(
        application_id=app_id,
        event_type=event_type,
        title=title,
        detail=detail,
        event_date=event_date,
    )
    event_id = store.add_event(event)
    return {"event_id": event_id}
