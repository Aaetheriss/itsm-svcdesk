<!-- ai-generated: 100% - ChatGPT generated this specification from the course requirements and published checks. -->
# svcdesk specification

## Scope

The service exposes a JSON HTTP API on port 8080 for creating, reading, listing and progressing service-desk tickets. It computes priority and SLA due instants, supports a per-request test clock, and persists tickets in a named Docker volume.

## Decisions to implement

- C1: `wallclock` - P1 acknowledgement and resolution targets use elapsed wall-clock time; P2-P4 use business hours.
- C2: `immutable` - resolved tickets may be reopened within seven days; closed tickets cannot be reopened.
- C3: `matrix` - priority is determined only by impact and urgency; the VIP flag is stored but does not raise priority.

## Functional requirements

### Health and errors

- `GET /health` returns status 200 and `{"status":"ok","service":"svcdesk"}`.
- Unknown paths return a JSON 404 response.
- Unknown ticket identifiers return 404 with a top-level `error` object.
- Invalid transitions return 409 with a top-level `error` object.
- Validation failures return 400 or 422 with a top-level `error` object.

### Ticket creation and validation

`POST /tickets` accepts:

- `title`: required string, 1-200 characters;
- `description`: optional string, at most 4000 characters, default empty string;
- `reporter.name`: required string, 1-100 characters;
- `reporter.email`: optional string or null;
- `reporter.vip`: optional boolean, default false;
- `impact`: required strict integer from 1 through 3;
- `urgency`: required strict integer from 1 through 3;
- `related_to`: optional string or null.

Unknown request fields and server-owned fields are ignored. A successful request returns 201 with a full ticket. The service generates a unique opaque identifier, sets state to `new`, records `created_at`, computes priority, and computes both SLA due instants.

### Priority

The impact/urgency matrix is:

| impact / urgency | 1 | 2 | 3 |
|---|---|---|---|
| 1 | P1 | P2 | P3 |
| 2 | P2 | P3 | P4 |
| 3 | P3 | P4 | P4 |

Under C3=`matrix`, `reporter.vip` does not alter this result. A client-supplied `priority` is ignored.

### Reading and listing

- `GET /tickets/{id}` returns the full ticket.
- `GET /tickets` returns every ticket in one JSON array.
- Optional `state` and `priority` query parameters are exact-match filters and may be combined.

### State machine

Valid actions are:

- `POST /tickets/{id}/ack`: `new` to `acknowledged`, setting `acknowledged_at`;
- `POST /tickets/{id}/start`: `acknowledged` to `in_progress`;
- `POST /tickets/{id}/resolve`: `in_progress` to `resolved`, setting `resolved_at`;
- `POST /tickets/{id}/close`: `resolved` to `closed`, setting `closed_at`;
- `POST /tickets/{id}/reopen`: `resolved` to `in_progress` while `now <= resolved_at + 7 days`, clearing `resolved_at` and `closed_at`.

Every other transition is rejected with 409. Under C2=`immutable`, a closed ticket is always rejected by `/reopen`. Reopening never changes the original SLA due instants.

### SLA targets

| priority | acknowledge | resolve |
|---|---:|---:|
| P1 | 15 minutes | 4 hours |
| P2 | 1 hour | 8 hours |
| P3 | 4 hours | 24 hours |
| P4 | 8 hours | 72 hours |

For C1=`wallclock`, both P1 targets equal `created_at + target`. P2-P4 count only business time in Europe/Warsaw, Monday-Friday, 08:00 inclusive to 16:00 exclusive. Time before opening moves to that day's opening; time at or after closing and weekends move to the next weekday opening. A target ending exactly at 16:00 is due at 16:00 that day. Due instants are returned in UTC.

The implementation must reproduce every T1-T8 vector in API.md exactly.

### SLA status

`GET /tickets/{id}/sla` returns:

- `priority`;
- `ack_due_at`;
- `resolve_due_at`;
- `ack_breached`;
- `resolve_breached`;
- `paused`.

A target is breached only when its event occurs after the due instant, or the event has not occurred and `now` is later than the due instant. Equality is not a breach. A reopened ticket is unresolved again. `paused` is true only for an open ticket whose resolution target uses business hours and whose current time is outside the business window. P1 is never paused under C1=`wallclock`.

### Test clock

When `SVCDESK_TEST_CLOCK` is `1` or `true`, an RFC 3339 `X-Test-Clock` header sets `now` for that request only. A malformed or offset-free value is rejected with 400 or 422. Without the header, real UTC time is used. Request clocks are independent and need not be monotonic.

## Deployment and persistence

- Docker Compose defines a service named `svcdesk` with `build:` and internal port 8080.
- `SVCDESK_TEST_CLOCK` is enabled in Compose.
- No service uses a host-path bind mount.
- Dependencies are installed during image build, and the running image needs no network access.
- A named volume stores a SQLite database under `/data` so tickets survive a container restart.
- `docker compose up --wait svcdesk` and `GET /health` must succeed within 120 seconds.

## Acceptance

The implementation is accepted when `itsmlab verify 1` reports all Core specifications as pass, with L1-CORE-5 shown locally as skip, and observations equal to C1=`wallclock`, C2=`immutable`, C3=`matrix`.
