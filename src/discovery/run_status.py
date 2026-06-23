"""In-memory progress feed for the background `pipeline.run()` job.

Lets the web UI poll for live feedback (current source, offers as they're
added/skipped) instead of a fire-and-forget "check back later" message.
Single-process, single-user tool — module-level state is enough, no DB table.
"""

_state = {
    "running": False,
    "source": None,
    "events": [],
    "totals": {"added": 0, "skipped": 0, "error": 0},
}


def is_running() -> bool:
    return _state["running"]


def start() -> None:
    _state["running"] = True
    _state["source"] = None
    _state["events"] = []
    _state["totals"] = {"added": 0, "skipped": 0, "error": 0}


def set_source(name: str) -> None:
    if not _state["running"]:
        return
    _state["source"] = name
    _state["events"].append({"kind": "source", "text": f"Searching: {name}"})


def report(kind: str, text: str) -> None:
    if not _state["running"]:
        return
    _state["totals"][kind] += 1
    _state["events"].append({"kind": kind, "text": text})


def finish() -> None:
    _state["running"] = False
    _state["source"] = None


def snapshot() -> dict:
    return {
        "running": _state["running"],
        "source": _state["source"],
        "events": list(reversed(_state["events"])),
        "totals": dict(_state["totals"]),
    }
