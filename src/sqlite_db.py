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

PUPIL_SCHEMA = """
CREATE TABLE IF NOT EXISTS pupils (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL DEFAULT '',
  pin_hash TEXT NOT NULL,
  session TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pupil_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pupil_id INTEGER NOT NULL,
  key TEXT NOT NULL,
  label TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'number',
  unit TEXT NOT NULL DEFAULT '',
  sort INTEGER NOT NULL DEFAULT 0,
  enabled INTEGER NOT NULL DEFAULT 1,
  UNIQUE(pupil_id, key)
);
CREATE TABLE IF NOT EXISTS pupil_day_values (
  pupil_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  metric_key TEXT NOT NULL,
  value REAL NOT NULL,
  PRIMARY KEY (pupil_id, day, metric_key)
);
CREATE TABLE IF NOT EXISTS auth_sessions (
  token TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  role TEXT NOT NULL,
  pupil_id INTEGER,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS discount_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  code TEXT NOT NULL UNIQUE,
  offer TEXT NOT NULL DEFAULT '3meses',
  percent INTEGER NOT NULL DEFAULT 50,
  used INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  token TEXT,
  expires_at TEXT
);
CREATE TABLE IF NOT EXISTS marketing_leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  ads_consent INTEGER NOT NULL DEFAULT 0,
  source TEXT NOT NULL DEFAULT 'herramientas',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pupil_lifts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pupil_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  week INTEGER NOT NULL DEFAULT 1,
  exercise TEXT NOT NULL,
  load REAL,
  sets INTEGER,
  reps INTEGER,
  minutes REAL,
  notes TEXT,
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
        _conn.executescript(PUPIL_SCHEMA)
        cols = [r[1] for r in _conn.execute("PRAGMA table_info(pupils)").fetchall()]
        if cols and "guide" not in cols:
            _conn.execute("ALTER TABLE pupils ADD COLUMN guide TEXT")
        lift_cols = [r[1] for r in _conn.execute("PRAGMA table_info(pupil_lifts)").fetchall()]
        if lift_cols and "minutes" not in lift_cols:
            _conn.execute("ALTER TABLE pupil_lifts ADD COLUMN minutes REAL")
        disc_cols = [r[1] for r in _conn.execute("PRAGMA table_info(discount_codes)").fetchall()]
        if disc_cols and "token" not in disc_cols:
            _conn.execute("ALTER TABLE discount_codes ADD COLUMN token TEXT")
        if disc_cols and "expires_at" not in disc_cols:
            _conn.execute("ALTER TABLE discount_codes ADD COLUMN expires_at TEXT")
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


def get_marketing_by_email(email: str) -> dict | None:
    cur = _connect().execute(
        "SELECT * FROM marketing_leads WHERE lower(email) = lower(?) LIMIT 1",
        (email,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def upsert_marketing_lead(entry: dict) -> dict:
    conn = _connect()
    email = entry.get("email") or ""
    existing = get_marketing_by_email(email)
    if existing:
        conn.execute(
            """
            UPDATE marketing_leads
            SET name = ?, phone = ?, ads_consent = ?, source = ?
            WHERE lower(email) = lower(?)
            """,
            (
                entry.get("name"),
                entry.get("phone") or "",
                1 if entry.get("ads_consent") else 0,
                entry.get("source") or "herramientas",
                email,
            ),
        )
        conn.commit()
        return get_marketing_by_email(email) or existing
    cur = conn.execute(
        """
        INSERT INTO marketing_leads (name, email, phone, ads_consent, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entry.get("name"),
            email,
            entry.get("phone") or "",
            1 if entry.get("ads_consent") else 0,
            entry.get("source") or "herramientas",
            entry.get("created_at") or "",
        ),
    )
    conn.commit()
    entry = dict(entry)
    entry["id"] = cur.lastrowid
    return entry


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


def get_payment_by_ref(payment_ref: str) -> dict | None:
    if not payment_ref:
        return None
    cur = _connect().execute(
        "SELECT * FROM payments WHERE payment_ref = ? OR provider_id = ? LIMIT 1",
        (payment_ref, payment_ref),
    )
    row = cur.fetchone()
    return dict(row) if row else None


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


