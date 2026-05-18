from __future__ import annotations

from datetime import datetime

from app.ask.metadata_repository import (
    add_created_at,
    add_timestamps,
    build_upsert_sql,
    normalize_row,
    prepare_row_params,
    serialize_json_value,
    split_sql_statements,
    truncate_error_message,
)


def test_build_upsert_sql_for_metric_info():
    columns = (
        "metric_code",
        "metric_name",
        "description",
        "main_table",
        "time_field",
        "aggregation",
        "default_filter",
        "supported_dimensions",
        "sql_template_key",
        "source_hash",
        "created_at",
        "updated_at",
    )

    sql = build_upsert_sql("ask_metric_info", columns)

    assert sql.startswith("INSERT INTO `ask_metric_info`")
    assert "`metric_code`" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert "`metric_name` = VALUES(`metric_name`)" in sql
    assert "`created_at` = VALUES(`created_at`)" not in sql


def test_build_upsert_sql_rejects_unknown_table():
    try:
        build_upsert_sql("unknown_table", ("id",))
    except ValueError as exc:
        assert "Unsupported metadata table" in str(exc)
    else:
        raise AssertionError("unknown metadata table should fail")


def test_json_fields_are_serialized_stably():
    value = ["paid_amount", "refund_amount"]

    assert serialize_json_value(value) == '["paid_amount","refund_amount"]'

    row = {
        "table_name": "series",
        "important_columns": ["id", "series_name"],
        "related_metrics": value,
        "tags": ["course"],
    }
    normalized = normalize_row("ask_table_info", row)
    assert normalized["important_columns"] == '["id","series_name"]'
    assert normalized["related_metrics"] == '["paid_amount","refund_amount"]'
    assert normalized["tags"] == '["course"]'


def test_prepare_row_params_preserves_column_order_and_serializes_json():
    row = {
        "metric_code": "paid_amount",
        "supported_dimensions": ["date", "channel"],
        "metric_name": "收入金额",
    }

    params = prepare_row_params("ask_metric_info", row)

    assert params == ("paid_amount", '["date","channel"]', "收入金额")


def test_split_sql_statements_handles_multiple_statements():
    sql = """
    SET NAMES utf8mb4;
    CREATE TABLE IF NOT EXISTS ask_table_info (id BIGINT);

    CREATE TABLE IF NOT EXISTS ask_metric_info (id BIGINT);
    """

    statements = split_sql_statements(sql)

    assert statements == [
        "SET NAMES utf8mb4",
        "CREATE TABLE IF NOT EXISTS ask_table_info (id BIGINT)",
        "CREATE TABLE IF NOT EXISTS ask_metric_info (id BIGINT)",
    ]


def test_timestamp_helpers_add_expected_fields():
    now = datetime(2026, 5, 19, 8, 0, 0)

    assert add_timestamps({"id": 1}, now) == {
        "id": 1,
        "created_at": now,
        "updated_at": now,
    }
    assert add_created_at({"id": 1}, now) == {"id": 1, "created_at": now}


def test_truncate_error_message_limits_length():
    assert truncate_error_message(None) is None
    assert truncate_error_message("x" * 1200) == "x" * 1000
