# Space Coast Studios — Master Project Memory File

> **Read this file at the start of every session before doing any work.**
> This is the single source of truth for project context, architecture, features, patterns, and status.
> Last substantive update: 2026-07-01 (Dashboard theming completed for screenshot-readiness: light/dark toggle + per-business brand color, column sorting and Active/History split on Appointments, dark-mode legibility fixes across all pages including form fields and selected-row states, muted-text contrast tuned. See Section 18.)

> **Git workflow reminder (Cowork sandbox):** In **Cowork** (this environment), Claude **cannot** run `git add`, `git commit`, or `git push` from bash -- the Linux sandbox mounts the Windows filesystem and creates lock files (`.git/HEAD.lock`, `.git/index.lock`) that cannot be removed from the sandbox, breaking subsequent commits. **In Cowork sessions: all git commands must be run by Ryan in his terminal.** Provide each command on its own line (no `&&` chaining -- PowerShell doesn't support it for copy-paste). Format:
> ```
> git add <file>
> git commit -m "message"
> git push
> ```
> Tell Ryan exactly which files to add and what commit message to use.
>
> **Claude Code sessions (native terminal):** This restriction does NOT apply. Claude Code runs natively on Ryan's machine with real filesystem access, so it CAN run git commands directly without lock file issues.
>
> **Documentation structure:** CLAUDE.md contains core architecture and active reference. These companion files hold content that grows over time -- always update them instead of CLAUDE.md when the topic matches:
> - `docs/activity-log.md` -- session history (append new entries here after every session)
> - `docs/roadmap.md` -- build status, priorities, blocked items
> - `docs/maintenance.md` -- periodic maintenance schedule and automated task details
> - `docs/clients/` -- per-tenant config notes (one file per client; new clients get a new file, not a CLAUDE.md entry)
>
> **Push rule:** ALL file changes require a push to be saved to GitHub — including CLAUDE.md and README.md. Without a push, changes only exist locally and could be lost. There are no exceptions.
>
> **Always provide git commands:** After any session where files are changed, Claude must provide Ryan with the exact `git add`, `git commit`, and `git push` commands in a code block. List every changed file explicitly -- never use `git add .` as it may stage unintended files.
>
> **After every session:** append a dated summary to `docs/activity-log.md` (what was built, changed, or decided). Keep CLAUDE.md sections 1-29 updated for architecture changes; the activity log and companion docs absorb everything else.
>
> **When features ship, change, or are removed:** update `docs/status.md` (built/partial/not-built list) and `docs/roadmap.md` (priorities and completed items) in the same session -- do not wait for the next session. If a task involves adding, modifying, or removing a platform capability, these two files are part of the definition of done.
>
> **Confirm before acting:** When Ryan asks a question or asks for thoughts ("what do you think?", "should we?", "do we need to?"), provide information only -- do not make any changes until Ryan explicitly confirms. Questions = gather information to decide. "Yes, go ahead" = act.

---

## Table of Contents

1. [What This Project Is](#1-what-this-project-is)
2. [The Three Sites](#2-the-three-sites)
3. [What SCS Sells to Clients](#3-what-scs-sells-to-clients)
4. [Pricing](#4-pricing)
5. [Infrastructure & Deployment](#5-infrastructure--deployment)
6. [Tech Stack](#6-tech-stack)
7. [Repository Structure](#7-repository-structure)
8. [Environment Variables](#8-environment-variables)
9. [Database Migrations](#9-database-migrations)
10. [Auth System](#10-auth-system)
11. [Multi-Tenancy](#11-multi-tenancy)
12. [Stripe Billing Flow](#12-stripe-billing-flow)
13. [Notification System](#13-notification-system)
14. [AI Systems](#14-ai-systems)
15. [Key Business Logic](#15-key-business-logic)
16. [Complete API Reference](#16-complete-api-reference)
17. [Frontend Routing](#17-frontend-routing)
18. [Frontend Patterns](#18-frontend-patterns)
19. [First-Login Setup Wizard](#19-first-login-setup-wizard)
20. [Platform Admin Impersonation](#20-platform-admin-impersonation)
21. [Platform Capability Status](#21-platform-capability-status)
22. [AI Model Maintenance](#22-ai-model-maintenance)
23. [Periodic Maintenance Schedule](#23-periodic-maintenance-schedule)
24. [Build Roadmap](#24-build-roadmap)
25. [A2P 10DLC Compliance](#25-a2p-10dlc-compliance)
26. [Client Services Agreement](#26-client-services-agreement)
27. [Client Onboarding Process](#27-client-onboarding-process)
28. [Common Pitfalls](#28-common-pitfalls)
29. [Local Development](#29-local-development)
30. [Activity Log](#30-activity-log)

---

## 1. What This Project Is

**Space Coast Studios (SCS)** is a B2B SaaS company founded by Ryan Ussery, based in Florida. SCS builds and manages **Launchpad**, an AI-powered booking platform for home service businesses (HVAC, plumbing, landscaping, roofing, pest control, pool service, etc.) on the Space Coast.

**Platform branding:** The product is named **Launchpad**. The legal entity remains Space Coast Studios LLC. Use "Launchpad" in all client-facing and product contexts; use "Launchpad by Space Coast Studios" in legal/formal contexts (CSA, invoices, email footers, terms/privacy pages). Domain, emails (@spacecoaststudios.com), and infrastructure remain unchanged -- no DBA filed, no domain change.

**The business model:** SCS charges a one-time setup fee + monthly retainer. Clients get a fully managed platform -- SCS handles all setup, configuration, and ongoing support.

**Contact:** Ryan Ussery · ryan@spacecoaststudios.com · usserry@gmail.com

---

## 2. The Three Sites

It is critical to understand these are three separate things with different audiences:

### 2.1 SCS Marketing Site — `spacecoaststudios.com`
- **Audience:** Prospective clients (business owners evaluating the platform)
- **Purpose:** Lead generation — showcase features, explain pricing, capture demo requests
- **Tech:** Static HTML/CSS/JS, deployed on Netlify
- **Location:** `marketing-site/`
- **Key page:** `index.html` — all-in-one marketing page with features, pricing, `#contact` form
- The `#contact` form is **SCS's own lead capture** — not a client booking widget
- `booking-demo.html` — standalone demo page (created for A2P reviewers)
- `terms.html`, `privacy.html` — required for TCPA/A2P compliance

### 2.2 Admin Dashboard — `dashboard.spacecoaststudios.com`
- **Audience:** SCS's client businesses (HVAC companies, plumbers, etc.) and SCS platform admins
- **Purpose:** Manage appointments, customers, technicians, SMS, notifications, billing
- **Tech:** React 18 + Vite + Tailwind CSS, deployed on Netlify
- **Location:** `frontend/dashboard/`

### 2.3 Platform Backend — `api.spacecoaststudios.com`
- **Audience:** Internal — serves the dashboard, client widgets, and Twilio/Stripe webhooks
- **Tech:** Python 3.11 + FastAPI, PostgreSQL 18 (DigitalOcean managed)
- **Location:** `backend/`

---

## 3. What SCS Sells to Clients

Each client gets a fully managed platform instance. **Single-tier pricing as of 2026-06-10** — one plan ("Launchpad"), everything included:

- Embeddable contact form widget (iframe on their website)
- AI-powered auto-responder to contact form submissions
- Self-scheduling booking widget (customer picks own slot from live calendar)
- AI SMS booking agent (inbound texts → Claude handles booking)
- Appointment management dashboard
- SMS and email confirmations and 24h reminders
- On The Way (OTW) technician & customer alerts
- Automated Google review requests via SMS
- Emergency dispatch with on-call rotation management
- Recurring appointment scheduling
- Custom AI persona and branding
- Unlimited service types and technicians
- Priority support (next-business-day) + monthly check-in call

Future revenue expansion is via add-ons (additional locations; voicemail AI when built; promotional SMS campaigns when built), not tiers. The old Starter/Professional split is retired — legacy plan names map to `launchpad` in the checkout API.

**The widget chain:** Homeowner visits client's website → fills out booking widget → appointment created in dashboard → tech assigned → SMS confirmation sent → OTW flow on day of job → review request after completion.

---

## 4. Pricing

### Standard Pricing (Stripe Checkout — automatic provisioning)

**Single tier (restructured 2026-06-10):**

| Plan | Setup | Monthly | Stripe product |
|---|---|---|---|
| Launchpad (everything included) | $999 | $299/mo | `prod_Ug8lLmR2lobv8S` |

### Founding Client Offer (manual provisioning, limited time — 5 spots only)

Capped at **5 founding clients** for exclusivity and to keep real-world testing manageable. Do not exceed this number.

| Plan | Setup | First 3 months | Then |
|---|---|---|---|
| Launchpad | $497 | $149/mo | $299/mo |

### Test Plan (internal use only)
`POST /api/billing/checkout` with `{"plan": "test"}` → $1 one-time + $1/mo. Use a real card; refund immediately after testing.

**Stripe publishable key** (safe to commit):
`pk_live_51TM7kZ2MJMR8rAcZ2jSBcduwtelYsLikfR9OsPACEOypphYntZ1MmdpSK7lFdMb8egcatVty5vL5h4SiB2X7sc2n00HqCzzbqd`

---

## 5. Infrastructure & Deployment

| Component | Provider | URL |
|---|---|---|
| API / Backend | DigitalOcean App Platform | `https://api.spacecoaststudios.com` |
| Database | DigitalOcean Managed PostgreSQL 18 | NYC3, 1GB RAM / 10GB disk |
| Dashboard | Netlify | `https://dashboard.spacecoaststudios.com` |
| Marketing Site | Netlify | `https://spacecoaststudios.com` |

- DNS managed in **GoDaddy** — CNAME `api.*` → DigitalOcean, `dashboard.*` + root → Netlify
- `.do/app.yaml` only defines the `api` service and database — NOT the frontend or marketing site
- **Auto-deploy on push to `main`** for all three (DO and Netlify both watch the same repo)
- Backend run command: `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- **DB backups:** GitHub Actions workflow dumps DB and uploads to Backblaze B2 (S3-compatible)

### Database Access (no console in DO UI)
```bash
psql "postgresql://doadmin:PASSWORD@host.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
```
Get full connection string from DO → Databases → spacecoast-db → Overview → Connection Details.

### Push to Deploy
```bash
git add <files>
git commit -m "message"
git push
# All three components auto-deploy on push to main
```

---

## 6. Tech Stack

### Backend
- **Python 3.11** / **FastAPI** (async where needed, sync elsewhere)
- **SQLAlchemy 2.x** (ORM with `Mapped` / `mapped_column` syntax)
- **PostgreSQL 18** via `psycopg2`
- **APScheduler** (BackgroundScheduler, runs in-process — no separate worker)
- **Stripe Python SDK** (`stripe==11.1.0`)
- **Twilio** for SMS (A2P 10DLC)
- **SendGrid** for email
- **Anthropic Python SDK** for AI responses (`claude-haiku-4-5-20251001` model — see model maintenance note below)
- **bcrypt** for password hashing
- **PyJWT** for JWT tokens
- **pydantic-settings** for config (`app/config.py`)

### Frontend
- **React 18** + **Vite**
- **React Router v6**
- **Tailwind CSS** (utility classes only — no custom config needed)
- **lucide-react** for icons
- Deployed to Netlify; `netlify.toml` + `public/_redirects` handle SPA routing

### Marketing Site
- Static HTML, vanilla JS, no framework
- Stripe Checkout buttons call `POST /api/billing/checkout`
- Demo contact form submits to `POST /contact/submit?business_id=1` (hardcoded — correct, routes to SCS's own demo intake)

---

## 7. Repository Structure

> Full annotated file tree is in `docs/repo-structure.md`. Load it when navigating unfamiliar parts of the codebase or when file locations matter. The actual filesystem is always authoritative.

Key top-level layout:
- `backend/` -- FastAPI app (`app/`), scripts, seed files, requirements.txt
- `frontend/dashboard/` -- React 18 + Vite dashboard
- `marketing-site/` -- Static HTML marketing site and demo pages
- `docs/` -- Companion reference docs (activity log, roadmap, status, API ref, clients)
- `.do/app.yaml` -- DigitalOcean App Platform config (API + DB only)
- `CLAUDE.md` -- Master project memory (this file)


## 8. Environment Variables

Set on the **api component** in DigitalOcean App Platform. Sensitive values must be **Encrypted**.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (DO injects automatically from managed DB) |
| `SECRET_KEY` | ✅ | App secret key |
| `JWT_SECRET_KEY` | ✅ | JWT signing key |
| `JWT_ALGORITHM` | — | Default: `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | — | Default: `60` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | — | Default: `30` |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio auth token + webhook validation |
| `TWILIO_PHONE_NUMBER` | ✅ | Default Twilio sending number (E.164) |
| `SENDGRID_API_KEY` | ✅ | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | ✅ | Default sender address (`noreply@spacecoaststudios.com`) |
| `FROM_NAME` | — | Default sender name (`Space Coast Studios`) |
| `ANTHROPIC_API_KEY` | ✅ | Claude API — SMS booking agent + contact AI responder |
| `LLM_MODEL` | — | Default: `claude-haiku-4-5-20251001` — used by contact form auto-responder |
| `SMS_AGENT_MODEL` | — | Default: `claude-sonnet-4-6` — used by SMS booking agent (needs stronger reasoning for multi-turn context) |
| `STRIPE_SECRET_KEY` | ✅ | Stripe live secret key (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Stripe webhook signing secret (`whsec_...`) |
| `STRIPE_PRICE_LAUNCHPAD_SETUP` | ✅ | Stripe price ID — Launchpad setup ($999). Created by `scripts/create_launchpad_prices.py` |
| `STRIPE_PRICE_LAUNCHPAD_MONTHLY` | ✅ | Stripe price ID — Launchpad monthly ($299/mo). Created by same script |
| `BASE_URL` | ✅ | `https://api.spacecoaststudios.com` — used in calendar links |
| `ALLOWED_ORIGINS` | ✅ | CORS origins (comma-separated) |
| `CONTACT_AUTO_RESPOND` | — | `true`/`false` — auto-fire AI responder on form submit |

Frontend env (set in Netlify): `VITE_API_URL=https://api.spacecoaststudios.com`

---

## 9. Database Migrations

**There is no Alembic.** Schema changes use raw `ALTER TABLE IF NOT EXISTS` in `run_migrations()` in `main.py`, which runs on every startup. This makes migrations idempotent — no errors on redeploy when columns already exist.

```python
# Pattern — always use IF NOT EXISTS
db.execute(text("ALTER TABLE businesses ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500)"))
```

Never use `ALTER TABLE ADD COLUMN` without `IF NOT EXISTS` — it logs PostgreSQL ERRORs on every deploy once the column exists.

---

## 10. Auth System

### JWT Token Structure
```python
# Standard token payload
{
  "sub": user.id,              # AdminUser.id (integer)
  "username": user.username,
  "role": user.role,           # "admin", "platform_admin", etc.
  "business_id": user.business_id,    # None for platform admins
  "is_platform_admin": True/False,
  "type": "access" | "refresh",
  "exp": ...
}

# Impersonation tokens also include (for frontend display only — API ignores these)
{
  "impersonating": True,
  "impersonated_by_id": platform_admin.id,
  "impersonated_by_name": platform_admin.username,
  "business_name": business.name,
}
```

### FastAPI Auth Dependencies (`utils/auth.py`)
- `get_current_user` — any valid JWT; returns `AdminUser`
- `get_platform_admin` — requires `is_platform_admin == True`; 403 otherwise
- `get_business_id_for_user(user, requested_id)` — platform admins must pass explicit ID; business admins always get their own `business_id`

### Platform Admin Detection
`AdminUser.business_id IS NULL` → platform admin (can see all tenants).
`AdminUser.business_id = <id>` → scoped to that business only.

### Password Reset / Account Setup Tokens
- `secrets.token_urlsafe(48)` stored in `AdminUser.password_reset_token`
- **72-hour expiry** for new account setup (from Stripe checkout provisioning)
- **1-hour expiry** for forgot-password resets
- Token is nulled out after successful use
- `set-password` returns `access_token` + `refresh_token` — auto-logs user in, redirects directly to `/setup` (new) or `/` (reset). No re-login required.

---

## 11. Multi-Tenancy

Every data model (Customer, Appointment, Technician, etc.) has a `business_id` FK. All queries filter by it.

**Platform admin** (`business_id = NULL`) sees all tenants. Uses `?business_id=X` on API calls. Frontend `useBusinessContext` hook tracks the currently active tenant.

**Business admin** — `get_business_id_for_user()` ignores any passed `business_id` and always returns their own.

### Key Business Model Fields
```python
business.slug                     # unique URL identifier (e.g. "peak-hvac")
business.twilio_phone_number      # per-client Twilio number (E.164)
business.brand_color              # hex color for widget branding (e.g. "#2563eb")
business.ai_agent_name            # e.g. "Max", "Scout"
business.ai_system_prompt         # custom AI instructions
business.ai_response_mode         # 'auto_send' | 'draft_only'
business.google_review_url        # required for review request feature
business.timezone                 # default: 'America/New_York'
business.plan                     # 'starter' | 'professional' | 'full' (demo)
business.has_completed_setup      # False until wizard finished — gates /setup redirect
business.route_optimization_enabled  # deferred feature, default: False
business.logo_url                 # business logo URL for branding
```

### Per-Business System Settings (in `system_settings` table)
```
slot_granularity_minutes         — booking slot increment (default: 30)
buffer_minutes                   — buffer between appointments (default: 15)
max_advance_booking_days         — how far out customers can book (default: 30)
min_lead_time_hours              — minimum booking notice required (default: 2)
max_appointments_per_tech_per_day
allow_same_day_booking
```

### Demo / Default Tenant
- Slug: `default`, name: "Launchpad Demo", AI agent: "Scout", `is_demo: True`, `business_id=1`
- **Tenant #1 serves double duty:** SCS lead intake AND generic demo. Marketing-site `#contact` form and `booking-demo.html` both point at `business_id=1`. **Never rebrand it as a trade-specific company. Never change the business_id target of the marketing site contact form.**
- Demo seed script for HVAC: `backend/seed_peak_hvac.py` -- available but not seeded. `peak-hvac` / `peakhvac.com` references in code are illustrative placeholders only.

### Active Demo Tenants
See `docs/clients/` for full per-tenant details (Twilio numbers, A2P status, seed scripts, notes).
Current tenants: `default` (Launchpad Demo), `brevard-pool-pros` (Brevard Pool Pros / Marina). Each vertical demo gets its own tenant and a file in `docs/clients/`.

**Rule for new clients/verticals:** create `docs/clients/[slug].md`, do NOT add tenant details to CLAUDE.md.

### Default Credentials (dev/demo only — never use in production)
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Platform admin (`business_id = NULL`) |

---

## 12. Stripe Billing Flow

### Automatic (standard pricing — via Stripe Checkout)
1. Prospect clicks **Get Started** → marketing site calls `POST /api/billing/checkout`
2. Backend creates Stripe Checkout session for the single Launchpad plan (collects email, address, phone, "Business / DBA Name")
3. Visitor redirected to Stripe Checkout, completes payment
4. Stripe sends `checkout.session.completed` webhook → `_provision_tenant()`:
   - Creates `Business` record with Stripe IDs and subscription info
   - Creates `AdminUser` (username = email, password unusable until set)
   - Generates 72-hour password-reset token
   - Sends welcome email with login username and set-password link
5. Visitor lands on `/welcome` → checks email → clicks set-password link
6. Sets password at `/set-password?token=...` → auto-logged in → redirected to `/setup` wizard
7. Wizard: 3 steps (Business Info → Look & Feel → AI & Notifications) + done screen
8. On wizard completion: `has_completed_setup = True` on Business record

### Manual (founding clients at introductory pricing)
See `docs/founder-client-onboarding.md` for step-by-step.

### Stripe Product & Price IDs

**Single-tier restructure (2026-06-10):** DONE — prices created (product `prod_Ug8lLmR2lobv8S`), IDs in `config.py` + DO env vars, checkout verified live ($1,298 first payment, then $299/mo). Old Starter/Professional products archived in Stripe (not deleted).

#### Standard Pricing (single tier)
| Price | Stripe Price ID | Amount |
|---|---|---|
| Launchpad — Setup | `price_1TgmTt2MJMR8rAcZShLwtrpM` | $999 one-time |
| Launchpad — Monthly | `price_1TgmTt2MJMR8rAcZshH8T7uB` | $299/month |

#### Founding Client Pricing (manual subscriptions only — not in checkout API)
| Price | Stripe Price ID | Amount |
|---|---|---|
| Launchpad — Founding Setup | `price_1TgmTt2MJMR8rAcZ6YZo6E1P` | $497 one-time |
| Launchpad — Founding Monthly | `price_1TgmTt2MJMR8rAcZkwbMP0rK` | $149/month (first 3 months) |

#### Legacy Pricing (retired 2026-06-10 — products remain in Stripe, no longer sold)
Starter $1,997/$249 and Professional $2,997/$399 (+ founding variants). Old price IDs preserved in `scripts/create_stripe_products.py` and git history. Legacy plan names ("starter"/"professional") sent to the checkout API map to `launchpad` via `LEGACY_PLAN_ALIASES` in `billing.py`.

#### Test Pricing
| Price | Stripe Price ID | Amount |
|---|---|---|
| Test — Setup | `price_1TbkYi2MJMR8rAcZO4iP0oHP` | $1.00 one-time |
| Test — Monthly | `price_1TbkkP2MJMR8rAcZAPo5kJx5` | $1.00/month |

### Subscription Status Updates (via webhook)
| Webhook Event | Action |
|---|---|
| `checkout.session.completed` | Provision tenant (Business + AdminUser + welcome email) |
| `customer.subscription.updated` | Update `subscription_status` and `subscription_period_end` |
| `customer.subscription.deleted` | Set `subscription_status = "cancelled"`, `is_active = False` |
| `invoice.payment_failed` | Set `subscription_status = "past_due"` |

Webhook URL: `https://api.spacecoaststudios.com/api/billing/webhook`

---

## 13. Notification System

### Notification Events
| Event | Channel | Trigger |
|---|---|---|
| `confirmation` | SMS + Email | Appointment created |
| `reminder_24h` | SMS + Email | Daily 11am–1pm local → next open business day |
| `otw_tech_prompt` | SMS to tech | 45–75 min before appointment |
| `otw_morning_kickoff` | SMS to tech | After 7am local — ~60 min before tech's first job |
| `otw_customer` | SMS to customer | Tech replies YES to OTW prompt |
| `otw_tech_complete_prompt` | SMS to tech | After OTW customer notification |
| `review_request` | SMS + Email | Tech replies YES to complete prompt |
| `emergency_dispatch` | SMS | AI agent calls emergency tool |
| `escalation_alert` | SMS + Email | Fires when Scout escalates any conversation — both `escalate_to_human` and `emergency_dispatch` (success or failure) |

All templates are editable per-business in the dashboard. Default templates in `notification_template.py`. Uses `{{token}}` syntax for variables.

### OTW / Complete Reply Flow
1. Scheduler fires `otw_tech_prompt` → tech: "Reply YES when leaving for [Customer]"
2. Tech replies YES → **inbound SMS webhook** (`/webhook/sms/inbound`) → appointment → `en_route`, customer gets "On The Way" SMS, tech gets "Reply YES when done"
3. Tech replies YES again:
   - More appointments today → next-stop prompt sent immediately
   - Last job → review request sent to customer + "Great work! That's a wrap!" to tech
4. **Collision prevention:** Won't send new OTW prompt if tech already has an `en_route` appointment
5. **Tenant scoping (fixed 2026-06-10):** the YES handler first resolves which business owns the inbound Twilio number and only matches active techs in that tenant (cross-tenant fallback only when no business owns the number). This lets the same cell phone exist as a tech in multiple demo tenants without YES replies binding to the wrong one. Hygiene rule still applies: keep Ryan's cell on only ONE active tech record per tenant context being demoed.

### Emergency Dispatch → Appointment
When the SMS agent's `emergency_dispatch` tool fires (after a successful alert to the on-call tech), the system also creates an appointment so the business keeps a record:
- `status="emergency"`, `source="emergency_sms"`, `scheduled_start=now`, duration from a dedicated **"Emergency Service"** type (auto-created once per business, 120 min default)
- Assigned to the on-call tech who was alerted; `technician_id=NULL` if dispatched to a fallback number
- Address: prefers what the agent collected in chat, then the latest non-deleted contact submission, then the customer record
- Issue summary saved to `problem_description`; explanatory note in `notes`
- **No automated notifications fire** — created directly (not via the API), and `emergency` status is excluded from the reminder, OTW-prompt, and morning-kickoff scheduler jobs. The tech was already told to contact the customer immediately.
- Customer lookup skips soft-deleted records (won't reattach to a deleted customer)
- Dashboard: bold red **emergency** badge; staff close it out manually via the status dropdown or the "Mark Complete" row action

### Escalation Alerts
When the SMS agent escalates a conversation — via `escalate_to_human` or `emergency_dispatch` (either success or failure) — `send_escalation_alert()` in `services/notifications.py` fires immediately. Recipients and channels are configured per-business on the `OnCallConfig` record:

| Field | Type | Description |
|---|---|---|
| `escalation_sms_phone` | VARCHAR(20) | Dedicated SMS alert number (office manager, owner, any mobile) |
| `escalation_email` | VARCHAR(255) | Email address for full alert email |
| `escalation_notify_oncall` | BOOLEAN | Also SMS the current on-call tech |

All configured channels fire simultaneously. Fallback chain if none are set: `fallback_phone` → `business.phone`. If neither exists, the alert is logged but not sent.

**Message content by event:**
- `escalate_to_human`: "Scout flagged a conversation for human follow-up. Customer: [name]. Reason: [reason]."
- `emergency_dispatch` success: "EMERGENCY dispatched to [tech] for [customer]. Issue / Address."
- `emergency_dispatch` failure: "EMERGENCY DISPATCH FAILED for [customer]. Immediate follow-up required."

**SMS conversations tab note:** When either escalation type fires, `SmsConversation.status` is set to `"escalated"`. These conversations appear in the **Escalated** tab of the SMS Conversations page — NOT the default Active tab.

### Background Scheduler (APScheduler — runs in-process, no separate worker)
| Job | Schedule | Description |
|---|---|---|
| `send_reminders` | Every 30 min | 11am–1pm local window; reminds for next open business day |
| `send_otw_prompts` | Every 15 min | Texts techs 45–75 min before appointment |
| `send_morning_kickoffs` | Every 15 min | After 7am local — first job of the day |
| `generate_recurring` | Daily 6am UTC | Pre-generates recurring appointment instances |

### Deduplication
The `Notification` model logs every sent notification (`appointment_id`, `notification_type`, `sent_at`). All scheduler jobs check this log before sending to prevent duplicates.

### Admin Manual Triggers (bypass time windows — for testing)
- `POST /api/admin/trigger/reminders`
- `POST /api/admin/trigger/otw-prompts`
- `POST /api/admin/trigger/morning-kickoffs`
- `GET /api/admin/scheduler/status`

These are also accessible via the Developer Tools panel in the dashboard Settings page.

---

## 14. AI Systems

### SMS Booking Agent (`services/sms_agent.py`)
- Model: set by `SMS_AGENT_MODEL` env var (default `claude-sonnet-4-6`) via Anthropic API with `tool_use`
- Runs up to **5 tool-call iterations** per inbound message
- Maintains last **20 messages** of conversation history per thread
- **4 Tools:** `check_availability`, `create_booking`, `escalate_to_human`, `emergency_dispatch`
- Required booking fields before confirming: name, service type, date/time, address
- Emergency flow: AI asks qualifying questions → confirms the service address (asks for it if not already known) → discloses fee if enabled → dispatches on-call tech → **creates an `emergency`-status Appointment** (see Section 13) → sets conversation to `escalated`. The dispatch SMS to the tech includes the customer's address and issue summary.
- Graceful fallback if no `ANTHROPIC_API_KEY`: sends polite holding message

### Contact Form AI Responder (`services/contact_responder.py`)
- Triggered on `POST /contact/submit` as a FastAPI BackgroundTask
- Opens its **own DB session** (never reuse the request session — causes DetachedInstanceError in background tasks)
- Analyzes message + availability → drafts a reply with up to 5 suggested slots
- If `ai_response_mode == "auto_send"` → sends response immediately
- If `ai_response_mode == "draft_only"` → stores as draft for staff approval in Contacts queue UI
- Staff can approve, edit, or override from dashboard → `/contacts`

#### Channel Routing (single channel only — no duplication)
The responder sends via exactly one channel based on `preferred_contact_method` and `sms_consent`:

| Preferred method | SMS consent | Channel used |
|---|---|---|
| `text` | ✅ True | **SMS only** |
| `text` | ❌ False | **Email only** (can't text without consent) |
| `email` | either | **Email only** |
| `call` | either | **Email only** (automated; staff follows up by phone) |

Sending both channels when one was chosen would be noisy and produce mismatched language (e.g. an email saying "reply to this text").

#### Channel-Aware AI Prompt
`preferred_contact_method` is passed to the LLM in both the system prompt and user message. The LLM is instructed to reference **only** the customer's preferred channel in its closing sentence:
- `text` + consent → "reply to this text"
- `email` → "reply to this email"
- `call` → "we'll give you a call / feel free to call us at [phone]"
- `text` + no consent → falls back to email language automatically

#### SMS Consent Gate (A2P/TCPA Compliance)
- `sms_consent: bool` stored on every `ContactSubmission`
- SMS is **only sent when `sms_consent = True`**
- The embed form checkbox is **optional** — submission is allowed either way (consent is not a condition of service per A2P rules)
- Consent language on form: `(Optional) I agree to receive SMS messages... SMS consent is not required to submit this form or receive service.`
- Inline form hint: when "text" is selected but consent unchecked → `"To receive your reply by text, check the SMS consent box below. Without consent, we'll send your response by email instead."` — hint disappears when both are selected

#### SMS Body Construction
Old behavior grabbed only the first paragraph (which was the greeting "Hi Name,") → SMS was always just the greeting. Fixed:
- Splits reply into paragraphs, detects and skips greeting line (short line ending with comma)
- Flattens remaining paragraphs, caps at 300 characters (~2 SMS segments)
- Logs character count on send

---

## 15. Key Business Logic

### Availability Engine (`routers/availability.py`)
`GET /api/availability` — given a service type, date range, optional technician: returns available slots. Considers business hours, blocked times, existing appointments, and technician skills/assignments. Slot granularity: 30 min (configurable per business). 15-min buffer between appointments (configurable).

### Recurring Schedules
`RecurringSchedule` records define frequency (weekly, biweekly, monthly). The `generate_recurring` job pre-generates individual appointment records so they appear in the normal appointment feed. `deactivateRecurringSchedule` soft-deletes (`is_active = False`).

### On-Call Routing
`OnCallConfig` + `OnCallRotation` + `OnCallOverride`. `GET /api/oncall/current` returns the currently on-call technician based on rotation schedule and any manual override. Used for after-hours emergency SMS routing.

**Timezone (fixed 2026-05-29):** day-of-week rotation, weekly-rolling week math, and the after-hours window are all evaluated in the **business's local timezone** (`business.timezone`, default `America/New_York`), not UTC. Previously used UTC, which returned the wrong tech in the evening once UTC rolled past midnight. Both `routers/oncall.py` and `services/oncall_notifier.py` use a `_business_local_now()` helper.

**Phone normalization:** emergency dispatch normalizes both the from- and to-numbers to E.164, so a tech stored with a bare 10-digit number still receives the alert.

### Calendar Links
Every appointment gets a unique `calendar_token` at creation. Public endpoints at `/cal/{token}` serve:
- Landing page with all platform buttons (Google, Apple, Outlook, Yahoo)
- `.ics` file download (universal format)
- Direct Google Calendar / Outlook / Yahoo URL redirects

Included in all confirmation and reminder emails and SMS messages.

---

## 16. Complete API Reference

> Full endpoint table is in `docs/api-reference.md`. Load it when adding endpoints, debugging routing issues, or auditing what's exposed. The router files in `backend/app/routers/` are always authoritative.

**Auth prefix:** `/api/auth/` -- login, refresh, set-password, forgot-password
**Business prefix:** `/api/businesses/` -- CRUD, `/me`, impersonate
**Billing prefix:** `/api/billing/` -- checkout, webhook, portal, subscription
**Appointments:** `/api/appointments/` -- CRUD, cancel
**Public (no auth):** `/contact/submit`, `/embed/{slug}/...`, `/cal/{token}/...`
**Admin triggers:** `/api/admin/trigger/...`, `/api/admin/scheduler/status`

All other resource endpoints (customers, services, technicians, availability, oncall, sms, notifications, settings, recurring) follow standard REST patterns under `/api/`.


## 17. Frontend Routing (`App.jsx`)

### Public Routes (no auth)
| Route | Component | Notes |
|---|---|---|
| `/login` | `LoginPage` | |
| `/forgot-password` | `ForgotPasswordPage` | Request reset email |
| `/set-password?token=&mode=reset` | `SetPasswordPage` | `mode=reset` → reset flow; no mode → initial setup |
| `/welcome?session_id=` | `WelcomePage` | Post-Stripe-checkout landing |
| `/setup` | `SetupPage` | First-login wizard; redirects to `/` if `has_completed_setup=true` |

### Protected Routes (JWT + `BusinessProvider`)
| Route | Component | Notes |
|---|---|---|
| `/` | `DashboardPage` | |
| `/appointments` | `AppointmentsPage` | Sort + 3-dot row menu |
| `/customers` | `CustomersPage` | Inline edit |
| `/services` | `ServicesPage` | |
| `/technicians` | `TechniciansPage` | |
| `/contacts` | `ContactsPage` | Contact form queue + AI responder controls |
| `/sms` | `SMSConversationsPage` | Full thread view + manual reply |
| `/notification-templates` | `NotificationTemplatesPage` | 12 editable templates |
| `/oncall` | `OnCallPage` | Rotation + override |
| `/settings` | `SettingsPage` | Includes Developer Tools panel for manual job triggers |
| `/billing` | `BillingPage` | Plan info (client) / tenant overview (platform admin) |
| `/businesses` | `BusinessesPage` | **Platform admin only** — Log in as button |
| `/onboard` | `OnboardingPage` | **Platform admin only** — manual tenant setup |

---

## 18. Frontend Patterns

### `api.js` Client
```javascript
// Dev: Vite proxies /api → localhost:8000
// Prod: direct to https://api.spacecoaststudios.com
const API_ROOT = isLocalhost ? '' : 'https://api.spacecoaststudios.com'

// All requests attach Bearer token from localStorage.access_token
// 401 response → clear tokens + redirect to /login
// Business-scoped calls accept optional businessId (passed as ?business_id=)
getCustomers(search = '', businessId = null)
```

### `useAuth` Hook
```javascript
const {
  user,                // { id, username, role, businessId, isPlatformAdmin }
  loading,             // true during initial token check
  login,               // (username, password) → stores tokens, sets user
  logout,              // clears access_token, refresh_token, platform_token
  impersonate,         // (businessId) → stashes current token, sets impersonation JWT
  exitImpersonation,   // restores platform_token → access_token
  isImpersonating,     // bool
  impersonatedBizName, // string shown in amber banner
} = useAuth()
```

### Impersonation localStorage Pattern
```
Normal:          localStorage.access_token = platform admin JWT
During session:  localStorage.platform_token = (stashed platform JWT)
                 localStorage.access_token   = (impersonation JWT)
After exit:      localStorage.access_token   = platform_token (restored)
                 localStorage.platform_token = cleared
logout():        clears all three keys
```

### Theming & Brand Color (added 2026-07-01)

The dashboard has a CSS-variable theming system supporting a global light/dark toggle plus per-business brand color. **Status: infrastructure is app-wide; brand color is only wired into `Layout.jsx`, `DashboardPage.jsx`, and `AppointmentsPage.jsx` so far** -- the other ~17 pages still use hardcoded blue for primary actions (see `docs/roadmap.md` for the rollout plan). Read this section before touching styling on ANY page.

**Tokens** (`frontend/dashboard/src/index.css`, `:root` + `[data-theme='dark']`):
- Neutral: `--page`, `--surface`, `--subtle`, `--ink`, `--ink-muted`, `--line`, `--line-strong`
- Brand: `--brand`, `--brand-hover`, `--brand-tint`, `--brand-ink` -- set at runtime (not in CSS) by `Layout.jsx`'s `useEffect`, which calls `computeBrandTokens(business.brand_color, theme)` (`utils/color.js`) and publishes them via `document.documentElement.style.setProperty`. Falls back to `#2563eb` when no business brand is set (platform admin view, pre-auth pages).
- Status: `--status-{emergency,pending,confirmed,inprogress,enroute,completed,cancelled,noshow}-{bg,fg}` -- dark-mode-safe replacements for Tailwind's stock pastel badge classes. Used as arbitrary-value classes, e.g. `bg-[var(--status-pending-bg)] text-[var(--status-pending-fg)]`.

**Tailwind config** (`tailwind.config.js`) remaps Tailwind's own `gray` palette (all 10 shades) onto the neutral tokens above, plus adds `page`/`surface`/`subtle`/`line`/`brand` as new color names (`bg-brand`, `text-brand-ink`, `bg-brand-tint`, `hover:bg-brand-hover`, etc.). This means **existing `text-gray-900`, `border-gray-200`, `bg-gray-50` etc. classes already re-theme for light/dark on every page with zero edits** -- no need to touch those on pages you're not otherwise changing.

**`white`/`black` and `blue` were deliberately left un-remapped** -- do not "fix" this without reading why:
- `white`/`black`: used for `text-white` sitting on solid color badges/buttons (e.g. `text-white` on `bg-red-600`) and must stay literal in both themes. Only the `bg-white` *class name* (never `text-white`) should be swapped to `bg-surface`, per file, by hand.
- `blue`: confirmed via grep audit to be overloaded across the app -- both primary-action chrome (buttons/links/focus rings, convert to `brand`) AND fixed status/semantic meaning in at least 8 pages (`in_progress` status, "New" contact badge, "active" SMS badge, business plan badge, service category tag, notification-template info banner, on-call icon, setup-wizard icon -- leave these as literal Tailwind blue). Any future page migration must distinguish these two uses per line, not blanket find-replace.

**Pitfall: literal-color background + remapped gray text = invisible in dark mode (found + fixed 2026-07-01).** Any element combining a literal (un-remapped) Tailwind background color -- `bg-blue-50`, `bg-purple-50`, `bg-green-50`, etc. -- with a `text-gray-*` class breaks in dark mode: the background stays fixed/light (these color families aren't remapped) while `text-gray-*` *is* remapped and turns light-colored, producing light-on-light invisible text. This hit "selected row/card" states in `ContactsPage.jsx`, `OnboardingPage.jsx`, `OnCallPage.jsx`, and `SMSConversationsPage.jsx`, plus static info boxes in `ContactsPage.jsx` (AI response preview) and `OnCallPage.jsx` (current on-call summary card). Two different fixes depending on intent -- pick per element, not blanket:
- **"Selected/chosen" interactive chrome** (a clicked row, a picked card, a hover backdrop) → convert to brand tokens: `bg-brand-tint` / `border-brand`. This is consistent with treating "selected" as a chrome/brand concept, same as nav active states and tab underlines.
- **Informational/status containers that must stay recognizably a fixed color** (e.g. the on-call "current tech" card, which is intentionally blue/amber to signal normal-vs-override -- see the `blue` status list above) → leave the background alone, and instead change `text-gray-*` to the equivalent `text-slate-*`. Tailwind's `slate` family is a separate, unremapped palette, so it stays a fixed dark/legible color regardless of theme without recoloring the box itself.
- **Known remaining instance, deferred, not yet fixed:** `OnboardingPage.jsx`'s 3-tile "done" screen stat cards (`bg-blue-50`/`bg-purple-50`/`bg-green-50` each with a `text-gray-500` caption) have this same bug. Not fixed yet because patching only the blue tile would look inconsistent with the still-broken purple/green ones -- needs the `text-slate-*` treatment applied to all three at once. Low priority: platform-admin-only screen, rarely seen.
- If you find more `bg-{color}-50`-with-`text-gray-*` combinations while touching a page, apply the same two-pattern test rather than assuming one fix works everywhere.

**Global form-field fix (`index.css`):** every `input`/`select`/`textarea` in the app had zero explicit bg/text classes (relied on native browser white input styling), which broke the same way in dark mode. Fixed once, app-wide, via a CSS rule targeting `input:not([type='checkbox']):not([type='radio']), select, textarea` (sets `background-color: var(--surface)`, `color: var(--ink)`, `border-color: var(--line-strong)`, plus a placeholder rule) -- no per-page edits needed for this class of bug.

**`useTheme` hook** (`frontend/dashboard/src/hooks/useTheme.jsx`, wrapped around the app in `main.jsx` alongside `AuthProvider`):
```javascript
const { theme, setTheme, toggleTheme } = useTheme()
// theme: 'light' | 'dark' — persisted to localStorage ('scs_theme'), defaults to OS
// prefers-color-scheme on first visit. Sets data-theme on <html>.
```
Two toggle entry points exist: a sun/moon icon button in the sidebar footer (`Layout.jsx`), and an "Appearance" section with explicit Light/Dark buttons at the top of Settings (`SettingsPage.jsx`) -- added because the sidebar icon alone wasn't discoverable enough.

**Dark-mode muted-text contrast:** `--ink-muted` in `[data-theme='dark']` is `#b0b0b8` (bumped one shade lighter from the original `#9a9aa2` on 2026-07-01 per Ryan's feedback that secondary/caption text was a little hard to read). Deliberately did NOT switch to pure white -- full white on a dark background reads harsh/glowy, which is why `--ink` itself is an off-white (`#f2f2f0`), not `#ffffff`. If more contrast is ever requested again, nudge this token further rather than defaulting to white.

---

## 19. First-Login Setup Wizard (`/setup`)

Runs automatically after a new business admin sets their password for the first time. If `has_completed_setup` is already `true`, redirects immediately to `/`. Platform admins also redirect to `/`.

**Step 1 — Business Info:** name (with DBA hint), phone, website, address

**Step 2 — Look & Feel:** brand color (color picker + hex input with live preview chip showing initial + business name), logo URL

**Step 3 — AI & Notifications:** AI persona name, Google Review URL (with explanation of what it's for)

Each "Next" saves the current step's data via `PUT /api/businesses/{id}`. Both "Skip for now" and "Skip setup" call `finish()` which sets `has_completed_setup: true` before navigating.

**Done screen:** 4 shortcut cards → Add Services `/services`, Add Technicians `/technicians`, Customize Notifications `/notification-templates`, Explore Dashboard `/`.

---

## 20. Platform Admin Impersonation

1. Platform admin clicks **Log in as** on `/businesses` page (disabled for inactive businesses)
2. Frontend calls `POST /api/businesses/{id}/impersonate`
3. Backend finds first active `AdminUser` for that business, mints a 2-hour JWT with standard claims (the API treats it as a normal business admin JWT)
4. Frontend stashes current token as `localStorage.platform_token`, sets new token as `localStorage.access_token`, navigates to `/`
5. Amber banner in Layout: "Viewing as **[Business Name]** — changes you make affect this client's real data"
6. **Exit impersonation** button restores `platform_token` → `access_token`, clears `platform_token`, navigates to `/businesses`

The API does not differentiate impersonation — it's a valid JWT for the business admin user. The extra impersonation claims are for frontend display only.

---

## 21. Platform Capability Status

> Full capability list (built / partial / not built) is in `docs/status.md`. Load it when planning what to build, answering "is X done?", or updating the roadmap. Keep it in sync with `docs/roadmap.md`.

**All core features are built and tested.** Key shipped items: contact form + AI responder, SMS booking agent, OTW flow, emergency dispatch, escalation alerts, recurring appointments, self-scheduling booking widget, Stripe billing + provisioning, setup wizard, platform admin impersonation, A2P-compliant consent flow.

**Partially built:** booking widget Phase 2 (Google Calendar sync), lead deduplication.
**Not yet built:** visual calendar view, customer portal, voicemail AI (high interest), promotional SMS campaigns.


## 22. AI Model Maintenance

### Model Selection Guide

Pick the cheapest model that reliably handles the task. Upgrade only when a simpler model produces bad results.

| Model | When to use | SCS example |
|---|---|---|
| `claude-haiku-4-5-20251001` | Single-turn responses, classification, summarization, high-volume tasks where cost matters | Contact form auto-responder, urgency detection on contact form, AI-generated analytics summaries |
| `claude-sonnet-4-6` | Multi-turn conversations, tool use with several steps, tasks requiring judgment or complex reasoning | SMS booking agent (multi-turn + 4 tools), quote/estimate generation |
| Opus | Not needed for any current SCS use case — only reach for it if a task repeatedly fails on Sonnet | — |

**Starting point:** single-turn / high-volume → try Haiku first; multi-turn / tool use → try Sonnet first. Test on the simpler model and only upgrade if the output quality isn't there. Either model can surprise you — Haiku handles more than you'd expect, and sometimes a task that looks complex is fine on Haiku once you see it in practice.

### Current Models in Production

`LLM_MODEL` is set to `claude-haiku-4-5-20251001` in both `backend/app/config.py` (default fallback) and the DigitalOcean App-Level Environment Variables (production value).

`SMS_AGENT_MODEL` is set to `claude-sonnet-4-6` in `config.py` (override via DO env var `SMS_AGENT_MODEL`).

These models are used by:
- **Contact form auto-responder** (`services/contact_responder.py`) — uses `LLM_MODEL` (Haiku): single-turn, high volume
- **SMS booking agent** (`services/sms_agent.py`) — uses `SMS_AGENT_MODEL` (Sonnet): multi-turn, tool use, needs reliable reasoning

### What Breaks When the Model String is Wrong
A 404 `not_found_error` from Anthropic's API silently sets contact submissions to **"Error"** status. The customer receives no reply and staff must follow up manually. The error appears in DigitalOcean Runtime Logs as:
```
anthropic.NotFoundError: Error code: 404 - model: <model-string>
```

### How to Update the Model
1. Check current valid model strings at https://docs.anthropic.com/en/docs/about-claude/models
2. Update `LLM_MODEL` in DigitalOcean → App → Settings → App-Level Environment Variables
3. Also update the default in `backend/app/config.py` line `LLM_MODEL: str = "..."`
4. Commit and push the config.py change

### How Often to Check
Anthropic publishes deprecation notices 3–6 months in advance. Check https://docs.anthropic.com/en/docs/about-claude/models every **3 months** or when you see "Error" status appearing on new contact submissions. A startup validation log line (`LLM model validated OK`) confirms the model is reachable on each deploy.

### Startup Health Check
`main.py` runs a lightweight Anthropic API call at startup to validate the model string. If it fails, a **prominent WARNING** is logged — visible in the DigitalOcean Runtime Logs immediately after deploy, before any customer traffic hits. This means a bad model string surfaces at deploy time, not on the first customer submission.

---

## 23. Periodic Maintenance Schedule

> Full schedule with task IDs and details is in `docs/maintenance.md`.

**Monthly:** DB backup verification (DO), Twilio balance (>$20), SendGrid bounce/spam rates.

**Quarterly:** LLM model string validation (`LLM_MODEL` + `SMS_AGENT_MODEL`), Python/npm dependency audit, A2P 10DLC campaign status, Stripe webhook health.

**Annually:** Rotate `JWT_SECRET_KEY` + `SECRET_KEY`, domain/SSL renewal, Stripe price ID review, CSA template review.

**Automated Cowork tasks** (run while Cowork is open):
| Task ID | Schedule | What It Does |
|---|---|---|
| `scs-quarterly-llm-model-check` | Jan/Apr/Jul/Oct 1 at 9am | Validates + auto-patches `LLM_MODEL` / `SMS_AGENT_MODEL` in `config.py` |
| `scs-quarterly-dependency-audit` | Jan/Apr/Jul/Oct 1 at 9am | Audits pip + npm packages for outdated versions and CVEs |
| `scs-monthly-infrastructure-check` | 1st of month at 9am | Reminds to check DO backups, Twilio balance, SendGrid rates |
| `scs-annual-maintenance-reminder` | Jan 1 at 9am | JWT rotation, domain, SSL, Stripe price IDs, CSA review |

**Quick diagnostic reference** -- see `docs/maintenance.md` for the full symptom/fix table.


## 24. Build Roadmap

> Full roadmap with completed items, near-term priorities, blocked items, and nice-to-haves is in `docs/roadmap.md`.
> Update `docs/roadmap.md` when features ship, priorities change, or blocked items resolve.

**Next priorities:** Screenshot refresh (pool demo tenant), A6.5 end-to-end demo readiness test, begin prospect outreach (Track A cold email).

**Pending:** CSA attorney review (Anjali Sareen, Uncommon Counsel) -- redline expected week of June 15, 2026. Must be complete before first client signs.

**Not yet built:** Visual calendar view, customer portal, voicemail AI (HIGH INTEREST), promotional SMS campaigns, cross-tenant activity log.

**Pre-client business ops checklist** (must resolve before first paying client -- does not block demos or outreach):
- Find a Florida CPA (SaaS sales tax confirmation, quarterly estimated taxes, bookkeeping)
- Brevard County local business tax receipt
- ~~Update LLC industry in Tailor Brands~~ -- OBSOLETE: Tailor Brands cancelled 2026-07-02; Northwest Registered Agent now handles registered agent services


## 25. A2P 10DLC Compliance

> Full compliance details, rejection history, approved consent language, and per-client setup checklist are in `docs/a2p-compliance.md`. Load it for any Twilio or new-client onboarding work.

**Campaign status:** APPROVED (CUSTOMER_CARE use case) as of May 2026.
**Critical rule:** Do NOT change the consent checkbox language or CTA URL without re-submitting to TCR.
**Per-client:** each new client needs their own Brand + Campaign registration -- SCS's covers SCS only.
**Adding demo numbers:** new SCS-owned demo numbers can join the existing approved campaign with no new TCR submission (buy number → sender pool → register to campaign → set number-level inbound webhook).


## 26. Client Services Agreement

**Files:** `Test Project/SCS-Client-Services-Agreement-Template.docx` (and `.pdf`) + `Test Project/SCS-Founding-Client-Pricing-Addendum.docx`

**Founding Client Pricing Addendum:** A separate signed addendum for the 5 founding clients. Supersedes Schedule A pricing for the promotional period. Key terms (updated 2026-06-10 for single-tier pricing): $497 setup + $149/mo for months 1-3, then auto-transition to the standard rate ($299/mo). 14-day written notice required before the transition date -- calendar this at onboarding (~2.5 months after go-live). Non-transferable, one-time use, capped at 5 clients. Both the CSA and this addendum must be signed for founding clients.

**File:** `Test Project/SCS-Client-Services-Agreement-Template.docx` (and `.pdf`)

**Version:** v6 (redline from Anjali Sareen received and accepted 2026-07-01). 14 sections:
1. Services, 2. Fees & Payment, 3. Term, 4. Client Responsibilities, 5. Termination, 6. IP, 7. Confidentiality, 8. Support, 9. Limitation of Liability, 10. Indemnification, 11. Warranties, **12. AI Services**, 13. Governing Law & Disputes, 14. General Provisions

**Key terms settled in Anjali's redline (2026-07-01):**
- Liability cap: 12 months of fees paid (accepted -- courts view 3 months as too one-sided; 12 months = ~$3,588 worst case)
- Performance warranty: Platform will "materially conform to the Documentation" -- satisfied by platform user guides/feature docs (see roadmap: Platform Documentation item)
- Schedule A: Fully modifiable as needed. Pricing lives in Schedule A, not the agreement body. **60 days written notice required before changing the monthly fee.**
- AI update notice: 7 days for material changes (reduced from 15); no notice required for legal/regulatory/security changes
- Testimonial clause: SCS has perpetual license to use any provided testimonial; written consent recommended before soliciting

**Section 5.4 survival clause:** Sections 5.3, 6, 7, 9, 10, 11, 12, 13, and 14.10 survive termination.

**Next action:** Update Schedule A to single Launchpad tier ($999 setup + $299/mo) and accept Anjali's redline to produce v6 final. **Ready to send to clients once Schedule A is updated.**

---

## 27. Client Onboarding Process

### Timeline
- **Day 1:** Create business tenant, assign Twilio number, submit A2P registration, configure services/techs/hours/AI persona, customize notification templates
- **Days 3–7:** Platform live — embed widget installed on client site, email notifications active, dashboard training
- **Days 7–21:** Client live and taking bookings. A2P under carrier review.
- **Days 21–28:** A2P approved → all SMS features activate → full smoke test

**What to tell clients:** "Your platform will be up and taking bookings within one week. SMS features require a one-time carrier registration that takes 2–4 weeks. We submit it on Day 1 — everything else goes live immediately while we wait."

**Full smoke test checklist:** `Test Project/SCS_Onboarding_Checklist.docx`

### Automatic Provisioning (Stripe Checkout)
1. Client completes Stripe Checkout → tenant provisioned automatically
2. Welcome email sent (72-hr set-password link)
3. Client sets password → redirected to setup wizard → completes in-dashboard setup
4. You: complete A2P 10DLC (2–3 days minimum before go-live)
5. Set `twilio_phone_number` on Business record
6. Confirm Google Review URL is set
7. Create test appointment → verify confirmation SMS + email
8. Test OTW: `POST /api/admin/trigger/otw-prompts` → confirm tech prompt → reply YES → confirm customer SMS

### Manual Provisioning (Founding Clients)
See `docs/founder-client-onboarding.md`.

---

## 28. Common Pitfalls

### SMS / Twilio
- **30034 Unregistered Number** — number not registered to campaign; use Register Phone Numbers button on the campaign page
- **30024 Provisioning Issue** — number in sender pool but not registered to campaign (different step)
- **"No HTTP Requests logged for this event"** — inbound handler not configured at the number level; go to Active Numbers → click the number → Messaging → set "A MESSAGE COMES IN" to the webhook URL. Adding a number to the sender pool only controls outbound.
- **Phone format mismatch** — DB may store numbers as 10-digit; Twilio sends E.164. Backend uses multi-format `.in_()` lookups to handle both.
- **Morning kickoff missed** — fires every 15 min but only if tech's first appointment is within 60 min AND after 7am local. If appointments created after lookahead window passes, kickoff can miss. Use manual trigger to test: `POST /api/admin/trigger/morning-kickoffs`.

### Stripe / Billing
- **`customer_creation` not valid** — only valid in `payment` mode, not `subscription` mode
- **Missing recurring price** — Stripe requires at least one recurring price in subscription mode; always include both setup (one-time) and monthly (recurring) line items
- **Email blank after provisioning** — customer email is in `customer_details.email` in the webhook payload, not top-level `customer_email`
- **`stripe` module not found** — ensure `stripe==11.1.0` in `requirements.txt`

### Deployment / Backend
- **DO env vars** — all Stripe keys must be on the **api component**, not app-level env vars
- **Migrations** — always use `IF NOT EXISTS` on `ALTER TABLE` statements; without it, PostgreSQL logs ERRORs on every deploy once the column exists
- **`ADD COLUMN` spacing** — when editing migration SQL, verify there's a space after `IF NOT EXISTS` before the column name

### Git / Bash
- **File-tool writes do not truncate on the Windows mount (CRITICAL, found 2026-06-10, recurred 2026-07-01):** when the Edit/Write tools rewrite an existing repo file, the tail is sometimes silently lost -- either padded with NUL bytes or just cut clean with no padding. This truncated `marketing-site/index.html` (broke the live checkout JS for ~9 days) and CLAUDE.md itself in June. **Recurrence 2026-07-01 disproved the "shrink-only" theory:** during the dashboard retheme session, three files were silently truncated -- `main.jsx` (an Edit that *grew* the file by one line), `Layout.jsx` and `DashboardPage.jsx` (both full-file Write rewrites), and `AppointmentsPage.jsx` (after a long chain of small Edits, cut off mid-JSX-attribute at the very end). Two sibling files written via Write in the same session (`tailwind.config.js`, `index.css`) were unaffected. So the bug is not reliably tied to shrinking, file size, or Edit vs. Write -- treat it as flaky/non-deterministic on this mount. **Rule: after EVERY Edit or Write to an existing repo file (regardless of size or direction of change), verify via bash: zero NUL bytes (`python3 -c "print(open(path,'rb').read().count(b'\\x00'))"`) and the file's actual tail matches what was intended (`tail -c 200 path`). Do not trust the tool's success message alone.** If truncated, repair via bash Python `io.open(path, "a"/"w", encoding="utf-8")` (append the missing tail, or rewrite in full), then re-verify. Write tool is fine for brand-new files only -- but even those should get the same post-write check now.
- **Never run `git add`/`git commit` from bash (Cowork only)** -- the Cowork Linux sandbox mounts a Windows filesystem. Git lock files created in bash cannot be removed from bash (`Operation not permitted`), breaking all subsequent commits in the session. Give Ryan the commands to run in his terminal instead. **Exception: Claude Code** runs natively on Ryan's machine and CAN run git commands without this problem.
- **PowerShell does not support `&&` chaining** -- put each command on its own line so Ryan can copy-paste individually.

### Marketing Site
- `API_URL` is declared at the top of the script block (before checkout button handlers that use it)
- Checkout buttons use `data-checkout-plan="starter"` / `"professional"` attributes
- Demo contact form submits to `?business_id=1` (hardcoded — intentional, routes to SCS demo intake)
- Error contact email: `hello@spacecoaststudios.com`

---

## 29. Local Development

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in secrets
uvicorn app.main:app --reload
# → http://localhost:8000

# Frontend
cd frontend/dashboard
npm install
npm run dev
# → http://localhost:5173
# /api/* proxied to https://api.spacecoaststudios.com (see vite.config.js)
```

### Test Stripe Checkout Locally
```powershell
$result = Invoke-RestMethod -Method POST -Uri "https://api.spacecoaststudios.com/api/billing/checkout" -ContentType "application/json" -Body '{"plan": "test"}'
$result.url  # open in browser — $2 total, refund immediately after
```

---

## 30. Activity Log

> Full session history is in `docs/activity-log.md`.
> **After every session:** append a dated entry there -- what was built, changed, or decided.
> Do NOT add session history here.

**Most recent update:** 2026-07-02 (CSA v6 finalized and Schedule A updated to single Launchpad tier; Twilio number assignments confirmed; Tailor Brands cancelled/Northwest Registered Agent engaged. See `docs/activity-log.md` for full details.)

**Key recent history:**
- 2026-07-01: Dashboard theming (see above) -- see `docs/activity-log.md` for the full multi-entry breakdown of this session
- 2026-06-10: Single-tier pricing restructured ($999+$299/mo); pool vertical built (Brevard Pool Pros, Marina, +13213984101 live); index.html truncation bug repaired; YES-reply tenant scoping fix shipped
- 2026-06-02: Escalation alerts built (SMS+email+on-call); on-call banner and week-position UI fixed
- 2026-06-01: Launchpad rebrand across all files; CSA v3 sent to Anjali Sareen (attorney)
- 2026-05-31: Recurring appointments dashboard UI; demo page polish; AI model selection guide added
- 2026-05-30: Self-scheduling booking widget (Phase 1) shipped and tested; GTM sales assets built
- 2026-05-29: SMS booking agent end-to-end flow; on-call timezone fix; emergency dispatch hardening
