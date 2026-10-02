"""GaryFelicienFit / PlanFit HTTP server. Landing + one-shot delivery."""

from __future__ import annotations

import hmac
import json
import os
import re
import secrets
import sys
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from envload import get, load_env, require  # noqa: E402

load_env()

from mailer import send_discount_code, send_guia_upgrade, send_plan_pdf  # noqa: E402
from payments import (  # noqa: E402
    course_list_clp,
    course_sale_clp,
    create_mp_preference,
    create_mp_preference_3meses,
    create_stripe_checkout,
    email_from_stripe_session,
    fetch_mp_payment,
    fulfill_course_payment,
    fulfill_mp_payment,
    fulfill_shopify_order,
    issue_paid_access,
    mp_configured,
    offer_minutes,
    price_clp,
    price_usd,
    stripe_configured,
    test_checkout_allowed,
    unique_ref,
    verify_shopify_webhook,
    verify_stripe_signature,
)
from pdf_builder import build_pdf  # noqa: E402
from plan import build_plan  # noqa: E402
import store  # noqa: E402
from store import (  # noqa: E402
    consume_pending,
    ensure_dirs,
    get_by_payment_ref,
    get_by_token,
    list_all,
    save_coaching,
)
from validate import ValidationError, normalize_email, normalize_payment_ref, validate_payload  # noqa: E402
import pupils  # noqa: E402
import sqlite_db  # noqa: E402

PUBLIC = ROOT / "public"
WEB = ROOT / "web"
LANDING = {
    "index.html",
    "gracias.html",
    "bajar.html",
    "recomposicion.html",
    "empezar.html",
    "3meses.html",
    "ejercicios.html",
    "ejercicios-mapa.js",
    "herramientas.html",
    "registro.js",
    "site.css",
    "site.js",
    "quiz.js",
    "nav.js",
    "videos.json",
}
MAX_BODY = 200_000
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".ico": "image/x-icon",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".json": "application/json; charset=utf-8",
}


def _app_url() -> str:
    url = get("APP_URL") or ""
    if (not url) or ("localhost" in url):
        domain = get("RAILWAY_PUBLIC_DOMAIN")
        if domain:
            url = f"https://{domain}"
    return (url or "http://localhost:3000").rstrip("/")


def _admin_secret() -> str:
    return require("ADMIN_SECRET")


def _parse_iso(ts: object) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def offer_remaining_s(row: dict | None) -> int:
    if not row or row.get("used"):
        return 0
    expires = _parse_iso(row.get("expires_at"))
    if not expires:
        return 0
    return max(0, int((expires - datetime.now(timezone.utc)).total_seconds()))


def offer_public(row: dict | None, *, message: str = "") -> dict:
    remaining = offer_remaining_s(row)
    live = remaining > 0
    payload = {
        "ok": True,
        "token": (row or {}).get("token") or "",
        "expires_at": (row or {}).get("expires_at"),
        "remaining_s": remaining,
        "live": live,
        "price_clp": course_sale_clp() if live else course_list_clp(),
        "list_clp": course_list_clp(),
        "sale_clp": course_sale_clp(),
        "mp": mp_configured(),
    }
    if message:
        payload["message"] = message
    return payload


def _whatsapp_offer_url() -> str:
    text = "Hola Gary, pedí el 50% del acompañamiento de 3 meses."
    return "https://wa.me/56959128603?text=" + quote(text)


