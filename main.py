from fastapi import Depends, FastAPI,Request,HTTPException
from fastapi.responses import RedirectResponse
from db.models import Usuario,create_db_and_tables
from routers import empresa,puesto,candidato,auth,entrevista,postulaciones,user,papeleria,dashboard
from fastapi.templating import Jinja2Templates
from helpers import get_current_user



app = FastAPI()
templates = Jinja2Templates(directory="templates")
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