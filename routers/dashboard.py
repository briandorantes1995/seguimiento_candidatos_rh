from datetime import date, datetime
from fastapi import Depends, APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
from db.models import Candidato, Empresa, Puesto, Postulacion, Entrevista, Usuario, get_session
from helpers import get_current_user, apply_ownership_filter

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)

templates = Jinja2Templates(directory="templates")


@router.get("/")
def dashboard_page(request: Request, current_user: Usuario = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"current_user": current_user})


@router.get("/data")
def dashboard_data(
    request: Request,
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
):
    start_date = date.fromisoformat(start) if start else date(2000, 1, 1)
    end_date = date.fromisoformat(end) if end else date(2100, 1, 1)

    def count_filtered(model, date_col):
        q = select(func.count(model.id))
        if current_user.user_type.value not in ("admin", "owner"):
            q = q.where(model.created_by == current_user.id)
        q = q.where(date_col >= start_date).where(date_col <= end_date)
        return session.exec(q).one()

    total_candidatos = count_filtered(Candidato, Candidato.created_at)
    total_empresas = count_filtered(Empresa, Empresa.created_at)
    total_puestos = count_filtered(Puesto, Puesto.created_at)
    total_postulaciones = count_filtered(Postulacion, Postulacion.created_at)
    total_entrevistas = count_filtered(Entrevista, Entrevista.created_at)

    # Postulaciones por estado
    status_q = select(Postulacion.status, func.count(Postulacion.id))
    if current_user.user_type.value not in ("admin", "owner"):
        status_q = status_q.where(Postulacion.created_by == current_user.id)
    status_q = status_q.where(Postulacion.created_at >= start_date).where(Postulacion.created_at <= end_date)
    status_q = status_q.group_by(Postulacion.status)
    statuses = session.exec(status_q).all()

    # Postulaciones por mes (portable: no strftime)
    from collections import defaultdict
    month_q = select(Postulacion.created_at)
    if current_user.user_type.value not in ("admin", "owner"):
        month_q = month_q.where(Postulacion.created_by == current_user.id)
    month_q = month_q.where(Postulacion.created_at >= start_date).where(Postulacion.created_at <= end_date)
    dates = session.exec(month_q).all()
    month_counts = defaultdict(int)
    for dt in dates:
        key = dt.strftime("%Y-%m") if dt else "Sin fecha"
        month_counts[key] += 1
    months = [{"month": k, "count": v} for k, v in sorted(month_counts.items())]

    return {
        "kpi": {
            "candidatos": total_candidatos,
            "empresas": total_empresas,
            "puestos": total_puestos,
            "postulaciones": total_postulaciones,
            "entrevistas": total_entrevistas,
        },
        "statuses": [{"name": s[0] or "Sin estado", "count": s[1]} for s in statuses],
        "months": months,
    }
