import os
import unittest

from helpers import TEST_EMAIL
from payments import (
    course_list_clp,
    course_sale_clp,
    email_from_mp_payment,
    fulfill_mp_payment,
    mp_configured,
    offer_minutes,
    price_clp,
)
from validate import ValidationError


class MercadoPagoTests(unittest.TestCase):
    def test_price_clp_reads_env(self):
        prev = os.environ.get("PRICE_CLP")
        os.environ["PRICE_CLP"] = "45000"
        try:
            self.assertEqual(price_clp(), 45000)
        finally:
            if prev is None:
                os.environ.pop("PRICE_CLP", None)
            else:
                os.environ["PRICE_CLP"] = prev

    def test_email_from_payer(self):
        pay = {"id": 99, "status": "approved", "payer": {"email": TEST_EMAIL.upper()}, "metadata": {}}
        self.assertEqual(email_from_mp_payment(pay), TEST_EMAIL)

    def test_email_from_metadata(self):
        pay = {"metadata": {"email": TEST_EMAIL}, "payer": {}, "external_reference": "other"}
        self.assertEqual(email_from_mp_payment(pay), TEST_EMAIL)

    def test_email_missing(self):
        with self.assertRaises(ValidationError):
            email_from_mp_payment({"payer": {}, "metadata": {}})

    def test_course_prices(self):
        self.assertEqual(course_list_clp(), 450000)
        self.assertEqual(course_sale_clp(), 225000)
        self.assertEqual(offer_minutes(), 10)

    def test_mp_3meses_pending_ignored(self):
        result = fulfill_mp_payment({"status": "pending", "metadata": {"product": "3meses"}})
        self.assertEqual(result.get("ignored"), "pending")

    def test_mp_configured_false_without_token(self):
        prev = os.environ.get("MP_ACCESS_TOKEN")
        os.environ["MP_ACCESS_TOKEN"] = ""
        try:
            self.assertFalse(mp_configured())
        finally:
            if prev is None:
                os.environ.pop("MP_ACCESS_TOKEN", None)
            else:
                os.environ["MP_ACCESS_TOKEN"] = prev


if __name__ == "__main__":
    unittest.main()
