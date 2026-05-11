# Muscle Mania — Gym API (FastAPI)

The backend for the Muscle Mania gym management system. FastAPI + SQLAlchemy + PostgreSQL/SQLite + JWT.

> Built as a deployment-learning project. Pairs with [`gym-client`](../gym-client).

## Tech stack

- **FastAPI** — REST API
- **SQLAlchemy 2.0** — ORM
- **PostgreSQL** (production) / **SQLite** (zero-config local dev)
- **Pydantic v2** — request/response validation
- **python-jose** + **bcrypt** — JWT auth + password hashing

## Local setup

### 1. Prerequisites
- Python 3.11+ (3.13 tested)

### 2. Install
```bash
cd gym-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env if you want to use Postgres. Default = SQLite in ./gym.db.
```

### 4. Seed sample data
```bash
python -m app.seed
```

This creates:
- 3 packages (Basic / Pro / Elite)
- 1 admin: `admin@musclemania.com` / `admin123`
- 3 sample customers: `alex@example.com`, `priya@example.com`, `ryan@example.com` (passwords are first-name + 123)
- Workouts, vitals, attendance, fees, achievements, classes

### 5. Run
```bash
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Project layout

```
app/
├── main.py             # FastAPI entrypoint (CORS, routers, table creation)
├── config.py           # Settings via pydantic-settings (.env)
├── database.py         # SQLAlchemy engine + session
├── models.py           # All ORM models
├── schemas.py          # Pydantic schemas
├── auth.py             # JWT encode/decode + bcrypt
├── deps.py             # FastAPI deps (current user, role gates)
├── seed.py             # Seed script
├── chatbot_data.py     # Canned chatbot replies (no real AI)
└── routers/
    ├── auth.py         # /api/auth/*
    ├── public.py       # /api/public/* (packages, classes, enquiries)
    ├── customer.py     # /api/me/* (profile, vitals, workouts, attendance, fees, achievements, notifications)
    ├── admin.py        # /api/admin/* (members, fees, broadcast, analytics, enquiries)
    └── chatbot.py      # /api/chatbot/* (streaming)
```

## Key endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register` | Create customer account, returns JWT |
| POST | `/api/auth/login-json` | Email + password login (JSON) |
| POST | `/api/auth/login` | Email + password login (form, used by `/docs`) |
| GET | `/api/auth/me` | Current user |
| GET | `/api/public/packages` | List membership packages |
| POST | `/api/public/enquiries` | Submit a contact enquiry |
| GET | `/api/me/stats` | Personal stats: streak, workouts, latest vitals |
| POST | `/api/me/attendance/check-in` | Mark today's attendance |
| GET/POST | `/api/me/workouts` | List/log workouts |
| GET/POST | `/api/me/vitals` | List/log vitals (auto-computes BMI) |
| POST | `/api/chatbot/stream` | Streaming gym coach chatbot |
| GET | `/api/admin/analytics` | Admin dashboard analytics |
| GET | `/api/admin/members` | List members |
| POST | `/api/admin/fees` | Create a fee for a member |

See `http://localhost:8000/docs` for the full interactive list.

## Database

By default, uses SQLite (`gym.db`). To switch to PostgreSQL, set `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Tables auto-create on app start (no migrations). For production hardening, add Alembic.

## Auth model

- Customer registers via `/api/auth/register` → automatically gets `role=customer` and a `MemberProfile` row.
- Admin accounts are created **only via the seed script** (or directly in the DB). There is no public admin signup.
- JWT (HS256) is signed with `SECRET_KEY` and stored client-side in `localStorage`.
- Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 7 days).

## Deployment

See [`DEPLOYMENT.md`](../gym-client/DEPLOYMENT.md) for step-by-step Render + Neon guide.
