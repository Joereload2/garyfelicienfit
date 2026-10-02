"""End-to-end process: emit access, submit once, reject the second submit, keep the PDF."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from helpers import ADMIN_SECRET, PAYMENT_REF_MANUAL, TEST_EMAIL, valid_form
import store


def _json_request(method: str, url: str, body=None, headers=None):
    h = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8")) if raw else {}, raw.decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        parsed = {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            pass
        return exc.code, parsed, raw.decode("utf-8", errors="replace")


class FlujoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        os.environ["PLANFIT_DATA_DIR"] = cls.tmp.name
        os.environ["SMTP_HOST"] = ""
        os.environ["ADMIN_SECRET"] = ADMIN_SECRET
        store.configure_paths(Path(cls.tmp.name))
        store.ensure_dirs()
        import server

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.secret_h = {"X-Admin-Secret": ADMIN_SECRET}

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        store.configure_paths()
        cls.tmp.cleanup()

    def test_01_portada_acompanamiento(self):
        req = urllib.request.Request(self.base + "/")
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        self.assertEqual(resp.status, 200)
        self.assertIn("GaryFelicienFit", html)
        self.assertIn("450.000", html)
        self.assertIn("/herramientas", html)
        self.assertIn("/3meses", html)
        self.assertIn("nav-drop", html)
        self.assertIn("Calculadora", html)
        self.assertIn("wa.me/56959128603", html)
        self.assertIn("Ya soy alumno", html)
        self.assertIn("id=\"faq\"", html)
        self.assertIn("tiempo limitado", html)
        self.assertNotIn("10 min", html.lower())
        self.assertNotIn("USD $40", html)
        self.assertNotIn("buyModal", html)
        self.assertNotIn("panel-tresmeses", html)
        self.assertNotIn("jspdf", html.lower())
        self.assertNotIn("generatePlan", html)
        self.assertNotIn("myshopify.com", html.lower())
        self.assertNotIn("youtube.com", html.lower())

    def test_01d_oferta_3meses(self):
        req = urllib.request.Request(self.base + "/3meses")
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        self.assertEqual(resp.status, 200)
        self.assertIn("450.000", html)
        self.assertIn("data-open-offer", html)
        self.assertIn("data-offer-clock", html)
        self.assertIn("50%", html)
        self.assertIn("ganar músculo", html.lower())
        self.assertIn("tiempo limitado", html)
        self.assertNotIn("10 min", html.lower())
        self.assertNotIn("USD $40", html)
        self.assertNotIn("buyModal", html)

    def test_01e_oferta_timer(self):
        email = "timer.offer@example.com"
        code, data, raw = _json_request(
            "POST",
            self.base + "/api/oferta-3meses",
            {"email": email},
        )
        self.assertEqual(code, 200, data)
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("live"))
        token = data.get("token")
        self.assertTrue(token)
        self.assertGreater(data.get("remaining_s"), 0)
        self.assertLessEqual(data.get("remaining_s"), 10 * 60)
        self.assertEqual(data.get("price_clp"), 225000)
        self.assertEqual(data.get("list_clp"), 450000)
        self.assertNotIn("GARY50", raw)
        self.assertNotIn('"code"', raw)

        code2, data2, _ = _json_request(
            "POST",
            self.base + "/api/oferta-3meses",
            {"email": email},
        )
        self.assertEqual(code2, 200, data2)
        self.assertEqual(data2.get("token"), token)
        self.assertLessEqual(data2.get("remaining_s"), data.get("remaining_s"))

        code3, data3, _ = _json_request(
            "GET",
            self.base + "/api/oferta-estado?token=" + token,
        )
        self.assertEqual(code3, 200, data3)
        self.assertTrue(data3.get("live"))
        self.assertEqual(data3.get("token"), token)

        code4, data4, _ = _json_request(
            "POST",
            self.base + "/api/checkout-3meses",
            {"email": email, "token": token},
        )
        self.assertEqual(code4, 200, data4)
        self.assertEqual(data4.get("mode"), "whatsapp")
        self.assertIn("wa.me/56959128603", data4.get("url", ""))
        self.assertEqual(data4.get("price_clp"), 225000)

        code5, data5, _ = _json_request(
            "POST",
            self.base + "/api/checkout-3meses",
            {"email": email, "token": "no-existe"},
        )
        self.assertEqual(code5, 400, data5)

    def test_01b_viejas_ofertas_redirigen(self):
        for path in ("/bajar", "/recomposicion", "/empezar"):
            req = urllib.request.Request(self.base + path)
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8")
            self.assertTrue(resp.geturl().rstrip("/").endswith("/3meses"), path)
            self.assertIn("450.000", html)
            self.assertNotIn("buyModal", html)

    def test_01c_herramientas_y_registro(self):
        req = urllib.request.Request(self.base + "/herramientas")
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        self.assertEqual(resp.status, 200)
        self.assertIn("calcForm", html)
        self.assertIn("glosario", html.lower())
        self.assertIn("registro.js", html)
        self.assertIn("regAds", html)
        self.assertNotIn("checked", html.split("id=\"regAds\"")[1][:80])
        self.assertNotIn("USD $40", html)
        self.assertNotIn("youtube.com", html.lower())

        req = urllib.request.Request(self.base + "/ejercicios")
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        self.assertEqual(resp.status, 200)
        self.assertIn("ejercicios-mapa.js", html)
        self.assertIn("registro.js", html)

        code, data, _ = _json_request(
            "POST",
            self.base + "/api/registro",
            {
                "name": "Ana Test",
                "email": "ana.registro@example.com",
                "phone": "+56 9 1234 5678",
                "ads_consent": True,
                "source": "herramientas",
            },
        )
        self.assertEqual(code, 200, data)
        self.assertTrue(data.get("ok"))

        code, data, _ = _json_request(
            "POST",
            self.base + "/api/registro",
            {"name": "Ana", "email": "ana.registro@example.com", "phone": "912345678"},
        )
        self.assertEqual(code, 400, data)
        self.assertIn("autoriz", data.get("error", "").lower())

    def test_02_emitir_acceso(self):
        code, data, _ = _json_request(
            "POST",
            self.base + "/internal/entitlements",
            {"email": TEST_EMAIL, "payment_ref": PAYMENT_REF_MANUAL},
            self.secret_h,
        )
        self.assertEqual(code, 201, data)
        self.assertTrue(data.get("url", "").endswith("/usar/" + data["token"]))
        type(self).token = data["token"]
        type(self).url = data["url"]

    def test_03_payment_ref_duplicado_409(self):
        code, data, _ = _json_request(
            "POST",
            self.base + "/internal/entitlements",
            {"email": TEST_EMAIL, "payment_ref": PAYMENT_REF_MANUAL},
            self.secret_h,
        )
        self.assertEqual(code, 409)
        self.assertIn("payment_ref", data.get("error", "").lower())

    def test_04_abrir_link_no_gasta(self):
        code, data, _ = _json_request("GET", self.base + f"/api/access/{self.token}")
        self.assertEqual(code, 200, data)
        self.assertEqual(data["status"], "pending")
        self.assertEqual(data["email"], TEST_EMAIL)
        req = urllib.request.Request(self.base + f"/usar/{self.token}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        self.assertIn("form.js", html)
        self.assertNotIn("jspdf", html.lower())
        code, data, _ = _json_request("GET", self.base + f"/api/access/{self.token}")
        self.assertEqual(data["status"], "pending")

    def test_05_post_invalido_no_gasta(self):
        code, data, _ = _json_request(
            "POST",
            self.base + f"/api/submit/{self.token}",
            valid_form(age=17),
        )
        self.assertEqual(code, 400)
        self.assertIn("18", data.get("error", ""))
        code, access, _ = _json_request("GET", self.base + f"/api/access/{self.token}")
        self.assertEqual(code, 200)
        self.assertEqual(access["status"], "pending")

    def test_06_post_valido_sin_plan_en_web(self):
        code, data, raw = _json_request(
            "POST",
            self.base + f"/api/submit/{self.token}",
            valid_form(),
        )
        self.assertEqual(code, 200, data)
        self.assertTrue(data.get("ok"))
        low = raw.lower()
        self.assertNotIn("kcal", low)
        self.assertNotIn("menú", low)
        self.assertNotIn("menu", low)
        pdfs = list(Path(self.tmp.name).joinpath("pdfs").glob("*.pdf"))
        self.assertTrue(pdfs, "no se generó PDF")
        self.assertTrue(pdfs[0].read_bytes().startswith(b"%PDF-"))
        type(self).pdf = pdfs[0]
        type(self).pdf_hash = hashlib.sha256(pdfs[0].read_bytes()).hexdigest()

    def test_07_segundo_submit_409(self):
        code, data, _ = _json_request(
            "POST",
            self.base + f"/api/submit/{self.token}",
            valid_form(),
        )
        self.assertEqual(code, 409)
        self.assertIn("utilizado", data.get("error", "").lower())

    def test_08_resend_mismo_pdf(self):
        code, data, _ = _json_request(
            "POST",
            self.base + "/internal/resend-pdf",
            {"payment_ref": PAYMENT_REF_MANUAL},
            self.secret_h,
        )
        self.assertEqual(code, 200, data)
        self.assertEqual(
            hashlib.sha256(self.pdf.read_bytes()).hexdigest(),
            self.pdf_hash,
        )


if __name__ == "__main__":
    unittest.main()
