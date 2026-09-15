# Historial de cambios y por qué

Registro de decisiones de producto y técnica de **GaryFelicienFit**. No es un changelog de cada commit: es **qué se decidió, por qué, y qué quedó fuera**.

Productos actuales:

1. **Plan personalizado 12 semanas** (antes “guía”) — ~USD $40 / CLP, PDF de un solo uso.
2. **Acompañamiento 3 meses** — $450.000 CLP (50% con código por correo) — área de alumno, planner, videos.

---

## 2026-09 — Tienda y cobro

### De Netlify a Shopify, y luego **fuera de Shopify**

- **Por qué se pensó Shopify:** caja, checkout y Mercado Pago en Chile sin mantener Netlify Functions.
- **Por qué se salió:** la vitrina y el diseño se controlan mejor en el repo (`web/`) + Railway. Shopify dejaba la página blanca/genérica y cada cambio era pegar Liquid a mano.
- **Qué quedó:** cobro del PDF por **Mercado Pago en esta web** (`/api/checkout`). El de 3 meses, por ahora, **WhatsApp** tras código de descuento.
- **Qué no se hace:** volver a Shopify.

### Railway ahora, **host propio después**

- **Por qué Railway:** el backend Python (PDF, webhook, `/alumno`) tiene que estar 24/7.
- **Por qué no atarse:** van a un VPS. El código usa `.env` (`APP_URL`, `HOST`, `PORT`, `DATA_DIR`, Resend/SMTP). Sin nombres de Railway en la lógica.
- **Pausa hasta el host propio:** login de producción, disco persistente “serio”, cron de recordatorios. En Railway el SQLite **puede borrarse** al redesplegar si no hay volumen.

### Login abierto (`PIN 12345` + cualquier mail)

- **Por qué:** poder **diseñar y probar** el planner sin crear alumnos a mano.
- **Por qué no es el modelo final:** con alumnos de pago cualquiera vería/ensuciaría datos.
- **Después, en el host:** PIN único o magic link; flag `ALUMNO_OPEN_LOGIN` para apagar el modo diseño.

---

## 2026-09 — Copy y modelos de la landing

### “Guía” / “PDF” → **plan personalizado**

- **Por qué:** “guía” suena a PDF genérico. El producto es un plan a medida de 12 semanas. En la web pública no se vende “el PDF”, se vende el plan (el archivo sigue existiendo por detrás).

### Dos modelos: **bajar de peso** y **recomposición corporal**

- **Por qué:** un solo PDF genérico no cierra ads. Misma estructura de 12 semanas, distinto enfoque.
- **Vitalidad se descartó:** se reemplazó por **recomposición** (grasa ↓, músculo cuidado). `/vitalidad` redirige a `/recomposicion`.
- **Ads:** `/empezar` (cuestionario) reparte a `/bajar` o `/recomposicion`. No hace falta una landing por cada combinación de preguntas.

### Calculadora en la web (no en Shopify)

- **Por qué:** IMC / TMB / GET orientan y empujan al modelo. Cálculo **local**, sin APIs.

### Oferta 3 meses + popup 50%

- **Por qué:** el PDF de $40 no es el negocio de acompañamiento. El curso es 3 meses, $450.000.
- **50% al dejar el correo:** el código (`GARY50-…`) va **por email**, no se muestra en la página (evita que copien el precio tachado sin dejar lead).
- **Popup:** “¿Quieres 50% de descuento?” + email. En `/3meses` se abre solo la primera vez.

### Quien compra la **guía** recibe incentivo al curso

- **Por qué:** no canibalizar: el de $40 ya pagó; el salto al acompañamiento es **precio vigente del curso − lo que pagó la guía**.
- **No** es el 50% del popup (eso es otro canal). Es un cupón tipo `GUIA-…` atado a ese email.

---

## 2026-09 — Área de alumnos (`/alumno`)

### Planner digital (hábitos, cargas, dashboard)

- **Por qué:** el acompañamiento 3 meses promete seguimiento real. Hábitos configurables (agua, sueño, pasos, Coca-Cola, macros, **peso**).
- **Máximo 2 ejercicios/día se revirtió:** fue un error; no hay tope.
- **Lista desplegable + “Otro…”:** no tipear siempre el mismo movimiento.
- **Cardio con minutos:** caminata/bici/etc. no van en kg/series.
- **Promedios:** solo días **con dato** (si hay 2 pesos, se divide entre 2).
- **Fechas:** `dd-mm-aa` en la UI del alumno.

### Dashboard semanal / quincenal / mensual

- **Por qué:** Gary y el alumno miran cumplimiento a 7 / 15 / 30 días, no solo el día suelto. Botón **Volver a los registros**.

### Guía del plan (tabla kcal / macros / peso)

- **Por qué:** el alumno tiene que ver **la meta**, no solo lo que anotó. Si existe un plan generado con el mismo email, se intenta cargar; si no, se puede guardar a mano.

---

## Cumplimiento (diseño a implementar / en curso)

**Cumplir = qué tan al 100% sigue su plan**, no si “le dio por registrar”.

| Cola en admin | Significado |
|-----------------|-------------|
| **Sin registro** | No rellenó el planner (abandono de carga) |
| **Registra y falla** | Hay datos, pero lejos de kcal/macros/entreno |

**Semáforo en el planner del alumno:** verde (~100%) → rojo (~0%). Los días vacíos **no** se cuentan como “falló el plan”; son “sin registro”.

**Recordatorios a los 2 días:** pensados **solo para sin registro**. **Pausados** hasta host + correo real.

---

## Videos

- **Una sola página** gated (misma puerta que `/alumno`).
- Videos **incrustados de YouTube** (alojados ahí, no en el servidor).
- **Por qué una página:** no 40 rutas. Las URLs se editan en un JSON.

---

## Catálogo de ejercicios

Hay **dos listas** históricas:

- `plan.py` `GYM` / `HOME` — lo que arma el PDF de 12 semanas.
- `pupils.py` fuerza/cardio — lo que sale en el planner.

**Por qué unificar:** si no, el PDF, el planner y la página de videos no coinciden. La lista canónica es la del PDF + cardio.

---

## Lo que no se hace (y por qué)

| No | Por qué |
|----|---------|
| Shopify como vitrina | Fricción de diseño; la web propia es la marca |
| Mezclar compradores de $40 como alumnos 3 meses | Productos distintos |
| Login de producción y cron ahora | Esperan host propio; ahora es diseño |
| App móvil | Con ≤100 alumnos basta la web |
| Mostrar el código 50% en pantalla | El lead no dejaría el mail |

---

## Orden de trabajo vigente

**Ahora (diseño):** semáforo + admin en dos colas; página de videos; unificar ejercicios; promo guía→curso; flags de host / login abierto.

**En el host propio:** login real, disco persistente, recordatorios 2 días, alta al pagar 3 meses.
