"""Runtime settings, read once from the environment."""

import os
from dataclasses import dataclass, field
from functools import lru_cache


# Key types we recognise when importing keys from other Docket instances.
# Only the ones in signing.SIGNERS can actually be used to sign.
KNOWN_KEY_TYPES = (
    "Ed25519",
    "RSA-PSS-3072",
    "ML-DSA-65",
    # reserved for future key types
    "ML-DSA-87",
)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
PREVIEW_TTL_SECONDS = 15 * 60


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: _env(
            "DATABASE_URL", "postgresql+psycopg://docket:docket@localhost:5432/docket"
        )
    )
    storage_dir: str = field(default_factory=lambda: _env("STORAGE_DIR", "./data/blobs"))

    # document signing
    doc_signing_alg: str = field(default_factory=lambda: _env("DOC_SIGNING_ALG", "ed25519"))
    doc_signing_key_path: str | None = field(
        default_factory=lambda: _env("DOC_SIGNING_KEY_PATH")
    )

    # login tokens
    jwt_alg: str = field(default_factory=lambda: _env("JWT_ALG", "RS256"))
    jwt_private_key_path: str | None = field(
        default_factory=lambda: _env("JWT_PRIVATE_KEY_PATH")
    )
    jwt_ttl_minutes: int = field(default_factory=lambda: int(_env("JWT_TTL_MINUTES", "60")))

    # blob encryption, hex encoded
    data_key_hex: str | None = field(default_factory=lambda: _env("DATA_KEY"))

    # outgoing webhooks
    webhook_secret: str = field(default_factory=lambda: _env("WEBHOOK_SECRET", "change-me"))

    # archive export
    archive_bucket: str | None = field(default_factory=lambda: _env("ARCHIVE_BUCKET"))
    archive_signing_alg: str = field(
        default_factory=lambda: _env("ARCHIVE_KMS_SIGNING_ALG", "RSASSA_PSS_SHA_256")
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
