from fastapi import Depends,APIRouter, Query,Request,HTTPException,Response
from db.models import Empresa,Puesto,PuestoUpdate, get_session
from db.crud import delete_db_element,insert_db_element,update_db_element
from sqlmodel import Session, select
from fastapi.templating import Jinja2Templates
from helpers import is_htmx,get_current_user


router = APIRouter(
    prefix="/puestos",
    tags=["puestos"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")

@router.get("/form")
def read_puesto_form(request: Request,session: Session = Depends(get_session)):
    empresas = session.exec(select(Empresa)).all()
    return templates.TemplateResponse(request=request, name="puesto.html" ,context={ "empresas": empresas})

@router.get("/{puesto_id}/edit")
def edit_puesto_form(puesto_id: int,request: Request,session: Session = Depends(get_session)):
    puesto = session.get(Puesto, puesto_id)
    empresas = session.exec(select(Empresa)).all()

    return templates.TemplateResponse(
        request=request,
        name="partials/puesto_edit_row.html",
        context={"puesto": puesto,"empresas": empresas}
    ) 


@router.get("/")
def read_puestos(request: Request,session: Session = Depends(get_session),offset: int = 0,limit: int = Query(default=100, le=100)) -> list[Puesto]:
    puestos = session.exec(select(Puesto).offset(offset).limit(limit)).all()
    if is_htmx(request):
     return templates.TemplateResponse(request=request,name="partials/puesto/puesto_list.html",context={"puestos": puestos},)
    else:
      return puestos
    
@router.get("/{puesto_id}")
def get_puesto(puesto_id: int,request: Request,session: Session = Depends(get_session)):
    puesto = session.get(Puesto, puesto_id)

    if is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/puesto/puesto_row.html",
            context={"puesto": puesto}
        )

    return empresa     
    
@router.post("/")
def create_puesto(puesto: Puesto,request: Request, session: Session = Depends(get_session)) -> Puesto:
    insert_db_element(session,puesto)
    if is_htmx(request):
        return templates.TemplateResponse(request=request, name="partials/puesto/puesto_row.html", context={"puesto": puesto})
    else:
       return puesto
   
    

@router.put("/{puesto_id}")
def update_puesto(puesto_id: int,puesto_data: PuestoUpdate,request: Request,session: Session = Depends(get_session)):
    puesto = session.get(Puesto, puesto_id)
    if not puesto:
       raise HTTPException(status_code=404)
    puesto = update_db_element(session, puesto, puesto_data)

    if is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/puesto/puesto_row.html",
            context={"puesto": puesto}
        )

    return puesto

@router.delete("/{puesto_id}")
def delete_puesto(puesto_id: int,request: Request,session: Session = Depends(get_session)):
   puesto = session.get(Puesto,puesto_id)
   if not puesto:
    raise HTTPException(status_code=404)
   delete_db_element(session, puesto)
   if is_htmx(request):
      return Response(status_code=204)

   return {"ok": True}
