from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.ask.llm_extractor import build_extraction_prompt
from app.main import app


def _payload(
    *,
    metric: str = "enrollment_count",
    dimensions: list[str] | None = None,
    time_text: str = "",
    analysis_type: str = "ranking",
    confidence: float = 0.92,
):
    return json.dumps(
        {
            "analysis_type": analysis_type,
            "metric_terms": [],
            "metric_code_candidates": [metric],
            "dimension_terms": [],
            "dimension_code_candidates": dimensions or [],
            "time_range": {
                "type": "relative" if time_text else "unknown",
                "text": time_text,
                "grain": "day" if "30" in time_text else "none",
            },
            "filters": [],
            "sort": {"by": "metric", "direction": "desc"},
            "limit": 10,
            "field_terms": [],
            "value_terms": [],
            "confidence": confidence,
        },
        ensure_ascii=False,
    )


def test_rule_match_does_not_call_llm(monkeypatch):
    monkeypatch.setenv("ASK_LLM_EXTRACT_ENABLED", "true")

    def fail_call(_prompt):
        raise AssertionError("LLM should not be called for rule matches")

    monkeypatch.setattr("app.ask.llm_extractor.call_llm", fail_call)

    with TestClient(app) as client:
        response = client.post("/ask/query", json={"query": "本月报名人数是多少？"})

    assert response.status_code == 200
    trace = response.json()["data"]["trace"]
    assert trace["understandingMode"] == "rule"
    assert trace["llmExtraction"] is None


def test_rule_miss_with_llm_disabled_returns_unsupported(monkeypatch):
    monkeypatch.setenv("ASK_LLM_EXTRACT_ENABLED", "false")

    with TestClient(app) as client:
        response = client.post("/ask/query", json={"query": "请按校区统计报名冠军"})

    assert response.status_code == 400
    assert response.json()["code"] == "ASK_UNSUPPORTED_QUERY"


def test_llm_fallback_links_enrollment_campus_rank(monkeypatch):
    monkeypatch.setenv("ASK_LLM_EXTRACT_ENABLED", "true")
    monkeypatch.setattr(
        "app.ask.llm_extractor.call_llm",
        lambda _prompt: _payload(dimensions=["campus"]),
    )

    with TestClient(app) as client:
        response = client.post("/ask/query", json={"query": "帮我按校区看报名冠军"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["matchedIntent"] == "campus_enrollment_rank"
    assert data["trace"]["understandingMode"] == "llm"
    assert data["trace"]["llmExtraction"]["metricCodeCandidates"] == ["enrollment_count"]
    assert data["trace"]["semanticLinking"]["templateKey"] == "campus_enrollment_rank"


def test_llm_fallback_links_paid_amount_last_30_days(monkeypatch):
    monkeypatch.setenv("ASK_LLM_EXTRACT_ENABLED", "true")
    monkeypatch.setattr(
        "app.ask.llm_extractor.call_llm",
        lambda _prompt: _payload(
            metric="paid_amount",
            dimensions=["date"],
            time_text="最近30天",
            analysis_type="trend",
        ),
    )

    with TestClient(app) as client:
        response = client.post("/ask/query", json={"query": "近一个月每天营收趋势"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["matchedIntent"] == "last_30_days_income"
    assert data["trace"]["understandingMode"] == "llm"
    assert data["trace"]["semanticLinking"]["templateKey"] == "last_30_days_income"


def test_llm_fallback_rejects_invalid_metric(monkeypatch):
    monkeypatch.setenv("ASK_LLM_EXTRACT_ENABLED", "true")
    monkeypatch.setattr(
        "app.ask.llm_extractor.call_llm",
        lambda _prompt: _payload(metric="made_up_metric", dimensions=["campus"]),
    )

    with TestClient(app) as client:
        response = client.post("/ask/query", json={"query": "帮我看看神秘指标"})

    assert response.status_code == 400
    assert response.json()["code"] == "ASK_UNSUPPORTED_QUERY"


def test_llm_fallback_rejects_low_confidence(monkeypatch):
    monkeypatch.setenv("ASK_LLM_EXTRACT_ENABLED", "true")
    monkeypatch.setattr(
        "app.ask.llm_extractor.call_llm",
        lambda _prompt: _payload(dimensions=["campus"], confidence=0.2),
    )

    with TestClient(app) as client:
        response = client.post("/ask/query", json={"query": "这个问题有点含糊"})

    assert response.status_code == 400
    assert response.json()["code"] == "ASK_UNSUPPORTED_QUERY"


def test_llm_fallback_rejects_non_json(monkeypatch):
    monkeypatch.setenv("ASK_LLM_EXTRACT_ENABLED", "true")
    monkeypatch.setattr("app.ask.llm_extractor.call_llm", lambda _prompt: "不是 JSON")

    with TestClient(app) as client:
        response = client.post("/ask/query", json={"query": "随便分析一下"})

    assert response.status_code == 400
    assert response.json()["code"] == "ASK_UNSUPPORTED_QUERY"


def test_prompt_injects_runtime_metric_and_dimension_lists():
    prompt = build_extraction_prompt("最近30天收入如何？")

    assert "运行时允许的指标" in prompt
    assert "paid_amount" in prompt
    assert "运行时允许的维度" in prompt
    assert "campus" in prompt
    assert "不要生成 SQL" in prompt
