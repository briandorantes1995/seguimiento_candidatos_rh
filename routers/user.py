from fastapi import Depends, APIRouter, Request, HTTPException, Response
from db.models import Usuario, UsuarioUpdate, AdminUpdate, get_session
from db.crud import update_db_element, delete_db_element
from sqlmodel import Session, select
import uuid
from fastapi.templating import Jinja2Templates
from helpers import is_htmx, get_current_user, get_admin_user

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/perfil")
def read_perfil(request: Request, current_user: Usuario = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="perfil.html", context={"current_user": current_user})


@router.get("/form", dependencies=[Depends(get_admin_user)])
def read_usuarios_form(request: Request):
    return templates.TemplateResponse(request=request, name="usuarios.html")


@router.get("/", dependencies=[Depends(get_admin_user)])
def read_usuarios(request: Request, session: Session = Depends(get_session)):
    usuarios = session.exec(select(Usuario)).all()
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_list.html", context={"usuarios": usuarios})
    return usuarios


@router.get("/{usuario_id}/edit", dependencies=[Depends(get_admin_user)])
def edit_usuario_form(usuario_id: str, request: Request, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, uuid.UUID(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_edit_row.html", context={"usuario": usuario})


@router.get("/{usuario_id}", dependencies=[Depends(get_admin_user)])
def get_usuario(usuario_id: str, request: Request, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, uuid.UUID(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_row.html", context={"usuario": usuario})
    return usuario


@router.put("/me")
def update_perfil(usuario_data: UsuarioUpdate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    usuario = update_db_element(session, current_user, usuario_data)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_perfil.html", context={"usuario": usuario})
    return usuario


@router.put("/{usuario_id}", dependencies=[Depends(get_admin_user)])
def update_usuario(usuario_id: str, usuario_data: AdminUpdate, request: Request, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, uuid.UUID(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404)
    usuario = update_db_element(session, usuario, usuario_data)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_row.html", context={"usuario": usuario})
    return usuario


@router.delete("/{usuario_id}", dependencies=[Depends(get_admin_user)])
def delete_usuario(usuario_id: str, request: Request, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, uuid.UUID(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404)
    delete_db_element(session, usuario)
    if is_htmx(request):
        return Response(status_code=204)
    return {"ok": True}