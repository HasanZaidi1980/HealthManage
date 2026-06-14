# HealthManage — Backend

FastAPI + PostgreSQL backend for the HealthManage patient/doctor portal.

## Status

| Deliverable | Status |
|-------------|--------|
| #1 Auth (JWT, 3 roles) | ✅ |
| #2 Multi-tenant schema (`practice_id` everywhere) | ✅ |
| #3 Practice Admin (accounts + billing) | ✅ |
| Server-side role guards + tenant scoping | ✅ |
| Subscription tiers (feature flags + seat limits) | ✅ |
| HIPAA audit logging | ✅ |
| Consent model + patient consent endpoints | ✅ |
| **Feature 2 — Active Medication List** | ✅ |
| **Feature 1 — Medical History Summary (One-Page Snapshot)** | ✅ |
| Features 3, 4, 5, 6 | ⏳ next |
| React frontend (portal shells) | ⏳ next |

Verified end-to-end: foundation suite ran against PostgreSQL 16; full suite
(foundation + medications) passes on SQLite via the portable `GUID` type.

## Run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set SECRET_KEY + DATABASE_URL

python -m app.seed            # 2 synthetic practices, 5 users, 3 meds, 1 consent
uvicorn app.main:app --reload
```

Interactive API at **http://localhost:8000/docs**.

Seeded logins (password `password123`):
- `admin@katyclinic.example.com` — admin, Professional tier
- `dr.reyes@katyclinic.example.com` — doctor
- `patient.jordan@katyclinic.example.com` — patient (has warfarin+aspirin → interaction flag)
- `admin@houstonheart.example.com` — admin, Starter tier (separate tenant)

## Test

```bash
DATABASE_URL=sqlite:///./test.sqlite3 SECRET_KEY=test pytest -q
```

## Feature 2 — Active Medication List

Endpoints (all gated by the `medications` feature flag; all write audit rows):

| Method | Path | Role | Notes |
|--------|------|------|-------|
| POST | `/medications` | doctor | Creates med; AI fills patient + clinical purpose |
| GET | `/patients/{id}/medications` | doctor | Full clinical view |
| GET | `/patients/{id}/medications/interactions` | doctor | Drug-drug flags |
| GET | `/me/medications` | patient | Own list, plain-language, **no** clinical_indication |
| GET | `/me/medications/interactions` | patient | Requires `ai_processing` consent |
| PATCH | `/medications/{id}/deactivate` | doctor | Soft-delete |
| POST / GET | `/me/consents` | patient | Grant / list consents |

Role split is enforced by separate response schemas: `MedicationDoctorOut`
includes `clinical_indication`; `MedicationPatientOut` omits it.

## Feature 1 — Medical History Summarization (One-Page Snapshot)

Structured source records are uploaded (EHR import simulated as JSON per the
spec). The AI assembles a One-Page Snapshot with role-appropriate phrasing.

| Method | Path | Role | Notes |
|--------|------|------|-------|
| POST | `/me/records` / `/patients/{id}/records` | patient / doctor | Upload structured source record |
| GET | `/me/records` / `/patients/{id}/records` | patient / doctor | List source records |
| POST | `/me/health-summary/generate` / `/patients/{id}/...generate` | patient / doctor | Build snapshot (requires `ai_processing` consent) |
| GET | `/me/health-summary` | patient | Plain-language snapshot |
| GET | `/patients/{id}/health-summary` | doctor | Clinical snapshot |
| GET | `.../health-summary/pdf` | patient / doctor | Download printable PDF |
| POST | `/patients/{id}/health-summary/share` | doctor | Create expiring share link |
| GET | `/shared/health-summary/{token}` | public (token) | Outside-provider read-only view |

Snapshot sections: Chief Conditions, Current Medications (aligned to the active
med list from Feature 2), Known Allergies, Recent Labs/Imaging, Recommended
Follow-Ups. A completeness indicator (% + missing-data flags, e.g. "no allergy
list found") and a last-updated timestamp accompany every snapshot. The AI is
instructed never to fabricate diagnoses; only de-identified clinical data is
sent. PDF rendering uses reportlab (`app/services/pdf.py`).

## AI integration (`app/services/ai.py`)

- Only de-identified clinical data (drug name/dose/frequency) is sent to the
  model — never patient identifiers — so Feature 2's AI calls stay outside the
  PHI boundary.
- Every call uses the required HIPAA system prompt.
- **No API key needed to run**: each function returns a deterministic offline
  fallback (incl. a small interaction table) so the prototype and tests run
  offline. Set `ANTHROPIC_API_KEY` to use Claude.

## HIPAA note

Synthetic data only. For production with real PHI, route Anthropic calls through
a HIPAA-ready API organization under a signed BAA (the standard key is not
BAA-covered), and ensure your Postgres host and storage are covered too.
