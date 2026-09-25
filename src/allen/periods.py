from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True, slots=True)
class Period:
    """Represents a single timezone-aware, half-open temporal interval [start, end).

    Attributes:
        start (datetime): The inclusive start boundary of the interval. Must be timezone-aware.
        end (datetime): The exclusive end boundary of the interval. Must be timezone-aware.

    Raises:
        TypeError: If `start` or `end` are not `datetime` instances.
        ValueError: If `start` or `end` are naive (missing `tzinfo`), if UTC offsets differ,
            or if `start >= end`.
    """

    start: datetime
    end: datetime

    @staticmethod
    def _validate_dt_type(value: Any):
        """Validates that a given input is an instance of `datetime`.

        Args:
            value (Any): The value to check.

        Raises:
            TypeError: If `value` is not a `datetime` instance.
        """
        if not isinstance(value, datetime):
            raise TypeError(f"Expected datetime, got `{type(value)}`.")

    @staticmethod
    def _validate_naive_dt(value: datetime):
        """Validates that a datetime object is timezone-aware.

        Args:
            value (datetime): The datetime instance to validate.

        Raises:
            ValueError: If `value.tzinfo` is None (i.e., naive datetime).
        """
        if value.tzinfo is None:
            raise ValueError("Start and End must be timezone-aware.")

    def _validate_tz(self):
        """Validates that `start` and `end` have identical UTC offsets.

        Raises:
            ValueError: If `start` and `end` have differing UTC offsets.
        """
        if self.start.utcoffset() != self.end.utcoffset():
            raise ValueError("Start and End must be in the same timezone.")

    def _validate_start_lt_end(self):
        """Validates that `start` is strictly less than `end`.

        Raises:
            ValueError: If `start` is greater than or equal to `end`.
        """
        if self.start >= self.end:
            raise ValueError("End must be greater than Start.")

    def __post_init__(self):
        """Executes post-initialization validation rules on the interval."""
        self._validate_dt_type(self.start)
        self._validate_dt_type(self.end)
        self._validate_naive_dt(self.start)
        self._validate_naive_dt(self.end)
        self._validate_tz()
        self._validate_start_lt_end()

    @property
    def duration(self) -> timedelta:
        """Calculates the total time duration spanned by the period.

        Returns:
            timedelta: The exact time difference (`end - start`).
        """
        return self.end - self.start

    def is_after(self, period: Period) -> bool:
        """Determines whether this period occurs entirely after another period.

        Implements Allen's *after* (or *preceded by*) relation.

        Args:
            period (Period): The period to compare against.

        Returns:
            bool: True if `self.start >= period.end`, False otherwise.
        """
        return self.start >= period.end

    def is_before(self, period: Period) -> bool:
        """Determines whether this period occurs entirely before another period.

        Implements Allen's *before* relation.

        Args:
            period (Period): The period to compare against.

        Returns:
            bool: True if `self.end <= period.start`, False otherwise.
        """
        return self.end <= period.start

    def _contains_dt(self, value: datetime) -> bool:
        """Checks if a datetime instant falls within this interval [start, end).

        Args:
            value (datetime): The datetime instant to check. Must be timezone-aware.

        Returns:
            bool: True if `start <= value < end`, False otherwise.

        Raises:
            ValueError: If `value` is timezone-naive.
        """
        if value.tzinfo is None:
            raise ValueError("Datetime must be timezone-aware.")
        return self.start <= value < self.end

    def _contains_period(self, period: Period) -> bool:
        """Checks if another period is fully enclosed within this interval.

        Args:
            period (Period): The target period to evaluate.

        Returns:
            bool: True if `period` is fully contained within `self`, False otherwise.
        """
        return self.start <= period.start and period.end <= self.end

    def contains(self, item: datetime | Period) -> bool:
        """Checks whether a datetime instant or another Period is contained within this interval.

        Args:
            item (datetime | Period): The instant or interval to check for containment.

        Returns:
            bool: True if `item` is within `self`, False otherwise.

        Raises:
            TypeError: If `item` is neither a `datetime` nor a `Period`.
            ValueError: If `item` is a `datetime` and is timezone-naive.
        """
        if isinstance(item, Period):
            return self._contains_period(item)
        elif isinstance(item, datetime):
            return self._contains_dt(item)
        else:
            raise TypeError(f"Expected datetime or Period, got `{type(item)}`.")

    def during(self, period: Period) -> bool:
        """Determines whether this period is fully contained within another period.

        Implements Allen's *during* relation.

        Args:
            period (Period): The enclosing period to evaluate against.

        Returns:
            bool: True if `self` is fully contained inside `period`, False otherwise.
        """
        return period.contains(self)

    def finishes(self, period: Period) -> bool:
        """Determines whether this period shares the same end boundary as another period
        and starts later.

        Implements Allen's *finishes* relation.

        Args:
            period (Period): The reference period to compare against.

        Returns:
            bool: True if `self.end == period.end` and `self.start > period.start`, False otherwise.
        """
        return self.end == period.end and self.start > period.start

    def finished_by(self, period: Period) -> bool:
        """Determines whether another period finishes this period.

        Implements Allen's *finished-by* relation (inverse of *finishes*).

        Args:
            period (Period): The reference period to compare against.

        Returns:
            bool: True if `period` finishes `self`, False otherwise.
        """
        return period.finishes(self)

    def gap(self, period: Period) -> timedelta | None:
        """Calculates the time duration separating two disjoint periods.

        Args:
            period (Period): The target period to compute the gap with.

        Returns:
            timedelta | None: A `timedelta` representing the duration between the periods,
                or `None` if the periods overlap or touch.
        """
        if self.end < period.start:
            return period.start - self.end
        elif period.end < self.start:
            return self.start - period.end
        return None

    def intersect(self, period: Period) -> Period | None:
        """Computes the overlapping interval between this period and another.

        Args:
            period (Period): The target period to intersect with.

        Returns:
            Period | None: A new `Period` representing the shared overlapping interval,
                or `None` if there is no overlap.
        """
        max_start = max(self.start, period.start)
        min_end = min(self.end, period.end)
        if max_start < min_end:
            return Period(max_start, min_end)
        return None

    def meets(self, period: Period) -> bool:
        """Determines whether this period meets another period (i.e., touches end-to-start).

        Implements Allen's *meets* relation.

        Args:
            period (Period): The subsequent period to evaluate.

        Returns:
            bool: True if `self.end == period.start`, False otherwise.
        """
        return self.end == period.start

    def met_by(self, period: Period) -> bool:
        """Determines whether this period is met by another period (i.e., touches start-to-end).

        Implements Allen's *met-by* relation (inverse of *meets*).

        Args:
            period (Period): The preceding period to evaluate.

        Returns:
            bool: True if `period.end == self.start`, False otherwise.
        """
        return period.meets(self)

    def overlaps(self, period: Period) -> bool:
        """Determines whether this period starts before and overlaps into another period.

        Implements Allen's *overlaps* relation.

        Args:
            period (Period): The overlapping period to evaluate.

        Returns:
            bool: True if `self.start < period.start < self.end < period.end`, False otherwise.
        """
        return self.start < period.start < self.end < period.end

    def overlapped_by(self, period: Period) -> bool:
        """Determines whether another period overlaps into this period.

        Implements Allen's *overlapped-by* relation (inverse of *overlaps*).

        Args:
            period (Period): The reference period to evaluate.

        Returns:
            bool: True if `period` overlaps `self`, False otherwise.
        """
        return period.overlaps(self)

    def starts(self, period: Period) -> bool:
        """Determines whether this period shares the same start boundary as another period
        and ends earlier.

        Implements Allen's *starts* relation.

        Args:
            period (Period): The reference period to compare against.

        Returns:
            bool: True if `self.start == period.start` and `self.end < period.end`, False otherwise.
        """
        return self.start == period.start and self.end < period.end

    def started_by(self, period: Period) -> bool:
        """Determines whether another period starts this period.

        Implements Allen's *started-by* relation (inverse of *starts*).

        Args:
            period (Period): The reference period to compare against.

        Returns:
            bool: True if `period` starts `self`, False otherwise.
        """
        return period.starts(self)

    def union(self, period: Period) -> Period | None:
        """Merges this period with another period if they overlap or touch.

        Args:
            period (Period): The period to merge with.

        Returns:
            Period | None: A new merged `Period` if overlapping or contiguous,
                or `None` if disjoint.
        """
        max_start = max(self.start, period.start)
        min_end = min(self.end, period.end)
        if max_start <= min_end:
            return Period(
                min(self.start, period.start),
                max(self.end, period.end),
            )
        return None

    def __add__(self, other: Period) -> list[Period]:
        """Operator overloaded addition (`self + other`).

        Merges overlapping/contiguous periods into a single element list or returns
        a sorted two-element list if disjoint.

        Args:
            other (Period): The target period to add.

        Returns:
            list[Period]: A list containing one merged `Period` or two sorted disjoint `Period`s.
        """
        if not isinstance(other, Period):
            return NotImplemented
        if (merged := self.union(other)) is not None:
            return [merged]
        return sorted([self, other])

    def __and__(self, period: Period) -> Period | None:
        """Operator overloaded bitwise AND (`self & period`).

        Computes the intersection of two periods.

        Args:
            period (Period): The target period to intersect with.

        Returns:
            Period | None: Overlapping `Period` or `None` if disjoint.
        """
        return self.intersect(period)

    def __contains__(self, item: datetime | Period) -> bool:
        """Operator overloaded membership test (`item in self`).

        Args:
            item (datetime | Period): Instant or interval to check for containment.

        Returns:
            bool: True if contained, False otherwise.
        """
        return self.contains(item)

    def __eq__(self, period: Period | Any) -> bool:
        """Evaluates equality between two `Period` instances (`self == period`).

        Args:
            period (Period | Any): Object to compare with.

        Returns:
            bool: True if both `start` and `end` match exactly, False otherwise.
        """
        if not isinstance(period, Period):
            return NotImplemented
        return self.start == period.start and self.end == period.end

    def __gt__(self, period: Period) -> bool:
        """Operator overloaded greater-than comparison (`self > period`).

        Args:
            period (Period): Target period to compare.

        Returns:
            bool: True if `self` occurs after `period`.
        """
        return self.is_after(period)

    def __lt__(self, period: Period) -> bool:
        """Operator overloaded less-than comparison (`self < period`).

        Args:
            period (Period): Target period to compare.

        Returns:
            bool: True if `self` occurs before `period`.
        """
        return self.is_before(period)

    def __or__(self, period: Period) -> Period | None:
        """Operator overloaded bitwise OR (`self | period`).

        Merges two periods if overlapping or contiguous.

        Args:
            period (Period): Target period to merge.

        Returns:
            Period | None: Merged `Period` or `None`.
        """
        return self.union(period)

    def __sub__(self, period: Period) -> list[Period]:
        """Operator overloaded subtraction (`self - period`).

        Calculates the relative set difference between two single periods.

        Args:
            period (Period): The period window to subtract from `self`.

        Returns:
            list[Period]: A list containing 0, 1, or 2 disjoint remaining `Period`s.
        """
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
