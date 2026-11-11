"""Contenido del plan Gary Felicien Fit (formato 12 semanas, negro y dorado).

Todo lo que depende de los datos del usuario se arma aquí. pdf_builder.py solo dibuja.
"""

from __future__ import annotations

from plan import (
    EXPERIENCE_NAMES,
    FOCUS_NAMES,
    FOOD_SWAPS,
    GOAL_NAMES,
    LOCATION_NAMES,
    MOTIVATION_NAMES,
    build_habits,
    calculate_calories,
    macros_for,
)

# ---------------------------------------------------------------- utilidades


def miles(n: float) -> str:
    """1798 -> '1.798'."""
    return f"{int(round(n)):,}".replace(",", ".")


def _r(value: float, step: int = 10) -> int:
    return int(step * round(value / step))


def _scale(calories: int) -> float:
    return max(0.8, min(1.5, calories / 1800.0))


# ---------------------------------------------------------------- alimentos

MAIN_PROTEINS = {"Pollo", "Carne magra", "Pavo", "Huevos", "Legumbres"}
FRUIT_CUP = {"Frutilla", "Arándanos", "Uvas", "Piña"}


def protein_portion(p: str, s: float) -> str:
    if p == "Huevos":
        return f"Huevos {max(2, min(4, round(3 * s)))} un."
    if p == "Yogurt griego":
        return f"Yogurt griego {_r(170 * s)} g"
    if p == "Legumbres":
        return f"Legumbres {_r(200 * s)} g cocidas"
    if p == "Carne magra":
        return f"Carne magra {_r(150 * s)} g cocida"
    return f"{p} {_r(150 * s)} g cocido"


def protein_grams(p: str, s: float) -> str:
    if p == "Huevos":
        return f"{max(2, min(4, round(3 * s)))} huevos"
    if p == "Legumbres":
        return f"{_r(200 * s)} g de legumbres cocidas"
    if p == "Yogurt griego":
        return f"{_r(170 * s)} g de yogurt griego"
    return f"{_r(150 * s)} g de {p}"


def carb_portion(c: str, s: float, half: bool = False) -> str:
    k = 0.5 if half else 1.0
    if c == "Papa":
        return f"Papa {_r(250 * s * k)} g"
    if c == "Pan integral":
        n = max(1, round(2 * s * k))
        return f"Pan integral {n} rebanada{'s' if n > 1 else ''}"
    if c == "Avena":
        return f"Avena {_r(50 * s * k, 5)} g cruda"
    if c == "Pasta":
        return f"Pasta {_r(60 * s * k, 5)} g cruda"
    return f"Arroz {_r(60 * s * k, 5)} g crudo"


def fruit_portion(f: str) -> str:
    if f in FRUIT_CUP:
        return f"{f} 1 taza (~120 g)"
    if f == "Kiwi":
        return "Kiwi 2 un."
    return f"{f} 1 un."


def _rot(items: list[str], i: int) -> str:
    return items[i % len(items)]


def _dish(p: str, c: str, vs: list[str]) -> str:
    veg = ", ".join(vs)
    if p == "Huevos":
        return f"Huevos con {veg} y {c}"
    if p == "Legumbres":
        return f"Legumbres guisadas con {veg} y {c}"
    return f"{p}, {c}, {' y '.join(vs) if len(vs) == 2 else vs[0]}"


