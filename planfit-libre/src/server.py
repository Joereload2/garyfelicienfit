"""PlanFit libre: formulario -> plan personalizado en PDF. Sin pagos, sin claves."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pdf_builder import build_pdf  # noqa: E402
from validate import ValidationError, validate_payload  # noqa: E402

PUBLIC = ROOT / "public"
MAX_BODY = 200_000
STATIC = {
    "/": ("form.html", "text/html; charset=utf-8"),
    "/form.js": ("form.js", "application/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, data: dict) -> None:
        self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in STATIC:
            name, ctype = STATIC[path]
            self._send(200, (PUBLIC / name).read_bytes(), ctype)
            return
        self._json(404, {"ok": False, "error": "No encontrado"})

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/api/plan":
            self._json(404, {"ok": False, "error": "No encontrado"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY:
            self._json(400, {"ok": False, "error": "Datos inválidos."})
            return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            cleaned = validate_payload(data)
        except ValidationError as exc:
            self._json(400, {"ok": False, "error": exc.message, "field": exc.field})
            return
        except (ValueError, UnicodeDecodeError):
            self._json(400, {"ok": False, "error": "Datos inválidos."})
            return
        slug = re.sub(r"[^a-z0-9]+", "-", cleaned["name"].lower()).strip("-") or "plan"
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "plan.pdf"
            build_pdf(pdf_path, cleaned)
            body = pdf_path.read_bytes()
        self._send(
            200,
            body,
            "application/pdf",
            {"Content-Disposition": f'attachment; filename="plan-{slug}.pdf"'},
        )


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "3000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"PlanFit listo en http://localhost:{port}  (Ctrl+C para salir)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
