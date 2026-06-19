import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from fastapi import UploadFile, HTTPException

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
BUCKET_NAME = "candidatos-docs"

_supabase = None


def get_supabase():
    global _supabase
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise HTTPException(status_code=500, detail="Supabase no configurado (SUPABASE_URL y SUPABASE_ANON_KEY)")
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase


async def upload_document(file: UploadFile, candidato_id: int) -> str:
    ext = os.path.splitext(file.filename or "file")[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    storage_path = f"{candidato_id}/{unique_name}"

    content = await file.read()

    sup = get_supabase()
    sup.storage.from_(BUCKET_NAME).upload(
        path=storage_path,
        file=content,
        file_options={"content-type": file.content_type or "application/octet-stream"},
    )

    public_url = sup.storage.from_(BUCKET_NAME).get_public_url(storage_path)
    return public_url


def delete_document(file_url: str):
    parts = file_url.split(f"{BUCKET_NAME}/")
    if len(parts) < 2:
        return
    storage_path = parts[1]
    sup = get_supabase()
    sup.storage.from_(BUCKET_NAME).remove([storage_path])


AVATAR_BUCKET = "avatar"


async def upload_avatar(file: UploadFile, user_id: str) -> str:
    ext = os.path.splitext(file.filename or "file")[1]
    storage_path = f"{user_id}/avatar{ext}"

    content = await file.read()

    sup = get_supabase()

    for old_ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        try:
            sup.storage.from_(AVATAR_BUCKET).remove([f"{user_id}/avatar{old_ext}"])
        except Exception:
            pass

    sup.storage.from_(AVATAR_BUCKET).upload(
        path=storage_path,
        file=content,
        file_options={"content-type": file.content_type or "image/png"},
    )

    public_url = sup.storage.from_(AVATAR_BUCKET).get_public_url(storage_path)
    return public_url
