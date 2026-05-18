"""Time range parsing for rule-template ask queries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

TIME_RANGE_ALL_TIME = "all_time"
TIME_RANGE_CURRENT_MONTH = "current_month"
TIME_RANGE_LAST_30_DAYS = "last_30_days"
TIME_RANGE_LAST_3_MONTHS = "last_3_months"


@dataclass(frozen=True)
class TimeRange:
    kind: str
    label: str
    start: datetime | None
    end: datetime | None
    grain: str | None = None

    def as_trace(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "label": self.label,
            "start": self.start.isoformat(sep=" ") if self.start else None,
            "end": self.end.isoformat(sep=" ") if self.end else None,
            "grain": self.grain,
        }


def parse_time_range(kind: str, now: datetime) -> TimeRange | None:
    if kind == TIME_RANGE_ALL_TIME:
        return TimeRange(kind=kind, label="全量", start=None, end=None)
    if kind == TIME_RANGE_CURRENT_MONTH:
        start = datetime(now.year, now.month, 1)
        return TimeRange(
            kind=kind,
            label="本月",
            start=start,
            end=_add_months(start, 1),
            grain="month",
        )
    if kind == TIME_RANGE_LAST_30_DAYS:
        return TimeRange(
            kind=kind,
            label="最近30天",
            start=now - timedelta(days=30),
            end=now,
            grain="day",
        )
    if kind == TIME_RANGE_LAST_3_MONTHS:
        this_month = datetime(now.year, now.month, 1)
        return TimeRange(
            kind=kind,
            label="最近三个月",
            start=_add_months(this_month, -2),
            end=_add_months(this_month, 1),
            grain="month",
        )
    return None


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month)
