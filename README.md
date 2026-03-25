# Infotec Study System

AI-enhanced compulsory education information technology platform built with `FastAPI + Vue 3`.

## Structure

- `backend/` FastAPI API, SQLite demo data, teacher/student workflow contracts
- `frontend/` Vue 3 + Vite interface for portal, teacher workbench, and student center
- `docs/` product plan and wireframe artifacts

## Highlights

- Multi-school portal, teacher workbench, student center, and admin console in one platform
- AI-enhanced course activities, submissions, reviews, and classroom analytics
- Portal admin can configure the platform LLM connection with `base_url`, `api_key`, model, and runtime parameters

## Quick Start

### Backend

```powershell
cd backend
python -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
uvicorn app.main:app --reload
```

Demo accounts:

- Student: `240101` / `12345`
- Teacher: `kylin` / `222221`
- Portal admin: `portaladmin` / `333333`

Optional environment variables:

- `INFOTEC_DATABASE_URL` custom SQLite/PostgreSQL connection string
- `INFOTEC_LLM_ENCRYPTION_KEY` secret used to encrypt stored LLM API keys at rest

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to the backend.

## Admin

After logging in as the portal admin, open `/admin` to manage:

- portal hero copy and featured school
- school profiles, themes, metrics, and announcements
- platform-wide LLM connection settings for future AI generation features
