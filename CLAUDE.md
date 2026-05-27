# Space Coast Studios — Platform Memory File

This file is the complete context reference for Claude (or any AI assistant) working on this codebase. It covers architecture, every feature built, all code patterns, deployment, and pending work. Drop it in the repo root and reference it at the start of any new session.

---

## What This Project Is

**Space Coast Studios** is a multi-tenant SaaS platform for home service businesses (HVAC, plumbing, landscaping, etc.) on the Space Coast of Florida. Space Coast Studios sells and operates the platform; each client business is a "tenant."

The platform provides:
- Online booking (self-scheduling widget + contact form)
- AI-powered contact form auto-responder (Claude / Anthropic API)
- Appointment management dashboard
- Automated SMS + email notifications (confirmations, reminders, OTW alerts, review requests)
- Technician dispatch and on-call routing
- Recurring appointment scheduling
- SMS conversation inbox
- Stripe-powered subscription billing with automatic tenant provisioning

**Owner:** Ryan (usserry@gmail.com) — Space Coast Studios LLC, Florida

---

## Infrastructure

| Component | Provider | URL |
|---|---|---|
| API / Backend | DigitalOcean App Platform | `https://api.spacecoaststudios.com` |
| Database | DigitalOcean Managed PostgreSQL 18 | NYC3, 1GB RAM / 10GB disk |
| Dashboard (frontend) | Netlify | `https://dashboard.spacecoaststudios.com` |
| Marketing Site | Netlify | `https://spacecoaststudios.com` |

- DNS is managed in **GoDaddy** — CNAME records point `api.*` to DO, `dashboard.*` and root to Netlify.
- The `.do/app.yaml` only defines the `api` service and the database. The frontend and marketing site are NOT in `app.yaml`.
- Auto-deploy on push to `main` for all three (DO and Netlify both watch the same repo).
- Backend runs as: `uvicorn app.main:app --host 0.0.0.0 --port 8080`

### Database Access (no UI console)
```bash
psql "postgresql://doadmin:PASSWORD@host.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
```
Get the full connection string from DO → Databases → spacecoast-db → Overview → Connection Details.

---

## Tech Stack

### Backend
- **Python 3.11** / **FastAPI** (async where needed, sync elsewhere)
- **SQLAlchemy 2.x** (ORM with `Mapped` / `mapped_column` syntax)
- **PostgreSQL 18** via `psycopg2`
- **APScheduler** (BackgroundScheduler, runs in-process)
- **Stripe Python SDK** (`stripe==11.1.0`)
- **Twilio** for SMS (A2P 10DLC)
- **SendGrid** for email
- **Anthropic Python SDK** for AI responses
- **bcrypt** for password hashing
- **PyJWT** for JWT tokens
- **pydantic-settings** for config (`app/config.py`)

### Frontend
- **React 18** + **Vite**
- **React Router v6** (file-based routes in `App.jsx`)
- **Tailwind CSS** (utility classes only — no custom config file)
- **lucide-react** for icons
- Deployed to Netlify; `netlify.toml` + `public/_redirects` handle SPA routing

### Marketing Site
- Static HTML, vanilla JS, no framework
- Stripe Checkout buttons wire directly to `POST /api/billing/checkout`
- Demo contact form submits to `POST /contact/submit?business_id=1` (hardcoded to platform business ID 1)

---

## Repository Structure

