"""SQL templates for the rule-template education analytics MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Callable

from .patterns import (
    INTENT_CAMPUS_ENROLLMENT_RANK,
    INTENT_LAST_30_DAYS_INCOME,
    INTENT_LAST_3_MONTH_COMPLETION_RATE,
    INTENT_MONTHLY_ENROLLMENT_COUNT,
    INTENT_MONTHLY_REFUND_AMOUNT,
    INTENT_SERIES_REFUND_AMOUNT_RANK,
)

DEFAULT_RANK_LIMIT = 10


@dataclass(frozen=True)
class SQLTemplate:
    intent: str
    sql: str
    params_factory: Callable[[datetime], tuple[Any, ...]]
    answer_factory: Callable[[list[dict[str, Any]]], str]


def get_template(intent: str) -> SQLTemplate:
    return SQL_TEMPLATES[intent]


def _month_range(now: datetime) -> tuple[datetime, datetime]:
    start = datetime(now.year, now.month, 1)
    return start, _add_months(start, 1)


def _last_30_days_range(now: datetime) -> tuple[datetime, datetime]:
    return now - timedelta(days=30), now


def _last_3_months_range(now: datetime) -> tuple[datetime, datetime]:
    this_month = datetime(now.year, now.month, 1)
    return _add_months(this_month, -2), _add_months(this_month, 1)


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    return value.replace(year=year, month=month)


def _as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _answer_monthly_enrollment(rows: list[dict[str, Any]]) -> str:
    count = int((rows[0] if rows else {}).get("enrollment_count") or 0)
    return f"本月报名人数为 {count} 人。"


def _answer_last_30_days_income(rows: list[dict[str, Any]]) -> str:
    total = sum(_as_decimal(row.get("paid_amount")) for row in rows)
    return f"最近30天收入合计为 {float(total):.2f} 元。"


def _answer_monthly_refund(rows: list[dict[str, Any]]) -> str:
    amount = _as_decimal((rows[0] if rows else {}).get("refund_amount"))
    return f"本月退款金额为 {float(amount):.2f} 元。"


def _answer_campus_rank(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "暂无校区报名数据。"
    top = rows[0]
    return f"报名人数最多的校区是 {top['campus_name']}，报名人数为 {top['enrollment_count']} 人。"


def _answer_series_refund_rank(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "暂无课程系列退款数据。"
    top = rows[0]
    amount = _as_decimal(top.get("refund_amount"))
    return f"退款金额最高的课程系列是 {top['series_name']}，退款金额为 {float(amount):.2f} 元。"


def _answer_completion_rate(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "最近三个月暂无完课率数据。"
    latest = rows[-1]
    rate = _as_decimal(latest.get("completion_rate")) * Decimal("100")
    return f"最近三个月完课率已返回趋势数据，最近月份完课率为 {float(rate):.2f}%。"


SQL_TEMPLATES: dict[str, SQLTemplate] = {
    INTENT_MONTHLY_ENROLLMENT_COUNT: SQLTemplate(
        intent=INTENT_MONTHLY_ENROLLMENT_COUNT,
        sql="""
            SELECT COUNT(DISTINCT student_id) AS enrollment_count
            FROM student_cohort_rel
            WHERE enroll_status IN ('active', 'completed')
              AND enroll_at >= %s
              AND enroll_at < %s
            LIMIT 1
        """,
        params_factory=_month_range,
        answer_factory=_answer_monthly_enrollment,
    ),
    INTENT_LAST_30_DAYS_INCOME: SQLTemplate(
        intent=INTENT_LAST_30_DAYS_INCOME,
        sql="""
            SELECT DATE(paid_at) AS stat_date,
                   COALESCE(SUM(amount), 0) AS paid_amount
            FROM payment_record
            WHERE payment_status IN ('paid', 'partial_refunded', 'refunded')
              AND paid_at >= %s
              AND paid_at < %s
            GROUP BY DATE(paid_at)
            ORDER BY stat_date ASC
            LIMIT 30
        """,
        params_factory=_last_30_days_range,
        answer_factory=_answer_last_30_days_income,
    ),
    INTENT_MONTHLY_REFUND_AMOUNT: SQLTemplate(
        intent=INTENT_MONTHLY_REFUND_AMOUNT,
        sql="""
            SELECT COALESCE(SUM(approved_amount), 0) AS refund_amount
            FROM refund_request
            WHERE refund_status = 'refunded'
              AND refunded_at >= %s
              AND refunded_at < %s
            LIMIT 1
        """,
        params_factory=_month_range,
        answer_factory=_answer_monthly_refund,
    ),
    INTENT_CAMPUS_ENROLLMENT_RANK: SQLTemplate(
        intent=INTENT_CAMPUS_ENROLLMENT_RANK,
        sql="""
            SELECT COALESCE(campus.campus_name, '未分配校区') AS campus_name,
                   COUNT(DISTINCT rel.student_id) AS enrollment_count
            FROM student_cohort_rel AS rel
            JOIN series_cohort AS cohort ON cohort.id = rel.cohort_id
            LEFT JOIN org_campus AS campus ON campus.id = cohort.campus_id
            WHERE rel.enroll_status IN ('active', 'completed')
            GROUP BY COALESCE(campus.campus_name, '未分配校区')
            ORDER BY enrollment_count DESC, campus_name ASC
            LIMIT %s
        """,
        params_factory=lambda _: (DEFAULT_RANK_LIMIT,),
        answer_factory=_answer_campus_rank,
    ),
    INTENT_SERIES_REFUND_AMOUNT_RANK: SQLTemplate(
        intent=INTENT_SERIES_REFUND_AMOUNT_RANK,
        sql="""
            SELECT series.series_name,
                   COALESCE(SUM(refund.approved_amount), 0) AS refund_amount
            FROM refund_request AS refund
            JOIN order_item AS item ON item.id = refund.order_item_id
            JOIN series_cohort AS cohort ON cohort.id = item.cohort_id
            JOIN series ON series.id = cohort.series_id
            WHERE refund.refund_status = 'refunded'
            GROUP BY series.id, series.series_name
            ORDER BY refund_amount DESC, series.series_name ASC
            LIMIT %s
        """,
        params_factory=lambda _: (DEFAULT_RANK_LIMIT,),
        answer_factory=_answer_series_refund_rank,
    ),
    INTENT_LAST_3_MONTH_COMPLETION_RATE: SQLTemplate(
        intent=INTENT_LAST_3_MONTH_COMPLETION_RATE,
        sql="""
            SELECT DATE_FORMAT(enroll_at, '%%Y-%%m') AS stat_month,
                   COUNT(DISTINCT CASE
                       WHEN enroll_status = 'completed' THEN student_id
                   END) AS completed_count,
                   COUNT(DISTINCT CASE
                       WHEN enroll_status IN ('active', 'completed') THEN student_id
                   END) AS enrolled_count,
                   COALESCE(
                       ROUND(
                           COUNT(DISTINCT CASE
                               WHEN enroll_status = 'completed' THEN student_id
                           END) / NULLIF(COUNT(DISTINCT CASE
                               WHEN enroll_status IN ('active', 'completed') THEN student_id
                           END), 0),
                           4
                       ),
                       0
                   ) AS completion_rate
            FROM student_cohort_rel
            WHERE enroll_status IN ('active', 'completed')
              AND enroll_at >= %s
              AND enroll_at < %s
            GROUP BY DATE_FORMAT(enroll_at, '%%Y-%%m')
            ORDER BY stat_month ASC
            LIMIT 3
        """,
        params_factory=_last_3_months_range,
        answer_factory=_answer_completion_rate,
    ),
}
