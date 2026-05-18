"""Rule-template query service for the education ask MVP."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Any

from ..database import fetch_all
from ..utils import local_now
from .errors import unsafe_sql, unsupported_query
from .patterns import match_intent
from .sql_templates import get_template

FORBIDDEN_SQL_WORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|replace|merge)\b",
    re.IGNORECASE,
)


def answer_query(question: str) -> dict[str, Any]:
    intent = match_intent(question)
    if intent is None:
        raise unsupported_query()

    template = get_template(intent)
    sql = _normalize_sql(template.sql)
    _ensure_readonly_select(sql)
    params = template.params_factory(local_now())
    rows = [_serialize_row(row) for row in fetch_all(sql, params)]
    return {
        "question": question,
        "matchedIntent": intent,
        "sql": sql,
        "result": rows,
        "answer": template.answer_factory(rows),
        "trace": {
            "mode": "rule_template",
            "llm": False,
            "rag": False,
            "langGraph": False,
            "sqlReadonly": True,
            "params": [_serialize_value(value) for value in params],
            "rowCount": len(rows),
        },
    }


def _ensure_readonly_select(sql: str) -> None:
    stripped = sql.strip().lower()
    if not stripped.startswith("select"):
        raise unsafe_sql()
    if FORBIDDEN_SQL_WORDS.search(stripped):
        raise unsafe_sql()
    if " limit " not in f" {stripped} ":
        raise unsafe_sql()


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.split())


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: _serialize_value(value) for key, value in row.items()}


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    return value
