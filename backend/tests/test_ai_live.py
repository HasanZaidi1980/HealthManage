"""Live AI check — makes ONE real Anthropic call to confirm the key works.

Run locally from backend/ after setting ANTHROPIC_API_KEY in .env:
    pytest tests/test_ai_live.py -v -s

Skips itself automatically if no key is configured, so it won't break CI or the
offline test suite.
"""
import pytest

from app.config import settings
from app.services import ai

pytestmark = pytest.mark.skipif(
    not settings.ANTHROPIC_API_KEY,
    reason="ANTHROPIC_API_KEY not set — skipping live AI test",
)


def test_medication_purpose_is_live():
    """A real call should return text that differs from the offline fallback."""
    out = ai.generate_medication_purpose(
        generic="metformin", brand="Glucophage",
        dosage="500 mg", frequency="twice daily", audience="patient")
    print("\n--- patient purpose ---\n", out)

    assert out and len(out) > 20
    # The offline fallback always contains this exact phrase; a live call won't.
    assert "Ask your provider how it helps you specifically." not in out
    assert "metformin" in out.lower()


def test_interaction_check_is_live():
    flags = ai.check_interactions(["warfarin", "aspirin", "metformin"])
    print("\n--- interactions ---\n", flags)

    assert isinstance(flags, list)
    for f in flags:
        assert {"drug_a", "drug_b", "severity", "note"} <= set(f)
        assert f["severity"] in {"low", "moderate", "high"}