```
home-services-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Entry point: FastAPI app, run_migrations(), seed_defaults(), lifespan
│   │   ├── config.py                # Pydantic Settings — reads from env vars
│   │   ├── database.py              # SQLAlchemy engine, SessionLocal, Base, get_db()
│   │   ├── models/
│   │   │   ├── admin_user.py        # AdminUser — platform admins (business_id=NULL) and business admins
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
│   │   │   ├── contact.py           # Public contact form submission + AI responder
│   │   │   ├── embed.py             # Public booking widget endpoints
│   │   │   ├── calendar_links.py    # ICS file generation
│   │   │   ├── notification_templates.py
│   │   │   ├── oncall.py
│   │   │   ├── recurring.py
│   │   │   ├── services.py
│   │   │   ├── sms_webhook.py       # Twilio inbound SMS — OTW/complete flow
│   │   │   └── technicians.py
│   │   ├── services/
│   │   │   ├── scheduler.py         # APScheduler jobs
│   │   │   ├── notifications.py     # SMS (Twilio) + email (SendGrid) send functions
│   │   │   └── ai_responder.py      # Claude API integration for contact form AI
│   │   └── utils/
│   │       ├── auth.py              # JWT helpers, password hashing, FastAPI dependencies
│   │       └── ics.py               # ICS calendar file generator
│   ├── requirements.txt
│   └── .env.example
├── frontend/dashboard/
│   ├── src/
│   │   ├── App.jsx                  # Route definitions — protected + public routes
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── ForgotPasswordPage.jsx    # /forgot-password — request reset email
│   │   │   ├── SetPasswordPage.jsx       # /set-password?token=&mode=reset — set/reset password
│   │   │   ├── WelcomePage.jsx           # /welcome?session_id= — post-Stripe-checkout landing
│   │   │   ├── SetupPage.jsx             # /setup — first-login wizard (3 steps + done screen)
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── AppointmentsPage.jsx      # Sort options + 3-dot row menu
│   │   │   ├── CustomersPage.jsx
│   │   │   ├── ServicesPage.jsx
│   │   │   ├── TechniciansPage.jsx
│   │   │   ├── ContactsPage.jsx          # Contact form submission inbox + AI responder
│   │   │   ├── SMSConversationsPage.jsx
│   │   │   ├── NotificationTemplatesPage.jsx
│   │   │   ├── OnCallPage.jsx
│   │   │   ├── SettingsPage.jsx
│   │   │   ├── BillingPage.jsx           # Plan info (client) / tenant overview (platform admin)
│   │   │   ├── BusinessesPage.jsx        # Platform admin: all tenants + "Log in as" impersonation
│   │   │   └── OnboardingPage.jsx        # Platform admin: manual tenant provisioning
│   │   ├── components/
│   │   │   ├── Layout.jsx               # Sidebar nav + impersonation amber banner
│   │   │   └── RowMenu.jsx              # Reusable 3-dot dropdown (portal-based)
│   │   ├── hooks/
│   │   │   ├── useAuth.jsx              # Auth state, login, logout, impersonate, exitImpersonation
│   │   │   └── useBusinessContext.jsx   # Active business context for platform admins
│   │   └── services/
│   │       └── api.js                   # API client — all backend calls with JWT auth
│   ├── vite.config.js                   # Proxies /api → API root in dev
│   ├── netlify.toml
│   └── public/_redirects                # /* /index.html 200 (SPA fallback)
├── marketing-site/
│   ├── index.html                       # All-in-one marketing page
│   ├── booking-demo.html
│   ├── privacy.html
│   └── terms.html
├── docs/
│   └── founder-client-onboarding.md     # Manual provisioning guide for founding clients
├── README.md                            # Operations reference (API table, Stripe IDs, A2P checklist)
├── CLAUDE.md                            # This file
└── .do/app.yaml                         # DigitalOcean App Platform config (API + DB only)
```

---

## Environment Variables

Set on the **api component** in DigitalOcean App Platform. Sensitive values must be **Encrypted**.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (injected from DO managed DB) |
| `SECRET_KEY` | ✅ | App secret key |
| `JWT_SECRET_KEY` | ✅ | JWT signing key |
| `JWT_ALGORITHM` | — | Default: `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | — | Default: `60` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | — | Default: `30` |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | ✅ | Default Twilio sending number (E.164) |
| `SENDGRID_API_KEY` | ✅ | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | ✅ | Default sender address (`noreply@spacecoaststudios.com`) |
| `FROM_NAME` | — | Default sender name (`Space Coast Studios`) |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key for AI contact form responses |
| `STRIPE_SECRET_KEY` | ✅ | Stripe live secret key (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Stripe webhook signing secret (`whsec_...`) |
| `STRIPE_PRICE_STARTER_SETUP` | ✅ | Stripe price ID — Starter one-time setup ($1,997) |
| `STRIPE_PRICE_STARTER_MONTHLY` | ✅ | Stripe price ID — Starter monthly ($249/mo) |
| `STRIPE_PRICE_PRO_SETUP` | ✅ | Stripe price ID — Professional one-time setup ($2,997) |
| `STRIPE_PRICE_PRO_MONTHLY` | ✅ | Stripe price ID — Professional monthly ($399/mo) |
| `BASE_URL` | ✅ | `https://api.spacecoaststudios.com` |
| `ALLOWED_ORIGINS` | ✅ | CORS origins (comma-separated) |