def build_menus(user: dict, calories: int) -> list[dict]:
    s = _scale(calories)
    mains = [p for p in user["proteins"] if p in MAIN_PROTEINS] or ["Huevos"]
    carbs = user["carbs"]
    v = user["vegetables"]
    f = user["fruits"]
    p0, p1 = mains[0], _rot(mains, 1)
    c0, c1 = carbs[0], _rot(carbs, 1)
    veg = _r(150 * s)
    oat = _r(50 * s, 5)
    yog = _r(150 * s, 10)

    def meal(kind: str, title: str, detail: str) -> dict:
        return {"kind": kind, "title": title, "detail": detail}

    def lunch(p: str, c: str, a: str, b: str) -> dict:
        return meal(
            "ALMUERZO",
            _dish(p, c, [a, b]),
            f"{protein_portion(p, s)} · {carb_portion(c, s)} · verdura {veg} g + {veg} g",
        )

    def dinner(p: str, c: str, a: str) -> dict:
        title = f"{p} con {c} y {a}" if p not in ("Huevos", "Legumbres") else _dish(p, c, [a])
        return meal("CENA", title, f"{protein_portion(p, s)} · {carb_portion(c, s)} · {a} {veg} g")

    def snack(fr: str) -> dict:
        return meal("MERIENDA", f"{fr} y yogurt griego", f"{fruit_portion(fr)} · yogurt {yog} g")

    eggs = max(2, min(4, round(3 * s)))
    bread = max(2, round(2 * s))
    return [
        {
            "name": "Menú 01",
            "days": "Lun · Jue",
            "meals": [
                meal("DESAYUNO", f"Avena con yogurt griego y {f[0]}",
                     f"Avena {oat} g cruda · Yogurt griego {yog} g · {fruit_portion(f[0])}"),
                lunch(p0, c0, v[0], v[1]),
                snack(f[1]),
                dinner(p1, c1, v[2]),
            ],
        },
        {
            "name": "Menú 02",
            "days": "Mar · Vie",
            "meals": [
                meal("DESAYUNO", f"Huevos, pan integral y {f[1]}",
                     f"Huevos {eggs} un. · pan {bread} rebanadas · {fruit_portion(f[1])}"),
                lunch(p0, c1, v[2], v[0]),
                snack(f[2]),
                dinner(p1, c0, v[1]),
            ],
        },
        {
            "name": "Menú 03",
            "days": "Mié · Sáb",
            "meals": [
                meal("DESAYUNO", f"Avena, yogurt y {f[2]}",
                     f"Avena {oat} g cruda · yogurt {yog} g · {fruit_portion(f[2])}"),
                lunch(p1, c0, v[1], v[2]),
                snack(f[0]),
                dinner(p0, c1, v[0]),
            ],
        },
        {
            "name": "Menú 04",
            "days": "Domingo · extra",
            "meals": [
                meal("DESAYUNO", f"Tostadas con huevo y {f[0]}",
                     f"Pan {bread} rebanadas · huevos {max(2, eggs - 1)} un. · {fruit_portion(f[0])}"),
                meal("ALMUERZO", f"Plato único: {p0}, {c0} y {v[0]} + {v[1]}",
                     f"{protein_portion(p0, s)} · {carb_portion(c0, s)} · verdura {veg * 2} g"),
                meal("MERIENDA", f"{f[1]} o {f[2]}", "1 porción (~120 g)"),
                meal("CENA", f"Cena ligera: {p1}, {v[2]} y media porción de {c1}",
                     f"{protein_portion(p1, s)} · {v[2]} {_r(200 * s)} g · {carb_portion(c1, s, half=True)}"),
            ],
        },
    ]


def _cook_protein(p: str) -> str:
    if p == "Huevos":
        return "Bate los huevos y cuájalos a fuego medio-bajo, sin secarlos. Reserva."
    if p == "Legumbres":
        return "Las legumbres cocidas (enjuagadas y escurridas) se calientan 3-4 min. Reserva."
    if p == "Yogurt griego":
        return "El yogurt va frío, al final. No se cocina."
    return f"El {p} va 4-6 min por lado (o se calienta si ya está cocido). Reserva."


def _cook_carb(c: str) -> str:
    if c == "Papa":
        return "La papa, hervida 15-20 min o al horno en cubos. Reserva."
    if c == "Pan integral":
        return "El pan integral se tuesta al final, para que no se ablande."
    if c == "Avena":
        return "La avena se cocina 3-4 min con agua o se hidrata 5 min fuera del fuego."
    return f"El {c.lower()} se cuece según el paquete, hasta que esté tierno. Reserva."


