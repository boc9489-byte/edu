"""Static semantic column catalog for ask metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnMetadata:
    table_name: str
    column_name: str
    display_name: str
    data_type: str
    role: str
    description: str
    enum_values: tuple[str, ...] = ()
    related_metrics: tuple[str, ...] = ()


def _c(
    table_name: str,
    column_name: str,
    display_name: str,
    data_type: str,
    role: str,
    description: str,
    enum_values: tuple[str, ...] = (),
    related_metrics: tuple[str, ...] = (),
) -> ColumnMetadata:
    return ColumnMetadata(
        table_name=table_name,
        column_name=column_name,
        display_name=display_name,
        data_type=data_type,
        role=role,
        description=description,
        enum_values=enum_values,
        related_metrics=related_metrics,
    )


COLUMNS: tuple[ColumnMetadata, ...] = (
    _c("order", "id", "订单ID", "BIGINT", "primary_key", "订单主键。"),
    _c("order", "student_id", "学员档案ID", "BIGINT", "foreign_key", "关联 student_profile.id。"),
    _c(
        "order",
        "order_source_channel_id",
        "订单来源渠道ID",
        "BIGINT",
        "foreign_key",
        "关联 dim_channel.id，用于订单归因。",
        related_metrics=("conversion_rate",),
    ),
    _c(
        "order",
        "order_status",
        "订单状态",
        "VARCHAR",
        "status",
        "订单支付、完成、取消和退款状态。",
        ("pending", "paid", "completed", "cancelled", "partial_refunded", "refunded"),
        ("paid_amount", "refund_amount"),
    ),
    _c("order", "paid_amount", "实付金额", "DECIMAL", "measure", "订单实付金额。", related_metrics=("paid_amount",)),
    _c("order", "refund_amount", "累计退款金额", "DECIMAL", "measure", "订单累计退款金额。", related_metrics=("refund_amount",)),
    _c("order", "paid_at", "支付时间", "DATETIME", "time", "订单支付时间。", related_metrics=("paid_amount",)),
    _c("order", "created_at", "创建时间", "DATETIME", "time", "订单创建时间。"),
    _c("order_item", "id", "订单明细ID", "BIGINT", "primary_key", "订单明细主键。"),
    _c("order_item", "order_id", "订单ID", "BIGINT", "foreign_key", "关联 order.id。"),
    _c("order_item", "student_id", "学员档案ID", "BIGINT", "foreign_key", "关联 student_profile.id。"),
    _c("order_item", "cohort_id", "班次ID", "BIGINT", "foreign_key", "关联 series_cohort.id。"),
    _c(
        "order_item",
        "order_item_status",
        "订单明细状态",
        "VARCHAR",
        "status",
        "订单明细支付、完成、取消和退款状态。",
        ("pending", "paid", "completed", "cancelled", "refunded"),
    ),
    _c("order_item", "payable_amount", "应付金额", "DECIMAL", "measure", "订单明细应付金额。", related_metrics=("paid_amount",)),
    _c("payment_record", "id", "支付记录ID", "BIGINT", "primary_key", "支付记录主键。"),
    _c("payment_record", "order_id", "订单ID", "BIGINT", "foreign_key", "关联 order.id。"),
    _c(
        "payment_record",
        "payment_channel",
        "支付渠道",
        "VARCHAR",
        "dimension",
        "支付渠道。",
        ("wechat_pay", "alipay", "bank_card", "offline_transfer", "public_account", "campus_cashier"),
    ),
    _c(
        "payment_record",
        "payment_status",
        "支付状态",
        "VARCHAR",
        "status",
        "支付状态。",
        ("pending", "paid", "failed", "closed", "partial_refunded", "refunded"),
        ("paid_amount",),
    ),
    _c("payment_record", "amount", "支付金额", "DECIMAL", "measure", "支付流水金额。", related_metrics=("paid_amount",)),
    _c("payment_record", "refund_amount", "累计退款金额", "DECIMAL", "measure", "支付记录累计退款金额。", related_metrics=("refund_amount",)),
    _c("payment_record", "paid_at", "支付时间", "DATETIME", "time", "支付成功时间。", related_metrics=("paid_amount",)),
    _c("payment_record", "refund_at", "退款时间", "DATETIME", "time", "支付记录退款时间。", related_metrics=("refund_amount",)),
    _c("refund_request", "id", "退款申请ID", "BIGINT", "primary_key", "退款申请主键。"),
    _c("refund_request", "order_id", "订单ID", "BIGINT", "foreign_key", "关联 order.id。"),
    _c("refund_request", "order_item_id", "订单明细ID", "BIGINT", "foreign_key", "关联 order_item.id。"),
    _c("refund_request", "payment_id", "支付记录ID", "BIGINT", "foreign_key", "关联 payment_record.id。"),
    _c(
        "refund_request",
        "refund_status",
        "退款状态",
        "VARCHAR",
        "status",
        "退款申请状态。",
        ("pending", "approved", "rejected", "refunded"),
        ("refund_amount",),
    ),
    _c("refund_request", "apply_amount", "申请退款金额", "DECIMAL", "measure", "用户申请退款金额。"),
    _c("refund_request", "approved_amount", "审批退款金额", "DECIMAL", "measure", "审批通过的退款金额。", related_metrics=("refund_amount",)),
    _c("refund_request", "refunded_at", "退款完成时间", "DATETIME", "time", "退款完成时间。", related_metrics=("refund_amount",)),
    _c("student_cohort_rel", "id", "报名关系ID", "BIGINT", "primary_key", "学员班次关系主键。"),
    _c("student_cohort_rel", "student_id", "学员档案ID", "BIGINT", "foreign_key", "关联 student_profile.id。", related_metrics=("enrollment_count", "completion_rate")),
    _c("student_cohort_rel", "cohort_id", "班次ID", "BIGINT", "foreign_key", "关联 series_cohort.id。", related_metrics=("enrollment_count",)),
    _c("student_cohort_rel", "order_item_id", "订单明细ID", "BIGINT", "foreign_key", "关联 order_item.id。"),
    _c(
        "student_cohort_rel",
        "enroll_status",
        "报名状态",
        "VARCHAR",
        "status",
        "报名履约状态。",
        ("active", "completed", "cancelled", "refunded"),
        ("enrollment_count", "completion_rate"),
    ),
    _c("student_cohort_rel", "enroll_at", "报名时间", "DATETIME", "time", "报名时间。", related_metrics=("enrollment_count", "completion_rate")),
    _c("student_cohort_rel", "completed_at", "完课时间", "DATETIME", "time", "完课时间。", related_metrics=("completion_rate",)),
    _c("series", "id", "课程系列ID", "BIGINT", "primary_key", "课程系列主键。"),
    _c(
        "series",
        "delivery_mode",
        "授课方式",
        "VARCHAR",
        "dimension",
        "课程授课方式。",
        ("online_live", "online_recorded", "offline_face_to_face"),
    ),
    _c("series", "series_name", "课程系列名称", "VARCHAR", "dimension", "课程系列名称。", related_metrics=("enrollment_count", "paid_amount", "refund_amount")),
    _c("series", "sale_status", "售卖状态", "VARCHAR", "status", "课程系列售卖状态。", ("draft", "on_sale", "off_sale")),
    _c("series_cohort", "id", "班次ID", "BIGINT", "primary_key", "班次主键。"),
    _c("series_cohort", "series_id", "课程系列ID", "BIGINT", "foreign_key", "关联 series.id。"),
    _c("series_cohort", "campus_id", "校区ID", "BIGINT", "foreign_key", "关联 org_campus.id。"),
    _c("series_cohort", "cohort_name", "班次名称", "VARCHAR", "dimension", "班次名称。", related_metrics=("enrollment_count", "paid_amount", "refund_amount")),
    _c("series_cohort", "sale_price", "班次售价", "DECIMAL", "measure", "班次售价。", related_metrics=("paid_amount",)),
    _c("series_cohort", "current_student_count", "当前学员数", "INT", "measure", "班次当前学员数。", related_metrics=("enrollment_count",)),
    _c("series_cohort", "yn", "是否启用", "TINYINT", "status", "班次是否启用。", ("0", "1")),
    _c("series_cohort", "start_date", "开始日期", "DATE", "time", "班次开始日期。"),
    _c("series_cohort", "end_date", "结束日期", "DATE", "time", "班次结束日期。"),
    _c("org_campus", "id", "校区ID", "BIGINT", "primary_key", "校区主键。"),
    _c("org_campus", "campus_name", "校区名称", "VARCHAR", "dimension", "校区名称。", related_metrics=("enrollment_count", "paid_amount", "refund_amount")),
    _c("student_profile", "id", "学员档案ID", "BIGINT", "primary_key", "学员档案主键。"),
    _c("student_profile", "user_id", "用户ID", "BIGINT", "foreign_key", "关联 sys_user.id。"),
    _c("student_profile", "learner_identity_id", "学习者身份ID", "BIGINT", "foreign_key", "关联 dim_learner_identity.id。"),
    _c("dim_learner_identity", "id", "学习者身份ID", "BIGINT", "primary_key", "学习者身份主键。"),
    _c("dim_learner_identity", "identity_code", "学习者身份编码", "VARCHAR", "dimension", "学习者身份编码。"),
    _c("dim_learner_identity", "identity_name", "学习者身份名称", "VARCHAR", "dimension", "学习者身份名称。", related_metrics=("enrollment_count", "completion_rate")),
    _c("dim_channel", "id", "渠道ID", "BIGINT", "primary_key", "招生渠道主键。"),
    _c("dim_channel", "channel_category_code", "渠道分类编码", "VARCHAR", "dimension", "渠道分类编码。"),
    _c("dim_channel", "channel_category_name", "渠道分类名称", "VARCHAR", "dimension", "渠道分类名称。"),
    _c("dim_channel", "channel_code", "渠道编码", "VARCHAR", "dimension", "招生渠道编码。"),
    _c("dim_channel", "channel_name", "渠道名称", "VARCHAR", "dimension", "招生渠道名称。", related_metrics=("paid_amount", "refund_amount", "conversion_rate")),
    _c("session_attendance", "id", "考勤ID", "BIGINT", "primary_key", "课次考勤主键。"),
    _c("session_attendance", "session_id", "课次ID", "BIGINT", "foreign_key", "关联 series_cohort_session.id。"),
    _c("session_attendance", "cohort_id", "班次ID", "BIGINT", "foreign_key", "关联 series_cohort.id。", related_metrics=("attendance_rate",)),
    _c("session_attendance", "student_id", "学员档案ID", "BIGINT", "foreign_key", "关联 student_profile.id。", related_metrics=("attendance_rate",)),
    _c(
        "session_attendance",
        "attendance_status",
        "考勤状态",
        "VARCHAR",
        "status",
        "课次考勤状态。",
        ("pending", "present", "absent", "leave", "late"),
        ("attendance_rate",),
    ),
    _c("session_attendance", "checkin_time", "签到时间", "DATETIME", "time", "签到时间。"),
    _c("session_attendance", "created_at", "创建时间", "DATETIME", "time", "考勤记录创建时间。", related_metrics=("attendance_rate",)),
    _c("session_video_play", "id", "视频播放会话ID", "BIGINT", "primary_key", "视频播放会话主键。"),
    _c("session_video_play", "video_id", "视频ID", "BIGINT", "foreign_key", "关联 session_video.id。"),
    _c("session_video_play", "student_id", "学员档案ID", "BIGINT", "foreign_key", "关联 student_profile.id。"),
    _c("session_video_play", "progress_percent", "观看进度", "DECIMAL", "measure", "观看进度百分比。", related_metrics=("completion_rate",)),
    _c("session_video_play", "completed_flag", "是否看完", "TINYINT", "status", "视频是否看完。", ("0", "1"), ("completion_rate",)),
    _c("session_video_play", "watched_seconds", "观看秒数", "INT", "measure", "累计观看秒数。"),
    _c("session_video_play", "started_at", "开始播放时间", "DATETIME", "time", "开始播放时间。"),
    _c("session_video_play", "ended_at", "结束播放时间", "DATETIME", "time", "结束播放时间。"),
    _c("session_homework_submission", "id", "作业提交ID", "BIGINT", "primary_key", "作业提交主键。"),
    _c("session_homework_submission", "homework_id", "作业ID", "BIGINT", "foreign_key", "关联 session_homework.id。"),
    _c("session_homework_submission", "student_id", "学员档案ID", "BIGINT", "foreign_key", "关联 student_profile.id。"),
    _c("session_homework_submission", "session_id", "课次ID", "BIGINT", "foreign_key", "关联 series_cohort_session.id。"),
    _c("session_homework_submission", "submit_status", "提交状态", "VARCHAR", "status", "作业提交状态。", ("submitted", "expired_unsubmitted"), ("completion_rate",)),
    _c("session_homework_submission", "total_score", "总分", "DECIMAL", "measure", "作业得分。"),
    _c("session_homework_submission", "correction_status", "批改状态", "VARCHAR", "status", "作业批改状态。", ("pending", "corrected")),
    _c("session_homework_submission", "submitted_at", "提交时间", "DATETIME", "time", "作业提交时间。"),
    _c("session_exam_submission", "id", "考试作答ID", "BIGINT", "primary_key", "考试作答主键。"),
    _c("session_exam_submission", "exam_id", "考试ID", "BIGINT", "foreign_key", "关联 session_exam.id。"),
    _c("session_exam_submission", "student_id", "学员档案ID", "BIGINT", "foreign_key", "关联 student_profile.id。"),
    _c("session_exam_submission", "attempt_status", "作答状态", "VARCHAR", "status", "考试作答状态。", ("not_started", "in_progress", "submitted", "absent", "timeout"), ("completion_rate",)),
    _c("session_exam_submission", "duration_seconds", "作答时长", "INT", "measure", "考试作答时长。"),
    _c("session_exam_submission", "score_value", "得分", "DECIMAL", "measure", "考试得分。"),
    _c("session_exam_submission", "start_at", "开始作答时间", "DATETIME", "time", "开始作答时间。"),
    _c("session_exam_submission", "submit_at", "提交时间", "DATETIME", "time", "考试提交时间。"),
    _c("consultation_record", "id", "咨询记录ID", "BIGINT", "primary_key", "咨询记录主键。"),
    _c("consultation_record", "cohort_id", "班次ID", "BIGINT", "foreign_key", "关联 series_cohort.id。", related_metrics=("conversion_rate",)),
    _c("consultation_record", "source_channel_id", "来源渠道ID", "BIGINT", "foreign_key", "关联 dim_channel.id。", related_metrics=("conversion_rate",)),
    _c("consultation_record", "consulted_at", "咨询时间", "DATETIME", "time", "咨询时间。", related_metrics=("conversion_rate",)),
)

COLUMN_CATALOG: dict[tuple[str, str], ColumnMetadata] = {
    (column.table_name, column.column_name): column for column in COLUMNS
}


def get_column(table_name: str, column_name: str) -> ColumnMetadata | None:
    return COLUMN_CATALOG.get((table_name, column_name))


def list_columns() -> tuple[ColumnMetadata, ...]:
    return tuple(COLUMN_CATALOG.values())


def list_columns_by_table(table_name: str) -> tuple[ColumnMetadata, ...]:
    return tuple(column for column in COLUMN_CATALOG.values() if column.table_name == table_name)
