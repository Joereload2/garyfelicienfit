"""JSON store for one-shot entitlements."""

from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import os

from envload import ROOT
import supabase_db

DATA_DIR = ROOT / "data"
STORE_PATH = DATA_DIR / "store.json"
PDF_DIR = DATA_DIR / "pdfs"
OUTBOX_DIR = DATA_DIR / "outbox"

_lock = threading.RLock()


def configure_paths(root: Path | None = None) -> None:
    """Point the store at a directory. Tests use a temp folder via PLANFIT_DATA_DIR."""
    global DATA_DIR, STORE_PATH, PDF_DIR, OUTBOX_DIR
    override = (os.environ.get("PLANFIT_DATA_DIR") or "").strip()
    DATA_DIR = Path(root) if root is not None else (Path(override) if override else ROOT / "data")
    STORE_PATH = DATA_DIR / "store.json"
    PDF_DIR = DATA_DIR / "pdfs"
    OUTBOX_DIR = DATA_DIR / "outbox"


configure_paths()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        _atomic_write({"entitlements": {}, "by_payment_ref": {}})


def _atomic_write(payload: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STORE_PATH.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp.replace(STORE_PATH)


def _read() -> dict:
    ensure_dirs()
    try:
        data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}
    data.setdefault("entitlements", {})
    data.setdefault("by_payment_ref", {})
    return data


def get_by_token(token: str) -> dict | None:
    if supabase_db.enabled():
        return supabase_db.get_entitlement_by_token(token)
    with _lock:
        ent = _read()["entitlements"].get(token)
        return deepcopy(ent) if ent else None


def get_by_payment_ref(payment_ref: str) -> dict | None:
    if supabase_db.enabled():
        return supabase_db.get_entitlement_by_payment_ref(payment_ref)
    with _lock:
        data = _read()
        token = data["by_payment_ref"].get(payment_ref)
        if not token:
            return None
        ent = data["entitlements"].get(token)
        return deepcopy(ent) if ent else None


def list_all() -> list[dict]:
    if supabase_db.enabled():
        return supabase_db.list_entitlements()
    with _lock:
        items = list(_read()["entitlements"].values())
        items.sort(key=lambda e: e.get("created_at") or "", reverse=True)
        return deepcopy(items)


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
    with _lock:
        data = _read()
        if payment_ref in data["by_payment_ref"]:
            raise ValueError("payment_ref_used")
        if token in data["entitlements"]:
            raise ValueError("token_collision")
        data["entitlements"][token] = ent
        data["by_payment_ref"][payment_ref] = token
        _atomic_write(data)
        return deepcopy(ent)


def save_coaching(entry: dict) -> dict:
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
    with _lock:
        ensure_dirs()
        path = DATA_DIR / "coaching.json"
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            items = []
        if not isinstance(items, list):
            items = []
        items.insert(0, entry)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        return entry


def consume_pending(token: str, pdf_path: str, pdf_filename: str, submission: dict) -> dict:
    """Spend the token only after a valid submission. Raises KeyError/ValueError."""
    stored_path = pdf_path
    if supabase_db.enabled():
        local = Path(pdf_path)
        if local.is_file():
            try:
                stored_path = supabase_db.upload_pdf(pdf_filename, local.read_bytes())
            except Exception:
                stored_path = pdf_path
        return supabase_db.consume_entitlement(token, stored_path, pdf_filename, submission)
    with _lock:
        data = _read()
        ent = data["entitlements"].get(token)
        if not ent:
            raise KeyError("not_found")
        if ent.get("status") != "pending":
            raise ValueError("used")
        ent["status"] = "used"
        ent["used_at"] = now_iso()
        ent["pdf_path"] = stored_path
        ent["pdf_filename"] = pdf_filename
        ent["submission"] = submission
        data["entitlements"][token] = ent
        _atomic_write(data)
        return deepcopy(ent)


def resolve_pdf(ent: dict) -> Path | None:
    """Local path to the PDF, downloading from Supabase Storage if needed."""
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
