"""Rule-template education ask APIs."""

from __future__ import annotations

from fastapi import APIRouter, Body

from ..ask.query_service import answer_query
from ..ask.schemas import AskQueryData, AskQueryRequest
from ..response import ok

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("/query")
def ask_query(body: AskQueryRequest = Body(description="教育问数请求体。")):
    data = AskQueryData(**answer_query(body.query))
    if not body.debug:
        data.trace.clear()
    return ok(data.model_dump())
