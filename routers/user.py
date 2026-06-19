import bcrypt
from fastapi import Depends, APIRouter, Request, HTTPException, Response, UploadFile, File
from db.models import Usuario, UsuarioUpdate, AdminUpdate, UsuarioCreate, PasswordChange, UserType, get_session
from db.crud import insert_db_element, update_db_element, delete_db_element
from sqlmodel import Session, select
import uuid
from fastapi.templating import Jinja2Templates
from helpers import is_htmx, get_current_user, get_admin_or_owner, get_owner_user, delete_response, with_toast, utc_now
from supabase_helper import upload_avatar

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/perfil")
def read_perfil(request: Request, current_user: Usuario = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="perfil.html", context={"current_user": current_user})


@router.get("/form")
def read_usuarios_form(request: Request, current_user: Usuario = Depends(get_admin_or_owner)):
    return templates.TemplateResponse(request=request, name="usuarios.html", context={"current_user": current_user})


@router.get("/")
def read_usuarios(request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_admin_or_owner)):
    query = select(Usuario)
    if current_user.user_type == UserType.ADMIN:
        query = query.where(Usuario.user_type == UserType.RECRUITER)
    usuarios = session.exec(query).all()
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_list.html", context={"usuarios": usuarios})
    return usuarios


@router.get("/{usuario_id}/edit")
def edit_usuario_form(usuario_id: str, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_admin_or_owner)):
    usuario = session.get(Usuario, uuid.UUID(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404)
    _check_user_edit_permission(current_user, usuario)
    return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_edit_row.html", context={"usuario": usuario})


@router.get("/{usuario_id}")
def get_usuario(usuario_id: str, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_admin_or_owner)):
    usuario = session.get(Usuario, uuid.UUID(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_row.html", context={"usuario": usuario})
    return usuario


def _check_user_edit_permission(current_user: Usuario, target: Usuario):
    if current_user.user_type == UserType.OWNER:
        return
    if current_user.user_type == UserType.ADMIN:
        if target.user_type != UserType.RECRUITER:
            raise HTTPException(status_code=403, detail="Los admins solo pueden editar reclutadores")
        return
    raise HTTPException(status_code=403)


@router.post("/")
def create_usuario(usuario_data: UsuarioCreate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_owner_user)):
    existing = session.exec(select(Usuario).where(Usuario.email == usuario_data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    hashed = bcrypt.hashpw(usuario_data.password.encode(), bcrypt.gensalt()).decode()
    usuario = Usuario(
        name=usuario_data.name,
        email=usuario_data.email,
        password=hashed,
        user_type=usuario_data.user_type,
    )
    insert_db_element(session, usuario)
    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/usuarios/usuario_row.html", context={"usuario": usuario}),
            "Usuario creado correctamente", "success"
        )
    return usuario


@router.put("/me")
def update_perfil(usuario_data: UsuarioUpdate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    usuario = update_db_element(session, current_user, usuario_data)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_perfil.html", context={"usuario": usuario})
    return usuario


@router.post("/me/avatar")
async def upload_perfil_avatar(
    file: UploadFile = File(...),
    request: Request = None,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo requerido")

    url = await upload_avatar(file, str(current_user.id))
    current_user.avatar = url
    current_user.updated_at = utc_now()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_perfil.html", context={"usuario": current_user, "success": "Avatar actualizado"})
    return {"avatar": url}


@router.put("/me/password")
def change_password(password_data: PasswordChange, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    if not bcrypt.checkpw(password_data.current_password.encode(), current_user.password.encode()):
        if is_htmx(request):
            return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_perfil.html", context={"usuario": current_user, "error": "Contraseña actual incorrecta"})
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    current_user.password = bcrypt.hashpw(password_data.new_password.encode(), bcrypt.gensalt()).decode()
    current_user.updated_at = utc_now()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/usuarios/usuario_perfil.html", context={"usuario": current_user, "success": "Contraseña actualizada correctamente"})
    return {"ok": True}


@router.put("/{usuario_id}")
def update_usuario(usuario_id: str, usuario_data: AdminUpdate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_admin_or_owner)):
    usuario = session.get(Usuario, uuid.UUID(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404)
    _check_user_edit_permission(current_user, usuario)

    data = usuario_data.model_dump(exclude_unset=True)

    if data.get("password"):
        usuario.password = bcrypt.hashpw(data.pop("password").encode(), bcrypt.gensalt()).decode()

    for key, value in data.items():
        setattr(usuario, key, value)

    usuario.updated_at = utc_now()
    session.add(usuario)
    session.commit()
    session.refresh(usuario)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/usuarios/usuario_row.html", context={"usuario": usuario}),
            "Usuario actualizado correctamente", "info"
        )
    return usuario


@router.delete("/{usuario_id}")
def delete_usuario(usuario_id: str, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_admin_or_owner)):
    usuario = session.get(Usuario, uuid.UUID(usuario_id))
    if not usuario:
        raise HTTPException(status_code=404)
    _check_user_edit_permission(current_user, usuario)
    delete_db_element(session, usuario)
    if is_htmx(request):
        return delete_response()
    return {"ok": True}