def build_recipes(user: dict, calories: int) -> list[dict]:
    s = _scale(calories)
    mains = [p for p in user["proteins"] if p in MAIN_PROTEINS] or ["Huevos"]
    carbs = user["carbs"]
    v = user["vegetables"]
    f = user["fruits"]
    p0, p1 = mains[0], _rot(mains, 1)
    c0, c1 = carbs[0], _rot(carbs, 1)
    veg = _r(150 * s)
    return [
        {
            "title": f"Sartén de {p0} y {v[0]}",
            "meta": "20 min · 1 plato",
            "ingredients": [
                f"{protein_grams(p0, s)}" + (" (cocido o a la plancha)" if p0 not in ("Huevos", "Legumbres") else ""),
                f"{veg} g de {v[0]} y 100 g de {v[1]}",
                "1 cucharadita de aceite (5 ml)",
                "Sal, pimienta, ajo o limón al gusto",
            ],
            "steps": [
                "Corta la verdura en trozos parejos. Sartén a fuego medio, una cucharadita de aceite.",
                _cook_protein(p0),
                f"Saltea {v[0]} y {v[1]} 5 min. Vuelve la proteína 1 min. Sirve.",
            ],
        },
        {
            "title": f"Bowl de {c0} con {p1}",
            "meta": "25 min · 1 bowl",
            "ingredients": [
                f"{carb_portion(c0, s)}",
                f"{protein_portion(p1, s)}",
                f"{veg} g de {v[2]}",
                f"{fruit_portion(f[0])} de acompañamiento (opcional)",
            ],
            "steps": [
                _cook_carb(c0),
                _cook_protein(p1),
                f"Arma el bowl: {c0} abajo, {p1}, {v[2]} al lado. Un chorrito de limón alcanza.",
            ],
        },
        {
            "title": f"Desayuno rápido de avena y {f[0]}",
            "meta": "8 min · 1 bowl",
            "ingredients": [
                f"{_r(50 * s, 5)} g de avena cruda",
                f"{_r(150 * s)} g de yogurt griego o 200 ml de agua/leche",
                f"{fruit_portion(f[0])}, en trozos",
                "Canela al gusto (opcional, sin azúcar extra)",
            ],
            "steps": [
                "Avena con agua o leche 3-4 min a fuego bajo, o hidratada 5 min fuera del fuego.",
                "Si usas yogurt, mézclalo al final. No hace falta endulzar.",
                f"Cierra con {f[0]}. Si entrenas en la mañana, come 45-60 min antes.",
            ],
        },
        {
            "title": f"Wrap o tostada de {p0}",
            "meta": "12 min · 1 plato",
            "ingredients": [
                "2 rebanadas de pan integral o 1 tortilla",
                f"{protein_grams(p0, s)}",
                f"80 g de {v[0]} o {v[1]} en tiras",
                "1 cucharada de yogurt griego o 1 cucharadita de aceite",
            ],
            "steps": [
                "Si la proteína está fría, un minuto a la sartén. Verdura en tiras.",
                "Arma el pan o wrap: proteína, verdura, un poco de yogurt.",
                "Come despacio. Si es almuerzo, añade una fruta al lado.",
            ],
        },
        {
            "title": f"Huevos con {v[1]} y {c0}",
            "meta": "15 min · 1 plato",
            "ingredients": [
                "2-3 huevos",
                f"120 g de {v[1]}",
                f"{carb_portion(c0, s, half=True)} (media porción)",
                "Pimienta y un toque de aceite",
            ],
            "steps": [
                f"{v[1]} a la sartén 3 min. Reserva al borde.",
                "Huevos revueltos o estrellados a fuego medio-bajo.",
                f"Plato: huevos, {v[1]} y {c0}. Desayuno o cena ligera.",
            ],
        },
        {
            "title": f"Ensalada tibia de {v[2]} y {p1}",
            "meta": "15 min · 1 bowl",
            "ingredients": [
                f"{protein_grams(p1, s)}",
                f"{veg} g de {v[2]} y 80 g de {v[0]}",
                f"{fruit_portion(f[1])} en cubos (opcional)",
                "Limón y pimienta",
            ],
            "steps": [
                "Proteína a temperatura: plancha corta o del tupper. Verdura cruda o apenas salteada.",
                "Todo al bowl. El limón sustituye a salsas calóricas.",
                f"Si entrenaste, añade media porción extra de {c1}.",
            ],
        },
    ]


def build_shopping(user: dict, calories: int) -> list[tuple[str, str]]:
    s = _scale(calories)
    mains = [p for p in user["proteins"] if p in MAIN_PROTEINS] or ["Huevos"]
    rows: list[tuple[str, str]] = []
    share = 1.0 / len(mains[:2])
    for p in mains[:2]:
        if p == "Huevos":
            continue
        lo, hi = 2.0 * share * s, 2.4 * share * s
        if p == "Legumbres":
            rows.append(("Legumbres", f"{_r(lo * 500, 50)}–{_r(hi * 500, 50)} g secas (o 4–5 tarros)"))
        else:
            rows.append((p, f"{lo:.1f}–{hi:.1f} kg (crudo)".replace(".", ",")))
    rows.append(("Yogurt griego", f"{_r(1.2 * s * 1000, 100) / 1000:.1f} kg (o 8 potes de 150 g)".replace(".", ",")))
    for c in user["carbs"]:
        amount = {
            "Arroz": "500 g (crudo)",
            "Pasta": "500 g",
            "Papa": "2 kg",
            "Avena": "500 g",
            "Pan integral": "1 bolsa (o 14 rebanadas)",
        }[c]
        rows.append((c, amount))
    if "Avena" not in user["carbs"]:
        rows.append(("Avena (desayunos)", "400 g (bolsa chica)"))
    if "Pan integral" not in user["carbs"]:
        rows.append(("Pan integral (desayunos)", "1 bolsa chica"))
    rows += [
        ("Verduras de tu lista", f"{', '.join(user['vegetables'])} · ~3 kg en total a la semana"),
        ("Frutas de tu lista", f"{', '.join(user['fruits'])} · ~8–10 porciones"),
        ("Huevos", "1 bandeja de 12" if "Huevos" not in mains else "2 bandejas de 12"),
        ("Aceite", "1 botella chica · 1 cucharadita/comida, no a ojo"),
        ("Limón, ajo, especias", "Lo que uses para no aburrirte del mismo plato"),
    ]
    return rows


