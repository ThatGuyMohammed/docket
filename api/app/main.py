import logging

from fastapi import FastAPI

from . import __version__
from .routes import accounts, documents, hooks, shares
from .signing import get_signer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Docket API", version=__version__)
app.include_router(accounts.router)
app.include_router(documents.router)
app.include_router(shares.router)
app.include_router(hooks.router)


@app.get("/healthz")
def healthz():
    return {"ok": True, "version": __version__}


@app.get("/api/signing-key")
def signing_key():
    """Public key used for document signatures, for offline verification."""
    signer = get_signer()
    return {"alg": signer.alg, "public_key_pem": signer.public_key_pem()}
