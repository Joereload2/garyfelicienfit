"""Local SQLite database. Free, no account, lives in data/planfit.db."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

_db_path = Path("data/planfit.db")
_conn: sqlite3.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS entitlements (
  token TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  payment_ref TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending',
  url TEXT,
  created_at TEXT NOT NULL,
  used_at TEXT,
  pdf_path TEXT,
  pdf_filename TEXT,
  submission TEXT
);
CREATE TABLE IF NOT EXISTS coaching_leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mail_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  to_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT,
  payment_ref TEXT,
  provider TEXT,
  status TEXT NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  provider_id TEXT UNIQUE,
  email TEXT NOT NULL,
  payment_ref TEXT NOT NULL,
  amount_cents INTEGER,
  currency TEXT DEFAULT 'usd',
  status TEXT NOT NULL,
  raw TEXT,
  created_at TEXT NOT NULL
);
"""


def init(path: Path) -> None:
    global _db_path, _conn
    _db_path = Path(path)
    if _conn is not None:
        try:
            _conn.close()
        except sqlite3.Error:
            pass
        _conn = None


def _connect() -> sqlite3.Connection:
    global _conn
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    if _conn is None:
        _conn = sqlite3.connect(str(_db_path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _conn.executescript(SCHEMA)
        _conn.commit()
    return _conn


def _ent(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    data = dict(row)
    raw = data.get("submission")
    if isinstance(raw, str) and raw:
        try:
            data["submission"] = json.loads(raw)
        except json.JSONDecodeError:
            pass
    else:
        data["submission"] = None
    return data


def get_entitlement_by_token(token: str) -> dict | None:
    cur = _connect().execute("SELECT * FROM entitlements WHERE token = ?", (token,))
    return _ent(cur.fetchone())


def get_entitlement_by_payment_ref(payment_ref: str) -> dict | None:
    cur = _connect().execute(
        "SELECT * FROM entitlements WHERE payment_ref = ?", (payment_ref,)
    )
    return _ent(cur.fetchone())


def list_entitlements() -> list[dict]:
    cur = _connect().execute("SELECT * FROM entitlements ORDER BY created_at DESC")
    return [d for d in (_ent(r) for r in cur.fetchall()) if d]


def insert_entitlement(ent: dict) -> dict:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO entitlements (
              token, email, payment_ref, status, url, created_at,
              used_at, pdf_path, pdf_filename, submission
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ent["token"],
                ent["email"],
                ent["payment_ref"],
                ent.get("status") or "pending",
                ent.get("url"),
                ent["created_at"],
                ent.get("used_at"),
                ent.get("pdf_path"),
                ent.get("pdf_filename"),
                json.dumps(ent["submission"], ensure_ascii=False) if ent.get("submission") else None,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError("payment_ref_used") from exc
    return get_entitlement_by_token(ent["token"]) or ent


def consume_entitlement(token: str, pdf_path: str, pdf_filename: str, submission: dict, used_at: str) -> dict:
    conn = _connect()
    row = get_entitlement_by_token(token)
    if not row:
        raise KeyError("not_found")
    if row.get("status") != "pending":
        raise ValueError("used")
    cur = conn.execute(
        """
        UPDATE entitlements
        SET status = 'used', used_at = ?, pdf_path = ?, pdf_filename = ?, submission = ?
        WHERE token = ? AND status = 'pending'
        """,
        (
            used_at,
            pdf_path,
            pdf_filename,
            json.dumps(submission, ensure_ascii=False),
            token,
        ),
    )
    conn.commit()
    if cur.rowcount != 1:
        raise ValueError("used")
    return get_entitlement_by_token(token) or row


def insert_coaching(entry: dict) -> dict:
    conn = _connect()
    cur = conn.execute(
        """
        INSERT INTO coaching_leads (name, email, phone, message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            entry.get("name"),
            entry.get("email"),
            entry.get("phone") or "",
            entry.get("message"),
            entry.get("created_at") or "",
        ),
    )
    conn.commit()
    entry = dict(entry)
    entry["id"] = cur.lastrowid
    return entry


def log_mail(entry: dict) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO mail_log (
          kind, to_email, subject, body, payment_ref, provider, status, error, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            entry.get("kind"),
            entry.get("to_email"),
            entry.get("subject"),
            entry.get("body"),
            entry.get("payment_ref"),
            entry.get("provider"),
            entry.get("status"),
            entry.get("error"),
        ),
    )
    conn.commit()


def log_payment(entry: dict) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO payments (
              provider, provider_id, email, payment_ref, amount_cents, currency, status, raw, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                entry.get("provider"),
                entry.get("provider_id"),
                entry.get("email"),
                entry.get("payment_ref"),
                entry.get("amount_cents"),
                entry.get("currency") or "usd",
                entry.get("status"),
                json.dumps(entry.get("raw"), ensure_ascii=False) if entry.get("raw") else None,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return


def import_json_if_empty(json_path: Path) -> None:
    if not json_path.is_file():
        return
    conn = _connect()
    n = conn.execute("SELECT COUNT(*) FROM entitlements").fetchone()[0]
    if n:
        return
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for ent in (data.get("entitlements") or {}).values():
        if not isinstance(ent, dict) or not ent.get("token"):
            continue
        try:
            insert_entitlement(ent)
        except ValueError:
            continue