# ---------------------------------------------------------------- energía


def build_energy(user: dict, calories: int) -> dict:
    w, h, a = user["weight"], user["height"], user["age"]
    bmr = 10 * w + 6.25 * h - 5 * a + (5 if user["sex"] == "male" else -161)
    activity = {2: 1.35, 3: 1.45, 4: 1.50, 5: 1.55, 6: 1.60}
    tdee = bmr * activity.get(user["days"], 1.4)
    eat = user["days"] * int(user["duration"]) * 6 / 7.0
    eta = tdee * 0.08
    neat = max(0.0, tdee - bmr - eat - eta)
    parts = [
        ("Reposo (TMB)", bmr),
        ("Moverte en el día (NEAT)", neat),
        ("Entreno (EAT)", eat),
        ("Digerir (ETA)", eta),
    ]
    rows = [(label, f"{miles(v)} kcal · {round(100 * v / tdee)}%") for label, v in parts]
    b, t, c = miles(bmr), miles(tdee), miles(calories)
    goal = user["goal"]
    if goal == "lose":
        text = (
            f"En reposo tu cuerpo ya gasta unas {b} kcal (TMB). En un día normal, sumando movimiento, "
            f"entreno y digerir, rondas {t} kcal. El plan te deja en {c} kcal. Esa cifra no debe caer por "
            "debajo de tu TMB de forma prolongada: ahí el cuerpo entra en alarma, pierdes músculo y el hambre "
            "se vuelve feroz. Por eso no recortamos «a lo loco»."
        )
    elif goal == "gain":
        text = (
            f"En reposo tu cuerpo ya gasta unas {b} kcal (TMB). En un día normal, sumando movimiento, "
            f"entreno y digerir, rondas {t} kcal. El plan te deja en {c} kcal: un margen pequeño por encima "
            "de tu gasto para construir músculo. Más no es mejor: subir muy rápido es, sobre todo, grasa."
        )
    else:
        text = (
            f"En reposo tu cuerpo ya gasta unas {b} kcal (TMB). En un día normal, sumando movimiento, "
            f"entreno y digerir, rondas {t} kcal. El plan te deja en {c} kcal, un poco por debajo de tu gasto: "
            "suficiente para entrenar fuerte y bajar grasa sin perder músculo."
        )
    return {"bmr": bmr, "tdee": tdee, "rows": rows, "text": text}


def build_science(goal: str) -> list[str]:
    ego = (
        "El ego en el gym y las horas de cinta sin progresión de carga no construyen nada. "
        "Tensión con técnica, no sudor por sudar."
    )
    if goal == "lose":
        return [
            "La grasa que más importa no es la del espejo: es la visceral, alrededor de órganos. "
            "La fuerza + el déficit la bajan mejor que solo el cardio.",
            "Músculo = mejor manejo de la glucosa y menos inflamación de bajo grado. "
            "No entrenas solo para «la panza».",
            ego,
        ]
    if goal == "gain":
        return [
            "Para ganar músculo hace falta un pequeño superávit y una carga que progresa. "
            "Comer de más sin entrenar duro solo suma grasa.",
            "La proteína repartida en 3-4 comidas y el sueño hacen el trabajo que el gym empieza.",
            ego,
        ]
    return [
        "Comer cerca de tu gasto y entrenar fuerza cambia la composición aunque la báscula se mueva poco. "
        "Mira la cintura y la ropa, no solo el número.",
        "Músculo = mejor manejo de la glucosa y menos inflamación de bajo grado.",
        ego,
    ]


# ---------------------------------------------------------------- entrenamiento
# (nombre, pista, alternativa)

