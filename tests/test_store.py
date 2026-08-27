import tempfile
import unittest
from pathlib import Path

from helpers import PAYMENT_REF_MANUAL, TEST_EMAIL
import store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        store.configure_paths(Path(self.tmp.name))
        store.ensure_dirs()

    def tearDown(self):
        store.configure_paths()
        self.tmp.cleanup()

    def test_create_and_get(self):
        ent = store.create_entitlement("tok_a", TEST_EMAIL, PAYMENT_REF_MANUAL, "http://x/usar/tok_a")
        self.assertEqual(ent["status"], "pending")
        self.assertEqual(store.get_by_token("tok_a")["email"], TEST_EMAIL)
        self.assertEqual(store.get_by_payment_ref(PAYMENT_REF_MANUAL)["token"], "tok_a")

    def test_duplicate_payment_ref(self):
        store.create_entitlement("tok_a", TEST_EMAIL, PAYMENT_REF_MANUAL, "http://x/usar/tok_a")
        with self.assertRaises(ValueError) as ctx:
            store.create_entitlement("tok_b", TEST_EMAIL, PAYMENT_REF_MANUAL, "http://x/usar/tok_b")
        self.assertEqual(str(ctx.exception), "payment_ref_used")

    def test_consume_only_once(self):
        store.create_entitlement("tok_a", TEST_EMAIL, PAYMENT_REF_MANUAL, "http://x/usar/tok_a")
        store.consume_pending("tok_a", "x.pdf", "x.pdf", {"name": "Ana"})
        with self.assertRaises(ValueError):
            store.consume_pending("tok_a", "y.pdf", "y.pdf", {"name": "Ana"})
        self.assertEqual(store.get_by_token("tok_a")["status"], "used")

    def test_missing_token(self):
        with self.assertRaises(KeyError):
            store.consume_pending("nope", "x.pdf", "x.pdf", {})


if __name__ == "__main__":
    unittest.main()
