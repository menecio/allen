from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .periods import Period


@dataclass(slots=True)
class PeriodSet:
    periods: list[Period] = field(default_factory=list)

    def __post_init__(self):
        if any(not isinstance(period, Period) for period in self.periods):
            raise TypeError("All items must be of type Period.")
        self._normalize()

    def __add__(self, other: PeriodSet) -> PeriodSet:
        if not isinstance(other, PeriodSet):
            return NotImplemented

        return PeriodSet(self.periods + other.periods)

    def __and__(self, other: PeriodSet | Period) -> PeriodSet:
        if isinstance(other, Period):
            return PeriodSet(
                [
                    intersection
                    for current in self
                    if (intersection := current.intersect(other)) is not None
                ]
            )
        elif isinstance(other, PeriodSet):
            intersections: list[Period] = []
            self_idx, other_idx = 0, 0
            while self_idx < len(self) and other_idx < len(other):
                current_self, current_other = self[self_idx], other[other_idx]
                if (intersection := current_self.intersect(current_other)) is not None:
                    intersections.append(intersection)
                if current_self.end < current_other.end:
                    self_idx += 1
                else:
                    other_idx += 1
            return PeriodSet(intersections)
        return NotImplemented

    def __len__(self) -> int:
        return len(self.periods)

    def __iter__(self) -> Iterator[Period]:
        return iter(self.periods)

    def __contains__(self, item: Period | datetime) -> bool:
        if isinstance(item, Period):
            return any(item in p for p in self.periods)
        elif isinstance(item, datetime):
            return self.contains_dt(item)
        return False

    def __getitem__(self, index: int) -> Period:
        return self.periods[index]

    def __or__(self, other: PeriodSet) -> PeriodSet:
        return self + other

    def __repr__(self) -> str:
        return f"PeriodSet({self.periods!r})"

    def __sub__(self, other: PeriodSet | Period) -> PeriodSet:
        if isinstance(other, Period):
            return PeriodSet([diff for current in self for diff in current - other])
        elif isinstance(other, PeriodSet):
            current_set = list(self.periods)
            for other_period in other:
                current_set = [diff for p in current_set for diff in p - other_period]
            return PeriodSet(current_set)
        return NotImplemented

    def _normalize(self) -> None:
        if not self.periods:
            return

        sorted_periods = sorted(self.periods)
        normalized = [sorted_periods[0]]
        for current in sorted_periods[1:]:
            last = normalized[-1]
            merged = last.union(current)
            if merged is not None:
                normalized[-1] = merged
            else:
                normalized.append(current)
        self.periods = normalized

    @property
    def duration(self) -> timedelta:
        return sum((p.duration for p in self.periods), start=timedelta())

    @property
    def is_empty(self) -> bool:
        return not self.periods

    @property
    def first(self) -> Period | None:
        if self.is_empty:
            return None
        return self.periods[0]

    @property
    def gaps(self) -> PeriodSet:
        pairs = zip(self.periods[:-1], self.periods[1:])
        return PeriodSet([Period(pair[0].end, pair[1].start) for pair in pairs])

    @property
    def hull(self) -> Period | None:
        if self.is_empty:
            return None
        return Period(self.first.start, self.last.end)

    @property
    def last(self) -> Period | None:
        if self.is_empty:
            return None
        return self.periods[-1]

    def add(self, period: Period) -> None:
        if not isinstance(period, Period):
            raise TypeError("Item must be of type Period.")
        self.periods.append(period)
        self._normalize()

    def contains_dt(self, dt: datetime) -> bool:
        if self.is_empty or dt not in self.hull:
            return False
        return any(dt in period for period in self.periods)