GYM = {
    "legs_c": [
        ("Prensa", "Pies a la anchura de cadera. No bloquees las rodillas arriba.", "Sentadilla en máquina guiada"),
        ("Sentadilla en máquina guiada", "Espalda apoyada. Baja hasta donde mantengas la lumbar neutra.", "Prensa o sentadilla goblet"),
        ("Zancadas con mancuernas", "Paso largo, rodilla de atrás cerca del suelo. Tronco alto.", "Step-up al cajón"),
    ],
    "legs_i": [
        ("Extensión de cuádriceps", "Sube en 1 s, baja en 3 s. Sin impulso.", "Sentadilla goblet lenta"),
        ("Curl femoral en máquina", "Cadera pegada al asiento. Baja lento.", "Peso muerto rumano ligero"),
    ],
    "glutes_c": [
        ("Hip thrust en máquina", "Mentón metido. Empuja con talones. Pausa 1 s arriba.", "Hip thrust con barra o puente"),
        ("Peso muerto rumano con mancuernas", "Cadera atrás, espalda neutra, mancuernas pegadas a las piernas.", "Hip thrust o good morning ligero"),
    ],
    "glutes_i": [
        ("Abducción en máquina", "Tronco quieto. Abre controlado, pausa 1 s.", "Abducción con banda"),
        ("Patada de glúteo en polea", "Cadera quieta. Aprieta arriba sin arquear la lumbar.", "Patada a cuatro patas"),
    ],
    "chest_c": [
        ("Press de pecho en máquina", "Escápulas contra el respaldo. No bloquees los codos. Recorre completo.", "Press banca o press con mancuernas"),
        ("Press inclinado con mancuernas", "Banco a 30°. Baja hasta la línea del pecho, codos a 45°.", "Press inclinado en máquina"),
    ],
    "chest_i": [
        ("Aperturas en máquina", "Codos ligeramente flexionados. Junta sin chocar.", "Cruces en polea"),
    ],
    "back_c": [
        ("Jalón al pecho", "Pecho arriba, barra a la clavícula. No te cuelgues de los brazos.", "Dominada asistida o remo en máquina"),
        ("Remo en máquina", "Pecho alto. Codos junto al cuerpo. No uses impulso de lumbar.", "Remo unilateral o jalón al pecho"),
        ("Remo unilateral con mancuerna", "Espalda plana. Lleva el codo hacia la cadera.", "Remo en máquina"),
    ],
    "back_i": [
        ("Face pull en polea", "Cuerda a la frente, codos altos. Abre al final.", "Pájaros con mancuernas"),
    ],
    "shoulders_c": [
        ("Press de hombros en máquina", "No encojas los trapecios. Recorre sin arquear la lumbar.", "Press militar sentado"),
    ],
    "shoulders_i": [
        ("Elevaciones laterales", "Codos altos, muñeca relajada. Para a la altura del hombro.", "Elevaciones en máquina o con banda"),
        ("Pájaros en máquina", "Brazos casi rectos. Abre con la espalda alta, sin impulso.", "Face pull en polea"),
    ],
    "arms_i": [
        ("Curl en máquina", "Codos fijos al apoyo. Baja en 3 s.", "Curl de bíceps"),
        ("Extensión de tríceps en polea", "Codos pegados al cuerpo. Extiende completo sin balancearte.", "Fondos en banco"),
        ("Curl martillo", "Agarre neutro. Sin balanceo del tronco.", "Curl en polea con cuerda"),
    ],
    "core": [
        ("Plancha 30-45 s", "Costillas adentro, glúteos firmes. No dejes caer la cadera.", "Plancha de rodillas o dead bug"),
        ("Dead bug", "Lumbar pegada al suelo. Brazo y pierna opuestos, lento.", "Plancha o bird-dog"),
        ("Pallof press", "De lado a la polea. Empuja al frente sin dejar que te gire.", "Plancha lateral"),
    ],
}

