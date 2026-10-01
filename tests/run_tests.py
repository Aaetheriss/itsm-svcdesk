# ai-generated: 100% - ChatGPT generated repository-owned tests for the Lab 1 and Lab 2 contracts.
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = os.getenv("SVCDESK_URL", "http://svcdesk:8080").rstrip("/")
CLOCK = "2026-10-14T10:00:00Z"
WINDOW = {"from": "2026-09-01T00:00:00Z", "to": "2026-09-22T00:00:00Z"}
passed = 0
failed = 0


def request(method, path, body=None, clock=CLOCK):
    headers = {"Accept": "application/json"}
    if clock is not None:
        headers["X-Test-Clock"] = clock
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else None
            return response.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, json.loads(raw) if raw else None


def check(condition, name):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {name}")


for _ in range(30):
    try:
        status, body = request("GET", "/health", clock=None)
        if status == 200:
            break
    except Exception:
        pass
    time.sleep(1)
else:
    print("ITSMLAB-TESTS: passed=0 failed=1")
    sys.exit(1)

check(status == 200 and body.get("status") == "ok", "health")

base_reporter = {"name": "Own test", "email": None, "vip": False}
p1_body = {
    "title": "Own test P1",
    "description": "created by the repository test suite",
    "reporter": base_reporter,
    "impact": 1,
    "urgency": 1,
}
p4_body = {
    "title": "Own test P4",
    "reporter": base_reporter,
    "impact": 3,
    "urgency": 3,
}

status, p1 = request("POST", "/tickets", p1_body)
check(status == 201 and p1.get("priority") == "P1", "create P1")
check(p1.get("state") == "new" and bool(p1.get("id")), "created ticket fields")
check(p1.get("created_at") == CLOCK, "test clock")
check(p1.get("sla", {}).get("ack_due_at") == "2026-10-14T10:15:00Z", "P1 acknowledgement due")

status, p4 = request("POST", "/tickets", p4_body)
check(status == 201 and p4.get("priority") == "P4", "create P4")
check(p1.get("id") != p4.get("id"), "distinct identifiers")

status, fetched = request("GET", f"/tickets/{p1['id']}")
check(status == 200 and fetched.get("title") == p1_body["title"], "get by id")

status, listed = request("GET", "/tickets?priority=P1")
ids = {item.get("id") for item in listed} if isinstance(listed, list) else set()
check(status == 200 and p1["id"] in ids and p4["id"] not in ids, "priority filter")

status, acked = request("POST", f"/tickets/{p1['id']}/ack", clock="2026-10-14T10:05:00Z")
check(status == 200 and acked.get("state") == "acknowledged", "acknowledge")

status, _ = request("POST", f"/tickets/{p1['id']}/ack", clock="2026-10-14T10:06:00Z")
check(status == 409, "duplicate acknowledgement rejected")

status, started = request("POST", f"/tickets/{p1['id']}/start", clock="2026-10-14T10:10:00Z")
check(status == 200 and started.get("state") == "in_progress", "start")

status, resolved = request("POST", f"/tickets/{p1['id']}/resolve", clock="2026-10-14T11:00:00Z")
check(status == 200 and resolved.get("state") == "resolved", "resolve")

status, events_before_reopen = request("GET", "/dora/ticket-events", clock=None)
phases = [
    event["phase"]
    for event in events_before_reopen
    if event.get("ticket_id") == p1["id"]
]
check(phases == ["created", "acknowledged", "resolved"], "ticket event lifecycle")
check(
    events_before_reopen == sorted(events_before_reopen, key=lambda event: (event["at"], event["ticket_id"])),
    "ticket events ordered",
)

status, reopened = request("POST", f"/tickets/{p1['id']}/reopen", clock="2026-10-20T11:00:00Z")
check(status == 200 and reopened.get("state") == "in_progress", "reopen resolved within seven days")

status, error = request("POST", "/tickets", {"reporter": base_reporter, "impact": 1, "urgency": 1})
check(status in {400, 422} and isinstance(error, dict) and "error" in error, "validation error shape")

status, _ = request("POST", "/tickets", p1_body, clock="yesterday")
check(status in {400, 422}, "malformed clock rejected")

fixture_dir = Path("/tests/fixtures")
practice_events = [
    json.loads(line)
    for line in (fixture_dir / "events-practice.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]
expected_metrics = json.loads((fixture_dir / "metrics-practice.json").read_text(encoding="utf-8"))
metric_request = {"window": WINDOW, "events": practice_events}

status, metrics = request("POST", "/dora/metrics", metric_request, clock=None)
check(status == 200 and metrics == expected_metrics, "practice metrics")

status, repeated = request("POST", "/dora/metrics", metric_request, clock=None)
check(status == 200 and repeated == metrics, "metrics pure function")

status, reversed_metrics = request(
    "POST", "/dora/metrics", {"window": WINDOW, "events": list(reversed(practice_events))}, clock=None
)
check(status == 200 and reversed_metrics == metrics, "metrics order independent")

status, duplicated_metrics = request(
    "POST", "/dora/metrics", {"window": WINDOW, "events": practice_events + practice_events}, clock=None
)
check(status == 200 and duplicated_metrics == metrics, "duplicate events ignored")

status, empty_metrics = request("POST", "/dora/metrics", {"window": WINDOW, "events": []}, clock=None)
check(
    status == 200
    and empty_metrics.get("deployment_frequency_per_day") == 0.0
    and empty_metrics.get("change_lead_time_seconds_p50") is None
    and empty_metrics.get("change_fail_rate") is None
    and all(value == 0 for value in empty_metrics.get("counts", {}).values()),
    "empty metric log",
)

status, malformed = request(
    "POST",
    "/dora/metrics",
    {
        "window": WINDOW,
        "events": [
            {
                "event_id": "bad-revert",
                "type": "commit",
                "at": "2026-09-01T01:00:00Z",
                "sha": "bad-sha",
                "branch": "main",
                "change_id": None,
                "reverts": "missing-sha",
            }
        ],
    },
    clock=None,
)
check(status in {400, 422} and isinstance(malformed, dict) and "error" in malformed, "malformed log rejected")

status, missing_window = request("POST", "/dora/metrics", {"events": []}, clock=None)
check(status in {400, 422} and "error" in missing_window, "missing window rejected")

status, empty_window = request(
    "POST",
    "/dora/metrics",
    {"window": {"from": WINDOW["from"], "to": WINDOW["from"]}, "events": []},
    clock=None,
)
check(status in {400, 422} and "error" in empty_window, "empty window rejected")

print(f"ITSMLAB-TESTS: passed={passed} failed={failed}")
sys.exit(0 if failed == 0 and passed >= 10 else 1)
