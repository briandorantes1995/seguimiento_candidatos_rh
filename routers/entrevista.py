import uuid
from fastapi import Depends, APIRouter, Query, Request, HTTPException, Response
from db.models import Candidato, Entrevista, EntrevistaUpdate, EntrevistaCreate, Usuario, DocumentType, get_session
from sqlmodel import Session, select
from db.crud import delete_db_element, insert_db_element, update_db_element
from fastapi.templating import Jinja2Templates
from helpers import is_htmx, get_current_user, check_owner, apply_ownership_filter, delete_response, with_toast

router = APIRouter(
    prefix="/entrevistas",
    tags=["entrevistas"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/form")
def read_entrevista_form(request: Request):
    return templates.TemplateResponse(request=request, name="entrevista.html")


@router.get("/postulacion/{postulacion_id}")
def entrevistas_por_postulacion(postulacion_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    from db.models import Postulacion
    postulacion = session.get(Postulacion, postulacion_id)
    if not postulacion:
        raise HTTPException(status_code=404)
    check_owner(postulacion, current_user)

    query = apply_ownership_filter(select(Entrevista), Entrevista, current_user)
    entrevistas = session.exec(query.where(Entrevista.postulacion_id == postulacion_id)).all()

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/entrevista/entrevista_list.html", context={"entrevistas": entrevistas})

    document_types = list(DocumentType)
    return templates.TemplateResponse(request=request, name="candidato.html", context={"postulacion": postulacion, "postulacion_id": postulacion_id, "document_types": document_types})


@router.get("/")
def read_entrevistas(request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user), offset: int = 0, limit: int = Query(default=100, le=100)) -> list[Entrevista]:
    query = apply_ownership_filter(select(Entrevista), Entrevista, current_user)
    entrevistas = session.exec(query.offset(offset).limit(limit)).all()

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/entrevista/entrevista_list.html", context={"entrevistas": entrevistas})
    return entrevistas


@router.get("/{entrevista_id}/edit")
def edit_entrevista_form(entrevista_id: uuid.UUID, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    entrevista = session.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404)
    check_owner(entrevista, current_user)
    return templates.TemplateResponse(request=request, name="partials/entrevista/entrevista_edit_row.html", context={"entrevista": entrevista})


@router.get("/{entrevista_id}")
def get_entrevista(entrevista_id: uuid.UUID, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    entrevista = session.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404)
    check_owner(entrevista, current_user)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/entrevista/entrevista_row.html", context={"entrevista": entrevista})
    return entrevista


@router.post("/")
def create_entrevista(entrevista_data: EntrevistaCreate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)) -> Entrevista:
    entrevista = Entrevista(**entrevista_data.model_dump(), created_by=current_user.id)
    entrevista = insert_db_element(session, entrevista)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/entrevista/entrevista_row.html", context={"entrevista": entrevista}),
            "Entrevista creada correctamente", "success"
        )
    return entrevista


@router.put("/{entrevista_id}")
def update_entrevista(entrevista_id: uuid.UUID, entrevista_data: EntrevistaUpdate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    entrevista = session.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404)
    check_owner(entrevista, current_user)

    entrevista = update_db_element(session, entrevista, entrevista_data)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/entrevista/entrevista_row.html", context={"entrevista": entrevista}),
            "Entrevista actualizada correctamente", "info"
        )
    return entrevista


@router.delete("/{entrevista_id}")
def delete_entrevista(entrevista_id: uuid.UUID, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    entrevista = session.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404)
    check_owner(entrevista, current_user)

    delete_db_element(session, entrevista)

    if is_htmx(request):
        return delete_response()
    return {"ok": True}