DEFAULT_METRICS = [
    ("entreno", "Entrenamiento hecho", "bool", "", 10),
    ("peso", "Peso", "number", "kg", 15),
    ("sueno", "Sueño", "number", "h", 20),
    ("agua", "Vasos de agua", "number", "vasos", 30),
    ("pasos", "Pasos", "number", "pasos", 40),
    ("capsulas", "Cápsulas de ejercicio", "number", "", 50),
    ("kcal", "Kcal", "number", "kcal", 60),
    ("proteina", "Proteína", "number", "g", 70),
    ("carbos", "Carbos", "number", "g", 80),
    ("grasa", "Grasa", "number", "g", 90),
    ("coca", "Vasos de Coca-Cola", "number", "vasos", 100),
]


def _row(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def put_session(token: str, email: str, role: str, pupil_id: int | None, created_at: str) -> None:
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO auth_sessions (token, email, role, pupil_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (token, email, role, pupil_id, created_at),
    )
    conn.commit()


def get_session(token: str) -> dict | None:
    if not token:
        return None
    cur = _connect().execute("SELECT * FROM auth_sessions WHERE token = ?", (token,))
    row = cur.fetchone()
    return dict(row) if row else None


def get_discount_by_email(email: str, offer: str = "3meses") -> dict | None:
    cur = _connect().execute(
        """
        SELECT * FROM discount_codes
        WHERE lower(email) = lower(?) AND offer = ?
        ORDER BY id DESC LIMIT 1
        """,
        (email, offer),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def insert_discount(
    email: str,
    code: str,
    created_at: str,
    offer: str = "3meses",
    percent: int = 50,
    token: str = "",
    expires_at: str = "",
) -> dict:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO discount_codes (email, code, offer, percent, used, created_at, token, expires_at)
        VALUES (?, ?, ?, ?, 0, ?, ?, ?)
        """,
        (email, code, offer, percent, created_at, token or None, expires_at or None),
    )
    conn.commit()
    return get_discount_by_email(email, offer) or {"email": email, "code": code}


def get_discount_by_token(token: str) -> dict | None:
    if not token:
        return None
    cur = _connect().execute(
        "SELECT * FROM discount_codes WHERE token = ? ORDER BY id DESC LIMIT 1",
        (token,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def mark_discount_used(token: str) -> None:
    if not token:
        return
    conn = _connect()
    conn.execute("UPDATE discount_codes SET used = 1 WHERE token = ?", (token,))
    conn.commit()


def insert_pupil(email: str, name: str, pin_hash: str, created_at: str) -> dict:
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO pupils (email, name, pin_hash, created_at) VALUES (?, ?, ?, ?)",
        (email, name, pin_hash, created_at),
    )
    pid = cur.lastrowid
    for key, label, kind, unit, sort in DEFAULT_METRICS:
        conn.execute(
            """
            INSERT INTO pupil_metrics (pupil_id, key, label, kind, unit, sort, enabled)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (pid, key, label, kind, unit, sort),
        )
    conn.commit()
    return get_pupil_by_id(pid)


def get_pupil_by_id(pid: int) -> dict | None:
    cur = _connect().execute("SELECT * FROM pupils WHERE id = ?", (pid,))
    return _row(cur.fetchone())


def get_pupil_by_email(email: str) -> dict | None:
    cur = _connect().execute("SELECT * FROM pupils WHERE email = ?", (email,))
    return _row(cur.fetchone())


def get_pupil_by_session(session: str) -> dict | None:
    if not session:
        return None
    cur = _connect().execute("SELECT * FROM pupils WHERE session = ?", (session,))
    return _row(cur.fetchone())


def list_pupils() -> list[dict]:
    cur = _connect().execute("SELECT id, email, name, created_at FROM pupils ORDER BY created_at DESC")
    return [dict(r) for r in cur.fetchall()]


def set_pupil_session(pid: int, session: str | None) -> None:
    conn = _connect()
    conn.execute("UPDATE pupils SET session = ? WHERE id = ?", (session, pid))
    conn.commit()


def set_pupil_guide(pid: int, guide: dict | None) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE pupils SET guide = ? WHERE id = ?",
        (json.dumps(guide, ensure_ascii=False) if guide else None, pid),
    )
    conn.commit()


