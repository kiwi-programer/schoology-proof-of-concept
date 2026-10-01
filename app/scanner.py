import os
import re
import threading
import time
from collections import deque

from . import schoology
from .endpoints import ENDPOINTS

SKIP = {"/v1/courses", "/v1/sections", "/v1/districts"}
MAX_IDS_PER_ENDPOINT = 5

state = {
    "running": False,
    "total": 0,
    "completed": 0,
    "current": "",
    "counts": {},
    "results": [],
}
_lock = threading.Lock()


def _ids(body, found):
    """Collect IDs from real API responses only."""
    if not isinstance(body, dict):
        return

    if "name_display" in body and "id" in body:
        found["users"].add(str(body["id"]))
    if body.get("school_id"):
        found["schools"].add(str(body["school_id"]))

    for resource in ("user", "section", "course", "group"):
        items = body.get(resource)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and "id" in item:
                found[f"{resource}s"].add(str(item["id"]))


def _resource_kind(path):
    return re.search(r"/v1/(\w+)/\{id\}", path).group(1)


def _queue_id_endpoints(queue, pending, found):
    remaining = []
    for endpoint in pending:
        kind = _resource_kind(endpoint["path"])
        ids = sorted(found.get(kind, set()))[:MAX_IDS_PER_ENDPOINT]
        if ids:
            queue.extend(endpoint["path"].replace("{id}", item) for item in ids)
        else:
            remaining.append(endpoint)
    return remaining


def _run():
    max_requests = int(os.getenv("MAX_REQUESTS_PER_SCAN", 100))
    request_delay = int(os.getenv("REQUEST_DELAY_MS", 250)) / 1000
    found = {key: set() for key in ("users", "schools", "sections", "courses", "groups")}
    queue = deque(
        endpoint["path"]
        for endpoint in ENDPOINTS
        if not endpoint["requires_id"] and endpoint["path"] not in SKIP
    )
    pending = [endpoint for endpoint in ENDPOINTS if endpoint["requires_id"]]
    completed = 0

    while completed < max_requests:
        if not queue:  # queue endpoints whose IDs have now been discovered
            remaining = _queue_id_endpoints(queue, pending, found)
            if len(remaining) == len(pending):
                break
            pending = remaining
            if not queue:
                break

        path = queue.popleft()
        with _lock:
            state["current"] = path

        response = schoology.get(path)
        _ids(response["body"], found)
        completed += 1

        with _lock:
            classification = response["classification"]
            state["completed"] = completed
            state["counts"][classification] = state["counts"].get(classification, 0) + 1
            state["results"].append(
                {
                    "path": path,
                    "status": response["status"],
                    "class": classification,
                }
            )
            state["total"] = min(max_requests, completed + len(queue))

        time.sleep(request_delay)

    with _lock:
        state.update(running=False, current="")


def start():
    with _lock:
        if state["running"]:
            return False
        state.update(
            running=True,
            total=len(ENDPOINTS),
            completed=0,
            current="",
            counts={},
            results=[],
        )

    threading.Thread(target=_run, daemon=True).start()
    return True
