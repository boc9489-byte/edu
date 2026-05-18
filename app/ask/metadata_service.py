"""Lookup helpers for the static ask metadata catalog."""

from __future__ import annotations

from typing import Any

from .column_catalog import ColumnMetadata, get_column
from .dimension_registry import get_dimension
from .metric_registry import get_metric
from .table_catalog import TableMetadata, get_table

DIMENSION_TRACE_COLUMNS: dict[tuple[str, str], tuple[tuple[str, str], ...]] = {
    ("enrollment_count", "campus"): (
        ("student_cohort_rel", "cohort_id"),
        ("series_cohort", "id"),
        ("series_cohort", "campus_id"),
        ("org_campus", "id"),
        ("org_campus", "campus_name"),
    ),
    ("refund_amount", "series"): (
        ("refund_request", "order_item_id"),
        ("order_item", "id"),
        ("order_item", "cohort_id"),
        ("series_cohort", "id"),
        ("series_cohort", "series_id"),
        ("series", "id"),
        ("series", "series_name"),
    ),
    ("enrollment_count", "learner_identity"): (
        ("student_cohort_rel", "student_id"),
        ("student_profile", "id"),
        ("student_profile", "learner_identity_id"),
        ("dim_learner_identity", "id"),
        ("dim_learner_identity", "identity_name"),
    ),
    ("completion_rate", "learner_identity"): (
        ("student_cohort_rel", "student_id"),
        ("student_profile", "id"),
        ("student_profile", "learner_identity_id"),
        ("dim_learner_identity", "id"),
        ("dim_learner_identity", "identity_name"),
    ),
    ("paid_amount", "channel"): (
        ("payment_record", "order_id"),
        ("order", "id"),
        ("order", "order_source_channel_id"),
        ("dim_channel", "id"),
        ("dim_channel", "channel_name"),
    ),
    ("refund_amount", "channel"): (
        ("refund_request", "order_id"),
        ("order", "id"),
        ("order", "order_source_channel_id"),
        ("dim_channel", "id"),
        ("dim_channel", "channel_name"),
    ),
    ("conversion_rate", "channel"): (
        ("consultation_record", "source_channel_id"),
        ("dim_channel", "id"),
        ("dim_channel", "channel_name"),
    ),
}


def get_table_metadata(table_name: str) -> TableMetadata | None:
    return get_table(table_name)


def get_column_metadata(table_name: str, column_name: str) -> ColumnMetadata | None:
    return get_column(table_name, column_name)


def resolve_metric_metadata(metric_code: str) -> dict[str, Any] | None:
    metric = get_metric(metric_code)
    if metric is None:
        return None
    table = get_table(metric.main_table)
    time_column = get_column(metric.main_table, metric.time_field)
    if table is None or time_column is None:
        return None
    related_columns = tuple(
        column
        for column in _metric_columns(metric_code)
        if column.table_name == metric.main_table or metric_code in column.related_metrics
    )
    return {
        "metric": metric,
        "table": table,
        "time_column": time_column,
        "columns": related_columns,
    }


def resolve_dimension_metadata(
    dimension_code: str,
    metric_code: str | None = None,
) -> tuple[ColumnMetadata, ...]:
    if dimension_code == "date":
        if metric_code is None:
            return ()
        metric = get_metric(metric_code)
        if metric is None:
            return ()
        time_column = get_column(metric.main_table, metric.time_field)
        return (time_column,) if time_column else ()

    bridge_columns = _bridge_columns(metric_code, dimension_code)
    if bridge_columns:
        return bridge_columns

    dimension = get_dimension(dimension_code)
    if dimension is None:
        return ()
    column = get_column(dimension.table_name, dimension.field_name)
    return (column,) if column else ()


def build_trace_metadata(metric_code: str, dimension_codes: tuple[str, ...]) -> dict[str, list[str]]:
    tables: set[str] = set()
    columns: set[str] = set()

    metric_metadata = resolve_metric_metadata(metric_code)
    if metric_metadata:
        table = metric_metadata["table"]
        time_column = metric_metadata["time_column"]
        tables.add(table.table_name)
        columns.add(_column_ref(time_column))
        for column in metric_metadata["columns"]:
            tables.add(column.table_name)
            columns.add(_column_ref(column))

    for dimension_code in dimension_codes:
        for column in resolve_dimension_metadata(dimension_code, metric_code):
            tables.add(column.table_name)
            columns.add(_column_ref(column))

    return {
        "tables": sorted(tables),
        "columns": sorted(columns),
    }


def _metric_columns(metric_code: str) -> tuple[ColumnMetadata, ...]:
    from .column_catalog import list_columns

    return tuple(column for column in list_columns() if metric_code in column.related_metrics)


def _bridge_columns(metric_code: str | None, dimension_code: str) -> tuple[ColumnMetadata, ...]:
    if metric_code is None:
        return ()
    refs = DIMENSION_TRACE_COLUMNS.get((metric_code, dimension_code), ())
    columns = [get_column(table_name, column_name) for table_name, column_name in refs]
    return tuple(column for column in columns if column is not None)


def _column_ref(column: ColumnMetadata) -> str:
    return f"{column.table_name}.{column.column_name}"
