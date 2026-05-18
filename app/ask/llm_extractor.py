"""LLM semantic extraction fallback for ask queries.

The extractor only asks for structured understanding. It never asks an LLM to
produce SQL, and the actual LLM call is deliberately isolated for tests to mock.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Callable

from .dimension_registry import list_dimensions
from .metric_registry import list_metrics

ASK_LLM_EXTRACT_ENABLED = "ASK_LLM_EXTRACT_ENABLED"
MIN_CONFIDENCE = 0.7
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "llm_prompts_chines.prompt"


@dataclass(frozen=True)
class LLMExtraction:
    analysis_type: str
    metric_terms: tuple[str, ...]
    metric_code_candidates: tuple[str, ...]
    dimension_terms: tuple[str, ...]
    dimension_code_candidates: tuple[str, ...]
    time_range: dict[str, Any]
    filters: tuple[dict[str, Any], ...]
    sort: dict[str, Any]
    limit: int | None
    field_terms: tuple[str, ...]
    value_terms: tuple[str, ...]
    confidence: float

    def to_trace(self) -> dict[str, Any]:
        return {
            "analysisType": self.analysis_type,
            "metricTerms": list(self.metric_terms),
            "metricCodeCandidates": list(self.metric_code_candidates),
            "dimensionTerms": list(self.dimension_terms),
            "dimensionCodeCandidates": list(self.dimension_code_candidates),
            "timeRange": self.time_range,
            "filters": list(self.filters),
            "sort": self.sort,
            "limit": self.limit,
            "fieldTerms": list(self.field_terms),
            "valueTerms": list(self.value_terms),
            "confidence": self.confidence,
        }


def is_llm_extract_enabled() -> bool:
    value = os.getenv(ASK_LLM_EXTRACT_ENABLED, "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def extract_with_llm(
    question: str,
    llm_call: Callable[[str], str] | None = None,
) -> LLMExtraction | None:
    prompt = build_extraction_prompt(question)
    raw = (llm_call or call_llm)(prompt)
    payload = _parse_json_object(raw)
    if payload is None:
        return None

    confidence = _as_float(payload.get("confidence"))
    if confidence < MIN_CONFIDENCE:
        return None

    return LLMExtraction(
        analysis_type=_as_text(payload.get("analysis_type")) or "unknown",
        metric_terms=_as_text_tuple(payload.get("metric_terms")),
        metric_code_candidates=_as_text_tuple(payload.get("metric_code_candidates")),
        dimension_terms=_as_text_tuple(payload.get("dimension_terms")),
        dimension_code_candidates=_as_text_tuple(payload.get("dimension_code_candidates")),
        time_range=_as_dict(payload.get("time_range")),
        filters=tuple(item for item in _as_list(payload.get("filters")) if isinstance(item, dict)),
        sort=_as_dict(payload.get("sort")),
        limit=_as_int_or_none(payload.get("limit")),
        field_terms=_as_text_tuple(payload.get("field_terms")),
        value_terms=_as_text_tuple(payload.get("value_terms")),
        confidence=confidence,
    )


def build_extraction_prompt(question: str) -> str:
    base_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    metric_lines = "\n".join(
        f"- {metric.metric_code}：{metric.metric_name}" for metric in list_metrics()
    )
    dimension_lines = "\n".join(
        f"- {dimension.dimension_code}：{dimension.dimension_name}"
        for dimension in list_dimensions()
    )
    return (
        f"{base_prompt}\n\n"
        f"运行时允许的指标：\n{metric_lines}\n\n"
        f"运行时允许的维度：\n{dimension_lines}\n\n"
        f"用户问题：{question}\n"
    )


def call_llm(_prompt: str) -> str:
    raise RuntimeError("LLM extractor is not configured")


def _parse_json_object(raw: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw.strip())
    except (json.JSONDecodeError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _as_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_text_tuple(value: Any) -> tuple[str, ...]:
    return tuple(item for item in _as_list(value) if isinstance(item, str))


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_float(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _as_int_or_none(value: Any) -> int | None:
    return value if isinstance(value, int) else None
