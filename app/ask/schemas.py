"""Request and response schemas for the ask MVP."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AskQueryRequest(BaseModel):
    query: str = Field(min_length=1, description="自然语言问数问题。")
    debug: bool = Field(default=True, description="是否返回 SQL 与 trace 信息。")


class AskQueryData(BaseModel):
    question: str
    matchedIntent: str
    sql: str
    result: list[dict[str, Any]]
    answer: str
    trace: dict[str, Any]
