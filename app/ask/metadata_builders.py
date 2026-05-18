"""Build MySQL metadata row payloads from the static ask catalog."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .column_catalog import list_columns
from .dimension_registry import list_dimensions
from .metric_registry import list_metrics
from .relation_catalog import list_relations
from .table_catalog import list_tables


def build_table_info_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for table in list_tables():
        row = {
            "table_name": table.table_name,
            "display_name": table.display_name,
            "domain": table.domain,
            "description": table.description,
            "primary_key_name": table.primary_key,
            "important_columns": list(table.important_columns),
            "related_metrics": list(table.related_metrics),
            "tags": list(table.tags),
        }
        rows.append(_with_source_hash(row))
    return rows


def build_column_info_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for column in list_columns():
        row = {
            "table_name": column.table_name,
            "column_name": column.column_name,
            "display_name": column.display_name,
            "data_type": column.data_type,
            "role": column.role,
            "description": column.description,
            "enum_values": list(column.enum_values),
            "related_metrics": list(column.related_metrics),
        }
        rows.append(_with_source_hash(row))
    return rows


def build_metric_info_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in list_metrics():
        row = {
            "metric_code": metric.metric_code,
            "metric_name": metric.metric_name,
            "description": metric.description,
            "main_table": metric.main_table,
            "time_field": metric.time_field,
            "aggregation": metric.aggregation,
            "default_filter": metric.default_filter,
            "supported_dimensions": list(metric.supported_dimensions),
            "sql_template_key": metric.sql_template_key,
        }
        rows.append(_with_source_hash(row))
    return rows


def build_dimension_info_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dimension in list_dimensions():
        row = {
            "dimension_code": dimension.dimension_code,
            "dimension_name": dimension.dimension_name,
            "description": dimension.description,
            "table_name": dimension.table_name,
            "field_name": dimension.field_name,
            "groupable": 1 if dimension.groupable else 0,
        }
        rows.append(_with_source_hash(row))
    return rows


def build_column_metric_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for column in list_columns():
        for metric_code in column.related_metrics:
            rows.append(
                {
                    "table_name": column.table_name,
                    "column_name": column.column_name,
                    "metric_code": metric_code,
                    "relation_type": "related",
                }
            )
    return rows


def build_table_relation_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in list_relations():
        row = {
            "from_table": relation.from_table,
            "from_column": relation.from_column,
            "to_table": relation.to_table,
            "to_column": relation.to_column,
            "relation_type": relation.relation_type,
            "description": relation.description,
        }
        rows.append(_with_source_hash(row))
    return rows


def stable_source_hash(payload: dict[str, Any]) -> str:
    normalized = {
        key: value for key, value in payload.items() if key != "source_hash"
    }
    serialized = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _with_source_hash(row: dict[str, Any]) -> dict[str, Any]:
    return {**row, "source_hash": stable_source_hash(row)}
