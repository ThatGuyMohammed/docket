-- 0002 sharing and outgoing webhooks

CREATE TABLE shares (
    id           SERIAL PRIMARY KEY,
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    sender_id    INTEGER NOT NULL REFERENCES users(id),
    recipient_id INTEGER NOT NULL REFERENCES users(id),
    version      SMALLINT NOT NULL DEFAULT 2,
    envelope     BYTEA NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX shares_recipient_idx ON shares (recipient_id);

CREATE TABLE webhook_endpoints (
    id       SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url      VARCHAR(500) NOT NULL,
    events   VARCHAR(200) NOT NULL DEFAULT 'document.signed'
);
