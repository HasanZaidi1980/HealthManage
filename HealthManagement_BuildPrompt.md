# Claude Build Prompt: Health Management App
## "HealthManage" — Patient & Doctor Portal Web Application

---

## ROLE & CONTEXT

You are a senior full-stack developer and UI/UX designer building a HIPAA-compliant web application called **HealthManage**. The app has two distinct portals: a **Patient Portal** and a **Doctor Portal**. Both are accessed from a shared landing/login page that routes users based on their role.

The tech stack is:
- **Frontend:** React (functional components, hooks)
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (with encrypted fields for PHI)
- **AI:** Anthropic Claude API (`claude-sonnet-4-6`) for all AI features
- **Auth:** JWT-based role authentication (patient vs. doctor)
- **Storage:** AWS S3 (or local simulation) for document uploads
- **HIPAA compliance** is a non-negotiable architectural requirement: all PHI must be encrypted at rest and in transit, audit logs must be maintained, and no PHI should ever be sent to AI models without patient consent acknowledgment.

---

## SHARED FEATURES (Both Portals)

### Feature 1 — Medical History Summarization

Patients can upload their medical records (PDF, image, or structured EHR login data via FHIR API). The AI model reads and summarizes the records. Both patients and doctors can view this summary.

**Selected Format: Option C — One-Page Snapshot**
Implement a concise, printable structured summary modeled after a clinical brief with the following sections:
- **Chief Conditions** — primary active diagnoses listed clearly
- **Current Medications** — aligned with the active medication list in Feature 2
- **Known Allergies** — drug, food, and environmental, with reaction type
- **Recent Labs/Imaging** — most recent results with date and a plain-language interpretation flag
- **Recommended Follow-Ups** — AI-identified next steps based on the record

The summary must be downloadable as a PDF and shareable directly with other providers from within the app. A "last updated" timestamp and record completeness indicator must be displayed at the top of the summary.

The AI prompt for summarization must instruct the model to:
- Use plain language (8th-grade reading level) for the patient view
- Use clinical terminology for the doctor view
- Never fabricate diagnoses or infer conditions not present in the source documents
- Flag any missing critical information (e.g., no allergy list found)

---

### Feature 2 — Active Medication List

Display a clean, card-based medication list. Each card shows:
- Medication name (generic + brand)
- Dosage and frequency
- Prescribing provider
- Start date and refill due date (if available)
- Purpose (AI-generated plain-language explanation for patients; clinical indication for doctors)
- A warning badge if the AI detects a potential drug-drug interaction (flag only — do not diagnose)

Patients see plain-language purpose. Doctors see full clinical detail.

---

### Feature 3 — AI Condition Explainer

A dedicated section where patients can tap on any condition in their record and receive an AI-generated explanation at three levels:
- **Simple:** A one-paragraph explanation as if speaking to someone with no medical background.
- **Moderate:** A 3–5 paragraph explanation covering causes, symptoms, treatment options, and lifestyle impact.
- **Detailed:** A clinically structured breakdown for medically literate users or caregivers.

Doctors can use the same interface to generate patient-ready explanations to share or print. The AI must always append: *"This explanation is for informational purposes only. Please consult your care team for personalized medical advice."*

---

### Feature 4 — Appointment Tracker

A calendar-integrated appointment manager:
- Upcoming appointments displayed in a list and mini-calendar view
- Each appointment shows: date/time, provider name, location/telehealth link, purpose of visit
- AI generates a pre-visit checklist: questions to ask the doctor, documents to bring, medications to mention
- Post-visit: appointment is archived with any notes or summaries linked to it
- Patients receive in-app reminders (push notification simulation)
- Doctors see all patient appointments in a daily/weekly schedule view

---

## SHARED FEATURES — CONTINUED

### Feature 5 — AI Visit Recording & Transcription

Recording is **doctor-initiated** (within the Doctor Portal), but the outputs are shared with patients through their portal. This feature serves both portals with role-appropriate access.

