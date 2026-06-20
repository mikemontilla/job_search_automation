import logging
from contextlib import asynccontextmanager

import markdown as md
from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.agent.config import APPLICATIONS_DIR
from src.discovery import pipeline, store
from src.discovery.config import STATIC_DIR, TEMPLATES_DIR
from src.discovery.models import OfferStatus
from src.tracking import service, store as tracking_store
from src.tracking.models import ApplicationEvent, ApplicationStage, EventType

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.init_schema()
    tracking_store.init_schema()
    yield


app = FastAPI(title="Job Discovery", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/files", StaticFiles(directory=APPLICATIONS_DIR), name="files")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_ACTIVE_STATUSES = [s.value for s in OfferStatus]
_STAGES = [s.value for s in ApplicationStage]
_EVENT_TYPES = [e.value for e in EventType]


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    status: str | None = None,
    recommended: int = 0,
    sort: str = "score",
):
    offers = store.list_offers(
        status=status or None,
        recommended_only=bool(recommended),
        sort=sort,
    )
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "offers": offers,
            "status": status,
            "recommended_only": bool(recommended),
            "sort": sort,
            "statuses": _ACTIVE_STATUSES,
            "counts": store.counts_by_status(),
        },
    )


@app.get("/offer/{offer_id}", response_class=HTMLResponse)
def offer_detail(request: Request, offer_id: str):
    offer = store.get(offer_id)
    if not offer:
        return HTMLResponse("Offer not found", status_code=404)
    return templates.TemplateResponse(request, "detail.html", {"offer": offer})


@app.post("/ingest")
def ingest(url: str = Form(...)):
    """Fetch + score a single pasted URL synchronously (runs in a threadpool)."""
    summary = pipeline.ingest_url(url)
    if summary["added"]:
        return Response(headers={"HX-Redirect": "/"})
    if summary["skipped"]:
        return HTMLResponse("Already known — this offer is already in the list.")
    return HTMLResponse("Could not process that URL (fetch or analysis failed).")


@app.post("/run")
def run_pipeline(background: BackgroundTasks):
    background.add_task(pipeline.run)
    return HTMLResponse("Search started. New offers will appear after refresh.")


@app.post("/offer/{offer_id}/status")
def change_status(request: Request, offer_id: str, value: str, redirect: int = 0):
    if value not in _ACTIVE_STATUSES:
        return HTMLResponse(f"Invalid status: {value}", status_code=400)
    store.set_status(offer_id, value)
    if redirect:
        return Response(headers={"HX-Redirect": "/"})
    offer = store.get(offer_id)
    return templates.TemplateResponse(request, "_row.html", {"offer": offer})


@app.post("/offer/{offer_id}/delete")
def delete_offer(offer_id: str, redirect: int = 0):
    store.delete(offer_id)
    if redirect:
        return Response(headers={"HX-Redirect": "/"})
    return HTMLResponse("")


def _file_inventory(slug: str) -> dict:
    folder = APPLICATIONS_DIR / slug
    if not folder.exists():
        return {"cvs": [], "prep": [], "research": []}
    cvs = sorted(p.relative_to(folder).as_posix() for p in folder.glob("*/cv.html"))
    prep_dir, research_dir = folder / "prep", folder / "research"
    prep = sorted(p.relative_to(folder).as_posix() for p in prep_dir.glob("*.md")) if prep_dir.exists() else []
    research = sorted(p.relative_to(folder).as_posix() for p in research_dir.glob("*.md")) if research_dir.exists() else []
    return {"cvs": cvs, "prep": prep, "research": research}


@app.get("/applications", response_class=HTMLResponse)
def applications_index(request: Request, stage: str | None = None):
    applications = tracking_store.list_applications(stage=stage or None)
    return templates.TemplateResponse(
        request,
        "applications.html",
        {"applications": applications, "stage": stage, "stages": _STAGES},
    )


@app.get("/applications/{app_id}", response_class=HTMLResponse)
def application_detail(request: Request, app_id: str):
    application = tracking_store.get(app_id)
    if not application:
        return HTMLResponse("Application not found", status_code=404)
    job_description = ""
    jd_path = APPLICATIONS_DIR / app_id / "job_description.md"
    if jd_path.exists():
        job_description = jd_path.read_text(encoding="utf-8")
    return templates.TemplateResponse(
        request,
        "application_detail.html",
        {
            "application": application,
            "events": tracking_store.list_events(app_id),
            "stages": _STAGES,
            "event_types": _EVENT_TYPES,
            "files": _file_inventory(app_id),
            "job_description": job_description,
        },
    )


@app.post("/applications")
def create_application(offer_id: str = Form(...)):
    application = service.promote_offer(offer_id)
    return Response(headers={"HX-Redirect": f"/applications/{application.id}"})


@app.post("/applications/{app_id}/stage")
def change_application_stage(app_id: str, value: str, redirect_to: str = "detail"):
    if value not in _STAGES:
        return HTMLResponse(f"Invalid stage: {value}", status_code=400)
    tracking_store.set_stage(app_id, value)
    tracking_store.add_event(ApplicationEvent(
        application_id=app_id,
        event_type=EventType.STAGE_CHANGE.value,
        title=f"Stage changed to {value}",
    ))
    target = "/applications" if redirect_to == "list" else f"/applications/{app_id}"
    return Response(headers={"HX-Redirect": target})


@app.post("/applications/{app_id}/event")
def add_application_event(
    app_id: str,
    event_type: str = Form(...),
    title: str = Form(""),
    detail: str = Form(""),
    event_date: str = Form(""),
):
    if event_type not in _EVENT_TYPES:
        return HTMLResponse(f"Invalid event type: {event_type}", status_code=400)
    tracking_store.add_event(ApplicationEvent(
        application_id=app_id,
        event_type=event_type,
        title=title or None,
        detail=detail or None,
        event_date=event_date or None,
    ))
    return Response(headers={"HX-Redirect": f"/applications/{app_id}"})


@app.get("/applications/{app_id}/doc/{relpath:path}", response_class=HTMLResponse)
def application_doc(request: Request, app_id: str, relpath: str):
    base = (APPLICATIONS_DIR / app_id).resolve()
    path = (base / relpath).resolve()
    if not path.is_relative_to(base) or not path.exists() or path.suffix != ".md":
        return HTMLResponse("Not found", status_code=404)
    html = md.markdown(path.read_text(encoding="utf-8"))
    return templates.TemplateResponse(
        request, "doc.html", {"title": relpath, "html": html, "app_id": app_id}
    )
