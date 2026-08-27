"""Server-side validation. The web UI never computes the plan."""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PAYMENT_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,79}$")

ALLOWED_SEX = {"male", "female"}
ALLOWED_GOALS = {"lose", "gain", "recomp"}
ALLOWED_DAYS = {2, 3, 4, 5, 6}
ALLOWED_LOCATIONS = {"gym", "home"}
ALLOWED_DURATIONS = {"30", "45", "60", "75", "90"}
ALLOWED_EXPERIENCE = {"beginner", "intermediate", "advanced"}
ALLOWED_FOCUS = {
    "balanced",
    "chest",
    "back",
    "legs",
    "shoulders",
    "arms",
    "glutes",
}
ALLOWED_MOTIVATION = {
    "",
    "appearance",
    "strength",
    "health",
    "habit",
    "event",
}

ALLOWED_VEGETABLES = {
    "Brócoli",
    "Zanahoria",
    "Tomate",
    "Lechuga",
    "Espinaca",
    "Pimentón",
    "Pepino",
    "Calabacín",
    "Cebolla",
}
ALLOWED_FRUITS = {
    "Plátano",
    "Manzana",
    "Naranja",
    "Frutilla",
    "Arándanos",
    "Pera",
    "Piña",
    "Kiwi",
    "Uvas",
}
ALLOWED_PROTEINS = {
    "Pollo",
    "Carne magra",
    "Huevos",
    "Pavo",
    "Yogurt griego",
    "Legumbres",
}
ALLOWED_CARBS = {
    "Arroz",
    "Papa",
    "Avena",
    "Pasta",
    "Pan integral",
}


class ValidationError(Exception):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


def normalize_email(value: object) -> str:
    text = str(value or "").strip().lower()
    if not EMAIL_RE.match(text) or len(text) > 120:
        raise ValidationError("Introduce un email válido.", "email")
    return text


def normalize_payment_ref(value: object) -> str:
    text = str(value or "").strip()
    if not PAYMENT_REF_RE.match(text):
        raise ValidationError(
            "payment_ref inválido (3-80 caracteres: letras, números, . _ : -).",
            "payment_ref",
        )
    return text


def _num(data: dict, field: str, label: str) -> float:
    raw = data.get(field)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValidationError(f"Introduce {label} válido.", field) from None
    if not (value == value):  # NaN
        raise ValidationError(f"Introduce {label} válido.", field)
    return value


def _text(data: dict, field: str, max_len: int = 80) -> str:
    value = str(data.get(field) or "")
    value = value.replace("<", "").replace(">", "").strip()
    return value[:max_len]


def _list(data: dict, field: str, allowed: set[str], label: str, minimum: int) -> list[str]:
    raw = data.get(field) or []
    if not isinstance(raw, list):
        raise ValidationError(f"Selecciona {label}.", field)
    items = []
    seen = set()
    for item in raw:
        name = str(item).replace("<", "").replace(">", "").strip()
        if name not in allowed:
            raise ValidationError(f"{label} no permitido: {name}.", field)
        if name not in seen:
            items.append(name)
            seen.add(name)
    if len(items) < minimum:
        raise ValidationError(f"Debes seleccionar al menos {minimum} {label}.", field)
    return items


def bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100.0
    if height_m <= 0:
        return 0.0
    return weight_kg / (height_m * height_m)


def max_change_kg(weight: float, goal: str) -> float:
    if goal == "lose":
        return min(weight * 0.09, 10.8)
    if goal == "gain":
        return min(weight * 0.06, 6.0)
    return min(weight * 0.04, 4.0)


