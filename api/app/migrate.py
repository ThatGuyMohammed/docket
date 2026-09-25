"""Apply SQL files in migrations/ in order. Tracks applied files in schema_migrations."""

import sys
from pathlib import Path

from sqlalchemy import text

from .db import engine

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def main() -> int:
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        ))
        done = {r[0] for r in conn.execute(text("SELECT name FROM schema_migrations"))}
        for path in sorted(MIGRATIONS.glob("*.sql")):
            if path.name in done:
                continue
            print(f"applying {path.name}")
            conn.exec_driver_sql(path.read_text())
            conn.execute(text("INSERT INTO schema_migrations (name) VALUES (:n)"), {"n": path.name})
    return 0


if __name__ == "__main__":
    sys.exit(main())
