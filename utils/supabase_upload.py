# utils/supabase_upload.py
import os
import io
import uuid
import mimetypes
from typing import Optional
from urllib.parse import urlparse

from supabase import create_client

# --- ENV (server-side only) ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
# Gunakan SERVICE ROLE key HANYA di server (aman di Django)
SUPABASE_KEY = os.environ["SUPABASE_ROLE_KEY"]
BUCKET = os.environ.get("SUPABASE_BUCKET", "upload")

# --- Singleton client (lazy) ---
_supabase_client = None
def _get_supabase():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client

# --- FileOptions (v2) optional ---
try:
    from supabase.lib.storage import FileOptions  # supabase-py v2
except Exception:
    FileOptions = None  # fallback untuk v1


def _normalize_public_url(public_url_obj) -> str:
    """
    SDK v2 mengembalikan dict {'publicUrl': '...'}, sedangkan beberapa
    versi/adapter bisa langsung string. Samakan jadi string.
    """
    if isinstance(public_url_obj, dict):
        # v2
        if "publicUrl" in public_url_obj:
            return public_url_obj["publicUrl"]
        if "signedURL" in public_url_obj:
            return public_url_obj["signedURL"]
    return str(public_url_obj)

def upload_bytes_and_get_url(
    *, content: bytes, filename: str, folder: str = "qr", bucket: Optional[str] = None,
    content_type: Optional[str] = None, upsert: bool = True
) -> str:
    sb = _get_supabase()
    bucket = bucket or BUCKET

    base, ext = os.path.splitext(filename)
    if not ext:
        ext = ".bin"
    filename = f"{base}{ext.lower()}"
    path = f"{folder.rstrip('/')}/{filename}"

    mime = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # --- Upload ---
    try:
        if FileOptions:  # v2
            opts = FileOptions(content_type=mime, upsert=upsert)
            # v2: kirim BYTES langsung
            sb.storage.from_(bucket).upload(path=path, file=content, file_options=opts)
        else:
            # v1 sebagian besar juga mau BYTES langsung
            sb.storage.from_(bucket).upload(
                path,
                content,  # <-- BYTES, bukan BytesIO
                {"content-type": mime, "upsert": "true" if upsert else "false"},
            )
    except TypeError:
        # Beberapa adapter lama butuh file-like object (punya .read/.name)
        bio = io.BytesIO(content)
        bio.name = filename
        if FileOptions:
            opts = FileOptions(content_type=mime, upsert=upsert)
            sb.storage.from_(bucket).upload(path=path, file=bio, file_options=opts)
        else:
            sb.storage.from_(bucket).upload(
                path, bio, {"content-type": mime, "upsert": "true" if upsert else "false"}
            )

    public_url_obj = sb.storage.from_(bucket).get_public_url(path)
    return _normalize_public_url(public_url_obj)



def upload_file_and_get_url(django_file, folder: str = "qr", bucket: Optional[str] = None) -> str:
    """
    Upload UploadedFile (request.FILES['...']) ke Supabase, return PUBLIC URL.
    """
    # nama unik + ekstensi asli
    _, ext = os.path.splitext(getattr(django_file, "name", "") or "")
    ext = (ext or ".bin").lower()
    filename = f"{uuid.uuid4().hex}{ext}"

    content = django_file.read()  # -> bytes
    mime, _ = mimetypes.guess_type(filename)
    mime = mime or "application/octet-stream"

    return upload_bytes_and_get_url(
        content=content,
        filename=filename,
        folder=folder,
        bucket=bucket,
        content_type=mime,
        upsert=True,
    )


def _extract_path_from_public_url(public_url: str, expected_bucket: str) -> str:
    """
    Ambil 'folder/file.ext' dari public URL Supabase:
    https://<proj>.supabase.co/storage/v1/object/public/<bucket>/<folder>/<file>
    """
    if not public_url:
        raise ValueError("public_url kosong")

    parsed = urlparse(public_url)
    parts = parsed.path.split("/")  # ['', 'storage', 'v1', 'object', 'public', '<bucket>', 'qr', 'abc.png']

    try:
        i_public = parts.index("public")
        bucket = parts[i_public + 1]
        if bucket != expected_bucket:
            raise ValueError(f"Bucket URL ({bucket}) != expected ({expected_bucket})")
        remainder = parts[i_public + 2 :]
        path = "/".join(p for p in remainder if p)
        if not path:
            raise ValueError("Path file kosong setelah bucket.")
        return path
    except (ValueError, IndexError) as e:
        raise ValueError(f"Gagal parse path dari public_url: {e}")


def delete_file_by_public_url(public_url: str, bucket: Optional[str] = None) -> None:
    """
    Hapus file berdasarkan public URL. Raise exception bila gagal.
    """
    sb = _get_supabase()
    bucket = bucket or BUCKET
    path = _extract_path_from_public_url(public_url, expected_bucket=bucket)
    # remove() menerima list path
    res = sb.storage.from_(bucket).remove([path])
    # Optional: cek error dari adapter tertentu
    if hasattr(res, "error") and res.error:
        raise RuntimeError(f"Gagal hapus file: {res.error}")
