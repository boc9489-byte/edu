"""Rule-based intent matching for the ask MVP."""

from __future__ import annotations

import re

INTENT_MONTHLY_ENROLLMENT_COUNT = "monthly_enrollment_count"
INTENT_LAST_30_DAYS_INCOME = "last_30_days_income"
INTENT_MONTHLY_REFUND_AMOUNT = "monthly_refund_amount"
INTENT_CAMPUS_ENROLLMENT_RANK = "campus_enrollment_rank"
INTENT_SERIES_REFUND_AMOUNT_RANK = "series_refund_amount_rank"
INTENT_LAST_3_MONTH_COMPLETION_RATE = "last_3_month_completion_rate"


def match_intent(query: str) -> str | None:
    text = _normalize(query)
    if "本月" in text and ("报名人数" in text or "报名数" in text):
        return INTENT_MONTHLY_ENROLLMENT_COUNT
    if ("最近30天" in text or "近30天" in text) and ("收入" in text or "营收" in text):
        return INTENT_LAST_30_DAYS_INCOME
    if "本月" in text and ("退款金额" in text or "退款额" in text):
        return INTENT_MONTHLY_REFUND_AMOUNT
    if "校区" in text and ("报名人数最多" in text or "报名最多" in text):
        return INTENT_CAMPUS_ENROLLMENT_RANK
    if "课程系列" in text and ("退款金额最高" in text or "退款最高" in text):
        return INTENT_SERIES_REFUND_AMOUNT_RANK
    if ("最近三个月" in text or "近三个月" in text) and "完课率" in text:
        return INTENT_LAST_3_MONTH_COMPLETION_RATE
    return None


def _normalize(query: str) -> str:
    return re.sub(r"[\s,，。？?！!：:；;、]+", "", query.strip())