**Doctor Portal — Full Access:**
- Doctor initiates a recording session; a per-session consent acknowledgment (checkbox + logged timestamp) is required before audio capture begins
- Audio is transcribed in real time using a speech-to-text model
- On session end, the AI produces three outputs displayed in tabs:
  - **Tab 1 — Full Transcript:** The complete verbatim script of the conversation
  - **Tab 2 — Critical Points:** Bulleted list of diagnoses mentioned, medications prescribed or changed, instructions given, and follow-up actions required
  - **Tab 3 — Concise Summary:** A 3–5 sentence clinical note summarizing the visit, suitable for the medical record
- The doctor can edit the transcript and summary before pushing it to the patient's record
- Recordings are never stored in plaintext; audio is deleted after transcription unless explicitly saved by the doctor

**Patient Portal — Read-Only Access:**
- After the doctor finalizes and publishes the visit output, the patient receives a notification in their portal
- Patients can view **Tab 2 (Critical Points)** and **Tab 3 (Concise Summary)** only — written in plain language for their view
- Patients do **not** have access to Tab 1 (Full Transcript) or the raw audio
- Visit outputs are stored under "Visit Notes" in the patient's navigation and linked to the corresponding appointment in the Appointment Tracker

---

## PATIENT-ONLY FEATURES

### Feature 6 — Condition Education: AI-Curated Animations & Personalized Explanations

A patient education section powered by an AI-curated library — no video generation:
- The app maintains a **pre-built, medically reviewed library** of condition-specific animated SVG diagrams and slide decks, tagged by condition name, body system, and complexity level
- When a patient selects a condition, the AI matches it to the most relevant library asset(s) using tag-based retrieval
- The AI then generates a **personalized narration overlay** in the context of the patient's specific record (e.g., "Your Type 2 diabetes is currently managed with Metformin. Here's what that means for how your body processes sugar...")
- Presentations display as step-through slide decks (5–8 slides):
  - Slide 1: Condition overview with animated diagram
  - Slides 2–5: Causes, symptoms, treatment options, lifestyle impact
  - Final slide: "What This Means For You" — personalized to the patient's own record data
- Patients can export the deck as a PDF or view it as an in-app slideshow
- Doctors can browse the same library from their portal and **assign specific educational content** to a patient, which then appears highlighted in that patient's portal

---

## DESIGN SPECIFICATIONS

### Patient Portal — Selected Design: Option C (Dark/High-Contrast Mode)
- **Background:** `#121212` near-black
- **Cards:** `#1E1E1E` dark gray surface
- **Accent:** `#00C853` bright green — pops strongly against dark background
- **Text:** `#FAFAFA` white headings, `#B0BEC5` cool gray body
- **Signature element:** All section headers use a subtle green left-glow effect (box-shadow on left border)
- Best for: patients who spend significant screen time, users with photosensitivity

---

### Doctor Portal — Selected Design: Option C (Clean Minimal White/Blue)
- **Background:** `#FFFFFF` pure white
- **Dividers:** `#E3F2FD` very light blue
- **Accent:** `#1976D2` standard blue
- **Text:** `#212121`/`#616161`
- **Signature element:** Breadcrumb-style patient navigation at the top of every view, showing: Patient Name → Current View → Last Updated, so doctors always know context without hunting

---

## MONETIZATION MODEL — B2B2C

The app uses a **B2B2C (Business-to-Business-to-Consumer)** model. Clinics and medical practices are the paying customers; their patients get access free through the clinic's subscription.

**How it works:**
- Clinics/practices subscribe at the **practice level** (monthly or annual SaaS fee per provider seat)
- The clinic admin creates doctor accounts and links the practice's patient roster
- Patients are invited by the clinic via email and create free accounts — no payment required from patients
- The clinic's subscription tier determines feature access for both the doctors and their patients

**Subscription Tiers (build the data model to support this from day one):**

| Tier | Target | Features Included |
|------|--------|-------------------|
| **Starter** | Solo practitioners / small clinics | Features 1–4, up to 3 doctor accounts, 200 patient accounts |
| **Professional** | Mid-size practices | All features including Visit Recording (Feature 5) and Education Library (Feature 6), up to 10 doctor accounts, unlimited patients |
| **Enterprise** | Hospital systems / large groups | All features + custom branding, EHR integration, dedicated support, unlimited seats |

