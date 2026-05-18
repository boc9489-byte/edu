"""Static semantic relation catalog for ask metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RelationMetadata:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relation_type: str
    description: str


RELATIONS: tuple[RelationMetadata, ...] = (
    RelationMetadata("order_item", "order_id", "order", "id", "many_to_one", "订单明细归属订单。"),
    RelationMetadata("payment_record", "order_id", "order", "id", "many_to_one", "支付记录归属订单。"),
    RelationMetadata("refund_request", "order_id", "order", "id", "many_to_one", "退款申请归属订单。"),
    RelationMetadata("refund_request", "order_item_id", "order_item", "id", "many_to_one", "退款申请关联订单明细。"),
    RelationMetadata("refund_request", "payment_id", "payment_record", "id", "many_to_one", "退款申请关联支付记录。"),
    RelationMetadata("order", "order_source_channel_id", "dim_channel", "id", "many_to_one", "订单归因到招生渠道。"),
    RelationMetadata("order_item", "cohort_id", "series_cohort", "id", "many_to_one", "订单明细关联成交班次。"),
    RelationMetadata("series_cohort", "series_id", "series", "id", "many_to_one", "班次归属课程系列。"),
    RelationMetadata("series_cohort", "campus_id", "org_campus", "id", "many_to_one", "班次可关联校区。"),
    RelationMetadata("student_cohort_rel", "order_item_id", "order_item", "id", "one_to_one", "报名关系来源于订单明细。"),
    RelationMetadata("student_cohort_rel", "cohort_id", "series_cohort", "id", "many_to_one", "报名关系关联班次。"),
    RelationMetadata("student_cohort_rel", "student_id", "student_profile", "id", "many_to_one", "报名关系关联学员档案。"),
    RelationMetadata("student_profile", "learner_identity_id", "dim_learner_identity", "id", "many_to_one", "学员档案关联学习者身份。"),
    RelationMetadata("session_attendance", "cohort_id", "series_cohort", "id", "many_to_one", "考勤记录关联班次。"),
    RelationMetadata("session_attendance", "student_id", "student_profile", "id", "many_to_one", "考勤记录关联学员档案。"),
    RelationMetadata("session_video_play", "student_id", "student_profile", "id", "many_to_one", "视频播放会话关联学员档案。"),
    RelationMetadata("session_homework_submission", "student_id", "student_profile", "id", "many_to_one", "作业提交关联学员档案。"),
    RelationMetadata("session_exam_submission", "student_id", "student_profile", "id", "many_to_one", "考试作答关联学员档案。"),
    RelationMetadata("consultation_record", "cohort_id", "series_cohort", "id", "many_to_one", "咨询记录关联班次。"),
    RelationMetadata("consultation_record", "source_channel_id", "dim_channel", "id", "many_to_one", "咨询记录关联来源渠道。"),
)


def list_relations() -> tuple[RelationMetadata, ...]:
    return RELATIONS


def find_relation(
    from_table: str,
    from_column: str,
    to_table: str,
    to_column: str,
) -> RelationMetadata | None:
    for relation in RELATIONS:
        if (
            relation.from_table == from_table
            and relation.from_column == from_column
            and relation.to_table == to_table
            and relation.to_column == to_column
        ):
            return relation
    return None
