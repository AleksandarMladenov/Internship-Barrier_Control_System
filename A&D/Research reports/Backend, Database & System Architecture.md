Research Report: Backend, Database & System Architecture for a Smart Barrier Control System
1. Context and Objectives

This project aims to design and implement the backend of a Parking Barrier Control System that must reliably decide whether to open, deny, or charge for entry based on license plate recognition and subscription status. Beyond this critical control path, the system must support online subscriptions and payments, and provide operator dashboards with near real-time visibility.

The solution should be reproducible for development and deployment, secure in how it handles credentials and roles, extensible as new features emerge, and cloud-ready to run on common hosting platforms.

The resulting architecture needs to balance three sometimes competing priorities:

Robust, auditable decisions at the barrier with low latency;

Modern, responsive operator UX; and

Straightforward integration with third-party payment providers.

2. Candidate Technology Stack
Application Layer

FastAPI (Python) was selected as the primary framework due to its asynchronous I/O support, first-class request/response validation through Pydantic, and an ecosystem well-suited to building APIs rapidly without sacrificing structure.

Alternative frameworks considered included Flask (Python) and Express/Nest (Node.js/TypeScript). Flask’s minimalism is attractive for prototypes but requires more manual scaffolding as complexity grows; Node.js options, while strong, would add language/runtime heterogeneity without clear advantage for this domain.

Persistence Layer

PostgreSQL was chosen for its ACID guarantees, mature query planner, partial indexes, and strong support for analytical SQL (CTEs, window functions). SQLAlchemy provides a flexible ORM layer, while Alembic manages schema evolution with versioned migrations—an essential capability for a system that will iterate on data models (sessions, payments, subscriptions) over time.

Deployment

To ensure reproducibility and dev/prod parity, the system is containerized with Docker and orchestrated with Docker Compose in development. This allows one-command startup of the API and database, clean environment separation, and straightforward deployment paths to containers-on-cloud in later stages.

3. Architectural Alternatives
3.1 Postgres-Only (Relational Core)

In the Postgres-only approach, all data—vehicles, sessions, subscriptions, payments, blacklists—resides in a single relational database. The API (FastAPI) exposes endpoints for cameras, operator tools, and dashboards, and every read/write is served from this single store.

Strengths:

Transactional integrity and strong consistency.

Auditable state changes are straightforward.

Complex analytical queries are easily expressed in SQL.

Schema evolution is controlled with Alembic.

Trade-offs:

Realtime dashboards require additional mechanisms (polling, SSE, or WebSockets).

Integration with payments demands careful webhook and idempotency handling.

Summary:
Postgres-only maximizes correctness and auditability but leaves realtime dashboards and “native” payments UX as additional engineering work.

3.2 Firebase-Only (Realtime NoSQL)

A Firebase-only design relies on Firebase Authentication, Firestore/Realtime Database, Cloud Functions, and Hosting for the entire system. Payments (Stripe/PayPal) integrate via Cloud Functions that directly update Firestore, and dashboards achieve realtime behavior out of the box.

Strengths:

Realtime updates natively supported.

Built-in authentication and hosting simplify development.

Excellent developer velocity and user experience for dashboards.

Trade-offs:

Eventual consistency and limited transactional integrity.

No migration system comparable to Alembic.

Denormalization complicates data correctness.

High-frequency operations can become costly.

Summary:
Firebase-only excels at realtime dashboards but is poorly matched to low-latency, strongly consistent gate decisions.

3.3 Hybrid (Relational Core + Event-Driven Firebase)

The Hybrid design purposefully splits responsibilities:

Relational Core (PostgreSQL + FastAPI + SQLAlchemy/Alembic):
Acts as the system of record for all critical entities and decisions (vehicles, sessions, subscriptions, payments, blacklists, audit logs). The control path—license plate recognition and resulting decisions—runs exclusively against this core.

Event-Driven Firebase Periphery (Auth, Dashboards, Payments Relay):
Firebase Authentication manages operator logins; dashboards consume a denormalized read-model mirrored from the backend to Firestore, enabling realtime UI. Payment webhooks are normalized by Firebase Functions and relayed securely to the FastAPI backend.

Summary:
The Hybrid model combines strong relational guarantees and realtime dashboards, but introduces more moving parts.

4. Comparative Evaluation

| **Criteria**                        | **Postgres-Only**                 | **Firebase-Only**             | **Hybrid (Chosen)**                      |
|-------------------------------------| --------------------------------- | ----------------------------- | ---------------------------------------- |
| **Barrier reliability & integrity** | High (ACID, transactions)         | Medium (eventual consistency) | High (decisions on Postgres)             |
| **Decision latency**                | Predictable, <150 ms with indexes | Variable, modeling overhead   | Predictable, <150 ms (Postgres + cache)  |
| **Payments integration**            | Possible, custom relay            | Native via Functions          | Functions normalize → upsert in Postgres |
| **Realtime dashboards**             | Extra infra (WS/SSE/polling)      | Native (Firestore)            | Native via mirrored read-model           |
| **Schema evolution**                | Alembic migrations                | No native migrations          | Alembic core, Firebase read-model        |
| **Analytics & reporting**           | Full SQL                          | BigQuery export               | Full SQL + Firebase UI                   |
| **Operational complexity**          | Low                               | Low–Medium                    | Medium (two systems)                     |


Summary:
Postgres-only and Hybrid deliver strong reliability and consistency. The Hybrid solution enhances realtime UX but adds integration complexity.

5. Final Architecture

For the MVP, a PostgreSQL-only layered architecture is adopted. This keeps the system simple while still meeting all functional requirements.

Core Components:

Authoritative Layer: PostgreSQL with SQLAlchemy and Alembic. All entities (vehicles, sessions, subscriptions, payments, blacklist, and audit logs) live here.

FastAPI Application: Layered structure (Routers → Services → Repositories). Provides clear separation of concerns and maintainability.

Payments Integration: Stripe/PayPal webhooks connect directly to FastAPI, verified and stored transactionally in Postgres with idempotent upserts.

Realtime Dashboards: Implemented using SSE or WebSockets. The API emits events post-commit for operator dashboards.

Security & Roles: Managed within Postgres; enforced at the API level with RBAC.

Resilience: Barrier decisions depend only on API + Postgres. Fail-safe behavior and nightly reconciliation jobs ensure reliability.

6. Conclusion and Rationale

The research compared three options: Postgres-only, Firebase-only, and a Hybrid architecture.

While the Hybrid model promises excellent realtime dashboards, it introduces additional complexity. For the MVP, reliability, simplicity, and maintainability are prioritized. A PostgreSQL-only layered architecture with FastAPI fulfills all functional needs while maintaining low latency and robust data integrity.

This choice ensures:

Reliable and auditable barrier decisions.

Easy schema evolution through Alembic.

Smooth payment integration with idempotent handling.

Realtime dashboards using SSE/WebSockets without overloading the core.

In conclusion, the MVP will ship with a FastAPI + PostgreSQL backend architecture. It is robust, maintainable, and ready for future extensions, including Firebase integration for enhanced realtime dashboards if needed.