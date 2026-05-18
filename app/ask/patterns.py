"""Rule-based intent matching for the ask MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .time_range_parser import (
    TIME_RANGE_ALL_TIME,
    TIME_RANGE_CURRENT_MONTH,
    TIME_RANGE_LAST_30_DAYS,
    TIME_RANGE_LAST_3_MONTHS,
)

INTENT_MONTHLY_ENROLLMENT_COUNT = "monthly_enrollment_count"
INTENT_LAST_30_DAYS_INCOME = "last_30_days_income"
INTENT_MONTHLY_REFUND_AMOUNT = "monthly_refund_amount"
INTENT_CAMPUS_ENROLLMENT_RANK = "campus_enrollment_rank"
INTENT_SERIES_REFUND_AMOUNT_RANK = "series_refund_amount_rank"
INTENT_LAST_3_MONTH_COMPLETION_RATE = "last_3_month_completion_rate"


@dataclass(frozen=True)
class QueryPattern:
    intent: str
    metric_code: str
    dimensions: tuple[str, ...]
    time_range_kind: str
    template_key: str


def match_intent(query: str) -> str | None:
    pattern = match_query_pattern(query)
    return pattern.intent if pattern else None


def match_query_pattern(query: str) -> QueryPattern | None:
    text = _normalize(query)
    if "本月" in text and ("报名人数" in text or "报名数" in text):
        return QUERY_PATTERNS[INTENT_MONTHLY_ENROLLMENT_COUNT]
    if ("最近30天" in text or "近30天" in text) and ("收入" in text or "营收" in text):
        return QUERY_PATTERNS[INTENT_LAST_30_DAYS_INCOME]
    if "本月" in text and ("退款金额" in text or "退款额" in text):
        return QUERY_PATTERNS[INTENT_MONTHLY_REFUND_AMOUNT]
    if "校区" in text and ("报名人数最多" in text or "报名最多" in text):
        return QUERY_PATTERNS[INTENT_CAMPUS_ENROLLMENT_RANK]
    if "课程系列" in text and ("退款金额最高" in text or "退款最高" in text):
        return QUERY_PATTERNS[INTENT_SERIES_REFUND_AMOUNT_RANK]
    if ("最近三个月" in text or "近三个月" in text) and "完课率" in text:
        return QUERY_PATTERNS[INTENT_LAST_3_MONTH_COMPLETION_RATE]
    return None


def _normalize(query: str) -> str:
    return re.sub(r"[\s,，。？?！!：:；;、]+", "", query.strip())


QUERY_PATTERNS: dict[str, QueryPattern] = {
    INTENT_MONTHLY_ENROLLMENT_COUNT: QueryPattern(
        intent=INTENT_MONTHLY_ENROLLMENT_COUNT,
        metric_code="enrollment_count",
        dimensions=(),
        time_range_kind=TIME_RANGE_CURRENT_MONTH,
        template_key=INTENT_MONTHLY_ENROLLMENT_COUNT,
    ),
    INTENT_LAST_30_DAYS_INCOME: QueryPattern(
        intent=INTENT_LAST_30_DAYS_INCOME,
        metric_code="paid_amount",
        dimensions=("date",),
        time_range_kind=TIME_RANGE_LAST_30_DAYS,
        template_key=INTENT_LAST_30_DAYS_INCOME,
    ),
    INTENT_MONTHLY_REFUND_AMOUNT: QueryPattern(
        intent=INTENT_MONTHLY_REFUND_AMOUNT,
        metric_code="refund_amount",
        dimensions=(),
        time_range_kind=TIME_RANGE_CURRENT_MONTH,
        template_key=INTENT_MONTHLY_REFUND_AMOUNT,
    ),
    INTENT_CAMPUS_ENROLLMENT_RANK: QueryPattern(
        intent=INTENT_CAMPUS_ENROLLMENT_RANK,
        metric_code="enrollment_count",
        dimensions=("campus",),
        time_range_kind=TIME_RANGE_ALL_TIME,
        template_key=INTENT_CAMPUS_ENROLLMENT_RANK,
    ),
    INTENT_SERIES_REFUND_AMOUNT_RANK: QueryPattern(
        intent=INTENT_SERIES_REFUND_AMOUNT_RANK,
        metric_code="refund_amount",
        dimensions=("series",),
        time_range_kind=TIME_RANGE_ALL_TIME,
        template_key=INTENT_SERIES_REFUND_AMOUNT_RANK,
    ),
    INTENT_LAST_3_MONTH_COMPLETION_RATE: QueryPattern(
        intent=INTENT_LAST_3_MONTH_COMPLETION_RATE,
        metric_code="completion_rate",
        dimensions=("date",),
        time_range_kind=TIME_RANGE_LAST_3_MONTHS,
        template_key=INTENT_LAST_3_MONTH_COMPLETION_RATE,
    ),
}
