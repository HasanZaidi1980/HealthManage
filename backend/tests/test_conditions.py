"""Feature 3 — Condition Explainer end-to-end test (offline AI fallback)."""
import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
import app.models  # noqa: F401
from app.main import app
from app.services.ai import EXPLAINER_DISCLAIMER


@pytest.fixture(scope="module", autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def h(t): return {"Authorization": f"Bearer {t}"}


def test_condition_explainer(client):
    admin = client.post("/auth/register-practice", json={
        "practice_name": "Cx Clinic", "subscription_tier": "professional",
        "admin_email": "admin@cx.example.com", "admin_password": "password123",
        "admin_full_name": "Admin"}).json()["access_token"]
    pid = client.post("/admin/patients", headers=h(admin), json={
        "email": "pat@cx.example.com", "password": "password123", "full_name": "Pat C"}).json()["id"]
    client.post("/admin/doctors", headers=h(admin), json={
        "email": "doc@cx.example.com", "password": "password123", "full_name": "Dr C"})
    doc = client.post("/auth/login", json={"email": "doc@cx.example.com", "password": "password123"}).json()["access_token"]
    pat = client.post("/auth/login", json={"email": "pat@cx.example.com", "password": "password123"}).json()["access_token"]

    # Upload a record so the patient has conditions
    client.post(f"/patients/{pid}/records", headers=h(doc), json={
        "title": "EHR", "source_type": "json",
        "data": {"conditions": [{"name": "Type 2 Diabetes", "status": "active"},
                                {"name": "Hypertension", "status": "active"}]}})

    # Conditions derived from records (patient + doctor views)
    pc = client.get("/me/conditions", headers=h(pat)).json()
    assert {c["name"] for c in pc} == {"Type 2 Diabetes", "Hypertension"}
    assert len(client.get(f"/patients/{pid}/conditions", headers=h(doc)).json()) == 2

    # Doctor explainer works without patient consent (generic, no identifiers)
    r = client.post(f"/patients/{pid}/conditions/explain", headers=h(doc),
                    json={"condition": "Type 2 Diabetes", "level": "moderate"}).json()
    assert r["level"] == "moderate" and "Type 2 Diabetes" in r["explanation"]
    assert EXPLAINER_DISCLAIMER in r["explanation"]
    assert r["disclaimer"] == EXPLAINER_DISCLAIMER

    # Patient explainer requires consent
    assert client.post("/me/conditions/explain", headers=h(pat),
                       json={"condition": "Hypertension", "level": "simple"}).status_code == 403
    client.post("/me/consents", headers=h(pat), json={
        "consent_type": "ai_processing", "version": "v1", "granted": True})
    ok = client.post("/me/conditions/explain", headers=h(pat),
                     json={"condition": "Hypertension", "level": "detailed"})
    assert ok.status_code == 200 and EXPLAINER_DISCLAIMER in ok.json()["explanation"]

    # Invalid level rejected by schema
    assert client.post("/me/conditions/explain", headers=h(pat),
                       json={"condition": "X", "level": "bogus"}).status_code == 422