def validate_payload(data: dict, locked_email: str) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("Datos inválidos.")

    email = normalize_email(data.get("email") or locked_email)
    if email != locked_email:
        raise ValidationError("El email no coincide con el pago.", "email")

    name = _text(data, "name", 60)
    if len(name) < 2:
        raise ValidationError("Introduce tu nombre.", "name")

    age_f = _num(data, "age", "una edad")
    if age_f != int(age_f) or not (18 <= int(age_f) <= 70):
        raise ValidationError("La edad debe estar entre 18 y 70 años.", "age")
    age = int(age_f)

    weight = _num(data, "weight", "un peso")
    if not (40 <= weight <= 180):
        raise ValidationError("El peso debe estar entre 40 y 180 kg.", "weight")

    height = _num(data, "height", "una altura")
    if height != int(height) or not (140 <= height <= 210):
        raise ValidationError("La altura debe estar entre 140 y 210 cm.", "height")
    height = int(height)

    sex = _text(data, "sex", 16)
    if sex not in ALLOWED_SEX:
        raise ValidationError("Selecciona tu sexo.", "sex")

    index = bmi(weight, height)
    if not (17 <= index <= 65):
        raise ValidationError("El IMC debe estar entre 17 y 65.", "weight")

    goal = _text(data, "goal", 16)
    if goal not in ALLOWED_GOALS:
        raise ValidationError("Selecciona un objetivo.", "goal")

    target = _num(data, "targetWeight", "un peso objetivo")
    if not (40 <= target <= 180):
        raise ValidationError("El peso objetivo debe estar entre 40 y 180 kg.", "targetWeight")

    delta = target - weight
    limit = max_change_kg(weight, goal)
    if goal == "lose":
        if target >= weight:
            raise ValidationError(
                "Para bajar de peso, la meta debe ser menor que tu peso actual.",
                "targetWeight",
            )
        if (weight - target) > limit + 1e-6:
            raise ValidationError(
                "Esa meta en 12 semanas es demasiado agresiva. Elige un objetivo más cercano.",
                "targetWeight",
            )
    elif goal == "gain":
        if target <= weight:
            raise ValidationError(
                "Para ganar masa, la meta debe ser mayor que tu peso actual.",
                "targetWeight",
            )
        if (target - weight) > limit + 1e-6:
            raise ValidationError(
                "Esa meta en 12 semanas es demasiado agresiva. Elige un objetivo más cercano.",
                "targetWeight",
            )
    else:
        if abs(delta) > limit + 1e-6:
            raise ValidationError(
                "En recomposición, la meta de peso debe ser moderada a 12 semanas.",
                "targetWeight",
            )

    motivation = _text(data, "motivation", 24)
    if motivation not in ALLOWED_MOTIVATION:
        raise ValidationError("Selecciona una motivación válida.", "motivation")

    try:
        days = int(str(data.get("days", "")).strip())
    except (TypeError, ValueError):
        days = 0
    if days not in ALLOWED_DAYS:
        raise ValidationError("Selecciona cuántos días puedes entrenar.", "days")

    location = _text(data, "location", 16)
    if location not in ALLOWED_LOCATIONS:
        raise ValidationError("Selecciona dónde quieres entrenar.", "location")

    duration = _text(data, "duration", 8)
    if duration not in ALLOWED_DURATIONS:
        raise ValidationError("Selecciona la duración de tus sesiones.", "duration")

    experience = _text(data, "experience", 24)
    if experience not in ALLOWED_EXPERIENCE:
        raise ValidationError("Selecciona tu nivel de experiencia.", "experience")

    focus = _text(data, "focusMuscle", 24)
    if focus not in ALLOWED_FOCUS:
        raise ValidationError("Indica si quieres enfocarte en algún músculo.", "focusMuscle")

    vegetables = _list(data, "vegetables", ALLOWED_VEGETABLES, "vegetales", 3)
    fruits = _list(data, "fruits", ALLOWED_FRUITS, "frutas", 3)
    proteins = _list(data, "proteins", ALLOWED_PROTEINS, "proteínas", 1)
    carbs = _list(data, "carbs", ALLOWED_CARBS, "carbohidratos", 1)

    return {
        "email": email,
        "name": name,
        "age": age,
        "weight": round(weight, 1),
        "height": height,
        "sex": sex,
        "bmi": round(index, 1),
        "goal": goal,
        "targetWeight": round(target, 1),
        "motivation": motivation,
        "days": days,
        "location": location,
        "duration": duration,
        "experience": experience,
        "focusMuscle": focus,
        "vegetables": vegetables,
        "fruits": fruits,
        "proteins": proteins,
        "carbs": carbs,
    }
