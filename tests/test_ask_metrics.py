from __future__ import annotations

from dataclasses import fields

from app.ask.dimension_registry import get_dimension, list_dimensions
from app.ask.metric_registry import get_metric, list_metrics
from app.ask.sql_templates import get_sql_template


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

REQUIRED_METRIC_FIELDS = {
    "metric_code",
    "metric_name",
    "description",
    "main_table",
    "time_field",
    "aggregation",
    "default_filter",
    "supported_dimensions",
    "sql_template_key",
}


def test_metric_registry_contains_first_batch_metrics():
    metrics = {metric.metric_code: metric for metric in list_metrics()}
    assert set(metrics) == METRIC_CODES

    for metric_code in METRIC_CODES:
        metric = get_metric(metric_code)
        assert metric is not None
        assert metric.metric_code == metric_code
        assert metric.metric_name
        assert metric.description
        assert metric.main_table
        assert metric.time_field
        assert metric.aggregation
        assert metric.default_filter
        assert metric.supported_dimensions
        assert metric.sql_template_key


def test_metric_definition_fields_are_complete():
    field_names = {field.name for field in fields(type(get_metric("enrollment_count")))}
    assert REQUIRED_METRIC_FIELDS <= field_names


def test_dimension_registry_contains_first_batch_dimensions():
    dimensions = {dimension.dimension_code: dimension for dimension in list_dimensions()}
    assert set(dimensions) == DIMENSION_CODES

    for dimension_code in DIMENSION_CODES:
        dimension = get_dimension(dimension_code)
        assert dimension is not None
        assert dimension.dimension_code == dimension_code
        assert dimension.dimension_name
        assert dimension.description
        assert dimension.table_name
        assert dimension.field_name


def test_missing_metric_returns_none():
    assert get_metric("unknown_metric") is None


def test_unopened_metrics_do_not_have_executable_templates():
    assert get_sql_template("attendance_rate") is None
    assert get_sql_template("conversion_rate") is None
