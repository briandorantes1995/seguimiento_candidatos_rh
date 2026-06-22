import bcrypt
import os
from jose import jwt
from fastapi import Depends,APIRouter,Request,HTTPException,Response
from fastapi.responses import RedirectResponse
from db.models import Usuario,Login, get_session
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from fastapi_csrf_protect import CsrfProtect
from db.crud import insert_db_element
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/")
def read_candidato_form(request: Request,csrf_protect: CsrfProtect = Depends()):
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

    response = templates.TemplateResponse(request=request,name="login.html",context={"csrf_token": csrf_token})

    csrf_protect.set_csrf_cookie(signed_token, response)

    return response


@router.post("/login")
async def login(request: Request, session: Session = Depends(get_session)):
    try:
        body = await request.json()
    except Exception:
        return Response(
            content="Error al procesar la solicitud",
            media_type="text/html",
            status_code=200,
            headers={"HX-Retarget": "#error", "HX-Reswap": "innerHTML"}
        )
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return Response(
            content="Correo y contraseña requeridos",
            media_type="text/html",
            status_code=200,
            headers={"HX-Retarget": "#error", "HX-Reswap": "innerHTML"}
        )

    usuario = session.exec(select(Usuario).where(Usuario.email == email)).first()

    if not usuario or not bcrypt.checkpw(password.encode(), usuario.password.encode()):
        return Response(
            content="Correo o contraseña incorrectos",
            media_type="text/html",
            status_code=200,
            headers={"HX-Retarget": "#error", "HX-Reswap": "innerHTML"}
        )

    payload = {"user_id": str(usuario.id), "user_name": usuario.name}
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)

    response = Response(status_code=200)
    response.headers["HX-Redirect"] = "/home"
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@router.post("/register")
def register(usuario: Usuario,session: Session = Depends(get_session)) -> Usuario:

    existing_user = session.exec(select(Usuario).where(Usuario.email == usuario.email)).first()

    if existing_user:
        raise HTTPException( status_code=400,detail="User already exists")

    hashed_password = bcrypt.hashpw(usuario.password.encode(), bcrypt.gensalt()).decode()

    usuario.password = hashed_password

    insert_db_element(session, usuario)

    return usuario


@router.post("/logout")
async def logout(request: Request, csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    response = RedirectResponse(
        url="/auth/",
        status_code=303
    )

    response.delete_cookie("access_token")

    return response

   

