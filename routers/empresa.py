from fastapi import Depends, APIRouter, Query, Request, HTTPException, Response
from db.models import Empresa, EmpresaUpdate, EmpresaCreate, Usuario, get_session
from db.crud import delete_db_element, insert_db_element, update_db_element
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from helpers import is_htmx, get_current_user, check_owner, apply_ownership_filter

router = APIRouter(
    prefix="/empresas",
    tags=["empresas"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/form")
def read_empresa_form(request: Request):
    return templates.TemplateResponse(request=request, name="empresa.html")


@router.get("/{empresa_id}/edit")
def edit_empresa_form(empresa_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    empresa = session.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404)
    check_owner(empresa, current_user)

    return templates.TemplateResponse(request=request, name="partials/empresa/empresa_edit_row.html", context={"empresa": empresa})


@router.get("/")
def read_empresas(request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user), offset: int = 0, limit: int = Query(default=100, le=100)) -> list[Empresa]:
    query = apply_ownership_filter(select(Empresa), Empresa, current_user)
    empresas = session.exec(query.offset(offset).limit(limit)).all()

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/empresa/empresa_list.html", context={"empresas": empresas})
    return empresas


@router.get("/{empresa_id}")
def get_empresa(empresa_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    empresa = session.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404)
    check_owner(empresa, current_user)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/empresa/empresa_row.html", context={"empresa": empresa})
    return empresa


@router.post("/")
def create_empresa(empresa_data: EmpresaCreate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)) -> Empresa:
    empresa = Empresa(**empresa_data.model_dump(), created_by=current_user.id)
    empresa = insert_db_element(session, empresa)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/empresa/empresa_row.html", context={"empresa": empresa})
    return empresa


@router.put("/{empresa_id}")
def update_empresa(empresa_id: int, empresa_data: EmpresaUpdate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    empresa = session.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404)
    check_owner(empresa, current_user)

    empresa = update_db_element(session, empresa, empresa_data)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/empresa/empresa_row.html", context={"empresa": empresa})
    return empresa


@router.delete("/{empresa_id}")
def delete_empresa(empresa_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    empresa = session.get(Empresa, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404)
    check_owner(empresa, current_user)

    delete_db_element(session, empresa)

    if is_htmx(request):
        return Response(status_code=204)
    return {"ok": True}