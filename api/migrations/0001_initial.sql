-- 0001 initial schema

CREATE TABLE users (
    id               SERIAL PRIMARY KEY,
    email            VARCHAR(255) NOT NULL UNIQUE,
    display_name     VARCHAR(120) NOT NULL,
    password_hash    VARCHAR(200) NOT NULL,
    share_public_key TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE documents (
    id            SERIAL PRIMARY KEY,
    owner_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename      VARCHAR(255) NOT NULL,
    content_type  VARCHAR(120) NOT NULL,
    size_bytes    INTEGER NOT NULL,
    blob_path     VARCHAR(255) NOT NULL,
    sha256        CHAR(64) NOT NULL,
    signature     TEXT,
    signature_alg VARCHAR(32),
    signed_at     TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX documents_owner_idx ON documents (owner_id);
CREATE INDEX documents_sha256_idx ON documents (sha256);
