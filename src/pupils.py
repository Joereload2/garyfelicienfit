"""Alumno tracking: PIN login, daily metrics, lifts planner."""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timezone

import json

import sqlite_db
from plan import GOAL_NAMES, LOCATION_NAMES, calculate_calories, macros_for
from validate import ValidationError, normalize_email

STRENGTH_EXERCISES = [
    "Sentadilla",
    "Prensa",
    "Zancadas",
    "Peso muerto",
    "Peso muerto rumano",
    "Hip thrust",
    "Press banca",
    "Press inclinado con mancuernas",
    "Jalón al pecho",
    "Remo con barra",
    "Remo unilateral",
    "Press militar",
    "Elevaciones laterales",
    "Curl de bíceps",
    "Extensión de tríceps en polea",
    "Dominadas",
    "Fondos",
    "Flexiones",
    "Plancha",
    "Abdominales",
]
CARDIO_EXERCISES = [
    "Caminata",
    "Trote",
    "Bici",
    "Elíptica",
    "Cinta",
    "Remo (cardio)",
    "Saltar la cuerda",
    "Nadar",
]


def exercise_catalog() -> dict:
    return {
        "strength": list(STRENGTH_EXERCISES),
        "cardio": list(CARDIO_EXERCISES),
    }


def is_cardio(name: str) -> bool:
    return (name or "").strip() in CARDIO_EXERCISES

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


def is_admin_email(email: str) -> bool:
    from envload import get

    raw = (get("ADMIN_EMAIL") or get("ADMIN_EMAILS") or "").lower()
    allowed = {p.strip() for p in raw.split(",") if p.strip()}
    e = (email or "").lower().strip()
    if e in allowed:
        return True
    local = e.split("@")[0]
    if get("ALUMNO_OPEN_LOGIN", "1") != "0" and local in {"admin", "gary"}:
        return True
    return False


def ingreso(email: str, pin: str) -> dict:
    """Unified login: admin dashboard or alumno planner."""
    from envload import get

    pin = str(pin or "").strip()
    open_login = get("ALUMNO_OPEN_LOGIN", "1") != "0"
    if open_login and pin != "12345":
        raise ValidationError("Usa el PIN 12345.")
    loose = _loose_email(email)
    if is_admin_email(loose) or is_admin_email(str(email or "").strip()):
        if not open_login:
            from envload import get as _g
            secret = _g("ADMIN_SECRET")
            if pin != secret and pin != "12345":
                raise ValidationError("PIN o clave incorrectos.")
        token = secrets.token_urlsafe(24)
        sqlite_db.put_session(token, loose, "admin", None, _now())
        return {"session": token, "email": loose, "role": "admin", "name": "Gary"}
    return {**login(email, pin), "role": "alumno"}


def login(email: str, pin: str) -> dict:
    from envload import get

    pin = str(pin or "").strip()
    open_login = get("ALUMNO_OPEN_LOGIN", "1") != "0"
    if open_login:
        if pin != "12345":
            raise ValidationError("Usa el PIN 12345.")
        email = _loose_email(email)
        pupil = sqlite_db.get_pupil_by_email(email)
        if not pupil:
            name = email.split("@")[0].replace(".", " ").strip()[:80]
            pupil = sqlite_db.insert_pupil(email, name or "Alumno", hash_pin(email, "12345"), _now())
    else:
        email = normalize_email(email)
        pupil = sqlite_db.get_pupil_by_email(email)
        if not pupil or pupil.get("pin_hash") != hash_pin(email, pin):
            raise ValidationError("Email o PIN incorrectos.")
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


def _parse_guide(raw) -> dict | None:
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def guide_for(pupil: dict) -> dict | None:
    sqlite_db.ensure_metric(pupil["id"], "peso", "Peso", "number", "kg", 15)
    fresh = sqlite_db.get_pupil_by_id(pupil["id"]) or pupil
    saved = _parse_guide(fresh.get("guide"))
    if saved and saved.get("kcal"):
        return saved
    sub = sqlite_db.latest_submission_by_email(pupil.get("email") or "")
    if not sub:
        return saved
    try:
        kcal = calculate_calories(sub)
        macros = macros_for(sub.get("goal") or "recomp", kcal)
    except Exception:
        return saved
    return {
        "objetivo": GOAL_NAMES.get(sub.get("goal"), sub.get("goal") or "—"),
        "peso": sub.get("weight"),
        "peso_meta": sub.get("targetWeight"),
        "kcal": kcal,
        "proteina": macros["protein_g"],
        "carbos": macros["carb_g"],
        "grasa": macros["fat_g"],
        "dias": sub.get("days"),
        "lugar": LOCATION_NAMES.get(sub.get("location"), sub.get("location") or ""),
        "from_plan": True,
    }


def save_guide(pupil: dict, data: dict) -> dict:
    def num(key, lo, hi):
        try:
            v = float(data.get(key))
        except (TypeError, ValueError):
            return None
        if v < lo or v > hi:
            return None
        return round(v, 1)

    guide = {
        "objetivo": str(data.get("objetivo") or "").strip()[:80],
        "peso": num("peso", 30, 250),
        "peso_meta": num("peso_meta", 30, 250),
        "kcal": num("kcal", 800, 6000),
        "proteina": num("proteina", 20, 400),
        "carbos": num("carbos", 20, 800),
        "grasa": num("grasa", 10, 250),
        "from_plan": False,
    }
    if not guide["kcal"]:
        raise ValidationError("Indica las kcal meta del plan.")
    sqlite_db.set_pupil_guide(pupil["id"], guide)
    return guide


