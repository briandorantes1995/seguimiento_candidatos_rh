from fastapi import Depends,APIRouter, Query,Request
from db.models import Candidato, get_session
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from helpers import is_htmx

router = APIRouter(
    prefix="/candidatos",
    tags=["candidatos"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")

@router.get("/form")
def read_candidato_form(request: Request):
    return templates.TemplateResponse(request=request, name="candidato.html")


@router.post("/")
def create_candidato(candidato: Candidato, session: Session = Depends(get_session)) -> Candidato:
    session.add(candidato)
    session.commit()
    session.refresh(candidato)
    return candidato


@router.get("/")
def read_candidatos(session: Session = Depends(get_session),offset: int = 0,limit: int = Query(default=100, le=100),) -> list[Candidato]:
    candidatos = session.exec(select(Candidato).offset(offset).limit(limit)).all()
    return candidatos