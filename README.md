# Home Services Platform

Multi-tenant home services scheduling, dispatch, and notifications platform built for Space Coast Studios.

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
- [ ] Use campaign use case: **Mixed** or **Notifications** depending on message types
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
- [ ] Set it to use the **Messaging Service** (select the client's Messaging Service)
      OR paste the webhook URL directly:
      `https://api.spacecoaststudios.com/webhook/sms/inbound` (HTTP POST)
- [ ] Also confirm the Messaging Service's **Integration** webhook is set to:
      `https://api.spacecoaststudios.com/webhook/sms/inbound` (HTTP POST)
- [ ] ⚠️ The number-level "A MESSAGE COMES IN" setting controls inbound routing.
      Just adding a number to a Messaging Service sender pool is NOT enough — that
      only affects outbound. Inbound requires the number itself to point at the
      Messaging Service or the webhook URL. If left blank, Twilio receives replies
      with no handler and logs "There were no HTTP Requests logged for this event."

### Step 6 — Platform Configuration
- [ ] Add the client as a Business in the dashboard
- [ ] Set `TWILIO_PHONE_NUMBER` for the client's business to their new number (E.164 format)
- [ ] Confirm phone number is in E.164 format (e.g. `+13215551234`)
- [ ] Create a test appointment and verify confirmation SMS + email arrive
- [ ] Wait ~5 minutes and verify the OTW prompt fires correctly

### Common Pitfalls
- **30034 Unregistered Number** — number is not registered to the campaign; use
  Register Phone Numbers button on the campaign page
- **30024 Provisioning Issue** — number was added to sender pool but not explicitly
  registered to campaign; click Register Phone Numbers
- **Wrong Messaging Service** — the campaign is linked to a specific Messaging Service
  (check the `MG...` SID on the campaign). The phone number must be in THAT service's
  sender pool, not a different one
- **Pending never resolves** — if pending for more than 24 hours, contact Twilio support
- **"No HTTP Requests logged for this event"** — inbound reply received by Twilio but
  no handler is configured. Go to Active Numbers → click the number → Messaging section →
  set "A MESSAGE COMES IN" to the Messaging Service or to the webhook URL directly.
  Adding a number to the sender pool only controls outbound; inbound is always set at
  the number level.

---

## Pricing Tiers

### Starter — $1,997 setup + $249/month
- AI-powered contact form responder
- Embeddable contact form widget
- Dedicated booking request page (shareable link)
- Up to 3 service types
- Up to 5 technicians
- Email confirmations & reminders
- Admin dashboard
- Email support (2-business-day response)

### Professional — $2,997 setup + $399/month
- Everything in Starter, plus:
- Unlimited service types & technicians
- Self-scheduling booking widget (live calendar availability)
- SMS booking agent (text-to-book)
- SMS confirmations, reminders & alerts
- On The Way technician notifications
- Automated Google review requests
- Emergency dispatch with on-call management
- Recurring appointment scheduling
- Custom AI persona & branding
- Priority support (next-business-day response)
- Monthly check-in call

### Founding Client Offer (Limited Time / Introductory)
- **Starter:** $497 setup + $99/month for first 3 months (then $249/month)
- **Professional:** $997 setup + $199/month for first 3 months (then $399/month)

### Stripe Configuration
- Publishable key: `pk_live_51TM7kZ2MJMR8rAcZ2jSBcduwtelYsLikfR9OsPACEOypphYntZ1MmdpSK7lFdMb8egcatVty5vL5h4SiB2X7sc2n00HqCzzbqd`
- Secret key: stored in DigitalOcean API component env vars as `STRIPE_SECRET_KEY`
- Webhook secret: stored as `STRIPE_WEBHOOK_SECRET` (set after webhook endpoint created)

#### Stripe Product IDs
| Product | ID |
|---|---|
| Starter Plan | `prod_Uail0oXz9jO2Nw` |
| Professional Plan | `prod_Uailjx0LeRYgYw` |

#### Stripe Price IDs
| Price | ID | Amount |
|---|---|---|
| Starter — Setup Fee | `price_1TbXKM2MJMR8rAcZfEKeo13B` | $1,997 one-time |
| Starter — Monthly | `price_1TbXKN2MJMR8rAcZ8ageyctL` | $249/month |
| Starter — Founding Setup | `price_1TbXKN2MJMR8rAcZvreEPLwo` | $497 one-time |
| Starter — Founding Monthly | `price_1TbXKN2MJMR8rAcZF8PV52FQ` | $99/month |
| Professional — Setup Fee | `price_1TbXKN2MJMR8rAcZIiW0KPMT` | $2,997 one-time |
| Professional — Monthly | `price_1TbXKO2MJMR8rAcZh0yQdVOv` | $399/month |
| Professional — Founding Setup | `price_1TbXKO2MJMR8rAcZ9MRzpF2s` | $997 one-time |
| Professional — Founding Monthly | `price_1TbXKO2MJMR8rAcZMiHThRka` | $199/month |

---

## Infrastructure

### Hosting

| Component | Provider | URL | Notes |
|---|---|---|---|
| **API / Backend** | DigitalOcean App Platform | `https://api.spacecoaststudios.com` | FastAPI, Python, 2 instances |
| **Database** | DigitalOcean Managed PostgreSQL 18 | `spacecoast-db` | Managed, ~$15/mo |
| **Dashboard (frontend)** | **Netlify** | `https://dashboard.spacecoaststudios.com` | React/Vite, auto-deploys from `main` |
| **Marketing Site** | **Netlify** | `https://spacecoaststudios.com` | Static HTML, auto-deploys from `main` |

> **Note:** The dashboard and marketing site are hosted on **Netlify**, not DigitalOcean.
> DNS for both is managed in **GoDaddy** with CNAME records pointing to Netlify.
> The `.do/app.yaml` file only reflects the `api` service and database — the dashboard/marketing
> entries in that file are not active DO deployments.

### DNS (GoDaddy)

| Record | Type | Points To |
|---|---|---|
| `api.spacecoaststudios.com` | CNAME | DigitalOcean App Platform |
| `dashboard.spacecoaststudios.com` | CNAME | Netlify |
| `spacecoaststudios.com` | A / CNAME | Netlify |

---

## Repository Structure

```
home-services-platform/
├── backend/                  # FastAPI backend (deployed to DigitalOcean)
│   ├── app/
│   │   ├── main.py           # App entry point, migrations, startup
│   │   ├── config.py         # Settings (pydantic-settings, reads .env)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── routers/          # FastAPI route handlers
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic (notifications, scheduler, AI)
│   │   └── utils/            # Auth helpers, ICS generator
│   ├── requirements.txt
│   └── .env.example
├── frontend/dashboard/       # React 18 + Vite dashboard (deployed to Netlify)
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Shared UI components
│   │   ├── services/api.js   # API client with JWT auth
│   │   └── hooks/            # useAuth, useBusinessContext
│   ├── netlify.toml          # Netlify build config
│   └── public/_redirects     # SPA fallback routing
├── marketing-site/           # Static HTML marketing site (deployed to Netlify)
│   ├── index.html
│   ├── booking-demo.html
│   ├── privacy.html
│   └── terms.html
└── .do/app.yaml              # DigitalOcean App Platform config (API + DB only)
```

---

## Backend Services

### Notifications
- **SMS**: Twilio (A2P 10DLC registered, E.164 phone normalization)
- **Email**: SendGrid with branded HTML envelope

### Notification Events
| Event | Trigger |
|---|---|
| `confirmation` | Immediately on appointment booking |
| `reminder_24h` | Daily at noon local time — sent for next open business day |
| `otw_tech_prompt` | 45–75 min before appointment — texts the technician |
| `otw_customer` | When technician replies YES to OTW prompt |
| `review_request` | When appointment is marked completed |

### Background Scheduler (APScheduler)
| Job | Interval | Description |
|---|---|---|
| `send_reminders` | Every 30 min | Fires during 11am–1pm local window; finds next open business day |
| `send_otw_prompts` | Every 15 min | Texts techs for appointments in 45–75 min window |
| `send_otw_morning_kickoffs` | Every 15 min | Morning kickoff SMS to techs for first job of the day (after 7am) |
| `generate_recurring` | Daily 6am | Pre-generates recurring appointment instances |

### Admin / Test Endpoints
All require JWT auth. Available in Settings → Developer Tools in the dashboard.

| Endpoint | Description |
|---|---|
| `POST /api/admin/trigger/reminders` | Fire reminder job now (bypasses noon window) |
| `POST /api/admin/trigger/otw-prompts` | Fire OTW tech prompt job now |
| `POST /api/admin/trigger/morning-kickoffs` | Fire morning kickoff job now |
| `GET /api/admin/scheduler/status` | Show next scheduled run times |
| `POST /api/admin/appointments/{id}/resend-confirmation` | Resend confirmation SMS + email |
| `POST /api/admin/appointments/{id}/send-reminder` | Send 24h-style reminder now |
| `POST /api/admin/appointments/{id}/send-review-request` | Send review request (requires google_review_url on business) |

### Appointments API — Sort Options
`GET /api/appointments?sort=upcoming` (default)

| Sort value | Behavior |
|---|---|
| `upcoming` | Future appointments first (soonest → latest), then past appointments (most recent first) |
| `newest` | All appointments by `scheduled_start DESC` |
| `oldest` | All appointments by `scheduled_start ASC` |

The dashboard defaults to `upcoming`. Sort buttons appear in the top-right of the Appointments tab.

---

## Local Development

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in secrets
uvicorn app.main:app --reload
```

### Frontend Dashboard
```bash
cd frontend/dashboard
npm install
npm run dev   # runs on localhost:5173, proxies /api to api.spacecoaststudios.com
```

---

## Environment Variables (Backend)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | App secret key |
| `JWT_SECRET_KEY` | JWT signing key |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Twilio sending number (E.164) |
| `SENDGRID_API_KEY` | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | Sender email address |
| `ANTHROPIC_API_KEY` | Claude API key (AI agent) |
| `BASE_URL` | Public API base URL |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
