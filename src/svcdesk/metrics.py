# ai-generated: 100% - ChatGPT implemented the published Lab 2 metric rules and validation.
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

UTC = timezone.utc
SPEC_VERSION = "1.0.0"
SIX_PLACES = Decimal("0.000001")
ONE_SECOND = Decimal("1")


class DoraValidationError(ValueError):
    """Raised when the submitted metric request or event log is malformed."""


@dataclass
class IncidentRecord:
    incident_id: str
    opened: datetime | None = None
    resolved: datetime | None = None
    deployments: set[str] = field(default_factory=set)


def parse_rfc3339(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise DoraValidationError(f"{field_name} must be an RFC 3339 instant")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise DoraValidationError(f"{field_name} must be an RFC 3339 instant") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DoraValidationError(f"{field_name} must include an offset")
    return parsed.astimezone(UTC)


def format_rfc3339(value: datetime) -> str:
    value = value.astimezone(UTC)
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.isoformat(timespec=timespec).replace("+00:00", "Z")


def duration_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal(1_000_000)
    return seconds


def rounded_duration(value: Decimal) -> int:
    return int(value.quantize(ONE_SECOND, rounding=ROUND_HALF_UP))


def rounded_rate(value: Decimal) -> float:
    return float(value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP))


def median_duration(values: list[Decimal]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = (ordered[middle - 1] + ordered[middle]) / Decimal(2)
    return rounded_duration(median)


def require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DoraValidationError(f"{field_name} must be an object")
    return value


def require_string(value: Any, field_name: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise DoraValidationError(f"{field_name} must be a non-empty string")
    return value


def require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise DoraValidationError(f"{field_name} must be a boolean")
    return value


def require_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise DoraValidationError(f"{field_name} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise DoraValidationError(f"{field_name}[{index}] must be a non-empty string")
        result.append(item)
    return result


def parse_events(raw_events: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_events, list):
        raise DoraValidationError("events must be an array")

    events: list[dict[str, Any]] = []
    seen_event_ids: set[str] = set()

    for index, raw in enumerate(raw_events):
        if not isinstance(raw, dict):
            raise DoraValidationError(f"events[{index}] must be an object")
        event_id = raw.get("event_id")
        if not isinstance(event_id, str) or not 1 <= len(event_id) <= 64:
            raise DoraValidationError(f"events[{index}].event_id must contain 1 to 64 characters")
        if event_id in seen_event_ids:
            # R-05: the first occurrence wins; a later copy is ignored completely.
            continue
        seen_event_ids.add(event_id)

        event_type = raw.get("type")
        if event_type not in {"commit", "deployment", "incident"}:
            raise DoraValidationError(f"events[{index}].type is invalid")
        at = parse_rfc3339(raw.get("at"), f"events[{index}].at")
        event: dict[str, Any] = {"event_id": event_id, "type": event_type, "at": at}

        if event_type == "commit":
            sha = require_string(raw.get("sha"), f"events[{index}].sha")
            branch = require_string(raw.get("branch"), f"events[{index}].branch")
            change_id = raw.get("change_id")
            reverts = raw.get("reverts")
            if reverts is None:
                change_id = require_string(change_id, f"events[{index}].change_id")
            else:
                reverts = require_string(reverts, f"events[{index}].reverts")
                if change_id is not None:
                    raise DoraValidationError(
                        f"events[{index}].change_id must be null on a revert commit"
                    )
            event.update(
                {
                    "sha": sha,
                    "branch": branch,
                    "change_id": change_id,
                    "reverts": reverts,
                }
            )

        elif event_type == "deployment":
            outcome = raw.get("outcome")
            if outcome not in {"success", "failure"}:
                raise DoraValidationError(f"events[{index}].outcome is invalid")
            caused_by = raw.get("caused_by")
            if caused_by is not None:
                caused_by = require_string(caused_by, f"events[{index}].caused_by")
            event.update(
                {
                    "deployment_id": require_string(
                        raw.get("deployment_id"), f"events[{index}].deployment_id"
                    ),
                    "environment": require_string(
                        raw.get("environment"), f"events[{index}].environment"
                    ),
                    "outcome": outcome,
                    "commits": require_string_list(
                        raw.get("commits"), f"events[{index}].commits"
                    ),
                    "unplanned": require_bool(
                        raw.get("unplanned"), f"events[{index}].unplanned"
                    ),
                    "caused_by": caused_by,
                }
            )

        else:
            phase = raw.get("phase")
            if phase not in {"opened", "resolved"}:
                raise DoraValidationError(f"events[{index}].phase is invalid")
            event.update(
                {
                    "incident_id": require_string(
                        raw.get("incident_id"), f"events[{index}].incident_id"
                    ),
                    "phase": phase,
                    "deployments": require_string_list(
                        raw.get("deployments"), f"events[{index}].deployments"
                    ),
                }
            )

        events.append(event)

    validate_references(events)
    return events


def validate_references(events: list[dict[str, Any]]) -> None:
    commits: dict[str, dict[str, Any]] = {}
    deployments: dict[str, dict[str, Any]] = {}
    incident_phases: dict[str, set[str]] = {}
    incident_ids: set[str] = set()

    for event in events:
        if event["type"] == "commit":
            sha = event["sha"]
            if sha in commits:
                raise DoraValidationError(f"duplicate commit sha: {sha}")
            commits[sha] = event
        elif event["type"] == "deployment":
            deployment_id = event["deployment_id"]
            if deployment_id in deployments:
                raise DoraValidationError(f"duplicate deployment id: {deployment_id}")
            deployments[deployment_id] = event
        else:
            incident_id = event["incident_id"]
            phases = incident_phases.setdefault(incident_id, set())
            if event["phase"] in phases:
                raise DoraValidationError(
                    f"incident {incident_id} has more than one {event['phase']} event"
                )
            phases.add(event["phase"])
            incident_ids.add(incident_id)

    for event in events:
        if event["type"] == "commit" and event["reverts"] is not None:
            if event["reverts"] not in commits:
                raise DoraValidationError(
                    f"reverts references missing commit {event['reverts']}"
                )
        elif event["type"] == "deployment":
            for sha in event["commits"]:
                if sha not in commits:
                    raise DoraValidationError(f"deployment references missing commit {sha}")
            if event["caused_by"] is not None and event["caused_by"] not in incident_ids:
                raise DoraValidationError(
                    f"caused_by references missing incident {event['caused_by']}"
                )
        elif event["type"] == "incident":
            if event["phase"] == "resolved" and "opened" not in incident_phases[event["incident_id"]]:
                raise DoraValidationError(
                    f"incident {event['incident_id']} resolved without being opened"
                )
            for deployment_id in event["deployments"]:
                if deployment_id not in deployments:
                    raise DoraValidationError(
                        f"incident references missing deployment {deployment_id}"
                    )

    # Resolve every revert once so cycles are rejected before any metric is computed.
    resolving: set[str] = set()
    resolved: dict[str, str] = {}

    def resolve_change_id(sha: str) -> str:
        if sha in resolved:
            return resolved[sha]
        if sha in resolving:
            raise DoraValidationError("revert chain contains a cycle")
        resolving.add(sha)
        commit = commits[sha]
        if commit["reverts"] is None:
            change_id = commit["change_id"]
        else:
            change_id = resolve_change_id(commit["reverts"])
        resolving.remove(sha)
        resolved[sha] = change_id
        return change_id

    for sha in commits:
        resolve_change_id(sha)


def compute_metrics(payload: Any) -> dict[str, Any]:
    body = require_mapping(payload, "body")
    if "window" not in body:
        raise DoraValidationError("window is required")
    if "events" not in body:
        raise DoraValidationError("events is required")

    window = require_mapping(body["window"], "window")
    start = parse_rfc3339(window.get("from"), "window.from")
    end = parse_rfc3339(window.get("to"), "window.to")
    if end <= start:
        raise DoraValidationError("window.to must be after window.from")

    events = parse_events(body["events"])
    commits = {event["sha"]: event for event in events if event["type"] == "commit"}
    deployments_all = [event for event in events if event["type"] == "deployment"]

    resolving: set[str] = set()
    resolved_change_ids: dict[str, str] = {}

    def change_for_sha(sha: str) -> str:
        if sha in resolved_change_ids:
            return resolved_change_ids[sha]
        if sha in resolving:
            raise DoraValidationError("revert chain contains a cycle")
        resolving.add(sha)
        commit = commits[sha]
        if commit["reverts"] is None:
            change_id = commit["change_id"]
        else:
            change_id = change_for_sha(commit["reverts"])
        resolving.remove(sha)
        resolved_change_ids[sha] = change_id
        return change_id

    for sha in commits:
        change_for_sha(sha)

    production = [
        deployment
        for deployment in deployments_all
        if deployment["environment"] == "production"
        and start <= deployment["at"] < end
    ]
    successful = [deployment for deployment in production if deployment["outcome"] == "success"]
    failed = [deployment for deployment in production if deployment["outcome"] == "failure"]

    deployment_count = len(production)
    successful_count = len(successful)
    failed_count = len(failed)
    rework_count = sum(
        1
        for deployment in production
        if deployment["unplanned"] is True and deployment["caused_by"] is not None
    )

    window_days = duration_seconds(end, start) / Decimal(86400)
    frequency = rounded_rate(Decimal(deployment_count) / window_days)
    change_fail_rate = (
        None
        if deployment_count == 0
        else rounded_rate(Decimal(failed_count) / Decimal(deployment_count))
    )
    deployment_rework_rate = (
        None
        if deployment_count == 0
        else rounded_rate(Decimal(rework_count) / Decimal(deployment_count))
    )

    # R-08: each commit contributes once, at its earliest successful production deployment.
    first_success_by_sha: dict[str, datetime] = {}
    for deployment in successful:
        for sha in deployment["commits"]:
            previous = first_success_by_sha.get(sha)
            if previous is None or deployment["at"] < previous:
                first_success_by_sha[sha] = deployment["at"]

    lead_times: list[Decimal] = []
    negative_lead_time_pairs = 0
    for sha, deployment_at in first_success_by_sha.items():
        lead = duration_seconds(deployment_at, commits[sha]["at"])
        if lead < 0:
            negative_lead_time_pairs += 1
            lead = Decimal(0)
        lead_times.append(lead)

    commits_never_on_main = {
        sha
        for deployment in production
        for sha in deployment["commits"]
        if commits[sha]["branch"] != "main"
    }
    deployments_without_commits = sum(1 for deployment in production if not deployment["commits"])

    incidents: dict[str, IncidentRecord] = {}
    for event in events:
        if event["type"] != "incident":
            continue
        record = incidents.setdefault(event["incident_id"], IncidentRecord(event["incident_id"]))
        record.deployments.update(event["deployments"])
        if event["phase"] == "opened":
            record.opened = event["at"]
        else:
            record.resolved = event["at"]

    recovery_times: list[Decimal] = []
    open_failures = 0
    for deployment in failed:
        candidates = [
            incident
            for incident in incidents.values()
            if deployment["deployment_id"] in incident.deployments and incident.opened is not None
        ]
        if not candidates:
            open_failures += 1
            continue
        covering = min(candidates, key=lambda incident: (incident.opened, incident.incident_id))
        if covering.resolved is None:
            open_failures += 1
            continue
        recovery = duration_seconds(covering.resolved, deployment["at"])
        if recovery < 0:
            recovery = Decimal(0)
        recovery_times.append(recovery)

    incident_intervals: list[tuple[str, datetime, datetime]] = []
    for incident in incidents.values():
        if incident.opened is None:
            continue
        incident_intervals.append(
            (incident.incident_id, incident.opened, incident.resolved or end)
        )
    overlapping_incident_pairs = 0
    for index, (_, first_opened, first_end) in enumerate(incident_intervals):
        for _, second_opened, second_end in incident_intervals[index + 1 :]:
            if first_opened < second_end and second_opened < first_end:
                overlapping_incident_pairs += 1

    # R-07, R-16 and R-17: change-level first commit and first successful delivery.
    first_commit_by_change: dict[str, datetime] = {}
    for sha, commit in commits.items():
        change_id = change_for_sha(sha)
        previous = first_commit_by_change.get(change_id)
        if previous is None or commit["at"] < previous:
            first_commit_by_change[change_id] = commit["at"]

    first_delivery_by_change: dict[str, datetime] = {}
    for deployment in successful:
        for sha in deployment["commits"]:
            change_id = change_for_sha(sha)
            previous = first_delivery_by_change.get(change_id)
            if previous is None or deployment["at"] < previous:
                first_delivery_by_change[change_id] = deployment["at"]

    true_lead_times: list[Decimal] = []
    for change_id, delivery_at in first_delivery_by_change.items():
        lead = duration_seconds(delivery_at, first_commit_by_change[change_id])
        if lead < 0:
            lead = Decimal(0)
        true_lead_times.append(lead)

    distinct_changes = set(resolved_change_ids.values())
    revert_commits = sum(1 for commit in commits.values() if commit["reverts"] is not None)

    return {
        "spec_version": SPEC_VERSION,
        "window": {"from": format_rfc3339(start), "to": format_rfc3339(end)},
        "deployment_frequency_per_day": frequency,
        "change_lead_time_seconds_p50": median_duration(lead_times),
        "failed_deployment_recovery_time_seconds_p50": median_duration(recovery_times),
        "change_fail_rate": change_fail_rate,
        "deployment_rework_rate": deployment_rework_rate,
        "counts": {
            "deployments": deployment_count,
            "successful_deployments": successful_count,
            "failed_deployments": failed_count,
            "recovered_failures": len(recovery_times),
            "open_failures": open_failures,
            "rework_deployments": rework_count,
            "lead_time_pairs": len(lead_times),
            "changes": len(distinct_changes),
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_lead_time_pairs,
            "deployments_without_commits": deployments_without_commits,
            "commits_never_on_main": len(commits_never_on_main),
            "revert_chains_collapsed": revert_commits,
            "overlapping_incident_pairs": overlapping_incident_pairs,
        },
        "ground_truth": {
            "changes_delivered": len(first_delivery_by_change),
            "true_change_lead_time_seconds_p50": median_duration(true_lead_times),
        },
    }
