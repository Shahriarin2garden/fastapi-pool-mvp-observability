import json
import logging
import queue
import threading
import time
from collections import defaultdict
from ipaddress import ip_address
from typing import Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])

frontend_events_total = Counter(
    "frontend_events_total", "Frontend events", ["event", "route"]
)
frontend_js_errors_total = Counter(
    "frontend_js_errors_total", "Frontend JavaScript errors", ["route", "kind"]
)
frontend_web_vital_seconds = Histogram(
    "frontend_web_vital_seconds",
    "Frontend web vitals in seconds",
    ["name"],
    buckets=[0.025, 0.05, 0.1, 0.2, 0.4, 0.5, 0.8, 1, 1.5, 1.8, 2.5, 3, 4, 5, 6, 10],
)
frontend_api_latency_seconds = Histogram(
    "frontend_api_latency_seconds",
    "Client-observed API latency in seconds",
    ["endpoint", "status_class"],
    buckets=[0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)
frontend_telemetry_rejected_total = Counter(
    "frontend_telemetry_rejected_total",
    "Rejected frontend telemetry batches",
    ["reason"],
)
frontend_log_push_failures_total = Counter(
    "frontend_log_push_failures_total", "Failed frontend Loki pushes"
)

ALLOWED_EVENTS = {
    "page_view",
    "order_submit",
    "order_success",
    "order_failure",
    "drill_start",
    "drill_end",
    "link_out",
}
ALLOWED_ENDPOINTS = {"health", "orders"}
ALLOWED_VITALS = {"LCP", "INP", "FCP", "TTFB"}
ALLOWED_ERROR_KINDS = {"error", "unhandledrejection"}
MAX_BODY_BYTES = 8192
MAX_EVENTS = 50
RATE_LIMIT = 60
RATE_WINDOW_SECONDS = 60


class TelemetryEvent(BaseModel):
    type: str
    name: Optional[str] = None
    value: Optional[float] = Field(default=None, ge=0)
    endpoint: Optional[str] = None
    status: Optional[int] = Field(default=None, ge=100, le=599)
    status_class: Optional[str] = None
    duration: Optional[float] = Field(default=None, ge=0)
    trace: Optional[str] = None
    kind: Optional[str] = None


class TelemetryBatch(BaseModel):
    session: str = Field(..., min_length=1, max_length=80)
    route: str
    events: List[TelemetryEvent]

    @validator("route")
    def validate_route(cls, value):
        if value != "console":
            raise ValueError("unsupported route")
        return value

    @validator("events")
    def validate_events(cls, value):
        if not value or len(value) > MAX_EVENTS:
            raise ValueError("events must contain 1 to 50 items")
        return value


_rate_lock = threading.Lock()
_rate_window: Dict[str, List[float]] = defaultdict(list)
_log_queue: "queue.Queue[dict]" = queue.Queue(maxsize=200)
_worker_started = False


def _client_ip(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    try:
        return str(ip_address(host))
    except ValueError:
        return "unknown"


def _allowed_request(client: str) -> bool:
    now = time.monotonic()
    with _rate_lock:
        recent = [item for item in _rate_window[client] if now - item < RATE_WINDOW_SECONDS]
        if len(recent) >= RATE_LIMIT:
            _rate_window[client] = recent
            return False
        recent.append(now)
        _rate_window[client] = recent
    return True


def _push_logs():
    while True:
        event = _log_queue.get()
        try:
            response = requests.post(
                "http://loki:3100/loki/api/v1/push",
                json={
                    "streams": [
                        {
                            "stream": {
                                "app": "order-ui",
                                "job": "frontend",
                                "level": event["level"],
                            },
                            "values": [[str(event["timestamp"]), event["line"]]],
                        }
                    ]
                },
                timeout=1,
            )
            response.raise_for_status()
        except requests.RequestException:
            frontend_log_push_failures_total.inc()
        finally:
            _log_queue.task_done()


def _ensure_worker():
    global _worker_started
    if _worker_started:
        return
    thread = threading.Thread(target=_push_logs, name="frontend-loki", daemon=True)
    thread.start()
    _worker_started = True


def _validate_event(event: TelemetryEvent):
    if event.type == "event":
        if event.name not in ALLOWED_EVENTS:
            raise ValueError("unsupported event name")
    elif event.type == "vital":
        if event.name not in ALLOWED_VITALS or event.value is None:
            raise ValueError("invalid web vital")
    elif event.type == "api":
        if event.endpoint not in ALLOWED_ENDPOINTS or event.status is None or event.duration is None:
            raise ValueError("invalid API telemetry")
        status_class = event.status_class or f"{event.status // 100}xx"
        if status_class not in {"2xx", "4xx", "5xx"}:
            raise ValueError("invalid status class")
    elif event.type == "error":
        if event.kind not in ALLOWED_ERROR_KINDS:
            raise ValueError("unsupported error kind")
    else:
        raise ValueError("unsupported telemetry type")


def _record(event: TelemetryEvent, batch: TelemetryBatch):
    _validate_event(event)
    if event.type == "event":
        frontend_events_total.labels(event.name, batch.route).inc()
    elif event.type == "vital":
        frontend_web_vital_seconds.labels(event.name).observe(event.value)
    elif event.type == "api":
        status_class = event.status_class or f"{event.status // 100}xx"
        frontend_api_latency_seconds.labels(event.endpoint, status_class).observe(event.duration)
    elif event.type == "error":
        frontend_js_errors_total.labels(batch.route, event.kind).inc()

    if event.type != "vital":
        event_name = event.name or event.type
        line = json.dumps(
            {
                "session": batch.session,
                "route": batch.route,
                "event": event_name,
                "endpoint": event.endpoint,
                "status": event.status,
                "duration_ms": round((event.duration or 0) * 1000, 2),
                "trace_id": event.trace,
            },
            separators=(",", ":"),
        )
        try:
            _log_queue.put_nowait(
                {"timestamp": time.time_ns(), "level": "error" if event.type == "error" else "info", "line": line}
            )
        except queue.Full:
            frontend_log_push_failures_total.inc()


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def receive_telemetry(batch: TelemetryBatch, request: Request):
    if request.headers.get("content-length") and int(request.headers["content-length"]) > MAX_BODY_BYTES:
        frontend_telemetry_rejected_total.labels("body_too_large").inc()
        raise HTTPException(status_code=422, detail="telemetry body is too large")
    if not _allowed_request(_client_ip(request)):
        frontend_telemetry_rejected_total.labels("rate_limit").inc()
        raise HTTPException(status_code=429, detail="telemetry rate limit exceeded")
    _ensure_worker()
    try:
        for event in batch.events:
            _validate_event(event)
        for event in batch.events:
            _record(event, batch)
    except ValueError as exc:
        frontend_telemetry_rejected_total.labels("validation").inc()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
