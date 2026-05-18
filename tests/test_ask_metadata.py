from __future__ import annotations

from app.ask.dimension_registry import list_dimensions
from app.ask.metadata_service import (
    build_trace_metadata,
    get_column_metadata,
    get_table_metadata,
    resolve_dimension_metadata,
    resolve_metric_metadata,
)
from app.ask.metric_registry import list_metrics
from app.ask.relation_catalog import find_relation
from app.ask.table_catalog import list_tables


CORE_TABLES = {
    "order",
    "order_item",
    "payment_record",
    "refund_request",
    "student_cohort_rel",
    "series",
    "series_cohort",
    "org_campus",
    "student_profile",
    "dim_learner_identity",
    "dim_channel",
    "session_attendance",
    "session_video_play",
    "session_homework_submission",
    "session_exam_submission",
}

CORE_COLUMNS = [
    ("payment_record", "payment_status"),
    ("payment_record", "amount"),
    ("payment_record", "paid_at"),
    ("refund_request", "refund_status"),
    ("refund_request", "approved_amount"),
    ("refund_request", "refunded_at"),
    ("student_cohort_rel", "enroll_status"),
    ("student_cohort_rel", "enroll_at"),
    ("student_cohort_rel", "completed_at"),
    ("series", "series_name"),
    ("series", "sale_status"),
    ("series_cohort", "cohort_name"),
    ("series_cohort", "campus_id"),
    ("org_campus", "campus_name"),
    ("student_profile", "learner_identity_id"),
    ("dim_learner_identity", "identity_name"),
    ("dim_channel", "channel_name"),
    ("session_attendance", "attendance_status"),
    ("session_attendance", "created_at"),
    ("session_video_play", "completed_flag"),
    ("session_video_play", "started_at"),
    ("session_homework_submission", "submit_status"),
    ("session_exam_submission", "attempt_status"),
]


def test_core_tables_are_queryable():
    table_names = {table.table_name for table in list_tables()}
    assert CORE_TABLES <= table_names

    for table_name in CORE_TABLES:
        table = get_table_metadata(table_name)
        assert table is not None
        assert table.table_name == table_name
        assert table.display_name
        assert table.domain
        assert table.primary_key == "id"
        assert table.important_columns
        assert table.tags


def test_core_columns_are_queryable():
    for table_name, column_name in CORE_COLUMNS:
        column = get_column_metadata(table_name, column_name)
        assert column is not None
        assert column.table_name == table_name
        assert column.column_name == column_name
        assert column.display_name
        assert column.data_type
        assert column.role
        assert column.description


def test_core_relations_exist():
    assert find_relation("payment_record", "order_id", "order", "id") is not None
    assert find_relation("refund_request", "order_item_id", "order_item", "id") is not None
    assert find_relation("order_item", "cohort_id", "series_cohort", "id") is not None
    assert find_relation("series_cohort", "series_id", "series", "id") is not None
    assert find_relation("series_cohort", "campus_id", "org_campus", "id") is not None
    assert find_relation("student_cohort_rel", "student_id", "student_profile", "id") is not None
    assert find_relation("student_profile", "learner_identity_id", "dim_learner_identity", "id") is not None
    assert find_relation("order", "order_source_channel_id", "dim_channel", "id") is not None


def test_metric_registry_references_metadata_catalog():
    for metric in list_metrics():
        metadata = resolve_metric_metadata(metric.metric_code)
        assert metadata is not None
        assert metadata["table"].table_name == metric.main_table
        assert metadata["time_column"].column_name == metric.time_field


def test_dimension_registry_references_metadata_catalog():
    for dimension in list_dimensions():
        if dimension.dimension_code == "date":
            columns = resolve_dimension_metadata(dimension.dimension_code, "paid_amount")
        else:
            columns = resolve_dimension_metadata(dimension.dimension_code, "enrollment_count")
        assert columns


def test_build_trace_metadata_returns_tables_and_columns():
    metadata = build_trace_metadata("enrollment_count", ("campus",))
    assert "student_cohort_rel" in metadata["tables"]
    assert "series_cohort" in metadata["tables"]
    assert "org_campus" in metadata["tables"]
    assert "student_cohort_rel.enroll_at" in metadata["columns"]
    assert "org_campus.campus_name" in metadata["columns"]


def test_conversion_metric_support_table_is_available():
    table = get_table_metadata("consultation_record")
    assert table is not None
    assert table.related_metrics == ("conversion_rate",)
    assert get_column_metadata("consultation_record", "consulted_at") is not None
