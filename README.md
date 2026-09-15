# PlanFit

Entrega de un plan de alimentación y entrenamiento de **un solo uso**.
El cobro objetivo es **Shopify** (Mercado Pago en el checkout, CLP). El backend emite el enlace tras el webhook `orders/paid`. Stripe / MP directo en Netlify quedan como legado. El PDF nunca se muestra en la web.

Historial de decisiones: **[docs/HISTORIAL.md](docs/HISTORIAL.md)**.  
Host propio (más adelante): **[docs/HOST.md](docs/HOST.md)**.  
Shopify (legado): **[docs/SHOPIFY.md](docs/SHOPIFY.md)**.

## Flujo (Shopify)

1. El cliente paga el producto en Shopify.
2. Shopify llama `POST /webhooks/shopify` → se emite acceso con `payment_ref = shopify_{order_id}` y se envía el correo.
3. El usuario abre `/usar/TOKEN` y envía el formulario **una vez**.
4. El servidor genera el PDF y lo manda en un **segundo correo**.
5. La web **no** muestra calorías, menús ni PDF.
6. El mismo `payment_ref` no puede generar otro plan.
7. Respaldo manual: `/admin` con email + `shopify_{order_id}`. Reenvío PDF: `/internal/resend-pdf`.

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
| POST | `/webhooks/shopify` | Pedido pagado (HMAC). Emite acceso + mail. |

El `index.html` de la raíz es el prototipo viejo y **no** es la entrada pública.

## Landing GaryFelicienFit

La portada en `/` es la tienda: guía **USD $40**, pestañas El coach / Videos / Coaching.
Tras el pago, el backend emite el enlace de un solo uso y envía el correo.

- Local: `ALLOW_TEST_CHECKOUT=1` simula el pago y dispara el envío.
- Mercado Pago (Chile, CLP): `MP_ACCESS_TOKEN` + `PRICE_CLP` (default 38000).
  El cobro lo hace la landing. Por ahora el enlace se emite **a mano** en `/admin`
  (email del pagador + `payment_ref` = `mp_` + id del pago en Mercado Pago).
  Webhook: `https://TU-SITIO.netlify.app/webhooks/mercadopago` (evento Payments).
  `PLANFIT_API_URL` es opcional: si un día el Python está en https, el webhook
  puede emitir el acceso solo.
  - Build command: `echo landing-static` (o vacío)
  - Publish directory: `web`
- Python (tu PC): `python src/server.py` → formulario, PDF, admin, SQLite.

Fotos de la landing en `web/img/` (retrato de Gary: `web/img/gary.jpg`). Videos: `web/videos.json`.

## Base de datos (gratis)

Por defecto usa **SQLite** en `data/planfit.db`: sin cuenta, sin cuota, incluye pagos, tokens, mails y coaching. Es la base importante.

El correo lo envía **Resend** (plan gratis) o SMTP. Si no hay ninguno, queda en `data/outbox/` y se registra en la tabla `mail_log`.

Supabase es **opcional** (también tiene plan gratis). Si más adelante quieres la DB en la nube, pones `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`. Sin esas claves, no se usa.

## Pruebas

Datos de ingreso, `payment_ref` de pruebas y cómo correr la batería: ver `PRUEBAS.md`.

```
python -m unittest discover -s tests -v
```
