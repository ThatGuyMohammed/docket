from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import check_password, current_user, hash_password, issue_token
from ..db import get_session
from ..models import User

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


class SignupIn(BaseModel):
    email: str = Field(max_length=255)
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=10)


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    share_public_key: str | None = None


def _out(u: User) -> UserOut:
    return UserOut(id=u.id, email=u.email, display_name=u.display_name, share_public_key=u.share_public_key)


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(body: SignupIn, db: Session = Depends(get_session)):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "email already registered")
    user = User(
        email=body.email.lower(),
        display_name=body.display_name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    return _out(user)


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_session)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not check_password(body.password, user.password_hash):
        raise HTTPException(401, "wrong email or password")
    return {"access_token": issue_token(user), "token_type": "bearer", "user": _out(user)}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return _out(user)


class ShareKeyIn(BaseModel):
    public_key: str = Field(max_length=4096)


@router.put("/me/share-key", response_model=UserOut)
def set_share_key(body: ShareKeyIn, user: User = Depends(current_user), db: Session = Depends(get_session)):
    user.share_public_key = body.public_key
    db.add(user)
    db.commit()
    return _out(user)


@router.get("/directory", response_model=list[UserOut])
def directory(user: User = Depends(current_user), db: Session = Depends(get_session)):
    return [_out(u) for u in db.scalars(select(User).where(User.id != user.id).order_by(User.display_name))]
