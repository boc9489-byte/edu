"""Ask module error helpers."""

from __future__ import annotations

import re

from ..errors import AppError

_CONNECTION_STRING_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://\S+")


def unsupported_query() -> AppError:
    return AppError(400, "ASK_UNSUPPORTED_QUERY", "暂不支持该问数问题")


def sql_unsafe(reason: str | None = None) -> AppError:
    message = "问数 SQL 未通过只读校验"
    if reason:
        message = f"{message}: {reason}"
    return AppError(400, "ASK_SQL_UNSAFE", message)


unsafe_sql = sql_unsafe


def sql_execution_failed(error: Exception) -> AppError:
    error_message = _truncate_error(str(error))
    return AppError(500, "ASK_SQL_EXECUTION_FAILED", f"SQL 执行失败: {error_message}")


def _truncate_error(message: str, max_length: int = 500) -> str:
    sanitized = " ".join(_CONNECTION_STRING_RE.sub("[redacted]", message).split())
    if not sanitized:
        sanitized = "unknown error"
    return sanitized[:max_length]