def state(pupil: dict, start: str, end: str) -> dict:
    if not DAY_RE.match(start) or not DAY_RE.match(end):
        raise ValidationError("Rango de fechas inválido.")
    pid = pupil["id"]
    sqlite_db.ensure_metric(pid, "peso", "Peso", "number", "kg", 15)
    metrics = sqlite_db.list_metrics(pid)
    values = sqlite_db.list_day_values(pid, start, end)
    lifts = sqlite_db.list_lifts(pid, start, end)
    by_day: dict[str, dict] = {}
    for row in values:
        by_day.setdefault(row["day"], {})[row["metric_key"]] = row["value"]
    guide = guide_for(pupil)
    return {
        "email": pupil["email"],
        "name": pupil.get("name") or "",
        "metrics": metrics,
        "days": by_day,
        "lifts": lifts,
        "exercises": exercise_catalog(),
        "guide": guide,
        "compliance": compliance_for(by_day, lifts, guide, start, end),
        "start": start,
        "end": end,
    }


def _band(actual, target, tol: float = 0.15) -> float | None:
    if actual is None or not target:
        return None
    try:
        actual_f = float(actual)
        target_f = float(target)
    except (TypeError, ValueError):
        return None
    if target_f <= 0:
        return None
    diff = abs(actual_f - target_f) / target_f
    if diff <= tol:
        return 1.0
    if diff >= 1.0:
        return 0.0
    return max(0.0, 1.0 - (diff - tol) / (1.0 - tol))


def _pct_color(pct: int | None) -> str:
    if pct is None:
        return "empty"
    if pct >= 85:
        return "green"
    if pct >= 60:
        return "yellow"
    if pct >= 35:
        return "orange"
    return "red"


def day_score(values: dict, has_lift: bool, guide: dict | None) -> dict:
    if not values and not has_lift:
        return {"status": "empty", "pct": None, "color": "empty"}
    guide = guide or {}
    scores: list[float] = []
    trained = bool(values.get("entreno")) or has_lift
    if "entreno" in values or has_lift:
        scores.append(1.0 if trained else 0.0)
    for key in ("kcal", "proteina", "carbos", "grasa"):
        s = _band(values.get(key), guide.get(key))
        if s is not None:
            scores.append(s)
    if not scores:
        return {"status": "logged", "pct": 50, "color": _pct_color(50)}
    pct = int(round(100 * sum(scores) / len(scores)))
    return {"status": "logged", "pct": pct, "color": _pct_color(pct)}


def compliance_for(by_day: dict, lifts: list, guide: dict | None, start: str, end: str) -> dict:
    from datetime import date as date_cls

    days: list[str] = []
    cur = date_cls.fromisoformat(start)
    last = date_cls.fromisoformat(end)
    while cur <= last:
        days.append(cur.isoformat())
        cur = date_cls.fromordinal(cur.toordinal() + 1)
    lift_days = {str(x.get("day") or "") for x in lifts or []}
    per_day = {}
    logged_pcts: list[int] = []
    empty = 0
    failing = 0
    for d in days:
        vals = by_day.get(d) or {}
        sc = day_score(vals, d in lift_days, guide)
        per_day[d] = sc
        if sc["status"] == "empty":
            empty += 1
        else:
            logged_pcts.append(int(sc["pct"] or 0))
            if (sc["pct"] or 0) < 70:
                failing += 1
    if not logged_pcts:
        kind = "no_fill"
        avg = None
    else:
        avg = int(round(sum(logged_pcts) / len(logged_pcts)))
        kind = "ok" if avg >= 70 and empty <= max(1, len(days) // 3) else "failing"
        if empty == len(days):
            kind = "no_fill"
    return {
        "kind": kind,
        "avg_pct": avg,
        "color": _pct_color(avg),
        "empty_days": empty,
        "logged_days": len(logged_pcts),
        "failing_days": failing,
        "days": per_day,
    }


def roster(days: int = 14) -> dict:
    from datetime import date as date_cls

    today = date_cls.today()
    start = today.fromordinal(today.toordinal() - (days - 1)).isoformat()
    end = today.isoformat()
    no_fill = []
    failing = []
    ok = []
    for row in sqlite_db.list_pupils():
        full = sqlite_db.get_pupil_by_id(row["id"]) or row
        st = state(full, start, end)
        comp = st.get("compliance") or {}
        item = {
            "id": row["id"],
            "email": row.get("email"),
            "name": row.get("name") or "",
            "kind": comp.get("kind"),
            "avg_pct": comp.get("avg_pct"),
            "color": comp.get("color"),
            "empty_days": comp.get("empty_days"),
            "logged_days": comp.get("logged_days"),
        }
        if comp.get("kind") == "no_fill":
            no_fill.append(item)
        elif comp.get("kind") == "failing":
            failing.append(item)
        else:
            ok.append(item)
    return {"no_fill": no_fill, "failing": failing, "ok": ok, "start": start, "end": end}


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
        "minutes": maybe_num(data.get("minutes")),
        "notes": str(data.get("notes") or "")[:120],
        "created_at": _now(),
    }
    return sqlite_db.insert_lift(row)


def remove_lift(pupil: dict, lift_id: int) -> None:
    if not sqlite_db.delete_lift(pupil["id"], int(lift_id)):
        raise ValidationError("No se encontró esa serie.")
