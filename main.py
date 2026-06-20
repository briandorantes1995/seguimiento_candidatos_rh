import os
from fastapi import Depends, FastAPI,Request,HTTPException
from fastapi.responses import RedirectResponse,JSONResponse
from db.models import Usuario,create_db_and_tables
from routers import empresa,puesto,candidato,auth,entrevista,postulaciones,user,papeleria,dashboard
from fastapi.templating import Jinja2Templates
from helpers import get_current_user
from rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY")


app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.state.limiter = limiter

class CsrfSettings(BaseSettings):
  secret_key: str = CSRF_SECRET_KEY
  cookie_samesite: str = "lax"
  cookie_secure: bool = True

@CsrfProtect.load_config
def get_csrf_config():
  return CsrfSettings()

@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
  return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
app.include_router(empresa.router)
app.include_router(puesto.router)
app.include_router(candidato.router)
app.include_router(postulaciones.router)
app.include_router(entrevista.router)
app.include_router(user.router)
app.include_router(papeleria.router)
app.include_router(dashboard.router)
app.include_router(auth.router)


@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/auth/")

    raise exc

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/health")
def health():
    return {"Hello": "World"}

@app.get("/home")
def home(request: Request,current_user: Usuario = Depends(get_current_user),):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "user": current_user
        })