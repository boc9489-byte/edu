"""Build ask metadata into supported targets."""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime
from typing import Any

from app.ask.metadata_builders import (
    build_column_info_rows,
    build_column_metric_rows,
    build_dimension_info_rows,
    build_metric_info_rows,
    build_table_info_rows,
    build_table_relation_rows,
)
from app.ask.metadata_repository import (
    add_created_at,
    add_timestamps,
    execute_schema,
    safe_write_build_log,
    upsert_all_metadata,
    write_build_log,
)

MYSQL_TABLE_ORDER = (
    "ask_table_info",
    "ask_column_info",
    "ask_metric_info",
    "ask_dimension_info",
    "ask_column_metric",
    "ask_table_relation",
)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.target != "mysql":
        print(f"Unsupported target: {args.target}", file=sys.stderr)
        return 2

    payloads = build_mysql_payloads()
    item_count = sum(len(rows) for rows in payloads.values())

    if args.dry_run:
        print_dry_run(payloads)
        print(f"total: {item_count}")
        return 0

    build_id = uuid.uuid4().hex
    started_at = datetime.now()
    try:
        if args.init_schema:
            execute_schema()
        write_build_log(
            build_id=build_id,
            target="mysql",
            status="running",
            rebuild_flag=args.rebuild,
            item_count=0,
            started_at=started_at,
            finished_at=None,
        )
        affected = upsert_all_metadata(payloads)
        write_build_log(
            build_id=build_id,
            target="mysql",
            status="success",
            rebuild_flag=args.rebuild,
            item_count=item_count,
            started_at=started_at,
            finished_at=datetime.now(),
        )
        print(f"mysql metadata build succeeded: rows={item_count}, affected={affected}")
        return 0
    except Exception as exc:
        safe_write_build_log(
            build_id=build_id,
            target="mysql",
            status="failed",
            rebuild_flag=args.rebuild,
            item_count=item_count,
            error_message=str(exc),
            started_at=started_at,
            finished_at=datetime.now(),
        )
        print(f"mysql metadata build failed: {exc}", file=sys.stderr)
        return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ask metadata indexes.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--init-schema", action="store_true")
    parser.add_argument("--rebuild", action="store_true")
    return parser.parse_args(argv)


def build_mysql_payloads(now: datetime | None = None) -> dict[str, list[dict[str, Any]]]:
    timestamp = now or datetime.now()
    return {
        "ask_table_info": [
            add_timestamps(row, timestamp) for row in build_table_info_rows()
        ],
        "ask_column_info": [
            add_timestamps(row, timestamp) for row in build_column_info_rows()
        ],
        "ask_metric_info": [
            add_timestamps(row, timestamp) for row in build_metric_info_rows()
        ],
        "ask_dimension_info": [
            add_timestamps(row, timestamp) for row in build_dimension_info_rows()
        ],
        "ask_column_metric": [
            add_created_at(row, timestamp) for row in build_column_metric_rows()
        ],
        "ask_table_relation": [
            add_timestamps(row, timestamp) for row in build_table_relation_rows()
        ],
    }


def print_dry_run(payloads: dict[str, list[dict[str, Any]]]) -> None:
    print("Ask metadata MySQL dry-run")
    for table_name in MYSQL_TABLE_ORDER:
        print(f"{table_name}: {len(payloads.get(table_name, []))}")


if __name__ == "__main__":
    raise SystemExit(main())
