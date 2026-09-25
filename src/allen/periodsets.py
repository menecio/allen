from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .periods import Period


@dataclass(slots=True)
class PeriodSet:
    """A collection of disjoint, non-overlapping `Period` instances sorted chronologically.

    `PeriodSet` automatically normalizes input periods upon instantiation and modification,
    merging overlapping or contiguous intervals into unified single periods.

    Attributes:
        periods (list[Period]): The underlying sorted and disjoint list of `Period` objects.

    Raises:
        TypeError: If any item passed during initialization is not an instance of `Period`.
    """

    periods: list[Period] = field(default_factory=list)

    def __post_init__(self):
        """Validates element types and applies normalization to ensure disjoint periods."""
        if any(not isinstance(period, Period) for period in self.periods):
            raise TypeError("All items must be of type Period.")
        self._normalize()

    def __add__(self, other: PeriodSet) -> PeriodSet:
        """Operator overloaded set union (`self + other`).

        Args:
            other (PeriodSet): The target set of periods to merge into `self`.

        Returns:
            PeriodSet: A new normalized `PeriodSet` containing the union of both sets.
        """
        if not isinstance(other, PeriodSet):
            return NotImplemented

        return PeriodSet(self.periods + other.periods)

    def __and__(self, other: PeriodSet | Period) -> PeriodSet:
        """Operator overloaded bitwise AND (`self & other`).

        Computes the intersection between `self` and another `Period` or `PeriodSet`.
        Uses an optimized O(N + M) two-pointer algorithm when intersecting two `PeriodSet` instances.

        Args:
            other (PeriodSet | Period): The interval or set of intervals to intersect with.

        Returns:
            PeriodSet: A new `PeriodSet` representing the shared overlapping periods.
        """
        if isinstance(other, Period):
            return PeriodSet(
                [intersection for current in self if (intersection := current.intersect(other)) is not None]
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
        """Returns the total number of disjoint periods in the set.

        Returns:
            int: Number of `Period` instances contained.
        """
        return len(self.periods)

    def __iter__(self) -> Iterator[Period]:
        """Returns an iterator over the underlying sorted periods.

        Returns:
            Iterator[Period]: Iterator yielding periods chronologically.
        """
        return iter(self.periods)

    def __contains__(self, item: Period | datetime) -> bool:
        """Operator overloaded membership check (`item in self`).

        Args:
            item (Period | datetime): The datetime instant or Period to evaluate for containment.

        Returns:
            bool: True if `item` is fully contained within any period in the set, False otherwise.
        """
        if isinstance(item, Period):
            return any(item in p for p in self.periods)
        elif isinstance(item, datetime):
            return self.contains_dt(item)
        return False

    def __getitem__(self, index: int) -> Period:
        """Retrieves a period by its 0-based positional index.

        Args:
            index (int): Index of the period to retrieve.

        Returns:
            Period: The period at the specified index.
        """
        return self.periods[index]

    def __or__(self, other: PeriodSet) -> PeriodSet:
        """Operator overloaded bitwise OR (`self | other`).

        Args:
            other (PeriodSet): Target set of periods to merge with `self`.

        Returns:
            PeriodSet: A new normalized `PeriodSet` containing the union of both sets.
        """
        return self + other

    def __repr__(self) -> str:
        """Returns a developer-friendly string representation of the `PeriodSet`.

        Returns:
            str: Formal string representation.
        """
        return f"PeriodSet({self.periods!r})"

    def __sub__(self, other: PeriodSet | Period) -> PeriodSet:
        """Operator overloaded relative set difference (`self - other`).

        Subtracts overlapping windows of `other` from every period in `self`.

        Args:
            other (PeriodSet | Period): The period or set of periods to subtract.

        Returns:
            PeriodSet: A new `PeriodSet` containing the remaining disjoint intervals.
        """
        if isinstance(other, Period):
            return PeriodSet([diff for current in self for diff in current - other])
        elif isinstance(other, PeriodSet):
            current_set = list(self.periods)
            for other_period in other:
                current_set = [diff for p in current_set for diff in p - other_period]
            return PeriodSet(current_set)
        return NotImplemented

    def _normalize(self) -> None:
        """Sorts and merges contiguous or overlapping periods in-place."""
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
        """Calculates the total aggregate active time across all disjoint periods.

        Returns:
            timedelta: The sum of `duration` across all periods in the set.
        """
        return sum((p.duration for p in self.periods), start=timedelta())

    @property
    def is_empty(self) -> bool:
        """Checks whether the set contains zero periods.

        Returns:
            bool: True if `periods` is empty, False otherwise.
        """
        return not self.periods

    @property
    def first(self) -> Period | None:
        """Returns the chronologically earliest period in the set.

        Returns:
            Period | None: The first `Period` instance, or `None` if the set is empty.
        """
        if self.is_empty:
            return None
        return self.periods[0]

    @property
    def gaps(self) -> PeriodSet:
        """Computes interior idle windows (gaps) separating disjoint periods.

        Returns:
            PeriodSet: A new `PeriodSet` representing the interior gaps between periods.
        """
        pairs = zip(self.periods[:-1], self.periods[1:], strict=False)
        return PeriodSet([Period(pair[0].end, pair[1].start) for pair in pairs])

    @property
    def hull(self) -> Period | None:
        """Calculates a single bounding period spanning from global start to global end.

        Returns:
            Period | None: A `Period` from `first.start` to `last.end`, or `None` if empty.
        """
        if self.is_empty:
            return None
        return Period(self.periods[0].start, self.periods[-1].end)

    @property
    def last(self) -> Period | None:
        """Returns the chronologically latest period in the set.

        Returns:
            Period | None: The last `Period` instance, or `None` if the set is empty.
        """
        if self.is_empty:
            return None
        return self.periods[-1]

    def add(self, period: Period) -> None:
        """Inserts a new `Period` into the set and re-normalizes the collection in-place.

        Args:
            period (Period): The period to add.

        Raises:
            TypeError: If `period` is not an instance of `Period`.
        """
        if not isinstance(period, Period):
            raise TypeError("Item must be of type Period.")
        self.periods.append(period)
        self._normalize()

    def contains_dt(self, dt: datetime) -> bool:
        """Evaluates whether a datetime instant falls within any period in the set.

        Utilizes bounding `hull` evaluation for rapid early-exit determination.

        Args:
            dt (datetime): The datetime instant to check. Must be timezone-aware.

        Returns:
            bool: True if `dt` is within any contained period, False otherwise.
        """
        if (hull := self.hull) is None or dt not in hull:
            return False
        return any(dt in period for period in self.periods)
