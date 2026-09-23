# ai-generated: 100% - ChatGPT generated this implementation from the course requirements and published checks.
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from starlette.exceptions import HTTPException as StarletteHTTPException

UTC = timezone.utc
WARSAW = ZoneInfo("Europe/Warsaw")
BUSINESS_OPEN = time(8, 0, 0)
BUSINESS_CLOSE = time(16, 0, 0)

C1 = "wallclock"
C2 = "immutable"
C3 = "matrix"

PRIORITY_MATRIX: dict[tuple[int, int], str] = {
    (1, 1): "P1",
    (1, 2): "P2",
    (1, 3): "P3",
    (2, 1): "P2",
    (2, 2): "P3",
    (2, 3): "P4",
    (3, 1): "P3",
    (3, 2): "P4",
    (3, 3): "P4",
}

SLA_TARGETS: dict[str, tuple[timedelta, timedelta]] = {
    "P1": (timedelta(minutes=15), timedelta(hours=4)),
    "P2": (timedelta(hours=1), timedelta(hours=8)),
    "P3": (timedelta(hours=4), timedelta(hours=24)),
    "P4": (timedelta(hours=8), timedelta(hours=72)),
}


class ServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class ReporterInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=100)
    email: str | None = None
    vip: bool = False


StrictLevel = Annotated[StrictInt, Field(ge=1, le=3)]


class TicketInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    reporter: ReporterInput
    impact: StrictLevel
    urgency: StrictLevel
    related_to: str | None = None


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first.get("loc", [])[1:])
    message = first.get("msg", "invalid request")
    if location:
        message = f"{location}: {message}"
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation", "message": message}},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == 404 else "http_error"
    detail = exc.detail if isinstance(exc.detail, str) else "request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": detail}},
    )


def database_path() -> Path:
    return Path(os.getenv("SVCDESK_DB", "/data/svcdesk.db"))


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS tickets (id TEXT PRIMARY KEY, data TEXT NOT NULL)"
    )
    connection.commit()
    return connection


def save_ticket(ticket: dict[str, Any]) -> None:
    payload = json.dumps(ticket, separators=(",", ":"), ensure_ascii=False)
    with connect() as connection:
        connection.execute(
            "INSERT INTO tickets(id, data) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET data = excluded.data",
            (ticket["id"], payload),
        )
        connection.commit()


