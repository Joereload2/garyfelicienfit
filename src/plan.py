"""Plan engine. Runs only on the server; never sent to the browser."""

from __future__ import annotations

GOAL_NAMES = {
    "lose": "Bajar de peso",
    "gain": "Ganar masa muscular",
    "recomp": "Recomposición corporal",
}
FOCUS_NAMES = {
    "balanced": "Trabajo equilibrado",
    "chest": "Pecho",
    "back": "Espalda",
    "legs": "Piernas",
    "shoulders": "Hombros",
    "arms": "Brazos",
    "glutes": "Glúteos",
}
LOCATION_NAMES = {"gym": "Gimnasio", "home": "Casa"}
EXPERIENCE_NAMES = {
    "beginner": "Principiante",
    "intermediate": "Intermedio",
    "advanced": "Avanzado",
}
MOTIVATION_NAMES = {
    "appearance": "Mejorar mi apariencia",
    "strength": "Ser más fuerte",
    "health": "Mejorar mi condición física",
    "habit": "Crear hábitos saludables",
    "event": "Prepararme para una fecha/evento",
    "": "—",
}

GYM = {
    "chest": ["Press banca", "Press inclinado con mancuernas", "Aperturas"],
    "back": ["Jalón al pecho", "Remo con barra", "Remo unilateral"],
    "legs": ["Sentadilla", "Prensa", "Zancadas"],
    "shoulders": ["Press militar", "Elevaciones laterales", "Pájaros"],
    "arms": ["Curl de bíceps", "Extensión de tríceps en polea", "Martillo"],
    "glutes": ["Hip thrust", "Peso muerto rumano", "Patada de glúteo"],
    "core": ["Plancha 30-45 s", "Dead bug", "Pallof press"],
}
HOME = {
    "chest": ["Flexiones", "Flexiones inclinadas", "Fondos en silla"],
    "back": ["Remo con mochila", "Superman", "Face pull con banda"],
    "legs": ["Sentadilla", "Zancadas", "Puente de glúteos"],
    "shoulders": ["Press con botellas", "Elevaciones laterales con botellas", "Pike push-up"],
    "arms": ["Curl con botellas", "Fondos de tríceps en silla", "Curl martillo"],
    "glutes": ["Puente de glúteos", "Patada de glúteo a cuatro patas", "Sentadilla sumo"],
    "core": ["Plancha 20-40 s", "Bicho muerto", "Mountain climber lento"],
}


def calculate_calories(user: dict) -> int:
    weight = user["weight"]
    height = user["height"]
    age = user["age"]
    if user["sex"] == "male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    activity = {2: 1.35, 3: 1.45, 4: 1.50, 5: 1.55, 6: 1.60}
    tdee = bmr * activity.get(user["days"], 1.4)

    if user["goal"] == "lose":
        calories = tdee * 0.80
    elif user["goal"] == "gain":
        calories = tdee * 1.10
    else:
        calories = tdee * 0.90
    return int(round(calories))


def macros_for(goal: str, calories: int) -> dict:
    if goal == "lose":
        p, c, f = 0.30, 0.35, 0.35
    elif goal == "gain":
        p, c, f = 0.25, 0.45, 0.30
    else:
        p, c, f = 0.30, 0.40, 0.30
    return {
        "protein_g": int(round(calories * p / 4)),
        "carb_g": int(round(calories * c / 4)),
        "fat_g": int(round(calories * f / 9)),
        "protein_pct": int(p * 100),
        "carb_pct": int(c * 100),
        "fat_pct": int(f * 100),
    }


def generate_menus(user: dict) -> list[dict]:
    proteins = user["proteins"]
    carbs = user["carbs"]
    v = user["vegetables"]
    f = user["fruits"]
    p0, p1 = proteins[0], proteins[1] if len(proteins) > 1 else proteins[0]
    c0, c1 = carbs[0], carbs[1] if len(carbs) > 1 else carbs[0]
    return [
        {
            "name": "Menú 1",
            "breakfast": f"Avena + {p1} + {f[0]}",
            "lunch": f"{p0} + {c0} + {v[0]} + {v[1]}",
            "snack": f"{f[1]} + yogurt griego",
            "dinner": f"{p1} + {c1} + {v[2]}",
        },
        {
            "name": "Menú 2",
            "breakfast": f"Huevos + pan integral + {f[1]}",
            "lunch": f"{p0} + {c1} + {v[2]} + {v[0]}",
            "snack": f"{f[2]} + yogurt griego",
            "dinner": f"{p1} + {c0} + {v[1]}",
        },
        {
            "name": "Menú 3",
            "breakfast": f"Avena + yogurt griego + {f[2]}",
            "lunch": f"{p1} + {c0} + {v[1]} + {v[2]}",
            "snack": f"{f[0]} + yogurt griego",
            "dinner": f"{p0} + {c1} + {v[0]}",
        },
    ]


