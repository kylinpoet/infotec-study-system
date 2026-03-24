# Infotec Study System

AI-enhanced compulsory education information technology platform built with `FastAPI + Vue 3`.

## Structure

- `backend/` FastAPI API, SQLite demo data, teacher/student workflow contracts
- `frontend/` Vue 3 + Vite interface for portal, teacher workbench, and student center
- `docs/` product plan and wireframe artifacts

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

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to the backend.