---

## Database Migrations

**There is no Alembic.** Schema changes are handled by raw `ALTER TABLE IF NOT EXISTS` statements in `run_migrations()` in `main.py`, which runs on every startup.

Pattern:
```python
db.execute(text("ALTER TABLE businesses ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500)"))
```

Always use `IF NOT EXISTS` to make migrations idempotent — without it, you get PostgreSQL ERROR logs on every deploy once the column already exists.

---

## Auth System

### JWT Claims
```python
{
  "sub": user.id,              # AdminUser.id
  "username": user.username,
  "role": user.role,           # "admin", "platform_admin", etc.
  "business_id": user.business_id,    # None for platform admins
  "is_platform_admin": True/False,
  "type": "access" | "refresh",
  "exp": ...
}
```

Impersonation tokens include additional claims (ignored by the API, used only by the frontend):
```python
{
  ...standard claims...,
  "impersonating": True,
  "impersonated_by_id": platform_admin.id,
  "impersonated_by_name": platform_admin.username,
  "business_name": business.name,
}
```

### FastAPI Dependencies
- `get_current_user` — any authenticated user
- `get_platform_admin` — platform admin only (403 otherwise)
- `get_business_id_for_user(user, requested_id)` — platform admins pass explicit ID; business admins always get their own

### Password Reset Tokens
- `secrets.token_urlsafe(48)` stored in `AdminUser.password_reset_token`
- 72-hour expiry for new account setup (from Stripe checkout provisioning)
- 1-hour expiry for forgot-password resets
- Token is nulled out after successful use
- `set-password` returns `access_token` + `refresh_token` for auto-login (no redirect to login page)

### Impersonation Flow (localStorage)
```
Normal session:    localStorage.access_token = platform admin JWT
During impersonation:
  localStorage.platform_token = (stash of platform admin JWT)
  localStorage.access_token   = (impersonation JWT for target business)
Exit impersonation:
  localStorage.access_token   = platform_token (restored)
  localStorage.platform_token = (cleared)
```
`logout()` clears all three keys. The frontend `useAuth` hook manages all of this; the API is unaware of impersonation — it just sees a valid JWT for the business admin user.

---

## Multi-Tenancy

Every data model (Customer, Appointment, Technician, etc.) has a `business_id` foreign key. All queries filter by `business_id`.

**Platform admin** (`business_id = NULL` on their `AdminUser` record) can query any business by passing `?business_id=X` on API calls. The frontend `useBusinessContext` hook manages which business is currently "active" when a platform admin is browsing.

**Business admin** — `get_business_id_for_user()` ignores any passed `business_id` and always returns their own.

---

## Pricing

### Standard (Stripe Checkout — automatic provisioning)

| Plan | Setup | Monthly | Stripe Price IDs |
|---|---|---|---|
| Starter | $1,997 | $249/mo | See README.md → Stripe Product & Price IDs |
| Professional | $2,997 | $399/mo | See README.md → Stripe Product & Price IDs |

### Founding Client Offer (manual provisioning, introductory rate)

| Plan | Setup | Monthly (first 3 months) | Then |
|---|---|---|---|
| Starter | $497 | $99/mo | $249/mo |
| Professional | $997 | $199/mo | $399/mo |

### Test Plan
`POST /api/billing/checkout` with `{"plan": "test"}` → $1 one-time + $1/mo. Use a real card; refund immediately after testing.

---

## Stripe Billing Flow

1. Prospect clicks **Get Started** → marketing site calls `POST /api/billing/checkout`
2. Backend creates Stripe Checkout session (collects email, address, phone, "Business / DBA Name")
3. Stripe sends `checkout.session.completed` webhook → `_provision_tenant()`:
   - Creates `Business` record
   - Creates `AdminUser` (username = email, password unusable until set)
   - Generates 72-hour password-reset token
   - Sends welcome email with set-password link