def _catalog(location: str) -> dict:
    return HOME if location == "home" else GYM


def _sets(experience: str) -> str:
    if experience == "beginner":
        return "3 series x 8-12 reps"
    if experience == "advanced":
        return "4 series x 6-10 reps"
    return "3-4 series x 8-12 reps"


def _day(title: str, moves: list[str], extra: str | None, sets: str) -> dict:
    items = list(moves)
    if extra and extra not in items:
        items.append(extra + " (énfasis)")
    return {"title": title, "sets": sets, "exercises": items}


def generate_workout(user: dict) -> dict:
    cat = _catalog(user["location"])
    sets = _sets(user["experience"])
    focus = user["focusMuscle"]
    extra = None
    if focus != "balanced":
        extra = cat[focus][0]

    days = user["days"]
    if days == 2:
        schedule = [
            _day("Día 1 — Cuerpo completo A", cat["legs"][:2] + cat["chest"][:1] + cat["back"][:1] + cat["core"][:1], extra, sets),
            _day("Día 2 — Cuerpo completo B", cat["legs"][1:] + cat["shoulders"][:1] + cat["back"][1:2] + cat["arms"][:1] + cat["core"][1:2], extra, sets),
        ]
    elif days == 3:
        schedule = [
            _day("Día 1 — Empuje", cat["chest"][:2] + cat["shoulders"][:1] + cat["arms"][1:2], extra, sets),
            _day("Día 2 — Tirón", cat["back"] + cat["arms"][:1], extra, sets),
            _day("Día 3 — Piernas y core", cat["legs"] + cat["glutes"][:1] + cat["core"][:1], extra, sets),
        ]
    elif days == 4:
        schedule = [
            _day("Día 1 — Tren superior A", cat["chest"][:2] + cat["back"][:1] + cat["shoulders"][:1], extra, sets),
            _day("Día 2 — Tren inferior A", cat["legs"] + cat["glutes"][:1], extra, sets),
            _day("Día 3 — Tren superior B", cat["back"][1:] + cat["shoulders"][1:] + cat["arms"], extra, sets),
            _day("Día 4 — Tren inferior B", cat["legs"][1:] + cat["glutes"] + cat["core"][:1], extra, sets),
        ]
    elif days == 5:
        schedule = [
            _day("Día 1 — Empuje", cat["chest"][:2] + cat["shoulders"][:1] + cat["arms"][1:2], extra, sets),
            _day("Día 2 — Tirón", cat["back"] + cat["arms"][:1], extra, sets),
            _day("Día 3 — Piernas", cat["legs"] + cat["glutes"][:1], extra, sets),
            _day("Día 4 — Tren superior", cat["chest"][1:] + cat["back"][1:2] + cat["shoulders"][1:2], extra, sets),
            _day("Día 5 — Tren inferior y core", cat["legs"][1:] + cat["glutes"][1:] + cat["core"], extra, sets),
        ]
    else:
        schedule = [
            _day("Día 1 — Empuje", cat["chest"] + cat["shoulders"][:1], extra, sets),
            _day("Día 2 — Tirón", cat["back"] + cat["arms"][:1], extra, sets),
            _day("Día 3 — Piernas", cat["legs"] + cat["glutes"][:1], extra, sets),
            _day("Día 4 — Empuje (volumen)", cat["chest"][1:] + cat["shoulders"][1:] + cat["arms"][1:], extra, sets),
            _day("Día 5 — Tirón (volumen)", cat["back"][1:] + cat["arms"][:2], extra, sets),
            _day("Día 6 — Piernas y core", cat["legs"][1:] + cat["glutes"] + cat["core"][:1], extra, sets),
        ]

    duration = user["duration"]
    dur_n = int(duration)
    if dur_n <= 30:
        rest = "45-60 s entre series"
    elif user["experience"] == "beginner":
        rest = "90-120 s entre series"
    elif user["experience"] == "advanced":
        rest = "60-90 s entre series"
    else:
        rest = "75-90 s entre series"

    warmup = [
        "3-5 min de marcha, bici o elíptica suave",
        "Movilidad de hombros, cadera y tobillos (1 min cada zona)",
        "1-2 series ligeras del primer ejercicio del día, sin llegar cerca del fallo",
    ]
    if user["location"] == "home":
        warmup[0] = "3-5 min de marcha en el sitio, jumping jacks lentos o shadow squat"

    return {
        "days": days,
        "location": LOCATION_NAMES[user["location"]],
        "location_key": user["location"],
        "focus": FOCUS_NAMES[focus],
        "focus_key": focus,
        "duration": duration,
        "experience": EXPERIENCE_NAMES[user["experience"]],
        "schedule": schedule,
        "rest": rest,
        "tempo": "Bajada de 2-3 s, subida controlada, sin rebotar. Deja 1-2 repeticiones en reserva.",
        "warmup": warmup,
        "cooldown": "2-3 min de caminata y estiramiento suave de la zona trabajada. Nada de estirar en frío ni forzar dolor.",
        "progression": (
            "Semanas 1-4: técnica y rango completo. "
            "Semanas 5-8: añade 1-2 repeticiones o una carga pequeña. "
            "Semanas 9-12: mantén 1-2 repeticiones en reserva y prioriza constancia."
        ),
        "progression_table": [
            ("Semanas 1-4", "Base", "Misma carga. Aprende el movimiento. Si puedes hacer el tope de reps con holgura, sube un poco el peso la semana siguiente."),
            ("Semanas 5-8", "Progreso", "Añade 1-2 reps o la carga más pequeña disponible. No sumes series extra por tu cuenta."),
            ("Semanas 9-11", "Asentar", "Mantén 1-2 repeticiones en reserva. Si duermes mal o duele una articulación, repite la semana, no fuerces."),
            ("Semana 12", "Cierre", "No busques récords. Entrena completo y anota qué te funcionó para el siguiente ciclo."),
        ],
    }


