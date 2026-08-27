"""Shared fixtures for PlanFit tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Reserved for the admin panel (see PRUEBAS.md). Automated tests append a suffix.
PAYMENT_REF_MANUAL = "pay_prueba_manual"
TEST_EMAIL = "prueba@planfit.local"
ADMIN_SECRET = "Z5ybdNf7xluObI6vOEkETT1vAA3isnLU-Xae8qX9W1-HyZInspyc-KJm4OsJKmz_"


def valid_form(email: str = TEST_EMAIL, **overrides) -> dict:
    payload = {
        "email": email,
        "name": "Ana Prueba",
        "age": 32,
        "weight": 70,
        "height": 165,
        "sex": "female",
        "goal": "lose",
        "targetWeight": 66,
        "motivation": "health",
        "days": 3,
        "location": "gym",
        "duration": "45",
        "experience": "beginner",
        "focusMuscle": "balanced",
        "vegetables": ["Brócoli", "Zanahoria", "Tomate"],
        "fruits": ["Manzana", "Pera", "Kiwi"],
        "proteins": ["Pollo"],
        "carbs": ["Arroz"],
    }
    payload.update(overrides)
    return payload
