# Shopify + PlanFit

## Tienda (en progreso)

| Campo | Valor |
| --- | --- |
| Shop | `garyfelicien.myshopify.com` |
| Admin | https://admin.shopify.com/store/garyfelicien |
| Product ID | `10255880847600` |
| Producto | Plan personalizado de 12 semanas |
| `SHOPIFY_PRODUCT_ID` | `10255880847600` |
| Backend público | `https://garyfelicienfit-production.up.railway.app` |
| Webhook | `https://garyfelicienfit-production.up.railway.app/webhooks/shopify` |

Flujo objetivo: el cliente paga en **Shopify** (Mercado Pago en el checkout). Shopify avisa a este backend. Aquí se emite el enlace de un solo uso y se manda el correo. El PDF completo se genera cuando el usuario completa `/usar/TOKEN`.

```
Shopify checkout → orders/paid webhook → POST /webhooks/shopify
  → payment_ref = shopify_{order_id}
  → mail con /usar/TOKEN
  → formulario → PDF → segundo mail
```

## Fase 0 — Checklist (tú en las consolas)

1. [ ] Crear tienda Shopify (trial o plan Basic).
2. [ ] Crear producto borrador: **Plan personalizado de 12 semanas** (precio CLP).
3. [ ] Instalar pasarela **Mercado Pago** para Shopify (Chile) y hacer un pago de prueba.
4. [ ] Desplegar este backend en **Railway** (u otro host 24/7 con HTTPS).
5. [ ] Variables en el host (mínimo):

| Variable | Valor |
| --- | --- |
| `ADMIN_SECRET` | un secreto largo (el de tu `.env` local o uno nuevo) |
| `APP_URL` | la URL pública HTTPS que dé Railway (sin `/` final) |
| `HOST` | `0.0.0.0` |
| `ALLOW_TEST_CHECKOUT` | `0` en producción |
| `SHOPIFY_PRODUCT_ID` | `10255880847600` |
| `SHOPIFY_WEBHOOK_SECRET` | el de Shopify (cuando creemos el webhook) |
| `RESEND_API_KEY` / SMTP | para correo real (si no, los mails van a log/outbox) |

6. [ ] Volumen persistente o Supabase si no quieres perder la DB al redeploy.

## Fase 1 — Producto

1. Publicar el producto con copy: plan a medida, un solo uso, llega por correo (no se muestra en la web).
2. En la confirmación de pedido / página de gracias: *“En unos minutos te llega el correo con el enlace para armar tu plan. El enlace es de un solo uso.”*
3. Anotar el **product_id** (y variant_id si quieres filtrar) → `SHOPIFY_PRODUCT_ID`.

## Fase 2 — Webhook (ya soportado en código)

En Shopify Admin → Settings → Notifications → Webhooks (o Apps / event subscriptions según el plan):

| Campo | Valor |
| --- | --- |
| Event | **Order payment** / `orders/paid` |
| Format | JSON |
| URL | `https://TU-BACKEND/webhooks/shopify` |

Copia el **signing secret** → `SHOPIFY_WEBHOOK_SECRET` en el `.env` del backend.

Comportamiento del endpoint:

- Verifica `X-Shopify-Hmac-Sha256`.
- Solo actúa si `financial_status` es `paid` (o vacío en payloads del evento paid).
- `payment_ref` = `shopify_{id}` (idempotente ante reintentos).
- Si defines `SHOPIFY_PRODUCT_ID` / `SHOPIFY_VARIANT_ID`, ignora pedidos de otros productos.

Prueba local del HMAC (con el server arriba y `ALLOW_TEST_CHECKOUT=1` si aún no hay secret):

```bash
python -m unittest tests.test_shopify -v
```

Emisión manual de respaldo en `/admin`:

| Campo | Valor |
| --- | --- |
| Email | email del pedido Shopify |
| payment_ref | `shopify_` + id numérico del pedido |

## Fase 3 — Apagar Netlify como caja

Cuando el E2E Shopify → mail → form → PDF funcione:

- CTA de la landing vieja → URL del producto Shopify.
- Redirect Netlify → tienda.
- Dejar de usar checkout Netlify / `mp-webhook` de Netlify como camino principal.

## Lead magnet H (después)

Calculadora → email con resumen IMC/TMB/GET + mini PDF de 1 día. No forma parte de esta integración de cobro.
