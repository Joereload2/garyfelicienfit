import unittest

from helpers import TEST_EMAIL, valid_form
from validate import ValidationError, bmi, max_change_kg, normalize_email, normalize_payment_ref, validate_payload


class ValidateTests(unittest.TestCase):
    def test_email_normalizes(self):
        self.assertEqual(normalize_email("  Prueba@PlanFit.Local "), TEST_EMAIL)

    def test_payment_ref_ok(self):
        self.assertEqual(normalize_payment_ref("pay_prueba_manual"), "pay_prueba_manual")

    def test_payment_ref_too_short(self):
        with self.assertRaises(ValidationError):
            normalize_payment_ref("ab")

    def test_valid_payload(self):
        cleaned = validate_payload(valid_form(), TEST_EMAIL)
        self.assertEqual(cleaned["email"], TEST_EMAIL)
        self.assertEqual(cleaned["age"], 32)
        self.assertTrue(17 <= cleaned["bmi"] <= 65)

    def test_email_locked_to_payment(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_payload(valid_form(email="otro@x.com"), TEST_EMAIL)
        self.assertEqual(ctx.exception.field, "email")

    def test_age_under_18(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_payload(valid_form(age=17), TEST_EMAIL)
        self.assertIn("18 y 70", ctx.exception.message)

    def test_need_three_vegetables(self):
        with self.assertRaises(ValidationError):
            validate_payload(valid_form(vegetables=["Brócoli", "Tomate"]), TEST_EMAIL)

    def test_need_one_protein(self):
        with self.assertRaises(ValidationError):
            validate_payload(valid_form(proteins=[]), TEST_EMAIL)

    def test_imc_over_65(self):
        # 180 kg at 140 cm -> BMI ~91.8
        with self.assertRaises(ValidationError) as ctx:
            validate_payload(valid_form(weight=180, height=140, targetWeight=170), TEST_EMAIL)
        self.assertIn("IMC", ctx.exception.message)

    def test_aggressive_loss_rejected(self):
        # 9% of 70 kg = 6.3 kg max; 20 kg loss is too much
        with self.assertRaises(ValidationError) as ctx:
            validate_payload(valid_form(targetWeight=50), TEST_EMAIL)
        self.assertIn("agresiva", ctx.exception.message)

    def test_max_change_lose(self):
        self.assertAlmostEqual(max_change_kg(70, "lose"), min(70 * 0.09, 10.8))

    def test_bmi_formula(self):
        self.assertAlmostEqual(bmi(70, 165), 70 / (1.65 ** 2), places=3)


if __name__ == "__main__":
    unittest.main()
