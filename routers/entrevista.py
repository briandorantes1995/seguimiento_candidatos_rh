import uuid
from fastapi import Depends,APIRouter, Query,Request,HTTPException,Response
from db.models import Candidato,Entrevista,EntrevistaUpdate,EntrevistaCreate, get_session
from sqlmodel import Session, select
from db.crud import delete_db_element,insert_db_element,update_db_element
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from helpers import is_htmx,get_current_user

router = APIRouter(
    prefix="/entrevistas",
    tags=["entrevistas"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/candidato/{candidato_id}")
def candidato_historial_entrevistas(candidato_id: int,request: Request,session: Session = Depends(get_session)):
    candidato = session.get(Candidato, candidato_id)

    return templates.TemplateResponse(
        request=request,
        name="candidato.html",
        context={"candidato": candidato}
    ) 

@router.get("/")
def read_entrevistas(request: Request,session: Session = Depends(get_session),offset: int = 0,limit: int = Query(default=100, le=100)) -> list[Entrevista]:
    entrevistas = session.exec(select(Entrevista).offset(offset).limit(limit)).all()
    if is_htmx(request):
     return templates.TemplateResponse(request=request,name="partials/entrevista/entrevista_list.html",context={"entrevistas": entrevistas},)
    else:
      return entrevistas
    
    
@router.get("/{entrevista_id}")
def get_entrevista(entrevista_id: int,request: Request,session: Session = Depends(get_session)):
    entrevista = session.get(Entrevista, entrevista_id)

    if is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/entrevista/entrevista_row.html",
            context={"entrevista": entrevista}
        )

    return entrevista 


@router.post("/")
def create_entrevista(entrevista: EntrevistaCreate,request: Request, session: Session = Depends(get_session)) -> Entrevista:
    entrevista = Entrevista(**entrevista.model_dump())
    entrevista = insert_db_element(session,entrevista)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/entrevista/entrevista_row.html", context={"entrevista": entrevista})
    else:
       return entrevista

       
@router.put("/{entrevista_id}")
def update_entrevista(entrevista_id: int,entrevista_data: EntrevistaUpdate,request: Request,session: Session = Depends(get_session)):
    entrevista = session.get(Entrevista, entrevista_id)

    if not entrevista:
        raise HTTPException(status_code=404)

    entrevista = update_db_element(session, entrevista,entrevista_data)

    if is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/entrevista/entrevista_row.html",
            context={"entrevista": entrevista}
        )

    return entrevista


@router.delete("/{entrevista_id}")
def delete_entrevista(entrevista_id: uuid.UUID, request: Request, session: Session = Depends(get_session)):
    entrevista = session.get(Entrevista, entrevista_id)

    if not entrevista:
        raise HTTPException(status_code=404)

    delete_db_element(session, entrevista)
    if is_htmx(request):
      return Response(status_code=204)

    return {"ok": True}