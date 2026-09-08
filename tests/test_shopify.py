"""Shopify webhook fulfillment tests."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import unittest

from helpers import TEST_EMAIL
from payments import (
    email_from_shopify_order,
    fulfill_shopify_order,
    order_matches_shopify_product,
    verify_shopify_webhook,
)
from validate import ValidationError


def _signed(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


class ShopifyVerifyTests(unittest.TestCase):
    def test_valid_hmac(self):
        secret = "whsec_test"
        body = b'{"id":1}'
        self.assertTrue(verify_shopify_webhook(body, _signed(body, secret), secret))

    def test_invalid_hmac(self):
        self.assertFalse(verify_shopify_webhook(b"{}", "nope", "secret"))

    def test_missing_secret(self):
        self.assertFalse(verify_shopify_webhook(b"{}", "x", ""))


class ShopifyEmailTests(unittest.TestCase):
    def test_email_from_order_root(self):
        self.assertEqual(
            email_from_shopify_order({"email": TEST_EMAIL.upper()}),
            TEST_EMAIL,
        )

    def test_email_from_customer(self):
        self.assertEqual(
            email_from_shopify_order({"customer": {"email": TEST_EMAIL}}),
            TEST_EMAIL,
        )

    def test_email_missing(self):
        with self.assertRaises(ValidationError):
            email_from_shopify_order({"id": 1})


class ShopifyProductFilterTests(unittest.TestCase):
    def test_no_filter_allows_all(self):
        prev = os.environ.get("SHOPIFY_PRODUCT_ID")
        os.environ.pop("SHOPIFY_PRODUCT_ID", None)
        os.environ.pop("SHOPIFY_VARIANT_ID", None)
        try:
            self.assertTrue(order_matches_shopify_product({"line_items": [{"product_id": 9}]}))
        finally:
            if prev is not None:
                os.environ["SHOPIFY_PRODUCT_ID"] = prev

    def test_filter_requires_match(self):
        prev_p = os.environ.get("SHOPIFY_PRODUCT_ID")
        prev_v = os.environ.get("SHOPIFY_VARIANT_ID")
        os.environ["SHOPIFY_PRODUCT_ID"] = "111"
        os.environ.pop("SHOPIFY_VARIANT_ID", None)
        try:
            self.assertTrue(
                order_matches_shopify_product({"line_items": [{"product_id": 111, "variant_id": 1}]})
            )
            self.assertFalse(
                order_matches_shopify_product({"line_items": [{"product_id": 222, "variant_id": 1}]})
            )
        finally:
            if prev_p is None:
                os.environ.pop("SHOPIFY_PRODUCT_ID", None)
            else:
                os.environ["SHOPIFY_PRODUCT_ID"] = prev_p
            if prev_v is None:
                os.environ.pop("SHOPIFY_VARIANT_ID", None)
            else:
                os.environ["SHOPIFY_VARIANT_ID"] = prev_v


class ShopifyFulfillTests(unittest.TestCase):
    def test_ignores_unpaid(self):
        result = fulfill_shopify_order(
            {"id": 99, "financial_status": "pending", "email": TEST_EMAIL}
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("ignored"), "pending")

    def test_issues_access_for_paid(self):
        # Unique id so repeated test runs do not collide on payment_ref.
        import secrets

        oid = secrets.randbelow(10**9) + 10**8
        order = {
            "id": oid,
            "financial_status": "paid",
            "email": TEST_EMAIL,
            "total_price": "38000.00",
            "currency": "CLP",
            "line_items": [{"product_id": 1, "variant_id": 1}],
        }
        result = fulfill_shopify_order(order)
        self.assertTrue(result.get("ok"))
        if result.get("duplicate"):
            self.skipTest("payment_ref already used in local db")
        self.assertIn("token", result)
        self.assertEqual(result.get("payment_ref"), f"shopify_{oid}")
        # Second call is idempotent
        again = fulfill_shopify_order(order)
        self.assertTrue(again.get("duplicate"))


if __name__ == "__main__":
    unittest.main()
