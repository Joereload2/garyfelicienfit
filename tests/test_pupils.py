"""Alumno tracking tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from helpers import TEST_EMAIL
import store
import pupils
from validate import ValidationError


class PupilTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["PLANFIT_DATA_DIR"] = self.tmp.name
        store.configure_paths(Path(self.tmp.name))
        store.ensure_dirs()

    def tearDown(self):
        store.configure_paths()
        self.tmp.cleanup()

    def test_create_login_and_day(self):
        created = pupils.create_pupil(TEST_EMAIL, "Jose")
        self.assertEqual(len(created["pin"]), 6)
        session = pupils.login(TEST_EMAIL, "12345")
        pupil = pupils.pupil_from_session(session["session"])
        pupils.save_day(pupil, "2026-09-13", {"entreno": 1, "agua": 6, "coca": 1})
        st = pupils.state(pupil, "2026-09-07", "2026-09-13")
        self.assertEqual(st["days"]["2026-09-13"]["agua"], 6)
        self.assertTrue(any(m["key"] == "coca" and m["enabled"] for m in st["metrics"]))

    def test_add_and_hide_metric(self):
        created = pupils.create_pupil("otro@test.com", "Ana")
        pupil = pupils.pupil_from_session(pupils.login("otro@test.com", "12345")["session"])
        metric = pupils.add_metric(pupil, "Caminata extra", "number", "min")
        self.assertTrue(metric["key"])
        pupils.toggle_metric(pupil, metric["key"], False)
        st = pupils.state(pupil, "2026-09-01", "2026-09-07")
        hidden = [m for m in st["metrics"] if m["key"] == metric["key"]][0]
        self.assertEqual(hidden["enabled"], 0)

    def test_lift_planner(self):
        created = pupils.create_pupil("lift@test.com", "Luis")
        pupil = pupils.pupil_from_session(pupils.login("lift@test.com", "12345")["session"])
        lift = pupils.add_lift(
            pupil,
            {"day": "2026-09-13", "week": 3, "exercise": "Sentadilla", "load": 60, "sets": 3, "reps": 8},
        )
        self.assertEqual(lift["exercise"], "Sentadilla")
        pupils.add_lift(
            pupil,
            {"day": "2026-09-13", "week": 3, "exercise": "Press banca", "load": 40, "sets": 3, "reps": 10},
        )
        pupils.add_lift(
            pupil,
            {"day": "2026-09-13", "week": 3, "exercise": "Zancadas", "load": 20, "sets": 3, "reps": 10},
        )
        pupils.remove_lift(pupil, lift["id"])
        st = pupils.state(pupil, "2026-09-13", "2026-09-13")
        self.assertEqual(len(st["lifts"]), 2)
        self.assertIn("Sentadilla", st["exercises"]["strength"])
        self.assertIn("Caminata", st["exercises"]["cardio"])

    def test_bad_login(self):
        pupils.create_pupil(TEST_EMAIL, "Jose")
        with self.assertRaises(ValidationError):
            pupils.login(TEST_EMAIL, "000000")

    def test_guide_and_peso_metric(self):
        out = pupils.login("guia@test.com", "12345")
        pupil = pupils.pupil_from_session(out["session"])
        st = pupils.state(pupil, "2026-09-01", "2026-09-13")
        self.assertTrue(any(m["key"] == "peso" for m in st["metrics"]))
        guide = pupils.save_guide(
            pupil,
            {"objetivo": "Recomposición corporal", "peso": 80, "peso_meta": 78, "kcal": 2200, "proteina": 160, "carbos": 200, "grasa": 70},
        )
        self.assertEqual(guide["kcal"], 2200)
        st2 = pupils.state(pupil, "2026-09-01", "2026-09-13")
        self.assertEqual(st2["guide"]["proteina"], 160)

    def test_compliance_empty_vs_failing(self):
        out = pupils.login("semaforo@test.com", "12345")
        pupil = pupils.pupil_from_session(out["session"])
        pupils.save_guide(
            pupil,
            {"objetivo": "Bajar de peso", "kcal": 2000, "proteina": 150, "carbos": 180, "grasa": 60},
        )
        empty = pupils.state(pupil, "2026-09-01", "2026-09-07")
        self.assertEqual(empty["compliance"]["kind"], "no_fill")
        pupils.save_day(
            pupil,
            "2026-09-07",
            {"entreno": 0, "kcal": 4000, "proteina": 20, "carbos": 400, "grasa": 200},
        )
        bad = pupils.state(pupil, "2026-09-07", "2026-09-07")
        self.assertEqual(bad["compliance"]["kind"], "failing")
        self.assertLess(bad["compliance"]["avg_pct"], 70)

    def test_open_login_any_email(self):
        out = pupils.login("solo-un-nombre", "12345")
        self.assertTrue(out["session"])
        self.assertIn("@", out["email"])


if __name__ == "__main__":
    unittest.main()