4. Client sets password at `/set-password?token=...` → auto-logged in → redirected to `/setup` wizard
5. Wizard: 3 steps (Business Info → Look & Feel → AI & Notifications) + done screen
6. On wizard completion: `has_completed_setup = True` on Business record

Subscription lifecycle updates via webhooks:
- `customer.subscription.updated` → updates `subscription_status`, `subscription_period_end`
- `customer.subscription.deleted` → sets `subscription_status = "cancelled"`, `is_active = False`
- `invoice.payment_failed` → sets `subscription_status = "past_due"`

**Stripe publishable key** (safe to commit): `pk_live_51TM7kZ2MJMR8rAcZ2jSBcduwtelYsLikfR9OsPACEOypphYntZ1MmdpSK7lFdMb8egcatVty5vL5h4SiB2X7sc2n00HqCzzbqd`

---

## Notification System

### Events

| Event | Trigger | Channel |
|---|---|---|
| `confirmation` | Immediately on booking | SMS + email |
| `reminder_24h` | Daily 11am–1pm local → next open business day | SMS + email |
| `otw_tech_prompt` | 45–75 min before appointment | SMS to tech |
| `otw_customer` | Tech replies YES to OTW prompt | SMS to customer |
| `complete_prompt` | After OTW customer notification | SMS to tech |
| `review_request` | Tech replies YES to complete prompt | SMS to customer |
| `morning_kickoff` | After 7am local → tech's first job | SMS to tech |

### OTW / Complete Reply Flow

1. Scheduler fires `otw_tech_prompt` → tech: "Reply YES when leaving for [Customer]"
2. Tech replies YES → **inbound SMS webhook** (`/webhook/sms/inbound`) → customer gets "On The Way" SMS
3. Tech receives "Reply YES when job is complete"
4. Tech replies YES:
   - More appointments today → next job prompt sent
   - Last job → review request sent to customer + "Great work! That's a wrap!" to tech

### Deduplication
The `Notification` model logs every sent notification (`appointment_id`, `notification_type`, `sent_at`). All scheduler jobs check this log before sending to prevent duplicate notifications.

### Background Scheduler (APScheduler — runs in-process)

| Job | Schedule | Description |
|---|---|---|
| `send_reminders` | Every 30 min | 11am–1pm local window; reminds for next open business day |
| `send_otw_prompts` | Every 15 min | Texts techs for appointments in 45–75 min window |
| `send_morning_kickoffs` | Every 15 min | After 7am local — texts tech with first job details |
| `generate_recurring` | Daily 6am UTC | Pre-generates recurring appointment instances |

**Admin manual triggers** (bypass time windows, for testing):
- `POST /api/admin/trigger/reminders`
- `POST /api/admin/trigger/otw-prompts`
- `POST /api/admin/trigger/morning-kickoffs`
- `GET /api/admin/scheduler/status`

---

## Key Business Logic

### Availability Calculation
`GET /api/availability` — given a service type, date range, and optional technician, returns available time slots. Considers business hours, blocked times, existing appointments, and technician assignments.

### Recurring Schedules
Recurring schedule records define frequency (weekly, biweekly, monthly). The `generate_recurring` job pre-generates individual appointment records so they appear in the normal appointment feed. `deactivateRecurringSchedule` soft-deletes (sets `is_active=False`).

### On-Call Routing
`OnCallConfig` + `OnCallRotation` + `OnCallOverride`. The `/oncall/current` endpoint returns the currently on-call technician based on rotation schedule and any manual override. Used for after-hours call routing.

### AI Contact Form Responder
1. Contact form submission arrives at `POST /contact/submit`
2. AI generates a response via Anthropic API using the business's `ai_system_prompt` + `ai_agent_name`
3. If `ai_response_mode == "auto_send"` → response sent immediately
4. If `ai_response_mode == "draft_only"` → stored as draft; staff approves in Contact queue UI

---

## API Reference (Complete)

### Auth (`/api/auth/...`)

| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| `POST` | `/api/auth/login` | none | `{username, password}` → `{access_token, refresh_token}` |
| `POST` | `/api/auth/refresh` | none | `{refresh_token}` → new token pair |
| `POST` | `/api/auth/set-password` | none | `{token, password, confirm_password}` → `{access_token, refresh_token}`. Token nulled after use. Redirects new users to `/setup`, resets to `/`. |
| `POST` | `/api/auth/forgot-password` | none | `{email}` → always 200 (prevents enumeration). Sends 1-hr reset link if email exists and is active. |

### Businesses (`/api/businesses/...`)

| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| `GET` | `/api/businesses` | platform admin | Lists all with billing fields |
| `POST` | `/api/businesses` | platform admin | Create business |
| `GET` | `/api/businesses/me` | business admin | Get caller's own business |
| `GET` | `/api/businesses/{id}` | platform admin | Get by ID |
| `PUT` | `/api/businesses/{id}` | any JWT | Business admins can only update their own; cannot change `plan`, `is_active`, `is_demo`, Stripe fields |
| `POST` | `/api/businesses/{id}/impersonate` | platform admin | Returns 2-hr impersonation JWT for business's first active admin user |

### Billing (`/api/billing/...`)

| Method | Endpoint | Auth | Notes |
|---|---|---|---|
| `POST` | `/api/billing/checkout` | none | `{plan}` → `{url}` (Stripe Checkout URL) |
| `GET` | `/api/billing/checkout-session` | none | `?session_id=` → `{email}` (for welcome page) |
| `POST` | `/api/billing/webhook` | Stripe sig | Handles `checkout.session.completed`, subscription events, payment failures |
| `GET` | `/api/billing/subscription` | JWT | Current plan/status for active business |
| `POST` | `/api/billing/portal` | JWT | Create Stripe Customer Portal session → `{url}` |

### Appointments (`/api/appointments/...`)

| Method | Endpoint | Notes |
|---|---|---|
| `GET` | `/api/appointments` | `?sort=upcoming\|newest\|oldest` (default: upcoming); `?business_id=` |
| `POST` | `/api/appointments` | Create |
| `GET` | `/api/appointments/{id}` | Get by ID |
| `PUT` | `/api/appointments/{id}` | Update |
| `POST` | `/api/appointments/{id}/cancel` | Cancel |

### Other Endpoints (all require JWT)

- `GET/PUT /api/business-hours` — business hours by day
- `GET/POST/DELETE /api/blocked-times` — blocked time slots
- `GET/PUT /api/settings/{key}` — per-business settings key-value store
- `GET/POST/PUT/DELETE /api/customers`
- `GET/POST/PUT/DELETE /api/services`
- `GET/POST/PUT /api/technicians`
- `GET /api/availability`
- `GET/POST/PUT/DELETE /api/recurring`
- `POST /api/recurring/{id}/generate`
- `GET/PUT /api/oncall/config`
- `GET/POST/DELETE /api/oncall/rotation`
- `GET/POST/DELETE /api/oncall/override`
- `GET /api/oncall/current`
- `GET/PUT /api/contact-submissions/{id}`
- `POST /api/contact-submissions/{id}/respond` — trigger AI response
- `POST /api/contact-submissions/{id}/approve` — approve AI draft
- `POST /api/contact-submissions/{id}/manual-response`
- `GET/POST /api/sms-conversations`
- `POST /api/sms-conversations/{id}/close`
- `POST /api/sms-conversations/{id}/send`
- `GET/PUT /api/notification-templates`
- `POST /api/notification-templates/reset`

### Public Endpoints (no auth)
- `POST /contact/submit?business_id=` — contact form widget
- `GET /embed/...` — public booking widget data

### Admin / Notification Triggers (JWT required)
- `POST /api/admin/trigger/reminders`
- `POST /api/admin/trigger/otw-prompts`
- `POST /api/admin/trigger/morning-kickoffs`
- `GET /api/admin/scheduler/status`
- `POST /api/admin/appointments/{id}/resend-confirmation`
- `POST /api/admin/appointments/{id}/send-reminder`
- `POST /api/admin/appointments/{id}/send-review-request`

---

## Frontend Routing (`App.jsx`)

