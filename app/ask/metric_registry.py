"""Metric registry for rule-template ask queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    metric_code: str
    metric_name: str
    description: str
    main_table: str
    time_field: str
    aggregation: str
    default_filter: str
    supported_dimensions: tuple[str, ...]
    sql_template_key: str


METRICS: dict[str, MetricDefinition] = {
    "enrollment_count": MetricDefinition(
        metric_code="enrollment_count",
        metric_name="报名人数",
        description="指定时间范围内有效报名班次的去重学员数量。",
        main_table="student_cohort_rel",
        time_field="enroll_at",
        aggregation="COUNT(DISTINCT student_id)",
        default_filter="enroll_status IN ('active', 'completed')",
        supported_dimensions=("date", "series", "cohort", "campus", "learner_identity"),
        sql_template_key="monthly_enrollment_count",
    ),
    "paid_amount": MetricDefinition(
        metric_code="paid_amount",
        metric_name="收入金额",
        description="指定时间范围内支付成功或已部分/全部退款支付记录的支付金额。",
        main_table="payment_record",
        time_field="paid_at",
        aggregation="SUM(amount)",
        default_filter="payment_status IN ('paid', 'partial_refunded', 'refunded')",
        supported_dimensions=("date", "series", "cohort", "campus", "channel"),
        sql_template_key="last_30_days_income",
    ),
    "refund_amount": MetricDefinition(
        metric_code="refund_amount",
        metric_name="退款金额",
        description="指定时间范围内退款成功申请的已审批金额。",
        main_table="refund_request",
        time_field="refunded_at",
        aggregation="SUM(approved_amount)",
        default_filter="refund_status = 'refunded'",
        supported_dimensions=("date", "series", "cohort", "campus", "channel"),
        sql_template_key="monthly_refund_amount",
    ),
    "completion_rate": MetricDefinition(
        metric_code="completion_rate",
        metric_name="完课率",
        description="完课学员数占有效报名学员数的比例。",
        main_table="student_cohort_rel",
        time_field="enroll_at",
        aggregation="completed_count / enrolled_count",
        default_filter="enroll_status IN ('active', 'completed')",
        supported_dimensions=("date", "series", "cohort", "campus", "learner_identity"),
        sql_template_key="last_3_month_completion_rate",
    ),
    "attendance_rate": MetricDefinition(
        metric_code="attendance_rate",
        metric_name="出勤率",
        description="实际出勤人次占应出勤人次的比例。",
        main_table="session_attendance",
        time_field="created_at",
        aggregation="attended_count / expected_count",
        default_filter="attendance_status IN ('present', 'late', 'leave', 'absent')",
        supported_dimensions=("date", "series", "cohort", "campus"),
        sql_template_key="attendance_rate",
    ),
    "conversion_rate": MetricDefinition(
        metric_code="conversion_rate",
        metric_name="转化率",
        description="支付报名人数占咨询或访问人数的比例。",
        main_table="consultation_record",
        time_field="consulted_at",
        aggregation="paid_enrollment_count / consultation_count",
        default_filter="consulted_at IS NOT NULL",
        supported_dimensions=("date", "series", "cohort", "campus", "channel"),
        sql_template_key="conversion_rate",
    ),
}


def get_metric(metric_code: str) -> MetricDefinition | None:
    return METRICS.get(metric_code)


def list_metrics() -> tuple[MetricDefinition, ...]:
    return tuple(METRICS.values())
