"""Doctor patient-roster endpoint: tenant-scoped, role-guarded."""
import pytest
from fastapi.testclient import TestClient
from app.database import Base, engine
import app.models  # noqa: F401
from app.main import app


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


def test_doctor_patient_roster(client):
    admin = client.post("/auth/register-practice", json={
        "practice_name": "Roster Clinic", "subscription_tier": "professional",
        "admin_email": "admin@r.example.com", "admin_password": "password123",
        "admin_full_name": "Admin"}).json()["access_token"]
    client.post("/admin/doctors", headers=h(admin), json={
        "email": "doc@r.example.com", "password": "password123", "full_name": "Dr R"})
    pid = client.post("/admin/patients", headers=h(admin), json={
        "email": "pat@r.example.com", "password": "password123", "full_name": "Pat R"}).json()["id"]
    doc = client.post("/auth/login", json={"email": "doc@r.example.com", "password": "password123"}).json()["access_token"]

    roster = client.get("/patients", headers=h(doc)).json()
    assert [p["email"] for p in roster] == ["pat@r.example.com"]
    assert client.get(f"/patients/{pid}", headers=h(doc)).json()["full_name"] == "Pat R"
    # admin (no PHI) cannot use the clinical roster
    assert client.get("/patients", headers=h(admin)).status_code == 403
