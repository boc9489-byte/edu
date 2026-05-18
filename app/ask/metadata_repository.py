"""MySQL repository helpers for ask metadata catalog builds."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
ASK_META_SQL_PATH = ROOT_DIR / "sql" / "ask_meta.sql"
BUILD_LOG_ERROR_MAX_LENGTH = 1000

JSON_FIELDS_BY_TABLE: dict[str, set[str]] = {
    "ask_table_info": {"important_columns", "related_metrics", "tags"},
    "ask_column_info": {"enum_values", "related_metrics"},
    "ask_metric_info": {"supported_dimensions"},
}

UPSERT_DEFINITIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "ask_table_info": (
        ("table_name",),
        (
            "display_name",
            "domain",
            "description",
            "primary_key_name",
            "important_columns",
            "related_metrics",
            "tags",
            "source_hash",
            "updated_at",
        ),
    ),
    "ask_column_info": (
        ("table_name", "column_name"),
        (
            "display_name",
            "data_type",
            "role",
            "description",
            "enum_values",
            "related_metrics",
            "source_hash",
            "updated_at",
        ),
    ),
    "ask_metric_info": (
        ("metric_code",),
        (
            "metric_name",
            "description",
            "main_table",
            "time_field",
            "aggregation",
            "default_filter",
            "supported_dimensions",
            "sql_template_key",
            "source_hash",
            "updated_at",
        ),
    ),
    "ask_dimension_info": (
        ("dimension_code",),
        (
            "dimension_name",
            "description",
            "table_name",
            "field_name",
            "groupable",
            "source_hash",
            "updated_at",
        ),
    ),
    "ask_column_metric": (
        ("table_name", "column_name", "metric_code"),
        ("relation_type",),
    ),
    "ask_table_relation": (
        ("from_table", "from_column", "to_table", "to_column"),
        ("relation_type", "description", "source_hash", "updated_at"),
    ),
}


def execute_schema(sql_path: Path = ASK_META_SQL_PATH) -> int:
    statements = split_sql_statements(sql_path.read_text(encoding="utf-8"))
    if not statements:
        return 0
    with _db_cursor(dict_cursor=False) as (_, cursor):
        for statement in statements:
            cursor.execute(statement)
    return len(statements)


def split_sql_statements(sql_text: str) -> list[str]:
    return [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip()
    ]


def upsert_metadata_rows(table_name: str, rows: Sequence[dict[str, Any]]) -> int:
    if not rows:
        return 0
    sql = build_upsert_sql(table_name, tuple(rows[0].keys()))
    params = [prepare_row_params(table_name, row) for row in rows]
    with _db_cursor(dict_cursor=False) as (_, cursor):
        affected = cursor.executemany(sql, params)
    return 0 if affected is None else int(affected)


def upsert_all_metadata(payloads: dict[str, Sequence[dict[str, Any]]]) -> int:
    total = 0
    for table_name, rows in payloads.items():
        total += upsert_metadata_rows(table_name, rows)
    return total


def build_upsert_sql(table_name: str, columns: Iterable[str]) -> str:
    column_tuple = tuple(columns)
    if table_name not in UPSERT_DEFINITIONS:
        raise ValueError(f"Unsupported metadata table: {table_name}")
    if not column_tuple:
        raise ValueError("columns cannot be empty")

    _, update_columns = UPSERT_DEFINITIONS[table_name]
    missing_update_columns = set(update_columns) - set(column_tuple)
    if missing_update_columns:
        raise ValueError(
            f"Missing upsert columns for {table_name}: {sorted(missing_update_columns)}"
        )

    quoted_columns = ", ".join(f"`{column}`" for column in column_tuple)
    placeholders = ", ".join(["%s"] * len(column_tuple))
    updates = ", ".join(
        f"`{column}` = VALUES(`{column}`)" for column in update_columns
    )
    return (
        f"INSERT INTO `{table_name}` ({quoted_columns}) "
        f"VALUES ({placeholders}) "
        f"ON DUPLICATE KEY UPDATE {updates}"
    )


def prepare_row_params(table_name: str, row: dict[str, Any]) -> tuple[Any, ...]:
    normalized = normalize_row(table_name, row)
    return tuple(normalized[column] for column in row.keys())


def normalize_row(table_name: str, row: dict[str, Any]) -> dict[str, Any]:
    json_fields = JSON_FIELDS_BY_TABLE.get(table_name, set())
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        if key in json_fields:
            normalized[key] = serialize_json_value(value)
        else:
            normalized[key] = value
    return normalized


def serialize_json_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def add_timestamps(row: dict[str, Any], now: datetime) -> dict[str, Any]:
    return {**row, "created_at": now, "updated_at": now}


def add_created_at(row: dict[str, Any], now: datetime) -> dict[str, Any]:
    return {**row, "created_at": now}


def write_build_log(
    *,
    build_id: str,
    target: str,
    status: str,
    rebuild_flag: bool,
    item_count: int,
    started_at: datetime,
    finished_at: datetime | None,
    error_message: str | None = None,
) -> None:
    params = (
        build_id,
        target,
        status,
        1 if rebuild_flag else 0,
        item_count,
        truncate_error_message(error_message),
        started_at,
        finished_at,
    )
    sql = """
        INSERT INTO ask_metadata_build_log (
            build_id,
            target,
            status,
            rebuild_flag,
            item_count,
            error_message,
            started_at,
            finished_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            item_count = VALUES(item_count),
            error_message = VALUES(error_message),
            finished_at = VALUES(finished_at)
    """
    with _db_cursor(dict_cursor=False) as (_, cursor):
        cursor.execute(sql, params)


def safe_write_build_log(**kwargs: Any) -> None:
    try:
        write_build_log(**kwargs)
    except Exception:
        return


def truncate_error_message(error_message: str | None) -> str | None:
    if error_message is None:
        return None
    return error_message[:BUILD_LOG_ERROR_MAX_LENGTH]


def _db_cursor(dict_cursor: bool = True) -> Any:
    from app.database import db_cursor

    return db_cursor(dict_cursor=dict_cursor)