def _safe_ref(payment_ref: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", payment_ref)[:80]


class Handler(BaseHTTPRequestHandler):
    server_version = "PlanFit/1.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))

    def _cors(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        if content_type.startswith("text/html"):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data: https://i.ytimg.com; "
                "font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; "
                "frame-src https://www.youtube.com https://www.youtube-nocookie.com; "
                "connect-src 'self'",
            )
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def _redirect(self, location: str, code: int = 301) -> None:
        self.send_response(code)
        self.send_header("Location", location)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _file_from(self, folder: Path, rel: str, code: int = 200) -> None:
        root = folder.resolve()
        path = (folder / rel).resolve()
        if root not in path.parents and path != root:
            self._json(404, {"ok": False, "error": "No encontrado"})
            return
        if not path.is_file():
            self._json(404, {"ok": False, "error": "No encontrado"})
            return
        self._send(code, path.read_bytes(), MIME.get(path.suffix, "application/octet-stream"))

    def _html_file(self, name: str, code: int = 200) -> None:
        folder = WEB if name in LANDING else PUBLIC
        self._file_from(folder, name, code)

    def _static(self, rel: str) -> None:
        if rel in LANDING or rel.startswith("img/"):
            self._file_from(WEB, rel)
            return
        self._file_from(PUBLIC, rel)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0 or length > MAX_BODY:
            raise ValidationError("Cuerpo inválido.")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("JSON inválido.") from exc
        if not isinstance(data, dict):
            raise ValidationError("JSON inválido.")
        return data

    def _admin_ok(self) -> bool:
        expected = _admin_secret().encode("utf-8")
        got = (self.headers.get("X-Admin-Secret") or "").encode("utf-8")
        if not got:
            auth = self.headers.get("Authorization") or ""
            if auth.lower().startswith("bearer "):
                got = auth[7:].strip().encode("utf-8")
        if len(got) != len(expected):
            return False
        return hmac.compare_digest(got, expected)

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path == "/":
            self._html_file("index.html")
            return
        if path in (
            "/bajar",
            "/bajar.html",
            "/recomposicion",
            "/recomposicion.html",
            "/empezar",
            "/empezar.html",
            "/tu-plan",
            "/vitalidad",
            "/vitalidad.html",
        ):
            self._redirect("/3meses")
            return
        if path in ("/3meses", "/3meses.html", "/acompanamiento"):
            self._html_file("3meses.html")
            return
        if path in ("/herramientas", "/herramientas.html"):
            self._html_file("herramientas.html")
            return
        if path == "/admin":
            self._html_file("admin.html")
            return
        if path in ("/ingreso", "/ingreso.html"):
            self._html_file("ingreso.html")
            return
        if path in ("/ingreso/panel", "/panel"):
            self._html_file("panel.html")
            return
        if path in ("/alumno", "/alumno.html"):
            self._html_file("alumno.html")
            return
        if path in ("/ejercicios", "/ejercicios.html"):
            self._html_file("ejercicios.html")
            return
        if path == "/alumno/ejercicios":
            self._file_from(PUBLIC, "ejercicios.html")
            return
        if path == "/gracias":
            self._html_file("gracias.html")
            return
        if path == "/webhooks/mercadopago":
            self._mp_webhook()
            return
        if path in (
            "/styles.css",
            "/form.js",
            "/site.css",
            "/site.js",
            "/quiz.js",
            "/nav.js",
            "/videos.json",
            "/registro.js",
            "/ejercicios-mapa.js",
            "/alumno.js",
            "/alumno.css",
            "/ejercicios.js",
            "/ejercicios-videos.json",
            "/ingreso.js",
            "/panel.js",
        ):
            self._static(path.lstrip("/"))
            return
        if re.fullmatch(r"/img/[A-Za-z0-9._-]+\.(jpg|jpeg|png|webp|svg)", path):
            self._static(path.lstrip("/"))
            return
        if path == "/api/product":
            self._json(
                200,
                {
                    "ok": True,
                    "price_usd": price_usd(),
                    "price_clp": price_clp(),
                    "course_clp": course_list_clp(),
                    "sale_clp": course_sale_clp(),
                    "stripe": stripe_configured(),
                    "mp": mp_configured(),
                    "test_checkout": test_checkout_allowed(),
                },
            )
            return
        if path == "/api/oferta-estado":
            self._oferta_estado()
            return
        match = re.fullmatch(r"/usar/([A-Za-z0-9_-]+)", path)
        if match:
            self._html_file("form.html")
            return
        match = re.fullmatch(r"/api/access/([A-Za-z0-9_-]+)", path)
        if match:
            self._api_access(match.group(1))
            return
        if path == "/api/alumno/state":
            self._alumno_state()
            return
        if path == "/internal/pupils":
            self._list_pupils()
            return
        if path == "/internal/alumno-roster":
            self._alumno_roster()
            return
        if path == "/api/admin/roster":
            self._admin_roster()
            return
        if path == "/api/admin/alumno":
            self._admin_alumno()
            return
        if path == "/internal/entitlements":
            if not self._admin_ok():
                self._json(401, {"ok": False, "error": "No autorizado"})
                return
            items = []
            for ent in list_all():
                items.append(
                    {
                        "email": ent["email"],
                        "payment_ref": ent["payment_ref"],
                        "status": ent["status"],
                        "url": ent.get("url") or f"{_app_url()}/usar/{ent['token']}",
                        "created_at": ent.get("created_at"),
                        "used_at": ent.get("used_at"),
                        "has_pdf": bool(ent.get("pdf_path")),
                    }
                )
            self._json(200, {"ok": True, "items": items})
            return
        self._json(404, {"ok": False, "error": "No encontrado"})

    def do_POST(self) -> None:
        path = unquote(urlparse(self.path).path)
        try:
            if re.fullmatch(r"/api/submit/([A-Za-z0-9_-]+)", path):
                token = path.rsplit("/", 1)[-1]
                self._submit(token)
                return
            if path == "/internal/entitlements":
                self._create_entitlement()
                return
            if path == "/internal/pupils":
                self._create_pupil()
                return
            if path == "/api/alumno/login":
                self._alumno_login()
                return
            if path == "/api/ingreso":
                self._ingreso()
                return
            if path == "/api/alumno/day":
                self._alumno_day()
                return
            if path == "/api/alumno/metric":
                self._alumno_metric()
                return
            if path == "/api/alumno/metric-toggle":
                self._alumno_metric_toggle()
                return
            if path == "/api/alumno/lift":
                self._alumno_lift()
                return
            if path == "/api/alumno/lift-delete":
                self._alumno_lift_delete()
                return
            if path == "/api/alumno/guide":
                self._alumno_guide()
                return
            if path == "/internal/resend-pdf":
                self._resend_pdf()
                return
            if path == "/api/checkout":
                self._checkout()
                return
            if path == "/api/coaching":
                self._coaching()
                return
            if path == "/api/oferta-3meses":
                self._oferta_3meses()
                return
            if path == "/api/checkout-3meses":
                self._checkout_3meses()
                return
            if path == "/internal/course-paid":
                self._course_paid()
                return
            if path == "/api/registro":
                self._registro()
                return
            if path == "/webhooks/stripe":
                self._stripe_webhook()
                return
            if path == "/webhooks/mercadopago":
                self._mp_webhook()
                return
            if path == "/webhooks/shopify":
                self._shopify_webhook()
                return
        except ValidationError as exc:
            self._json(400, {"ok": False, "error": exc.message, "field": exc.field})
            return
        self._json(404, {"ok": False, "error": "No encontrado"})

    def _api_access(self, token: str) -> None:
        if not TOKEN_RE.match(token):
            self._json(404, {"ok": False, "status": "missing", "error": "Enlace no válido."})
            return
        ent = get_by_token(token)
        if not ent:
            self._json(404, {"ok": False, "status": "missing", "error": "Enlace no válido."})
            return
        if ent.get("status") != "pending":
            self._json(
                409,
                {
                    "ok": False,
                    "status": "used",
                    "error": "Este acceso ya fue utilizado. Si hay un error, contacta a soporte.",
                },
            )
            return
        self._json(200, {"ok": True, "status": "pending", "email": ent["email"]})

    def _create_entitlement(self) -> None:
        if not self._admin_ok():
            self._json(401, {"ok": False, "error": "No autorizado"})
            return
        data = self._read_json()
        email = normalize_email(data.get("email"))
        payment_ref = normalize_payment_ref(data.get("payment_ref"))
        try:
            issued = issue_paid_access(email, payment_ref)
        except ValueError as exc:
            if str(exc) == "payment_ref_used":
                self._json(409, {"ok": False, "error": "Ese payment_ref ya tiene un acceso."})
                return
            raise
        self._json(201, {"ok": True, **issued})

    def _pupil_session(self) -> dict:
        auth = self.headers.get("Authorization") or ""
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        return pupils.pupil_from_session(token)

    def _create_pupil(self) -> None:
        if not self._admin_ok():
            self._json(401, {"ok": False, "error": "No autorizado"})
            return
        data = self._read_json()
        created = pupils.create_pupil(str(data.get("email") or ""), str(data.get("name") or ""))
        created["login_url"] = f"{_app_url()}/alumno"
        self._json(201, {"ok": True, **created})

    def _admin_session(self) -> dict:
        auth = self.headers.get("Authorization") or ""
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        sess = sqlite_db.get_session(token)
        if not sess or sess.get("role") != "admin":
            raise ValidationError("Sesión no válida. Entra de nuevo.")
        return sess

    def _ingreso(self) -> None:
        data = self._read_json()
        out = pupils.ingreso(str(data.get("email") or ""), str(data.get("pin") or ""))
        self._json(200, {"ok": True, **out})

    def _admin_roster(self) -> None:
        try:
            self._admin_session()
        except ValidationError as exc:
            self._json(401, {"ok": False, "error": exc.message})
            return
        self._json(200, {"ok": True, **pupils.roster(14)})

    def _admin_alumno(self) -> None:
        try:
            self._admin_session()
        except ValidationError as exc:
            self._json(401, {"ok": False, "error": exc.message})
            return
        qs = parse_qs(urlparse(self.path).query)
        try:
            pid = int((qs.get("id") or ["0"])[0])
        except ValueError:
            self._json(400, {"ok": False, "error": "Alumno inválido"})
            return
        full = sqlite_db.get_pupil_by_id(pid)
        if not full:
            self._json(404, {"ok": False, "error": "No existe ese alumno"})
            return
        today = datetime.now(timezone.utc).date()
        end = today.isoformat()
        start = today.fromordinal(today.toordinal() - 13).isoformat()
        self._json(200, {"ok": True, **pupils.state(full, start, end)})

    def _alumno_roster(self) -> None:
        if not self._admin_ok():
            self._json(401, {"ok": False, "error": "No autorizado"})
            return
        self._json(200, {"ok": True, **pupils.roster(14)})

    def _list_pupils(self) -> None:
        if not self._admin_ok():
            self._json(401, {"ok": False, "error": "No autorizado"})
            return
        try:
            self._json(200, {"ok": True, "items": pupils.list_pupils()})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)[:200]})

    def _alumno_login(self) -> None:
        data = self._read_json()
        out = pupils.login(str(data.get("email") or ""), str(data.get("pin") or ""))
        self._json(200, {"ok": True, **out})

    def _alumno_state(self) -> None:
        try:
            pupil = self._pupil_session()
            qs = parse_qs(urlparse(self.path).query)
            start = (qs.get("start") or [""])[0]
            end = (qs.get("end") or [""])[0]
            if not start or not end:
                today = datetime.now(timezone.utc).date()
                end = today.isoformat()
                start = today.fromordinal(today.toordinal() - 6).isoformat()
            self._json(200, {"ok": True, **pupils.state(pupil, start, end)})
        except ValidationError as exc:
            code = 401 if "Sesión" in exc.message else 400
            self._json(code, {"ok": False, "error": exc.message})

    def _alumno_day(self) -> None:
        pupil = self._pupil_session()
        data = self._read_json()
        pupils.save_day(pupil, str(data.get("day") or ""), data.get("values") or {})
        self._json(200, {"ok": True})

    def _alumno_metric(self) -> None:
        pupil = self._pupil_session()
        data = self._read_json()
        metric = pupils.add_metric(
            pupil,
            str(data.get("label") or ""),
            str(data.get("kind") or "number"),
            str(data.get("unit") or ""),
        )
        self._json(201, {"ok": True, "metric": metric})

    def _alumno_metric_toggle(self) -> None:
        pupil = self._pupil_session()
        data = self._read_json()
        pupils.toggle_metric(pupil, str(data.get("key") or ""), bool(data.get("enabled")))
        self._json(200, {"ok": True})

    def _alumno_lift(self) -> None:
        pupil = self._pupil_session()
        lift = pupils.add_lift(pupil, self._read_json())
        self._json(201, {"ok": True, "lift": lift})

    def _alumno_lift_delete(self) -> None:
        pupil = self._pupil_session()
        data = self._read_json()
        pupils.remove_lift(pupil, int(data.get("id") or 0))
        self._json(200, {"ok": True})

    def _alumno_guide(self) -> None:
        pupil = self._pupil_session()
        guide = pupils.save_guide(pupil, self._read_json())
        self._json(200, {"ok": True, "guide": guide})

    def _checkout(self) -> None:
        data = self._read_json()
        email = normalize_email(data.get("email"))
        modelo = str(data.get("modelo") or "").strip().lower()
        if modelo in {"vitalidad", "vitality", "recomp"}:
            modelo = "recomposicion"
        if modelo not in {"bajar", "recomposicion"}:
            modelo = "bajar"
        success = f"{_app_url()}/gracias?paid=1&modelo={modelo}"
        cancel = f"{_app_url()}/{modelo}"
        if mp_configured():
            notify = f"{_app_url()}/webhooks/mercadopago"
            try:
                url = create_mp_preference(email, success, cancel, notify, modelo=modelo)
            except Exception as exc:
                self._json(502, {"ok": False, "error": str(exc)})
                return
            self._json(200, {"ok": True, "mode": "mp", "url": url})
            return
        if stripe_configured():
            try:
                url = create_stripe_checkout(email, success, cancel)
            except Exception as exc:
                self._json(502, {"ok": False, "error": str(exc)})
                return
            self._json(200, {"ok": True, "mode": "stripe", "url": url})
            return
        if not test_checkout_allowed():
            self._json(
                503,
                {
                    "ok": False,
                    "error": "La pasarela de pago aún no está activa. Escríbenos por WhatsApp.",
                },
            )
            return
        ref = unique_ref("gff")
        try:
            issued = issue_paid_access(email, ref)
        except ValueError:
            self._json(409, {"ok": False, "error": "No se pudo emitir el acceso."})
            return
        self._json(
            200,
            {
                "ok": True,
                "mode": "test",
                "message": "Pago de prueba registrado. Revisa el correo (o data/outbox/).",
                **issued,
            },
        )

    def _stripe_webhook(self) -> None:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0 or length > 400_000:
            self._json(400, {"ok": False, "error": "Cuerpo inválido"})
            return
        raw = self.rfile.read(length)
        secret = get("STRIPE_WEBHOOK_SECRET")
        sig = self.headers.get("Stripe-Signature") or ""
        if secret and not verify_stripe_signature(raw, sig, secret):
            self._json(400, {"ok": False, "error": "Firma Stripe inválida"})
            return
        try:
            event = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "JSON inválido"})
            return
        etype = event.get("type")
        if etype != "checkout.session.completed":
            self._json(200, {"ok": True, "ignored": etype})
            return
        session = event.get("data", {}).get("object") or {}
        try:
            email = email_from_stripe_session(session)
        except ValidationError as exc:
            self._json(400, {"ok": False, "error": exc.message})
            return
        payment_ref = normalize_payment_ref(session.get("id") or unique_ref("stripe"))
        if get_by_payment_ref(payment_ref):
            self._json(200, {"ok": True, "duplicate": True})
            return
        try:
            issued = issue_paid_access(email, payment_ref)
        except ValueError:
            self._json(200, {"ok": True, "duplicate": True})
            return
        self._json(200, {"ok": True, **issued})

    def _mp_webhook(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        payment_id = ""
        if qs.get("data.id"):
            payment_id = qs["data.id"][0]
        elif qs.get("id") and (qs.get("topic") or [""])[0] == "payment":
            payment_id = qs["id"][0]
        elif qs.get("id") and (qs.get("type") or [""])[0] == "payment":
            payment_id = qs["id"][0]
        if self.command == "POST":
            length = int(self.headers.get("Content-Length") or "0")
            if 0 < length <= 400_000:
                raw = self.rfile.read(length)
                try:
                    body = json.loads(raw.decode("utf-8") or "{}")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    body = {}
                if isinstance(body, dict):
                    data = body.get("data") or {}
                    topic = str(body.get("type") or body.get("topic") or "")
                    if topic in {"", "payment"}:
                        payment_id = str(data.get("id") or body.get("id") or payment_id)
        if not payment_id:
            self._json(200, {"ok": True, "ignored": "no-id"})
            return
        if not mp_configured():
            self._json(503, {"ok": False, "error": "Mercado Pago no está configurado"})
            return
        try:
            payment = fetch_mp_payment(str(payment_id))
            result = fulfill_mp_payment(payment)
        except ValidationError as exc:
            self._json(400, {"ok": False, "error": exc.message})
            return
        except Exception as exc:
            self._json(502, {"ok": False, "error": str(exc)[:300]})
            return
        self._json(200, result)

    def _shopify_webhook(self) -> None:
        length = int(self.headers.get("Content-Length") or "0")
        if length < 0 or length > 400_000:
            print("shopify webhook: cuerpo inválido length=", length)
            self._json(400, {"ok": False, "error": "Cuerpo inválido"})
            return
        if length == 0:
            raw = self.rfile.read(400_000)
        else:
            raw = self.rfile.read(length)
        if not raw:
            print("shopify webhook: cuerpo vacío")
            self._json(400, {"ok": False, "error": "Cuerpo inválido"})
            return
        secret = get("SHOPIFY_WEBHOOK_SECRET")
        sig = (
            self.headers.get("X-Shopify-Hmac-Sha256")
            or self.headers.get("X-Shopify-Hmac-SHA256")
            or ""
        )
        topic = self.headers.get("X-Shopify-Topic") or ""
        # Require secret in production paths: if set, signature must match.
        if secret:
            if not verify_shopify_webhook(raw, sig, secret):
                print("shopify webhook: firma inválida topic=", topic)
                self._json(401, {"ok": False, "error": "Firma Shopify inválida"})
                return
        elif not test_checkout_allowed():
            self._json(503, {"ok": False, "error": "Falta SHOPIFY_WEBHOOK_SECRET"})
            return
        try:
            order = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            print("shopify webhook: JSON inválido topic=", topic)
            self._json(400, {"ok": False, "error": "JSON inválido"})
            return
        if not isinstance(order, dict):
            print("shopify webhook: pedido no es objeto topic=", topic)
            self._json(400, {"ok": False, "error": "Pedido inválido"})
            return
        try:
            result = fulfill_shopify_order(order)
        except ValidationError as exc:
            print(
                "shopify webhook 400:",
                exc.message,
                "topic=",
                topic,
                "keys=",
                list(order.keys())[:12],
            )
            self._json(400, {"ok": False, "error": exc.message})
            return
        except Exception as exc:
            print("shopify webhook 502:", str(exc)[:300])
            self._json(502, {"ok": False, "error": str(exc)[:300]})
            return
        print("shopify webhook ok:", result)
        self._json(200, result)

    def _oferta_3meses(self) -> None:
        data = self._read_json()
        email = normalize_email(data.get("email"))
        name = str(data.get("name") or "").replace("<", "").replace(">", "").strip()[:80]
        if len(name) < 2:
            name = email.split("@")[0].replace(".", " ").replace("_", " ").strip()[:80] or "Alumno"
        existing = sqlite_db.get_discount_by_email(email)
        if existing and offer_remaining_s(existing) > 0:
            self._json(
                200,
                offer_public(
                    existing,
                    message="Tu 50% sigue activo. Paga antes de que se acabe el tiempo.",
                ),
            )
            return
        now = datetime.now(timezone.utc)
        minutes = offer_minutes()
        expires = now + timedelta(minutes=minutes)
        token = secrets.token_urlsafe(24)
        code = "GARY50-" + secrets.token_hex(3).upper()
        row = sqlite_db.insert_discount(
            email,
            code,
            now.isoformat(),
            token=token,
            expires_at=expires.isoformat(),
        )
        save_coaching(
            {
                "name": name,
                "email": email,
                "phone": "",
                "message": (
                    f"Lead 50% off 3 meses. Código {code}. "
                    f"Lista {course_list_clp()} / con código {course_sale_clp()} CLP. "
                    f"Vence {expires.isoformat()}."
                ),
                "created_at": now.isoformat(),
            }
        )
        try:
            send_discount_code(email, code, minutes=minutes)
        except Exception as exc:
            print("discount mail:", str(exc)[:300])
        self._json(
            200,
            offer_public(
                row,
                message="El 50% está activo por tiempo limitado. El reloj ya corre. Revisa el correo: ahí va el código.",
            ),
        )

    def _oferta_estado(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        token = str((qs.get("token") or [""])[0]).strip()
        row = sqlite_db.get_discount_by_token(token)
        if not row:
            self._json(
                404,
                {
                    "ok": False,
                    "live": False,
                    "remaining_s": 0,
                    "price_clp": course_list_clp(),
                    "list_clp": course_list_clp(),
                    "sale_clp": course_sale_clp(),
                    "error": "Oferta no encontrada.",
                },
            )
            return
        self._json(200, offer_public(row))

    def _checkout_3meses(self) -> None:
        data = self._read_json()
        email = normalize_email(data.get("email"))
        token = str(data.get("token") or "").strip()
        row = sqlite_db.get_discount_by_token(token)
        if not row or str(row.get("email") or "").lower() != email:
            self._json(400, {"ok": False, "error": "Pide el 50% otra vez con este correo."})
            return
        live = offer_remaining_s(row) > 0
        amount = course_sale_clp() if live else course_list_clp()
        if mp_configured():
            success = f"{_app_url()}/gracias?paid=1&producto=3meses"
            cancel = f"{_app_url()}/3meses"
            notify = f"{_app_url()}/webhooks/mercadopago"
            try:
                url = create_mp_preference_3meses(email, amount, token, success, cancel, notify)
            except Exception as exc:
                self._json(502, {"ok": False, "error": str(exc)})
                return
            payload = offer_public(row)
            payload.update({"mode": "mp", "url": url, "price_clp": amount})
            self._json(200, payload)
            return
        payload = offer_public(row)
        payload.update(
            {
                "mode": "whatsapp",
                "url": _whatsapp_offer_url(),
                "price_clp": amount,
                "message": "Mercado Pago aún no está activo. Coordina el pago por WhatsApp.",
            }
        )
        self._json(200, payload)

    def _course_paid(self) -> None:
        if not self._admin_ok():
            self._json(401, {"ok": False, "error": "No autorizado"})
            return
        data = self._read_json()
        email = normalize_email(data.get("email"))
        payment_ref = normalize_payment_ref(data.get("payment_ref"))
        amount = int(data.get("amount") or 0)
        offer_token = str(data.get("offer_token") or "")
        fake = {
            "status": "approved",
            "id": str(data.get("id") or payment_ref.replace("mp_", "")),
            "transaction_amount": amount,
            "payer": {"email": email},
            "metadata": {"email": email, "product": "3meses", "offer_token": offer_token},
            "external_reference": email,
        }
        result = fulfill_course_payment(fake)
        self._json(200, result)

    def _registro(self) -> None:
        data = self._read_json()
        name = str(data.get("name") or "").replace("<", "").replace(">", "").strip()[:80]
        if len(name) < 2:
            raise ValidationError("Introduce tu nombre.", "name")
        email = normalize_email(data.get("email"))
        phone = str(data.get("phone") or "").replace("<", "").replace(">", "").strip()[:40]
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 8 or len(digits) > 15:
            raise ValidationError(
                "Introduce un teléfono válido. Ejemplo Chile: +56 9 1234 5678.",
                "phone",
            )
        ads = data.get("ads_consent")
        ads_ok = ads is True or ads == 1 or str(ads).strip().lower() in {"true", "1", "on", "sí", "si"}
        if not ads_ok:
            raise ValidationError(
                "Para registrarte hay que autorizar el envío de información comercial. La casilla no viene marcada a propósito.",
                "ads_consent",
            )
        source = str(data.get("source") or "herramientas").replace("<", "").replace(">", "").strip()[:40]
        if source not in {"herramientas", "ejercicios"}:
            source = "herramientas"
        store.save_marketing_lead(
            {
                "name": name,
                "email": email,
                "phone": phone,
                "ads_consent": 1,
                "source": source,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._json(
            200,
            {
                "ok": True,
                "message": "Listo. Ya puedes usar las herramientas.",
                "email": email,
            },
        )

    def _coaching(self) -> None:
        data = self._read_json()
        name = str(data.get("name") or "").replace("<", "").replace(">", "").strip()[:80]
        message = str(data.get("message") or "").replace("<", "").replace(">", "").strip()[:2000]
        phone = str(data.get("phone") or "").replace("<", "").replace(">", "").strip()[:40]
        if len(name) < 2:
            raise ValidationError("Introduce tu nombre.", "name")
        if len(message) < 10:
            raise ValidationError("Cuéntanos un poco más de lo que buscas.", "message")
        email = normalize_email(data.get("email"))
        entry = save_coaching(
            {
                "name": name,
                "email": email,
                "phone": phone,
                "message": message,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._json(
            200,
            {
                "ok": True,
                "message": "Recibido. Gary te escribe para coordinar el coaching personalizado.",
                "email": entry["email"],
            },
        )

    def _submit(self, token: str) -> None:
        if not TOKEN_RE.match(token):
            self._json(404, {"ok": False, "error": "Enlace no válido."})
            return
        ent = get_by_token(token)
        if not ent:
            self._json(404, {"ok": False, "error": "Enlace no válido."})
            return
        if ent.get("status") != "pending":
            self._json(
                409,
                {
                    "ok": False,
                    "error": "Este acceso ya fue utilizado. El plan no se vuelve a generar.",
                },
            )
            return
        data = self._read_json()
        cleaned = validate_payload(data, locked_email=ent["email"])
        plan = build_plan(cleaned)
        filename = f"{_safe_ref(ent['payment_ref'])}-{token[:8]}.pdf"
        pdf_path = store.PDF_DIR / filename
        build_pdf(pdf_path, cleaned, plan, ent["payment_ref"])
        try:
            consume_pending(token, str(pdf_path), filename, cleaned)
        except ValueError:
            current = get_by_token(token)
            stored = str((current or {}).get("pdf_path") or "")
            if stored != str(pdf_path) and pdf_path.exists():
                try:
                    pdf_path.unlink()
                except OSError:
                    pass
            self._json(409, {"ok": False, "error": "Este acceso ya fue utilizado."})
            return
        except KeyError:
            self._json(404, {"ok": False, "error": "Enlace no válido."})
            return
        try:
            send_plan_pdf(cleaned["email"], cleaned["name"], pdf_path, ent["payment_ref"])
        except Exception as exc:
            sys.stderr.write(f"mail pdf failed: {exc}\n")
        try:
            course = int(get("COURSE_PRICE_CLP") or "450000")
            guide = int(get("GUIDE_PRICE_CLP") or get("PRICE_CLP") or "38000")
            price = max(0, course - guide)
            email = cleaned["email"]
            existing = sqlite_db.get_discount_by_email(email, "guia-upgrade")
            if existing and existing.get("code"):
                code = existing["code"]
            else:
                code = "GUIA-" + secrets.token_hex(3).upper()
                sqlite_db.insert_discount(
                    email, code, datetime.now(timezone.utc).isoformat(), offer="guia-upgrade", percent=0
                )
            send_guia_upgrade(email, code, course, guide, price)
        except Exception as exc:
            sys.stderr.write(f"mail guia-upgrade failed: {exc}\n")
        self._json(
            200,
            {
                "ok": True,
                "message": "Hemos recibido tus datos. El plan se envía por correo, no se muestra aquí.",
            },
        )

    def _resend_pdf(self) -> None:
        if not self._admin_ok():
            self._json(401, {"ok": False, "error": "No autorizado"})
            return
        data = self._read_json()
        ref = str(data.get("payment_ref") or "").strip()
        token = str(data.get("token") or "").strip()
        ent = get_by_token(token) if token else None
        if not ent and ref:
            ent = get_by_payment_ref(normalize_payment_ref(ref))
        if not ent:
            self._json(404, {"ok": False, "error": "No hay un acceso con esa referencia."})
            return
        pdf_path = store.resolve_pdf(ent)
        if not pdf_path or not pdf_path.is_file():
            self._json(409, {"ok": False, "error": "Aún no hay PDF para reenviar."})
            return
        delivery = send_plan_pdf(ent["email"], (ent.get("submission") or {}).get("name") or "tú", pdf_path, ent["payment_ref"])
        self._json(200, {"ok": True, "mail": delivery, "email": ent["email"]})


def main() -> None:
    os.chdir(ROOT)
    ensure_dirs()
    if not get("ADMIN_SECRET"):
        print("WARN: falta ADMIN_SECRET; /admin y emisión interna no funcionarán")
    # Railway injects PORT and RAILWAY_*; always bind publicly there.
    # A copied local .env with HOST=127.0.0.1 would otherwise 502.
    port = int(get("PORT") or "3000")
    on_railway = bool(get("RAILWAY_ENVIRONMENT") or get("RAILWAY_PUBLIC_DOMAIN") or get("RAILWAY_PROJECT_ID"))
    host = "0.0.0.0" if on_railway else (get("HOST") or "0.0.0.0")
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"GaryFelicienFit { _app_url() }")
    print(f"Admin            { _app_url() }/admin")
    print("Ctrl+C para detener")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido")
        httpd.server_close()


if __name__ == "__main__":
    main()
