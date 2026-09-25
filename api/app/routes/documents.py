from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import MAX_UPLOAD_BYTES
from ..db import get_session
from ..models import Document, User
from ..signing import get_signer
from ..storage import etag_for, get_store, previews, sha256_hex
from ..webhooks import deliver

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _doc_out(d: Document) -> dict:
    return {
        "id": d.id,
        "filename": d.filename,
        "content_type": d.content_type,
        "size_bytes": d.size_bytes,
        "sha256": d.sha256,
        "signed": d.signature is not None,
        "signature_alg": d.signature_alg,
        "signed_at": d.signed_at.isoformat() if d.signed_at else None,
    }


def _owned(db: Session, doc_id: int, user: User) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None or doc.owner_id != user.id:
        raise HTTPException(404, "document not found")
    return doc


@router.get("")
def list_documents(user: User = Depends(current_user), db: Session = Depends(get_session)):
    docs = db.scalars(select(Document).where(Document.owner_id == user.id).order_by(Document.id.desc()))
    return [_doc_out(d) for d in docs]


@router.post("", status_code=201)
async def upload(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_session)):
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "file too large")
    doc = Document(
        owner_id=user.id,
        filename=file.filename or "untitled",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        blob_path=get_store().put(data),
        sha256=sha256_hex(data),
    )
    db.add(doc)
    db.commit()
    return _doc_out(doc)


@router.get("/{doc_id}/content")
def download(doc_id: int, request: Request, user: User = Depends(current_user), db: Session = Depends(get_session)):
    doc = _owned(db, doc_id, user)
    data = get_store().get(doc.blob_path)
    tag = etag_for(data)
    if request.headers.get("if-none-match") == tag:
        return Response(status_code=304)
    return Response(data, media_type=doc.content_type, headers={"ETag": tag})


@router.get("/{doc_id}/preview")
def preview(doc_id: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    doc = _owned(db, doc_id, user)
    cache_key = f"{doc.id}:{doc.sha256}"
    cached = previews.get(cache_key)
    if cached is None:
        data = get_store().get(doc.blob_path)
        cached = data[:4096]
        previews.set(cache_key, cached)
    return Response(cached, media_type="text/plain")


@router.post("/{doc_id}/sign")
def sign(doc_id: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    doc = _owned(db, doc_id, user)
    signer = get_signer()
    doc.signature = signer.sign(bytes.fromhex(doc.sha256))
    doc.signature_alg = signer.alg
    doc.signed_at = datetime.now(timezone.utc)
    db.commit()
    deliver(db, user.id, "document.signed", {"id": doc.id, "sha256": doc.sha256})
    return {**_doc_out(doc), "signature": doc.signature}


@router.get("/{doc_id}/verify")
def verify(doc_id: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    doc = _owned(db, doc_id, user)
    if doc.signature is None:
        return {"valid": False, "reason": "not signed"}
    signer = get_signer()
    if doc.signature_alg != signer.alg:
        return {"valid": False, "reason": f"signed with {doc.signature_alg}, server now uses {signer.alg}"}
    return {"valid": signer.verify(bytes.fromhex(doc.sha256), doc.signature)}


@router.delete("/{doc_id}", status_code=204)
def delete(doc_id: int, user: User = Depends(current_user), db: Session = Depends(get_session)):
    doc = _owned(db, doc_id, user)
    get_store().delete(doc.blob_path)
    db.delete(doc)
    db.commit()
