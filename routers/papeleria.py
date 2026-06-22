from fastapi import Depends, APIRouter, Query, Request, HTTPException, Response, UploadFile, Form, File
from db.models import Papeleria, PapeleriaCreate, PapeleriaUpdate, Candidato, Usuario, DocumentType, get_session
from db.crud import delete_db_element, insert_db_element, update_db_element
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from fastapi_csrf_protect import CsrfProtect
from helpers import is_htmx, get_current_user, check_owner, apply_ownership_filter, delete_response, with_toast, utc_now
from supabase_helper import upload_document, delete_document
import uuid

router = APIRouter(
    prefix="/papeleria",
    tags=["papeleria"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


@router.get("/candidato/{candidato_id}")
async def papeleria_por_candidato(candidato_id: int, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user), csrf_protect: CsrfProtect = Depends()):
    candidato = session.get(Candidato, candidato_id)
    if not candidato:
        raise HTTPException(status_code=404)

    query = apply_ownership_filter(select(Papeleria), Papeleria, current_user)
    papeleria = session.exec(query.where(Papeleria.candidato_id == candidato_id)).all()
    document_types = list(DocumentType)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/papeleria/papeleria_list.html", context={"papeleria": papeleria})

    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(request=request, name="papeleria.html", context={"candidato": candidato, "papeleria": papeleria, "document_types": document_types, "csrf_token": csrf_token})
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/upload")
async def upload_papeleria(
    candidato_id: int = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    request: Request = None,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)
    candidato = session.get(Candidato, candidato_id)
    if not candidato:
        raise HTTPException(status_code=404)
    check_owner(candidato, current_user)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo requerido")

    file_url = await upload_document(file, candidato_id)

    papeleria = Papeleria(
        document_type=document_type,
        file_name=file.filename,
        file_url=file_url,
        candidato_id=candidato_id,
        created_by=current_user.id,
    )
    insert_db_element(session, papeleria)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/papeleria/papeleria_row.html", context={"doc": papeleria}),
            "Documento subido correctamente", "success"
        )
    return papeleria


@router.get("/{papeleria_id}/edit")
async def edit_papeleria_form(papeleria_id: str, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user), csrf_protect: CsrfProtect = Depends()):
    papeleria = session.get(Papeleria, uuid.UUID(papeleria_id))
    if not papeleria:
        raise HTTPException(status_code=404)
    check_owner(papeleria, current_user)
    document_types = list(DocumentType)
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(request=request, name="partials/papeleria/papeleria_edit_row.html", context={"doc": papeleria, "document_types": document_types, "csrf_token": csrf_token})
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.get("/{papeleria_id}")
def get_papeleria(papeleria_id: str, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    papeleria = session.get(Papeleria, uuid.UUID(papeleria_id))
    if not papeleria:
        raise HTTPException(status_code=404)
    check_owner(papeleria, current_user)

    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/papeleria/papeleria_row.html", context={"doc": papeleria})
    return papeleria


@router.put("/{papeleria_id}/replace")
async def replace_papeleria(
    papeleria_id: str,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(None),
    request: Request = None,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)
    papeleria = session.get(Papeleria, uuid.UUID(papeleria_id))
    if not papeleria:
        raise HTTPException(status_code=404)
    check_owner(papeleria, current_user)

    papeleria.document_type = document_type

    if file and file.filename:
        delete_document(papeleria.file_url)
        new_url = await upload_document(file, papeleria.candidato_id)
        papeleria.file_url = new_url
        papeleria.file_name = file.filename

    papeleria.updated_at = utc_now()
    session.add(papeleria)
    session.commit()
    session.refresh(papeleria)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/papeleria/papeleria_row.html", context={"doc": papeleria}),
            "Documento reemplazado correctamente", "info"
        )
    return papeleria


@router.post("/")
async def create_papeleria(papeleria_data: PapeleriaCreate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user), csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    papeleria = Papeleria(**papeleria_data.model_dump(), created_by=current_user.id)
    papeleria = insert_db_element(session, papeleria)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/papeleria/papeleria_row.html", context={"doc": papeleria}),
            "Documento creado correctamente", "success"
        )
    return papeleria


@router.put("/{papeleria_id}")
async def update_papeleria(papeleria_id: str, papeleria_data: PapeleriaUpdate, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user), csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    papeleria = session.get(Papeleria, uuid.UUID(papeleria_id))
    if not papeleria:
        raise HTTPException(status_code=404)
    check_owner(papeleria, current_user)

    papeleria = update_db_element(session, papeleria, papeleria_data)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(request=request, name="partials/papeleria/papeleria_row.html", context={"doc": papeleria}),
            "Documento actualizado correctamente", "info"
        )
    return papeleria


@router.delete("/{papeleria_id}")
def delete_papeleria(papeleria_id: str, request: Request, session: Session = Depends(get_session), current_user: Usuario = Depends(get_current_user)):
    papeleria = session.get(Papeleria, uuid.UUID(papeleria_id))
    if not papeleria:
        raise HTTPException(status_code=404)
    check_owner(papeleria, current_user)

    delete_document(papeleria.file_url)
    delete_db_element(session, papeleria)

    if is_htmx(request):
        return delete_response()
    return {"ok": True}
