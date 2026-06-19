from fastapi import Depends, APIRouter, Query, Request, HTTPException, Response
from db.models import Empresa,Usuario,Candidato,Puesto,Postulacion, PostulacionUpdate, PostulacionCreate, get_session
from db.crud import delete_db_element, insert_db_element, update_db_element
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from helpers import is_htmx, get_current_user, check_owner, apply_ownership_filter, delete_response, with_toast

router = APIRouter(
    prefix="/postulaciones",
    tags=["postulaciones"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/form")
def read_postulacion_form(request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    puestos = session.exec(apply_ownership_filter(select(Puesto), Puesto, current_user)).all()
    candidatos = session.exec(apply_ownership_filter(select(Candidato), Candidato, current_user)).all()
    return templates.TemplateResponse(request=request, name="postulaciones.html", context={"puestos": puestos,"candidatos": candidatos})


@router.get("/{postulacion_id}/edit")
def edit_postulacion_form(postulacion_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    postulacion = session.get(Postulacion, postulacion_id)
    if not postulacion:
        raise HTTPException(status_code=404)
    check_owner(postulacion, current_user)

    puestos = session.exec(apply_ownership_filter(select(Puesto), Puesto, current_user)).all()
    candidatos = session.exec(apply_ownership_filter(select(Candidato), Candidato, current_user)).all()
    return templates.TemplateResponse(request=request, name="partials/postulaciones/postulacion_edit_row.html", context={"postulacion": postulacion,"puestos": puestos,"candidatos": candidatos})


@router.get("/")
def read_postulaciones(request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user), offset: int = 0, limit: int = Query(default=100, le=100)) -> list[Postulacion]:
    query = apply_ownership_filter(select(Postulacion), Postulacion, current_user)
    postulaciones = session.exec(query.offset(offset).limit(limit)).all()

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/postulaciones/postulacion_list.html", context={"postulaciones": postulaciones})
    return postulaciones


@router.get("/{postulacion_id}")
def get_postulacion(postulacion_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    postulacion = session.get(Postulacion, postulacion_id)
    if not postulacion:
        raise HTTPException(status_code=404)
    check_owner(postulacion, current_user)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/postulaciones/postulacion_row.html", context={"postulacion": postulacion})
    return postulacion


@router.post("/")
def create_postulacion(postulacion_data: PostulacionCreate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)) -> Postulacion:
    postulacion = Postulacion(**postulacion_data.model_dump(), created_by=current_user.id)
    postulacion = insert_db_element(session, postulacion)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/postulaciones/postulacion_row.html", context={"postulacion": postulacion}),
            "Postulación creada correctamente", "success"
        )
    return postulacion


@router.put("/{postulacion_id}")
def update_postulacion(postulacion_id: int, postulacion_data: PostulacionUpdate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    postulacion = session.get(Postulacion, postulacion_id)
    if not postulacion:
        raise HTTPException(status_code=404)
    check_owner(postulacion, current_user)

    postulacion = update_db_element(session, postulacion, postulacion_data)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/postulaciones/postulacion_row.html", context={"postulacion": postulacion}),
            "Postulación actualizada correctamente", "info"
        )
    return postulacion


@router.delete("/{postulacion_id}")
def delete_postulacion(postulacion_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    postulacion = session.get(Postulacion, postulacion_id)
    if not postulacion:
        raise HTTPException(status_code=404)
    check_owner(postulacion, current_user)

    delete_db_element(session, postulacion)

    if is_htmx(request):
        return delete_response()
    return {"ok": True}