"""Legacy receipt exporter.

Every few minutes: create a receipt for each newly signed document, then
write unexported receipts to a CSV drop folder that accounting picks up.
"""

import csv
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg

from .receipts import build_payload, load_or_create_key, sign_receipt

log = logging.getLogger("exporter")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://docket:docket@localhost:5432/docket")
RECEIPT_KEY_PATH = os.environ.get("RECEIPT_KEY_PATH", "./keys/receipts.pem")
DROP_DIR = Path(os.environ.get("EXPORT_DROP_DIR", "./export"))
INTERVAL = int(os.environ.get("EXPORT_INTERVAL_SECONDS", "300"))

NEW_SIGNED = """
SELECT d.id, d.filename, d.sha256, d.signed_at
FROM documents d
LEFT JOIN receipts r ON r.document_id = d.id
WHERE d.signed_at IS NOT NULL AND r.id IS NULL
"""


def issue_receipts(conn, key) -> int:
    rows = conn.execute(NEW_SIGNED).fetchall()
    for doc_id, filename, sha256, signed_at in rows:
        payload = build_payload(doc_id, filename, sha256, signed_at.isoformat())
        conn.execute(
            "INSERT INTO receipts (document_id, payload, signature) VALUES (%s, %s, %s)",
            (doc_id, payload, sign_receipt(key, payload)),
        )
    return len(rows)


def export_pending(conn) -> Path | None:
    rows = conn.execute(
        "SELECT id, document_id, issued_at, payload, signature FROM receipts WHERE NOT exported ORDER BY id"
    ).fetchall()
    if not rows:
        return None
    DROP_DIR.mkdir(parents=True, exist_ok=True)
    out = DROP_DIR / f"receipts-{datetime.now(timezone.utc):%Y%m%d%H%M%S}.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["receipt_id", "document_id", "issued_at", "payload", "signature"])
        for r in rows:
            w.writerow([r[0], r[1], r[2].isoformat(), r[3], r[4]])
    conn.execute("UPDATE receipts SET exported = true WHERE id = ANY(%s)", ([r[0] for r in rows],))
    return out


def run_once(key) -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        n = issue_receipts(conn, key)
        path = export_pending(conn)
        conn.commit()
    log.info("issued %d receipts, export=%s", n, path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    key = load_or_create_key(RECEIPT_KEY_PATH)
    while True:
        try:
            run_once(key)
        except psycopg.Error as exc:
            log.error("export run failed: %s", exc)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
