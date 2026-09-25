import base64

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_session
from ..models import Document, Share, User

router = APIRouter(prefix="/api/shares", tags=["shares"])


class ShareIn(BaseModel):
    document_id: int
    recipient_id: int
    version: int = Field(default=2, ge=1, le=2)
    # opaque to the server: the browser encrypts before upload
    envelope_b64: str


def _out(s: Share) -> dict:
    return {
        "id": s.id,
        "document_id": s.document_id,
        "sender_id": s.sender_id,
        "recipient_id": s.recipient_id,
        "version": s.version,
        "envelope_b64": base64.b64encode(s.envelope).decode(),
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.post("", status_code=201)
def create_share(body: ShareIn, user: User = Depends(current_user), db: Session = Depends(get_session)):
    doc = db.get(Document, body.document_id)
    if doc is None or doc.owner_id != user.id:
        raise HTTPException(404, "document not found")
    if db.get(User, body.recipient_id) is None:
        raise HTTPException(404, "recipient not found")
    share = Share(
        document_id=doc.id,
        sender_id=user.id,
        recipient_id=body.recipient_id,
        version=body.version,
        envelope=base64.b64decode(body.envelope_b64),
    )
    db.add(share)
    db.commit()
    return _out(share)


@router.get("")
def list_shares(user: User = Depends(current_user), db: Session = Depends(get_session)):
    rows = db.scalars(
        select(Share)
        .where(or_(Share.recipient_id == user.id, Share.sender_id == user.id))
        .order_by(Share.id.desc())
    )
    return [_out(s) for s in rows]
