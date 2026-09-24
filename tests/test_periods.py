from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from allen import Period


@pytest.mark.parametrize(
    "args",
    [
        {
            "start": "2025-01-01T00:00:00.000Z",
            "end": datetime(2026, 1, 1, tzinfo=UTC),
        },
        {
            "start": datetime(2026, 1, 1, tzinfo=UTC),
            "end": "2025-01-01T00:00:00.000Z",
        },
    ],
    ids=[
        "validate start",
        "validate end",
    ],
)
def test_periods_only_datetime_allowed(args: dict[str, str | datetime]):
    with pytest.raises(TypeError):
        (lambda: Period(**args))()


@pytest.mark.parametrize(
    "args",
    [
        {
            "start": datetime(2026, 1, 1),
            "end": datetime(2026, 1, 2, tzinfo=UTC),  # tz aware
        },
        {
            "start": datetime(2026, 1, 1, tzinfo=UTC),  # tz aware
            "end": datetime(2026, 1, 2),
        },
    ],
    ids=[
        "validate start",
        "validate end",
    ],
)
def test_periods_only_allow_tz_aware_datetimes(args: dict[str, datetime]):
    with pytest.raises(ValueError):
        (lambda: Period(**args))()


def test_periods_must_be_in_same_tz():
    with pytest.raises(ValueError):
        (
            lambda: Period(
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(
                    2026,
                    1,
                    1,
                    tzinfo=ZoneInfo("America/New_York"),
                ),
            )
        )()


def test_periods_end_must_be_gt_start():
    with pytest.raises(ValueError):
        (
            lambda: Period(
                start=datetime(2026, 2, 1, tzinfo=UTC),
                end=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )()


def test_periods_duration_ok():
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = start + timedelta(days=1)
    period = Period(start=start, end=end)

    assert period.duration == timedelta(days=1)


def test_periods_after_ok():
    xmas = Period(
        datetime(2026, 12, 24, tzinfo=UTC),
        datetime(2026, 12, 24, 23, 59, 59, tzinfo=UTC),
    )
    nye = Period(
        datetime(2026, 12, 31, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC),
    )

    assert nye.is_after(xmas)


def test_periods_before_ok():
    xmas = Period(
        datetime(2026, 12, 24, tzinfo=UTC),
        datetime(2026, 12, 24, 23, 59, 59, tzinfo=UTC),
    )
    nye = Period(
        datetime(2026, 12, 31, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC),
    )

    assert xmas.is_before(nye)


def test_periods_contains_datetime_ok():
    period = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    # same tz
    assert period.contains(datetime(2026, 6, 1, tzinfo=UTC))
    assert not period.contains(datetime(2027, 1, 1, tzinfo=UTC))

    # different tz (UTC-5)
    assert period.contains(
        datetime(2026, 12, 31, 18, 59, 58, tzinfo=ZoneInfo("America/New_York")),
    )
    assert not period.contains(
        datetime(2026, 12, 31, 19, 0, 0, tzinfo=ZoneInfo("America/New_York")),
    )


def test_periods_contains_other_period_ok():
    period = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    # same tz
    assert period.contains(
        Period(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 12, 31, 23, 59, 59, 998, tzinfo=UTC),
        )
    )
    assert not period.contains(
        Period(
            datetime(2025, 12, 31, tzinfo=UTC),
            datetime(2026, 12, 31, 23, 59, 59, 998, tzinfo=UTC),
        )
    )
    assert not period.contains(
        Period(
            datetime(2025, 1, 1, tzinfo=UTC),
            datetime(2026, 12, 31, 23, 59, 59, 998, tzinfo=UTC),
        )
    )

    # different tz
    assert period.contains(
        Period(
            datetime(2025, 12, 31, 19, tzinfo=ZoneInfo("America/New_York")),
            datetime(2026, 12, 31, 18, 59, 59, 998, tzinfo=ZoneInfo("America/New_York")),
        )
    )
    assert not period.contains(
        Period(
            datetime(2025, 12, 31, tzinfo=ZoneInfo("America/New_York")),
            datetime(2026, 12, 31, 18, 59, 59, 999, tzinfo=ZoneInfo("America/New_York")),
        )
    )
    assert not period.contains(
        Period(
            datetime(2025, 12, 30, 19, tzinfo=ZoneInfo("America/New_York")),
            datetime(2026, 12, 31, 18, 59, 59, 999, tzinfo=ZoneInfo("America/New_York")),
        )
    )


