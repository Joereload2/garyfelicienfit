"""Send mail via SMTP, or write to data/outbox/ when SMTP_HOST is empty."""

from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from envload import get
import store
from store import ensure_dirs


def smtp_configured() -> bool:
    return bool(get("SMTP_HOST"))


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


def send_mail(kind: str, to_addr: str, subject: str, body: str, pdf_path: Path | None = None) -> str:
    if smtp_configured():
        _send_smtp(to_addr, subject, body, pdf_path)
        return "smtp"
    out = _write_outbox(kind, to_addr, subject, body, pdf_path)
    return f"outbox:{out.name}"


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
        "PlanFit\n"
    )
    return send_mail("access", email, "Tu enlace de PlanFit", body)


def send_plan_pdf(email: str, name: str, pdf_path: Path, payment_ref: str) -> str:
    body = (
        f"Hola {name},\n\n"
        "Adjunto va tu plan personalizado de 12 semanas en PDF.\n"
        "No lo publicamos en la web y este envío corresponde a un único pago.\n\n"
        f"Referencia: {payment_ref}\n"
        "Si necesitas el mismo archivo otra vez, pide el reenvío a soporte "
        "(no se regenera).\n\n"
        "PlanFit\n"
    )
    return send_mail("pdf", email, "Tu plan PlanFit (PDF)", body, pdf_path)
