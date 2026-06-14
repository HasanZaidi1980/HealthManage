"""Deterministic assembly for the One-Page Snapshot.

This module does the non-AI work: merging source records, computing the
completeness indicator, and producing an offline snapshot used as the AI
fallback. The AI layer (services/ai.py) adds plain-language / clinical phrasing
and follow-up recommendations on top of this when a key is configured.
"""
from __future__ import annotations

DISCLAIMER = ("This summary is generated from your records for informational purposes "
              "only and may be incomplete. Please consult your care team for personalized "
              "medical advice.")

# Sections considered critical for the completeness indicator.
_CRITICAL = ["conditions", "medications", "allergies", "labs"]


def merge_records(records: list[dict]) -> dict:
    """Aggregate structured clinical data across all source records."""
    merged = {"conditions": [], "allergies": [], "labs": [], "imaging": []}
    for rec in records:
        for key in merged:
            items = rec.get(key)
            if isinstance(items, list):
                merged[key].extend(items)
    return merged


def build_completeness(merged: dict, medications: list[dict]) -> dict:
    present = {
        "has_conditions": bool(merged.get("conditions")),
        "has_medications": bool(medications),
        "has_allergies": bool(merged.get("allergies")),
        "has_labs": bool(merged.get("labs") or merged.get("imaging")),
    }
    missing = []
    if not present["has_allergies"]:
        missing.append("No allergy list found — confirm allergies with the patient.")
    if not present["has_conditions"]:
        missing.append("No active conditions documented.")
    if not present["has_medications"]:
        missing.append("No active medications on file.")
    if not present["has_labs"]:
        missing.append("No recent labs or imaging on file.")
    pct = round(100 * sum(present.values()) / len(_CRITICAL))
    return {**present, "percent_complete": pct, "missing": missing}


def _fmt_condition(c: dict) -> str:
    name = c.get("name", "Unknown condition")
    status = c.get("status")
    return f"{name}" + (f" ({status})" if status else "")


def _fmt_allergy(a: dict) -> str:
    sub = a.get("substance", "Unknown")
    typ = a.get("type")
    rxn = a.get("reaction")
    extra = ", ".join(x for x in [typ, f"reaction: {rxn}" if rxn else None] if x)
    return f"{sub}" + (f" ({extra})" if extra else "")


def _fmt_lab(l: dict) -> str:
    name = l.get("name", "Lab")
    val = l.get("value") or l.get("result") or ""
    date = l.get("date", "")
    flag = l.get("flag")
    flagtxt = f" [{flag}]" if flag and flag.lower() not in ("normal", "") else ""
    return f"{name}: {val}{flagtxt}" + (f" ({date})" if date else "")


def offline_snapshot(merged: dict, medications: list[dict], audience: str = "patient") -> dict:
    """Assemble the 5-section snapshot directly from data (no AI)."""
    conditions = [_fmt_condition(c) for c in merged.get("conditions", [])]
    allergies = [_fmt_allergy(a) for a in merged.get("allergies", [])]
    labs = [_fmt_lab(l) for l in merged.get("labs", [])] + \
           [_fmt_lab(i) for i in merged.get("imaging", [])]
    meds = [f"{m.get('name_generic','?')} {m.get('dosage','')} {m.get('frequency','')}".strip()
            for m in medications]

    follow_ups = []
    for l in merged.get("labs", []):
        flag = (l.get("flag") or "").lower()
        if flag and flag not in ("normal", ""):
            follow_ups.append(f"Discuss {l.get('name','lab')} result with your provider.")
    if not allergies:
        follow_ups.append("Confirm and document any allergies.")

    return {
        "chief_conditions": conditions,
        "current_medications": meds,
        "known_allergies": allergies,
        "recent_labs_imaging": labs,
        "recommended_followups": follow_ups,
        "disclaimer": DISCLAIMER,
    }
