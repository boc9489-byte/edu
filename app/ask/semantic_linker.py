"""Link LLM semantic extraction to existing ask rule templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .dimension_registry import get_dimension
from .llm_extractor import LLMExtraction
from .metric_registry import get_metric
from .patterns import (
    INTENT_CAMPUS_ENROLLMENT_RANK,
    INTENT_LAST_30_DAYS_INCOME,
    INTENT_LAST_3_MONTH_COMPLETION_RATE,
    INTENT_MONTHLY_ENROLLMENT_COUNT,
    INTENT_MONTHLY_REFUND_AMOUNT,
    INTENT_SERIES_REFUND_AMOUNT_RANK,
    QueryPattern,
)
from .sql_templates import get_sql_template
from .time_range_parser import (
    TIME_RANGE_ALL_TIME,
    TIME_RANGE_CURRENT_MONTH,
    TIME_RANGE_LAST_30_DAYS,
    TIME_RANGE_LAST_3_MONTHS,
)


@dataclass(frozen=True)
class SemanticLinkResult:
    pattern: QueryPattern
    selected_metric: str
    selected_dimensions: tuple[str, ...]
    time_range_kind: str
    template_key: str

    def to_trace(self) -> dict[str, Any]:
        return {
            "matched": True,
            "metricCode": self.selected_metric,
            "dimensions": list(self.selected_dimensions),
            "timeRangeKind": self.time_range_kind,
            "templateKey": self.template_key,
            "intent": self.pattern.intent,
        }


def link_extraction(extraction: LLMExtraction) -> SemanticLinkResult | None:
    metrics = extraction.metric_code_candidates
    dimensions = extraction.dimension_code_candidates
    if not metrics:
        return None
    if any(get_metric(metric_code) is None for metric_code in metrics):
        return None
    if any(get_dimension(dimension_code) is None for dimension_code in dimensions):
        return None

    metric_code = metrics[0]
    selected_dimensions = tuple(dict.fromkeys(dimensions))
    time_range_kind = _resolve_time_range_kind(extraction)
    template_key = _resolve_template_key(
        metric_code=metric_code,
        dimensions=selected_dimensions,
        time_range_kind=time_range_kind,
        analysis_type=extraction.analysis_type,
        sort=extraction.sort,
    )
    if template_key is None or get_sql_template(template_key) is None:
        return None

    pattern = QueryPattern(
        intent=template_key,
        metric_code=metric_code,
        dimensions=selected_dimensions,
        time_range_kind=time_range_kind,
        template_key=template_key,
    )
    return SemanticLinkResult(
        pattern=pattern,
        selected_metric=metric_code,
        selected_dimensions=selected_dimensions,
        time_range_kind=time_range_kind,
        template_key=template_key,
    )


def _resolve_time_range_kind(extraction: LLMExtraction) -> str:
    time_range = extraction.time_range
    text = str(time_range.get("text") or "")
    grain = str(time_range.get("grain") or "")
    range_type = str(time_range.get("type") or "")
    haystack = f"{text}{grain}{range_type}"
    if "30" in haystack and ("天" in haystack or "day" in haystack):
        return TIME_RANGE_LAST_30_DAYS
    if "三个月" in haystack or "3个月" in haystack or "3月" in haystack:
        return TIME_RANGE_LAST_3_MONTHS
    if "本月" in haystack or "当月" in haystack or range_type == "current_period":
        return TIME_RANGE_CURRENT_MONTH
    return TIME_RANGE_ALL_TIME


def _resolve_template_key(
    *,
    metric_code: str,
    dimensions: tuple[str, ...],
    time_range_kind: str,
    analysis_type: str,
    sort: dict[str, Any],
) -> str | None:
    dimension_set = set(dimensions)
    is_ranking = analysis_type == "ranking" or str(sort.get("direction")) == "desc"
    is_trend = analysis_type == "trend" or "date" in dimension_set

    if metric_code == "enrollment_count" and "campus" in dimension_set and is_ranking:
        return INTENT_CAMPUS_ENROLLMENT_RANK
    if metric_code == "enrollment_count" and not dimension_set and time_range_kind == TIME_RANGE_CURRENT_MONTH:
        return INTENT_MONTHLY_ENROLLMENT_COUNT
    if metric_code == "paid_amount" and "date" in dimension_set and time_range_kind == TIME_RANGE_LAST_30_DAYS:
        return INTENT_LAST_30_DAYS_INCOME
    if metric_code == "refund_amount" and "series" in dimension_set and is_ranking:
        return INTENT_SERIES_REFUND_AMOUNT_RANK
    if metric_code == "refund_amount" and not dimension_set and time_range_kind == TIME_RANGE_CURRENT_MONTH:
        return INTENT_MONTHLY_REFUND_AMOUNT
    if metric_code == "completion_rate" and is_trend and time_range_kind == TIME_RANGE_LAST_3_MONTHS:
        return INTENT_LAST_3_MONTH_COMPLETION_RATE
    return None
