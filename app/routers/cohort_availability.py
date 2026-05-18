"""Cohort sale availability checks shared by router endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..errors import conflict, not_found
from ..utils import local_now

CLOSABLE_DELIVERY_MODES = {"online_live", "offline_face_to_face"}


def ensure_series_on_sale(series: dict[str, Any] | None) -> dict[str, Any]:
    if series is None or series.get("sale_status") != "on_sale":
        raise conflict("SERIES_NOT_ON_SALE", "课程不存在或未上架")
    return series


def ensure_cohort_viewable(cohort: dict[str, Any] | None) -> dict[str, Any]:
    if cohort is None or cohort.get("yn") != 1:
        raise not_found("COHORT_NOT_FOUND", "班次不存在")
    ensure_series_on_sale(cohort)
    return cohort


def ensure_cohort_tradable(cohort: dict[str, Any] | None) -> dict[str, Any]:
    cohort = ensure_cohort_viewable(cohort)
    if is_cohort_closed(cohort):
        raise conflict("COHORT_CLOSED", "班次已结束")
    return cohort


def is_cohort_closed(cohort: dict[str, Any]) -> bool:
    if cohort.get("delivery_mode") not in CLOSABLE_DELIVERY_MODES:
        return False
    end_date = _as_date(cohort.get("end_date"))
    return end_date is None or local_now().date() > end_date


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()