**Architectural implications:**
- Every user account must be linked to a `practice_id` (tenant ID) — this is a **multi-tenant architecture**
- All data queries must be scoped to the practice tenant; doctors in Practice A must never see patients from Practice B
- Feature flags must be controlled by the practice's subscription tier, enforced server-side
- A lightweight **Practice Admin role** must be added (in addition to Doctor and Patient) for managing accounts, billing, and settings within a practice


## NAVIGATION STRUCTURE

### Patient Portal Navigation
- Home / Dashboard (health snapshot, next appointment, medication reminder)
- My Health Summary (One-Page Snapshot — downloadable PDF)
- My Medications
- My Conditions (condition explainer + assigned education content)
- Appointments
- Visit Notes (Critical Points + Summary from doctor-published visit records)
- Settings / Profile / Consent Management

### Doctor Portal Navigation
- Dashboard (daily schedule, patient queue)
- Patient Search & Records
- Visit Recording (initiate session, review + publish transcripts)
- Prescriptions & Medication Review
- Appointment Manager
- Patient Education (browse library + assign content to patients)
- Settings / Practice Info

### Practice Admin Portal Navigation
- Practice Dashboard (usage stats, active accounts)
- Manage Doctors (add/remove/invite)
- Manage Patients (view roster, deactivate accounts)
- Billing & Subscription (current tier, upgrade, invoices)
- Settings (practice branding, notification preferences)

---

## TECHNICAL ARCHITECTURE NOTES

1. **Never send raw PHI to the Claude API** without: (a) stripping or pseudonymizing identifiers where possible, or (b) explicit patient consent stored in the database with timestamp and version.
2. **All AI calls** must use a `system` prompt that includes: "You are a HIPAA-compliant medical assistant. Do not fabricate medical facts. Always recommend consulting a licensed provider for personalized advice."
3. **Audit log table** must record: user_id, action_type, timestamp, and data_accessed for every interaction with PHI.
4. **Role separation** is enforced server-side, not just client-side. Doctor endpoints must validate `role === 'doctor'`, patient endpoints `role === 'patient'`, and admin endpoints `role === 'admin'` via JWT middleware.
5. **The recording feature (Feature 5)** requires explicit per-session consent from the patient (checkbox + timestamp logged) before any audio capture begins.
6. **Multi-tenancy:** Every database record (users, appointments, records, medications, visit notes) must carry a `practice_id` foreign key. All queries must be scoped to the requesting user's `practice_id` — cross-tenant data access must be architecturally impossible, not just policy-blocked.
7. **Feature flags:** A `subscription_tier` field on the `practices` table controls which features are accessible. Tier checks must be enforced at the API route level, not in the frontend.
8. **Practice Admin** is a third user role (`role === 'admin'`) with access to account management and billing endpoints only — no access to individual patient health records.

---

## DELIVERABLE ORDER

Build in this sequence:
1. Auth system (login, JWT, role routing — patient / doctor / admin)
2. Multi-tenant database schema (practices, users, records, medications, appointments — all scoped to practice_id)
3. Practice Admin Portal shell + account/billing management
4. Patient Portal shell + navigation
5. Doctor Portal shell + navigation
6. Feature 2 (Medication List) — simplest, good for testing data flow
7. Feature 4 (Appointment Tracker)
8. Feature 1 (Medical History Summarization — One-Page Snapshot)
9. Feature 3 (AI Condition Explainer)
10. Feature 5 (Visit Recording — doctor-initiated; patient read-only output)
11. Feature 6 (Patient Education — AI-curated library + personalized narration)
12. Apply full design system to all portals
13. Subscription tier feature-flagging layer
14. HIPAA audit logging layer
15. Final QA pass: role separation, tenant isolation, consent flows, error states

---

## IMPORTANT CONSTRAINTS

- Do not use any third-party health APIs that require separate enterprise agreements for a prototype (e.g., Epic FHIR). Simulate EHR data import with a structured JSON upload for now.
- Do not generate real patient data or use real medical records as test data. Use synthetic data only.
- All AI-generated medical content must include a disclaimer.
- The app must be responsive (mobile-first for the patient portal, desktop-first for the doctor portal).