FOOD_SWAPS = {
    "Brócoli": ["Coliflor", "Judías verdes", "Espárragos"],
    "Zanahoria": ["Calabaza", "Remolacha", "Pimentón"],
    "Tomate": ["Pepino", "Pimentón", "Calabacín"],
    "Lechuga": ["Espinaca", "Rúcula", "Col china"],
    "Espinaca": ["Acelga", "Lechuga", "Kale"],
    "Pimentón": ["Tomate", "Zanahoria", "Calabacín"],
    "Pepino": ["Apio", "Lechuga", "Tomate"],
    "Calabacín": ["Berenjena", "Pepino", "Pimentón"],
    "Cebolla": ["Puerro", "Cebolleta", "Ajo en menor cantidad"],
    "Plátano": ["Manzana", "Pera", "Mango"],
    "Manzana": ["Pera", "Kiwi", "Naranja"],
    "Naranja": ["Mandarina", "Kiwi", "Piña"],
    "Frutilla": ["Arándanos", "Frambuesa", "Kiwi"],
    "Arándanos": ["Frutilla", "Moras", "Uvas"],
    "Pera": ["Manzana", "Plátano", "Kiwi"],
    "Piña": ["Naranja", "Mango", "Kiwi"],
    "Kiwi": ["Naranja", "Frutilla", "Manzana"],
    "Uvas": ["Arándanos", "Manzana", "Pera"],
    "Pollo": ["Pavo", "Pescado blanco", "Tofu firme"],
    "Carne magra": ["Pollo", "Pavo", "Legumbres"],
    "Huevos": ["Clara + 1 yema", "Yogurt griego", "Tofu"],
    "Pavo": ["Pollo", "Pescado blanco", "Carne magra"],
    "Yogurt griego": ["Queso fresco batido", "Kéfir", "Huevos"],
    "Legumbres": ["Tofu", "Tempeh", "Pollo"],
    "Arroz": ["Papa", "Quinoa", "Pasta"],
    "Papa": ["Arroz", "Boniatos", "Avena"],
    "Avena": ["Pan integral", "Arroz", "Cereales sin azúcar"],
    "Pasta": ["Arroz", "Papa", "Pan integral"],
    "Pan integral": ["Avena", "Arroz", "Tortilla de maíz"],
}

