# Space Coast Studios — Home Services Platform

Multi-tenant AI-powered scheduling, dispatch, and notifications platform.

**Last updated:** 2026-05-29 | **Status:** Production-ready (founding client phase)

---

## Table of Contents

1. [Infrastructure](#infrastructure)
2. [Repository Structure](#repository-structure)
3. [Environment Variables](#environment-variables)
4. [Stripe Billing](#stripe-billing)
5. [Client Onboarding — Signup Flow](#client-onboarding--signup-flow)
6. [Client Onboarding — A2P 10DLC Checklist](#client-onboarding--a2p-10dlc-checklist)
7. [AI Systems](#ai-systems)
8. [Backend Services & Notifications](#backend-services--notifications)
9. [Platform Capabilities — Tested Status](#platform-capabilities--tested-status)
10. [API Reference](#api-reference)
11. [Local Development](#local-development)
12. [Common Pitfalls](#common-pitfalls)
13. [Changelog](#changelog)

---

## Infrastructure

| Component | Provider | URL |
|---|---|---|
| **API / Backend** | DigitalOcean App Platform | `https://api.spacecoaststudios.com` |
| **Database** | DigitalOcean Managed PostgreSQL 18 | NYC3, 1GB RAM / 10GB disk |
| **Dashboard** | Netlify | `https://dashboard.spacecoaststudios.com` |
| **Marketing Site** | Netlify | `https://spacecoaststudios.com` |

DNS managed in **GoDaddy** — CNAME `api.*` → DigitalOcean, `dashboard.*` + root → Netlify.
`.do/app.yaml` only defines the `api` service and database — NOT the frontend or marketing site.

**Auto-deploy:** All three components deploy automatically on push to `main`.

**Database access:**
```bash
psql "postgresql://doadmin:PASSWORD@host.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
```
Get the full connection string from DO → Databases → spacecoast-db → Overview → Connection Details.

---

## Repository Structure

```
home-services-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Entry point, run_migrations(), seed_defaults(), lifespan
│   │   ├── config.py                # Pydantic Settings — reads env vars + defaults
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── routers/                 # FastAPI route handlers
│   │   │   ├── auth.py              # Login, set-password, forgot-password, refresh
│   │   │   ├── billing.py           # Stripe checkout, webhook, portal, subscription
│   │   │   ├── businesses.py        # Business CRUD + /me + impersonate
│   │   │   ├── contact.py           # Contact form submission + AI responder
│   │   │   ├── embed.py             # Public booking widget (contact form iframe)
│   │   │   ├── sms_webhook.py       # Twilio inbound SMS — OTW/booking reply flow
│   │   │   └── ...
│   │   └── services/
│   │       ├── sms_agent.py         # Claude SMS booking agent (tool_use, 4 tools)
│   │       ├── contact_responder.py # AI auto-reply to contact form submissions
│   │       ├── scheduler.py         # APScheduler background jobs
│   │       ├── notifications.py     # Twilio SMS + SendGrid email
│   │       └── scheduling.py        # Availability engine
│   └── requirements.txt
├── frontend/dashboard/              # React 18 + Vite + Tailwind CSS
│   └── src/
│       ├── pages/                   # All dashboard pages
│       ├── hooks/useAuth.jsx        # Auth state + impersonation
│       └── hooks/useBusinessContext.jsx
├── marketing-site/                  # Static HTML
│   ├── index.html
│   ├── privacy.html
│   └── terms.html
├── docs/
│   └── founder-client-onboarding.md
├── CLAUDE.md                        # Master project memory (read each session)
└── .do/app.yaml                     # DigitalOcean App Platform config
```

---

## Environment Variables

Set on the **api component** in DigitalOcean App Platform. Sensitive values must be **Encrypted**.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (DO injects automatically) |
| `SECRET_KEY` | ✅ | App secret key |
| `JWT_SECRET_KEY` | ✅ | JWT signing key |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | ✅ | Default Twilio sending number (E.164) |
| `SENDGRID_API_KEY` | ✅ | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | ✅ | Sender email (`noreply@spacecoaststudios.com`) |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key — used by both AI systems |
| `LLM_MODEL` | — | Default: `claude-haiku-4-5-20251001` — contact form responder only. Check validity quarterly at https://docs.anthropic.com/en/docs/about-claude/models |
| `SMS_AGENT_MODEL` | — | Default: `claude-sonnet-4-6` — SMS booking agent. Sonnet required for multi-turn reasoning. Check validity quarterly. |
| `STRIPE_SECRET_KEY` | ✅ | Stripe live secret key (`sk_live_...`) |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Stripe webhook signing secret (`whsec_...`) |
| `STRIPE_PRICE_STARTER_SETUP` | ✅ | `price_1TbXKM2MJMR8rAcZfEKeo13B` — $1,997 one-time |
| `STRIPE_PRICE_STARTER_MONTHLY` | ✅ | `price_1TbXKN2MJMR8rAcZ8ageyctL` — $249/month |
| `STRIPE_PRICE_PRO_SETUP` | ✅ | `price_1TbXKN2MJMR8rAcZIiW0KPMT` — $2,997 one-time |
| `STRIPE_PRICE_PRO_MONTHLY` | ✅ | `price_1TbXKO2MJMR8rAcZh0yQdVOv` — $399/month |
| `BASE_URL` | ✅ | `https://api.spacecoaststudios.com` — used in calendar links |
| `ALLOWED_ORIGINS` | ✅ | CORS origins (comma-separated) |
| `CONTACT_AUTO_RESPOND` | — | `true`/`false` — auto-fire AI responder on form submit |

**Frontend** (Netlify): `VITE_API_URL=https://api.spacecoaststudios.com`

---

## Stripe Billing

**Publishable key:** `pk_live_51TM7kZ2MJMR8rAcZ2jSBcduwtelYsLikfR9OsPACEOypphYntZ1MmdpSK7lFdMb8egcatVty5vL5h4SiB2X7sc2n00HqCzzbqd`

**Webhook endpoint:** `https://api.spacecoaststudios.com/api/billing/webhook`
Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`

### Price IDs

| Plan | Price ID | Amount |
|---|---|---|
| Starter Setup | `price_1TbXKM2MJMR8rAcZfEKeo13B` | $1,997 one-time |
| Starter Monthly | `price_1TbXKN2MJMR8rAcZ8ageyctL` | $249/month |
| Pro Setup | `price_1TbXKN2MJMR8rAcZIiW0KPMT` | $2,997 one-time |
| Pro Monthly | `price_1TbXKO2MJMR8rAcZh0yQdVOv` | $399/month |
| Founding Starter Setup | `price_1TbXKN2MJMR8rAcZvreEPLwo` | $497 one-time |
| Founding Starter Monthly | `price_1TbXKN2MJMR8rAcZF8PV52FQ` | $99/month (first 3 mo) |
| Founding Pro Setup | `price_1TbXKO2MJMR8rAcZ9MRzpF2s` | $997 one-time |
| Founding Pro Monthly | `price_1TbXKO2MJMR8rAcZMiHThRka` | $199/month (first 3 mo) |
| Test Setup | `price_1TbkYi2MJMR8rAcZO4iP0oHP` | $1.00 one-time |
| Test Monthly | `price_1TbkkP2MJMR8rAcZAPo5kJx5` | $1.00/month |

**Test checkout:**
```powershell
$r = Invoke-RestMethod -Method POST -Uri "https://api.spacecoaststudios.com/api/billing/checkout" -ContentType "application/json" -Body '{"plan":"test"}'
$r.url  # open in browser — $2 total, refund immediately after
```

---

## Client Onboarding — Signup Flow

### Automatic (Stripe Checkout)
1. Client clicks **Get Started** → `POST /api/billing/checkout` → Stripe Checkout
2. Payment completes → `checkout.session.completed` webhook → tenant provisioned automatically
3. Welcome email sent with username + 72-hour set-password link
4. Client sets password → auto-logged in → redirected to **Setup Wizard** (`/setup`)
5. Wizard (3 steps): Business Info → Look & Feel → AI & Notifications
6. On completion: `has_completed_setup = true`; wizard no longer appears

### Manual (Founding Clients)
See `docs/founder-client-onboarding.md`.

---

## Client Onboarding — A2P 10DLC Checklist

Complete **before go-live** — registration takes 2–3+ days.

- [ ] Purchase local Twilio number in client's area code
- [ ] Create Messaging Service → add number to sender pool
- [ ] Register A2P Brand (EIN, business info) → wait for approval
- [ ] Create Campaign (CUSTOMER_CARE or Mixed) → link to Messaging Service
- [ ] **Register phone number to Campaign** (separate step — easy to miss)
- [ ] Configure inbound webhook on the **number itself** (not just the Messaging Service):
  `https://api.spacecoaststudios.com/webhook/sms/inbound` (POST)
- [ ] Set `twilio_phone_number` on Business record in Settings (E.164 format)
- [ ] Test: submit contact form → verify AI SMS reply arrives
- [ ] Test: reply to AI SMS → verify booking agent handles conversation
- [ ] Test: create appointment → trigger OTW flow

---

## AI Systems

### 1. Contact Form AI Responder (`services/contact_responder.py`)

Triggered as a BackgroundTask after every `POST /contact/submit`. Opens its own DB session.

**Flow:**
1. Load business context (services, available slots in business local timezone)
2. Call Claude Haiku with customer message + context
3. Parse JSON response (`reply` + `suggested_slots`)
4. Send via customer's preferred channel (one channel only — no duplication)
5. Stamp submission with AI response, status, responded_at

**Channel routing:**

| Preferred | SMS Consent | Channel |
|---|---|---|
| text | ✅ | SMS only |
| text | ❌ | Email only |
| email | — | Email only |
| call | — | Email only (staff calls back) |

**SMS format:** Greeting line stripped; body capped at 480 chars; slots shown in business local timezone with full dates (e.g. "Friday, May 30 at 2:30 PM").

**Draft mode:** If `ai_response_mode == "draft_only"`, response held for staff approval in Contact Queue instead of auto-sending.

### 2. SMS Booking Agent (`services/sms_agent.py`)

Handles inbound text replies after the contact responder sends an initial SMS. Uses Claude Sonnet with tool_use.

**Flow per inbound message:**
1. Look up business by Twilio `To` number
2. Check if it's a tech YES reply (OTW flow) — handled separately
3. Look up most recent contact submission for this phone (within 30 days) — provides name, service, address context
4. Load or create `SmsConversation` for this phone + business
5. Run agent loop (up to 5 iterations)

**4 Tools:**
- `check_availability` — called on every turn (mandatory) before suggesting or booking any slot
- `create_booking` — called once all 4 fields confirmed (name, service, datetime, address)
- `escalate_to_human` — sets conversation to escalated, notifies staff
- `emergency_dispatch` — alerts on-call technician

**Context injection:** On every inbound message, the agent's system prompt is enriched with confirmed info from the contact form submission (name, service, address). Agent skips asking for already-known fields.

**Booking result:**
- Appointment created with `status="confirmed"`, `source="sms"`
- Customer record created/updated with email, address, city, state, zip from contact submission
- `SmsConversation.status` set to `"booked"`
- Agent sends natural confirmation reply (no separate confirmation SMS)

**Timezone handling:** All slot datetimes are stored in UTC. Display times are converted to business local timezone (default: `America/New_York`). Naive datetimes passed by the agent are treated as business local time before UTC conversion.

---

## Backend Services & Notifications

### Notification Events

| Event | Channel | Trigger |
|---|---|---|
| `confirmation` | SMS + Email | Appointment created |
| `reminder_24h` | SMS + Email | Daily 11am–1pm local → next open business day |
| `otw_tech_prompt` | SMS to tech | 45–75 min before appointment |
| `otw_morning_kickoff` | SMS to tech | 2h before first appointment (full day summary + schedule URL) |
| `otw_customer` | SMS to customer | Tech replies YES to OTW prompt |
| `review_request` | SMS + Email | Tech replies YES to complete prompt |

### OTW Reply Flow

1. Scheduler → tech: "Reply YES when leaving for [Customer]"
2. Tech replies YES → appointment → `en_route` → customer gets OTW SMS → tech gets "Reply YES when done"
3. Tech replies YES → last job: review request + "That's a wrap!" / more jobs: next stop prompt

### Background Scheduler

| Job | Schedule | Notes |
|---|---|---|
| `send_reminders` | Every 30 min | 11am–1pm local window only |
| `send_otw_prompts` | Every 15 min | 45–75 min before appointment |
| `send_morning_kickoffs` | Every 15 min | 2h before first appt; "no appointments" variant 7–8am local |
| `generate_recurring` | Daily 6am UTC | Pre-generates recurring appointment instances |

**Manual triggers** (bypass time windows — for testing):
- `POST /api/admin/trigger/reminders`
- `POST /api/admin/trigger/otw-prompts`
- `POST /api/admin/trigger/morning-kickoffs`

---

## Platform Capabilities — Tested Status

### ✅ Fully Built & Smoke Tested (2026-05-29)

| Feature | Notes |
|---|---|
| Contact form widget (embed) | Address, service, problem description, SMS consent — all fields saving correctly |
| Contact form AI auto-responder | Single-channel routing; slot times in business local timezone; 480-char SMS cap |
| SMS booking agent (text-to-book) | Full end-to-end: form → AI reply → customer texts → agent books → confirmed appointment |
| Appointment creation via SMS | Status `confirmed`, correct timezone, address, problem description in notes |
| Customer creation via SMS | Email, address, city, state, zip populated from contact form submission |
| Appointment management dashboard | Expandable rows with address (Maps link), notes, problem description |
| Morning kickoff SMS | Full day summary, schedule URL, no-appointments variant |
| OTW tech prompt + reply flow | en_route → customer OTW → complete prompt → review request |
| Review request (SMS + email) | Triggered on job completion |
| Appointment reminders | Next-business-day, noon local window, idempotent |
| Stripe billing | Checkout → webhook → tenant provisioning → welcome email |
| First-login setup wizard | 3-step, auto-saves, has_completed_setup gate |
| Platform admin impersonation | Amber banner, localStorage stash/restore |
| Forgot password / reset flow | 1-hour token, auto-login after reset |
| Soft delete | Appointments, customers, contact submissions |
| Notification templates | 12 editable per-business |
| On-call rotation + override | Emergency dispatch via SMS agent |
| Calendar invite links | .ics + Google/Apple/Outlook/Yahoo |
| Tech daily schedule page | Public mobile page per-tech, no login required |
| Twilio phone number in Settings | Platform admin can set per-business number from dashboard |

### ⚠️ Built, Not Yet Fully Tested
- Self-scheduling booking widget (availability engine ready; no public UI)
- Recurring appointments UI (backend exists)
- Emergency contact form routing

### ❌ Not Yet Built
- Visual calendar view (day/week/month)
- Customer portal

---

## API Reference

### Auth
| Method | Endpoint | Notes |
|---|---|---|
| `POST` | `/api/auth/login` | `{username, password}` → tokens |
| `POST` | `/api/auth/refresh` | `{refresh_token}` → new token pair |
| `POST` | `/api/auth/set-password` | `{token, password, confirm_password}` → auto-login |
| `POST` | `/api/auth/forgot-password` | `{email}` → always 200 |

### Businesses
| Method | Endpoint | Notes |
|---|---|---|
| `GET` | `/api/businesses` | Platform admin only |
| `GET` | `/api/businesses/me` | Caller's own business |
| `PUT` | `/api/businesses/{id}` | Business admins: own only, no plan/billing fields |
| `POST` | `/api/businesses/{id}/impersonate` | Platform admin → 2hr impersonation JWT |

### Appointments
| Method | Endpoint | Notes |
|---|---|---|
| `GET` | `/api/appointments` | `?sort=upcoming\|newest\|oldest` |
| `POST` | `/api/appointments` | Fires confirmation SMS + email |
| `PUT` | `/api/appointments/{id}` | |
| `POST` | `/api/appointments/{id}/cancel` | |
| `DELETE` | `/api/appointments/{id}` | Soft delete |

### Contact Submissions
Public: `POST /contact/submit?business_id=`

**Payload:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "3215550100",
  "service_requested": "AC Repair",
  "message": "My AC isn't working.",
  "problem_description": "Grinding noise when it kicks on",
  "street_address": "123 Oak St",
  "city": "Cocoa",
  "state": "FL",
  "zip_code": "32922",
  "preferred_contact_method": "text",
  "sms_consent": true,
  "preferred_date": "2026-06-01",
  "preferred_time": "morning"
}
```
Phone is normalized to E.164 at submission time. `sms_consent: true` required for SMS reply.

### Public Endpoints (no auth)
- `POST /contact/submit?business_id=` — contact form submission
- `GET /embed/{slug}/contact` — embeddable contact form widget
- `POST /webhook/sms/inbound` — Twilio inbound SMS handler
- `GET /schedule/tech/{token}` — technician daily schedule (mobile)
- `GET /cal/{token}` — calendar landing page
- `GET /cal/{token}/ical` — .ics download

### Admin Triggers
| Endpoint | Description |
|---|---|
| `POST /api/admin/trigger/reminders` | Fire reminder job now |
| `POST /api/admin/trigger/otw-prompts` | Fire OTW prompt job now |
| `POST /api/admin/trigger/morning-kickoffs` | Fire kickoff job now |
| `GET /api/admin/scheduler/status` | Next run times |

---

## Local Development

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# → http://localhost:8000

# Frontend
cd frontend/dashboard
npm install
npm run dev
# → http://localhost:5173 (/api proxied to production API)
```

---

## Common Pitfalls

### SMS / Twilio
- **30034 Unregistered Number** — number not registered to campaign; use Register Phone Numbers on campaign page
- **Inbound not routing** — configure webhook on the number itself (Active Numbers → click number → Messaging → "A MESSAGE COMES IN"). Adding to sender pool only controls outbound.
- **Phone format mismatch** — contact form normalizes to E.164 on submit. Old customer records may store 10-digit format — availability engine uses multi-format `.in_()` lookups.
- **SMS booking agent loses context** — each inbound message does a fresh DB lookup of the contact submission by phone. If the submission was soft-deleted, context is lost. Close (status change) instead of deleting during active booking conversations.

### Stripe / Billing
- **Missing recurring price** — checkout must include both setup (one-time) and monthly (recurring) line items
- **Email blank after provisioning** — use `customer_details.email` from webhook payload, not `customer_email`

### Deployment
- **Migrations** — use `ALTER TABLE ADD COLUMN IF NOT EXISTS` in `run_migrations()`. Never Alembic.
- **Git from bash** — never run `git add`/`git commit`/`git push` from the bash sandbox on Windows filesystem mounts (creates unremovable lock files). All git commands must run in Ryan's PowerShell terminal, one command per line.

### AI Models
- **Wrong LLM_MODEL** — bad model string silently sets contact submissions to "Error". Startup log prints `LLM model validated OK` or a WARNING. Check DO Runtime Logs after deploy.
- **SMS agent needs Sonnet** — Haiku lacks the multi-turn reasoning needed for booking conversations. `SMS_AGENT_MODEL` defaults to `claude-sonnet-4-6`.

---

## Changelog

### 2026-05-29 — SMS Booking Agent (End-to-End)
- **SMS booking flow fully tested and working**: contact form → AI SMS reply → customer texts → agent books → confirmed appointment with correct time, address, customer record
- Address fields added to contact form (street, city, state, zip) — stored on submission, passed to agent context, saved to customer record on booking
- Phone normalized to E.164 at contact form submission — fixes agent context lookup
- Agent uses live DB lookup of contact submission on every inbound message (name, service, address pre-loaded)
- Mandatory `check_availability` on every agent turn — prevents stale slot booking
- Initial slot offer reduced to exactly 2 (reduces stale-slot risk)
- Timezone fix — slots displayed in business local time; naive datetimes treated as local not UTC
- SMS bookings created as `confirmed` (not `pending`) — included in kickoff/OTW flows
- Duplicate confirmation SMS removed — agent reply is the only confirmation
- `SMS_AGENT_MODEL` config added — Sonnet for agent, Haiku for contact responder
- Twilio phone number field added to Settings page (platform admin)
- `twilio_phone_number` added to BusinessResponse schema

### 2026-05-28 — Problem Description, Tech Schedule, Soft Delete
- Problem description field on contact form and appointments
- Tech daily schedule page (public, mobile, per-tech token)
- Morning kickoff overhauled — 2h before first appointment, full day summary
- Soft delete for appointments, customers, contact submissions
- Contact responder channel awareness + SMS truncation fix
- SMS consent gate (A2P compliance)

### 2026-05-27 — Auth, Billing, Impersonation, Setup Wizard
- Forgot-password flow
- Platform admin impersonation with amber banner
- First-login setup wizard (3-step)
- Stripe billing fully configured and tested
- Notification templates (12 editable per-business)
- On-call rotation + override

### 2026-05-26 — Core Platform
- Customer address split fields, phone E.164 normalization
- Appointment confirmation SMS on creation
- Reminder scheduler (noon local, idempotent)
- Admin manual trigger endpoints + Developer Tools panel
- Calendar invite links (.ics + Google/Apple/Outlook/Yahoo)
