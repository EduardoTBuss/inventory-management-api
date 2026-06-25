# Inventory Management System

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT%20%2B%20bcrypt-000000?logo=jsonwebtokens&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

A full-stack, **multi-tenant** inventory management system. A FastAPI + SQLAlchemy 2.0
backend exposes a JWT-authenticated REST API; a dependency-free HTML/Tailwind/Alpine.js
frontend is served by the same FastAPI process. SQLite is used for development — switching
to PostgreSQL only requires changing the connection URL.

The interesting part is **not** the CRUD. It is the **stock-control design**: quantities
are never stored as a mutable counter — they are *derived from an append-only ledger of
movements*, and every change is serialized with a **pessimistic row lock**. See
[Design decision](#design-decision-event-sourcing-lite).

---

## Table of contents

1. [Features](#features)
2. [Design decision: event-sourcing-lite](#design-decision-event-sourcing-lite)
3. [Tech stack](#tech-stack)
4. [Project layout](#project-layout)
5. [Running locally](#running-locally)
6. [Demo login (seed)](#demo-login-seed)
7. [API overview](#api-overview)
8. [Security notes](#security-notes)

---

## Features

- **Products, categories and suppliers** — full CRUD, SKU uniqueness per tenant, low-stock thresholds.
- **Stock movements** — `entrada` (in), `saida` (out), `ajuste` (adjustment), each with a reason and audit trail.
- **Derived stock** — a product's quantity is computed from its movement ledger, not set by hand.
- **Multi-tenant** — a single server hosts several isolated inventories; one tenant never sees another's data.
- **Roles** — *super-admin* (manages tenants), *admin* (manages a tenant), *operator* (registers movements).
- **JWT auth** with bcrypt-hashed passwords and a basic in-memory login rate limiter.
- **Dashboard** — totals, stock value, low-stock alerts and recent activity.
- **Self-contained frontend** — no build step; served as static files by FastAPI.

---

## Design decision: event-sourcing-lite

Most tutorial inventory systems keep a single mutable column, `product.quantity`, and do
`quantity += n` on every operation. That is simple but loses history, is impossible to audit,
and corrupts silently under concurrent writes (lost updates → overselling).

This project takes a different route, **event-sourcing-lite**:

> **A product's quantity is a *derived value*, reconstructed from an append-only ledger of
> stock movements — never written directly by the application.**

### The invariant

For every product:

```
product.quantidade == SUM(delta over its movements)

where delta = +quantity  for "entrada" / "ajuste"
              -quantity  for "saida"
```

`product.quantidade` is kept as a **materialized cache** of this sum (so reads are O(1)), but
it is only ever mutated *together with* the insertion of the corresponding movement row, inside
one transaction. The seed script audits the invariant across all products and **fails loudly**
if any product's cached quantity diverges from the sum of its ledger
(`seed.py → _verify_invariant`).

### Why "lite"

It is not full event sourcing — there is no event replay engine and no separate event store;
the canonical state lives in normal relational tables. But it keeps event sourcing's two most
valuable properties: a **complete, immutable audit log** of every stock change (who, what, when,
why) and a state that is **always reconstructable** from that log. This is the right trade-off
for a single-service inventory system that still needs to be auditable.

### Concurrency: pessimistic locking

The risky operation is registering a movement: read current quantity → validate → write new
quantity. Run two of those at once on the same product and a naive implementation loses one
update. The movement service serializes them with a **pessimistic lock**:

```python
# app/services/movimentacao_service.py
produto = db.execute(
    select(Produto)
    .where(Produto.id == dados.produto_id, Produto.sistema_id == sistema_id)
    .with_for_update()          # ← lock the product row for the transaction
).scalar_one_or_none()

# validate (reject a 'saida' that would make stock negative), then:
produto.quantidade += delta     # update materialized cache
db.add(Movimentacao(...))       # append to the immutable ledger
db.commit()                     # both, atomically — or neither
```

`with_for_update()` (`SELECT ... FOR UPDATE`) holds a row-level lock until commit, so
concurrent movements on the same product are processed strictly one at a time. A `saida` that
would drive stock negative is rejected with HTTP `422` **before** anything is written. The whole
sequence is one transaction — it either commits the cache update *and* the ledger row together,
or rolls both back.

> SQLite serializes writers at the database level, so `FOR UPDATE` is effectively a no-op there;
> the code is written so that on PostgreSQL/MySQL the same logic gives true per-row pessimistic
> locking with no changes.

---

## Tech stack

| Layer        | Technology                                                        |
|--------------|-------------------------------------------------------------------|
| Backend      | FastAPI 0.115, Uvicorn                                             |
| ORM / DB     | SQLAlchemy 2.0 (typed), Alembic migrations, SQLite (dev)          |
| Validation   | Pydantic v2                                                       |
| Auth         | JWT (python-jose), bcrypt password hashing (passlib)              |
| Frontend     | HTML, Tailwind CSS (CDN), Alpine.js (CDN), vanilla JS             |

---

## Project layout

```
gestao-estoque/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, routers, static frontend mount
│   │   ├── database.py          # engine, session, Base, get_db dependency
│   │   ├── auth/                # JWT creation/decoding, auth dependencies
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── routes/              # API endpoints (one module per resource)
│   │   └── services/            # business logic (movement ledger lives here)
│   ├── alembic/                 # database migrations
│   ├── seed.py                  # demo data + audit-invariant check
│   └── requirements.txt
└── frontend/                    # static HTML/CSS/JS, served by FastAPI at /
```

---

## Running locally

**Prerequisites:** Python 3.11+.

```bash
# 1. Clone
git clone https://github.com/EduardoTBuss/gestao-estoque.git
cd gestao-estoque/backend

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed the database with demo data (creates backend/estoque.db)
python seed.py

# 5. Run the server
uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:8000** in your browser. FastAPI serves both the API (under
`/api`) and the frontend, so no separate frontend server is needed. Interactive API docs are
available at **http://localhost:8000/docs**.

Optionally set a real JWT secret instead of the dev fallback:

```bash
export JWT_SECRET_KEY="a-long-random-string"     # PowerShell: $env:JWT_SECRET_KEY="..."
```

---

## Demo login (seed)

Login is multi-tenant — the form has three fields: **system code**, **username** and **password**.

| Role        | System code  | Username     | Password   |
|-------------|--------------|--------------|------------|
| Admin       | `principal`  | `admin`      | `admin123` |
| Operator    | `principal`  | `op`         | `op123`    |
| Super-admin | *(blank)*    | `superadmin` | `super123` |

> These are demonstration seed credentials for a local database only — there are no real
> secrets in this repository.

---

## API overview

All endpoints are under `/api`. Every request except `POST /api/auth/login` requires an
`Authorization: Bearer <token>` header, and operations are scoped to the authenticated user's tenant.

| Method | Path                       | Description                              |
|--------|----------------------------|------------------------------------------|
| POST   | `/api/auth/login`          | Authenticate, returns a JWT              |
| GET    | `/api/auth/me`             | Current user profile                     |
| GET    | `/api/produtos`            | List products (paginated, searchable)    |
| POST   | `/api/produtos`            | Create a product                         |
| POST   | `/api/movimentacoes`       | Register a stock movement (locked)       |
| GET    | `/api/movimentacoes`       | List movements (paginated, filterable)   |
| GET    | `/api/categorias`          | List categories                          |
| GET    | `/api/fornecedores`        | List suppliers                           |
| GET    | `/api/dashboard`           | Aggregated metrics                       |
| GET    | `/api/sistemas`            | Manage tenants (super-admin only)        |

See the full, always-up-to-date contract at `/docs` (Swagger UI).

---

## Security notes

- Passwords are hashed with **bcrypt**; plaintext is never stored.
- The JWT secret is read from `JWT_SECRET_KEY`; a clearly-labelled dev fallback is used only
  when it is unset.
- Login responses are deliberately vague ("invalid code, user or password") to avoid user/tenant
  enumeration, and an in-memory per-IP rate limiter throttles brute-force attempts.
- All data access is scoped by `sistema_id` (tenant) at the query level, enforcing isolation
  between tenants.

---

## License

[MIT](LICENSE) © 2025 Eduardo Timm Buss
