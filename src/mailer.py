"""Send mail via SMTP, or write to data/outbox/ when SMTP_HOST is empty."""

from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import json
import urllib.error
import urllib.request

from envload import get
import store
import supabase_db
from store import ensure_dirs


def smtp_configured() -> bool:
    return bool(get("SMTP_HOST"))


def resend_configured() -> bool:
    return bool(get("RESEND_API_KEY"))


def _from_addr() -> str:
    return get("SMTP_FROM") or "PlanFit <noreply@localhost>"


def _write_outbox(kind: str, to_addr: str, subject: str, body: str, pdf_path: Path | None) -> Path:
    ensure_dirs()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_kind = kind.replace(" ", "-")
    path = store.OUTBOX_DIR / f"{stamp}-{safe_kind}.txt"
    lines = [
        f"From: {_from_addr()}",
        f"To: {to_addr}",
        f"Subject: {subject}",
        f"Date: {stamp}",
        "",
        body.strip(),
        "",
    ]
    if pdf_path:
        lines.append(f"Attachment: {pdf_path}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _send_smtp(to_addr: str, subject: str, body: str, pdf_path: Path | None) -> None:
    msg = EmailMessage()
    msg["From"] = _from_addr()
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    if pdf_path and pdf_path.is_file():
        data = pdf_path.read_bytes()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=pdf_path.name,
        )

    host = get("SMTP_HOST")
    port = int(get("SMTP_PORT") or "587")
    user = get("SMTP_USER")
    password = get("SMTP_PASSWORD")
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        if user:
            smtp.login(user, password)
        smtp.send_message(msg)


def _send_resend(to_addr: str, subject: str, body: str, pdf_path: Path | None) -> None:
    payload = {
        "from": _from_addr(),
        "to": [to_addr],
        "subject": subject,
        "text": body,
    }
    if pdf_path and pdf_path.is_file():
        import base64

        payload["attachments"] = [
            {
                "filename": pdf_path.name,
                "content": base64.b64encode(pdf_path.read_bytes()).decode("ascii"),
            }
        ]
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + get("RESEND_API_KEY"),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Resend " + exc.read().decode("utf-8", errors="replace")[:300]) from exc


def send_mail(kind: str, to_addr: str, subject: str, body: str, pdf_path: Path | None = None) -> str:
    status = "error"
    provider = "none"
    err = None
    try:
        if resend_configured():
            _send_resend(to_addr, subject, body, pdf_path)
            provider, status = "resend", "sent"
        elif smtp_configured():
            _send_smtp(to_addr, subject, body, pdf_path)
            provider, status = "smtp", "sent"
        else:
            out = _write_outbox(kind, to_addr, subject, body, pdf_path)
            provider, status = "outbox", "outbox"
            result = f"outbox:{out.name}"
            _log(kind, to_addr, subject, body, provider, status, None)
            return result
        _log(kind, to_addr, subject, body, provider, status, None)
        return provider
    except Exception as exc:
        err = str(exc)
        _log(kind, to_addr, subject, body, provider, "error", err)
        raise


def _log(kind: str, to_addr: str, subject: str, body: str, provider: str, status: str, error: str | None) -> None:
    payload = {
        "kind": kind,
        "to_email": to_addr,
        "subject": subject,
        "body": body[:8000],
        "provider": provider,
        "status": status,
        "error": error,
    }
    try:
        store.log_mail(payload)
    except Exception:
        return


def send_discount_code(email: str, code: str) -> str:
    body = (
        "Hola,\n\n"
        "Pediste el 50% de descuento del entrenamiento personalizado "
        "con seguimiento real (3 meses).\n\n"
        f"Tu código: {code}\n\n"
        "Precio lista: $450.000 CLP\n"
        "Con este código: $225.000 CLP\n\n"
        "Escríbele a Gary por WhatsApp y menciona el código para coordinar el pago:\n"
        "https://wa.me/56959128603\n\n"
        "Si no pediste este descuento, ignora este correo.\n\n"
        "GaryFelicienFit\n"
    )
    return send_mail("discount", email, "Tu 50% off — código GaryFelicienFit", body)


def send_access_link(email: str, url: str, payment_ref: str) -> str:
    body = (
        "Hola,\n\n"
        "Tu pago ya está verificado. Tienes un enlace de un solo uso para "
        "completar el formulario de PlanFit.\n\n"
        f"{url}\n\n"
        f"Referencia: {payment_ref}\n\n"
        "El formulario solo se puede enviar una vez. El plan no se muestra "
        "en la web: lo recibirás en un segundo correo, en PDF.\n"
        "Si te equivocas, no reutilices el enlace; escribe a soporte.\n\n"
        "GaryFelicienFit\n"
    )
    return send_mail("access", email, "Tu enlace de GaryFelicienFit", body)


def send_plan_pdf(email: str, name: str, pdf_path: Path, payment_ref: str) -> str:
    body = (
        f"Hola {name},\n\n"
        "Adjunto va tu plan personalizado de 12 semanas en PDF.\n"
        "No lo publicamos en la web y este envío corresponde a un único pago.\n\n"
        f"Referencia: {payment_ref}\n"
        "Si necesitas el mismo archivo otra vez, pide el reenvío a soporte "
        "(no se regenera).\n\n"
        "GaryFelicienFit\n"
    )
    return send_mail("pdf", email, "Tu plan GaryFelicienFit (PDF)", body, pdf_path)
