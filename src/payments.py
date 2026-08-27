"""Paid access: Stripe when configured, test checkout when ALLOW_TEST_CHECKOUT=1."""

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
from store import create_entitlement, get_by_payment_ref
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


def issue_paid_access(email: str, payment_ref: str) -> dict:
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
        import supabase_db

        if supabase_db.enabled():
            supabase_db.log_payment(
                {
                    "provider": "checkout",
                    "provider_id": payment_ref,
                    "email": email,
                    "payment_ref": payment_ref,
                    "amount_cents": price_usd() * 100,
                    "currency": "usd",
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


def email_from_stripe_session(session: dict) -> str:
    meta = session.get("metadata") or {}
    email = meta.get("email") or session.get("customer_email") or session.get("client_reference_id")
    details = session.get("customer_details") or {}
    email = email or details.get("email")
    if not email:
        raise ValidationError("El pago no trajo email.")
    return normalize_email(email)
