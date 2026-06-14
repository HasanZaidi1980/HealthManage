"""Feature 1 — Medical History Summarization end-to-end test.

Verifies: record upload, consent-gated generation, role-split snapshots,
completeness/missing flags, PDF export, tokenized sharing, and guards.
Runs with the offline snapshot fallback (no API key needed).
"""
import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
import app.models  # noqa: F401
from app.main import app


@pytest.fixture(scope="module", autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def h(t):
    return {"Authorization": f"Bearer {t}"}


def _register(client, name, email):
    return client.post("/auth/register-practice", json={
        "practice_name": name, "subscription_tier": "professional",
        "admin_email": email, "admin_password": "password123",
        "admin_full_name": "Admin"}).json()["access_token"]


RECORD = {
    "title": "EHR Import",
    "source_type": "json",
    "data": {
        "conditions": [{"name": "Type 2 Diabetes", "status": "active"}],
        "allergies": [{"substance": "Penicillin", "type": "drug", "reaction": "hives"}],
        "labs": [{"name": "HbA1c", "value": "7.4%", "date": "2026-05-02", "flag": "high"}],
    },
}


def test_health_summary_feature(client):
    admin = _register(client, "Katy Clinic", "admin@s.example.com")
    pat_id = client.post("/admin/patients", headers=h(admin), json={
        "email": "pat@s.example.com", "password": "password123", "full_name": "Jordan Lee"}).json()["id"]
    client.post("/admin/doctors", headers=h(admin), json={
        "email": "doc@s.example.com", "password": "password123", "full_name": "Dr Reyes"})
    doc = client.post("/auth/login", json={"email": "doc@s.example.com", "password": "password123"}).json()["access_token"]
    pat = client.post("/auth/login", json={"email": "pat@s.example.com", "password": "password123"}).json()["access_token"]

    # Doctor uploads a source record + a medication (for the meds section)
    assert client.post(f"/patients/{pat_id}/records", headers=h(doc), json=RECORD).status_code == 201
    client.post("/medications", headers=h(doc), json={
        "patient_id": pat_id, "name_generic": "metformin", "dosage": "500 mg", "frequency": "twice daily"})

    # Generate BEFORE consent -> 403
    assert client.post(f"/patients/{pat_id}/health-summary/generate", headers=h(doc)).status_code == 403

    # Patient grants consent, then generation succeeds
    client.post("/me/consents", headers=h(pat), json={
        "consent_type": "ai_processing", "version": "v1", "granted": True})
    r = client.post(f"/patients/{pat_id}/health-summary/generate", headers=h(doc))
    assert r.status_code == 200, r.text
    snap = r.json()
    assert "Type 2 Diabetes" in " ".join(snap["snapshot"]["chief_conditions"])
    assert any("metformin" in m for m in snap["snapshot"]["current_medications"])
    assert snap["snapshot"]["disclaimer"]
    assert snap["completeness"]["has_allergies"] is True
    assert snap["source_record_count"] == 1
    assert snap["last_updated"]

    # Patient view present; clinician view present
    assert client.get("/me/health-summary", headers=h(pat)).status_code == 200
    assert client.get(f"/patients/{pat_id}/health-summary", headers=h(doc)).status_code == 200

    # PDF export -> real PDF bytes
    pdf_resp = client.get("/me/health-summary/pdf", headers=h(pat))
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content[:4] == b"%PDF"

    # Share -> tokenized read-only link works without auth
    share = client.post(f"/patients/{pat_id}/health-summary/share", headers=h(doc),
                        json={"shared_with": "Dr. External", "expires_in_days": 7}).json()
    shared = client.get(share["share_url"])
    assert shared.status_code == 200
    assert "Type 2 Diabetes" in " ".join(shared.json()["snapshot"]["chief_conditions"])
    # Bogus token rejected
    assert client.get("/shared/health-summary/not-a-real-token").status_code == 404

    # Guards: admin (no PHI) blocked; cross-tenant blocked
    assert client.post(f"/patients/{pat_id}/records", headers=h(admin), json=RECORD).status_code == 403
    other = _register(client, "Other", "admin@o.example.com")
    client.post("/admin/doctors", headers=h(other), json={
        "email": "doc@o.example.com", "password": "password123", "full_name": "Dr X"})
    other_doc = client.post("/auth/login", json={"email": "doc@o.example.com", "password": "password123"}).json()["access_token"]
    assert client.get(f"/patients/{pat_id}/health-summary", headers=h(other_doc)).status_code == 404


def test_missing_allergy_flag(client):
    admin = _register(client, "Gap Clinic", "admin@gap.example.com")
    pid = client.post("/admin/patients", headers=h(admin), json={
        "email": "gap@gap.example.com", "password": "password123", "full_name": "No Allergy"}).json()["id"]
    client.post("/admin/doctors", headers=h(admin), json={
        "email": "gapdoc@gap.example.com", "password": "password123", "full_name": "Dr G"})
    doc = client.post("/auth/login", json={"email": "gapdoc@gap.example.com", "password": "password123"}).json()["access_token"]
    pt = client.post("/auth/login", json={"email": "gap@gap.example.com", "password": "password123"}).json()["access_token"]

    client.post(f"/patients/{pid}/records", headers=h(doc), json={
        "title": "Partial", "source_type": "json",
        "data": {"conditions": [{"name": "Asthma", "status": "active"}]}})  # no allergies/labs
    client.post("/me/consents", headers=h(pt), json={
        "consent_type": "ai_processing", "version": "v1", "granted": True})
    r = client.post(f"/patients/{pid}/health-summary/generate", headers=h(doc)).json()
    assert r["completeness"]["has_allergies"] is False
    assert any("allergy" in m.lower() for m in r["completeness"]["missing"])
