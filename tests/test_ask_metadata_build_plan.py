from __future__ import annotations

from app.ask.metadata_builders import (
    build_column_info_rows,
    build_column_metric_rows,
    build_dimension_info_rows,
    build_metric_info_rows,
    build_table_info_rows,
    build_table_relation_rows,
    stable_source_hash,
)


METRIC_CODES = {
    "enrollment_count",
    "paid_amount",
    "refund_amount",
    "completion_rate",
    "attendance_rate",
    "conversion_rate",
}

DIMENSION_CODES = {
    "date",
    "series",
    "cohort",
    "campus",
    "learner_identity",
    "channel",
}


def test_build_table_info_rows_from_static_catalog():
    rows = build_table_info_rows()

    assert rows
    assert all(row["source_hash"] for row in rows)
    assert all(row["table_name"] for row in rows)
    assert all(row["primary_key_name"] for row in rows)
    assert {row["table_name"] for row in rows} >= {"order", "payment_record", "series"}


def test_build_column_info_rows_from_static_catalog():
    rows = build_column_info_rows()

    assert rows
    assert all(row["source_hash"] for row in rows)
    assert all(row["table_name"] for row in rows)
    assert all(row["column_name"] for row in rows)
    assert ("payment_record", "amount") in {
        (row["table_name"], row["column_name"]) for row in rows
    }


def test_build_metric_info_rows_contains_first_batch_metrics():
    rows = build_metric_info_rows()

    assert {row["metric_code"] for row in rows} == METRIC_CODES
    assert all(row["source_hash"] for row in rows)
    assert all(row["main_table"] for row in rows)
    assert all(row["time_field"] for row in rows)


def test_build_dimension_info_rows_contains_first_batch_dimensions():
    rows = build_dimension_info_rows()

    assert {row["dimension_code"] for row in rows} == DIMENSION_CODES
    assert all(row["source_hash"] for row in rows)
    assert all(row["table_name"] for row in rows)
    assert all(row["field_name"] for row in rows)


def test_build_table_relation_rows_from_static_catalog():
    rows = build_table_relation_rows()

    assert rows
    assert all(row["source_hash"] for row in rows)
    assert all(row["from_table"] for row in rows)
    assert all(row["from_column"] for row in rows)
    assert all(row["to_table"] for row in rows)
    assert all(row["to_column"] for row in rows)


def test_stable_source_hash_is_deterministic_and_ignores_existing_hash():
    left = {"table_name": "series", "tags": ["course", "series"]}
    right = {"tags": ["course", "series"], "table_name": "series"}
    with_hash = {**left, "source_hash": "old"}

    assert stable_source_hash(left) == stable_source_hash(right)
    assert stable_source_hash(left) == stable_source_hash(with_hash)
    assert len(stable_source_hash(left)) == 64


def test_column_metric_rows_are_generated_from_related_metrics():
    rows = build_column_metric_rows()

    assert rows
    assert all(row["table_name"] for row in rows)
    assert all(row["column_name"] for row in rows)
    assert all(row["metric_code"] for row in rows)
    assert all(row["relation_type"] == "related" for row in rows)
    assert {
        ("payment_record", "amount", "paid_amount"),
        ("refund_request", "approved_amount", "refund_amount"),
    } <= {
        (row["table_name"], row["column_name"], row["metric_code"]) for row in rows
    }
