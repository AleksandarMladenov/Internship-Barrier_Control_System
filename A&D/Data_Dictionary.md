Self-Service Parking — Analysis Document (Markdown)
Data Dictionary

Vehicle / Car — Physical object arriving at the lane; identified by License Plate; starts/ends a Session at entry/exit.

License Plate — Alphanumeric ID read by the camera; used to match Whitelist/Blacklist and link Sessions/Payments.

Camera (LPR camera) — Captures the plate at entry/exit; emits a Recognition Event (plate, timestamp, lane, read quality).

Recognition Event — Immutable record from the camera; may auto-trigger a Barrier Command or (if low read quality) require confirmation in the self-service UI.

Barrier (Gate) — Physical arm controlled via relay (e.g., Raspberry Pi GPIO) to Open/Deny on decision.

Lane / Gate — Physical entry/exit point associated to one camera and one barrier relay.

Session — Parking transaction for a vehicle:
{ plate, lane, start_time, end_time, duration, pricing_applied, fee, payment_status }
Opened on entry; closed on exit.

Pricing Rule — Configuration describing how to compute a fee from a session (e.g., hourly rate, blocks, grace minutes, rounding).

Payment — Settlement record {amount, method(card-test), time, reference} linked to a session. Card via Stripe (test mode).

Payment Status — unpaid | paid | failed | waived; tied to session close/exit logic.

Whitelist Entry — Authorized plate (e.g., subscriber/tenant) with optional label/expiry; may auto-open and waive/discount fees per policy.

Blacklist Entry — Blocked plate; denies access and logs an event.

Dashboard (Admin) — Server-hosted UI for admins: live occupancy, events, lists, pricing, payments overview, and configuration.

Occupancy — Computed count of vehicles currently inside (number of open sessions).

Self-Service UI (Driver App/Web) — Server-hosted UI the Driver uses to look up their plate, view fees, and pay (card test). Also shows receipts and QR/exit token if needed.

Admin — Staff with elevated privileges (pricing, lists, users/roles, audits, reports).

Driver / Customer — Person paying and passing through the barrier; interacts with the self-service UI.

User Groups (no operator)
Driver (self-service)

Look up their plate/session in the Self-Service UI.

See current fee and accepted methods.

Pay by card (Stripe test mode) and receive confirmation/receipt.

Proceed to exit; system detects a paid session and opens the barrier automatically.

Admin

Configure Pricing Rules (rates, grace, rounding) and lane settings (minimum read quality for auto-open).

Manage Whitelist/Blacklist (CRUD, optional import).

Manage Users/Roles (admin accounts only).

Review Audit Logs and run basic Reports (revenue by period, occupancy by hour).

Functionality & Constraints (incl. design options)
Core Functionality

Entry: Camera recognizes plate → create Session →
– if whitelisted, auto-open & (optionally) mark fee waived/discounted;
– if blacklisted, deny and log.

Payment: Driver opens Self-Service UI → enters plate (or scans lane QR) → sees computed fee → pays via Stripe (test) → session marked paid.

Exit: Camera recognizes plate → finds paid session → barrier opens; if unpaid, lane signage instructs driver to pay via the UI.

Constraints & Policies

Accountless driver flow (no login); session lookup by license plate (optionally last 4 digits + CAPTCHA to deter abuse).

Low read quality at entry/exit: treat as uncertain → prompt driver in the UI to confirm/correct plate; define a retention policy for unpaid/abandoned sessions.

Security: Admin accounts required for dashboard; role-based access; payments only via a PCI-compliant provider (Stripe test in MVP).

Sessions, Pricing, Payments

Entry opens a Session; Exit closes it and computes fee via the Pricing Rule.

Payments: Card (Stripe test mode) via the payment UI; system stores transaction status/reference.

Whitelist may imply auto-open and fee = 0 (or discounted). Blacklist implies deny + audit.

Roles, Audit, Security

Role-based access: protected actions (pricing, lists, user/role changes) require Admin.

Audit required for sensitive actions (pricing changes, list edits, user/role changes, payment status adjustments).

Dashboard is server-hosted on the local network; production packaging/cloud sync is later scope.

Hardware Constraints

Barrier control via Raspberry Pi GPIO / relay (prototype). Safety interlocks assumed external.

RTSP camera ingest; recorded clips acceptable during development.

Reporting (groundwork)

Templates only: revenue by period; occupancy by hour.

Exports: CSV acceptable for MVP.

ChatGPT can make mistakes. Check important info. See Cookie Preferences.