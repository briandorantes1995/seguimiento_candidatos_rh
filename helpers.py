import uuid
from fastapi import Depends, Request, Cookie, HTTPException
from datetime import UTC, datetime
from db.models import Usuario, UserType, get_session
from sqlmodel import Session, SQLModel
from jose import jwt

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") is not None


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_current_user(access_token: str | None = Cookie(default=None), session: Session = Depends(get_session)):
    if not access_token:
        raise HTTPException(status_code=401)

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload["user_id"])
    except Exception:
        raise HTTPException(status_code=401)

    usuario = session.get(Usuario, user_id)

    if not usuario:
        raise HTTPException(status_code=401)

    return usuario


def get_admin_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(status_code=403, detail="Se requiere rol admin")
    return current_user


def check_owner(obj: SQLModel, current_user: Usuario):
    if current_user.user_type != UserType.ADMIN and obj.created_by != current_user.id:
        raise HTTPException(status_code=403)


def apply_ownership_filter(query, model, current_user: Usuario):
    if current_user.user_type != UserType.ADMIN:
        query = query.where(model.created_by == current_user.id)
    return query