import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.discovery import pipeline, store
from src.discovery.config import STATIC_DIR, TEMPLATES_DIR
from src.discovery.models import OfferStatus

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.init_schema()
    yield


app = FastAPI(title="Job Discovery", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_ACTIVE_STATUSES = [s.value for s in OfferStatus]


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
