"""Render registered SQL templates with parsed ask parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .sql_templates import get_sql_template
from .time_range_parser import TimeRange


@dataclass(frozen=True)
class RenderedTemplate:
    template_key: str
    sql: str
    params: tuple[Any, ...]
    answer_factory: Callable[[list[dict[str, Any]]], str]


def render_template(template_key: str, time_range: TimeRange) -> RenderedTemplate | None:
    template = get_sql_template(template_key)
    if template is None:
        return None
    return RenderedTemplate(
        template_key=template.template_key,
        sql=template.sql,
        params=template.params_factory(time_range),
        answer_factory=template.answer_factory,
    )
