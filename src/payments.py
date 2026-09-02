"""Paid access: Mercado Pago / Stripe when configured, test checkout when ALLOW_TEST_CHECKOUT=1."""

from __future__ import annotations

import hmac
import hashlib
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from envload import get
from mailer import send_access_link
from store import create_entitlement, get_by_payment_ref, log_payment
from validate import ValidationError, normalize_email, normalize_payment_ref


def app_url() -> str:
    return get("APP_URL", "http://localhost:3000").rstrip("/")


def price_usd() -> int:
    try:
        return int(get("PRICE_USD") or "40")
    except ValueError:
        return 40


def test_checkout_allowed() -> bool:
    return get("ALLOW_TEST_CHECKOUT") in {"1", "true", "yes", "on"}


def stripe_configured() -> bool:
    return bool(get("STRIPE_SECRET_KEY"))


def mp_configured() -> bool:
    return bool(get("MP_ACCESS_TOKEN"))


def price_clp() -> int:
    try:
        n = int(get("PRICE_CLP") or "38000")
    except ValueError:
        n = 38000
    return max(1000, n)


def issue_paid_access(
    email: str,
    payment_ref: str,
    *,
    provider: str = "checkout",
    amount_cents: int | None = None,
    currency: str = "usd",
) -> dict:
    email = normalize_email(email)
    payment_ref = normalize_payment_ref(payment_ref)
    if get_by_payment_ref(payment_ref):
        raise ValueError("payment_ref_used")
    token = secrets.token_urlsafe(32)
    url = f"{app_url()}/usar/{token}"
    ent = create_entitlement(token, email, payment_ref, url)
    try:
        mail = send_access_link(email, url, payment_ref)
    except Exception as exc:
        mail = f"error:{exc}"
    try:
        log_payment(
            {
                "provider": provider,
                "provider_id": payment_ref,
                "email": email,
                "payment_ref": payment_ref,
                "amount_cents": amount_cents if amount_cents is not None else price_usd() * 100,
                "currency": currency,
                "status": "approved",
            }
        )
    except Exception:
        pass
    return {
        "token": ent["token"],
        "url": url,
        "email": email,
        "payment_ref": payment_ref,
        "mail": mail,
    }


def unique_ref(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{stamp}_{secrets.token_hex(3)}"


def create_stripe_checkout(email: str, success_url: str, cancel_url: str) -> str:
    key = get("STRIPE_SECRET_KEY")
    if not key:
        raise RuntimeError("Stripe no está configurado")
    email = normalize_email(email)
    body = urllib.parse.urlencode(
        {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "customer_email": email,
            "client_reference_id": email,
            "metadata[email]": email,
            "metadata[product]": "guia-12-semanas",
            "line_items[0][quantity]": "1",
            "line_items[0][price_data][currency]": "usd",
            "line_items[0][price_data][unit_amount]": str(price_usd() * 100),
            "line_items[0][price_data][product_data][name]": "Guía 12 semanas — GaryFelicienFit",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.stripe.com/v1/checkout/sessions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Stripe error {exc.code}: {detail[:300]}") from exc
    url = data.get("url")
    if not url:
        raise RuntimeError("Stripe no devolvió URL de pago")
    return url


def verify_stripe_signature(payload: bytes, header: str, secret: str) -> bool:
    if not secret or not header:
        return False
    parts = {}
    for item in header.split(","):
        if "=" in item:
            k, _, v = item.partition("=")
            parts[k.strip()] = v.strip()
    ts = parts.get("t")
    v1 = parts.get("v1")
    if not ts or not v1:
        return False
    signed = f"{ts}.".encode("utf-8") + payload
    mac = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, v1)


def _mp_request(method: str, path: str, payload: dict | None = None) -> dict:
    token = get("MP_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("Mercado Pago no está configurado")
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["X-Idempotency-Key"] = secrets.token_hex(16)
    req = urllib.request.Request(
        "https://api.mercadopago.com" + path,
        data=data,
        method=method,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Mercado Pago error {exc.code}: {detail[:400]}") from exc
    if not raw:
        return {}
    return json.loads(raw)


def create_mp_preference(
    email: str,
    success_url: str,
    failure_url: str,
    notification_url: str,
) -> str:
    email = normalize_email(email)
    pending_url = success_url.replace("paid=1", "pending=1")
    body = {
        "items": [
            {
                "id": "guia-12-semanas",
                "title": "Guía 12 semanas — GaryFelicienFit",
                "description": "Plan personalizado de nutrición y entrenamiento. Un solo uso.",
                "quantity": 1,
                "currency_id": "CLP",
                "unit_price": price_clp(),
            }
        ],
        "payer": {"email": email},
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        },
        "auto_return": "approved",
        "binary_mode": True,
        "external_reference": email,
        "metadata": {"email": email, "product": "guia-12-semanas"},
        "statement_descriptor": "GARYFELICIENFIT",
    }
    if notification_url.startswith("https://"):
        body["notification_url"] = notification_url
    data = _mp_request("POST", "/checkout/preferences", body)
    token = get("MP_ACCESS_TOKEN")
    if token.startswith("TEST-"):
        url = data.get("sandbox_init_point") or data.get("init_point")
    else:
        url = data.get("init_point") or data.get("sandbox_init_point")
    if not url:
        raise RuntimeError("Mercado Pago no devolvió URL de pago")
    return url


def fetch_mp_payment(payment_id: str) -> dict:
    pid = str(payment_id or "").strip()
    if not pid:
        raise RuntimeError("Pago de Mercado Pago sin id")
    return _mp_request("GET", f"/v1/payments/{urllib.parse.quote(pid)}")


def email_from_mp_payment(payment: dict) -> str:
    meta = payment.get("metadata") or {}
    payer = payment.get("payer") or {}
    additional = payment.get("additional_info") or {}
    add_payer = additional.get("payer") or {}
    email = (
        meta.get("email")
        or payer.get("email")
        or add_payer.get("email")
        or payment.get("external_reference")
    )
    if not email:
        raise ValidationError("El pago de Mercado Pago no trajo email.")
    return normalize_email(email)


def fulfill_mp_payment(payment: dict) -> dict:
    status = str(payment.get("status") or "")
    if status != "approved":
        return {"ok": True, "ignored": status or "unknown"}
    email = email_from_mp_payment(payment)
    pid = str(payment.get("id") or "")
    payment_ref = normalize_payment_ref(f"mp_{pid}")
    if get_by_payment_ref(payment_ref):
        return {"ok": True, "duplicate": True, "payment_ref": payment_ref}
    try:
        issued = issue_paid_access(
            email,
            payment_ref,
            provider="mercadopago",
            amount_cents=int(payment.get("transaction_amount") or price_clp()),
            currency="clp",
        )
    except ValueError:
        return {"ok": True, "duplicate": True, "payment_ref": payment_ref}
    return {"ok": True, **issued}


def email_from_stripe_session(session: dict) -> str:
    meta = session.get("metadata") or {}
    email = meta.get("email") or session.get("customer_email") or session.get("client_reference_id")
    details = session.get("customer_details") or {}
    email = email or details.get("email")
    if not email:
        raise ValidationError("El pago no trajo email.")
    return normalize_email(email)
