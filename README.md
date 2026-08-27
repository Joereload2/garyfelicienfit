# PlanFit

Entrega de un plan de alimentación y entrenamiento de **un solo uso**.
El pago se verifica en otra plataforma. Aquí no hay Stripe ni cobros.

## Flujo

1. Verificas el pago fuera.
2. En `/admin` emites un enlace atado a email + `payment_ref`.
3. El usuario abre `/usar/TOKEN` y envía el formulario **una vez**.
4. El servidor genera el PDF y lo manda en un **segundo correo**.
5. La web **no** muestra calorías, menús ni PDF.
6. El mismo `payment_ref` no puede generar otro plan.
7. Si se equivocó, el enlace no se reabre; corrección solo por soporte (`/internal/resend-pdf` reenvía el mismo PDF).

## Arranque

```
python -m pip install reportlab
python src/server.py
```

- App: http://localhost:3000
- Admin: http://localhost:3000/admin
- `ADMIN_SECRET` está en `.env` (no en el código).

Si `SMTP_HOST` está vacío, los correos se guardan en `data/outbox/` y los PDF en `data/pdfs/`.

## Endpoints

| Método | Ruta | Notas |
| --- | --- | --- |
| GET | `/` | Portada. El plan no se ofrece aquí. |
| GET | `/admin` | Panel interno. |
| GET | `/usar/:token` | Wizard. El token no se gasta al abrir. |
| GET | `/api/access/:token` | Email bloqueado + estado. |
| POST | `/api/submit/:token` | Gasta el token si el POST es válido. 409 si ya se usó. |
| POST | `/internal/entitlements` | Header `X-Admin-Secret`. |
| GET | `/internal/entitlements` | Lista. Mismo header. |
| POST | `/internal/resend-pdf` | Reenvía el mismo PDF. No regenera. |

El `index.html` de la raíz es el prototipo viejo y **no** es la entrada pública.

## Landing GaryFelicienFit

La portada en `/` es la tienda: guía **USD $40**, pestañas El coach / Videos / Coaching.
Tras el pago, el backend emite el enlace de un solo uso y envía el correo.

- Local: `ALLOW_TEST_CHECKOUT=1` simula el pago y dispara el envío.
- Producción: `STRIPE_SECRET_KEY` + webhook `/webhooks/stripe`.
- Netlify: publica `public/` (ver `netlify.toml`). El generador de PDF sigue en Python; configura `PLANFIT_API_URL` y `ADMIN_SECRET` en Netlify.

Fotos de prueba en `public/img/` (el retrato de Gary está en `public/img/gary.jpg`). Videos en `public/videos.json`.

## Supabase (base de datos)

Los pagos, emails, leads de coaching y PDFs no deberían vivir solo en el disco local.

1. Crea un proyecto en [supabase.com](https://supabase.com).
2. SQL Editor → pega y corre `supabase/schema.sql`.
3. Settings → API: copia **Project URL** y **service_role** (nunca la anon key en el servidor de mails).
4. En `.env`:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
RESEND_API_KEY=re_...   # opcional, para mandar el correo de verdad
```

Con eso: entitlements, coaching, log de mails y el PDF van a Supabase. Sin esas claves, sigue el JSON local (`data/store.json`) para desarrollo.

El correo en sí lo envía **Resend** o **SMTP**. Supabase guarda quién pagó, el token y si el mail salió.

## Pruebas

Datos de ingreso, `payment_ref` de pruebas y cómo correr la batería: ver `PRUEBAS.md`.

```
python -m unittest discover -s tests -v
```
