"""Anthropic-backed AI helpers for Feature 2.

Design notes:
- Only de-identified clinical data (drug name / dose / frequency) is ever sent
  to the model — never patient identifiers. This keeps AI calls outside the PHI
  boundary for this feature.
- Every call uses the HIPAA system prompt required by the spec.
- If no API key is configured (or the SDK isn't installed), each function
  returns a deterministic offline fallback, so the prototype and the test suite
  run without network access. Swap in a HIPAA-ready API org for production.
"""
import json

try:  # optional at runtime; not needed for offline fallback
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None

from app.config import settings

SYSTEM_PROMPT = (
    "You are a HIPAA-compliant medical assistant. Do not fabricate medical facts. "
    "Always recommend consulting a licensed provider for personalized advice."
)

# Minimal offline interaction table so the warning badge is demonstrable without
# an API key. NOT a clinical reference — replace with the model / a drug DB in prod.
_OFFLINE_INTERACTIONS = {
    frozenset({"warfarin", "aspirin"}): ("high", "Increased bleeding risk when combined."),
    frozenset({"warfarin", "ibuprofen"}): ("high", "NSAIDs raise bleeding risk with anticoagulants."),
    frozenset({"lisinopril", "potassium"}): ("moderate", "May raise potassium to unsafe levels."),
    frozenset({"simvastatin", "clarithromycin"}): ("high", "Raises statin levels; muscle-injury risk."),
    frozenset({"metformin", "contrast dye"}): ("moderate", "Hold around contrast imaging."),
}


def _client():
    if not settings.ANTHROPIC_API_KEY or anthropic is None:
        return None
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _complete(prompt: str, max_tokens: int = 400) -> str | None:
    client = _client()
    if client is None:
        return None
    msg = client.messages.create(
        model=settings.ANTHROPIC_MODEL, max_tokens=max_tokens,
        system=SYSTEM_PROMPT, messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text").strip()


def generate_medication_purpose(*, generic: str, brand: str | None, dosage: str,
                                frequency: str, audience: str = "patient") -> str:
    """audience: 'patient' -> plain language (8th grade); 'doctor' -> clinical."""
    name = f"{generic}" + (f" ({brand})" if brand else "")
    if audience == "doctor":
        ask = (f"In one or two clinical sentences, state the typical indication for {name} "
               f"at {dosage} {frequency}. Do not infer this specific patient's diagnosis.")
    else:
        ask = (f"Explain in 1-2 sentences at an 8th-grade reading level what {name} is "
               f"generally used for. The patient takes {dosage} {frequency}. "
               f"Do not give personalized medical advice.")
    out = _complete(ask, max_tokens=180)
    if out:
        return out
    # Offline fallback
    if audience == "doctor":
        return f"{name}: see prescribing reference for indication. Dose {dosage} {frequency}."
    return (f"{name} is a medication your care team prescribed. You take {dosage} {frequency}. "
            f"Ask your provider how it helps you specifically.")


def check_interactions(med_generics: list[str]) -> list[dict]:
    """Return a list of {drug_a, drug_b, severity, note}. Flags only — no diagnosis."""
    names = [m.strip().lower() for m in med_generics if m and m.strip()]
    if len(names) < 2:
        return []

    client = _client()
    if client is not None:
        ask = (
            "Given this medication list, return ONLY a JSON array of potential "
            "drug-drug interactions. Each item: "
            '{"drug_a": str, "drug_b": str, "severity": "low"|"moderate"|"high", "note": str}. '
            "Flag possibilities only; do not diagnose. Return [] if none. "
            f"Medications: {json.dumps(names)}"
        )
        raw = _complete(ask, max_tokens=500)
        if raw:
            try:
                cleaned = raw.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned)
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, ValueError):
                pass  # fall through to offline table

    # Offline fallback: pairwise lookup
    flags = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            hit = _OFFLINE_INTERACTIONS.get(frozenset({names[i], names[j]}))
            if hit:
                sev, note = hit
                flags.append({"drug_a": names[i], "drug_b": names[j], "severity": sev, "note": note})
    return flags


def generate_health_summary(*, merged: dict, medications: list[dict],
                            audience: str = "patient") -> dict:
    """Feature 1 — One-Page Snapshot.

    Sends only de-identified clinical data (conditions/allergies/labs + the med
    list) to the model — never patient identifiers. Audience controls phrasing:
    'patient' = plain language (8th grade); 'doctor' = clinical terminology.
    Falls back to the deterministic offline snapshot when no key is configured.
    """
    from app.services import summary as _summary  # local import avoids cycle

    client = _client()
    if client is not None:
        level = ("plain language at an 8th-grade reading level" if audience == "patient"
                 else "clinical terminology suitable for a clinician")
        ask = (
            "Build a One-Page Snapshot from this de-identified record. Use "
            f"{level}. Return ONLY a JSON object with these keys (each a list of "
            "short strings, except disclaimer): chief_conditions, "
            "current_medications, known_allergies, recent_labs_imaging, "
            "recommended_followups, disclaimer. Rules: do NOT fabricate diagnoses "
            "or infer conditions not present in the data; base medications on the "
            "provided list; for labs add a brief plain interpretation flag; if "
            "critical info is missing (e.g. no allergies) note it in "
            "recommended_followups. Always include a disclaimer string. "
            f"\n\nRECORD: {json.dumps(merged)}\nMEDICATIONS: {json.dumps(medications)}"
        )
        raw = _complete(ask, max_tokens=900)
        if raw:
            try:
                data = json.loads(raw.replace("```json", "").replace("```", "").strip())
                if isinstance(data, dict) and "chief_conditions" in data:
                    data.setdefault("disclaimer", _summary.DISCLAIMER)
                    return data
            except (json.JSONDecodeError, ValueError):
                pass  # fall through to offline

    return _summary.offline_snapshot(merged, medications, audience)