### Public Routes (no auth required)
- `/login` — `LoginPage`
- `/forgot-password` — `ForgotPasswordPage`
- `/set-password?token=&mode=reset` — `SetPasswordPage`
- `/welcome?session_id=` — `WelcomePage`
- `/setup` — `SetupPage` (first-login wizard; redirects to `/` if `has_completed_setup=true`)

### Protected Routes (JWT required, inside `<ProtectedRoute>` + `<BusinessProvider>`)
- `/` — `DashboardPage`
- `/appointments`, `/customers`, `/services`, `/technicians`
- `/contacts`, `/sms`, `/notification-templates`
- `/oncall`, `/settings`, `/billing`
- `/businesses` — `PlatformAdminRoute` only
- `/onboard` — `PlatformAdminRoute` only

---

## Frontend `api.js` Patterns

```javascript
// Dev: Vite proxies /api → localhost:8000
// Prod: direct to https://api.spacecoaststudios.com
const API_ROOT = isLocalhost ? '' : 'https://api.spacecoaststudios.com'

// All requests attach Bearer token from localStorage.access_token
// 401 response → clear tokens + redirect to /login

// Business-scoped calls accept optional businessId:
getCustomers(search = '', businessId = null)
// businessId is passed as ?business_id= query param
// Platform admins pass it explicitly; business admins omit it
```

---

## `useAuth` Hook

```javascript
const {
  user,                // { id, username, role, businessId, isPlatformAdmin, isImpersonating, impersonatedBizName }
  loading,             // true during initial token validation
  login,               // (username, password) → stores tokens, sets user
  logout,              // clears access_token, refresh_token, platform_token
  impersonate,         // (businessId) → stashes current token, sets impersonation JWT
  exitImpersonation,   // restores platform token
  isImpersonating,     // bool
  impersonatedBizName, // string — shown in amber banner
} = useAuth()
```

---

## First-Login Setup Wizard (`/setup`)

3-step wizard that runs after a new business admin sets their password for the first time.

- **Step 1 — Business Info:** name (with DBA hint), phone, website, address
- **Step 2 — Look & Feel:** brand color (color picker + hex input with live preview chip), logo URL
- **Step 3 — AI & Notifications:** AI persona name, Google Review URL

Each "Next" click saves the current step's data via `PUT /api/businesses/{id}`. "Skip for now" and "Skip setup" both call finish with `has_completed_setup: true`.

Done screen shows 4 shortcut cards: Add Services → `/services`, Add Technicians → `/technicians`, Customize Notifications → `/notification-templates`, Explore Dashboard → `/`.

If `has_completed_setup` is already `true` when the page loads, it immediately redirects to `/`. Platform admins also redirect to `/`.

---

## Impersonation (Platform Admin)

1. Platform admin clicks **Log in as** on `/businesses` page
2. Frontend calls `POST /api/businesses/{id}/impersonate`
3. Backend finds first active `AdminUser` for that business, mints a 2-hour JWT
4. Frontend stashes current token as `localStorage.platform_token`, sets new token as `localStorage.access_token`
5. User is navigated to `/` — they see the dashboard exactly as the business admin does
6. Amber banner appears: "Viewing as **[Business Name]** — changes you make affect this client's real data"
7. **Exit impersonation** button restores `platform_token` → `access_token`, clears `platform_token`, navigates to `/businesses`

The API does not enforce impersonation differently — the impersonation JWT is simply a valid JWT for the target business admin user. The extra impersonation claims in the JWT are for frontend display only.

---

## Twilio / SMS

### A2P 10DLC — Must complete before go-live
1. Purchase local number in client's area code
2. Create Messaging Service, add number to sender pool
3. Register Brand (EIN, business info) → wait for approval
4. Create Campaign (Mixed or Notifications use case) linked to Messaging Service
5. **Register phone number to campaign** (separate step from sender pool — easy to miss)
6. Configure inbound webhook on the **phone number itself**: `https://api.spacecoaststudios.com/webhook/sms/inbound` (POST)
7. Set `twilio_phone_number` on Business record (E.164 format)

### Phone Number Normalization
The DB may store numbers in various formats (10-digit, E.164). The backend uses multi-format `.in_()` lookups when matching inbound Twilio numbers to business records.

