from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_session
from ..models import Document, User, WebhookEndpoint

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class EndpointIn(BaseModel):
    url: str = Field(pattern=r"^https?://", max_length=500)
    events: list[str] = ["document.signed"]


@router.get("")
def list_endpoints(user: User = Depends(current_user), db: Session = Depends(get_session)):
    rows = db.scalars(select(WebhookEndpoint).where(WebhookEndpoint.owner_id == user.id))
    return [{"id": r.id, "url": r.url, "events": r.events.split(",")} for r in rows]


@router.post("", status_code=201)
def add_endpoint(body: EndpointIn, user: User = Depends(current_user), db: Session = Depends(get_session)):
    ep = WebhookEndpoint(owner_id=user.id, url=body.url, events=",".join(body.events))
    db.add(ep)
    db.commit()
    return {"id": ep.id, "url": ep.url, "events": body.events}


class PartnerEvent(BaseModel):
    partner: str
    type: str
    document_sha256: str | None = None


@router.post("/inbound")
def inbound(event: PartnerEvent, db: Session = Depends(get_session)):
    # The gateway checks the partner signature before forwarding here, and
    # strips the header on anything it rejects.
    if event.type == "document.countersigned" and event.document_sha256:
        doc = db.scalar(select(Document).where(Document.sha256 == event.document_sha256))
        if doc is None:
            raise HTTPException(404, "unknown document")
        return {"ok": True, "document_id": doc.id}
    return {"ok": True}