@pytest.mark.parametrize(
    "period, expected",
    [
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
            ),
            True,
        ),
        (
            Period(
                datetime(2026, 2, 1, tzinfo=UTC),
                datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
            ),
            False,
        ),
    ],
    ids=[
        "during",
        "not during",
    ],
)
def test_periods_during_other_period_ok(period: Period, expected: bool):
    inner = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    assert inner.during(period=period) == expected


def test_periods_one_period_finishes_another_ok():
    december = Period(
        datetime(2026, 12, 1, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    assert december.finishes(
        Period(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
        )
    )


def test_periods_a_period_finished_by_another_ok():
    december = Period(
        datetime(2026, 12, 1, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
    )
    y2k26 = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    assert y2k26.finished_by(december)


def test_periods_gap_between_two_periods_ok():
    january = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, 23, 59, 59, 999, tzinfo=UTC),
    )
    march = Period(
        datetime(2026, 3, 1, tzinfo=UTC),
        datetime(2026, 3, 31, tzinfo=UTC),
    )
    gap = march.gap(january)

    assert gap is not None
    assert gap.days == 28


@pytest.mark.parametrize(
    "right",
    [
        Period(
            datetime(2026, 1, 31, 23, 59, 59, 999, tzinfo=UTC),
            datetime(2026, 2, 28, tzinfo=UTC),
        ),
        Period(
            datetime(2026, 1, 2, tzinfo=UTC),
            datetime(2026, 1, 30, 23, 59, 59, 999, tzinfo=UTC),
        ),
        Period(
            datetime(2025, 12, 31, tzinfo=UTC),
            datetime(2026, 3, 1, tzinfo=UTC),
        ),
    ],
    ids=[
        "immediate after",
        "overlapping to the end",
        "overlapping to the start",
    ],
)
def test_periods_no_gap_between_two_periods_ok(right: Period):
    left = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    assert left.gap(right) is None


def test_periods_meet_ok():
    period = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    assert period.meets(
        Period(
            datetime(2026, 1, 31, 23, 59, 59, 999, tzinfo=UTC),
            datetime(2026, 2, 28, tzinfo=UTC),
        )
    )


def test_periods_met_by_ok():
    period = Period(
        datetime(2026, 2, 1, tzinfo=UTC),
        datetime(2026, 2, 28, 23, 59, 59, 999, tzinfo=UTC),
    )

    assert period.met_by(
        Period(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 2, 1, tzinfo=UTC),
        )
    )


def test_periods_x_overlaps_with_y_ok():
    x = Period(
        datetime(2026, 2, 1, tzinfo=UTC),
        datetime(2026, 2, 28, 23, 59, 59, 999, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 2, 27, tzinfo=UTC),
        datetime(2026, 3, 1, tzinfo=UTC),
    )

    assert x.overlaps(y)


def test_periods_x_overlapped_by_y_ok():
    x = Period(
        datetime(2026, 2, 1, tzinfo=UTC),
        datetime(2026, 2, 28, 23, 59, 59, 999, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 2, 2, tzinfo=UTC),
    )

    assert x.overlapped_by(y)


def test_periods_x_starts_y():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, 23, 59, 59, 999, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 11, 30, 23, 59, 59, 999, tzinfo=UTC),
    )
    z = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    assert x.starts(y)
    assert not z.starts(y)


def test_periods_y_started_by_x():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, 23, 59, 59, 999, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 12, 31, 23, 59, 59, 999, tzinfo=UTC),
    )

    assert y.started_by(x)
    assert not x.started_by(y)


@pytest.mark.parametrize(
    "inner",
    [
        Period(
            datetime(2026, 1, 7, tzinfo=UTC),
            datetime(2026, 1, 15, tzinfo=UTC),
        ),
        datetime(2026, 1, 2, tzinfo=UTC),
    ],
)
def test_periods_in_operator(inner: Period | datetime):
    outer = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )

    assert inner in outer


def test_periods_equality_operator():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert x == y


def test_periods_greater_than_operator():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 1, 31, tzinfo=UTC),
        datetime(2026, 2, 28, tzinfo=UTC),
    )

    assert y > x


def test_periods_lower_than_operator():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 1, 31, tzinfo=UTC),
        datetime(2026, 2, 28, tzinfo=UTC),
    )

    assert x < y


