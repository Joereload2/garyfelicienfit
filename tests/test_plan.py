import unittest

from helpers import TEST_EMAIL, valid_form
from plan import build_habits, build_plan, calculate_calories
from validate import validate_payload


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.user = validate_payload(valid_form(), TEST_EMAIL)

    def test_calories_positive(self):
        kcal = calculate_calories(self.user)
        self.assertGreater(kcal, 1000)
        self.assertLess(kcal, 4000)

    def test_macros_match_calories(self):
        plan = build_plan(self.user)
        m = plan["macros"]
        approx = m["protein_g"] * 4 + m["carb_g"] * 4 + m["fat_g"] * 9
        self.assertAlmostEqual(approx, plan["calories"], delta=20)

    def test_three_menus(self):
        plan = build_plan(self.user)
        self.assertEqual(len(plan["menus"]), 3)
        self.assertIn("Pollo", plan["menus"][0]["lunch"])

    def test_habits_water_from_weight(self):
        habits = build_habits(self.user)
        self.assertEqual(habits["water_ml"], int(round(70 * 33)))
        self.assertIn("8.000", habits["steps"])

    def test_intro_and_donts(self):
        plan = build_plan(self.user)
        self.assertGreaterEqual(len(plan["intro"]), 6)
        self.assertTrue(any("enlace" in d.lower() for d in plan["donts"]))

    def test_food_swaps_include_selected(self):
        plan = build_plan(self.user)
        keys = [row[0] for row in plan["food_swaps"]]
        self.assertIn("Pollo", keys)
        self.assertIn("Brócoli", keys)


if __name__ == "__main__":
    unittest.main()
