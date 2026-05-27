# Home Services Platform

Multi-tenant AI-powered scheduling, dispatch, and notifications platform built for Space Coast Studios.

---

## Table of Contents

1. [Infrastructure](#infrastructure)
2. [Repository Structure](#repository-structure)
3. [Environment Variables](#environment-variables)
4. [Stripe Billing](#stripe-billing)
5. [Client Onboarding — New Client Signup Flow](#client-onboarding--new-client-signup-flow)
6. [Client Onboarding — A2P 10DLC Checklist](#client-onboarding--a2p-10dlc-checklist)
7. [Backend Services](#backend-services)
8. [API Reference](#api-reference)
9. [Local Development](#local-development)
10. [Common Pitfalls](#common-pitfalls)

---

## Infrastructure

### Hosting

| Component | Provider | URL | Notes |
|---|---|---|---|
| **API / Backend** | DigitalOcean App Platform | `https://api.spacecoaststudios.com` | FastAPI, Python |
| **Database** | DigitalOcean Managed PostgreSQL 18 | `spacecoast-db` | NYC3, 1GB RAM / 10GB disk |
| **Dashboard (frontend)** | Netlify | `https://dashboard.spacecoaststudios.com` | React 18 + Vite, auto-deploys from `main` |
| **Marketing Site** | Netlify | `https://spacecoaststudios.com` | Static HTML, auto-deploys from `main` |

> The dashboard and marketing site are hosted on **Netlify**, not DigitalOcean.
> DNS for both is managed in **GoDaddy** with CNAME records pointing to Netlify.
> The `.do/app.yaml` file only reflects the `api` service and database.

### DNS (GoDaddy)

| Record | Type | Points To |
|---|---|---|
| `api.spacecoaststudios.com` | CNAME | DigitalOcean App Platform |
| `dashboard.spacecoaststudios.com` | CNAME | Netlify |
| `spacecoaststudios.com` | A / CNAME | Netlify |

### DigitalOcean Database Access

The managed PostgreSQL database does not have a query console in the DO UI. To run SQL:

```bash
psql "postgresql://doadmin:PASSWORD@host.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
```

Get the full connection string from **DigitalOcean → Databases → spacecoast-db → Overview → Connection Details**.

---

## Repository Structure

```
home-services-platform/
├── backend/                    # FastAPI backend (deployed to DigitalOcean)
│   ├── app/
│   │   ├── main.py             # App entry point, run_migrations(), startup
│   │   ├── config.py           # Settings (pydantic-settings, reads .env)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── business.py     # Business tenant model (incl. Stripe billing fields)
│   │   │   ├── admin_user.py   # Admin user model (incl. password reset fields)
│   │   │   └── ...
│   │   ├── routers/            # FastAPI route handlers
│   │   │   ├── billing.py      # Stripe checkout, webhook, portal, subscription
│   │   │   ├── businesses.py   # Business CRUD (platform admin only)
│   │   │   ├── auth.py         # Login, set-password
│   │   │   ├── appointments.py
│   │   │   ├── sms_webhook.py  # Twilio inbound SMS handler
│   │   │   └── ...
│   │   ├── services/           # Business logic (notifications, scheduler, AI)
│   │   └── utils/              # Auth helpers, ICS generator
│   ├── requirements.txt
│   └── .env.example
├── frontend/dashboard/         # React 18 + Vite dashboard (deployed to Netlify)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── AppointmentsPage.jsx  # Sort + 3-dot row menu
│   │   │   ├── CustomersPage.jsx     # 3-dot row menu
│   │   │   ├── TechniciansPage.jsx   # 3-dot row menu
│   │   │   ├── BillingPage.jsx       # Plan info (client) / tenant overview (platform admin)
│   │   │   ├── SetPasswordPage.jsx   # Token-based password setup (/set-password?token=)
│   │   │   ├── WelcomePage.jsx       # Post-checkout landing (/welcome?session_id=)
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── Layout.jsx            # Sidebar nav
│   │   │   ├── RowMenu.jsx           # Reusable 3-dot dropdown (portal-based)
│   │   │   └── ...
│   │   ├── services/api.js           # API client with JWT auth
│   │   └── hooks/                    # useAuth, useBusinessContext
│   ├── netlify.toml
│   └── public/_redirects             # SPA fallback routing
├── marketing-site/             # Static HTML marketing site (deployed to Netlify)
│   ├── index.html              # Pricing buttons wire to Stripe Checkout API
│   ├── booking-demo.html
│   ├── privacy.html
│   └── terms.html
├── docs/
│   └── founder-client-onboarding.md  # Manual onboarding guide for founding clients
└── .do/app.yaml                # DigitalOcean App Platform config (API + DB only)
```

---

## Environment Variables

All variables are set on the **api component** in DigitalOcean App Platform. Sensitive values should be marked **Encrypted**.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | App secret key |
| `JWT_SECRET_KEY` | ✅ | JWT signing key |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | ✅ | Default Twilio sending number (E.164) |
| `SENDGRID_API_KEY` | ✅ | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | ✅ | Sender email address |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key (AI agent) |
| `STRIPE_SECRET_KEY` | ✅ | Stripe live secret key (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Stripe webhook signing secret (`whsec_...`) |
| `STRIPE_PRICE_STARTER_SETUP` | ✅ | Stripe price ID — Starter one-time setup fee |
| `STRIPE_PRICE_STARTER_MONTHLY` | ✅ | Stripe price ID — Starter monthly recurring |
| `STRIPE_PRICE_PRO_SETUP` | ✅ | Stripe price ID — Professional one-time setup fee |
| `STRIPE_PRICE_PRO_MONTHLY` | ✅ | Stripe price ID — Professional monthly recurring |
| `BASE_URL` | ✅ | Public API base URL (`https://api.spacecoaststudios.com`) |
| `ALLOWED_ORIGINS` | ✅ | CORS origins (comma-separated) |
| `OPENAI_API_KEY` | optional | OpenAI key (if using OpenAI instead of Anthropic) |

---

## Stripe Billing

### Overview

Stripe is used for all client subscription billing. The checkout flow runs on the marketing site; tenant provisioning happens automatically via webhook.

**Flow:**
1. Prospect clicks **Get Started** on `spacecoaststudios.com` → marketing site calls `POST /api/billing/checkout`
2. API creates a Stripe Checkout session → returns URL → visitor is redirected to Stripe
3. Visitor completes checkout (billing info, business name, phone number collected in Stripe)
4. Stripe sends `checkout.session.completed` webhook → backend provisions tenant automatically:
   - Creates `Business` record with Stripe IDs and subscription info
   - Creates `AdminUser` record (username = email)
   - Generates 72-hour set-password token
   - Sends welcome email with login username and set-password link
5. Visitor lands on `/welcome` page → checks email → sets password → logs in to dashboard

### Stripe Configuration

**Publishable key:** `pk_live_51TM7kZ2MJMR8rAcZ2jSBcduwtelYsLikfR9OsPACEOypphYntZ1MmdpSK7lFdMb8egcatVty5vL5h4SiB2X7sc2n00HqCzzbqd`

**Secret key:** stored in DO env vars as `STRIPE_SECRET_KEY`

**Webhook endpoint:** `scs-billing-webhook` in Stripe Workbench
- URL: `https://api.spacecoaststudios.com/api/billing/webhook`
- Signing secret: stored in DO env vars as `STRIPE_WEBHOOK_SECRET`
- Subscribed events:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`
  - `invoice.payment_succeeded`

### Stripe Product & Price IDs

#### Standard Pricing

| Price | Stripe Price ID | Amount |
|---|---|---|
| Starter — Setup Fee | `price_1TbXKM2MJMR8rAcZfEKeo13B` | $1,997 one-time |
| Starter — Monthly | `price_1TbXKN2MJMR8rAcZ8ageyctL` | $249/month |
| Professional — Setup Fee | `price_1TbXKN2MJMR8rAcZIiW0KPMT` | $2,997 one-time |
| Professional — Monthly | `price_1TbXKO2MJMR8rAcZh0yQdVOv` | $399/month |

#### Founding Client Pricing (manual subscriptions only — not in checkout API)

| Price | Stripe Price ID | Amount |
|---|---|---|
| Starter — Founding Setup | `price_1TbXKN2MJMR8rAcZvreEPLwo` | $497 one-time |
| Starter — Founding Monthly | `price_1TbXKN2MJMR8rAcZF8PV52FQ` | $99/month (first 3 months) |
| Professional — Founding Setup | `price_1TbXKO2MJMR8rAcZ9MRzpF2s` | $997 one-time |
| Professional — Founding Monthly | `price_1TbXKO2MJMR8rAcZMiHThRka` | $199/month (first 3 months) |

#### Test Pricing (internal use only)

| Price | Stripe Price ID | Amount |
|---|---|---|
| Test — Setup (one-time) | `price_1TbkYi2MJMR8rAcZO4iP0oHP` | $1.00 one-time |
| Test — Monthly (recurring) | `price_1TbkkP2MJMR8rAcZAPo5kJx5` | $1.00/month |

To trigger a test checkout: `POST /api/billing/checkout` with `{"plan": "test"}` — returns a Stripe Checkout URL. Use a real card; cancel and refund immediately after testing.

### Billing Dashboard

- **Platform admin** (`/billing`): sees all tenant businesses in a table with plan, status, next billing date, and a direct link to each customer in the Stripe Dashboard.
- **Business admin** (`/billing`): sees their own plan, subscription status, next billing date, included features, and a **Manage Billing** button that opens the Stripe Customer Portal.

### Subscription Status Updates

Subscription status changes (upgrades, cancellations, payment failures) update in real time via Stripe webhooks — no polling needed. Status is stored on the `Business` model and reflected immediately in the billing dashboard on refresh.

---

## Client Onboarding — New Client Signup Flow

### Automatic (via Stripe Checkout — standard pricing)

1. Client clicks **Get Started** on the pricing page
2. Completes Stripe Checkout (collects name, email, address, phone, business name)
3. Tenant is provisioned automatically — no manual steps required
4. Client receives welcome email with their username (email address) and set-password link
5. Client sets password, logs into dashboard at `dashboard.spacecoaststudios.com`
6. Complete A2P 10DLC setup and platform configuration (see sections below)

### Manual (founding clients at introductory pricing)

See `docs/founder-client-onboarding.md` for the full step-by-step guide.

Summary:
1. Create customer + subscription in Stripe at founding prices
2. Create Business + AdminUser records in the database
3. Send set-password link manually

---

## Client Onboarding — A2P 10DLC Checklist

A2P 10DLC registration must be completed **before go-live** — provisioning can take
hours to days and SMS will fail until the number is fully registered.
Complete these steps at least 2–3 days before the client's launch date.

### Step 1 — Twilio Account Setup
- [ ] Purchase a local phone number in the client's area code via Twilio Console
- [ ] Verify the number appears under **Phone Numbers → Manage → Active Numbers**

### Step 2 — Messaging Service
- [ ] Go to **Messaging → Services → Create Messaging Service**
- [ ] Name it after the client (e.g. "Peak HVAC Services")
- [ ] Under **Sender Pool**, add the purchased phone number
- [ ] Note the Messaging Service SID (starts with `MG...`) — you'll need it for the campaign

### Step 3 — A2P 10DLC Brand & Campaign
- [ ] Go to **Messaging → Regulatory Compliance → A2P 10DLC**
- [ ] Register a **Brand** for the client (business name, EIN, address, contact info)
- [ ] Once brand is approved, create a **Campaign** linked to the client's Messaging Service
- [ ] Use campaign use case: **Mixed** or **Notifications**
- [ ] Campaign description should include: appointment confirmations, reminders, on-the-way
      notifications, and review requests — mention opt-in/opt-out language

### Step 4 — Register the Phone Number to the Campaign
- [ ] On the Campaign details page, click **Register phone numbers**
- [ ] Select the client's number and confirm
- [ ] Wait for status to change from **Pending** to **Registered** before going live
- [ ] ⚠️ Do NOT just add the number to the sender pool — you must also explicitly
      register it to the campaign via the Register button or it stays in pending

### Step 5 — Configure Inbound Webhook (CRITICAL)
- [ ] Go to **Phone Numbers → Manage → Active Numbers** and click the client's number
- [ ] In the **Messaging** section, find **"A MESSAGE COMES IN"**
- [ ] Set it to **Webhook** and paste the URL:
      `https://api.spacecoaststudios.com/webhook/sms/inbound` (HTTP POST)
- [ ] Also confirm the Messaging Service's **Integration** page webhook is set to the same URL
- [ ] ⚠️ The number-level "A MESSAGE COMES IN" setting controls inbound routing.
      Just adding a number to the Messaging Service sender pool is NOT enough — that
      only affects outbound. Inbound requires the number itself to point at the webhook.

### Step 6 — Platform Configuration
- [ ] Business record should already exist (created via Stripe checkout or manually)
- [ ] Set `twilio_phone_number` on the Business to the client's Twilio number (E.164 format, e.g. `+13215551234`)
- [ ] Set business hours, service types, and technicians in the dashboard
- [ ] Set Google Review URL in Settings (required for automated review requests)
- [ ] Configure notification templates if needed
- [ ] Create a test appointment and verify confirmation SMS + email arrive
- [ ] Test the OTW flow: trigger a tech prompt and confirm YES reply flows through

---

## Backend Services

### Notifications
- **SMS**: Twilio (A2P 10DLC registered, E.164 phone normalization with multi-format `.in_()` lookups)
- **Email**: SendGrid with branded HTML templates

### Notification Events

| Event | Trigger |
|---|---|
| `confirmation` | Immediately on appointment booking |
| `reminder_24h` | Daily during 11am–1pm local window — sent for next open business day |
| `otw_tech_prompt` | 45–75 min before appointment — texts the technician |
| `otw_customer` | When technician replies YES to OTW prompt |
| `complete_prompt` | After OTW customer notification — texts tech asking if job is done |
| `review_request` | When technician replies YES to complete prompt (or manually triggered) |
| `morning_kickoff` | After 7am — texts tech with first job details if not yet sent |

### OTW Reply Flow (Technician SMS)

1. Scheduler fires `otw_tech_prompt` → tech receives "Reply YES when leaving for [Customer]"
2. Tech replies YES → `checkout.session.completed` webhook → customer gets "On The Way" SMS
3. Tech receives "Reply YES when job is complete"
4. Tech replies YES → if more appointments today → next stop prompt; if last job → review request sent to customer + "Great work! That's a wrap!" to tech

### Background Scheduler (APScheduler)

| Job | Interval | Description |
|---|---|---|
| `send_reminders` | Every 30 min | Fires during 11am–1pm local window |
| `send_otw_prompts` | Every 15 min | Texts techs for appointments in 45–75 min window |
| `send_otw_morning_kickoffs` | Every 15 min | Morning kickoff SMS to techs for first job (after 7am) |
| `generate_recurring` | Daily 6am | Pre-generates recurring appointment instances |

---

## API Reference

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | none | Username + password login, returns JWT |
| `POST` | `/api/auth/set-password` | none | Set password via reset token (from welcome email) |

### Billing

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/billing/checkout` | none | Create Stripe Checkout session; body: `{"plan": "starter"\|"professional"\|"test"}` |
| `GET` | `/api/billing/checkout-session` | none | Get customer email from Stripe session (for welcome page) |
| `POST` | `/api/billing/webhook` | Stripe sig | Handle Stripe webhook events |
| `GET` | `/api/billing/subscription` | JWT | Get current plan/status for active business |
| `POST` | `/api/billing/portal` | JWT | Create Stripe Customer Portal session |

### Businesses (platform admin only)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/businesses` | JWT (admin) | List all businesses with billing fields |
| `POST` | `/api/businesses` | JWT (admin) | Create business |
| `GET` | `/api/businesses/{id}` | JWT (admin) | Get business |
| `PUT` | `/api/businesses/{id}` | JWT (admin) | Update business |

### Appointments

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/appointments` | JWT | List appointments; `?sort=upcoming\|newest\|oldest` (default: `upcoming`) |
| `POST` | `/api/appointments` | JWT | Create appointment |
| `PUT` | `/api/appointments/{id}` | JWT | Update appointment |
| `POST` | `/api/appointments/{id}/cancel` | JWT | Cancel appointment |

### Admin / Notification Triggers

All require JWT auth.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/admin/trigger/reminders` | Fire reminder job now (bypasses noon window) |
| `POST` | `/api/admin/trigger/otw-prompts` | Fire OTW tech prompt job now |
| `POST` | `/api/admin/trigger/morning-kickoffs` | Fire morning kickoff job now |
| `GET` | `/api/admin/scheduler/status` | Show next scheduled run times |
| `POST` | `/api/admin/appointments/{id}/resend-confirmation` | Resend confirmation SMS + email |
| `POST` | `/api/admin/appointments/{id}/send-reminder` | Send reminder now |
| `POST` | `/api/admin/appointments/{id}/send-review-request` | Send review request (requires `google_review_url` on business) |

### Appointments — Sort Options

`GET /api/appointments?sort=upcoming` (default)

| Value | Behavior |
|---|---|
| `upcoming` | Future appointments soonest first, then past appointments most recent first |
| `newest` | All appointments by `scheduled_start DESC` |
| `oldest` | All appointments by `scheduled_start ASC` |

---

## Pricing Tiers

### Starter — $1,997 setup + $249/month
- AI-powered contact form responder
- Embeddable contact form widget
- Dedicated booking request page
- Up to 3 service types & 5 technicians
- Email confirmations & reminders
- Admin dashboard
- Email support (2-business-day response)

### Professional — $2,997 setup + $399/month
- Everything in Starter, plus:
- Unlimited service types & technicians
- Self-scheduling booking widget
- SMS booking agent (text-to-book)
- SMS confirmations, reminders & alerts
- On The Way technician notifications
- Automated Google review requests
- Emergency dispatch with on-call management
- Recurring appointment scheduling
- Custom AI persona & branding
- Priority support (next-business-day response)
- Monthly check-in call

### Founding Client Offer (Limited Time)
- **Starter:** $497 setup + $99/month for first 3 months, then $249/month
- **Professional:** $997 setup + $199/month for first 3 months, then $399/month
- See `docs/founder-client-onboarding.md` for manual provisioning steps

---

## Local Development

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in secrets
uvicorn app.main:app --reload
# API runs on http://localhost:8000
```

### Frontend Dashboard
```bash
cd frontend/dashboard
npm install
npm run dev
# Runs on http://localhost:5173
# /api requests are proxied to https://api.spacecoaststudios.com (see vite.config.js)
```

### Testing Stripe Checkout Locally
Use the `test` plan to avoid charging real money:
```powershell
# PowerShell
$result = Invoke-RestMethod -Method POST -Uri "https://api.spacecoaststudios.com/api/billing/checkout" -ContentType "application/json" -Body '{"plan": "test"}'
$result.url   # open this URL in browser
```
Complete with a real card ($2 total). Cancel subscription and refund immediately after testing.

---

## Common Pitfalls

### SMS / Twilio
- **30034 Unregistered Number** — number not registered to campaign; use Register Phone Numbers button on the campaign page
- **30024 Provisioning Issue** — number added to sender pool but not registered to campaign
- **"No HTTP Requests logged for this event"** — inbound reply received but no handler configured. Go to Active Numbers → click the number → Messaging → set "A MESSAGE COMES IN" to the webhook URL. Adding a number to the sender pool only controls outbound.
- **Phone format mismatch** — DB may store numbers as 10-digit; Twilio sends E.164. The backend uses multi-format `.in_()` lookups to handle both.

### Stripe / Billing
- **`customer_creation` not valid** — this parameter is only valid in `payment` mode, not `subscription` mode. Do not add it to the checkout session.
- **Missing recurring price** — Stripe requires at least one recurring price in subscription mode. Every checkout must include both a setup (one-time) and monthly (recurring) line item.
- **Email blank after provisioning** — customer email is in `customer_details.email` in the webhook payload, not the top-level `customer_email` field.
- **`stripe` module not found** — ensure `stripe==11.1.0` is in `requirements.txt`.

### Deployment
- **DO env vars** — all Stripe keys must be on the **api component**, not app-level env vars.
- **Migrations** — schema changes are handled by `run_migrations()` in `main.py` using raw `ALTER TABLE IF NOT EXISTS` — no Alembic.
