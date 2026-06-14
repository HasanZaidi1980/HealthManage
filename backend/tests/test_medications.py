"""Feature 2 — Medication List end-to-end test.

Verifies: doctor create, role-split views (patient sees no clinical_indication),
tenant + role guards, drug-interaction flagging, and consent-gated patient AI.
Runs with the offline AI fallback (no API key needed).
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


def _register(client, name, tier, email):
    return client.post("/auth/register-practice", json={
        "practice_name": name, "subscription_tier": tier,
        "admin_email": email, "admin_password": "password123",
        "admin_full_name": "Admin"}).json()["access_token"]


def test_medication_feature(client):
    admin = _register(client, "Katy Clinic", "professional", "admin@med.example.com")

    # admin creates a doctor and a patient
    doc_id = client.post("/admin/doctors", headers=h(admin), json={
        "email": "doc@med.example.com", "password": "password123", "full_name": "Dr Reyes"}).json()["id"]
    pat_id = client.post("/admin/patients", headers=h(admin), json={
        "email": "pat@med.example.com", "password": "password123", "full_name": "Jordan Lee"}).json()["id"]

    doc = client.post("/auth/login", json={"email": "doc@med.example.com", "password": "password123"}).json()["access_token"]
    pat = client.post("/auth/login", json={"email": "pat@med.example.com", "password": "password123"}).json()["access_token"]

    # --- Doctor creates meds (warfarin + aspirin -> interaction) ---
    for g, b, d, f in [("warfarin", "Coumadin", "5 mg", "once daily"),
                       ("aspirin", "Bayer", "81 mg", "once daily")]:
        r = client.post("/medications", headers=h(doc), json={
            "patient_id": pat_id, "name_generic": g, "name_brand": b,
            "dosage": d, "frequency": f})
        assert r.status_code == 201, r.text
        # Doctor view includes clinical_indication + AI plain-language purpose
        assert "clinical_indication" in r.json()
        assert r.json()["plain_language_purpose"]

    # --- Doctor full list ---
    doc_list = client.get(f"/patients/{pat_id}/medications", headers=h(doc)).json()
    assert len(doc_list) == 2
    assert all("clinical_indication" in m for m in doc_list)

    # --- Patient view: own meds, NO clinical_indication exposed ---
    pat_list = client.get("/me/medications", headers=h(pat)).json()
    assert len(pat_list) == 2
    assert all("clinical_indication" not in m for m in pat_list)
    assert all(m["plain_language_purpose"] for m in pat_list)

    # --- Interaction flag (offline table catches warfarin+aspirin) ---
    flags = client.get(f"/patients/{pat_id}/medications/interactions", headers=h(doc)).json()
    pair = {flags[0]["drug_a"], flags[0]["drug_b"]}
    assert pair == {"warfarin", "aspirin"} and flags[0]["severity"] == "high"

    # --- Patient AI interaction requires consent ---
    assert client.get("/me/medications/interactions", headers=h(pat)).status_code == 403
    client.post("/me/consents", headers=h(pat), json={
        "consent_type": "ai_processing", "version": "v1", "granted": True})
    r = client.get("/me/medications/interactions", headers=h(pat))
    assert r.status_code == 200 and len(r.json()) == 1

    # --- Guards: admin (no PHI) and cross-tenant blocked ---
    assert client.get(f"/patients/{pat_id}/medications", headers=h(admin)).status_code == 403

    other_admin = _register(client, "Other Practice", "professional", "admin@other.example.com")
    other_doc = client.post("/admin/doctors", headers=h(other_admin), json={
        "email": "doc@other.example.com", "password": "password123", "full_name": "Dr X"})
    other_doc_tok = client.post("/auth/login", json={
        "email": "doc@other.example.com", "password": "password123"}).json()["access_token"]
    # Doctor from another practice cannot read this patient (tenant isolation -> 404)
    assert client.get(f"/patients/{pat_id}/medications", headers=h(other_doc_tok)).status_code == 404
