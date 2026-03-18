# Sector Relay

Sector Relay is an async browser tycoon MVP built as a monorepo. Players run autonomous sci-fi trade hubs, return for short decision windows, and influence one another through a shared market, player contracts, sector events, and soft co-op transfers.

## Architecture Overview

- Backend: FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, Argon2id password hashing, JWT access tokens plus rotating refresh cookie, DB-backed brute-force protection, server-authoritative world tick.
- Simulation: station processing is calculated from `station.last_processed_at` with bounded offline progress; the world tick updates stations, market prices, contracts, and events every `WORLD_TICK_SECONDS`.
- Content system: baseline game definitions live in code under `app/game/default_definitions.py`, admin-created and admin-overridden revisions live in the database, and runtime services read the merged effective definitions layer from `app/services/admin_definitions.py`.
- Frontend: React, Vite, Tailwind CSS, Zustand auth store, TanStack Query for server state, mobile-first control-panel UI with bottom navigation.
- Infra: Dockerfiles for backend and frontend, `docker-compose.yml` for local and VPS-style deployment, Postgres as primary DB, Redis optional.

## Project Tree

```text
.
├── app
│   ├── alembic
│   ├── api
│   ├── core
│   ├── db
│   ├── game
│   ├── models
│   ├── schemas
│   ├── security
│   ├── services
│   ├── tasks
│   ├── tests
│   └── main.py
├── docker
├── frontend
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Local Run

1. Copy `.env.example` to `.env`.
2. Start Postgres: `docker compose up -d postgres`.
3. Install backend deps: `pip install -e .[dev,postgres]`.
4. Run migrations: `alembic upgrade head`.
5. Optional seed: `python -m app.tasks.seed`.
6. Start backend: `python -m app.main`.
7. In another terminal: `cd frontend && npm install && npm run dev`.
8. Open `http://localhost:5173`.

Default local backend port: `8001`.

Seeded demo users:

- `captain_one` / `Captain123`
- `captain_two` / `Captain123`

## Admin / Designer Console

The project now includes a protected in-app admin section at `http://localhost:5173/admin`.

Core ideas:

- baseline definitions ship with the codebase
- admin changes are stored as revisions in the database
- published revisions are merged into effective definitions without restarting the server
- runtime services use the effective definitions layer for modules, resources, events, contracts, specializations, and balance numbers

Built-in roles:

- `super_admin`: full access, role assignment, dangerous actions
- `admin`: publish content and balance, read audit
- `designer`: create and edit content, save drafts, publish balance and content
- `moderator`: read-only admin access and audit visibility

What the admin UI supports today:

- dashboard with recent content, balance, and audit entries
- content list with filters by type, status, and search
- editor flow for resources, modules, events, contract templates, meta upgrades, and specializations
- draft save, publish, disable, archive, duplicate, revision history, diff, rollback
- balance editor with live publish and revision rollback
- role management page for `super_admin`
- audit log page

## Admin Bootstrap

Create the first super admin from CLI:

```powershell
python -m app.tasks.create_admin --email admin@example.com --username admin --password ChangeMe123
```

Or bootstrap one via `.env` before startup:

```env
BOOTSTRAP_ADMIN_EMAIL=admin@example.com
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=ChangeMe123
```

Then log in through the normal auth screen and open `/admin`.

## Live Publish Flow

1. Create or edit a content item in `/admin/content`.
2. Save a draft revision.
3. Publish the revision.
4. The backend invalidates the in-memory effective definitions cache.
5. New ticks, market refreshes, contract generation, and station processing immediately use the updated values.

Rollback works the same way:

1. Open revision history for the item or balance parameter.
2. Roll back to a previous version.
3. A new revision is created and published.
4. The live effective definitions cache is invalidated again.

## Quick Docker Preview

```bash
docker compose up --build
```

Frontend will be on `http://localhost:8080`, backend on `http://localhost:8001`.

## Useful Commands

- `python -m app.main`
- `python -m app.tasks.seed`
- `python -m app.tasks.create_admin --email admin@example.com --username admin --password ChangeMe123`
- `alembic upgrade head`
- `pytest`
- `make lint`
- `make frontend`
- `.\dev.cmd`
- `.\dev.ps1`

## One-Command Local Dev On Windows

From the repository root:

```powershell
.\dev.cmd
```

Or:

```powershell
.\dev.ps1
```

What it does:

- starts FastAPI backend in a background PowerShell job
- starts Vite frontend in the current terminal
- stops backend automatically when you exit the frontend process
- if `npm` is missing from `PATH`, it also tries `D:\programms\Node\npm.cmd` and `C:\Program Files\nodejs\npm.cmd`

## Gameplay Systems Included

- Registration, login, logout, refresh, change password
- 1 station per account
- 8 modules with upgrade costs and effects
- Shared market with drifting sector prices and history
- NPC contracts and player-created contracts
- Transfers between players
- 15 persistent meta upgrades
- 20 contract templates
- 20 world event templates
- Sector snapshot, event feed, notifications, reports, bottleneck indicators

## Security Notes

- Password hashing: Argon2id via `argon2-cffi`
- Access auth: bearer access token
- Refresh auth: rotating `HttpOnly` cookie
- Login/register brute-force control: DB-backed attempt tracking by IP and identity with escalating lock windows
- Generic invalid-credential response on login
- Server-authoritative simulation and market pricing

## VPS Deploy Path

1. Provision a small VPS with Docker and Docker Compose.
2. Copy the repository and create `.env` with production values.
3. Point `DATABASE_URL` to the Compose Postgres service or external Postgres.
4. Build and launch: `docker compose up -d --build`.
5. Run migrations inside backend container: `docker compose exec backend alembic upgrade head`.
6. Put Caddy or Nginx in front if you want HTTPS and a custom domain.
7. Replace `FRONTEND_ORIGIN` and enable `COOKIE_SECURE=true`.

## Backup and Maintenance

- Backup DB: `docker compose exec postgres pg_dump -U sectorrelay sectorrelay > backup.sql`
- Restore DB: `docker compose exec -T postgres psql -U sectorrelay sectorrelay < backup.sql`
- Force a dev tick: `POST /admin/dev/tick`
- Force a dev event: `POST /admin/dev/event`

## What Is Ready

- End-to-end MVP structure
- Working backend API surface
- Server-side station simulation
- Mobile-first frontend dashboard and flows
- Admin/designer console with RBAC, revisions, audit, rollback, and live content publish
- Migrations, seeds, tests, Docker, and README

## Good Next Improvements

- Add richer form editors per content type instead of the current JSON-assisted editor for advanced fields
- Add warning-level semantic validation for destructive balance changes before publish
- Add effective config snapshots and Redis-backed cache invalidation for multi-process deploys
- Expand research queue into timed unlocks instead of immediate purchases
- Add alliance and sector megaproject systems