def load_ticket(ticket_id: str) -> dict[str, Any]:
    with connect() as connection:
        row = connection.execute(
            "SELECT data FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
    if row is None:
        raise ServiceError(404, "not_found", "ticket not found")
    return json.loads(row["data"])


def load_tickets() -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute("SELECT data FROM tickets").fetchall()
    return [json.loads(row["data"]) for row in rows]


def parse_instant(value: str) -> datetime:
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError("timestamp is not valid RFC 3339") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include an offset")
    return parsed.astimezone(UTC)


def format_instant(value: datetime) -> str:
    value = value.astimezone(UTC)
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.isoformat(timespec=timespec).replace("+00:00", "Z")


def request_now(
    test_clock: str | None = Header(default=None, alias="X-Test-Clock"),
) -> datetime:
    enabled = os.getenv("SVCDESK_TEST_CLOCK", "0").strip().lower() in {"1", "true"}
    if enabled and test_clock is not None:
        try:
            return parse_instant(test_clock)
        except ValueError as exc:
            raise ServiceError(422, "invalid_clock", str(exc)) from exc
    return datetime.now(UTC)


def next_weekday(day: date) -> date:
    candidate = day
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def business_open(day: date) -> datetime:
    return datetime.combine(day, BUSINESS_OPEN, tzinfo=WARSAW)


def business_close(day: date) -> datetime:
    return datetime.combine(day, BUSINESS_CLOSE, tzinfo=WARSAW)


def normalize_business_start(local: datetime) -> datetime:
    day = local.date()
    if day.weekday() >= 5:
        day = next_weekday(day)
        return business_open(day)

    opening = business_open(day)
    closing = business_close(day)
    if local < opening:
        return opening
    if local >= closing:
        return business_open(next_weekday(day + timedelta(days=1)))
    return local


def add_business_time(created_at: datetime, target: timedelta) -> datetime:
    current = normalize_business_start(created_at.astimezone(WARSAW))
    remaining = target

    while True:
        closing = business_close(current.date())
        available = closing - current
        if remaining <= available:
            return (current + remaining).astimezone(UTC)
        remaining -= available
        current = business_open(next_weekday(current.date() + timedelta(days=1)))


def uses_business_clock(priority: str) -> bool:
    return priority != "P1" or C1 == "business"


def calculate_due_instants(priority: str, created_at: datetime) -> tuple[datetime, datetime]:
    ack_target, resolve_target = SLA_TARGETS[priority]
    if uses_business_clock(priority):
        return (
            add_business_time(created_at, ack_target),
            add_business_time(created_at, resolve_target),
        )
    return created_at + ack_target, created_at + resolve_target


def is_business_window(now: datetime) -> bool:
    local = now.astimezone(WARSAW)
    return (
        local.weekday() < 5
        and BUSINESS_OPEN <= local.time().replace(tzinfo=None) < BUSINESS_CLOSE
    )


def compute_priority(impact: int, urgency: int, vip: bool) -> str:
    priority = PRIORITY_MATRIX[(impact, urgency)]
    if C3 == "vip" and vip and priority in {"P3", "P4"}:
        return "P2"
    return priority


def ticket_sla_status(ticket: dict[str, Any], now: datetime) -> dict[str, Any]:
    ack_due = parse_instant(ticket["sla"]["ack_due_at"])
    resolve_due = parse_instant(ticket["sla"]["resolve_due_at"])

    acknowledged_at = (
        parse_instant(ticket["acknowledged_at"])
        if ticket.get("acknowledged_at")
        else None
    )
    resolved_at = (
        parse_instant(ticket["resolved_at"]) if ticket.get("resolved_at") else None
    )

    ack_breached = (
        acknowledged_at > ack_due if acknowledged_at is not None else now > ack_due
    )
    resolve_breached = (
        resolved_at > resolve_due if resolved_at is not None else now > resolve_due
    )
    paused = (
        ticket["state"] not in {"resolved", "closed"}
        and uses_business_clock(ticket["priority"])
        and not is_business_window(now)
    )

    return {
        "priority": ticket["priority"],
        "ack_due_at": ticket["sla"]["ack_due_at"],
        "resolve_due_at": ticket["sla"]["resolve_due_at"],
        "ack_breached": ack_breached,
        "resolve_breached": resolve_breached,
        "paused": paused,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets", status_code=201)
def create_ticket(
    payload: TicketInput,
    now: datetime = Depends(request_now),
) -> dict[str, Any]:
    priority = compute_priority(payload.impact, payload.urgency, payload.reporter.vip)
    ack_due, resolve_due = calculate_due_instants(priority, now)
    ticket: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "title": payload.title,
        "description": payload.description,
        "reporter": payload.reporter.model_dump(),
        "impact": payload.impact,
        "urgency": payload.urgency,
        "priority": priority,
        "state": "new",
        "created_at": format_instant(now),
        "acknowledged_at": None,
        "resolved_at": None,
        "closed_at": None,
        "related_to": payload.related_to,
        "sla": {
            "ack_due_at": format_instant(ack_due),
            "resolve_due_at": format_instant(resolve_due),
        },
    }
    save_ticket(ticket)
    return ticket


@app.get("/tickets")
def list_tickets(
    state: str | None = Query(default=None),
    priority: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    tickets = load_tickets()
    if state is not None:
        tickets = [ticket for ticket in tickets if ticket["state"] == state]
    if priority is not None:
        tickets = [ticket for ticket in tickets if ticket["priority"] == priority]
    return tickets


@app.get("/tickets/{ticket_id}/sla")
def get_ticket_sla(
    ticket_id: str,
    now: datetime = Depends(request_now),
) -> dict[str, Any]:
    return ticket_sla_status(load_ticket(ticket_id), now)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> dict[str, Any]:
    return load_ticket(ticket_id)


def require_state(ticket: dict[str, Any], expected: str, action: str) -> None:
    if ticket["state"] != expected:
        raise ServiceError(
            409,
            "invalid_transition",
            f"cannot {action} a ticket in state {ticket['state']}",
        )


@app.post("/tickets/{ticket_id}/ack")
def acknowledge_ticket(
    ticket_id: str,
    now: datetime = Depends(request_now),
) -> dict[str, Any]:
    ticket = load_ticket(ticket_id)
    require_state(ticket, "new", "acknowledge")
    ticket["state"] = "acknowledged"
    ticket["acknowledged_at"] = format_instant(now)
    save_ticket(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/start")
def start_ticket(ticket_id: str) -> dict[str, Any]:
    ticket = load_ticket(ticket_id)
    require_state(ticket, "acknowledged", "start")
    ticket["state"] = "in_progress"
    save_ticket(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(
    ticket_id: str,
    now: datetime = Depends(request_now),
) -> dict[str, Any]:
    ticket = load_ticket(ticket_id)
    require_state(ticket, "in_progress", "resolve")
    ticket["state"] = "resolved"
    ticket["resolved_at"] = format_instant(now)
    ticket["closed_at"] = None
    save_ticket(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/close")
def close_ticket(
    ticket_id: str,
    now: datetime = Depends(request_now),
) -> dict[str, Any]:
    ticket = load_ticket(ticket_id)
    require_state(ticket, "resolved", "close")
    ticket["state"] = "closed"
    ticket["closed_at"] = format_instant(now)
    save_ticket(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/reopen")
def reopen_ticket(
    ticket_id: str,
    now: datetime = Depends(request_now),
) -> dict[str, Any]:
    ticket = load_ticket(ticket_id)

    if ticket["state"] == "closed":
        if C2 == "immutable":
            raise ServiceError(409, "ticket_closed", "closed tickets are immutable")
        reference = ticket.get("closed_at")
    elif ticket["state"] == "resolved":
        reference = ticket.get("resolved_at")
    else:
        raise ServiceError(
            409,
            "invalid_transition",
            f"cannot reopen a ticket in state {ticket['state']}",
        )

    if not reference:
        raise ServiceError(409, "invalid_transition", "ticket has no reopen reference")
    if now > parse_instant(reference) + timedelta(days=7):
        raise ServiceError(409, "reopen_window_expired", "reopen window has expired")

    ticket["state"] = "in_progress"
    ticket["resolved_at"] = None
    ticket["closed_at"] = None
    save_ticket(ticket)
    return ticket
