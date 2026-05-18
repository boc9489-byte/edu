"""Trace builders for ask query execution."""

from __future__ import annotations

from typing import Any

from .metric_registry import MetricDefinition
from .patterns import QueryPattern
from .sql_validator import SqlValidation
from .time_range_parser import TimeRange


def build_success_trace(
    *,
    metric: MetricDefinition,
    pattern: QueryPattern,
    time_range: TimeRange,
    template_key: str,
    metadata: dict[str, list[str]],
    validation: SqlValidation,
    params: list[Any],
    row_count: int,
    duration_ms: float,
) -> dict[str, Any]:
    return {
        "mode": "rule_template",
        "llm": False,
        "rag": False,
        "langGraph": False,
        "metricCode": metric.metric_code,
        "metricName": metric.metric_name,
        "dimensions": list(pattern.dimensions),
        "templateKey": template_key,
        "timeRange": time_range.as_trace(),
        "metadataTables": metadata["tables"],
        "metadataColumns": metadata["columns"],
        "sqlReadonly": validation.passed,
        "sqlValidation": validation.to_trace(),
        "sqlExecution": {
            "status": "success",
            "rowCount": row_count,
            "durationMs": round(duration_ms, 3),
        },
        "params": params,
        "rowCount": row_count,
    }
