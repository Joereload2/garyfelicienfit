# Supabase — GaryFelicienFit

Aquí vive lo importante: quién pagó, el email, el `payment_ref`, el token de un solo uso, los leads de coaching y una copia del PDF.

## Tablas

| Tabla | Qué guarda |
| --- | --- |
| `entitlements` | Acceso de un solo uso (email + payment_ref + token + PDF) |
| `payments` | Evento de pago (Stripe / MercadoPago / prueba) |
| `mail_log` | Cada correo de enlace o PDF, enviado o fallido |
| `coaching_leads` | Pedidos de coaching personalizado |
| Storage `pdfs` | El archivo PDF, para reenviar el mismo |

## Correo

Supabase **no** manda el mail. Opciones:

- `RESEND_API_KEY` (recomendado con Netlify)
- `SMTP_HOST` (Gmail, etc.)
- Si ambos están vacíos: se guarda en `data/outbox/` y queda copia en `mail_log`

## Encendido

1. Run `schema.sql` en el SQL Editor.
2. Pega URL + **service_role** en `.env`.
3. Reinicia `python src/server.py`.

Sin esas variables el sitio sigue con JSON local; no se rompe.