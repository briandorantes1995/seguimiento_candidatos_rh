import bcrypt
from jose import jwt
from fastapi import Depends,APIRouter, Query,Request,HTTPException,Response
from fastapi.responses import RedirectResponse
from db.models import Usuario,Login, get_session
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from helpers import is_htmx


SECRET_KEY = "supersecret"
ALGORITHM = "HS256"

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/")
def read_candidato_form(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login")
def login(login_data: Login,session: Session = Depends(get_session)):
    usuario = session.exec(
        select(Usuario)
        .where(Usuario.email == login_data.email)
    ).first()

    if not usuario:
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    if not bcrypt.checkpw(
        login_data.password.encode(),
        usuario.password.encode()
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid credentials"
        )

    payload = {
        "user_id": str(usuario.id),
        "user_name": usuario.name
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = RedirectResponse(
        url="/home",
        status_code=303
    )

    response = Response(status_code=200)

    response.headers["HX-Redirect"] = "/home"

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True
    )

    return response


@router.post("/register")
def register(usuario: Usuario,session: Session = Depends(get_session)) -> Usuario:

    existing_user = session.exec(select(Usuario).where(Usuario.email == usuario.email)).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    hashed_password = bcrypt.hashpw(usuario.password.encode(), bcrypt.gensalt()).decode()

    usuario.password = hashed_password

    session.add(usuario)
    session.commit()
    session.refresh(usuario)

    return usuario


@router.post("/logout")
def logout():
    response = RedirectResponse(
        url="/auth/",
        status_code=303
    )

    response.delete_cookie("access_token")

    return response

   

