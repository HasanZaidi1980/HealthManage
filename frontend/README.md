# HealthManage — Frontend

React (Vite) frontend for the HealthManage portals. Talks to the FastAPI
backend. Three role-routed portals share one login.

## Status

| Portal | Design | Built |
|--------|--------|-------|
| Shared login + role routing | — | ✅ |
| **Patient Portal** | Dark / high-contrast (#121212 / #00C853, green left-glow headers) | ✅ |
| **Doctor Portal** | Clean white/blue (#1976D2, breadcrumb context bar) | ✅ |
| **Practice Admin Portal** | White/blue | ✅ |
| Feature 2 — Medications (patient + doctor) | | ✅ |
| Feature 1 — Health Summary (patient + doctor, PDF + share) | | ✅ |
| Consent management (patient) | | ✅ |
| Features 3–6 | | ⏳ |

## Run

```bash
npm install
cp .env.example .env      # VITE_API_URL=http://localhost:8000
npm run dev               # http://localhost:5173
```

The backend must be running (uvicorn on :8000) and seeded. Its CORS allow-list
already includes http://localhost:5173.

Demo logins (password `password123`):
- patient.jordan@katyclinic.example.com — Patient Portal
- dr.reyes@katyclinic.example.com — Doctor Portal
- admin@katyclinic.example.com — Admin Portal

## Structure

```
src/
  api/client.js          fetch wrapper + JWT handling
  auth/                  AuthContext + ProtectedRoute (role-gated)
  pages/Login.jsx        shared login, routes by role
  pages/patient/         dark-theme portal: Dashboard, Medications, HealthSummary, Consents
  pages/doctor/          white/blue portal: Dashboard, Patients, PatientDetail
  pages/admin/           white/blue portal: Dashboard, Doctors, Patients, Billing
  components/ManageUsers.jsx
  styles/                base.css, patient.css, clinic.css, login.css
```

## Notes

- Token is stored in localStorage (this is a real app, not a Claude artifact).
- Requires the backend `GET /patients` and `GET /patients/{id}` doctor endpoints
  (added alongside this frontend).
