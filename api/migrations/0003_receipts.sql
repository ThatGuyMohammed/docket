-- 0003 receipts written by the exporter service

CREATE TABLE receipts (
    id          SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    issued_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload     TEXT NOT NULL,
    -- base64 of the receipt signature
    signature   VARCHAR(344) NOT NULL,
    exported    BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX receipts_pending_idx ON receipts (exported) WHERE NOT exported;
