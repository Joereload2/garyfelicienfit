"""Entitlements store: SQLite by default (free). Supabase if keys are set."""

from __future__ import annotations

import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from envload import ROOT
import sqlite_db
import supabase_db

DATA_DIR = ROOT / "data"
STORE_PATH = DATA_DIR / "store.json"
DB_PATH = DATA_DIR / "planfit.db"
PDF_DIR = DATA_DIR / "pdfs"
OUTBOX_DIR = DATA_DIR / "outbox"

_lock = __import__("threading").RLock()


def configure_paths(root: Path | None = None) -> None:
    global DATA_DIR, STORE_PATH, DB_PATH, PDF_DIR, OUTBOX_DIR
    override = (os.environ.get("PLANFIT_DATA_DIR") or "").strip()
    DATA_DIR = Path(root) if root is not None else (Path(override) if override else ROOT / "data")
    STORE_PATH = DATA_DIR / "store.json"
    DB_PATH = DATA_DIR / "planfit.db"
    PDF_DIR = DATA_DIR / "pdfs"
    OUTBOX_DIR = DATA_DIR / "outbox"
    sqlite_db.init(DB_PATH)


configure_paths()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    sqlite_db.init(DB_PATH)
    sqlite_db.import_json_if_empty(STORE_PATH)


def get_by_token(token: str) -> dict | None:
    if supabase_db.enabled():
        return supabase_db.get_entitlement_by_token(token)
    ensure_dirs()
    with _lock:
        return sqlite_db.get_entitlement_by_token(token)


def get_by_payment_ref(payment_ref: str) -> dict | None:
    if supabase_db.enabled():
        return supabase_db.get_entitlement_by_payment_ref(payment_ref)
    ensure_dirs()
    with _lock:
        return sqlite_db.get_entitlement_by_payment_ref(payment_ref)


def list_all() -> list[dict]:
    if supabase_db.enabled():
        return supabase_db.list_entitlements()
    ensure_dirs()
    with _lock:
        return sqlite_db.list_entitlements()


def create_entitlement(token: str, email: str, payment_ref: str, url: str) -> dict:
    ent = {
        "token": token,
        "email": email,
        "payment_ref": payment_ref,
        "status": "pending",
        "url": url,
        "created_at": now_iso(),
        "used_at": None,
        "pdf_path": None,
        "pdf_filename": None,
        "submission": None,
    }
    if supabase_db.enabled():
        return supabase_db.insert_entitlement(ent)
    ensure_dirs()
    with _lock:
        return sqlite_db.insert_entitlement(ent)


def save_coaching(entry: dict) -> dict:
    if not entry.get("created_at"):
        entry = dict(entry)
        entry["created_at"] = now_iso()
    if supabase_db.enabled():
        payload = {
            "name": entry.get("name"),
            "email": entry.get("email"),
            "phone": entry.get("phone") or "",
            "message": entry.get("message"),
        }
        saved = supabase_db.insert_coaching(payload)
        entry.update({k: saved[k] for k in saved if k in entry or k == "id"})
        return entry
    ensure_dirs()
    with _lock:
        return sqlite_db.insert_coaching(entry)


def consume_pending(token: str, pdf_path: str, pdf_filename: str, submission: dict) -> dict:
    stored_path = pdf_path
    if supabase_db.enabled():
        local = Path(pdf_path)
        if local.is_file():
            try:
                stored_path = supabase_db.upload_pdf(pdf_filename, local.read_bytes())
            except Exception:
                stored_path = pdf_path
        return supabase_db.consume_entitlement(token, stored_path, pdf_filename, submission)
    ensure_dirs()
    with _lock:
        return sqlite_db.consume_entitlement(
            token, stored_path, pdf_filename, submission, now_iso()
        )


def log_mail(entry: dict) -> None:
    if supabase_db.enabled():
        supabase_db.log_mail(entry)
        return
    ensure_dirs()
    with _lock:
        sqlite_db.log_mail(entry)


def log_payment(entry: dict) -> None:
    if supabase_db.enabled():
        supabase_db.log_payment(entry)
        return
    ensure_dirs()
    with _lock:
        sqlite_db.log_payment(entry)


def resolve_pdf(ent: dict) -> Path | None:
    filename = ent.get("pdf_filename")
    raw = ent.get("pdf_path") or ""
    local = Path(raw) if raw and not str(raw).startswith("storage://") else None
    if local and local.is_file():
        return local
    if filename:
        fallback = PDF_DIR / filename
        if fallback.is_file():
            return fallback
        if supabase_db.enabled() and (str(raw).startswith("storage://") or not local):
            ensure_dirs()
            try:
                return supabase_db.download_pdf(filename, fallback)
            except Exception:
                return None
    return None