HOME = {
    "legs_c": [
        ("Sentadilla", "Pies a la anchura de hombros. Baja con el pecho alto.", "Sentadilla a la silla"),
        ("Zancadas atrás", "Paso largo hacia atrás. Rodilla de adelante estable.", "Step-up en silla firme"),
        ("Sentadilla búlgara en silla", "Pie trasero en la silla. Baja recto, sin prisa.", "Zancadas atrás"),
    ],
    "legs_i": [
        ("Sentadilla isométrica en pared", "Espalda pegada a la pared, muslos casi paralelos al suelo.", "Sentadilla lenta (4 s bajada)"),
        ("Step-up en silla firme", "Sube empujando con el talón de arriba. Baja lento.", "Zancadas atrás"),
    ],
    "glutes_c": [
        ("Puente de glúteos", "Mentón metido. Empuja con talones. Pausa 1 s arriba.", "Hip thrust en el suelo"),
        ("Peso muerto rumano con mochila", "Cadera atrás, espalda neutra, mochila pegada a las piernas.", "Puente de glúteos a una pierna"),
    ],
    "glutes_i": [
        ("Patada de glúteo a cuatro patas", "Cadera quieta. Aprieta arriba sin arquear la lumbar.", "Puente a una pierna"),
        ("Abducción con banda", "Tumbado de lado o de pie. Abre controlado.", "Abducción tumbado sin banda"),
    ],
    "chest_c": [
        ("Flexiones", "Cuerpo en bloque. Pecho al suelo, codos a 45°.", "Flexiones de rodillas o contra la pared"),
        ("Flexiones inclinadas en silla", "Manos en la silla. Más fácil que en el suelo, misma técnica.", "Flexiones contra la pared"),
    ],
    "chest_i": [
        ("Flexiones abiertas lentas", "Manos más anchas. Baja en 3 s.", "Flexiones de rodillas"),
    ],
    "back_c": [
        ("Remo con mochila", "Espalda plana. Lleva el codo hacia la cadera.", "Remo con banda"),
        ("Remo con banda", "Pecho alto. Aprieta las escápulas al final.", "Remo con mochila"),
        ("Remo invertido bajo la mesa", "Mesa firme. Cuerpo en bloque, pecho al borde.", "Remo con mochila"),
    ],
    "back_i": [
        ("Superman", "Sube brazos y piernas a la vez, pausa 2 s, sin dolor lumbar.", "Bird-dog"),
        ("Face pull con banda", "Banda a la frente, codos altos. Abre al final.", "Pájaros con botellas"),
    ],
    "shoulders_c": [
        ("Pike push-up", "Cadera alta. Lleva la cabeza por delante de las manos.", "Press con botellas sentado"),
        ("Press con botellas", "Sentado, espalda apoyada. Sube sin arquear la lumbar.", "Pike push-up"),
    ],
    "shoulders_i": [
        ("Elevaciones laterales con botellas", "Codos suaves. Para a la altura del hombro.", "Elevaciones con banda"),
        ("Pájaros con botellas", "Tronco inclinado, espalda plana. Abre sin impulso.", "Face pull con banda"),
    ],
    "arms_i": [
        ("Curl con botellas", "Codos quietos. Baja en 3 s.", "Curl con banda"),
        ("Fondos de tríceps en silla", "Hombros lejos de las orejas. Baja hasta 90° de codo.", "Extensión de tríceps con botella"),
        ("Curl martillo con botellas", "Agarre neutro. Sin balanceo del tronco.", "Curl con banda en agarre neutro"),
    ],
    "core": [
        ("Plancha 20-40 s", "Costillas adentro, glúteos firmes. No dejes caer la cadera.", "Plancha de rodillas"),
        ("Dead bug", "Lumbar pegada al suelo. Brazo y pierna opuestos, lento.", "Plancha o bird-dog"),
        ("Mountain climber lento", "Hombros sobre las manos. Rodilla al pecho sin saltar.", "Plancha + rodilla al pecho"),
    ],
}

GROUP_OF = {
    "legs": ("legs_c", "legs_i"),
    "glutes": ("glutes_c", "glutes_i"),
    "chest": ("chest_c", "chest_i"),
    "back": ("back_c", "back_i"),
    "shoulders": ("shoulders_c", "shoulders_i"),
    "arms": ("arms_i",),
}

PUSH = ["chest_c:0", "shoulders_c:0", "chest_c:1", "shoulders_i:0", "arms_i:1", "chest_i:0", "core:0"]
PULL = ["back_c:0", "back_c:1", "back_c:2", "back_i:0", "arms_i:0", "arms_i:2", "core:1"]
LEGS = ["legs_c:0", "glutes_c:0", "legs_c:1", "legs_i:0", "glutes_i:0", "legs_i:1", "core:0"]

TEMPLATES = {
    2: [
        ("Cuerpo completo A", ["legs_c:0", "chest_c:0", "back_c:0", "shoulders_i:0", "core:0", "legs_i:0", "arms_i:1"]),
        ("Cuerpo completo B", ["glutes_c:0", "back_c:1", "shoulders_c:0", "arms_i:0", "core:1", "chest_c:1", "glutes_i:0"]),
    ],
    3: [("Empuje", PUSH), ("Tirón", PULL), ("Piernas y core", LEGS)],
    4: [
        ("Tren superior A", ["chest_c:0", "back_c:0", "shoulders_c:0", "back_c:1", "arms_i:0", "arms_i:1", "shoulders_i:0"]),
        ("Tren inferior A", ["legs_c:0", "glutes_c:0", "legs_i:0", "legs_i:1", "core:0", "glutes_i:0", "legs_c:2"]),
        ("Tren superior B", ["back_c:2", "chest_c:1", "shoulders_i:0", "back_i:0", "chest_i:0", "arms_i:2", "arms_i:1"]),
        ("Tren inferior B", ["glutes_c:1", "legs_c:1", "glutes_i:0", "legs_i:1", "core:1", "legs_i:0", "core:2"]),
    ],
    5: [
        ("Empuje", PUSH),
        ("Tirón", PULL),
        ("Piernas", LEGS),
        ("Tren superior", ["chest_c:1", "back_c:2", "shoulders_i:0", "back_i:0", "arms_i:0", "arms_i:1", "chest_i:0"]),
        ("Tren inferior y core", ["glutes_c:1", "legs_c:2", "glutes_i:1", "core:1", "core:2", "legs_i:0", "glutes_i:0"]),
    ],
    6: [
        ("Empuje A", PUSH),
        ("Tirón A", PULL),
        ("Piernas A", LEGS),
        ("Empuje B", ["shoulders_c:0", "chest_c:1", "shoulders_i:0", "chest_i:0", "arms_i:1", "shoulders_i:1", "core:2"]),
        ("Tirón B", ["back_c:1", "back_c:2", "back_i:0", "arms_i:0", "arms_i:2", "back_c:0", "core:1"]),
        ("Piernas B y core", ["glutes_c:0", "legs_c:2", "glutes_i:0", "legs_i:1", "core:0", "glutes_c:1", "legs_i:0"]),
    ],
}