EX_SWAPS = {
    "Press banca": "Press con mancuernas o flexiones",
    "Press inclinado con mancuernas": "Press banca inclinado o flexiones con pies elevados",
    "Aperturas": "Cruces en polea o flexiones abiertas",
    "Jalón al pecho": "Dominadas asistidas o remo con banda",
    "Remo con barra": "Remo con mancuerna o remo con mochila",
    "Remo unilateral": "Remo en máquina o remo con banda",
    "Sentadilla": "Sentadilla al cajón o prensa",
    "Prensa": "Sentadilla o zancadas",
    "Zancadas": "Step-up o sentadilla búlgara",
    "Press militar": "Press con mancuernas sentado o pike push-up",
    "Elevaciones laterales": "Elevaciones con botellas o banda",
    "Pájaros": "Face pull con banda",
    "Curl de bíceps": "Curl con banda o botellas",
    "Extensión de tríceps en polea": "Fondos en banco o extensión con botella",
    "Martillo": "Curl con botellas en agarre neutro",
    "Hip thrust": "Puente de glúteos a dos piernas",
    "Peso muerto rumano": "Puente de glúteos o good morning con mochila",
    "Patada de glúteo": "Puente a una pierna",
    "Plancha 30-45 s": "Plancha de rodillas o dead bug",
    "Dead bug": "Plancha o bird-dog",
    "Pallof press": "Plancha lateral",
    "Flexiones": "Flexiones de rodillas o contra la pared",
    "Flexiones inclinadas": "Flexiones de rodillas",
    "Fondos en silla": "Extensión de tríceps con mochila",
    "Remo con mochila": "Superman lento o remo con banda",
    "Superman": "Bird-dog",
    "Face pull con banda": "Pájaros con botellas",
    "Puente de glúteos": "Hip thrust en el suelo",
    "Press con botellas": "Pike push-up",
    "Elevaciones laterales con botellas": "Elevaciones con banda",
    "Pike push-up": "Press con botellas sentado",
    "Curl con botellas": "Curl con banda",
    "Fondos de tríceps en silla": "Extensión de tríceps con botella",
    "Curl martillo": "Curl con banda en agarre neutro",
    "Patada de glúteo a cuatro patas": "Puente a una pierna",
    "Sentadilla sumo": "Zancadas o puente de glúteos",
    "Plancha 20-40 s": "Plancha de rodillas",
    "Bicho muerto": "Dead bug o bird-dog",
    "Mountain climber lento": "Plancha + rodilla al pecho lento",
}


def _food_substitutions(user: dict) -> list[tuple[str, str]]:
    chosen = user["vegetables"] + user["fruits"] + user["proteins"] + user["carbs"]
    rows = []
    seen = set()
    for item in chosen:
        if item in seen:
            continue
        seen.add(item)
        alts = FOOD_SWAPS.get(item)
        if alts:
            rows.append((item, " · ".join(alts)))
    return rows


def _exercise_substitutions(workout: dict) -> list[tuple[str, str]]:
    rows = []
    seen = set()
    for day in workout["schedule"]:
        for raw in day["exercises"]:
            name = raw.replace(" (énfasis)", "").strip()
            if name in seen:
                continue
            seen.add(name)
            alt = EX_SWAPS.get(name)
            if alt:
                rows.append((name, alt))
    return rows


