# Barrier Control System

Computer-vision powered entry/exit barrier control with license-plate recognition (OCR + YOLO), payments via Stripe, and a containerized API/UI stack.

> **What you can do with this project**
>
> - Detect license plates from video (entry/exit flow)
> - Call the API for registering events & payments
> - Handle Stripe webhooks locally
> - Run everything via Docker Compose
> - Debug with structured service logs
> - Apply and manage Alembic database migrations
> - Use a simple Makefile to automate everyday dev commands

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Running the OCR demo scans](#running-the-ocr-demo-scans)
- [Stripe setup (local webhooks)](#stripe-setup-local-webhooks)
- [Database migrations (Alembic)](#database-migrations-alembic)
- [Using the Makefile](#using-the-makefile)
- [Useful commands (logs, exec, rebuild)](#useful-commands-logs-exec-rebuild)
- [Environment configuration](#environment-configuration)
- [Project structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Architecture

High-level components (service names may differ in your `docker-compose.yml`):

- **api** — REST API built with FastAPI + PostgreSQL, coordinates entry/exit events, pricing, & payment status. Includes Alembic for migrations.
- **ocr** — License-plate recognizer using YOLO + EasyOCR. Can be run in **entry** or **exit** mode and pointed at demo videos.
- **web** — React frontend (Vite-based) for admin dashboards and user subscriptions.
- **db/cache/...** — Datastores or queues (if included).

> The OCR container talks to the API using `API_BASE` (default: `http://api:8000/api`).

---

## Prerequisites

- Docker & Docker Compose v2  
- Stripe CLI (for local webhook forwarding)  
- Git  
- Node.js 18+ (for frontend)  
- (Optional) Python 3.10+ if you want to run the backend locally  

---

## Quick Start

Clone the repository:
```bash
git clone https://github.com/AleksandarMladenov/Internship-Barrier_Control_System.git
cd Internship-Barrier_Control_System
```

Build and start everything:
```bash
cd Implementation/backend/ops
docker compose up -d --build
```

Check services:
```bash
docker compose ps
docker compose logs -f api
```

The API should be available at [http://localhost:8000](http://localhost:8000).

---

## Running the OCR demo scans

The OCR service can be run in **entry** or **exit** mode.  
Make sure the demo videos exist under `Implementation/backend/ops/ocr_assets/`:

- `entry_demo.mp4`
- `exit_demo.mp4`

### Entry scan (demo video)
```bash
docker compose run --rm   -e MODE=entry   -e API_BASE=http://api:8000/api   -e PLATE_REGEX=ANY   -e YOLO_CONF=0.45   -e FRAME_SKIP=1   -e STABLE_FRAMES=3   -e EXIT_AFTER_FIRST=1   -v "$(pwd)/ocr_assets:/assets:ro"   ocr python lp_recognizer.py --video /assets/entry_demo.mp4
```

### Exit scan (demo video)
```bash
docker compose run --rm   -e MODE=exit   -e API_BASE=http://api:8000/api   -e PLATE_REGEX=ANY   -e YOLO_CONF=0.45   -e FRAME_SKIP=1   -e STABLE_FRAMES=3   -e EXIT_AFTER_FIRST=1   -v "$(pwd)/ocr_assets:/assets:ro"   ocr python lp_recognizer.py --video /assets/exit_demo.mp4
```

**Notes**
- `PLATE_REGEX=ANY` accepts any plate; adjust for your format.
- `YOLO_CONF` defines confidence threshold.
- `FRAME_SKIP` and `STABLE_FRAMES` improve stability/performance.
- `EXIT_AFTER_FIRST=1` stops processing after first stable plate.

---

## Stripe setup (local webhooks)

You’ll use the Stripe CLI to connect test events to your API and update payment status in real-time.

### 1. Login
```bash
stripe login
```

### 2. Listen & forward webhooks
```bash
stripe listen --forward-to localhost:8000/api/payments/webhook
```

This prints a secret key like:
```
whsec_1234567890abcdef
```

### 3. Add to `.env`
```
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXX
```

Restart the API:
```bash
docker compose up -d api
```

### 4. Test payment
```bash
stripe trigger payment_intent.succeeded
```

The API webhook will receive the event, verify the signature, and mark the session as **paid**.  
Once paid, the **exit OCR scan** will automatically open the barrier for that vehicle.

---

## Database migrations (Alembic)

The backend uses Alembic for database versioning and schema changes.

### Create a migration
```bash
docker compose exec api alembic revision --autogenerate -m "add new field"
```

### Apply migrations
```bash
docker compose exec api alembic upgrade head
```

### Roll back one revision
```bash
docker compose exec api alembic downgrade -1
```

> ⚙️ Note: Alembic is configured automatically. Run these commands after changing any SQLAlchemy models.

---

## Using the Makefile

A ready-to-use `Makefile` is included to simplify common tasks.

Run from the project root:

```bash
make up           # Start backend + OCR
make logs-api     # Stream backend logs
make migrate-up   # Apply all DB migrations
make scan-entry   # Run demo OCR entry video
make stripe-listen # Forward webhooks to API
make frontend-dev # Start Vite React app
```

### Why use it?
- Eliminates repetitive Docker commands  
- Manages migrations and OCR demos  
- Simplifies Stripe webhook setup  
- Works consistently on all environments  

---

## Useful commands (logs, exec, rebuild)

**View logs**
```bash
docker compose logs -f          # all
docker compose logs -f api      # backend
docker compose logs -f ocr      # OCR
```

**Open a container shell**
```bash
docker compose exec api bash
docker compose exec ocr bash
```

**Rebuild API**
```bash
docker compose build api && docker compose up -d api
```

**Stop services**
```bash
docker compose down
```

**Reset everything (wipe volumes)**
```bash
docker compose down -v
```

---

## Environment configuration

Example `.env` (backend):
```ini
# API
API_PORT=8000
API_BASE=http://api:8000/api

# OCR defaults
PLATE_REGEX=ANY
YOLO_CONF=0.45
FRAME_SKIP=1
STABLE_FRAMES=3
EXIT_AFTER_FIRST=1

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=barrier
POSTGRES_USER=barrier
POSTGRES_PASSWORD=barrier

# Frontend
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Frontend (`Implementation/frontend/.env.local`):
```ini
VITE_API_BASE=http://localhost:8000/api
```

> ⚠️ Keep secrets (Stripe keys, DB passwords) out of Git. Use `.env` or your CI/CD vault.

---

## Project structure

```
.
├── Implementation/
│   ├── backend/
│   │   ├── app/
│   │   │   └── src/
│   │   │       ├── api/ (FastAPI routes)
│   │   │       ├── services/ (business logic)
│   │   │       ├── models/, schemas/, repositories/
│   │   │       ├── core/ (settings, security)
│   │   │       └── migrations/ (Alembic)
│   │   └── ops/
│   │       ├── docker-compose.yml
│   │       ├── Dockerfile.api / Dockerfile.ocr
│   │       ├── lp_recognizer.py
│   │       └── ocr_assets/
│   └── frontend/
│       └── src/
│           ├── api/, components/, pages/
│           ├── layouts/, router/
│           └── main.jsx (Vite entry)
└── README.md
```

---

## Troubleshooting

**OCR container can’t reach the API**
- Ensure API is running: `docker compose ps`
- Check network base URL: `API_BASE=http://api:8000/api`

**Stripe webhook fails**
- Verify `STRIPE_WEBHOOK_SECRET` matches your active `stripe listen`
- Restart the API

**YOLO detects nothing**
- Lower `YOLO_CONF`
- Remove `EXIT_AFTER_FIRST=1`
- Increase `STABLE_FRAMES`

**DB schema mismatch**
- Run `make migrate-up`

**Frontend 404 / API blocked**
- Start frontend: `make frontend-dev`
- Add CORS origin in `.env`

---

## License

MIT License — free to use, modify, and extend.

---

## Maintainers

- @AleksandarMladenov

---

## Appendix: One-liners

**Run everything + Stripe + entry scan**

**Terminal A (services)**
```bash
make up
```

**Terminal B (webhooks)**
```bash
make stripe-listen
```

**Terminal C (entry scan)**
```bash
make scan-entry
```

Once the payment webhook succeeds, the backend updates the session, the OCR detects the paid license plate, and the system opens the barrier automatically.
