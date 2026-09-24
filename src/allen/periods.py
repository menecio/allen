from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True, slots=True)
class Period:
    start: datetime
    end: datetime

    @staticmethod
    def _validate_dt_type(value: Any):
        if not isinstance(value, datetime):
            raise TypeError(f"Expected datetime, got `{type(value)}`.")

    @staticmethod
    def _validate_naive_dt(value: datetime):
        if value.tzinfo is None:
            raise ValueError("Start and End must be timezone-aware.")

    def _validate_tz(self):
        if self.start.utcoffset() != self.end.utcoffset():
            raise ValueError("Start and End must be in the same timezone.")

    def _validate_start_lt_end(self):
        if self.start >= self.end:
            raise ValueError("End must be greater than Start.")

    def __post_init__(self):
        self._validate_dt_type(self.start)
        self._validate_dt_type(self.end)
        self._validate_naive_dt(self.start)
        self._validate_naive_dt(self.end)
        self._validate_tz()
        self._validate_start_lt_end()

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def is_after(self, period: Period) -> bool:
        return self.start >= period.end

    def is_before(self, period: Period) -> bool:
        return self.end <= period.start

    def _contains_dt(self, value: datetime) -> bool:
        if value.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware.")
        return self.start <= value < self.end

    def _contains_period(self, period: Period) -> bool:
        return self.start <= period.start and period.end <= self.end

    def contains(self, item: datetime | Period) -> bool:
        if isinstance(item, Period):
            return self._contains_period(item)
        elif isinstance(item, datetime):
            return self._contains_dt(item)
        else:
            raise TypeError(f"Expected datetime or Period, got `{type(item)}`.")

    def during(self, period: Period) -> bool:
        return period.contains(self)

    def finishes(self, period: Period) -> bool:
        return self.end == period.end and self.start > period.start

    def finished_by(self, period: Period) -> bool:
        return period.finishes(self)

    def gap(self, period: Period) -> timedelta | None:
        if self.end < period.start:
            return period.start - self.end
        elif period.end < self.start:
            return self.start - period.end
        return None

    def intersect(self, period: Period) -> Period | None:
        max_start = max(self.start, period.start)
        min_end = min(self.end, period.end)
        if max_start < min_end:
            return Period(max_start, min_end)
        return None

    def meets(self, period: Period) -> bool:
        return self.end == period.start

    def met_by(self, period: Period) -> bool:
        return period.meets(self)

    def overlaps(self, period: Period) -> bool:
        return self.start < period.start < self.end < period.end

    def overlapped_by(self, period: Period) -> bool:
        return period.overlaps(self)

    def starts(self, period: Period) -> bool:
        return self.start == period.start and self.end < period.end

    def started_by(self, period: Period) -> bool:
        return period.starts(self)

    def union(self, period: Period) -> Period | None:
        max_start = max(self.start, period.start)
        min_end = min(self.end, period.end)
        if max_start <= min_end:
            return Period(
                min(self.start, period.start),
                max(self.end, period.end),
            )
        return None

    def __add__(self, other: Period) -> list[Period]:
        if not isinstance(other, Period):
            return NotImplemented
        if (merged := self.union(other)) is not None:
            return [merged]
        return sorted([self, other])

    def __and__(self, period: Period) -> Period | None:
        return self.intersect(period)

    def __contains__(self, item: datetime | Period) -> bool:
        return self.contains(item)

    def __eq__(self, period: Period | Any) -> bool:
        if not isinstance(period, Period):
            return NotImplemented
        return self.start == period.start and self.end == period.end

    def __gt__(self, period: Period) -> bool:
        return self.is_after(period)

    def __lt__(self, period: Period) -> bool:
        return self.is_before(period)

    def __or__(self, period: Period) -> Period | None:
        return self.union(period)

    def __sub__(self, period: Period) -> list[Period]:
        if not isinstance(period, Period):
            return NotImplemented

        if self.intersect(period) is None:
            return [self]

        has_left_remainder = self.start < period.start
        has_right_remainder = self.end > period.end

        match (has_left_remainder, has_right_remainder):
            case (True, True):
                return [
                    Period(self.start, period.start),
                    Period(period.end, self.end),
                ]
            case (True, False):
                return [Period(self.start, period.start)]
            case (False, True):
                return [Period(period.end, self.end)]
        return []
