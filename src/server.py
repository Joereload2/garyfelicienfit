"""GaryFelicienFit / PlanFit HTTP server. Landing + one-shot delivery."""

from __future__ import annotations

import hmac
import json
import os
import re
import sys
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from envload import get, load_env, require  # noqa: E402

load_env()

from mailer import send_plan_pdf  # noqa: E402
from payments import (  # noqa: E402
    create_stripe_checkout,
    email_from_stripe_session,
    issue_paid_access,
    price_usd,
    stripe_configured,
    test_checkout_allowed,
    unique_ref,
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

PUBLIC = ROOT / "public"
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
    return get("APP_URL", "http://localhost:3000").rstrip("/")


def _admin_secret() -> str:
    return require("ADMIN_SECRET")


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

    def _html_file(self, name: str, code: int = 200) -> None:
        path = (PUBLIC / name).resolve()
        if not str(path).startswith(str(PUBLIC.resolve())) or not path.is_file():
            self._json(404, {"ok": False, "error": "No encontrado"})
            return
        self._send(code, path.read_bytes(), MIME.get(path.suffix, "application/octet-stream"))

    def _static(self, rel: str) -> None:
        path = (PUBLIC / rel).resolve()
        public = PUBLIC.resolve()
        if public not in path.parents and path != public:
            self._json(404, {"ok": False, "error": "No encontrado"})
            return
        if not path.is_file():
            self._json(404, {"ok": False, "error": "No encontrado"})
            return
        self._send(200, path.read_bytes(), MIME.get(path.suffix, "application/octet-stream"))

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
        if path == "/admin":
            self._html_file("admin.html")
            return
        if path == "/gracias":
            self._html_file("gracias.html")
            return
        if path in ("/styles.css", "/form.js", "/site.css", "/site.js", "/videos.json"):
            self._static(path.lstrip("/"))
            return
        if re.fullmatch(r"/img/[A-Za-z0-9._-]+\.(jpg|jpeg|png|webp)", path):
            self._static(path.lstrip("/"))
            return
        if path == "/api/product":
            self._json(
                200,
                {
                    "ok": True,
                    "price_usd": price_usd(),
                    "stripe": stripe_configured(),
                    "test_checkout": test_checkout_allowed(),
                },
            )
            return
        match = re.fullmatch(r"/usar/([A-Za-z0-9_-]+)", path)
        if match:
            self._html_file("form.html")
            return
        match = re.fullmatch(r"/api/access/([A-Za-z0-9_-]+)", path)
        if match:
            self._api_access(match.group(1))
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
            if path == "/internal/resend-pdf":
                self._resend_pdf()
                return
            if path == "/api/checkout":
                self._checkout()
                return
            if path == "/api/coaching":
                self._coaching()
                return
            if path == "/webhooks/stripe":
                self._stripe_webhook()
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

    def _checkout(self) -> None:
        data = self._read_json()
        email = normalize_email(data.get("email"))
        if stripe_configured():
            success = f"{_app_url()}/gracias?paid=1"
            cancel = f"{_app_url()}/#guia"
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
                    "error": "La pasarela de pago aún no está activa. Escribe para reservar tu guía.",
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
        pdf_path = Path(ent["pdf_path"]) if ent.get("pdf_path") else None
        if not pdf_path or not pdf_path.is_file():
            self._json(409, {"ok": False, "error": "Aún no hay PDF para reenviar."})
            return
        delivery = send_plan_pdf(ent["email"], (ent.get("submission") or {}).get("name") or "tú", pdf_path, ent["payment_ref"])
        self._json(200, {"ok": True, "mail": delivery, "email": ent["email"]})


def main() -> None:
    os.chdir(ROOT)
    ensure_dirs()
    _admin_secret()
    host = get("HOST") or "127.0.0.1"
    port = int(get("PORT") or "3000")
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
