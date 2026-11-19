# ai-generated: 100% - ChatGPT wrote behavioural boundary tests from every public slaclock.py docstring for Lab 5 mutation testing.
from datetime import datetime, timedelta

import pytest

import slaclock


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"),
        (2, 1, "P2"),
        (1, 3, "P3"),
        (2, 2, "P3"),
        (3, 1, "P3"),
        (2, 3, "P4"),
        (3, 2, "P4"),
        (3, 3, "P4"),
    ],
)
def test_priority_matrix(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency) == expected


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [(1, 1, "P1"), (1, 2, "P2"), (2, 2, "P2"), (3, 3, "P2")],
)
def test_vip_never_below_p2(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency, vip=True) == expected


@pytest.mark.parametrize(
    ("impact", "urgency"),
    [
        (0, 1),
        (4, 1),
        (1, 0),
        (1, 4),
        (2.0, 1),
        (1, 2.0),
        (True, 1),
        (1, False),
        ("1", 1),
        (1, "1"),
    ],
)
def test_priority_rejects_non_exact_levels(impact, urgency):
    with pytest.raises(ValueError):
        slaclock.priority_of(impact, urgency)


def test_targets_exact_values():
    assert slaclock.targets("P1") == (15, 240)
    assert slaclock.targets("P2") == (60, 480)
    assert slaclock.targets("P3") == (240, 1440)
    assert slaclock.targets("P4") == (480, 4320)


@pytest.mark.parametrize("priority", ["p1", " P1", "P1 ", "P5", "", None, 1])
def test_targets_reject_unknown_values(priority):
    with pytest.raises(ValueError):
        slaclock.targets(priority)


@pytest.mark.parametrize(
    ("elapsed", "target", "expected"),
    [
        (0, 100, "ok"),
        (74, 100, "ok"),
        (75, 100, "warning"),
        (99, 100, "warning"),
        (100, 100, "warning"),
        (101, 100, "breached"),
        (11, 15, "ok"),
        (12, 15, "warning"),
        (15, 15, "warning"),
        (16, 15, "breached"),
        (3, 4, "warning"),
        (2, 4, "ok"),
    ],
)
def test_sla_state_boundaries(elapsed, target, expected):
    assert slaclock.sla_state(elapsed, target) == expected


@pytest.mark.parametrize(("elapsed", "target"), [(-1, 10), (0, 0), (0, -1), (-5, -5)])
def test_sla_state_rejects_invalid_numbers(elapsed, target):
    with pytest.raises(ValueError):
        slaclock.sla_state(elapsed, target)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 11, 16, 7, 59), False),   # Monday before opening
        (datetime(2026, 11, 16, 8, 0), True),
        (datetime(2026, 11, 16, 15, 59), True),
        (datetime(2026, 11, 16, 16, 0), False),
        (datetime(2026, 11, 20, 12, 0), True),    # Friday
        (datetime(2026, 11, 21, 12, 0), False),   # Saturday
        (datetime(2026, 11, 22, 12, 0), False),   # Sunday
    ],
)
def test_is_business_time(moment, expected):
    assert slaclock.is_business_time(moment) is expected


def test_is_business_time_ignores_seconds_for_window_membership():
    assert slaclock.is_business_time(datetime(2026, 11, 16, 15, 59, 59)) is True
    assert slaclock.is_business_time(datetime(2026, 11, 16, 16, 0, 1)) is False


@pytest.mark.parametrize(
    ("start", "minutes", "expected"),
    [
        (datetime(2026, 11, 16, 8, 0), 0, datetime(2026, 11, 16, 8, 0)),
        (datetime(2026, 11, 16, 8, 0, 59, 999999), 1, datetime(2026, 11, 16, 8, 1)),
        (datetime(2026, 11, 16, 7, 0), 0, datetime(2026, 11, 16, 8, 0)),
        (datetime(2026, 11, 16, 7, 0), 30, datetime(2026, 11, 16, 8, 30)),
        (datetime(2026, 11, 16, 16, 0), 0, datetime(2026, 11, 17, 8, 0)),
        (datetime(2026, 11, 16, 17, 0), 30, datetime(2026, 11, 17, 8, 30)),
        (datetime(2026, 11, 20, 17, 0), 30, datetime(2026, 11, 23, 8, 30)),
        (datetime(2026, 11, 21, 12, 0), 0, datetime(2026, 11, 23, 8, 0)),
        (datetime(2026, 11, 16, 15, 0), 60, datetime(2026, 11, 16, 16, 0)),
        (datetime(2026, 11, 16, 15, 0), 61, datetime(2026, 11, 17, 8, 1)),
        (datetime(2026, 11, 16, 8, 0), 480, datetime(2026, 11, 16, 16, 0)),
        (datetime(2026, 11, 16, 8, 0), 481, datetime(2026, 11, 17, 8, 1)),
        (datetime(2026, 11, 20, 15, 59), 2, datetime(2026, 11, 23, 8, 1)),
    ],
)
def test_add_business_minutes_examples(start, minutes, expected):
    assert slaclock.add_business_minutes(start, minutes) == expected