WEEKDAYS = {
    2: ["Lunes", "Jueves"],
    3: ["Lunes", "Miércoles", "Viernes"],
    4: ["Lunes", "Martes", "Jueves", "Viernes"],
    5: ["Lunes", "Martes", "Miércoles", "Viernes", "Sábado"],
    6: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
}

WHY = {
    2: "El plan usa cuerpo completo A y B, para que cada músculo grande entre dos veces por semana.",
    3: "El plan separa empuje, tirón y piernas: cada sesión trabaja fuerte un bloque y deja descansar los demás.",
    4: "El plan alterna tren superior e inferior: cada músculo grande entra dos veces por semana con descanso entre medio.",
    5: "El plan combina empuje, tirón y piernas con dos sesiones de refuerzo para sumar volumen sin repetir el mismo músculo seguido.",
    6: "El plan repite empuje, tirón y piernas dos veces: más volumen, pero cada sesión es más corta y concreta.",
}


def _slot(cat: dict, token: str):
    key, idx = token.split(":")
    items = cat[key]
    return key, items[int(idx) % len(items)]


def _reps(experience: str, location: str) -> dict:
    if location == "home":
        comp, iso = "8-12", "12-20"
    else:
        comp, iso = "6-8", "10-15"
    if experience == "beginner":
        comp = "8-10" if location == "gym" else "8-12"
    sets = {"beginner": 2, "intermediate": 3, "advanced": 4}[experience]
    return {"sets": sets, "comp": comp, "iso": iso, "core": "30-45 s" if location == "gym" else "20-40 s"}