def test_periods_intersect_operator_returns_overlapping_period():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 1, 29, tzinfo=UTC),
        datetime(2026, 2, 28, tzinfo=UTC),
    )

    assert x & y == Period(
        datetime(2026, 1, 29, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )


def test_periods_intersect_operator_returns_none():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 2, 1, tzinfo=UTC),
        datetime(2026, 2, 28, tzinfo=UTC),
    )

    assert x & y is None


def test_periods_union_operator_returns_joined_period():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 1, 29, tzinfo=UTC),
        datetime(2026, 2, 28, tzinfo=UTC),
    )

    assert x | y == Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 2, 28, tzinfo=UTC),
    )


def test_periods_union_operator_returns_none_when_no_overlapping():
    x = Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )
    y = Period(
        datetime(2026, 2, 1, tzinfo=UTC),
        datetime(2026, 2, 28, tzinfo=UTC),
    )

    assert x | y is None


@pytest.mark.parametrize(
    "left, right, expected",
    [
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 31, tzinfo=UTC),
            ),
            Period(
                datetime(2026, 2, 1, tzinfo=UTC),
                datetime(2026, 2, 28, tzinfo=UTC),
            ),
            [
                Period(
                    datetime(2026, 1, 1, tzinfo=UTC),
                    datetime(2026, 1, 31, tzinfo=UTC),
                ),
                Period(
                    datetime(2026, 2, 1, tzinfo=UTC),
                    datetime(2026, 2, 28, tzinfo=UTC),
                ),
            ],
        ),
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 31, tzinfo=UTC),
            ),
            Period(
                datetime(2026, 1, 30, tzinfo=UTC),
                datetime(2026, 2, 28, tzinfo=UTC),
            ),
            [
                Period(
                    datetime(2026, 1, 1, tzinfo=UTC),
                    datetime(2026, 2, 28, tzinfo=UTC),
                )
            ],
        ),
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 31, tzinfo=UTC),
            ),
            Period(
                datetime(2026, 1, 7, tzinfo=UTC),
                datetime(2026, 1, 14, tzinfo=UTC),
            ),
            [
                Period(
                    datetime(2026, 1, 1, tzinfo=UTC),
                    datetime(2026, 1, 31, tzinfo=UTC),
                )
            ],
        ),
    ],
    ids=[
        "disjoint periods add up to a list of period",
        "overlapping periods add up to a list of a single larger period",
        "inner period add up to a list of the original period",
    ],
)
def test_periods_add_operator_ok(left: Period, right: Period, expected: list[Period]):
    assert left + right == expected


@pytest.mark.parametrize(
    "left, right, expected",
    [
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 31, tzinfo=UTC),
            ),
            Period(
                datetime(2026, 2, 1, tzinfo=UTC),
                datetime(2026, 2, 28, tzinfo=UTC),
            ),
            [
                Period(
                    datetime(2026, 1, 1, tzinfo=UTC),
                    datetime(2026, 1, 31, tzinfo=UTC),
                )
            ],
        ),
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 31, tzinfo=UTC),
            ),
            Period(
                datetime(2026, 1, 8, tzinfo=UTC),
                datetime(2026, 2, 28, tzinfo=UTC),
            ),
            [
                Period(
                    datetime(2026, 1, 1, tzinfo=UTC),
                    datetime(2026, 1, 8, tzinfo=UTC),
                ),
            ],
        ),
        (
            Period(
                datetime(2026, 2, 1, tzinfo=UTC),
                datetime(2026, 2, 28, tzinfo=UTC),
            ),
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 2, 26, tzinfo=UTC),
            ),
            [
                Period(
                    datetime(2026, 2, 26, tzinfo=UTC),
                    datetime(2026, 2, 28, tzinfo=UTC),
                ),
            ],
        ),
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 31, tzinfo=UTC),
            ),
            Period(
                datetime(2026, 1, 7, tzinfo=UTC),
                datetime(2026, 1, 14, tzinfo=UTC),
            ),
            [
                Period(
                    datetime(2026, 1, 1, tzinfo=UTC),
                    datetime(2026, 1, 7, tzinfo=UTC),
                ),
                Period(
                    datetime(2026, 1, 14, tzinfo=UTC),
                    datetime(2026, 1, 31, tzinfo=UTC),
                ),
            ],
        ),
    ],
    ids=[
        "no overlapping",
        "overlapping to the right",
        "overlapping to the left",
        "inner period",
    ],
)
def test_periods_sub_operator_ok(left: Period, right: Period, expected: list[Period]):
    assert left - right == expected