def test_add_business_minutes_rejects_negative():
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(datetime(2026, 11, 16, 8, 0), -1)


def test_add_business_minutes_enforces_maximum_calendar_span():
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(datetime(2026, 1, 1, 8, 0), 480 * 270)


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (datetime(2026, 11, 16, 8, 0), datetime(2026, 11, 16, 8, 0), 0),
        (datetime(2026, 11, 16, 7, 0), datetime(2026, 11, 16, 8, 0), 0),
        (datetime(2026, 11, 16, 7, 0), datetime(2026, 11, 16, 8, 1), 1),
        (datetime(2026, 11, 16, 8, 0), datetime(2026, 11, 16, 16, 0), 480),
        (datetime(2026, 11, 16, 15, 59), datetime(2026, 11, 16, 16, 1), 1),
        (datetime(2026, 11, 16, 16, 0), datetime(2026, 11, 17, 8, 0), 0),
        (datetime(2026, 11, 20, 15, 0), datetime(2026, 11, 23, 9, 0), 120),
        (datetime(2026, 11, 21, 8, 0), datetime(2026, 11, 22, 16, 0), 0),
        (datetime(2026, 11, 16, 8, 0, 59), datetime(2026, 11, 16, 8, 1, 59), 1),
    ],
)
def test_business_minutes_between_examples(start, end, expected):
    assert slaclock.business_minutes_between(start, end) == expected


def test_business_minutes_between_rejects_reverse_order():
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(
            datetime(2026, 11, 16, 8, 1), datetime(2026, 11, 16, 8, 0)
        )


def test_business_minutes_between_enforces_maximum_span():
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(
            datetime(2025, 1, 1, 8, 0), datetime(2026, 1, 3, 8, 0)
        )


@pytest.mark.parametrize(
    ("start", "minutes"),
    [
        (datetime(2026, 11, 16, 7, 31), 0),
        (datetime(2026, 11, 16, 8, 0), 1),
        (datetime(2026, 11, 16, 15, 58), 5),
        (datetime(2026, 11, 20, 15, 0), 600),
        (datetime(2026, 11, 21, 12, 0), 960),
    ],
)
def test_business_add_and_count_are_inverses(start, minutes):
    due = slaclock.add_business_minutes(start, minutes)
    assert slaclock.business_minutes_between(start, due) == minutes


@pytest.mark.parametrize(
    ("priority", "breached", "reopens", "expected"),
    [
        ("P1", False, 0, 1),
        ("P2", False, 0, 1),
        ("P3", False, 0, 0),
        ("P4", False, 0, 0),
        ("P1", True, 0, 3),
        ("P2", True, 0, 2),
        ("P3", True, 0, 1),
        ("P4", True, 0, 1),
        ("P3", False, 1, 0),
        ("P3", False, 2, 1),
        ("P2", False, 2, 2),
        ("P1", False, 2, 2),
        ("P2", True, 2, 3),
        ("P1", True, 5, 3),
    ],
)
def test_escalation_tier(priority, breached, reopens, expected):
    assert slaclock.escalation_tier(priority, breached, reopens) == expected


@pytest.mark.parametrize(("priority", "reopens"), [("P5", 0), ("p1", 0), ("P1", -1)])
def test_escalation_rejects_invalid_input(priority, reopens):
    with pytest.raises(ValueError):
        slaclock.escalation_tier(priority, False, reopens)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1m", 1),
        ("59m", 59),
        ("60m", 60),
        ("90m", 90),
        ("4h", 240),
        ("1h30m", 90),
        ("1h59m", 119),
        ("2d", 2880),
        ("1d4h", 1680),
        ("1d0h5m", 1445),
        ("0h60m", 60),
        (" 1h30m ", 90),
        ("999d23h59m", 1_440_000 - 1),
    ],
)
def test_parse_duration_valid(text, expected):
    assert slaclock.parse_duration(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "0m",
        "0h",
        "0d",
        "1.5h",
        "30m1h",
        "-5m",
        "1 h",
        "1H",
        "1h60m",
        "2d60m",
        "1d2h60m",
        "m",
        "1s",
        "1d1d",
        "1h1h",
        "1m1m",
        "01:30",
    ],
)
def test_parse_duration_rejects_invalid(text):
    with pytest.raises(ValueError):
        slaclock.parse_duration(text)
