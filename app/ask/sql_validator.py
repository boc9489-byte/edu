"""Static SQL safety validation for the ask query pipeline.

The validator runs on SQL produced by the registered rule templates and acts as
a guardrail in case future templates or NL2SQL stages introduce unsafe text.

The validator never raises: it always returns a structured ``SqlValidation``
result so that callers can decide how to surface failures (typically by raising
``errors.sql_unsafe(reason)``).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

MAX_LIMIT = 1000

# Tables that ask SQL is allowed to read from. The list mirrors the tables
# referenced by the current six rule templates plus the joins they perform.
ALLOWED_TABLES: frozenset[str] = frozenset(
    {
        "student_cohort_rel",
        "payment_record",
        "refund_request",
        "series_cohort",
        "series",
        "order_item",
        "org_campus",
    }
)

# Reserved words that imply mutation or privilege change. Matched outside of
# string literals.
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|truncate|create|replace|merge"
    r"|grant|revoke|rename|lock|unlock|call|set"
    r")\b",
    re.IGNORECASE,
)

# Schemas / namespaces that may expose server metadata or credentials.
_DANGEROUS_SCHEMAS = re.compile(
    r"\b(information_schema|performance_schema|sys|mysql)\s*\.",
    re.IGNORECASE,
)

# Functions that can exfiltrate data, stall the server, or read host info.
_DANGEROUS_FUNCTIONS = re.compile(
    r"\b(load_file|outfile|dumpfile|sleep|benchmark|user|database|version)\s*\(",
    re.IGNORECASE,
)

# Identifier directly following FROM / JOIN. Sub-queries open with "(" instead
# of an identifier and are excluded by the character class.
_TABLE_REFERENCE_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    re.IGNORECASE,
)

# Tail LIMIT clause; accepts an integer literal or the parameter placeholder
# ``%s``. ``OFFSET`` is optional and ignored for safety purposes.
_LIMIT_RE = re.compile(
    r"\bLIMIT\s+(\d+|%s)(?:\s+OFFSET\s+\d+)?\s*$",
    re.IGNORECASE,
)

# Single-quoted string literal. Doubled single quotes inside SQL strings are
# rare in the current templates and are not handled here on purpose.
_STRING_LITERAL_RE = re.compile(r"'[^']*'")


@dataclass(frozen=True)
class SqlValidation:
    passed: bool
    reason: str | None
    allowed_tables: tuple[str, ...]
    used_tables: tuple[str, ...]
    limit: int | None
    limit_missing: bool

    def to_trace(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "passed": self.passed,
            "allowedTables": list(self.allowed_tables),
            "usedTables": list(self.used_tables),
            "limit": self.limit,
            "limitMissing": self.limit_missing,
        }
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


def _strip_trailing_semicolon(sql: str) -> str:
    stripped = sql.rstrip()
    if stripped.endswith(";"):
        stripped = stripped[:-1].rstrip()
    return stripped


def _strip_string_literals(sql: str) -> str:
    return _STRING_LITERAL_RE.sub("''", sql)


def _fail(
    reason: str,
    *,
    used: tuple[str, ...] = (),
    limit: int | None = None,
    limit_missing: bool = True,
) -> SqlValidation:
    return SqlValidation(
        passed=False,
        reason=reason,
        allowed_tables=tuple(sorted(ALLOWED_TABLES)),
        used_tables=used,
        limit=limit,
        limit_missing=limit_missing,
    )


def validate_sql(sql: str, params: Sequence[Any] = ()) -> SqlValidation:
    """Validate a rendered ask SQL string. Never raises."""
    if not sql or not sql.strip():
        return _fail("empty_sql")

    normalised = _strip_trailing_semicolon(sql.strip())

    # Comment and multi-statement checks run on the un-stripped form because
    # the templates never embed ``--``/``/*``/``;`` inside string literals.
    if "--" in normalised or "/*" in normalised or "*/" in normalised:
        return _fail("comment_injection")
    if ";" in normalised:
        return _fail("multi_statement")

    # Remove string literals before identifier/keyword scans so that benign
    # text such as ``WHERE status = 'partial_refunded'`` does not trip the
    # forbidden-keyword regex.
    sanitised = _strip_string_literals(normalised)

    if not re.match(r"^\s*SELECT\b", sanitised, re.IGNORECASE):
        return _fail("not_select")
    if _FORBIDDEN_KEYWORDS.search(sanitised):
        return _fail("forbidden_keyword")
    if _DANGEROUS_SCHEMAS.search(sanitised):
        return _fail("dangerous_identifier")
    if _DANGEROUS_FUNCTIONS.search(sanitised):
        return _fail("dangerous_function")

    used_tables = tuple(
        match.group(1).lower() for match in _TABLE_REFERENCE_RE.finditer(sanitised)
    )
    for table in used_tables:
        if table not in ALLOWED_TABLES:
            return _fail("table_not_allowed", used=used_tables)

    limit_match = _LIMIT_RE.search(sanitised)
    if limit_match is None:
        return _fail("limit_missing", used=used_tables)

    limit_token = limit_match.group(1)
    if limit_token == "%s":
        if not params or not isinstance(params[-1], int):
            return _fail(
                "limit_param_invalid",
                used=used_tables,
                limit=None,
                limit_missing=False,
            )
        limit_value = int(params[-1])
    else:
        limit_value = int(limit_token)

    if limit_value > MAX_LIMIT:
        return _fail(
            "limit_exceeded",
            used=used_tables,
            limit=limit_value,
            limit_missing=False,
        )

    return SqlValidation(
        passed=True,
        reason=None,
        allowed_tables=tuple(sorted(ALLOWED_TABLES)),
        used_tables=used_tables,
        limit=limit_value,
        limit_missing=False,
    )
