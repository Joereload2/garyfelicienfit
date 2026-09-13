"""Alumno tracking: PIN login, daily metrics, lifts planner."""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timezone

import sqlite_db
from plan import GYM, HOME
from validate import ValidationError, normalize_email

MAX_LIFTS_PER_DAY = 2


def exercise_catalog() -> list[str]:
    names = set()
    for group in (GYM, HOME):
        for items in group.values():
            names.update(items)
    extra = [
        "Peso muerto",
        "Peso muerto rumano",
        "Sentadilla goblet",
        "Remo sentado",
        "Press banca inclinado",
        "Dominadas",
        "Fondos",
        "Face pull",
        "Abdominales",
        "Plancha",
        "Burpees",
        "Caminata",
        "Bici",
        "Elíptica",
    ]
    names.update(extra)
    return sorted(names)

KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def hash_pin(email: str, pin: str) -> str:
    return hashlib.sha256(f"{email.lower().strip()}:{pin}".encode("utf-8")).hexdigest()


def new_pin() -> str:
    n = secrets.randbelow(1_000_000)
    return f"{n:06d}"


def create_pupil(email: str, name: str) -> dict:
    email = normalize_email(email)
    name = (name or "").replace("<", "").replace(">", "").strip()[:80]
    if sqlite_db.get_pupil_by_email(email):
        raise ValidationError("Ese email ya tiene seguimiento.")
    pin = new_pin()
    pupil = sqlite_db.insert_pupil(email, name or email.split("@")[0], hash_pin(email, pin), _now())
    return {"id": pupil["id"], "email": email, "name": pupil["name"], "pin": pin}


def list_pupils() -> list[dict]:
    return sqlite_db.list_pupils()


def _loose_email(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text:
        raise ValidationError("Escribe un email o un nombre.")
    if "@" not in text:
        slug = "".join(ch if ch.isalnum() else "." for ch in text).strip(".") or "alumno"
        text = slug[:40] + "@alumno.local"
    if len(text) > 120:
        raise ValidationError("Ese email es demasiado largo.")
    return text


def login(email: str, pin: str) -> dict:
    pin = str(pin or "").strip()
    if pin != "12345":
        raise ValidationError("Usa el PIN 12345.")
    email = _loose_email(email)
    pupil = sqlite_db.get_pupil_by_email(email)
    if not pupil:
        name = email.split("@")[0].replace(".", " ").strip()[:80]
        pupil = sqlite_db.insert_pupil(email, name or "Alumno", hash_pin(email, "12345"), _now())
    session = secrets.token_urlsafe(24)
    sqlite_db.set_pupil_session(pupil["id"], session)
    return {"session": session, "email": email, "name": pupil.get("name") or ""}


def pupil_from_session(session: str) -> dict:
    pupil = sqlite_db.get_pupil_by_session((session or "").strip())
    if not pupil:
        raise ValidationError("Sesión no válida. Entra de nuevo.")
    return pupil


def _slug(label: str) -> str:
    raw = (label or "").lower().strip()
    raw = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    if not raw:
        raw = "habito"
    if raw[0].isdigit():
        raw = "m_" + raw
    return raw[:32]


def state(pupil: dict, start: str, end: str) -> dict:
    if not DAY_RE.match(start) or not DAY_RE.match(end):
        raise ValidationError("Rango de fechas inválido.")
    pid = pupil["id"]
    metrics = sqlite_db.list_metrics(pid)
    values = sqlite_db.list_day_values(pid, start, end)
    lifts = sqlite_db.list_lifts(pid, start, end)
    by_day: dict[str, dict] = {}
    for row in values:
        by_day.setdefault(row["day"], {})[row["metric_key"]] = row["value"]
    return {
        "email": pupil["email"],
        "name": pupil.get("name") or "",
        "metrics": metrics,
        "days": by_day,
        "lifts": lifts,
        "exercises": exercise_catalog(),
        "max_lifts": MAX_LIFTS_PER_DAY,
        "start": start,
        "end": end,
    }


def save_day(pupil: dict, day: str, values: dict) -> None:
    if not DAY_RE.match(day or ""):
        raise ValidationError("Día inválido.")
    allowed = {m["key"] for m in sqlite_db.list_metrics(pupil["id"]) if m.get("enabled")}
    kinds = {m["key"]: m["kind"] for m in sqlite_db.list_metrics(pupil["id"])}
    if not isinstance(values, dict):
        raise ValidationError("Valores inválidos.")
    for key, raw in values.items():
        if key not in allowed:
            continue
        try:
            num = float(raw)
        except (TypeError, ValueError):
            continue
        if kinds.get(key) == "bool":
            num = 1.0 if num else 0.0
        sqlite_db.upsert_day_value(pupil["id"], day, key, num)


def add_metric(pupil: dict, label: str, kind: str, unit: str) -> dict:
    label = (label or "").replace("<", "").replace(">", "").strip()[:40]
    if len(label) < 2:
        raise ValidationError("Ponle un nombre al hábito.")
    kind = "bool" if kind == "bool" else "number"
    unit = (unit or "").replace("<", "").replace(">", "").strip()[:16]
    key = _slug(label)
    existing = {m["key"] for m in sqlite_db.list_metrics(pupil["id"])}
    base = key
    n = 2
    while key in existing:
        key = f"{base}_{n}"[:32]
        n += 1
    try:
        return sqlite_db.add_metric(pupil["id"], key, label, kind, unit)
    except Exception as exc:
        raise ValidationError("No se pudo agregar.") from exc


def toggle_metric(pupil: dict, key: str, enabled: bool) -> None:
    if not KEY_RE.match(key or ""):
        raise ValidationError("Hábito inválido.")
    if enabled:
        sqlite_db.enable_metric(pupil["id"], key)
    else:
        sqlite_db.disable_metric(pupil["id"], key)


def add_lift(pupil: dict, data: dict) -> dict:
    day = str(data.get("day") or "")
    if not DAY_RE.match(day):
        raise ValidationError("Día inválido.")
    exercise = str(data.get("exercise") or "").replace("<", "").replace(">", "").strip()[:80]
    if len(exercise) < 2:
        raise ValidationError("Elige o escribe el ejercicio.")
    existing = sqlite_db.list_lifts(pupil["id"], day, day)
    if len(existing) >= MAX_LIFTS_PER_DAY:
        raise ValidationError("Este día admite como máximo 2 ejercicios.")
    try:
        week = int(data.get("week") or 1)
    except (TypeError, ValueError):
        week = 1
    week = max(1, min(12, week))

    def maybe_num(v):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    row = {
        "pupil_id": pupil["id"],
        "day": day,
        "week": week,
        "exercise": exercise,
        "load": maybe_num(data.get("load")),
        "sets": int(maybe_num(data.get("sets")) or 0) or None,
        "reps": int(maybe_num(data.get("reps")) or 0) or None,
        "notes": str(data.get("notes") or "")[:120],
        "created_at": _now(),
    }
    return sqlite_db.insert_lift(row)


def remove_lift(pupil: dict, lift_id: int) -> None:
    if not sqlite_db.delete_lift(pupil["id"], int(lift_id)):
        raise ValidationError("No se encontró esa serie.")
