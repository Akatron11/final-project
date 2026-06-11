# GymGate — Gym Access & Member Management API

Backend API for a smart gym access control and member management system. Gate devices scan QR codes or NFC tags and receive a grant/deny decision in under 200ms.

**Live API:** https://final-project-w7ms.onrender.com/docs

## Tech Stack

- **FastAPI** — async REST API
- **PostgreSQL** — relational data, tenant isolation via `gym_id`
- **Redis** — real-time occupancy counter + rate limiting
- **Docker Compose** — single-command deployment
- **GitHub Actions** — CI on every push to `main`

## Quick Start

```bash
# 1. Copy environment file and fill in your keys
cp .env.example .env

# Generate FERNET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Start all services
docker-compose up --build

# API is now running at http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | — | Register gym + admin |
| POST | `/api/v1/auth/login` | — | Admin login, returns JWT |
| GET | `/api/v1/gyms/me` | JWT | Get own gym info |
| PUT | `/api/v1/gyms/me` | JWT | Update gym info |
| GET | `/api/v1/members` | JWT | List members (pagination + search) |
| POST | `/api/v1/members` | JWT | Create member |
| GET | `/api/v1/members/{id}` | JWT | Get member |
| PUT | `/api/v1/members/{id}` | JWT | Update member |
| DELETE | `/api/v1/members/{id}` | JWT | Deactivate member |
| POST | `/api/v1/members/{id}/flag` | JWT | Flag member |
| DELETE | `/api/v1/members/{id}/flag` | JWT | Remove flag |
| GET | `/api/v1/plans` | JWT | List plans |
| POST | `/api/v1/plans` | JWT | Create plan |
| PUT | `/api/v1/plans/{id}` | JWT | Update plan |
| DELETE | `/api/v1/plans/{id}` | JWT | Deactivate plan |
| POST | `/api/v1/members/{id}/subscriptions` | JWT | Assign plan to member |
| GET | `/api/v1/members/{id}/subscriptions` | JWT | Subscription history |
| PUT | `/api/v1/subscriptions/{id}/freeze` | JWT | Freeze subscription |
| PUT | `/api/v1/subscriptions/{id}/unfreeze` | JWT | Unfreeze subscription |
| PUT | `/api/v1/subscriptions/{id}/cancel` | JWT | Cancel subscription |
| POST | `/api/v1/members/{id}/credentials/qr` | JWT | Generate QR code |
| POST | `/api/v1/members/{id}/credentials/nfc` | JWT | Assign NFC tag |
| GET | `/api/v1/members/{id}/credentials` | JWT | List credentials |
| DELETE | `/api/v1/credentials/{id}` | JWT | Revoke credential |
| GET | `/api/v1/devices` | JWT | List gate devices |
| POST | `/api/v1/devices` | JWT | Register gate device |
| DELETE | `/api/v1/devices/{id}` | JWT | Deactivate device |
| **POST** | **`/api/v1/verify`** | **API Key** | **Entry verification** |
| GET | `/api/v1/access-logs` | JWT | Access log (filterable) |
| GET | `/api/v1/occupancy` | JWT | Real-time occupancy |
| GET | `/api/v1/dashboard` | JWT | Dashboard summary |

## Verification Endpoint

The core of the system. Gate devices authenticate via `X-API-Key` header and POST to `/api/v1/verify`.

**Request:**
```json
{
  "credential_type": "qr",
  "credential_value": "<encrypted_qr_payload>",
  "gate_id": "GATE-A",
  "action": "entry"
}
```

**Response (GRANTED):**
```json
{
  "decision": "GRANTED",
  "member": {
    "id": "...",
    "name": "Ahmed Al-Rashidi",
    "membership_tier": "Premium",
    "photo_url": "https://...",
    "visits_this_month": 14
  },
  "gym_id": "...",
  "gate_id": "GATE-A",
  "credential_type": "qr",
  "gym_occupancy": { "current": 24, "max": 80 },
  "scanned_at": "2026-05-08T09:14:32Z"
}
```

**Possible decisions:** `GRANTED` · `DENIED_EXPIRED` · `DENIED_SUSPENDED` · `DENIED_FROZEN` · `DENIED_UNKNOWN` · `DENIED_FLAGGED`

**Rate limit:** 60 requests/minute per gate device.

## Performance

| Endpoint | Response Time |
|----------|------------------|
| `POST /verify` | ~215ms (p50) · ~255ms (p99) |

> Measured with `docker-compose up` on localhost (Windows + Docker Desktop), 60 sequential
> requests against an NFC credential with an active subscription. The brief's <200ms target
> assumes a Linux deployment (e.g. Render) without the Docker Desktop networking overhead
> seen on Windows.

## Authentication

- **Gym admins** → JWT Bearer token (login via `POST /auth/login`, 1-hour expiry)
- **Gate devices** → API Key in `X-API-Key` header (generated once at device creation)

## Multi-Tenancy

Every table has a `gym_id` column. All queries are automatically scoped to the authenticated admin's gym. QR payloads are Fernet-encrypted and contain the `gym_id` — a QR issued by Gym A is rejected at Gym B at the decryption/tenant-check step.

## Frontend (Demo)

A simple HTML/CSS/JS admin panel lives in `frontend/` and talks directly to the
live Render API (CORS is open). It covers:

- Registering a new gym + admin (`POST /auth/register`) and admin login (JWT
  stored in `localStorage`), with a logout button
- Member registration (with input validation)
- Plan creation & assigning a plan/subscription to a member, viewing subscription status
- QR code generation for a member
- **Gate/turnstile simulator** — scans a member's QR code via the device camera
  (using [html5-qrcode](https://github.com/mebjas/html5-qrcode)) and calls
  `POST /verify` with a demo gate device API key, showing the GRANTED/DENIED result
- Access log table and a real-time occupancy counter (polled every 5s)

If the stored JWT expires (1-hour expiry), the admin requests automatically log
the user out and return to the login screen with a "Session expired" message.

**Running it:** the QR scanner needs camera access, which browsers only allow on
`https://` or `localhost`. Serve the folder locally instead of opening the file directly:

```bash
cd frontend
python -m http.server 5500
# open http://localhost:5500/index.html
```

> Note: `GATE_API_KEY` in `frontend/script.js` is a demo gate device API key
> created for this project's demo gym, used only for the gate simulator. It is
> not a secret credential for the deployed system as a whole.

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

## Deployment (Render.com)

1. Create a **PostgreSQL** managed database on Render
2. Create a **Redis** managed instance on Render
3. Create a **Web Service** pointing to this repo, Docker runtime
4. Set environment variables (`DATABASE_URL`, `REDIS_URL`, `FERNET_KEY`, `SECRET_KEY`)
5. Render auto-deploys on push to `main`

For GitHub Actions to run CI with secrets, add `FERNET_KEY` and `SECRET_KEY` to your repository's **Settings → Secrets and variables → Actions**.
