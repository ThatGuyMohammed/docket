# Docket

Sign, store and share documents with your team.

Docket is a small self-hosted service for teams that pass contracts, invoices
and reports around and want to know who signed what, and when.

## Features

- Upload documents; they are encrypted at rest on the server.
- Sign a document with the server's signing key and verify it later, or
  download the public key and verify offline.
- Share a document end-to-end encrypted with a teammate. Encryption happens in
  the browser; the server only stores the encrypted envelope.
- Outgoing webhooks when a document is signed, and inbound callbacks from an
  e-signature partner.
- A receipt exporter that drops signed receipts into a folder for your
  accounting system.
- Optional nightly archive to S3.

## Layout

| Path       | What it is                                         |
|------------|----------------------------------------------------|
| `api/`     | FastAPI backend, PostgreSQL, SQL migrations         |
| `gateway/` | Go TLS front and reverse proxy for the API          |
| `web/`     | React + Vite frontend                               |
| `worker/`  | Receipt exporter                                    |
| `deploy/`  | Docker Compose file and Dockerfiles                 |

## Quick start

```sh
cp .env.example .env
# TLS material for the gateway and the edge proxy
mkdir -p deploy/certs && cp /path/to/tls.crt /path/to/tls.key deploy/certs/
# your edge proxy config (see below)
mkdir -p deploy/edge && cp /path/to/docket.conf deploy/edge/
docker compose -f deploy/docker-compose.yml up --build
```

Create the first account:

```sh
curl -k -X POST https://localhost/api/accounts/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","display_name":"You","password":"a long password"}'
```

### Edge proxy

The `edge` service runs stock nginx and loads whatever you put in
`deploy/edge/`. We don't ship a config because every install terminates TLS
differently (corporate CA, Let's Encrypt, a load balancer in front). It needs
to send `/api/` to `gateway:8443` and everything else to `web:80`.

## Local development

```sh
# api
cd api && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m app.migrate && uvicorn app.main:app --reload
pytest

# web
cd web && npm install && npm run dev

# gateway
cd gateway && go test ./... && go run .

# worker
cd worker && pip install -r requirements.txt && python -m exporter.main
```

## Configuration

API (`.env`):

| Variable                 | Default              | Notes                                   |
|--------------------------|----------------------|-----------------------------------------|
| `DATABASE_URL`           | local postgres       | SQLAlchemy URL                          |
| `STORAGE_DIR`            | `./data/blobs`       | where encrypted blobs are written       |
| `DATA_KEY`               | random per start     | 64 hex chars; set this in production    |
| `DOC_SIGNING_ALG`        | `ed25519`            | `ed25519`, `ml-dsa-65`, `rsa-pss-3072`  |
| `DOC_SIGNING_KEY_PATH`   | throwaway key        | PEM, PKCS#8                             |
| `JWT_ALG`                | `RS256`              | `RS256`, `ES256`, `EdDSA`               |
| `JWT_PRIVATE_KEY_PATH`   | throwaway key        | PEM                                     |
| `JWT_TTL_MINUTES`        | `60`                 |                                         |
| `WEBHOOK_SECRET`         | `change-me`          | HMAC secret for outgoing webhooks       |
| `ARCHIVE_BUCKET`         | unset                | enables the archive export              |
| `ARCHIVE_KMS_KEY_ID`     | unset                | KMS key used to sign archive manifests  |
| `ARCHIVE_KMS_SIGNING_ALG`| `RSASSA_PSS_SHA_256` | must match the KMS key                  |

Changing `DOC_SIGNING_ALG` does not re-sign existing documents; `verify`
reports documents signed under the previous algorithm.

Gateway:

| Variable               | Default          |
|------------------------|------------------|
| `GATEWAY_LISTEN`       | `:8443`          |
| `GATEWAY_ADMIN_LISTEN` | `:9443`          |
| `TLS_CERT_FILE`        | `/certs/tls.crt` |
| `TLS_KEY_FILE`         | `/certs/tls.key` |
| `UPSTREAM_URL`         | `http://api:8000`|
| `PARTNER_PUBLIC_KEY`   | unset            |

`PARTNER_PUBLIC_KEY` is the base64 public key your e-signature partner gives
you. Callbacks to `/api/webhooks/inbound` are rejected until it is set.

Worker: `DATABASE_URL`, `RECEIPT_KEY_PATH`, `EXPORT_DROP_DIR`,
`EXPORT_INTERVAL_SECONDS`.

### Webhook signatures

Outgoing deliveries carry `X-Docket-Timestamp` and `X-Docket-Signature`. The
signature is the hex HMAC-SHA256 of `"<timestamp>.<raw body>"` using
`WEBHOOK_SECRET`.

## License

MIT
