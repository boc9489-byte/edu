"""Ask module error helpers."""

from __future__ import annotations

from ..errors import AppError


def unsupported_query() -> AppError:
    return AppError(400, "ASK_UNSUPPORTED_QUERY", "暂不支持该问数问题")


def unsafe_sql() -> AppError:
    return AppError(400, "ASK_UNSAFE_SQL", "问数 SQL 未通过只读校验")
