"""Feature 4 — Appointment Tracker end-to-end test (offline AI fallback)."""
from datetime import datetime, timedelta, timezone

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


def test_appointments(client):
    admin = client.post("/auth/register-practice", json={
        "practice_name": "Appt Clinic", "subscription_tier": "professional",
        "admin_email": "admin@ap.example.com", "admin_password": "password123",
        "admin_full_name": "Admin"}).json()["access_token"]
    pid = client.post("/admin/patients", headers=h(admin), json={
        "email": "pat@ap.example.com", "password": "password123", "full_name": "Pat A"}).json()["id"]
    client.post("/admin/doctors", headers=h(admin), json={
        "email": "doc@ap.example.com", "password": "password123", "full_name": "Dr A"})
    doc = client.post("/auth/login", json={"email": "doc@ap.example.com", "password": "password123"}).json()["access_token"]
    pat = client.post("/auth/login", json={"email": "pat@ap.example.com", "password": "password123"}).json()["access_token"]

    soon = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    # Doctor creates an appointment
    r = client.post("/appointments", headers=h(doc), json={
        "patient_id": pid, "scheduled_at": soon, "purpose": "Diabetes follow-up",
        "location": "Room 4"})
    assert r.status_code == 201, r.text
    appt = r.json()
    assert appt["provider_name"] == "Dr A" and appt["status"] == "scheduled"
    aid = appt["id"]

    # Doctor schedule + patient list
    assert len(client.get("/appointments?range=week", headers=h(doc)).json()) == 1
    assert len(client.get(f"/patients/{pid}/appointments", headers=h(doc)).json()) == 1
    assert len(client.get("/me/appointments", headers=h(pat)).json()) == 1

    # Patient reminder for the upcoming appointment
    rem = client.get("/me/appointments/reminders", headers=h(pat)).json()
    assert len(rem) == 1 and "Diabetes follow-up" in rem[0]["message"]

    # Doctor generates checklist
    cl = client.post(f"/appointments/{aid}/checklist", headers=h(doc)).json()
    assert cl["questions"] and cl["documents"]
    # Patient can view the doctor-generated checklist
    assert client.get(f"/me/appointments/{aid}/checklist", headers=h(pat)).status_code == 200

    # Patient self-generate requires consent
    a2 = client.post("/appointments", headers=h(doc), json={
        "patient_id": pid, "scheduled_at": soon, "purpose": "BP check"}).json()["id"]
    assert client.post(f"/me/appointments/{a2}/checklist", headers=h(pat)).status_code == 403
    client.post("/me/consents", headers=h(pat), json={"consent_type": "ai_processing", "version": "v1", "granted": True})
    assert client.post(f"/me/appointments/{a2}/checklist", headers=h(pat)).status_code == 200

    # Complete + archive with notes
    upd = client.patch(f"/appointments/{aid}", headers=h(doc), json={
        "status": "completed", "notes": "Adjusted plan; recheck in 3 months."}).json()
    assert upd["status"] == "completed" and "recheck" in upd["notes"]
    # Completed appointment no longer appears as a reminder
    assert all(x["appointment_id"] != aid for x in client.get("/me/appointments/reminders", headers=h(pat)).json())

    # Guards
    assert client.get("/appointments", headers=h(admin)).status_code == 403
    other = client.post("/auth/register-practice", json={
        "practice_name": "Other", "subscription_tier": "professional",
        "admin_email": "admin@o2.example.com", "admin_password": "password123",
        "admin_full_name": "A"}).json()["access_token"]
    client.post("/admin/doctors", headers=h(other), json={
        "email": "doc@o2.example.com", "password": "password123", "full_name": "Dr O"})
    odoc = client.post("/auth/login", json={"email": "doc@o2.example.com", "password": "password123"}).json()["access_token"]
    assert client.patch(f"/appointments/{aid}", headers=h(odoc), json={"status": "cancelled"}).status_code == 404