def latest_submission_by_email(email: str) -> dict | None:
    cur = _connect().execute(
        """
        SELECT submission FROM entitlements
        WHERE lower(email) = lower(?) AND submission IS NOT NULL AND submission != ''
        ORDER BY created_at DESC LIMIT 1
        """,
        (email,),
    )
    row = cur.fetchone()
    if not row:
        return None
    raw = row["submission"]
    if isinstance(raw, str) and raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
    return None


def ensure_metric(pid: int, key: str, label: str, kind: str, unit: str, sort: int) -> None:
    conn = _connect()
    row = conn.execute(
        "SELECT id FROM pupil_metrics WHERE pupil_id = ? AND key = ?",
        (pid, key),
    ).fetchone()
    if row:
        return
    conn.execute(
        """
        INSERT INTO pupil_metrics (pupil_id, key, label, kind, unit, sort, enabled)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (pid, key, label, kind, unit, sort),
    )
    conn.commit()


def list_metrics(pid: int) -> list[dict]:
    cur = _connect().execute(
        "SELECT * FROM pupil_metrics WHERE pupil_id = ? ORDER BY sort, id",
        (pid,),
    )
    return [dict(r) for r in cur.fetchall()]


def add_metric(pid: int, key: str, label: str, kind: str, unit: str) -> dict:
    conn = _connect()
    sort = conn.execute(
        "SELECT COALESCE(MAX(sort), 0) + 10 FROM pupil_metrics WHERE pupil_id = ?",
        (pid,),
    ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO pupil_metrics (pupil_id, key, label, kind, unit, sort, enabled)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (pid, key, label, kind, unit, sort),
    )
    conn.commit()
    cur = conn.execute(
        "SELECT * FROM pupil_metrics WHERE pupil_id = ? AND key = ?",
        (pid, key),
    )
    return dict(cur.fetchone())


def disable_metric(pid: int, key: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE pupil_metrics SET enabled = 0 WHERE pupil_id = ? AND key = ?",
        (pid, key),
    )
    conn.commit()


def enable_metric(pid: int, key: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE pupil_metrics SET enabled = 1 WHERE pupil_id = ? AND key = ?",
        (pid, key),
    )
    conn.commit()


def upsert_day_value(pid: int, day: str, key: str, value: float) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO pupil_day_values (pupil_id, day, metric_key, value)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(pupil_id, day, metric_key) DO UPDATE SET value = excluded.value
        """,
        (pid, day, key, value),
    )
    conn.commit()


def list_day_values(pid: int, start: str, end: str) -> list[dict]:
    cur = _connect().execute(
        """
        SELECT day, metric_key, value FROM pupil_day_values
        WHERE pupil_id = ? AND day >= ? AND day <= ?
        ORDER BY day
        """,
        (pid, start, end),
    )
    return [dict(r) for r in cur.fetchall()]


def insert_lift(row: dict) -> dict:
    conn = _connect()
    cur = conn.execute(
        """
        INSERT INTO pupil_lifts (
          pupil_id, day, week, exercise, load, sets, reps, minutes, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["pupil_id"],
            row["day"],
            row.get("week") or 1,
            row["exercise"],
            row.get("load"),
            row.get("sets"),
            row.get("reps"),
            row.get("minutes"),
            row.get("notes") or "",
            row["created_at"],
        ),
    )
    conn.commit()
    row = dict(row)
    row["id"] = cur.lastrowid
    return row


def list_lifts(pid: int, start: str, end: str) -> list[dict]:
    cur = _connect().execute(
        """
        SELECT * FROM pupil_lifts
        WHERE pupil_id = ? AND day >= ? AND day <= ?
        ORDER BY day, id
        """,
        (pid, start, end),
    )
    return [dict(r) for r in cur.fetchall()]


def delete_lift(pid: int, lift_id: int) -> bool:
    conn = _connect()
    cur = conn.execute(
        "DELETE FROM pupil_lifts WHERE id = ? AND pupil_id = ?",
        (lift_id, pid),
    )
    conn.commit()
    return cur.rowcount == 1

