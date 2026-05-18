from __future__ import annotations

from app.scripts import build_ask_metadata


def test_dry_run_prints_counts_without_connecting_to_database(monkeypatch, capsys):
    def fail_if_called():
        raise AssertionError("dry-run must not execute schema")

    monkeypatch.setattr(build_ask_metadata, "execute_schema", fail_if_called)
    monkeypatch.setattr(
        build_ask_metadata,
        "upsert_all_metadata",
        lambda _payloads: (_ for _ in ()).throw(
            AssertionError("dry-run must not upsert metadata")
        ),
    )

    exit_code = build_ask_metadata.main(["--target", "mysql", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Ask metadata MySQL dry-run" in output
    assert "ask_table_info:" in output
    assert "ask_column_info:" in output
    assert "total:" in output


def test_non_mysql_target_is_rejected(capsys):
    exit_code = build_ask_metadata.main(["--target", "qdrant", "--dry-run"])

    err = capsys.readouterr().err
    assert exit_code == 2
    assert "Unsupported target: qdrant" in err


def test_mysql_build_calls_schema_upsert_and_build_log(monkeypatch):
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        build_ask_metadata,
        "execute_schema",
        lambda: calls.append(("schema", None)),
    )
    monkeypatch.setattr(
        build_ask_metadata,
        "upsert_all_metadata",
        lambda payloads: calls.append(("upsert", sorted(payloads))) or 123,
    )
    monkeypatch.setattr(
        build_ask_metadata,
        "write_build_log",
        lambda **kwargs: calls.append(("log", kwargs)),
    )

    exit_code = build_ask_metadata.main(["--target", "mysql", "--init-schema"])

    assert exit_code == 0
    assert calls[0] == ("schema", None)
    assert calls[1][0] == "log"
    assert calls[1][1]["status"] == "running"
    assert calls[2][0] == "upsert"
    assert calls[3][0] == "log"
    assert calls[3][1]["status"] == "success"
    assert calls[3][1]["target"] == "mysql"
    assert calls[3][1]["item_count"] > 0


def test_mysql_build_failed_log_is_safe(monkeypatch):
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        build_ask_metadata,
        "upsert_all_metadata",
        lambda _payloads: (_ for _ in ()).throw(RuntimeError("database down")),
    )
    monkeypatch.setattr(
        build_ask_metadata,
        "write_build_log",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        build_ask_metadata,
        "safe_write_build_log",
        lambda **kwargs: calls.append(kwargs),
    )

    exit_code = build_ask_metadata.main(["--target", "mysql"])

    assert exit_code == 1
    assert calls
    assert calls[0]["status"] == "failed"
    assert calls[0]["target"] == "mysql"
    assert calls[0]["error_message"] == "database down"


def test_build_mysql_payloads_contains_expected_tables():
    payloads = build_ask_metadata.build_mysql_payloads()

    assert set(payloads) == set(build_ask_metadata.MYSQL_TABLE_ORDER)
    assert payloads["ask_table_info"]
    assert payloads["ask_column_metric"]
    assert "created_at" in payloads["ask_table_info"][0]
    assert "updated_at" in payloads["ask_table_info"][0]
    assert "created_at" in payloads["ask_column_metric"][0]
    assert "updated_at" not in payloads["ask_column_metric"][0]
