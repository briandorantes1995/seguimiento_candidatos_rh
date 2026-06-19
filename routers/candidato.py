from fastapi import Depends, APIRouter, Query, Request, HTTPException, Response
from db.models import Candidato, CandidatoUpdate, CandidatoCreate, Usuario, get_session
from sqlmodel import Session, select
from db.crud import delete_db_element, insert_db_element, update_db_element
from fastapi.templating import Jinja2Templates
from helpers import is_htmx, get_current_user, check_owner, apply_ownership_filter, delete_response, with_toast

router = APIRouter(
    prefix="/candidatos",
    tags=["candidatos"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/form")
def read_candidato_form(request: Request):
    return templates.TemplateResponse(request=request, name="candidatos.html")


@router.get("/{candidato_id}/edit")
def edit_candidato_form(candidato_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    candidato = session.get(Candidato, candidato_id)
    if not candidato:
        raise HTTPException(status_code=404)
    check_owner(candidato, current_user)

    return templates.TemplateResponse(request=request, name="partials/candidato/candidato_edit_row.html", context={"candidato": candidato})


@router.get("/")
def read_candidatos(request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user), offset: int = 0, limit: int = Query(default=100, le=100)) -> list[Candidato]:
    query = apply_ownership_filter(select(Candidato), Candidato, current_user)
    candidatos = session.exec(query.offset(offset).limit(limit)).all()

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/candidato/candidato_list.html", context={"candidatos": candidatos})
    return candidatos


@router.get("/{candidato_id}")
def get_candidato(candidato_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    candidato = session.get(Candidato, candidato_id)
    if not candidato:
        raise HTTPException(status_code=404)
    check_owner(candidato, current_user)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/candidato/candidato_row.html", context={"candidato": candidato})
    return candidato


@router.post("/")
def create_candidato(candidato_data: CandidatoCreate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)) -> Candidato:
    candidato = Candidato(**candidato_data.model_dump(), created_by=current_user.id)
    candidato = insert_db_element(session, candidato)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/candidato/candidato_row.html", context={"candidato": candidato}),
            "Candidato creado correctamente", "success"
        )
    return candidato


@router.put("/{candidato_id}")
def update_candidato(candidato_id: int, candidato_data: CandidatoUpdate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    candidato = session.get(Candidato, candidato_id)
    if not candidato:
        raise HTTPException(status_code=404)
    check_owner(candidato, current_user)

    candidato = update_db_element(session, candidato, candidato_data)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/candidato/candidato_row.html", context={"candidato": candidato}),
            "Candidato actualizado correctamente", "info"
        )
    return candidato


@router.delete("/{candidato_id}")
def delete_candidato(candidato_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    candidato = session.get(Candidato, candidato_id)
    if not candidato:
        raise HTTPException(status_code=404)
    check_owner(candidato, current_user)

    delete_db_element(session, candidato)

    if is_htmx(request):
        return delete_response()
    return {"ok": True}