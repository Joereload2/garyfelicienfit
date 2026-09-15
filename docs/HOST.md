# Levantar GaryFelicienFit en un VPS (cuando dejen Railway)

El código no depende de Railway. En el servidor:

1. Python 3.12+, `pip install -r requirements.txt`
2. Copiar `.env.example` → `.env` y completar:
   - `APP_URL=https://tu-dominio`
   - `HOST=0.0.0.0`
   - `PORT` el que use el reverse proxy
   - `ADMIN_SECRET`
   - `RESEND_API_KEY` y `SMTP_FROM` (mails reales)
   - `ALUMNO_OPEN_LOGIN=0` en producción (PIN único por alumno)
   - `COURSE_PRICE_CLP` y `GUIDE_PRICE_CLP` (promo guía → curso)
3. Disco persistente en `data/` (SQLite). Sin esto se pierden alumnos al reiniciar.
4. Reverse proxy (nginx/caddy) → el `PORT`.
5. `python src/server.py` (systemd o similar).

Login abierto (`ALUMNO_OPEN_LOGIN=1`, PIN `12345`) es solo para diseñar. Los recordatorios a 2 días se activan cuando el correo funcione en este host.
