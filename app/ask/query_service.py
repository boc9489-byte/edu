"""Rule-template query service for the education ask MVP."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from time import perf_counter
from typing import Any

from ..utils import local_now
from .dimension_registry import get_dimension
from .errors import sql_unsafe, unsupported_query
from .llm_extractor import extract_with_llm, is_llm_extract_enabled
from .metadata_service import build_trace_metadata
from .metric_registry import get_metric
from .patterns import match_query_pattern
from .semantic_linker import link_extraction
from .sql_executor import execute_select
from .sql_validator import validate_sql
from .template_renderer import render_template
from .trace import build_success_trace
from .time_range_parser import parse_time_range


def answer_query(question: str) -> dict[str, Any]:
    pattern = match_query_pattern(question)
    understanding_mode = "rule"
    llm_extraction_trace = None
    semantic_linking_trace = None
    if pattern is None:
        if not is_llm_extract_enabled():
            raise unsupported_query()
        extraction = extract_with_llm(question)
        if extraction is None:
            raise unsupported_query()
        link_result = link_extraction(extraction)
        if link_result is None:
            raise unsupported_query()
        pattern = link_result.pattern
        understanding_mode = "llm"
        llm_extraction_trace = extraction.to_trace()
        semantic_linking_trace = link_result.to_trace()
    else:
        semantic_linking_trace = {
            "matched": True,
            "source": "rule",
            "intent": pattern.intent,
            "templateKey": pattern.template_key,
        }

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
    params = rendered.params
    validation = validate_sql(sql, params)
    if not validation.passed:
        raise sql_unsafe(validation.reason)

    started_at = perf_counter()
    rows = [_serialize_row(row) for row in execute_select(sql, params)]
    duration_ms = (perf_counter() - started_at) * 1000
    trace_metadata = build_trace_metadata(metric.metric_code, pattern.dimensions)
    row_count = len(rows)
    return {
        "question": question,
        "matchedIntent": pattern.intent,
        "sql": sql,
        "result": rows,
        "answer": rendered.answer_factory(rows),
        "trace": build_success_trace(
            metric=metric,
            pattern=pattern,
            time_range=time_range,
            template_key=rendered.template_key,
            metadata=trace_metadata,
            validation=validation,
            params=[_serialize_value(value) for value in params],
            row_count=row_count,
            duration_ms=duration_ms,
            understanding_mode=understanding_mode,
            llm_extraction=llm_extraction_trace,
            semantic_linking=semantic_linking_trace,
        ),
    }


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
