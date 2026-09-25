<div align="center">

# ⏳ Allen

**A modern, type-safe Python library for modeling, normalizing, and manipulating time periods using Allen's Interval
Algebra.**

[![PyPI version](https://badge.fury.io/py/allen-python.svg)](https://badge.fury.io/py/allen-python)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Checked with Pyright](https://img.shields.io/badge/type%20checker-pyright-brightgreen.svg)](https://github.com/microsoft/pyright)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 📌 Overview

Working with complex time ranges, schedules, overlapping events, and gaps in Python can easily lead to spaghetti code
full of nested `if/else` checks.

**`allen`** provides high-performance, strictly typed primitives (`Period` and `PeriodSet`) that
implement [Allen's Interval Algebra relations](https://en.wikipedia.org/wiki/Allen%27s_interval_algebra#Relations) (such
as *before*, *meets*, *overlaps*, *starts*, *during*, *finishes*, and *equals*).

It abstracts away edge-case complexity by automatically merging overlapping or contiguous intervals, calculating
interior gaps, computing intersections, and performing set arithmetic (`+`, `-`, `&`, `|`) in $O (N \log N)$ or
linear $O (N + M)$ time.

---

## ✨ Key Features

* **Zero external dependencies**: Lightweight and fast.
* **Strictly Typed & PEP 561 Compliant**: Built with `py.typed` and zero-suppression typing for Pyright/Mypy strict
  modes.
* **Automatic Normalization**: `PeriodSet` keeps intervals sorted, non-overlapping, and disjoint by design.
* **Intuitive Set Algebra**: Overloaded Python operators (`+`, `-`, `&`, `|`) for declarative time manipulations.
* **Immutability & Safety**: Memory-efficient slots-based dataclasses preventing accidental side effects.

---

## 📦 Installation

Install `allen` using [`uv`](https://github.com/astral-sh/uv) or `pip`:

```bash
# Using uv (Recommended)
uv add allen-python

# Using pip
pip install allen-python
```

## 🚀 Quickstart & Real-World Examples

### 1. Merging Overlapping Shifts (Scheduler Normalization)

**Use Case:** You receive raw shift records from multiple employees or systems. Some shifts overlap or are contiguous.
You want to compute the total actual working hours without double-counting overlapping times.

```python
from datetime import datetime, timezone
from allen import Period, PeriodSet

# Raw shift logs (some overlapping, some contiguous)
shift1 = Period(
    datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc),
    datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
)
shift2 = Period(
    datetime(2026, 10, 1, 11, 0, tzinfo=timezone.utc),
    datetime(2026, 10, 1, 15, 0, tzinfo=timezone.utc)
)  # Overlaps shift1
shift3 = Period(
    datetime(2026, 10, 1, 16, 0, tzinfo=timezone.utc),
    datetime(2026, 10, 1, 18, 0, tzinfo=timezone.utc)
)  # Disjoint shift

# Creating a PeriodSet automatically normalizes and merges overlaps
work_day = PeriodSet([shift1, shift2, shift3])

print(f"Normalized periods: {len(work_day)}")  # Output: 2
print(f"Total worked hours: {work_day.duration}")  # Output: 9:00:00
```

### 2. Finding Available Slot Windows (Calendar Free/Busy Analysis)

**Use Case:** You are building a booking engine. You know a provider's total working window (`hull`) and their booked
appointments (`PeriodSet`). You need to find all available idle windows (`gaps`).

```python
from datetime import datetime, timezone
from allen import Period, PeriodSet

# Appointments booked throughout the day
appointments = PeriodSet([
    Period(
        datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 1, 10, 30, tzinfo=timezone.utc)
    ),
    Period(
        datetime(2026, 10, 1, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    ),
    Period(
        datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 1, 15, 30, tzinfo=timezone.utc)
    ),
])

# Extract the idle gaps between scheduled appointments
free_slots = appointments.gaps

for slot in free_slots:
    print(f"Available break: {slot.start.strftime('%H:%M')} -> {slot.end.strftime('%H:%M')}")

# Output:
# Available break: 10:30 -> 11:00
# Available break: 12:00 -> 14:00
```

### 3. Subtracting Maintenance Windows (Uptime Calculation)

**Use Case:** You monitor server uptime across a month, but you must exclude scheduled maintenance windows
(`PeriodSet - PeriodSet` or `PeriodSet - Period`) to calculate SLA compliance.

```python
from datetime import datetime, timezone
from allen import Period, PeriodSet

# Total active uptime monitor
active_window = PeriodSet([
    Period(
        datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 10, 1, 23, 59, tzinfo=timezone.utc)
    )
])

# Maintenance windows to exclude
maintenance = Period(
    datetime(2026, 10, 1, 13, 0, tzinfo=timezone.utc),
    datetime(2026, 10, 1, 15, 0, tzinfo=timezone.utc)
)

# Perform set difference
billable_uptime = active_window - maintenance

print(f"Remaining disjoint periods: {len(billable_uptime)}")  # Output: 2
print(f"Net operational duration: {billable_uptime.duration}")  # Output: 21:59:00
```

## 🛠️ API Reference Summary

### `Period`

Primitive representing a single timezone-aware half-open interval $[start, end)$.
All `datetime` objects must be timezone-aware (e.g., `tzinfo=timezone.utc`).

* **Instantiation**: `Period(start: datetime, end: datetime)`
* **Key Methods**:
    * `.intersect(other: Period) -> Period | None`: Returns the overlapping period or `None`.
    * `.union(other: Period) -> Period | None`: Merges contiguous or overlapping periods into one.
* **Operators**:
    * `period_a - period_b -> list[Period]`: Set difference between two single periods.
    * `dt in period`: Returns `True` if `dt` falls within $[start, end)$.

---

### `PeriodSet`

Normalizing collection that automatically keeps a sequence of `Period` instances sorted, non-overlapping, and disjoint.

* **Instantiation**: `PeriodSet(periods: list[Period] = [])`
* **Operators**:
    * `+` / `|`: Union of sets/periods (`PeriodSet + PeriodSet`).
    * `-`: Set difference (`PeriodSet - PeriodSet` or `PeriodSet - Period`).
    * `&`: Set intersection (`PeriodSet & PeriodSet` or `PeriodSet & Period`).
    * `dt in period_set`: Checks if a `datetime` or `Period` is contained.
* **Properties**:
    * `.duration -> timedelta`: Sum of active durations across all disjoint periods.
    * `.gaps -> PeriodSet`: Returns a new `PeriodSet` representing the interior gaps between periods.
    * `.hull -> Period | None`: Returns a single `Period` spanning from global `.first.start` to `.last.end`.
    * `.first -> Period | None`: Returns the earliest period in the set.
    * `.last -> Period | None`: Returns the latest period in the set.
    * `.is_empty -> bool`: Returns `True` if the set contains no periods.

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more details.
