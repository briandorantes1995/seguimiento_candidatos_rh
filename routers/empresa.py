from fastapi import Depends,APIRouter, Query,Request,HTTPException,Response
from db.models import Empresa,EmpresaUpdate, get_session
from db.crud import delete_db_element,insert_db_element,update_db_element
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from helpers import is_htmx,get_current_user


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
def edit_empresa_form(empresa_id: int,request: Request,session: Session = Depends(get_session)):
    empresa = session.get(Empresa, empresa_id)

    return templates.TemplateResponse(
        request=request,
        name="partials/empresa_edit_row.html",
        context={"empresa": empresa}
    ) 

@router.get("/")
def read_empresas(request: Request,session: Session = Depends(get_session),offset: int = 0,limit: int = Query(default=100, le=100)) -> list[Empresa]:
    empresas = session.exec(select(Empresa).offset(offset).limit(limit)).all()
    if is_htmx(request):
     return templates.TemplateResponse(request=request,name="partials/empresa_list.html",context={"empresas": empresas},)
    else:
      return empresas
    
@router.get("/{empresa_id}")
def get_empresa(empresa_id: int,request: Request,session: Session = Depends(get_session)):
    empresa = session.get(Empresa, empresa_id)

    if is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/empresa_row.html",
            context={"empresa": empresa}
        )

    return empresa    


@router.post("/")
def create_empresa(empresa: Empresa,request: Request, session: Session = Depends(get_session)) -> Empresa:
    empresa = insert_db_element(session,empresa)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/empresa_row.html", context={"empresa": empresa})
    else:
       return empresa

       
@router.put("/{empresa_id}")
def update_empresa(empresa_id: int,empresa_data: EmpresaUpdate,request: Request,session: Session = Depends(get_session)):
    empresa = session.get(Empresa, empresa_id)

    if not empresa:
        raise HTTPException(status_code=404)

    empresa = update_db_element(session, empresa, empresa_data)

    if is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/empresa_row.html",
            context={"empresa": empresa}
        )

    return empresa


@router.delete("/{empresa_id}")
def delete_empresa(empresa_id: int, request: Request, session: Session = Depends(get_session)):
    empresa = session.get(Empresa, empresa_id)

    if not empresa:
        raise HTTPException(status_code=404)

    delete_db_element(session, empresa)
    if is_htmx(request):
      return Response(status_code=204)

    return {"ok": True}
   