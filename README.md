# AI Marketing Asset Engine

Production-oriented monorepo scaffold for a SaaS app with:
- FastAPI microservices (auth, billing, campaign, AI generation, asset)
- Next.js + Tailwind frontend
- Supabase PostgreSQL + Supabase Storage
- Google OAuth + JWT
- DeepSeek + SDXL (RunPod) integrations
- Credit billing, rate limiting (Redis), analytics events
- Render (backend) + Vercel (frontend) deployment configs
- GitHub Actions CI

## Folder Structure

```text
.
├─ backend/
│  ├─ common/                         # Shared settings, auth, db, models, schemas, utils
│  ├─ alembic/                        # DB migrations
│  ├─ auth-service/
│  ├─ billing-service/
│  ├─ campaign-service/
│  ├─ ai-generation-service/
│  └─ asset-service/
├─ frontend/                          # Next.js app
├─ deploy/
│  ├─ render.yaml
│  └─ vercel.json
├─ .github/workflows/ci.yml
├─ docker-compose.yml
└─ .env.example
```

## Module-by-Module Breakdown

### 1) Project setup
Description:
- Monorepo with backend microservices + frontend.
- Shared Python package in `backend/common`.

Dependencies:
- Python 3.11+
- Node 20+
- Docker Desktop

Install:
```bash
cp .env.example .env
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
pip install -e backend/common
cd frontend && npm install && cd ..
```

### 2) Database schema (Supabase + Alembic)
Description:
- Alembic migration creates: `users`, `campaigns`, `assets`, `asset_versions`, `credit_ledger`, `usage_events`.

Files:
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/20260216_0001_init.py`

Run migration:
```bash
cd backend
alembic upgrade head
cd ..
```

### 3) Microservices scaffolding
Description:
- Each service is a standalone FastAPI app with docs at `/docs`.
- Shared CORS/logging/settings model.

Services:
- `backend/auth-service/app/main.py`
- `backend/billing-service/app/main.py`
- `backend/campaign-service/app/main.py`
- `backend/ai-generation-service/app/main.py`
- `backend/asset-service/app/main.py`

### 4) API endpoints by service
Auth service:
- `POST /api/v1/auth/google`
- `GET /api/v1/me`
- `POST /api/v1/dev-token` (dev only)

Billing service:
- `GET /api/v1/credits/balance`
- `POST /api/v1/credits/add`
- `POST /api/v1/credits/deduct`
- `GET /api/v1/credits/ledger`

Campaign service:
- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns`
- `GET /api/v1/campaigns/{campaign_id}`
- `PATCH /api/v1/campaigns/{campaign_id}/status`

AI generation service:
- `POST /api/v1/ai/generate-text`
- `POST /api/v1/ai/generate-image`
- `POST /api/v1/ai/suggestions`
- `POST /api/v1/ai/refine`
- `POST /api/v1/ai/regenerate`

Asset service:
- `POST /api/v1/assets`
- `GET /api/v1/assets`
- `PATCH /api/v1/assets/{asset_id}`
- `GET /api/v1/assets/{asset_id}/versions`
- `POST /api/v1/assets/{asset_id}/undo`
- `POST /api/v1/assets/{asset_id}/redo`

### 5) Frontend pages/components
Description:
- App router dashboard with campaigns, assets, AI studio.

Files:
- `frontend/app/page.tsx` (entry/login)
- `frontend/app/(dashboard)/campaigns/page.tsx`
- `frontend/app/(dashboard)/assets/page.tsx`
- `frontend/app/(dashboard)/ai-studio/page.tsx`
- `frontend/components/top-nav.tsx`
- `frontend/lib/api.ts`

### 6) Authentication system
Description:
- Google ID token verification backend-side.
- Internal JWT created by auth service, used across all services.

Key files:
- `backend/common/common/core/security.py`
- `backend/common/common/utils/deps.py`
- `backend/auth-service/app/api/v1/routes.py`

### 7) AI orchestration (DeepSeek + SDXL RunPod)
Description:
- Text generation via DeepSeek chat endpoint.
- Image generation via RunPod SDXL endpoint.
- Automatic mock fallback if provider keys are missing.

Key file:
- `backend/ai-generation-service/app/api/v1/routes.py`

