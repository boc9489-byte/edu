"""Rule-template query service for the education ask MVP."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Any

from ..database import fetch_all
from ..utils import local_now
from .dimension_registry import get_dimension
from .errors import unsafe_sql, unsupported_query
from .metric_registry import get_metric
from .patterns import match_query_pattern
from .template_renderer import render_template
from .time_range_parser import parse_time_range

FORBIDDEN_SQL_WORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|replace|merge)\b",
    re.IGNORECASE,
)


def answer_query(question: str) -> dict[str, Any]:
    pattern = match_query_pattern(question)
    if pattern is None:
        raise unsupported_query()

    metric = get_metric(pattern.metric_code)
    dimensions = [get_dimension(code) for code in pattern.dimensions]
    now = local_now()
    time_range = parse_time_range(pattern.time_range_kind, now)
    if metric is None or any(dimension is None for dimension in dimensions) or time_range is None:
        raise unsupported_query()

    rendered = render_template(pattern.template_key, time_range)
    if rendered is None:
        raise unsupported_query()

    sql = _normalize_sql(rendered.sql)
    _ensure_readonly_select(sql)
    params = rendered.params
    rows = [_serialize_row(row) for row in fetch_all(sql, params)]
    return {
        "question": question,
        "matchedIntent": pattern.intent,
        "sql": sql,
        "result": rows,
        "answer": rendered.answer_factory(rows),
        "trace": {
            "mode": "rule_template",
            "llm": False,
            "rag": False,
            "langGraph": False,
            "metricCode": metric.metric_code,
            "metricName": metric.metric_name,
            "dimensions": [dimension.dimension_code for dimension in dimensions if dimension],
            "templateKey": rendered.template_key,
            "timeRange": time_range.as_trace(),
            "sqlReadonly": True,
            "params": [_serialize_value(value) for value in params],
            "rowCount": len(rows),
        },
    }


def _ensure_readonly_select(sql: str) -> None:
    stripped = sql.strip().lower()
    if not stripped.startswith("select"):
        raise unsafe_sql()
    if FORBIDDEN_SQL_WORDS.search(stripped):
        raise unsafe_sql()
    if " limit " not in f" {stripped} ":
        raise unsafe_sql()


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.split())


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _serialize_value(value) for key, value in row.items()}


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    return value