def build_training(user: dict) -> dict:
    loc = user["location"]
    cat = GYM if loc == "gym" else HOME
    exp = user["experience"]
    focus = user["focusMuscle"]
    days = user["days"]
    dur = int(user["duration"])
    count = {30: 4, 45: 5, 60: 6, 75: 7, 90: 7}.get(dur, 5)
    r = _reps(exp, loc)
    short = dur <= 30
    rest = {
        "c": "90-120 s" if short else "120-180 s",
        "i": "45-60 s" if short else "60-90 s",
        "core": "30-60 s",
    }
    focus_keys = GROUP_OF.get(focus, ())
    sessions = []
    seen_all: dict[str, str] = {}
    for n, (title, tokens) in enumerate(TEMPLATES[days], start=1):
        chosen = []
        names = set()
        for tok in tokens:
            if len(chosen) >= count:
                break
            key, ex = _slot(cat, tok)
            if ex[0] in names:
                continue
            names.add(ex[0])
            chosen.append((key, ex))
        if focus_keys and not any(k in focus_keys for k, _ in chosen):
            fk = focus_keys[-1]
            fex = cat[fk][0]
            if fex[0] not in names:
                # reemplaza el último ejercicio que no sea core
                for i in range(len(chosen) - 1, -1, -1):
                    if chosen[i][0] != "core":
                        chosen[i] = (fk, fex)
                        break
        rows = []
        marked = False
        for i, (key, (name, tip, alt)) in enumerate(chosen, start=1):
            if key == "core":
                scheme, rr = f"{r['sets']} × {r['core']}", rest["core"]
            elif key.endswith("_c"):
                scheme, rr = f"{r['sets']} × {r['comp']}", rest["c"]
            else:
                scheme, rr = f"{r['sets']} × {r['iso']}", rest["i"]
            label = name
            if focus_keys and key in focus_keys and not marked:
                label = f"{name} · énfasis"
                marked = True
            rows.append({"name": f"{i}. {label}", "tip": tip, "scheme": scheme, "rest": rr})
            seen_all.setdefault(name, alt)
        sessions.append(
            {
                "title": f"Día {n} — {title}",
                "header": f"{r['sets']} series × {r['comp']} / {r['iso']}",
                "rows": rows,
                "label": title,
            }
        )
    exp_name = EXPERIENCE_NAMES[exp]
    why = (
        f"Elegiste {days} días en {'gimnasio' if loc == 'gym' else 'casa'}, nivel {exp_name.lower()}. "
        f"{WHY[days]} La constancia de 12 semanas importa más que copiar un split de influencer."
    )
    progression = [
        ("Semanas 1-4", "Base",
         f"Misma carga. Aprende el movimiento. Principiante: 2 series. Si llegas al tope de reps con holgura, sube un poco el peso."),
        ("Semanas 5-8", "Doble progresión",
         f"Cuando llegas al máximo del rango ({r['comp']} o {r['iso']}) con buena técnica, sube la carga y vuelve al piso del rango. Principiante pasa a 3 series."),
        ("Semanas 9-11", "Asentar",
         "Sigue la doble progresión. 1-2 repeticiones en reserva. Si duele una articulación, repite la semana."),
        ("Semana 12", "Cierre", "No busques récords. Entrena completo y anota qué te funcionó para el siguiente ciclo."),
    ]
    warm = "Activación general corta (3-5 min suaves)." if loc == "gym" else "Activación general corta (3-5 min de marcha en el sitio o jumping jacks lentos)."
    first = (
        f"Primera sesión: elige un peso con el que te queden 1-2 repeticiones en reserva al final de la última serie. "
        f"Si las {r['comp'].split('-')[1]} van fáciles, sube. Si fallas antes de {r['comp'].split('-')[0]}, baja. "
        "Anota el kilo en el planner. Ese número es tuyo, no el de la máquina del lado."
    )
    if loc == "home":
        first = (
            "Primera sesión: elige una variante (más fácil o más difícil) con la que te queden 1-2 repeticiones en reserva "
            f"al final de la última serie. Si las {r['comp'].split('-')[1]} van fáciles, pasa a la variante más difícil o suma "
            "peso a la mochila. Anota lo que hiciste en el planner."
        )
    return {
        "sessions": sessions,
        "stats1": [
            ("Frecuencia", f"{days} días"),
            ("Lugar", LOCATION_NAMES[loc]),
            ("Sesión", f"{dur} min"),
            ("Foco", "Equilibrado" if focus == "balanced" else FOCUS_NAMES[focus]),
        ],
        "stats2": [
            ("Descanso", "según ejercicio"),
            ("Tempo", "2-3 s bajada"),
            ("Reserva", "1-2 reps"),
            ("Nivel", exp_name),
        ],
        "rest_line": f"Compuestos {rest['c'].replace('-', '–')} · aislamientos {rest['i'].replace('-', '–')} · core {rest['core'].replace('-', '–')}",
        "why": why,
        "distribution": list(zip(WEEKDAYS[days], [s["label"] for s in sessions])),
        "first_day": first,
        "warmup": [
            warm,
            "Movilidad de la zona que toca el día (hombros en tren superior, cadera y tobillo en tren inferior).",
            "1-2 series ligeras del primer ejercicio, sin llegar cerca del fallo.",
        ],
        "progression": progression,
        "cooldown": "2-3 min de actividad suave y estiramiento ligero de la zona trabajada. Nada de estirar en frío ni forzar dolor.",
        "exercise_swaps": list(seen_all.items()),
    }


def build_food_swaps(user: dict) -> list[tuple[str, str]]:
    rows, seen = [], set()
    for item in user["vegetables"] + user["fruits"] + user["proteins"] + user["carbs"]:
        if item in seen:
            continue
        seen.add(item)
        alts = FOOD_SWAPS.get(item)
        if alts:
            rows.append((item, " · ".join(alts)))
    return rows


# ---------------------------------------------------------------- plan completo


def build_full_plan(user: dict) -> dict:
    calories = calculate_calories(user)
    macros = macros_for(user["goal"], calories)
    habits = build_habits(user)
    return {
        "calories": calories,
        "macros": macros,
        "goal_label": GOAL_NAMES[user["goal"]],
        "motivation_label": MOTIVATION_NAMES.get(user.get("motivation") or "", "—"),
        "location_label": LOCATION_NAMES[user["location"]],
        "experience_label": EXPERIENCE_NAMES[user["experience"]],
        "focus_label": FOCUS_NAMES[user["focusMuscle"]],
        "energy": build_energy(user, calories),
        "science": build_science(user["goal"]),
        "menus": build_menus(user, calories),
        "recipes": build_recipes(user, calories),
        "shopping": build_shopping(user, calories),
        "training": build_training(user),
        "food_swaps": build_food_swaps(user),
        "habits": habits,
    }
