import pytest
from fastapi.testclient import TestClient
from app.database import Base, engine, SessionLocal
import app.models  # noqa: F401
from app.main import app
from app.models.audit import AuditLog


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


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_foundation_end_to_end(client):
    r = client.post("/auth/register-practice", json={
        "practice_name": "Katy Family Clinic", "subscription_tier": "professional",
        "admin_email": "admin@a.example.com", "admin_password": "password123",
        "admin_full_name": "Admin A"})
    assert r.status_code == 201, r.text
    a_admin = r.json()["access_token"]

    a_practice = client.get("/auth/me", headers=h(a_admin)).json()["practice_id"]
    assert client.post("/admin/doctors", headers=h(a_admin), json={
        "email": "doc@a.example.com", "password": "password123", "full_name": "Dr A"}).status_code == 201
    assert client.post("/admin/patients", headers=h(a_admin), json={
        "email": "pat@a.example.com", "password": "password123", "full_name": "Pat A"}).status_code == 201

    users = client.get("/admin/users", headers=h(a_admin)).json()
    assert len(users) == 3 and all(u["practice_id"] == a_practice for u in users)

    b_admin = client.post("/auth/register-practice", json={
        "practice_name": "Houston Heart", "subscription_tier": "starter",
        "admin_email": "admin@b.example.com", "admin_password": "password123",
        "admin_full_name": "Admin B"}).json()["access_token"]
    assert {u["email"] for u in client.get("/admin/users", headers=h(b_admin)).json()} == {"admin@b.example.com"}

    patient = client.post("/auth/login", json={"email": "pat@a.example.com", "password": "password123"}).json()["access_token"]
    assert client.get("/admin/users", headers=h(patient)).status_code == 403
    assert client.post("/auth/login", json={"email": "pat@a.example.com", "password": "nope"}).status_code == 401
    assert client.get("/admin/users").status_code == 403

    for i in range(3):
        assert client.post("/admin/doctors", headers=h(b_admin), json={
            "email": f"doc{i}@b.example.com", "password": "password123", "full_name": f"Dr B{i}"}).status_code == 201
    assert client.post("/admin/doctors", headers=h(b_admin), json={
        "email": "doc3@b.example.com", "password": "password123", "full_name": "Dr B3"}).status_code == 402

    bill = client.get("/admin/billing", headers=h(a_admin)).json()
    assert "visit_recording" in bill["features"] and bill["doctor_count"] == 1
    assert "visit_recording" not in client.get("/admin/billing", headers=h(b_admin)).json()["features"]

    db = SessionLocal()
    try:
        actions = {row.action_type for row in db.query(AuditLog).all()}
    finally:
        db.close()
    assert {"practice.register", "auth.login", "doctor.create", "patient.create"} <= actions
