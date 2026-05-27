# Home Services Platform

Multi-tenant home services scheduling, dispatch, and notifications platform built for Space Coast Studios.

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
