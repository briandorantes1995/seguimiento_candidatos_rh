import uuid
from fastapi import Depends,Request,Cookie, HTTPException
from datetime import UTC, datetime
from db.models  import Usuario,get_session
from sqlmodel import Session
from jose import jwt

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") is not None


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_current_user(access_token: str | None = Cookie(default=None),session: Session = Depends(get_session)):
    if not access_token:
        raise HTTPException(status_code=401)

    try:
        payload = jwt.decode(
            access_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = uuid.UUID(payload["user_id"])

    except Exception:
        raise HTTPException(status_code=401)

    usuario = session.get(Usuario, user_id)

    if not usuario:
        raise HTTPException(status_code=401)

    return usuario     