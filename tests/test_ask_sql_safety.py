from __future__ import annotations

from app.ask.errors import sql_unsafe, unsafe_sql
from app.ask.sql_executor import execute_select
from app.ask.sql_validator import MAX_LIMIT, validate_sql


def test_validate_sql_accepts_parameterized_select_with_limit():
    validation = validate_sql(
        """
        SELECT DATE(paid_at) AS stat_date, SUM(amount) AS paid_amount
        FROM payment_record
        WHERE payment_status = 'partial_refunded'
        GROUP BY DATE(paid_at)
        LIMIT %s
        """,
        (30,),
    )

    assert validation.passed is True
    assert validation.limit == 30
    assert validation.limit_missing is False
    assert validation.used_tables == ("payment_record",)


def test_validate_sql_rejects_missing_limit():
    validation = validate_sql("SELECT id FROM student_cohort_rel")

    assert validation.passed is False
    assert validation.reason == "limit_missing"


def test_validate_sql_rejects_limit_above_max_literal():
    validation = validate_sql(f"SELECT id FROM student_cohort_rel LIMIT {MAX_LIMIT + 1}")

    assert validation.passed is False
    assert validation.reason == "limit_exceeded"
    assert validation.limit == MAX_LIMIT + 1


def test_validate_sql_rejects_limit_above_max_parameter():
    validation = validate_sql("SELECT id FROM student_cohort_rel LIMIT %s", (MAX_LIMIT + 1,))

    assert validation.passed is False
    assert validation.reason == "limit_exceeded"
    assert validation.limit == MAX_LIMIT + 1


def test_validate_sql_rejects_non_select_and_mutation_keywords():
    assert validate_sql("UPDATE student_cohort_rel SET enroll_status = 'active' LIMIT 1").passed is False
    assert validate_sql("SELECT id FROM student_cohort_rel; SELECT id FROM payment_record LIMIT 1").passed is False


def test_validate_sql_rejects_unallowed_tables_and_dangerous_functions():
    assert validate_sql("SELECT id FROM sys_user LIMIT 1").reason == "table_not_allowed"
    assert validate_sql("SELECT SLEEP(1) FROM student_cohort_rel LIMIT 1").reason == "dangerous_function"


def test_sql_unsafe_error_code_and_alias():
    assert sql_unsafe().code == "ASK_SQL_UNSAFE"
    assert unsafe_sql("limit_missing").code == "ASK_SQL_UNSAFE"


def test_sql_executor_sanitizes_execution_failure(monkeypatch):
    def fail_fetch_all(*_args):
        raise RuntimeError("boom mysql://root:secret@localhost:3306/edu " + ("x" * 700))

    monkeypatch.setattr("app.ask.sql_executor.fetch_all", fail_fetch_all)

    try:
        execute_select("SELECT id FROM student_cohort_rel LIMIT 1", ())
    except Exception as exc:
        assert exc.status_code == 500
        assert exc.code == "ASK_SQL_EXECUTION_FAILED"
        assert "mysql://root:secret" not in exc.message
        assert "[redacted]" in exc.message
        assert len(exc.message.removeprefix("SQL 执行失败: ")) <= 500
    else:
        raise AssertionError("execute_select should raise on fetch failure")
