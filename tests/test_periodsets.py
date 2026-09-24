from datetime import UTC, datetime, timedelta

import pytest

from allen import Period, PeriodSet


@pytest.fixture
def period_january() -> Period:
    return Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 31, tzinfo=UTC),
    )


@pytest.fixture
def period_march() -> Period:
    return Period(
        datetime(2026, 3, 1, tzinfo=UTC),
        datetime(2026, 3, 31, tzinfo=UTC),
    )


@pytest.fixture
def default_periodset(
    period_january: Period,
    period_march: Period,
) -> PeriodSet:
    return PeriodSet([period_january, period_march])


def test_all_items_must_be_of_period_type():
    with pytest.raises(TypeError):
        PeriodSet([1, 2, 3])


def test_periods_can_be_an_empty_list():
    p = PeriodSet([])

    assert p.is_empty


def test_periods_are_sorted_by_default():
    periods = [
        Period(
            datetime(2026, 9, 1, tzinfo=UTC),
            datetime(2026, 9, 2, tzinfo=UTC),
        ),
        Period(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        ),
    ]
    p = PeriodSet(periods)

    assert p.periods == [
        Period(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        ),
        Period(
            datetime(2026, 9, 1, tzinfo=UTC),
            datetime(2026, 9, 2, tzinfo=UTC),
        ),
    ]


def test_overlapping_periods_are_joined_by_default():
    periods = [
        Period(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 31, tzinfo=UTC),
        ),
        Period(
            datetime(2026, 1, 15, tzinfo=UTC),
            datetime(2026, 9, 2, tzinfo=UTC),
        ),
    ]
    p = PeriodSet(periods)

    assert p.periods == [
        Period(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 9, 2, tzinfo=UTC),
        ),
    ]


def test_periodset_duration(default_periodset: PeriodSet):
    assert default_periodset.duration == timedelta(days=60)


def test_periodset_first_period_property(
    default_periodset: PeriodSet,
    period_january: Period,
):
    assert default_periodset.first == period_january


def test_periodset_last_period_property(
    default_periodset: PeriodSet,
    period_march: Period,
):
    assert default_periodset.last == period_march


@pytest.mark.parametrize(
    "periodset, expected",
    [
        (
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        datetime(2026, 1, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 3, 1, tzinfo=UTC),
                        datetime(2026, 3, 31, tzinfo=UTC),
                    ),
                ]
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 31, tzinfo=UTC),
                        datetime(2026, 3, 1, tzinfo=UTC),
                    ),
                ]
            ),
        ),
        (
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        datetime(2026, 1, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 1, 31, tzinfo=UTC),
                        datetime(2026, 3, 31, tzinfo=UTC),
                    ),
                ]
            ),
            PeriodSet([]),
        ),
    ],
    ids=[
        "disjoint periods",
        "continuous periods",
    ],
)
def test_gaps(periodset: PeriodSet, expected: PeriodSet):
    assert periodset.gaps == expected


def test_periodset_hull_covers_the_whole_period(default_periodset: PeriodSet):
    assert default_periodset.hull == Period(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 3, 31, tzinfo=UTC),
    )


def test_periodset_hull_is_none_when_periodset_is_empty(default_periodset: PeriodSet):
    assert PeriodSet().hull is None


def test_periodset_contains_datetime(default_periodset: PeriodSet):
    assert default_periodset.contains_dt(datetime(2026, 1, 3, tzinfo=UTC))
    assert not default_periodset.contains_dt(datetime(2026, 2, 1, tzinfo=UTC))


def test_adding_periods_to_periodset_joins_overlapping_periods(
    default_periodset: PeriodSet,
):
    new_period = Period(
        datetime(2026, 1, 31, tzinfo=UTC),
        datetime(2026, 3, 1, tzinfo=UTC),
    )
    default_periodset.add(new_period)

    assert default_periodset.periods == [
        Period(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 3, 31, tzinfo=UTC),
        )
    ]


def test_adding_period_to_periodset_enforces_order(
    default_periodset: PeriodSet,
    period_january: Period,
    period_march: Period,
):
    new_period = Period(
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 1, 10, tzinfo=UTC),
    )
    default_periodset.add(new_period)

    assert default_periodset.periods == [new_period, period_january, period_march]


def test_length_returns_periods_count(default_periodset: PeriodSet):
    assert len(default_periodset) == 2


