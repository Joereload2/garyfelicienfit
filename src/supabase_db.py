"""Supabase REST + Storage. Empty keys → disabled, JSON store keeps working."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from envload import get


class SupabaseError(RuntimeError):
    pass


def enabled() -> bool:
    return bool(get("SUPABASE_URL") and get("SUPABASE_SERVICE_ROLE_KEY"))


def _base() -> str:
    return get("SUPABASE_URL").rstrip("/")


def _key() -> str:
    return get("SUPABASE_SERVICE_ROLE_KEY")


def _headers(extra: dict | None = None) -> dict:
    key = _key()
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    if extra:
        h.update(extra)
    return h


def _request(method: str, url: str, body: bytes | None = None, headers: dict | None = None) -> tuple[int, object]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or _headers())
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
            code = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        code = exc.code
        text = raw.decode("utf-8", errors="replace")
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {"message": text}
        raise SupabaseError(f"{code}: {payload}") from exc
    if not raw:
        return code, None
    text = raw.decode("utf-8")
    try:
        return code, json.loads(text)
    except json.JSONDecodeError:
        return code, text


def rest(method: str, table: str, query: str = "", payload: dict | list | None = None, extra_headers: dict | None = None) -> object:
    url = f"{_base()}/rest/v1/{table}"
    if query:
        url += "?" + query
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    _code, data = _request(method, url, body, _headers(extra_headers))
    return data


def get_entitlement_by_token(token: str) -> dict | None:
    rows = rest("GET", "entitlements", "token=eq." + urllib.parse.quote(token) + "&select=*")
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


def get_entitlement_by_payment_ref(payment_ref: str) -> dict | None:
    rows = rest(
        "GET",
        "entitlements",
        "payment_ref=eq." + urllib.parse.quote(payment_ref) + "&select=*",
    )
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


def list_entitlements() -> list[dict]:
    rows = rest("GET", "entitlements", "select=*&order=created_at.desc")
    return rows if isinstance(rows, list) else []


def insert_entitlement(ent: dict) -> dict:
    try:
        rows = rest("POST", "entitlements", payload=ent)
    except SupabaseError as exc:
        if "23505" in str(exc):
            raise ValueError("payment_ref_used") from exc
        raise
    if isinstance(rows, list) and rows:
        return rows[0]
    return ent


def consume_entitlement(token: str, pdf_path: str, pdf_filename: str, submission: dict) -> dict:
    current = get_entitlement_by_token(token)
    if not current:
        raise KeyError("not_found")
    if current.get("status") != "pending":
        raise ValueError("used")
    from datetime import datetime, timezone

    patch = {
        "status": "used",
        "used_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "pdf_path": pdf_path,
        "pdf_filename": pdf_filename,
        "submission": submission,
    }
    rows = rest(
        "PATCH",
        "entitlements",
        "token=eq." + urllib.parse.quote(token) + "&status=eq.pending",
        payload=patch,
    )
    if isinstance(rows, list) and rows:
        return rows[0]
    again = get_entitlement_by_token(token)
    if again and again.get("status") == "used":
        raise ValueError("used")
    raise KeyError("not_found")


def insert_coaching(entry: dict) -> dict:
    rows = rest("POST", "coaching_leads", payload=entry)
    if isinstance(rows, list) and rows:
        return rows[0]
    return entry


def log_mail(entry: dict) -> None:
    try:
        rest("POST", "mail_log", payload=entry)
    except Exception:
        return


def log_payment(entry: dict) -> None:
    try:
        rest("POST", "payments", payload=entry)
    except Exception:
        return


def upload_pdf(filename: str, data: bytes) -> str:
    url = f"{_base()}/storage/v1/object/pdfs/{urllib.parse.quote(filename)}"
    headers = {
        "apikey": _key(),
        "Authorization": f"Bearer {_key()}",
        "Content-Type": "application/pdf",
        "x-upsert": "true",
    }
    _request("POST", url, data, headers)
    return f"storage://pdfs/{filename}"


def download_pdf(filename: str, dest: Path) -> Path:
    url = f"{_base()}/storage/v1/object/pdfs/{urllib.parse.quote(filename)}"
    headers = {
        "apikey": _key(),
        "Authorization": f"Bearer {_key()}",
    }
    req = urllib.request.Request(url, method="GET", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        dest.write_bytes(resp.read())
    return dest
