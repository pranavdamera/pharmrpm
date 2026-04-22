# PharmRPM MVP Demo

PharmRPM is a pharmacist-led remote patient monitoring MVP for independent pharmacies. This local demo shows patient identification, clinical monitoring, alert handling, interaction logging, and billing readiness in one operational workflow.

## Stack

- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + SQLite
- API: REST (`/api/*`)

## File Tree

```text
pharmrpm/
  backend/
    app/
      services/
        alerts.py
        billing.py
        interactions.py
      __init__.py
      database.py
      main.py
      models.py
      schemas.py
      seed.py
    requirements.txt
  frontend/
    src/
      components/
        Layout.tsx
        UI.tsx
      pages/
        AlertsPage.tsx
        BillingPage.tsx
        DashboardPage.tsx
        PatientDetailPage.tsx
        PatientsPage.tsx
        QueuePage.tsx
      api.ts
      App.tsx
      index.css
      main.tsx
      types.ts
    index.html
    package.json
    postcss.config.js
    tailwind.config.js
    tsconfig.json
    vite.config.ts
  .gitignore
  README.md
```

## Local Setup

### 1) Backend

```bash
cd backend
python3 -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8004
```

Backend URL: `http://127.0.0.1:8004`

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

## Seed Data

The backend auto-seeds on first startup if the DB is empty.

Manual reseed endpoint:

```bash
curl -X POST http://127.0.0.1:8004/api/demo/seed
```

Seed includes:
- 16 patients (mix of enrolled + eligible)
- 2 supervising physicians
- Conditions: HTN, T2DM, CHF, COPD (single and multi-condition)
- Device types: BP cuff, glucometer, weight scale, pulse oximeter
- Vital histories, interactions, yellow/red alert patterns, and offline/missing-reading cases

## Implemented API Endpoints

- `GET /api/dashboard/summary`
- `GET /api/patients/queue`
- `POST /api/patients/enroll`
- `GET /api/patients`
- `GET /api/patients/{id}`
- `GET /api/patients/{id}/vitals`
- `GET /api/patients/{id}/alerts`
- `GET /api/alerts`
- `POST /api/alerts/{id}/resolve`
- `POST /api/interactions/log`
- `GET /api/billing/summary?month=YYYY-MM`
- `GET /api/billing/patients?month=YYYY-MM`
- `GET /api/billing/summary/export?month=YYYY-MM` (JSON download)
- `POST /api/demo/seed`
- `POST /api/demo/ingest-mock-reading`

## Demo Flow Walkthrough

1. Open `Dashboard` to review active patients, alert counts, missing/offline, and revenue estimate.
2. Open `Patient Queue` and click `Enroll` on an eligible patient.
3. Open that patient in `Patients` and review vitals, alerts, 7-day summary, and billing indicators.
4. In patient detail, resolve an open alert with required note + optional time spent.
5. Log a pharmacist interaction (phone/video/in-person/secure_message); duration auto-calculates from start/end.
6. Go to `Billing` to review per-patient readiness, CPT code qualification, and estimated revenue/share.
7. Click `Generate Summary` to download JSON monthly summary for physician/billing review.

## Business Rules Implemented

- Billing ready requires both:
  - `>=16` transmission days this month
  - `>=20` interaction minutes this month
- CPT logic:
  - `99453`: one-time onboarding setup (shown when patient enrolled)
  - `99454`: monthly device supply with 16+ transmission days
  - `99457`: first 20 monthly interactive minutes
  - `99458`: additional 20 monthly interactive minutes (>=40 total)
- 2026 rates in app:
  - `99453 = 19.33`
  - `99454 = 48.42`
  - `99457 = 48.72`
  - `99458 = 38.22`
- Recurring monthly value shown: `99454 + 99457 = 97.14`
- Pharmacy share assumption default: `65%` and adjustable in billing UI