@pytest.mark.parametrize(
    "left, expected",
    [
        (datetime(2026, 1, 3, tzinfo=UTC), True),
        (datetime(2026, 2, 3, tzinfo=UTC), False),
        (
            Period(
                datetime(2026, 1, 3, tzinfo=UTC),
                datetime(2026, 1, 6, tzinfo=UTC),
            ),
            True,
        ),
        (
            Period(
                datetime(2026, 10, 3, tzinfo=UTC),
                datetime(2026, 11, 6, tzinfo=UTC),
            ),
            False,
        ),
    ],
    ids=[
        "dt in periodset",
        "dt not in periodset",
        "period in periodset",
        "period not in periodset",
    ],
)
def test_in_operator(
    default_periodset: PeriodSet,
    left: Period | datetime,
    expected: bool,
):
    assert (left in default_periodset) == expected


@pytest.mark.parametrize(
    "right, expected",
    [
        (
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 31, tzinfo=UTC),
                        datetime(2026, 3, 1, tzinfo=UTC),
                    )
                ]
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        datetime(2026, 3, 31, tzinfo=UTC),
                    )
                ]
            ),
        ),
        (
            PeriodSet(
                [
                    Period(
                        datetime(2026, 5, 1, tzinfo=UTC),
                        datetime(2026, 5, 31, tzinfo=UTC),
                    )
                ]
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        datetime(2026, 1, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 3, 1, tzinfo=UTC),
                        datetime(2026, 3, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 5, 1, tzinfo=UTC),
                        datetime(2026, 5, 31, tzinfo=UTC),
                    ),
                ]
            ),
        ),
    ],
    ids=[
        "operation joins overlapping periods",
        "operation concatenates non overlapping periods",
    ],
)
def test_add_operator(
    default_periodset: PeriodSet,
    right: PeriodSet,
    expected: PeriodSet,
):
    assert (default_periodset + right) == expected


@pytest.mark.parametrize(
    "right, expected",
    [
        (
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 31, tzinfo=UTC),
                        datetime(2026, 3, 1, tzinfo=UTC),
                    )
                ]
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        datetime(2026, 3, 31, tzinfo=UTC),
                    )
                ]
            ),
        ),
        (
            PeriodSet(
                [
                    Period(
                        datetime(2026, 5, 1, tzinfo=UTC),
                        datetime(2026, 5, 31, tzinfo=UTC),
                    )
                ]
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        datetime(2026, 1, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 3, 1, tzinfo=UTC),
                        datetime(2026, 3, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 5, 1, tzinfo=UTC),
                        datetime(2026, 5, 31, tzinfo=UTC),
                    ),
                ]
            ),
        ),
    ],
    ids=[
        "operation joins overlapping periods",
        "operation concatenates non overlapping periods",
    ],
)
def test_or_operator(
    default_periodset: PeriodSet,
    right: PeriodSet,
    expected: PeriodSet,
):
    assert (default_periodset | right) == expected


@pytest.mark.parametrize(
    "right, expected",
    [
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 7, tzinfo=UTC),
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 7, tzinfo=UTC),
                        datetime(2026, 1, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 3, 1, tzinfo=UTC),
                        datetime(2026, 3, 31, tzinfo=UTC),
                    ),
                ]
            ),
        ),
        (
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 7, tzinfo=UTC),
                        datetime(2026, 1, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 3, 1, tzinfo=UTC),
                        datetime(2026, 3, 31, tzinfo=UTC),
                    ),
                ]
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        datetime(2026, 1, 7, tzinfo=UTC),
                    ),
                ]
            ),
        ),
    ],
    ids=[
        "supports subtracting a Period",
        "supports subtracting a PeriodSet",
    ],
)
def test_substraction_operator(
    default_periodset: PeriodSet,
    right: Period | PeriodSet,
    expected: PeriodSet,
):
    assert (default_periodset - right) == expected


@pytest.mark.parametrize(
    "right, expected",
    [
        (
            Period(
                datetime(2026, 1, 1, tzinfo=UTC),
                datetime(2026, 1, 7, tzinfo=UTC),
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 1, tzinfo=UTC),
                        datetime(2026, 1, 7, tzinfo=UTC),
                    )
                ]
            ),
        ),
        (
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 7, tzinfo=UTC),
                        datetime(2026, 1, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 3, 1, tzinfo=UTC),
                        datetime(2026, 3, 15, tzinfo=UTC),
                    ),
                ]
            ),
            PeriodSet(
                [
                    Period(
                        datetime(2026, 1, 7, tzinfo=UTC),
                        datetime(2026, 1, 31, tzinfo=UTC),
                    ),
                    Period(
                        datetime(2026, 3, 1, tzinfo=UTC),
                        datetime(2026, 3, 15, tzinfo=UTC),
                    ),
                ]
            ),
        ),
    ],
    ids=[
        "supports subtracting a Period",
        "supports subtracting a PeriodSet",
    ],
)
def test_intersection_operator(
    default_periodset: PeriodSet,
    right: Period | PeriodSet,
    expected: PeriodSet,
):
    assert (default_periodset & right) == expected
