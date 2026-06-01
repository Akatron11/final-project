# DECISIONS.md — GymGate Technical Decisions

> SFWE477 — Backend Development & DevOps Fundamentals  
> This document explains the tools I chose for the project and why I chose them.

---

## 1. Why FastAPI?

I decided to use **FastAPI** as my backend framework.

The main reason is that we've been learning FastAPI in class, so I already have some familiarity with it. Starting from scratch with a new framework would waste time. But there are also good technical reasons:

- FastAPI supports `async/await`. In this project, the `/verify` endpoint needs to respond in under 200ms when the gate device sends a request. Async helps me hit that speed target.
- It uses Pydantic for automatic request/response validation. I don't have to manually check if the incoming data is in the right format.
- It auto-generates a `/docs` page (Swagger UI). This is really useful for testing the API — sometimes I don't even need Postman.

I considered Django REST and Flask too, but Django felt like overkill for this project, and Flask has weak async and validation support.

---

## 2. Why PostgreSQL?

I chose **PostgreSQL** as my database.

This project has a lot of relationships between data: a gym has members, members have plans, plans have subscriptions, members have QR/NFC credentials, and there are access logs... Relational (SQL) databases handle these relationships best.

My main reasons for picking PostgreSQL:
- Strong foreign key and JOIN support — I can easily set up relationships between tables
- Every table will have a `gym_id` column. This way, when a gym admin makes a query, they only see their own gym's data (tenant isolation)
- It has native UUID support — easy to generate primary keys with `gen_random_uuid()`
- It's one of the most widely used databases in the industry

I thought about MongoDB but there are too many relationships between the data, so NoSQL isn't a good fit. SQLite would cause problems in a multi-user production environment.

---

## 3. Why SQLAlchemy and Alembic?

Instead of writing raw SQL, I decided to use **SQLAlchemy ORM**. For database migrations, I'll use **Alembic**.

- With SQLAlchemy I can define tables as Python classes — I can do CRUD operations without writing SQL
- SQLAlchemy 2.0 supports async, which is important for working with FastAPI
- With Alembic, when I change the database schema (like adding a new column), I can generate a migration file and run `alembic upgrade head` to update the database. No need to write ALTER TABLE statements manually.

---

## 4. Why Redis?

One of the project requirements is tracking how many members are currently inside the gym (occupancy). I could have used a counter column in PostgreSQL, but I decided to use Redis because:

- Redis runs **in-memory** — it's very fast. The `/verify` endpoint has a 200ms target, so reading from RAM instead of disk makes more sense
- `INCR` and `DECR` commands are **atomic** — even if two people scan at the gate at the same time, the counter stays accurate (no race condition)
- Its key-value structure is perfect for this: `gym:abc123:occupancy → 24` is simple and clean

I'm only storing two things in Redis:
- `gym:{id}:occupancy` → current member count inside the gym
- `rate:{api_key}:{minute}` → rate limiting counter

---

## 5. Authentication: JWT + API Key

There are two types of users in the system, and I decided to use a different auth method for each:

| Who? | How do they authenticate? | Why? |
|------|--------------------------|------|
| **Gym admin** | JWT Token (gets it after login) | Logs in from the web panel, manages members and plans |
| **Gate device** | API Key (sends it in header) | Only calls the `/verify` endpoint, no login concept needed |

For JWT, I'm using the HS256 algorithm with a 1-hour token expiry. I'm not adding refresh tokens for now — I can add them later if needed.

For gate devices, I'll add rate limiting: max 60 requests per minute. This is for both security and preventing abuse.

---

## 6. Why Fernet Encryption?

The QR codes will contain member info (gym_id, member_id, etc.). If this data is stored as plain text in the QR code, it's a security risk — someone could copy the QR and enter as another person. So I'm encrypting the QR payload with **Fernet**.

Why Fernet:
- It's built into Python's `cryptography` library, easy to use
- It's symmetric encryption — I only need one key to encrypt and decrypt
- It's fast — much faster than asymmetric methods like RSA, and I don't need public/private key separation for this project
- Fernet tokens include a timestamp, so I can detect old QR codes

---

## 7. Multi-Tenancy: How I'm Doing It

The project will have multiple gyms, and each gym should only see its own data. This is called "multi-tenancy."

There are three approaches:
1. Separate database per gym (too expensive and complex)
2. Separate schema per gym (migrations become harder)
3. **Single database, filter by `gym_id` in every table** ← I chose this

This is the simplest approach and it's enough for this project's scale. Every table has a `gym_id` column, and every query automatically gets a `WHERE gym_id = ...` filter. This way, one gym admin can't see another gym's data.

---

## 8. Docker and Docker Compose

I'll run the project with 3 services using Docker Compose:

| Service | What for? | Image |
|---------|-----------|-------|
| `api` | FastAPI application | My own Dockerfile |
| `db` | PostgreSQL database | postgres:16-alpine |
| `redis` | Occupancy tracking + cache | redis:7-alpine |

I'm using Docker so that I can just type `docker-compose up` and everything starts. I don't need to install PostgreSQL and Redis separately on my machine. Also, the project requirements include containerization.

---

## 9. CI/CD: GitHub Actions

I'll use GitHub Actions to automatically run tests every time I push code.

The pipeline will have these steps:
1. Code quality check (linting)
2. Run tests (pytest)
3. Deploy to Render when merged to `main` branch

I chose GitHub Actions because the repo is already on GitHub and it's free for public repos.

---

## 10. Deployment: Render.com

I'll deploy the project on **Render.com**.

- It has a free plan
- It supports Docker
- It offers PostgreSQL and Redis as managed services
- It can auto-deploy from GitHub (updates automatically when I push)

---

## 11. Project Folder Structure

```
gymgate-backend/
├── app/
│   ├── main.py              # Main application file
│   ├── config.py            # Settings (.env reading)
│   ├── database.py          # Database connection
│   ├── models/              # Database tables (SQLAlchemy)
│   ├── schemas/             # Request/response schemas (Pydantic)
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   ├── auth/                # JWT and API key stuff
│   └── utils/               # Encryption, QR code generation
├── alembic/                 # Database migration files
├── tests/                   # Tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── DECISIONS.md
└── README.md
```

I chose this structure so that everything has its own folder — for example, all endpoints are under `routers/`, all database models are under `models/`. As the project grows, it's easy to find files.