### Common Twilio Errors
- **30034** — number not registered to campaign
- **30024** — number in sender pool but not registered to campaign
- **"No HTTP Requests logged"** — inbound handler not configured at the number level (sender pool ≠ inbound routing)

---

## Known Issues / Watchlist

- **Morning kickoff not received:** The kickoff fires every 15 min but only triggers if the tech's first appointment is within 60 minutes AND after 7am local. If appointments are created after the lookahead window passes, or there's mid-deploy timing, the kickoff can be missed. Manual trigger: `POST /api/admin/trigger/morning-kickoffs`.
- **Contact queue / AI responder:** End-to-end testing not yet confirmed. Need to run a test lead through the full flow and verify AI response is generated and sent/drafted correctly.
- **Route optimization:** `route_optimization_enabled` flag exists on Business model and in the DB, but the actual geographic sorting logic is not built yet. Flag is there so the column is ready.

---

## Local Development

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

## Default Credentials (local / demo only)

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Platform admin (business_id = NULL) |

**Never use these in production.** Change immediately on any real deployment.

---

## Deployment Checklist (new client)

1. Client completes Stripe checkout → provisioned automatically
2. Welcome email sent with set-password link (72-hr expiry)
3. Client sets password → directed to setup wizard → completes in-dashboard setup
4. **You:** Complete A2P 10DLC (see above — takes 2–3 days minimum)
5. Set `twilio_phone_number` on Business record
6. Set business hours in Settings
7. Add service types and technicians in dashboard
8. Confirm Google Review URL is set (required for review requests)
9. Create test appointment → verify confirmation SMS + email
10. Test OTW flow: `POST /api/admin/trigger/otw-prompts` → confirm tech prompt arrives → reply YES → confirm customer SMS

---

## Stripe Webhook Events Handled

| Event | Action |
|---|---|
| `checkout.session.completed` | Provision tenant (Business + AdminUser + welcome email) |
| `customer.subscription.updated` | Update `subscription_status` and `subscription_period_end` |
| `customer.subscription.deleted` | Set `subscription_status = "cancelled"`, `is_active = False` |
| `invoice.payment_failed` | Set `subscription_status = "past_due"` |

Webhook URL: `https://api.spacecoaststudios.com/api/billing/webhook`
Webhook secret: stored in DO env as `STRIPE_WEBHOOK_SECRET`

---

## Marketing Site Notes

- All-in-one `index.html` — no framework, vanilla JS
- `API_URL` is declared at the top of the script block (before the checkout button handlers that use it)
- Checkout buttons have `data-checkout-plan="starter"` / `data-checkout-plan="professional"` attributes
- Demo contact form submits to `POST /contact/submit?business_id=1` (hardcoded — correct, this is the platform's own demo intake)
- Founding offer promo banner is shown on the pricing page — states renewal price ("then $249/mo", "then $399/mo")
- Error contact email: `hello@spacecoaststudios.com`

---

## Session History (work completed as of May 2026)

- Multi-tenant architecture with platform admin + per-business admin roles
- Full scheduling + availability engine (business hours, blocked times, technician assignment)
- Appointment management with sort options (upcoming / newest / oldest) + cancellation
- SMS + email notification system (confirmation, reminder, OTW, complete, review request, morning kickoff)
- OTW inbound SMS reply flow (tech YES → customer OTW → complete prompt → review request)
- AI contact form responder (auto-send and draft-only modes) via Anthropic API
- Stripe billing — full checkout → webhook → auto-provisioning flow
- Password reset (forgot-password flow with 1-hr token + email)
- Platform admin impersonation (stash/restore pattern, amber banner, 2-hr JWT)
- First-login setup wizard (3-step, per-step save, `has_completed_setup` gate)
- A2P 10DLC onboarding checklist (documented)
- Recurring appointments with daily auto-generation job
- On-call routing (rotation + manual override)
- Notification templates (per-business customization + reset to defaults)
- Per-appointment notification triggers (resend confirmation, send reminder, send review request)
- Database migration idempotency (`IF NOT EXISTS` on all `ALTER TABLE` statements)
- Marketing site audit fixes (removed placeholder phone number, fixed API_URL ordering, added renewal pricing clarity)
- README kept in sync with all features
