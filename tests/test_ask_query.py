from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.main import app

QUESTIONS = [
    ("本月报名人数是多少？", "monthly_enrollment_count"),
    ("最近30天收入如何？", "last_30_days_income"),
    ("本月退款金额是多少？", "monthly_refund_amount"),
    ("哪个校区报名人数最多？", "campus_enrollment_rank"),
    ("哪个课程系列退款金额最高？", "series_refund_amount_rank"),
    ("最近三个月完课率变化情况？", "last_3_month_completion_rate"),
]

FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate)\b",
    re.IGNORECASE,
)


def test_ask_query_supported_questions():
    with TestClient(app) as client:
        for question, intent in QUESTIONS:
            response = client.post("/ask/query", json={"query": question})
            assert response.status_code == 200
            payload = response.json()
            assert payload["code"] == 0
            data = payload["data"]
            assert data["question"] == question
            assert data["matchedIntent"] == intent
            assert data["sql"].strip().lower().startswith("select")
            assert " limit " in f" {data['sql'].lower()} "
            assert not FORBIDDEN_SQL.search(data["sql"])
            assert isinstance(data["result"], list)
            assert data["answer"]
            assert data["trace"]["mode"] == "rule_template"
            assert data["trace"]["sqlReadonly"] is True
            assert data["trace"]["llm"] is False
            assert data["trace"]["rag"] is False
            assert data["trace"]["langGraph"] is False


def test_ask_query_unsupported_question():
    with TestClient(app) as client:
        response = client.post("/ask/query", json={"query": "帮我删除所有订单"})
    assert response.status_code == 400
    assert response.json()["code"] == "ASK_UNSUPPORTED_QUERY"