### 8) Credit and billing logic
Description:
- Credits stored on `users.credits_balance`.
- Mutations tracked in `credit_ledger`.
- AI operations deduct credits before generation.

Files:
- `backend/billing-service/app/api/v1/routes.py`
- `backend/ai-generation-service/app/api/v1/routes.py`

### 9) Asset versioning and undo/redo
Description:
- Each edit appends `asset_versions`.
- `current_version` pointer drives undo/redo behavior.
- Storage URL metadata stored in `assets.metadata_json`.

File:
- `backend/asset-service/app/api/v1/routes.py`

### 10) Tests
Description:
- Basic health tests for all services.
- Suggestion endpoint test in AI service.

Files:
- `backend/*-service/tests/test_health.py`
- `backend/ai-generation-service/tests/test_suggestions.py`

Run:
```bash
cd backend/auth-service && PYTHONPATH=../common:. pytest tests && cd ../..
cd backend/billing-service && PYTHONPATH=../common:. pytest tests && cd ../..
cd backend/campaign-service && PYTHONPATH=../common:. pytest tests && cd ../..
cd backend/ai-generation-service && PYTHONPATH=../common:. pytest tests && cd ../..
cd backend/asset-service && PYTHONPATH=../common:. pytest tests && cd ../..
```

### 11) Deployment (Render + Vercel + Supabase + RunPod)
Backend:
- Use `deploy/render.yaml` Blueprint in Render.
- Set env vars from `.env.example`.
- Point `SUPABASE_DB_URL` to Supabase pooled connection string.

Frontend:
- Import `frontend/` into Vercel project.
- Add env vars:
  - `NEXT_PUBLIC_AUTH_SERVICE_URL`
  - `NEXT_PUBLIC_BILLING_SERVICE_URL`
  - `NEXT_PUBLIC_CAMPAIGN_SERVICE_URL`
  - `NEXT_PUBLIC_AI_SERVICE_URL`
  - `NEXT_PUBLIC_ASSET_SERVICE_URL`

Supabase:
- Create project and `assets` storage bucket.
- Run migration from local or CI pipeline against Supabase DB.

RunPod:
- Create SDXL endpoint and set `RUNPOD_SDXL_ENDPOINT` + `RUNPOD_API_KEY`.

### 12) CI/CD workflow
Description:
- GitHub Actions pipeline for backend tests + frontend build.

File:
- `.github/workflows/ci.yml`

## Environment Variables

Use `.env.example` as baseline. Required production variables:
- `SECRET_KEY`
- `SUPABASE_DB_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GOOGLE_CLIENT_ID`
- `REDIS_URL`
- `DEEPSEEK_API_KEY`
- `RUNPOD_API_KEY`
- `RUNPOD_SDXL_ENDPOINT`
- Frontend `NEXT_PUBLIC_*_SERVICE_URL` endpoints

## Run Locally

Option A (Docker, easiest):
```bash
cp .env.example .env
docker compose up --build
```

Option B (manual):
1. Start Postgres + Redis.
2. Install Python deps and common package.
3. Run each service:
```bash
cd backend/auth-service && PYTHONPATH=../common:. uvicorn app.main:app --reload --port 8001
cd backend/billing-service && PYTHONPATH=../common:. uvicorn app.main:app --reload --port 8002
cd backend/campaign-service && PYTHONPATH=../common:. uvicorn app.main:app --reload --port 8003
cd backend/ai-generation-service && PYTHONPATH=../common:. uvicorn app.main:app --reload --port 8004
cd backend/asset-service && PYTHONPATH=../common:. uvicorn app.main:app --reload --port 8005
cd frontend && npm run dev
```

API docs:
- `http://localhost:8001/docs`
- `http://localhost:8002/docs`
- `http://localhost:8003/docs`
- `http://localhost:8004/docs`
- `http://localhost:8005/docs`

## Security and Reliability Notes
- JWT auth guard on protected endpoints.
- CORS locked by `CORS_ORIGINS`.
- Structured JSON logging via `structlog`.
- Redis fixed-window rate limit for AI endpoints.
- Error handling with explicit HTTP status responses.
- Provider keys optional in dev; mock fallbacks prevent hard crashes.

