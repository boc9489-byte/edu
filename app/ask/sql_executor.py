"""Controlled SQL execution for ask queries."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..database import fetch_all
from .errors import sql_execution_failed


def execute_select(sql: str, params: Sequence[Any]) -> list[dict[str, Any]]:
    try:
        return fetch_all(sql, tuple(params))
    except Exception as exc:
        raise sql_execution_failed(exc) from None
