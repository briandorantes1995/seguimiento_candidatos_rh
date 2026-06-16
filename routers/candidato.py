from fastapi import Depends,APIRouter, Query,Request,HTTPException,Response
from db.models import Candidato,CandidatoUpdate,Puesto, get_session
from sqlmodel import Session, select
from db.crud import delete_db_element,insert_db_element,update_db_element
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from helpers import is_htmx,get_current_user

router = APIRouter(
    prefix="/candidatos",
    tags=["candidatos"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")

@router.get("/form")
def read_candidato_form(request: Request,session: Session = Depends(get_session)):
    puestos = session.exec(select(Puesto)).all()
    return templates.TemplateResponse(request=request, name="candidatos.html" ,context={ "puestos": puestos})


@router.get("/{candidato_id}/edit")
def edit_candidato_form(candidato_id: int,request: Request,session: Session = Depends(get_session)):
    candidato = session.get(Candidato, candidato_id)
    puestos = session.exec(select(Puesto)).all()

    return templates.TemplateResponse(
        request=request,
        name="partials/candidato/candidato_edit_row.html",
        context={"candidato": candidato,"puestos": puestos}
    ) 

@router.get("/")
def read_candidatos(request: Request,session: Session = Depends(get_session),offset: int = 0,limit: int = Query(default=100, le=100)) -> list[Candidato]:
    candidatos = session.exec(select(Candidato).offset(offset).limit(limit)).all()
    if is_htmx(request):
     return templates.TemplateResponse(request=request,name="partials/candidato/candidato_list.html",context={"candidatos": candidatos},)
    else:
      return candidatos
    
    
@router.get("/{candidato_id}")
def get_candidato(candidato_id: int,request: Request,session: Session = Depends(get_session)):
    candidato = session.get(Candidato, candidato_id)

    if is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/candidato/candidato_row.html",
            context={"candidato": candidato}
        )

    return candidato  


@router.post("/")
def create_candidato(candidato: Candidato,request: Request, session: Session = Depends(get_session)) -> Candidato:
    candidato = insert_db_element(session,candidato)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/candidato/candidato_row.html", context={"candidato": candidato})
    else:
       return candidato

       
@router.put("/{candidato_id}")
def update_candidato(candidato_id: int,candidato_data: CandidatoUpdate,request: Request,session: Session = Depends(get_session)):
    candidato = session.get(Candidato, candidato_id)

    if not candidato:
        raise HTTPException(status_code=404)

    candidato = update_db_element(session, candidato, candidato_data)

    if is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/candidato/candidato_row.html",
            context={"candidato": candidato}
        )

    return candidato


@router.delete("/{candidato_id}")
def delete_candidato(candidato_id: int, request: Request, session: Session = Depends(get_session)):
    candidato = session.get(Candidato, candidato_id)

    if not candidato:
        raise HTTPException(status_code=404)

    delete_db_element(session, candidato)
    if is_htmx(request):
      return Response(status_code=204)

    return {"ok": True}