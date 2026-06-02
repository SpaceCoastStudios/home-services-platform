# Space Coast Studios — Master Project Memory File

> **Read this file at the start of every session before doing any work.**
> This is the single source of truth for project context, architecture, features, patterns, and status.
> Last substantive update: 2026-06-02 (Escalation alerts built; on-call banner fixed for weekly rolling rotation; week position dropdown UI improved; escalated SMS conversation tab behavior documented.)

> **Git workflow reminder:** Claude **cannot** run `git add`, `git commit`, or `git push` from bash -- doing so creates Windows filesystem lock files (`.git/HEAD.lock`, `.git/index.lock`) that cannot be removed from the sandbox, breaking subsequent commits. **All git commands must be run by Ryan in his terminal.** Provide each command on its own line (no `&&` chaining -- PowerShell doesn't support it for copy-paste). Format:
> ```
> git add <file>
> git commit -m "message"
> git push
> ```
> Tell Ryan exactly which files to add and what commit message to use.
>
> **Push rule:** ALL file changes require a push to be saved to GitHub — including CLAUDE.md and README.md. Without a push, changes only exist locally and could be lost. There are no exceptions.
>
> **Always provide git commands:** After any session where files are changed, Claude must provide Ryan with the exact `git add`, `git commit`, and `git push` commands in a code block. List every changed file explicitly -- never use `git add .` as it may stage unintended files.
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

Each client gets a fully managed platform instance. Features depend on plan:

**Starter plan:**
- Embeddable contact form widget (iframe on their website)
- AI-powered auto-responder to contact form submissions
- Appointment management dashboard
- SMS and email confirmations and 24h reminders
- Up to 5 service types, 5 technicians

**Professional plan (everything in Starter plus):**
- Self-scheduling booking widget (customer picks own slot from live calendar) — **backend ready, widget UI not yet built**
- AI SMS booking agent (inbound texts → Claude handles booking)
- On The Way (OTW) technician & customer alerts
- Automated review requests via SMS
- Automated Google review requests
- Emergency dispatch with on-call rotation management
- Recurring appointment scheduling
- Custom AI persona and branding
- Unlimited service types and technicians
- Priority support + monthly check-in call

**The widget chain:** Homeowner visits client's website → fills out booking widget → appointment created in dashboard → tech assigned → SMS confirmation sent → OTW flow on day of job → review request after completion.

---

## 4. Pricing

### Standard Pricing (Stripe Checkout — automatic provisioning)

| Plan | Setup | Monthly |
|---|---|---|
| Starter | $1,997 | $249/mo |
| Professional | $2,997 | $399/mo |

### Founding Client Offer (manual provisioning, limited time — 5 spots only)

Capped at **5 founding clients** for exclusivity and to keep real-world testing manageable. Do not exceed this number.

| Plan | Setup | First 3 months | Then |
|---|---|---|---|
| Starter | $497 | $99/mo | $249/mo |
| Professional | $997 | $199/mo | $399/mo |

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

```
home-services-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Entry point: FastAPI app, run_migrations(), seed_defaults(), lifespan
│   │   ├── config.py                # Pydantic Settings — reads env vars + defaults
│   │   ├── database.py              # SQLAlchemy engine, SessionLocal, Base, get_db()
│   │   ├── models/
│   │   │   ├── admin_user.py        # Platform admins (business_id=NULL) and business admins
│   │   │   ├── business.py          # Business tenant — all billing, branding, AI config fields
│   │   │   ├── appointment.py
│   │   │   ├── customer.py
│   │   │   ├── service_type.py
│   │   │   ├── technician.py
│   │   │   ├── business_hours.py
│   │   │   ├── blocked_time.py
│   │   │   ├── contact_submission.py
│   │   │   ├── notification.py      # Notification log (prevents duplicate sends)
│   │   │   ├── notification_template.py
│   │   │   ├── oncall.py            # OnCallConfig + OnCallRotation + OnCallOverride
│   │   │   ├── recurring_schedule.py
│   │   │   ├── sms_conversation.py
│   │   │   ├── system_settings.py
│   │   │   └── inquiry.py
│   │   ├── routers/
│   │   │   ├── auth.py              # login, refresh, set-password, forgot-password
│   │   │   ├── billing.py           # Stripe checkout, webhook, portal, subscription
│   │   │   ├── businesses.py        # Business CRUD + /me + impersonate
│   │   │   ├── admin.py             # Manual notification triggers, scheduler status
│   │   │   ├── appointments.py
│   │   │   ├── availability.py
│   │   │   ├── business_hours.py
│   │   │   ├── customers.py
│   │   │   ├── contact.py           # Public contact form + AI responder
│   │   │   ├── embed.py             # Public booking widget endpoints
│   │   │   ├── calendar_links.py    # ICS file generation + calendar landing page
│   │   │   ├── notification_templates.py
│   │   │   ├── oncall.py
│   │   │   ├── recurring.py
│   │   │   ├── services.py
│   │   │   ├── sms_webhook.py       # Twilio inbound SMS — OTW/complete reply flow
│   │   │   └── technicians.py
│   │   ├── services/
│   │   │   ├── scheduler.py         # APScheduler background jobs
│   │   │   ├── notifications.py     # SMS (Twilio) + email (SendGrid) send functions
│   │   │   ├── sms_agent.py         # Claude AI SMS booking agent (tool_use, 4 tools)
│   │   │   ├── contact_responder.py # AI auto-reply to contact form submissions
│   │   │   ├── scheduling.py        # Availability engine
│   │   │   ├── oncall_notifier.py   # Emergency dispatch
│   │   │   └── template_renderer.py # Notification template variable rendering
│   │   └── utils/
│   │       ├── auth.py              # JWT helpers, password hashing, FastAPI dependencies
│   │       └── ics.py               # ICS calendar file generator
│   ├── scripts/
│   │   ├── create_stripe_products.py  # One-time Stripe product/price setup
│   │   └── backup_db.py               # DB backup to Backblaze B2
│   ├── seed_peak_hvac.py              # Demo HVAC client seed script
│   ├── requirements.txt
│   └── .env.example
├── frontend/dashboard/
│   ├── src/
│   │   ├── App.jsx                  # All routes — public + protected
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── ForgotPasswordPage.jsx    # /forgot-password
│   │   │   ├── SetPasswordPage.jsx       # /set-password?token=&mode=reset
│   │   │   ├── WelcomePage.jsx           # /welcome?session_id= (post-Stripe)
│   │   │   ├── SetupPage.jsx             # /setup (first-login wizard)
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── AppointmentsPage.jsx
│   │   │   ├── CustomersPage.jsx
│   │   │   ├── ServicesPage.jsx
│   │   │   ├── TechniciansPage.jsx
│   │   │   ├── ContactsPage.jsx          # Contact form submission inbox + AI responder
│   │   │   ├── SMSConversationsPage.jsx
│   │   │   ├── NotificationTemplatesPage.jsx
│   │   │   ├── OnCallPage.jsx
│   │   │   ├── SettingsPage.jsx          # AI persona, email config, booking prefs, dev tools
│   │   │   ├── BillingPage.jsx
│   │   │   ├── BusinessesPage.jsx        # Platform admin: all tenants + impersonation
│   │   │   └── OnboardingPage.jsx        # Platform admin: manual tenant provisioning
│   │   ├── components/
│   │   │   ├── Layout.jsx               # Sidebar nav + amber impersonation banner
│   │   │   └── RowMenu.jsx              # Reusable 3-dot dropdown (portal-rendered)
│   │   ├── hooks/
│   │   │   ├── useAuth.jsx              # Auth state, login/logout, impersonate/exit
│   │   │   └── useBusinessContext.jsx   # Active business for platform admins
│   │   └── services/
│   │       └── api.js                   # All API calls with JWT auth
│   ├── vite.config.js                   # Proxies /api → API root in dev
│   ├── netlify.toml
│   └── public/_redirects                # /* /index.html 200 (SPA fallback)
├── marketing-site/
│   ├── index.html                       # All-in-one marketing page
│   ├── booking-demo.html
│   ├── privacy.html
│   └── terms.html
├── docs/
│   ├── founder-client-onboarding.md     # Manual provisioning guide for founding clients
│   └── archive/
│       └── HomeServices_Architecture_Plan.md  # Original pre-build spec (March 2026, historical)
├── README.md                            # Ops quick-reference: Stripe IDs, A2P checklist, pitfalls
├── CLAUDE.md                            # THIS FILE — master project memory
└── .do/app.yaml                         # DigitalOcean App Platform config (API + DB only)
```

### Key files outside the repo (in `Test Project/` root)
```
Test Project/
├── SCS-Client-Services-Agreement-Template.docx  # Signed CSA template
├── SCS-Client-Services-Agreement-Template.pdf   # PDF version
├── Platform Capability Checklist.docx           # Feature status tracker — KEEP CURRENT (see note below)
├── SCS Platform Roadmap.docx                     # Roadmap: Completed / Near-Term / Later — KEEP CURRENT
├── SCS_Onboarding_Checklist.docx                # Client onboarding + smoke test steps
└── SpaceCoastStudios_SystemGuide.docx           # Full system SOPs
```

> **Keep the status + onboarding trackers current.** Whenever a feature ships, is tested, or changes status, update `Platform Capability Checklist.docx` (capability status + notes + summary counts), `SCS Platform Roadmap.docx` (move items between Completed / Near-Term / Later), and `SCS_Onboarding_Checklist.docx` (onboarding + smoke-test steps as they change). These are the canonical *non-technical* status docs and are expected to stay in sync with this file and the README. **How to edit:** npm/docx-js is blocked in this environment, so regenerate them with **pandoc** from Markdown — `pandoc file.md -o "Test Project/<file>.docx"`. This is how both were rebuilt on 2026-05-29.

---

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
| `STRIPE_PRICE_STARTER_SETUP` | ✅ | Stripe price ID — Starter setup ($1,997) |
| `STRIPE_PRICE_STARTER_MONTHLY` | ✅ | Stripe price ID — Starter monthly ($249/mo) |
| `STRIPE_PRICE_PRO_SETUP` | ✅ | Stripe price ID — Professional setup ($2,997) |
| `STRIPE_PRICE_PRO_MONTHLY` | ✅ | Stripe price ID — Professional monthly ($399/mo) |
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
- Slug: `default`, name: "Space Coast Studios Demo", AI agent: "Scout", `is_demo: True`
- Demo seed script for a full HVAC client: `backend/seed_peak_hvac.py` — **available but not currently seeded.** As of 2026-05-29 the only live tenant on the platform is the Space Coast Studios Demo above (slug `default`). Other `peak-hvac` / `peakhvac.com` references in the codebase are illustrative examples and UI placeholders, not a live tenant.

### Default Credentials (dev/demo only — never use in production)
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Platform admin (`business_id = NULL`) |

---

## 12. Stripe Billing Flow

### Automatic (standard pricing — via Stripe Checkout)
1. Prospect clicks **Get Started** → marketing site calls `POST /api/billing/checkout`
2. Backend creates Stripe Checkout session (collects email, address, phone, "Business / DBA Name")
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

#### Standard Pricing
| Price | Stripe Price ID | Amount |
|---|---|---|
| Starter — Setup | `price_1TbXKM2MJMR8rAcZfEKeo13B` | $1,997 one-time |
| Starter — Monthly | `price_1TbXKN2MJMR8rAcZ8ageyctL` | $249/month |
| Professional — Setup | `price_1TbXKN2MJMR8rAcZIiW0KPMT` | $2,997 one-time |
| Professional — Monthly | `price_1TbXKO2MJMR8rAcZh0yQdVOv` | $399/month |

#### Founding Client Pricing (manual subscriptions only — not in checkout API)
| Price | Stripe Price ID | Amount |
|---|---|---|
| Starter — Founding Setup | `price_1TbXKN2MJMR8rAcZvreEPLwo` | $497 one-time |
| Starter — Founding Monthly | `price_1TbXKN2MJMR8rAcZF8PV52FQ` | $99/month (first 3 months) |
| Professional — Founding Setup | `price_1TbXKO2MJMR8rAcZ9MRzpF2s` | $997 one-time |
| Professional — Founding Monthly | `price_1TbXKO2MJMR8rAcZMiHThRka` | $199/month (first 3 months) |

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

### Auth (`/api/auth/...`)
| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| `POST` | `/api/auth/login` | none | `{username, password}` → `{access_token, refresh_token}` |
| `POST` | `/api/auth/refresh` | none | `{refresh_token}` → new token pair |
| `POST` | `/api/auth/set-password` | none | `{token, password, confirm_password}` → `{access_token, refresh_token}`. Token nulled after use. New users → `/setup`, resets → `/`. |
| `POST` | `/api/auth/forgot-password` | none | `{email}` → always 200 (prevents enumeration). Sends 1-hr reset link if email found and active. |

### Businesses (`/api/businesses/...`)
| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| `GET` | `/api/businesses` | platform admin | Lists all with billing fields |
| `POST` | `/api/businesses` | platform admin | Create business |
| `GET` | `/api/businesses/me` | business admin | Get caller's own business |
| `GET` | `/api/businesses/{id}` | platform admin | Get by ID |
| `PUT` | `/api/businesses/{id}` | any JWT | Business admins can only update own; cannot change `plan`, `is_active`, `is_demo`, Stripe fields |
| `POST` | `/api/businesses/{id}/impersonate` | platform admin | Returns 2-hr impersonation JWT for business's first active admin user |

### Billing (`/api/billing/...`)
| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| `POST` | `/api/billing/checkout` | none | `{plan}` → `{url}` (Stripe Checkout URL) |
| `GET` | `/api/billing/checkout-session` | none | `?session_id=` → `{email}` (for welcome page) |
| `POST` | `/api/billing/webhook` | Stripe sig | Handles Stripe events |
| `GET` | `/api/billing/subscription` | JWT | Current plan/status for active business |
| `POST` | `/api/billing/portal` | JWT | Create Stripe Customer Portal session → `{url}` |

### Appointments (`/api/appointments/...`)
| Method | Endpoint | Notes |
|---|---|---|
| `GET` | `/api/appointments` | `?sort=upcoming\|newest\|oldest` (default: upcoming) |
| `POST` | `/api/appointments` | Create; fires confirmation SMS + email immediately |
| `GET` | `/api/appointments/{id}` | Get by ID |
| `PUT` | `/api/appointments/{id}` | Update |
| `POST` | `/api/appointments/{id}/cancel` | Cancel |

### Other Endpoints (all JWT-protected unless noted)
- `GET/PUT /api/business-hours` — business hours by day of week
- `GET/POST/DELETE /api/blocked-times` — blocked time slots
- `GET/PUT /api/settings/{key}` — per-business key-value settings
- `GET/POST/PUT/DELETE /api/customers`
- `GET/POST/PUT/DELETE /api/services`
- `GET/POST/PUT /api/technicians`
- `GET /api/availability`
- `GET/POST/PUT/DELETE /api/recurring` + `POST /api/recurring/{id}/generate`
- `GET/PUT /api/oncall/config`, `GET/POST/DELETE /api/oncall/rotation`, `GET/POST/DELETE /api/oncall/override`, `GET /api/oncall/current`
- `GET /api/contact-submissions`, `PUT /api/contact-submissions/{id}`
- `POST /api/contact-submissions/{id}/respond` — trigger AI response
- `POST /api/contact-submissions/{id}/approve` — approve AI draft
- `POST /api/contact-submissions/{id}/manual-response`
- `GET/POST /api/sms-conversations`, `POST /api/sms-conversations/{id}/close`, `POST /api/sms-conversations/{id}/send`
- `GET/PUT /api/notification-templates`, `POST /api/notification-templates/reset`

### Public Endpoints (no auth)
- `POST /contact/submit?business_id=` — contact form widget submission
- `GET /embed/{slug}/contact` — contact widget iframe HTML
- `GET /embed/{slug}/booking` — self-scheduling booking widget HTML
- `GET /embed/{slug}/booking-config`, `GET /embed/{slug}/availability` — booking widget config + open slots
- `POST /embed/{slug}/book` — create a booking (re-validates slot, assigns tech, fires confirmation; honeypot + Emergency type excluded)
- `GET /cal/{token}`, `/cal/{token}/google`, `/cal/{token}/ical`, `/cal/{token}/outlook`, `/cal/{token}/yahoo`

### Admin / Notification Triggers (JWT required)
- `POST /api/admin/trigger/reminders`
- `POST /api/admin/trigger/otw-prompts`
- `POST /api/admin/trigger/morning-kickoffs`
- `GET /api/admin/scheduler/status`
- `POST /api/admin/appointments/{id}/resend-confirmation`
- `POST /api/admin/appointments/{id}/send-reminder`
- `POST /api/admin/appointments/{id}/send-review-request`

---

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

### ✅ Fully Built
Contact form + AI auto-responder, emergency SMS call routing, business hours config, blocked times, multi-technician dispatch, appointment status workflow, calendar invite (.ics + Google/Outlook/Yahoo), appointment reminders (next-business-day, noon local, 30-min check, idempotent), manual reply from dashboard, per-business email branding, full SMS OTW flow, booking confirmation SMS, login + JWT auth, forgot-password + reset flow, contact queue UI, appointments view (with expandable detail rows + Edit Details modal), customer records (inline edit), service types, technician management (first/last name split UI), settings page, multi-tenant architecture, business management, demo tenant seeding, add-to-calendar (customer-facing), phone number E.164 normalization, admin manual job triggers, Stripe billing (checkout → webhook → provisioning), first-login setup wizard, platform admin impersonation, notification templates (12 editable per-business), on-call rotation + override, **problem description capture** (contact form + appointment model + dashboard), **tech daily schedule page** (public mobile page per technician, no login), **morning kickoff overhaul** (2-hour trigger, full daily summary, no-appointments variant), **soft delete** (appointments, customers, contact submissions — `is_deleted` flag, filtered from all queries + availability engine), **contact responder channel awareness** (AI reply references only customer's preferred contact channel; SMS truncation improved to skip greeting, cap at 300 chars), **on-call rotation + override (tested end-to-end, business-local timezone; weekly rolling auto-cycles via modulo)**, **on-call banner now uses GET /api/oncall/current (fixed weekly rolling display bug)**, **week position UI now shows "Week 1/2/3" dropdown instead of 0-indexed number input**, **emergency SMS dispatch (tested end-to-end)**, **escalation alerts (SMS + email + on-call tech) when Scout escalates any conversation — configurable per-business in On-Call Settings**, — AI captures the service address in chat, alerts the on-call tech, and creates an `emergency`-status appointment, **customer-facing phone number formatting** `(321) 386-7604` across SMS agent, contact responder, and notification templates (tech alert intentionally stays E.164), **recurring appointments dashboard UI (2026-05-31)**: expandable rows showing details/address/notes, Edit modal (frequency, day, time, technician, end date, address, notes), appointment history panel (upcoming + last 5 past per schedule), "Generate appointments now" button — all in the existing Recurring Series tab of the Appointments page, **self-scheduling booking widget (Phase 1 — shipped + tested 2026-05-30)**: public slug-scoped `/embed/{slug}/booking-config|availability|book` + embeddable `/embed/{slug}/booking` UI reusing the availability engine; books a confirmed appointment, assigns a tech, fires the confirmation, is capacity-aware, excludes the internal Emergency Service type, and is embedded live on the demo page

### ⚠️ Partially Built
- **Online self-booking widget** — Phase 1 (internal-only) **shipped + tested 2026-05-30** (public endpoints + embeddable UI). Phase 2 (Google Calendar two-way sync) / Phase 3 (Outlook) not yet built.
- **Emergency contact form routing** — AI handles urgency in SMS; contact form doesn't route to on-call (SMS flow does)
- **Lead deduplication** — customer lookup exists; auto-linking on contact form submission not fully wired

### ❌ Not Yet Built
- Visual calendar view (day/week/month) in dashboard — currently list-only
- Customer portal (magic link login, view/reschedule appointments)
- Usage/analytics dashboard across all tenants
- Route optimization (column placeholder in DB, feature deferred)
- **Voicemail + AI response** (HIGH INTEREST) — Missed-call text-back via call forwarding + voicemail recording. Flow: client forwards their existing business number to Twilio; Twilio plays a greeting and records the voicemail; Whisper transcribes the audio; Claude generates an SMS response to the caller; logs voicemail/transcript/AI response in the dashboard alongside SMS conversations. Requires TwiML call handling (new capability layer, separate from SMS webhooks). Candidate for "Coming Soon" on the marketing site once fleshed out. Do NOT promise to prospects until built.
- **Promotional/re-engagement SMS campaigns** — Seasonal SMS to past customer lists (e.g. "time for your spring HVAC tune-up" or holiday pool specials). Requires: (1) new A2P MIXED campaign registration (brand stays approved, new campaign submission ~2-4 weeks); (2) explicit marketing opt-in mechanism separate from the service communications consent; (3) opt-in UI on the contact form. Build toward; do not promise until opt-in flow is designed.

---

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

These are recurring tasks that keep the platform running correctly. Most are low-effort but easy to forget. Review this section at the start of each quarter.

### Monthly

| Task | What to Check | Where |
|------|--------------|-------|
| **DB backup verification** | Confirm DigitalOcean automated backups are enabled and a recent snapshot exists | DO → Databases → Backups tab |
| **Twilio account balance** | Ensure credit balance won't run out mid-month; top up if under $20 | Twilio Console → Billing |
| **SendGrid sender reputation** | Check bounce/spam rates; >5% bounce rate can trigger account suspension | SendGrid → Stats → Overview |

### Quarterly

| Task | What to Check | Where |
|------|--------------|-------|
| **LLM model string** | Verify `claude-haiku-4-5-20251001` (or current value) is still valid at https://docs.anthropic.com/en/docs/about-claude/models | Update `LLM_MODEL` in DO env vars + `config.py` if changed |
| **SMS_AGENT_MODEL** | Verify `claude-sonnet-4-6` (or current value) is still valid at same URL | Update default in `config.py`; optionally add `SMS_AGENT_MODEL` to DO env vars to override |
| **Python dependencies** | `pip list --outdated` in backend; review security advisories | `backend/` |
| **npm dependencies** | `npm outdated` in frontend; watch for breaking changes | `frontend/dashboard/` |
| **A2P 10DLC campaign status** | Confirm campaign is still active; carriers can deactivate campaigns without notice | Twilio Console → Messaging → Regulatory Compliance |
| **Stripe webhook health** | Confirm webhook endpoint is active and receiving events | Stripe Dashboard → Developers → Webhooks |

### Annually

| Task | What to Check | Where |
|------|--------------|-------|
| **Rotate JWT_SECRET_KEY** | Generate a new random 64-char secret; redeploy; all existing sessions invalidate (users must log in again) | DO env vars + `config.py` |
| **Rotate SECRET_KEY** | Same process as JWT_SECRET_KEY | DO env vars + `config.py` |
| **Domain renewal** | `spacecoaststudios.com` and any client domains | Domain registrar |
| **SSL certificate** | DO typically auto-renews; verify it hasn't lapsed | DO → App → Domains |
| **Stripe price IDs** | If pricing tiers change, update all `STRIPE_PRICE_*` constants in `config.py` and the DO env vars | `config.py` lines 48–57 |

### Event-Triggered (Do When the Event Happens)

| Trigger | Action |
|---------|--------|
| Anthropic deprecation notice email | Update `LLM_MODEL` in DO env vars and `config.py`; redeploy; verify startup log shows `LLM model validated OK` |
| Client changes their Google Business listing URL | Update `google_review_url` in their Business Settings record |
| Stripe announces pricing API changes | Audit `routers/billing.py` and `config.py` Stripe constants |
| Twilio announces SMS API changes | Audit `services/sms_agent.py` and `services/notifications.py` |
| SendGrid announces API deprecation | Audit `services/email_service.py` |
| New client onboarded | Submit A2P Brand + Campaign registration Day 1 (see Section 25) |
| Client cancels / offboards | Disable their Stripe subscription, soft-delete or archive their Business record |

### Quick Diagnostic Reference

| Symptom | First place to look |
|---------|-------------------|
| Contact submissions show "Error" status | DigitalOcean Runtime Logs → look for `404 not_found_error` (bad LLM model) or `anthropic.AuthenticationError` (bad API key) |
| SMS messages not sending | Twilio Console → Monitor → Errors; check `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` |
| Emails not delivering | SendGrid Activity Feed; check `SENDGRID_API_KEY` and sender verification |
| Stripe webhooks failing | Stripe → Developers → Webhooks → click endpoint → view failed events |
| App won't start after deploy | DO Runtime Logs → look for migration errors or import errors |

### Automated Scheduled Tasks (Cowork)

The following maintenance tasks are automated via Cowork scheduled tasks (stored in `C:\Users\Ryan\Documents\Claude\Scheduled\`). They run while the Cowork app is open; if the app is closed at fire time, they run on next launch.

| Task ID | Schedule | What It Does |
|---------|----------|-------------|
| `scs-quarterly-llm-model-check` | Quarterly — Jan/Apr/Jul/Oct 1 at 9am | Fetches Anthropic docs, checks `LLM_MODEL` + `SMS_AGENT_MODEL` against current supported models, **auto-updates `config.py`** if either is deprecated, and gives exact DO env var + git steps to complete the update |
| `scs-quarterly-dependency-audit` | Quarterly — Jan/Apr/Jul/Oct 1 at 9am | Reads `requirements.txt` + `package.json`, checks key packages (fastapi, stripe, anthropic, twilio, react, vite, etc.) for outdated versions and CVEs, delivers a prioritized update list with pip/npm commands |
| `scs-monthly-infrastructure-check` | Monthly — 1st of month at 9am | Reminds Ryan to verify DO DB backups, Twilio balance (>$20 threshold), and SendGrid bounce/spam rates |
| `scs-annual-maintenance-reminder` | Annually — Jan 1 at 9am | Walks through JWT/SECRET key rotation, domain renewal, SSL cert check, Stripe price ID review, and CSA template review |

**LLM model check detail:** The quarterly task is the most critical — a deprecated model string causes silent "Error" status on all contact form submissions (customers get no reply). The task auto-patches `config.py` but Ryan still needs to update the DO env vars and redeploy. After running, watch for `LLM model validated OK` in the DigitalOcean Runtime Logs.

**First-run tip:** Click **Run now** on `scs-quarterly-llm-model-check` once from the Cowork Scheduled sidebar to pre-approve the web fetch tool, so future runs don't pause on permission prompts.

---

## 24. Build Roadmap

### Completed This Session (2026-05-31 session 2)
1. ✅ **Recurring appointments UI** — enhanced the existing Recurring Series tab: expandable rows, edit modal, appointment history, Generate Now button. Full CRUD + history in `AppointmentsPage.jsx`.
2. ✅ **Demo page polish** — `marketing-site/demo.html` fully polished: contact widget iframe auto-resize (ResizeObserver added to `embed.py`), all-screenshot 2x2 notification cards, 2x2 real-flow panels (emergency + kickoff), unified card titles, green badge, no em dashes. Ready for first demo calls pending A6.5 readiness test.
3. ✅ **Action plan A6.5** — end-to-end demo readiness test checklist added to `docs/action-plan-gtm-and-booking-widget.md`, triggered by CSA finalization.
4. ✅ **AI model selection guide** — added to Section 22 + per-item tags in Platform Capability Checklist.docx and SCS Platform Roadmap.docx.

### Next Session Priorities
1. ✅ **Test on-call rotation + override** -- DONE 2026-05-29.
2. ✅ **Recurring appointments UI** -- DONE 2026-05-31.
3. ✅ **Build self-scheduling booking widget** -- DONE 2026-05-30 (Phase 1 internal-only).
4. ✅ **Demo-page polish** -- DONE 2026-05-31.
5. ✅ **Platform rebrand to Launchpad** -- DONE 2026-06-01. Branding applied across all files; CSA v3 sent to Anjali Sareen for review.
6. **Screenshot refresh** -- populate Launchpad Demo tenant with appointments, retake all notification + flow screenshots, update demo page. Do while waiting for CSA review.
7. **A6.5 end-to-end demo readiness test** -- trigger: CSA attorney review complete + screenshots updated. Gate before first live prospect demo call.
8. **Start outreach (Track A)** -- prospect tracker loaded, templates ready. Begin cold email now; CSA review does not need to be complete to start outreach, only to sign.

### Pending Tests (High Priority -- before first client goes live)
- **Recurring appointments end-to-end** -- ⚠️ HIGH PRIORITY. UI and backend built (2026-05-31) but never tested end-to-end. Must confirm: create schedule → generate instances → appointments appear in feed → notifications fire correctly → disabling schedule stops generation. Run during A6.5 test.
- **Review requests** -- ✅ Confirmed working (2026-06-01). Tech replies YES to complete prompt, review request SMS fires and link works. NOTE: demo tenant Google Review URL is set to `https://www.spacecoaststudios.com` (placeholder). Must set a real Google Review URL on the demo tenant before any prospect demo, and on every new client tenant at onboarding. Set via dashboard Settings → Google Review URL.

### Roadmap (later)
- **Plan enforcement (service type + technician caps)** -- Triggered by first paying client. The 5 service type / 5 technician Starter cap and Pro unlimited are marketing/CSA commitments but not currently enforced in backend code. Add server-side validation on service and technician create endpoints that checks the business plan and rejects if over limit.
- **Platform-admin activity log (cross-tenant)** — platform-admin-only view of activity across all businesses (lead submissions, bookings, SMS sent/received, notification fires, errors) with tenant/date filters. Backend already logs notifications (`NotificationLog`) + SMS conversations; this surfaces them in one searchable screen.
- Visual calendar view (day/week/month) in dashboard
- Customer portal (magic link login, view/reschedule)
- Usage/analytics dashboard across tenants
- Emergency contact form routing (wire urgency detection to on-call dispatch)
- Notification template text audit and improvement
- Custom URL shortener for review links
- Quote / estimate workflow (request → estimate → quote → approve → schedule) — makes estimate-first trades (tree, pressure washing, roofing) a great fit

### Blocked / Pending
- **CSA attorney review** -- CSA v5 + Founding Client Pricing Addendum sent to Anjali Sareen (Uncommon Counsel) 2026-06-02 as Word files. Anjali out week of June 9; redline expected week of June 15. Also asked about Schedule A amendment cost if pricing structure changes. Must be reviewed before first client signs. Unblocks A6.5 demo readiness test.

### Pre-Client Business Operations Checklist
These items must be resolved before the first paying client goes live. None block cold outreach or demos.

- **Find an accountant** -- No accountant currently. Need a Florida CPA or bookkeeper familiar with SaaS/tech small business. Priority questions: (1) Is Launchpad subject to Florida sales tax? (2) Quarterly estimated tax setup. (3) General bookkeeping setup. Find before first client invoice is issued.
- **Florida SaaS sales tax** -- Florida taxes some software/technology services; SaaS classification is nuanced. Do not collect or not collect from first client until an accountant confirms the obligation. Do not assume either way.
- **Brevard County local business tax receipt** -- Florida has no statewide business license but Brevard County requires a local business tax receipt. Obtain before first client goes live. Typically straightforward and low cost.
- **Update LLC industry in Tailor Brands** -- Currently set to "Graphic Design" from original setup. Should be updated to "SaaS." Cosmetic (Tailor Brands internal only, not a government filing) but worth correcting for accurate recommendations.
- **Screenshot refresh** -- populate Launchpad Demo tenant with appointments, retake all notification + flow panel screenshots, update demo page images. Do while waiting for CSA review.

### Business Development
- Founding client outreach — templates ready, advised to start now (don't wait for A2P)
- Each new client needs their own A2P Brand + Campaign registration — submit Day 1 of onboarding
- **Action plan:** `docs/action-plan-gtm-and-booking-widget.md` — two parallel tracks: (1) cold-local + online/inbound outreach to land a founding **Starter** client (no warm network), (2) build the **self-scheduling booking widget**, v1 scope = **Phase 1 internal-only** (public slug-scoped endpoints + embeddable UI reusing the existing availability engine; Google/Outlook sync deferred to Phase 2/3). Awaiting Ryan's notes on the plan before starting the widget build.

### Nice to Have (later)
- Customer portal
- Usage/analytics dashboard across tenants
- **Notification template text audit** — review and improve all SMS/email templates (confirmation, reminder, OTW, kickoff, day-complete, review request). User noted templates could be "spruced up." Covers contact form AI responder copy too.
- **Custom URL shortener** — branded short domain per client (e.g. hvac.app) for review links and schedule URLs. Low priority for now; schedule token already shortened to 16 chars. Most relevant for Google Review SMS where URL is customer-facing.
- **Voicemail + AI response** (HIGH INTEREST -- candidate for "Coming Soon" on marketing site) — Client keeps existing business number, forwards to Twilio. Twilio records voicemail, Whisper transcribes, Claude generates SMS reply to caller, dashboard logs the full call/transcript/response thread. Requires TwiML call handling as a new capability layer. Cost: ~$0.04/call with Whisper (vs ~$0.23 with Twilio native transcription -- Whisper strongly preferred for both cost and accuracy). See cost estimate from 2026-06-01 session.
- **Promotional/re-engagement SMS campaigns** — Scheduled seasonal SMS to past customer lists (HVAC tune-up, pool holiday specials, etc.). Requires A2P MIXED campaign (new campaign registration; brand stays); marketing opt-in mechanism in platform; opt-in UI on contact form. Both marketing-opt-in UX and A2P re-registration needed before launch.

---

## 25. A2P 10DLC Compliance

### Current Status (as of May 2026)
**Campaign is APPROVED** (CUSTOMER_CARE use case). Do not change the consent flow without re-submitting to TCR — the live form must match the approved description exactly.

### Rejection History (resolved)
Rejected 5 times for "issues verifying the CTA." Ultimately approved with an **optional** checkbox and explicit "not required" language — this satisfies carriers that SMS consent is not a condition of service.

### Approved Consent Implementation
The campaign was approved with the following consent flow — **do not change any of this without updating the TCR registration**:
- Checkbox is **optional** — form submits whether or not it is checked
- Exact consent label text on form: `(Optional) I agree to receive SMS messages from [Business Name], including appointment confirmations, reminders, and service-related notifications. Msg & data rates may apply. Reply STOP to opt out at any time. Reply HELP for help. SMS consent is not required to submit this form or receive service.`
- CTA URL on file: `https://spacecoaststudios.com/#contact`
- The embed form at `/embed/{slug}/contact` uses identical consent language — **both forms must stay in sync**
- Backend behavior: `sms_consent` boolean stored on every `ContactSubmission`. SMS is only sent when `sms_consent = true`

### What Would Require a TCR Re-submission
- Changing the consent language (even minor wording changes)
- Changing the CTA URL
- Adding a new use case (e.g. marketing/promotional SMS — currently CUSTOMER_CARE only)

### Approved Campaign Details (Twilio — verified May 2026)
- Use case: `CUSTOMER_CARE`
- Opt-in keywords: START, YES
- Opt-out keywords: STOP, STOPALL, UNSUBSCRIBE, CANCEL, END, QUIT, REVOKE, OPTOUT
- Help keywords: HELP, INFO
- Embedded links: Yes | Embedded phone numbers: Yes | Age-gated: No
- **Important:** Each CLIENT business needs their own Brand + Campaign registration. SCS's registration covers SCS itself only. Client registrations are submitted Day 1 of their onboarding.

### Per-Client A2P Setup Checklist
1. Purchase local number in client's area code (Twilio Console)
2. Create Messaging Service, add number to sender pool
3. Register Brand (EIN, business info) → wait for approval
4. Create Campaign (Mixed or Notifications) linked to Messaging Service
5. **Register phone number to Campaign** (separate from sender pool — this step is easy to skip)
6. Configure inbound webhook on the **phone number itself** (not just the Messaging Service):
   `https://api.spacecoaststudios.com/webhook/sms/inbound` (POST)
7. Set `twilio_phone_number` on Business record (E.164 format)

---

## 26. Client Services Agreement

**Files:** `Test Project/SCS-Client-Services-Agreement-Template.docx` (and `.pdf`) + `Test Project/SCS-Founding-Client-Pricing-Addendum.docx`

**Founding Client Pricing Addendum:** A separate signed addendum for the 5 founding clients. Supersedes Schedule A pricing for the promotional period. Key terms: $497/$99 (Starter) or $997/$199 (Pro) for months 1-3, then auto-transition to standard rates ($249/$399/mo). 14-day written notice required before the transition date -- calendar this at onboarding (~2.5 months after go-live). Non-transferable, one-time use, capped at 5 clients. Both the CSA and this addendum must be signed for founding clients.

**File:** `Test Project/SCS-Client-Services-Agreement-Template.docx` (and `.pdf`)

**Version:** v5 (current -- send this one). 14 sections:
1. Services, 2. Fees & Payment, 3. Term, 4. Client Responsibilities, 5. Termination, 6. IP, 7. Confidentiality, 8. Support, 9. Limitation of Liability, 10. Indemnification, 11. Warranties, **12. AI Services** (NEW), 13. Governing Law, 14. General Provisions

**Section 12 — AI Services** covers: AI-powered features, no guarantee of accuracy, automated nature (no human agent), client configuration responsibility, third-party AI providers (Anthropic), TCPA indemnification, 15-day notice for material AI changes.

**Section 5.4 survival clause:** Sections 6, 7, 9, 10, 12, and 13 survive termination.

**Status:** CSA v5 and Founding Client Pricing Addendum sent to Anjali Sareen (Uncommon Counsel) on 2026-06-02 as Word (.docx) files. Anjali is out the week of June 9; review expected back the week of June 15, 2026. Ryan also asked about the cost to review Schedule A if pricing structure changes (one tier vs. Starter/Pro). Awaiting engagement letter from her assistant. **The CSA must be attorney-reviewed before the first client signs.**

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
- **Never run `git add`/`git commit` from bash** -- the Linux sandbox mounts a Windows filesystem. Git lock files created in bash cannot be removed from bash (`Operation not permitted`), breaking all subsequent commits in the session. Give Ryan the commands to run in his terminal instead.
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

### Features Built by Session

**2026-05-31 (session 2 — recurring UI + demo page polish):**
- **Recurring appointments dashboard UI** — enhanced `AppointmentsPage.jsx` Recurring Series tab: clickable expandable rows revealing address, notes, start/end dates; Edit modal for frequency, day/time, tech, end date, address, notes; appointment history panel showing upcoming (next 5) and past (last 5) per schedule loaded alongside schedules; "Generate appointments now" button triggering `POST /api/recurring/{id}/generate` with a toast. `generateRecurringSchedule` added to `api.js` imports. No backend changes needed.
- **AI model selection guide** — added to CLAUDE.md Section 22 with Haiku/Sonnet/Opus decision rules; Platform Capability Checklist.docx and SCS Platform Roadmap.docx updated with per-item model tags on all AI features; roadmap gains a callout box with the full guide.
- **Action plan A6.5** — end-to-end demo readiness test (10-step checklist) added to `docs/action-plan-gtm-and-booking-widget.md` as a gate before sending the demo link to any prospect, triggered by CSA attorney sign-off.
- **Demo page major polish** (`marketing-site/demo.html`):
  - Contact widget iframe auto-resize: `ResizeObserver` + `scs_contact_resize` postMessage added to `backend/app/routers/embed.py`; demo page listener added. Contact iframe starting height raised to 900px.
  - Badge changed from orange to green; header reworded to remove "not screenshots" (since screenshots are used); copy updated to "your website / your dashboard."
  - All 4 notification overview cards replaced with real screenshots: `Customer Appointment Confirmation Text.png`, `Reminder Text.png`, `Customer on the way text.png`, `Customer Review Request.png`. Fixed 2-column 2x2 grid.
  - "See the Real Flows" 2x2 panels: Emergency AI Dispatch Flow (`Emergency Text Thread.jpg`) + Emergency Tech Alert (`Emergency Text Tech Message.png`) on top row; Morning Kickoff (`Tech Daily Kickoff thread 1.png`) + Full OTW Day Cycle (`Tech Daily Kickoff thread 2.png`) on bottom row. All full natural height, rounded corners.
  - Section 4 redesigned: morning kickoff SMS screenshot (`Tech Kickoff Thread with schedule link.png`) + schedule page mockup side by side.
  - Unified card titles across all cards: `0.9rem`, bold, dark navy, centered, no emojis, no uppercase.
  - Screenshot cards: `object-fit:contain; background:#111827; height:220px` for even card heights without cropping.
  - Em dashes removed throughout. Saved as standing memory note.
- **Files committed**: `AppointmentsPage.jsx`, `embed.py`, `demo.html`, all screenshot images.

**2026-05-31 (outreach assets finalized — non-code):**
- **Cold-email sequence revised** (`SCS Cold Email Sequence.docx`, Test Project root): demo CTA now "try the booking and contact widgets your customers would actually use"; removed the "90-second demo" line; every email's opt-out reworded to natural language with a CAN-SPAM **mailing-address footer** (`{{Mailing_Address}}` placeholder); Email #2 founding offer is now a **`{{Founding_Offer}}` merge field** (Starter vs Pro, chosen per prospect); added a full **15-minute demo-call script** (prospect drives the demo page themselves, then Ryan screen-shares the dashboard: Contacts queue → SMS Conversations → the created Appointment — there is no "notification log" screen).
- **Action plan A6** (`docs/action-plan-gtm-and-booking-widget.md`) rewritten to match the new screen-share demo flow + the demo-page-polish gate.
- **Roadmap** (`SCS Platform Roadmap.docx` + this file): demo-page polish reframed as a **pre-demo prerequisite**; added **platform-admin cross-tenant activity log** to Later/Growth.
- **Fixed a broken working-tree file:** `frontend/dashboard/src/pages/AppointmentsPage.jsx` had a truncated/unclosed edit (missing closing `</div>)}`, would have failed the build); reverted via `git checkout --` after clearing a stale `.git/index.lock`. No intended changes lost.
- Outreach is otherwise ready to send pending Ryan filling `{{Your_Phone}}` + `{{Mailing_Address}}` and the demo-page polish pass.


**2026-06-01 (competitive positioning strategy + roadmap additions):**
- **Competitive positioning reframe** -- Launchpad repositioned as the customer-facing communication layer, complementary to (not competing with) Jobber/Housecall Pro/other FSM tools. Those platforms are back-office (invoicing, job costing, quoting); Launchpad is the customer front door (AI contact response, SMS booking, OTW flow, review requests, emergency dispatch). Positioning angle: "Works alongside whatever tool you already use." Invoicing explicitly de-prioritized.
- **Pricing strategy** -- One-tier simplification under consideration (Starter/Pro split adds friction for a complementary tool). Multiple locations = add-on discount, not a tier feature. No pricing changes before first prospect conversations (cold emails going out).
- **Voicemail + AI response added to roadmap (HIGH INTEREST)** -- Client keeps existing number, forwards to Twilio. Twilio records voicemail; Whisper transcribes; Claude generates SMS reply; dashboard logs full thread. Whisper preferred (~$0.04/call vs ~$0.23 with Twilio transcription). "Coming Soon" candidate for marketing site once fleshed out. Do NOT promise to prospects until built.
- **Promotional/re-engagement SMS added to roadmap** -- Seasonal SMS to past customer lists (HVAC tune-up, pool holiday specials). Requires A2P MIXED campaign (new campaign, brand stays) + marketing opt-in mechanism. A2P update: edit existing campaign to change use case type generally requires a new campaign submission; ~2-4 week approval. Hold off on demo campaign update until feature is near-built.
- **Cold email reframe notes** -- Emails are already well-targeted on customer communication pain. Two suggested updates: (1) "booking & instant-response systems" in the core opener could be tightened to "automated customer communication system"; (2) demo call script (13-15 min mark) should add: "If you're already using Jobber or Housecall Pro for invoicing, this runs alongside it -- it's the customer communication layer those tools don't have."
- **A2P re-engagement guidance** -- Changing use case from CUSTOMER_CARE to MIXED requires a new campaign submission (~2-4 weeks), not an edit. Brand registration stays. Hold off on updating demo Twilio campaign until re-engagement feature is near-ready.

**2026-06-01 (Launchpad rebrand + CSA v2/v3 + attorney engagement):**
- **Attorney selected:** Anjali Sareen, Uncommon Counsel (Altamonte Springs, FL). Licensed in FL/NY/CA, AIGP-certified, specializes in SaaS contracts and AI law. Flat fee $1,050 for initial review + redline. Ryan sending v3 CSA today.
- **CSA v2** -- fixed three issues found in audit: (1) Section 12.5 wrong AI provider "OpenAI" changed to "Anthropic, PBC"; (2) Schedule A pricing updated to match Stripe ($1,997/$249 Starter, $2,997/$399 Pro); (3) name corrected from "Ryan Usser" to "Ryan Ussery" throughout.
- **CSA v3** -- added "Launchpad" as the platform brand name in Section 1.1 ("branded as 'Launchpad'") and Schedule A title updated to "SCHEDULE A: LAUNCHPAD SERVICES AND PRICING."
- **Three questions sent to Anjali:** (1) 6-month initial term -- marketing copy "no long contracts" removed but flagging for her awareness; (2) "Launchpad" platform name -- is v3 language sufficient or should it be strengthened?; (3) SMS consent text says "Space Coast Studios" per A2P approval -- if product is "Launchpad by SCS," does consent need updating? Would that require TCR re-submission?
- **Platform rebranded as Launchpad** (product name; Space Coast Studios LLC remains company/legal entity; no DBA filed):
  - `marketing-site/index.html` -- title, meta, hero copy, nav, footer updated. "Launchpad by Space Coast Studios" in footer; "Launchpad" in headlines.
  - `marketing-site/booking-demo.html`, `demo.html`, `privacy.html`, `terms.html` -- all updated.
  - `frontend/dashboard/src/components/Layout.jsx` -- platform admin header now shows "Launchpad."
  - `frontend/dashboard/src/pages/` -- WelcomePage, SetupPage, ForgotPasswordPage, SetPasswordPage: "Welcome to Space Coast Studios" → "Welcome to Launchpad."
  - `backend/app/routers/auth.py` -- password reset email subject/body updated.
  - `backend/app/routers/billing.py` -- welcome email subject/body updated.
  - `CLAUDE.md` Section 1 -- added platform branding note; corrected Ryan's last name.
  - `README.md` -- title updated to "Launchpad by Space Coast Studios."
  - SMS consent text intentionally left as "Space Coast Studios" -- A2P approved language, cannot change without TCR re-submission.
- **Marketing site em dashes removed** -- all 31 em dashes across `index.html` replaced with contextually appropriate punctuation.
- **Marketing copy updated** -- "no long contracts or complicated onboarding" changed to "No complicated onboarding." (removed the contract duration claim to match the 6-month initial term in the CSA).
- **Demo tenant renamed** -- "Space Coast Studios Demo" updated to "Launchpad Demo" via dashboard Settings. Widget headers now show the correct brand.
- **Action plan updated** -- `docs/action-plan-gtm-and-booking-widget.md` reflects current status, Track B marked complete, A6.5 updated with screenshot pre-test checklist.
- **Next steps:** populate Launchpad Demo with appointments for screenshot refresh; await Anjali's redline; then run A6.5 end-to-end test; then first prospect demo call.
- **Files committed:** `CLAUDE.md`, `README.md`, `marketing-site/index.html`, `marketing-site/booking-demo.html`, `marketing-site/demo.html`, `marketing-site/privacy.html`, `marketing-site/terms.html`, `frontend/dashboard/src/components/Layout.jsx`, `frontend/dashboard/src/pages/WelcomePage.jsx`, `frontend/dashboard/src/pages/SetupPage.jsx`, `frontend/dashboard/src/pages/ForgotPasswordPage.jsx`, `frontend/dashboard/src/pages/SetPasswordPage.jsx`, `backend/app/routers/auth.py`, `backend/app/routers/billing.py`. CSA v2 and v3 saved to Test Project/ (outside repo).

**2026-05-30 (automated CLAUDE.md context-sync run — no code changes):**
- Scheduled daily maintenance run. Reviewed `git log` (HEAD `3b3b0bb`, 20:03 today): today's GTM groundwork (109-prospect tracker, competitor battlecard, 5-touch cold-email sequence) and booking widget Phase 1 (shipped + tested) are already captured in this log and reflected in Sections 21–26. No new commits since the last update — nothing to reclassify in the capability/roadmap/A2P/CSA sections.
- **Flag for Ryan:** an uncommitted, apparently-truncated edit to `frontend/dashboard/src/pages/AppointmentsPage.jsx` is sitting in the working tree (closing `</div>)}` removed, no trailing newline — looks like a stray/broken edit that would fail the build). Left untouched (this context task makes no code changes). Recommend reverting: `git checkout -- frontend/dashboard/src/pages/AppointmentsPage.jsx`.
- **Commit note:** per the git-workflow rule atop this file, the sandbox cannot run git (a stale `.git/index.lock` is present and unremovable here), so this CLAUDE.md update must be committed by Ryan from his terminal.

**2026-05-30 (GTM / Track A groundwork — sales assets, non-code):**
- **Prospect tracker expanded + scored** — `SCS Prospect Tracker.xlsx` (and a working copy `SCS Prospect Tracker Updated.xlsx`) in the Test Project root now holds **109 prospects** across 6 trade tabs: HVAC/Landscaping/Roofing (original 55 on the `Prospects` tab) + **Plumbing (13), Septic (14), Pool Service (19), House Cleaning (8)**; Tree Service + Pressure Washing tabs exist but intentionally empty (held until the quote/estimate workflow ships). Every prospect carries owner/email/website/GBP rating+reviews/Response-Gap notes, plus a computed **Priority** (57 High / 27 Medium / 25 Low, color-coded) and **Next Action**. Dashboard tab aggregates counts across all trade sheets.
- **Scoring logic:** High = clear response gap + fit ≥4 (or a low-rating-but-busy "response-gap signal"); DIY-tool shops (Housecall Pro/Jobber/etc.) auto-set Low "skip/example"; roofing dropped to Low (estimate-first). Standouts: **Pool Service 15/19 High** (strongest founding pool), ARK Plumbing & Septic flagged as a "broken ServiceTitan" swoop-in.
- **Competitor battlecard** — `SCS Competitor Comparison.xlsx` (Test Project root): side-by-side matrix of ServiceTitan, Housecall Pro, Jobber, Workiz, Service Fusion + SCS across ~19 data points, with **web-verified pricing (May 2026)** and a Notes/Positioning tab. Three positioning wedges: **done-for-you vs DIY, AI-first (included not add-on), and local.** Includes objection scripts.
- **Cold email sequence** — `SCS Cold Email Sequence.docx` (Test Project root): core 3-email cadence (opener → outcome+founding offer → breakup) + **5 trade-specific Email #1 variants** (HVAC, Pool, Plumbing, Septic, House Cleaning) + "already have a system" rebuttal + phone/voicemail script. CAN-SPAM compliant; merge-field driven.
- **New trades fact-checked** as plentiful in Brevard (web search): tree, pool, pressure washing, septic, house cleaning — all confirmed. Pool service + house cleaning flagged as best recurring-revenue fits (drove elevating the Recurring UI to top build priority).
- All four files live in the Test Project root (outside the repo) — saved on Ryan's computer, not part of git pushes.


**2026-06-02 (escalation alerts + on-call bug fixes):**
- **Emergency dispatch failure root cause:** Investigated via code review — dispatch failed because the weekly rolling rotation had no entry for today (on-call config was in day_of_week mode with no Tuesday entry, and no fallback phone configured). The dispatch logic does NOT check appointment status (en_route/scheduled) — only the rotation config. User hypothesis was incorrect.
- **Escalated SMS conversation:** Confirmed the conversation WAS recorded. It appeared in the Escalated tab (not default Active tab) because `convo.status = "escalated"` is always set when `emergency_dispatch` tool fires, regardless of dispatch success.
- **On-call banner bug fixed** (`OnCallPage.jsx`): The "No on-call tech assigned" banner was always showing for weekly rolling rotations. Root cause: the `activeTech` local computation returned `null` for the `weekly_rolling` branch. Fixed by calling `getCurrentOnCall(businessId)` alongside `getOnCallConfig` at load time and using the server-computed result. Banner now handles rotation/override/fallback states correctly.
- **Week position UI improved** (`OnCallPage.jsx`): Replaced the 0-indexed number input ("0 = Week 1") with a "Week in Rotation" dropdown showing "Week 1" through "Week 8". Display label changed from "Week position N" to "Week N". Weekly rolling cycles automatically via modulo (4 techs → Week 5 = Week 1).
- **Escalation alerts built** (`models/oncall.py`, `main.py`, `routers/oncall.py`, `services/notifications.py`, `services/sms_agent.py`, `OnCallPage.jsx`): Three new fields on `oncall_configs` — `escalation_sms_phone`, `escalation_email`, `escalation_notify_oncall`. `send_escalation_alert()` added to `notifications.py` — fires all configured channels simultaneously, falls back to `fallback_phone` → `business.phone`. Wired into `sms_agent.py` for both `escalate_to_human` and `emergency_dispatch`. On-Call Settings page gains an "Escalation Alerts" section with SMS phone input, email input, and on-call tech toggle. Amber warning shows if no escalation contacts configured.
- **Files changed:** `frontend/dashboard/src/pages/OnCallPage.jsx`, `backend/app/models/oncall.py`, `backend/app/main.py`, `backend/app/routers/oncall.py`, `backend/app/services/notifications.py`, `backend/app/services/sms_agent.py`.

**2026-06-02 (daily health check + demo tenant name fix):**
- **Daily health check scheduled task** (`scs-daily-health-check`) created — runs 7am daily; checks site availability + response times for all 3 URLs, API functionality (auth, booking widget config, contact widget, scheduler), config.py model string sanity, and sends ntfy.sh push alert for Critical/High findings. Silent on clean runs. ntfy.sh channel: `scs-health-q8m3x5k2` (install ntfy app, subscribe to that topic). Task includes setup instructions on first run.
- **Demo tenant business name fixed** — `/embed/default/booking-config` was returning `"business_name":"Space Coast Studios Demo"` instead of `"Launchpad Demo"`. Root cause: the previous rename via the dashboard Businesses edit modal had a transient save failure (network/navigation issue); the code itself is correct. Fixed via direct API call (`PUT /api/businesses/1 {"name":"Launchpad Demo"}`). Verified: endpoint now returns correct name. No code changes needed.

**2026-05-30 (Cowork automated maintenance tasks):**
- Created 4 Cowork scheduled tasks covering all periodic maintenance items from Section 23:
  - `scs-quarterly-llm-model-check` — runs Jan/Apr/Jul/Oct 1 at 9am; fetches Anthropic docs, validates `LLM_MODEL` + `SMS_AGENT_MODEL`, auto-updates `config.py` if deprecated, provides DO env var + git instructions
  - `scs-quarterly-dependency-audit` — same quarterly schedule; checks key Python + npm packages for outdated versions and CVEs, delivers prioritized update list with commands
  - `scs-monthly-infrastructure-check` — runs 1st of every month at 9am; reminds Ryan to check DO DB backups, Twilio balance (>$20), SendGrid bounce/spam rates
  - `scs-annual-maintenance-reminder` — runs Jan 1 at 9am; covers JWT/SECRET key rotation, domain renewal, SSL cert, Stripe price ID review, CSA template review
- Task files stored at `C:\Users\Ryan\Documents\Claude\Scheduled\<task-id>\SKILL.md`
- Section 23 updated with full task table and first-run instructions

**2026-05-30 (self-scheduling booking widget — Phase 1, shipped + tested):**
- New public, slug-scoped endpoints in `routers/embed.py`: `GET /embed/{slug}/booking-config`, `GET /embed/{slug}/availability`, `POST /embed/{slug}/book`, and `GET /embed/{slug}/booking` (embeddable widget UI). Reuse `services/scheduling.get_available_slots` + `auto_assign_technician` + `send_confirmation`. Honeypot field + slot re-validation guard against spam/double-booking; the internal "Emergency Service" type is excluded from public booking.
- Widget UX: service → day → time → details → confirm; brand-colored; iframe-resize `postMessage`; "Book another" reset on the success screen.
- Embedded live into `marketing-site/demo.html` section 2 (pill flipped to Live) with an auto-resize listener.
- Tested end-to-end on the demo tenant: bookings create confirmed appointments with assigned tech + problem description, fire confirmation SMS/email, render correct local time, and consume capacity correctly (a slot drops off once all qualified techs are booked). New-customer creation + soft-deleted-skip verified.
- Files: `backend/app/routers/embed.py`, `marketing-site/demo.html`.

**2026-05-29 (on-call testing + emergency dispatch hardening):**
- **On-call timezone fix** — rotation (day-of-week + weekly-rolling) and the after-hours window now evaluate in business-local time (`business.timezone`) instead of UTC, in both `routers/oncall.py` and `services/oncall_notifier.py` via a new `_business_local_now()` helper. Previously returned the wrong tech in the evening once UTC passed midnight. Verified: Friday rotation correctly returns Friday's tech at 4:30 PM local.
- **On-call config save bug** — `OnCallPage.jsx` sent `rolling_start_date: ""` (empty string) in day-of-week mode → 422 on the PUT → "Failed to save settings." Now sends `null`.
- **Emergency dispatch phone normalization** — `dispatch_emergency` normalizes both from- and to-numbers to E.164, so a tech stored as bare 10-digit still gets the alert.
- **Emergency → appointment** — `emergency_dispatch` now creates an `emergency`-status appointment (dedicated "Emergency Service" type, on-call tech, scheduled now, no automated notifications). Excluded from reminder/OTW/kickoff scheduler jobs. Soft-deleted customers skipped in the phone lookup.
- **In-chat address capture** — the agent's `emergency_dispatch` tool gained a `service_address` field; the prompt instructs the AI to confirm/collect the service address before dispatching. Address flows into the tech alert SMS (new `Address:` line in the default emergency template) and into the appointment.
- **Dashboard** — `emergency` status renders a bold red badge, is selectable/filterable, and "Mark Complete" works on it (`AppointmentsPage.jsx`).
- **Customer-facing phone formatting** — new `app/utils/phone.py` `format_phone_display()` → `(321) 386-7604`, applied to SMS agent replies, contact responder (prompt + email + context block), and notification templates (`{{business_phone}}` + email footer). Tech emergency alert intentionally kept in E.164.
- **Testing** — on-call rotation/override + emergency dispatch fully tested end-to-end (see `docs/on-call-emergency-testing.md`).
- Files: `routers/oncall.py`, `services/oncall_notifier.py`, `services/scheduler.py`, `services/sms_agent.py`, `services/contact_responder.py`, `services/template_renderer.py`, `models/notification_template.py`, `utils/phone.py` (new), `frontend/dashboard/src/pages/OnCallPage.jsx`, `frontend/dashboard/src/pages/AppointmentsPage.jsx`.

**2026-05-26 (major dev day — 15 commits):**
- Customer form: split address into street/city/state/zip; fixed `[object Object]` rendering bug
- Timezone display fix; booking confirmation SMS now fires on appointment creation
- Phone numbers auto-normalized to E.164 before Twilio send
- Customer inline edit added to dashboard
- Email calendar buttons + SMS business name fix in template renderer
- Reminder scheduler overhauled: noon local time for next open business day, 30-min interval, idempotent
- Admin router with manual trigger endpoints (reminders, OTW prompts, OTW kickoffs)
- Developer Tools panel in Settings page
- Stripe billing fully configured: products + prices created, IDs in config and app.yaml
- README added with infrastructure overview, pricing, and Stripe config

**2026-05-27 (audit and polish):**
- Forgot-password flow (backend + frontend): `POST /api/auth/forgot-password`, `ForgotPasswordPage.jsx`
- `set-password` now returns JWT tokens for auto-login
- Platform admin impersonation: backend endpoint + `localStorage` stash/restore pattern + amber banner
- Noisy DB migration errors fixed (`ALTER TABLE ADD COLUMN IF NOT EXISTS`)
- First-login setup wizard (`/setup`, 3-step, per-step auto-save, `has_completed_setup` gate)
- `GET /api/businesses/me` — business admin self-service endpoint
- `PUT /api/businesses/{id}` opened to business admins (with protected field list)
- Full platform audit: marketing site cleanup (removed placeholder phone, fixed API_URL ordering, clarified founding offer renewal prices, fixed error email), README synced with all new features
- Documentation consolidated: all .md files merged into single CLAUDE.md, `HomeServices_Architecture_Plan.md` archived to `docs/archive/`, `SCS_PROJECT_CONTEXT.md` deleted
- Stripe prices verified: confirmed all four standard price IDs in README/billing.py match actual amounts in Stripe dashboard ($1,997 setup, $249/mo, $2,997 setup, $399/mo)
- Scheduled task `scs-context-update` updated: now targets CLAUDE.md (was SCS_PROJECT_CONTEXT.md), section references corrected, added limitation warning explaining it only captures git commits — non-code events (A2P status, attorney responses, client signups) require manual input
- End-of-session habit established: say "Update CLAUDE.md with everything that happened today" to capture the full session, or "Update CLAUDE.md — [specific event]" for non-code updates (e.g. A2P approved, client signed)

**2026-05-28 (problem description + tech schedule feature — Pass 1):**
- `Appointment` model: added `problem_description` (Text, nullable) and `media_urls` (JSONB, nullable). Migration in `run_migrations()`.
- `Technician` model: added `schedule_token` (String 64, unique, default=`secrets.token_urlsafe(48)`). Migration backfills existing techs.
- `NotificationLog` model: made `appointment_id` nullable (was NOT NULL); added `technician_id` FK (nullable). Needed for "no appointments today" kickoff variant.
- `ContactSubmission` model: added `problem_description` (Text, nullable). Schema + endpoint updated. Migration added.
- `AppointmentResponse` schema: added `problem_description`, `media_urls`, `recurring_schedule_id`.
- `ContactFormSubmit` / `ContactSubmissionResponse` schemas: added `problem_description`.
- New router: `GET /schedule/tech/{token}` — public mobile-first daily schedule page for a single tech. No login. Shows all today's appointments (time, service, customer first name, address link, problem description). Dynamic query — no nightly cron.
- `embed.py` contact form: added "Describe the problem" textarea (200 char max, live character counter with near-limit/at-limit color warnings). `problem_description` sent in payload to `/contact/submit`.
- `AppointmentsPage.jsx`: expandable table rows — clicking a row with detail data reveals address (Google Maps link), problem description (amber icon), notes. Added `ChevronDown/Up`, `MapPin`, `FileText`, `AlertCircle` icons.
- Morning kickoff overhaul (`scheduler.py` + `notifications.py`):
  - **Removed 7am floor** — early texts are fine.
  - **Trigger: 2 hours before first appointment** (±15 min window, prevents re-firing every run).
  - **Techs WITH appointments**: numbered daily summary showing time, service, customer first name, short address, truncated problem description (~50 chars). Public schedule page URL at bottom. "Reply YES when heading to stop 1."
  - **Techs WITHOUT appointments**: fires once between 7–8 AM local. "Good morning [Name]! No appointments scheduled for you today. Enjoy your day off! 🌴". Logged to `notification_logs` with `appointment_id=NULL` keyed to `technician_id` + today date.
  - New `_build_kickoff_body()` helper formats the multi-appointment message.
  - New `send_otw_morning_no_appointments()` function handles the no-jobs variant.

**2026-05-27 (automated daily check — end of day):**
- No new commits since session-close update. CLAUDE.md current. Date stamp updated.

### Pending Monitoring Items
- **A2P approval:** ✅ APPROVED (CUSTOMER_CARE use case). See Section 25 for full verified campaign details. No further action needed unless consent language or CTA URL changes.
- **Morning kickoff delivery:** Kickoff now fires 2 hours before first appointment (±15 min window), no time-of-day floor. Techs with no appointments get a "day off" text between 7–8 AM local. If a tech reports missing kickoff: check (1) appointment exists and is not cancelled/completed, (2) scheduler.py `_send_otw_morning_kickoffs` ran, (3) `notification_logs` for an existing `otw_morning_kickoff` entry. Use admin manual trigger to force-send.
- **Contact responder SMS — mostly resolved:** File corruption caused a SyntaxError on deploy (2026-05-29); fixed by rewrite. SMS now sends full content (480-char cap, full slot dates). Remaining item: set `twilio_phone_number` on demo business via Settings so inbound replies route to the AI booking agent.
- **Soft delete:** All three soft-delete models (`appointments`, `customers`, `contact_submissions`) use a `deleted_at` TIMESTAMP column (not a boolean — set to current UTC time on delete, `NULL` = active). Dashboard UI shows delete buttons with confirmation modal; records disappear from all list views and availability checks immediately. No hard-delete path — recovery requires direct DB access if needed.

---

**2026-05-29 (SMS booking agent — full end-to-end flow):**
- Contact form address fields (street, city, state, zip) added to model, schema, migration, embed form HTML, and JS payload (payload was missing — root cause of address never saving)
- Phone normalized to E.164 at contact form submission time so inbound Twilio webhook lookup matches
- SMS agent `_tool_create_booking` signature fixed (was missing `contact_submission` param — caused TypeError/hiccup on every booking attempt)
- Live DB lookup: inbound webhook now looks up most recent contact submission by phone on every reply and passes to agent — replaces unreliable conversation seeding approach
- Customer enrichment: after booking, customer record populated with email, address, city, state, zip from contact submission
- Timezone fix: slots displayed in business local timezone (was UTC); naive datetimes in create_booking treated as business local time, not UTC
- Duplicate confirmation SMS removed (agent reply handles confirmation naturally)
- SMS bookings set to `confirmed` status (was `pending`) so kickoff/OTW flows include them
- Mandatory check_availability on every agent turn (prevents booking stale slots)
- Initial slot offer reduced to exactly 2 (was 3) to reduce stale-slot risk
- `SMS_AGENT_MODEL` added to config (defaults to `claude-sonnet-4-6`); `LLM_MODEL` now only used by contact form responder
- Twilio Phone Number field added to Settings page (platform admin only) with save + confirmation
- `twilio_phone_number` added to `BusinessResponse` schema so field persists on page load
- Git workflow corrected: all git commands run by Ryan in his terminal, one per line

**2026-05-29 (contact responder SMS fixes + Twilio Settings UI):**
- Contact responder SMS cap increased 300 -> 480 chars (~3 segments); AI now instructed to keep SMS replies under 400 chars and include full dates in slot suggestions (e.g. "Friday, May 30 at 6:30 PM").
- File corruption issue resolved: Edit tool corrupts files containing multi-byte Unicode chars (bullets, em-dashes) in f-strings on the Windows filesystem mount. Workaround: use `.format()` string methods and write files via bash Python script, not the Edit/Write tools.
- `SettingsPage.jsx`: added Twilio Phone Number section (platform admin only). Shows Phone icon, E.164 input, Save button, green confirmation line. Required so platform admins can assign a Twilio number to a business without touching the DB directly.
- Git workflow corrected: Claude must NOT run git commands from bash. All `git add`/`git commit`/`git push` go to Ryan's terminal, one command per line.

**2026-05-28 (Pass 2 — technician UI, soft delete, contact responder fixes):**
- `85321e1` — **Edit Details modal** in AppointmentsPage: "Edit Details" option in 3-dot row menu opens a modal to set `problem_description`, address, technician, and notes directly from the dashboard. Added `problem_description` to `AppointmentUpdate` schema so PUT endpoint accepts it.
- `fab4375` — `schedule_token` added to `TechnicianResponse` schema (was missing; API wasn't returning it so frontend couldn't build schedule page URLs).
- `030ef7e` — **Schedule token shortened**: `token_urlsafe(12)` → 16-char token. Tech schedule URL drops from ~115 chars to ~66 chars (much cleaner in SMS). `run_migrations()` auto-regenerates any existing long tokens on deploy.
- `80bdb60` — Fix `customer.name` → `customer.full_name` in tech schedule page and morning kickoff SMS. `Customer` model has `first_name`/`last_name` columns with a `full_name` property — there is no `.name` field. Was causing 500 on the tech schedule page.
- `50744c3` — Tech SMS day-complete message now uses first name only (`tech.name.split()[0]`). "That's a wrap, Tyler!" not "That's a wrap, Tyler Durden!" Matches the casual tone of employee messages.
- `4ca79a0` — **Technician first/last name split in UI** (frontend-only). Form splits existing `name` on open, joins on save. Last name optional, first name required. Underlying model still stores a single `name` column.
- `9cf3d06` — **Soft delete** (appointments, customers, contact submissions):
  - Added `is_deleted` boolean (default `False`) to `Appointment`, `Customer`, `ContactSubmission` models. Migrations in `run_migrations()`.
  - All list endpoints + availability engine filter