def build_habits(user: dict) -> dict:
    water_ml = int(round(user["weight"] * 33))
    water_l = round(water_ml / 1000.0, 1)
    if user["goal"] == "gain":
        steps = "7.000-9.000 pasos / día"
        steps_note = "Suficiente para moverte sin sumar un gasto enorme que frene la ganancia."
    elif user["goal"] == "lose":
        steps = "8.000-10.000 pasos / día"
        steps_note = "Prioriza caminar. No hace falta correr si las rodillas o el peso lo desaconsejan."
    else:
        steps = "8.000-9.500 pasos / día"
        steps_note = "Mantén el paso constante; no lo uses para 'compensar' una comida."
    return {
        "water_ml": water_ml,
        "water_l": water_l,
        "sleep": "7-9 horas",
        "steps": steps,
        "steps_note": steps_note,
        "scale": (
            "Pésate 3 mañanas por semana, en ayunas, y usa el promedio. "
            "Si en 14 días el promedio no se mueve, ajusta 100-150 kcal, no 500."
        ),
    }


def build_intro() -> list[tuple[str, str]]:
    return [
        ("Cómo usar este documento", "Léelo entero una vez. Luego úsalo como guía de 12 semanas, no como un menú de restaurante que hay que copiar al gramo."),
        ("Tu ficha", "Quién eres en este plan: peso, meta, objetivo. Si hay un error, no rellenes otro formulario: escribe a soporte."),
        ("Alimentación", "Calorías y macros de partida, más 3 menús con tus alimentos. Alterna los menús. Las cifras se ajustan si la báscula no se mueve en 14 días."),
        ("Cómo contar calorías y macros", "Una forma simple de registrar lo que comes, para acercarte a los números del plan sin obsesión."),
        ("Entrenamiento", "Rutina por días, calentamiento, descanso, tempo y progresión de las 12 semanas."),
        ("Sustituciones", "Si falta un alimento o un ejercicio, cámbialo por la opción de la tabla. No improvises un tercer entreno extra."),
        ("Hábitos", "Agua, sueño y pasos calculados para ti. Sostienen el plan más que cualquier suplemento."),
        ("Lo que no debes hacer", "Errores que rompen el progreso o el enlace de un solo uso. Léelos antes de empezar."),
    ]


def build_calorie_guide(user: dict, calories: int, macros: dict) -> list[str]:
    return [
        f"Tu objetivo diario es cerca de {calories} kcal, con {macros['protein_g']} g de proteína, {macros['carb_g']} g de carbohidratos y {macros['fat_g']} g de grasa.",
        "1. Elige una app o una libreta. Anota 7 días. No hace falta ser perfecto el día 1.",
        "2. Pesa en crudo (antes de cocinar) las proteínas y los carbos las primeras 2 semanas. Después estima.",
        "3. Recuerda: proteína y carbohidrato aportan 4 kcal por gramo; la grasa, 9 kcal por gramo.",
        "4. Aceite, frutos secos, salsas y alcohol cuentan. Una cucharada de aceite son ~120 kcal.",
        "5. Si un día te pasas, al siguiente vuelves al plan. No 'compensas' saltándote comidas ni alargando el cardio.",
        "6. Revisa el promedio semanal, no el martes a las 22:00.",
    ]


def build_donts() -> list[str]:
    return [
        "No cortes las calorías por debajo de este plan para 'ir más rápido'.",
        "No te saltes comidas para compensar un exceso.",
        "No compares el peso de cada día: usa el promedio de la semana.",
        "No entrenes con dolor agudo, mareo, o si te falta el aire de forma rara.",
        "No copies rutinas de redes ni añadas series extra en las semanas 1-4.",
        "No uses laxantes, diuréticos ni 'quemadores' para ver la báscula.",
        "No reutilices el enlace ni pidas un plan nuevo por un error de datos: ve a soporte.",
        "No abandones el sueño o los pasos para 'hacer más gym'. Sin eso, el plan no sostiene.",
    ]


def build_plan(user: dict) -> dict:
    calories = calculate_calories(user)
    macros = macros_for(user["goal"], calories)
    workout = generate_workout(user)
    return {
        "calories": calories,
        "macros": macros,
        "menus": generate_menus(user),
        "workout": workout,
        "goal_label": GOAL_NAMES[user["goal"]],
        "motivation_label": MOTIVATION_NAMES.get(user.get("motivation") or "", "—"),
        "intro": build_intro(),
        "calorie_guide": build_calorie_guide(user, calories, macros),
        "food_swaps": _food_substitutions(user),
        "exercise_swaps": _exercise_substitutions(workout),
        "habits": build_habits(user),
        "donts": build_donts(),
    }
