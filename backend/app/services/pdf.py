"""Render a One-Page Snapshot to a printable PDF (reportlab).

Returns PDF bytes. Kept dependency-light; reportlab is pure-Python.
"""
from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer,
)

_SECTIONS = [
    ("Chief Conditions", "chief_conditions"),
    ("Current Medications", "current_medications"),
    ("Known Allergies", "known_allergies"),
    ("Recent Labs / Imaging", "recent_labs_imaging"),
    ("Recommended Follow-Ups", "recommended_followups"),
]


def render_snapshot_pdf(*, patient_name: str, snapshot: dict, completeness: dict,
                        last_updated: datetime, audience: str = "patient") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                            leftMargin=0.8 * inch, rightMargin=0.8 * inch)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, spaceAfter=2)
    meta = ParagraphStyle("meta", parent=styles["Normal"], fontSize=9, textColor=HexColor("#616161"))
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12,
                        textColor=HexColor("#1976D2"), spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    foot = ParagraphStyle("foot", parent=styles["Normal"], fontSize=8,
                          textColor=HexColor("#9E9E9E"), spaceBefore=14)

    flow = [Paragraph("Health Snapshot", h1)]
    flow.append(Paragraph(
        f"{patient_name} &nbsp;•&nbsp; {audience.title()} view &nbsp;•&nbsp; "
        f"Last updated {last_updated.strftime('%b %d, %Y %H:%M UTC')} &nbsp;•&nbsp; "
        f"Record completeness: {completeness.get('percent_complete', 0)}%", meta))
    flow.append(Spacer(1, 4))
    flow.append(HRFlowable(width="100%", color=HexColor("#E3F2FD")))

    for label, key in _SECTIONS:
        flow.append(Paragraph(label, h2))
        items = snapshot.get(key) or []
        if items:
            flow.append(ListFlowable(
                [ListItem(Paragraph(str(i), body), leftIndent=10) for i in items],
                bulletType="bullet", start="•"))
        else:
            flow.append(Paragraph("<i>None on file.</i>", body))

    missing = completeness.get("missing") or []
    if missing:
        flow.append(Paragraph("Data Gaps", h2))
        flow.append(ListFlowable(
            [ListItem(Paragraph(str(m), body), leftIndent=10) for m in missing],
            bulletType="bullet", start="•"))

    flow.append(Paragraph(snapshot.get("disclaimer", ""), foot))
    doc.build(flow)
    return buf.getvalue()
