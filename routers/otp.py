import bcrypt
import base64
import io
import uuid
import qrcode
import pyotp
import os
from jose import jwt
from fastapi import Depends, APIRouter, Request, HTTPException, Response
from db.models import Usuario, get_session
from sqlmodel import Session
from fastapi.templating import Jinja2Templates
from fastapi_csrf_protect import CsrfProtect
from helpers import get_current_user, get_admin_or_owner, is_htmx, with_toast
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
OTP_ISSUER = "CandidatosRH"

router = APIRouter(
    prefix="/otp",
    tags=["otp"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="templates")


def generate_qr_b64(provisioning_uri: str) -> str:
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _get_qr_context(user: Usuario):
    if not user.otp_secret:
        return {}
    totp = pyotp.TOTP(user.otp_secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name=OTP_ISSUER)
    qr_b64 = generate_qr_b64(uri)
    return {"secret": user.otp_secret, "qr_b64": qr_b64}


@router.get("/section")
def otp_section(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
):
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(
        request=request,
        name="partials/otp/otp_section.html",
        context={"user": current_user, "csrf_token": csrf_token}
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/generate")
async def generate_otp(
    request: Request,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)

    secret = pyotp.random_base32()
    current_user.otp_secret = secret
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    qr_ctx = _get_qr_context(current_user)
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(
        request=request,
        name="partials/otp/otp_verify.html",
        context={"user": current_user, "csrf_token": csrf_token, **qr_ctx}
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/verify-enable")
async def verify_enable_otp(
    request: Request,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)
    form = await request.form()
    otp_code = form.get("otp_code")

    if not otp_code or not current_user.otp_secret:
        qr_ctx = _get_qr_context(current_user)
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        resp = templates.TemplateResponse(
            request=request,
            name="partials/otp/otp_verify.html",
            context={"user": current_user, "csrf_token": csrf_token, "error": "Código inválido", **qr_ctx}
        )
        csrf_protect.set_csrf_cookie(signed_token, resp)
        return resp

    totp = pyotp.TOTP(current_user.otp_secret)
    if not totp.verify(otp_code):
        qr_ctx = _get_qr_context(current_user)
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        resp = templates.TemplateResponse(
            request=request,
            name="partials/otp/otp_verify.html",
            context={"user": current_user, "csrf_token": csrf_token, "error": "Código incorrecto. Intenta de nuevo.", **qr_ctx}
        )
        csrf_protect.set_csrf_cookie(signed_token, resp)
        return resp

    current_user.otp_enabled = True
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    resp = templates.TemplateResponse(
        request=request,
        name="partials/otp/otp_section.html",
        context={"user": current_user, "csrf_token": csrf_token, "success": "2FA activado correctamente"}
    )
    csrf_protect.set_csrf_cookie(signed_token, resp)
    return resp


@router.post("/disable")
async def disable_otp(
    request: Request,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)
    form = await request.form()
    password = form.get("password")

    if not password or not bcrypt.checkpw(password.encode(), current_user.password.encode()):
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        resp = templates.TemplateResponse(
            request=request,
            name="partials/otp/otp_section.html",
            context={"user": current_user, "csrf_token": csrf_token, "error": "Contraseña incorrecta"}
        )
        csrf_protect.set_csrf_cookie(signed_token, resp)
        return resp

    current_user.otp_enabled = False
    current_user.otp_secret = None
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    resp = templates.TemplateResponse(
        request=request,
        name="partials/otp/otp_section.html",
        context={"user": current_user, "csrf_token": csrf_token, "success": "2FA desactivado correctamente"}
    )
    csrf_protect.set_csrf_cookie(signed_token, resp)
    return resp


@router.post("/admin-disable/{usuario_id}")
async def admin_disable_otp(
    usuario_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_admin_or_owner),
    csrf_protect: CsrfProtect = Depends(),
):
    await csrf_protect.validate_csrf(request)
    target = session.get(Usuario, uuid.UUID(usuario_id))
    if not target:
        raise HTTPException(status_code=404)

    target.otp_enabled = False
    target.otp_secret = None
    session.add(target)
    session.commit()
    session.refresh(target)

    if is_htmx(request):
        return with_toast(
            templates.TemplateResponse(
                request=request,
                name="partials/usuarios/usuario_row.html",
                context={"usuario": target}
            ),
            "2FA deshabilitado para el usuario", "info"
        )
    return {"ok": True}
