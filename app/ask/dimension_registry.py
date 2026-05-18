"""Dimension registry for rule-template ask queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DimensionDefinition:
    dimension_code: str
    dimension_name: str
    description: str
    table_name: str
    field_name: str
    groupable: bool = True


DIMENSIONS: dict[str, DimensionDefinition] = {
    "date": DimensionDefinition(
        dimension_code="date",
        dimension_name="日期",
        description="按日或按月统计趋势。",
        table_name="metric_time_field",
        field_name="date",
    ),
    "series": DimensionDefinition(
        dimension_code="series",
        dimension_name="课程系列",
        description="按课程系列分组或排名。",
        table_name="series",
        field_name="series_name",
    ),
    "cohort": DimensionDefinition(
        dimension_code="cohort",
        dimension_name="班次",
        description="按班次分组或筛选。",
        table_name="series_cohort",
        field_name="cohort_name",
    ),
    "campus": DimensionDefinition(
        dimension_code="campus",
        dimension_name="校区",
        description="按校区分组或排名。",
        table_name="org_campus",
        field_name="campus_name",
    ),
    "learner_identity": DimensionDefinition(
        dimension_code="learner_identity",
        dimension_name="学员身份",
        description="按学员身份分组。",
        table_name="dim_learner_identity",
        field_name="identity_name",
    ),
    "channel": DimensionDefinition(
        dimension_code="channel",
        dimension_name="渠道",
        description="按招生或转化渠道分组。",
        table_name="dim_channel",
        field_name="channel_name",
    ),
}


def get_dimension(dimension_code: str) -> DimensionDefinition | None:
    return DIMENSIONS.get(dimension_code)


def list_dimensions() -> tuple[DimensionDefinition, ...]:
    return tuple(DIMENSIONS.values())
