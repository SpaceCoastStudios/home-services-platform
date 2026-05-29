# Space Coast Studios — Home Services Platform

Multi-tenant AI-powered scheduling, dispatch, and notifications platform.

**Last updated:** 2026-05-29 | **Status:** Production-ready — founding client phase

---

## Table of Contents

1. [Infrastructure](#infrastructure)
2. [Environment Variables](#environment-variables)
3. [Stripe Billing](#stripe-billing)
4. [Client Onboarding — Signup Flow](#client-onboarding--signup-flow)
5. [Client Onboarding — A2P 10DLC Checklist](#client-onboarding--a2p-10dlc-checklist)
6. [AI Systems](#ai-systems)
7. [Notifications & Scheduler](#notifications--scheduler)
8. [Feature Audit — Build & Test Status](#feature-audit--build--test-status)
9. [Marketing Site Audit](#marketing-site-audit)
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

DNS: GoDaddy — `api.*` → DigitalOcean, `dashboard.*` + root → Netlify.
Auto-deploy on push to `main` for all three.

**DB access:**
```bash
psql "postgresql://doadmin:PASSWORD@host.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (DO injects automatically) |
| `SECRET_KEY` | ✅ | App secret key |
| `JWT_SECRET_KEY` | ✅ | JWT signing key |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | ✅ | Default Twilio sending number (E.164) |
| `SENDGRID_API_KEY` | ✅ | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | ✅ | Sender email |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key |
| `LLM_MODEL` | — | Default: `claude-haiku-4-5-20251001` — contact form responder only |
| `SMS_AGENT_MODEL` | — | Default: `claude-sonnet-4-6` — SMS booking agent (Sonnet required for multi-turn reasoning) |
| `STRIPE_SECRET_KEY` | ✅ | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | ✅ | `whsec_...` |
| `STRIPE_PRICE_STARTER_SETUP` | ✅ | `price_1TbXKM2MJMR8rAcZfEKeo13B` |
| `STRIPE_PRICE_STARTER_MONTHLY` | ✅ | `price_1TbXKN2MJMR8rAcZ8ageyctL` |
| `STRIPE_PRICE_PRO_SETUP` | ✅ | `price_1TbXKN2MJMR8rAcZIiW0KPMT` |
| `STRIPE_PRICE_PRO_MONTHLY` | ✅ | `price_1TbXKO2MJMR8rAcZh0yQdVOv` |
| `BASE_URL` | ✅ | `https://api.spacecoaststudios.com` |
| `ALLOWED_ORIGINS` | ✅ | CORS origins (comma-separated) |

> **Model maintenance:** Check both model strings quarterly at https://docs.anthropic.com/en/docs/about-claude/models. A wrong `LLM_MODEL` string silently sets contact submissions to "Error" status. Startup log prints `LLM model validated OK` or a WARNING.

---

## Stripe Billing

**Publishable key:** `pk_live_51TM7kZ2MJMR8rAcZ2jSBcduwtelYsLikfR9OsPACEOypphYntZ1MmdpSK7lFdMb8egcatVty5vL5h4SiB2X7sc2n00HqCzzbqd`
**Webhook:** `https://api.spacecoaststudios.com/api/billing/webhook`
**Events:** `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`

| Plan | Price ID | Amount |
|---|---|---|
| Starter Setup | `price_1TbXKM2MJMR8rAcZfEKeo13B` | $1,997 one-time |
| Starter Monthly | `price_1TbXKN2MJMR8rAcZ8ageyctL` | $249/month |
| Pro Setup | `price_1TbXKN2MJMR8rAcZIiW0KPMT` | $2,997 one-time |
| Pro Monthly | `price_1TbXKO2MJMR8rAcZh0yQdVOv` | $399/month |
| Founding Starter Setup | `price_1TbXKN2MJMR8rAcZvreEPLwo` | $497 |
| Founding Starter Monthly | `price_1TbXKN2MJMR8rAcZF8PV52FQ` | $99/month (first 3 mo) |
| Founding Pro Setup | `price_1TbXKO2MJMR8rAcZ9MRzpF2s` | $997 |
| Founding Pro Monthly | `price_1TbXKO2MJMR8rAcZMiHThRka` | $199/month (first 3 mo) |
| Test Setup | `price_1TbkYi2MJMR8rAcZO4iP0oHP` | $1.00 |
| Test Monthly | `price_1TbkkP2MJMR8rAcZAPo5kJx5` | $1.00/month |

---

## Client Onboarding — Signup Flow

### Automatic (Stripe Checkout)
1. Client clicks Get Started → `POST /api/billing/checkout` → Stripe Checkout
2. Payment → `checkout.session.completed` webhook → tenant auto-provisioned
3. Welcome email with set-password link (72-hour token)
4. Client sets password → auto-login → Setup Wizard (`/setup`, 3 steps)
5. Wizard completion sets `has_completed_setup = true`

### Manual (Founding Clients)
See `docs/founder-client-onboarding.md`.

---

## Client Onboarding — A2P 10DLC Checklist

- [ ] Purchase Twilio number in client's area code
- [ ] Create Messaging Service, add number to sender pool
- [ ] Register A2P Brand (EIN, business info)
- [ ] Create Campaign (CUSTOMER_CARE) linked to Messaging Service
- [ ] **Register phone number to Campaign** (separate from sender pool — easy to miss)
- [ ] Set inbound webhook on the **number itself**: `https://api.spacecoaststudios.com/webhook/sms/inbound`
- [ ] Set `twilio_phone_number` on Business record in Settings (platform admin, E.164 format)
- [ ] Test full contact form → SMS → booking flow

---

## AI Systems

### Contact Form AI Responder
- Model: `LLM_MODEL` (Haiku — adequate for structured email/SMS drafting)
- Triggered as BackgroundTask after `POST /contact/submit`
- Sends via one channel only based on `preferred_contact_method` + `sms_consent`
- Slots displayed in business local timezone
- SMS replies: greeting stripped, capped at 480 chars, exactly 2 slot options offered
- Draft mode: `ai_response_mode = "draft_only"` holds for staff approval

### SMS Booking Agent
- Model: `SMS_AGENT_MODEL` (Sonnet — required for multi-turn reasoning)
- Triggered on every inbound SMS to a business's Twilio number
- On each inbound: looks up most recent contact submission (last 30 days, by E.164 phone) to inject confirmed name/service/address into system prompt
- Tools: `check_availability` (mandatory every turn), `create_booking`, `escalate_to_human`, `emergency_dispatch`
- Booking creates `Appointment` with `status="confirmed"`, `source="sms"`
- Customer record enriched with email, address, city, state, zip from contact submission
- `SmsConversation.status` → `"booked"` after successful booking
- Stale conversations (>30 days or booked/escalated) closed and fresh one created on new form submission
- **Emergency flow:** `emergency_dispatch` tool — AI asks qualifying questions, confirms/collects the service address, alerts the on-call tech (address + issue in the SMS), and creates an `emergency`-status appointment (no automated notifications; excluded from scheduler jobs). On-call rotation + after-hours evaluated in business-local time.

---

## Notifications & Scheduler

| Event | Trigger |
|---|---|
| `confirmation` | Appointment created |
| `reminder_24h` | Daily 11am–1pm local window |
| `otw_tech_prompt` | 45–75 min before appointment |
| `otw_morning_kickoff` | 2h before tech's first appointment; "no jobs" variant 7–8am local |
| `otw_customer` | Tech replies YES to OTW prompt |
| `review_request` | Tech replies YES to complete prompt |
| `emergency_dispatch` | SMS agent detects emergency → alerts on-call tech + creates an `emergency`-status appointment |

**Manual triggers** (Developer Tools in Settings):
- `POST /api/admin/trigger/reminders`
- `POST /api/admin/trigger/otw-prompts`
- `POST /api/admin/trigger/morning-kickoffs`

---

## Feature Audit — Build & Test Status

### ✅ Fully Built & Smoke Tested

| Feature | Notes |
|---|---|
| Contact form widget (embed) | Address, service, problem description, SMS consent — all fields save and transmit correctly |
| Contact form AI auto-responder | Channel routing, local timezone slots, 2-slot offer, 480-char SMS cap, draft mode |
| **SMS booking agent (end-to-end)** | Form → AI reply → customer texts → agent books → confirmed appt, enriched customer record |
| Appointment creation & management | Expandable rows, Edit Details modal (technician pre-populated), problem description, address |
| Customer records | Created/enriched from SMS booking; inline edit in dashboard |
| Tech daily schedule page | Public mobile page, completed appts filtered out, city in address, problem description shown |
| Morning kickoff SMS (with appointments) | Full day summary, numbered stops, schedule URL, 2h trigger window |
| Morning kickoff SMS (idempotency) | Second manual trigger does not re-send |
| OTW tech prompt + reply flow | Confirmed → en_route → customer OTW → complete prompt → review request |
| Review request | Fires on job completion (SMS + email) |
| Appointment reminders | Next-business-day, noon local window, idempotent |
| Stripe billing | Checkout → webhook → provisioning → welcome email |
| First-login setup wizard | 3 steps, per-step save, has_completed_setup gate |
| Platform admin impersonation | Amber banner, localStorage stash/restore |
| Forgot password / reset | 1-hour token, auto-login after reset |
| Notification templates | 12 editable per-business |
| **On-call rotation + override** | Tested end-to-end; business-local timezone. Day-of-week, override (beats rotation), and fallback all verified |
| **Emergency dispatch → appointment** | Tested. AI captures address in chat, alerts on-call tech, creates `emergency`-status appointment, no auto-notifications |
| Calendar invite links | .ics + Google/Apple/Outlook/Yahoo |
| Soft delete | Appointments, customers, contact submissions |
| Twilio phone number in Settings | Platform admin sets per-business number from dashboard |

### ⏳ Built — Pending Test

| Feature | Status |
|---|---|
| Morning kickoff — no appointments variant | Waiting for tomorrow morning (7–8am local) to auto-fire |
| Edit Details modal refinement (Step 3) | Working; marked to revisit for richer detail display |

### ⚠️ Built — Backend Only (No UI)

| Feature | Notes |
|---|---|
| Self-scheduling booking widget | Availability engine complete; no public-facing widget UI yet |
| Recurring appointments | Backend router + model built; no dashboard UI page |

### 🎯 Next Session Priorities

| Priority | Task | Notes |
|---|---|---|
| ✅ | ~~Test on-call rotation + override~~ | DONE 2026-05-29 — verified end-to-end; timezone bug fixed |
| ✅ | ~~Test emergency dispatch~~ | DONE 2026-05-29 — AI captures address, tech alerted, `emergency` appointment created |
| 1 | Build recurring appointments UI | Backend complete, need `/recurring` frontend page |
| 2 | Build self-scheduling booking widget | Availability engine complete, need public widget UI |

### ❌ Not Yet Built (Roadmap)

| Feature | Notes |
|---|---|
| Visual calendar view (day/week/month) | Dashboard is list-only |
| Customer portal | Magic link login, view/reschedule appointments |
| Usage/analytics dashboard | Cross-tenant metrics |
| Emergency contact form routing | Contact form urgency → on-call dispatch |

---

## Marketing Site Audit

**Site:** https://spacecoaststudios.com

| Feature Claimed | Build Status | Notes |
|---|---|---|
| AI Contact Responder | ✅ Built & tested | Matches description |
| SMS Booking Agent | ✅ Built & tested | Matches description |
| Self-Scheduling Booking Widget | ⚠️ Backend only | Advertised as a live Pro feature on the marketing site (owner decision, 2026-05-29). Public widget UI still pending — prioritize before the first Professional client goes live. |
| Emergency Dispatch | ✅ Built & tested | Via SMS agent tool |
| Automated Notifications (confirmations, reminders, OTW) | ✅ Built & tested | Matches description |
| Automated Review Requests | ✅ Built & tested | Fires on job completion |
| Admin Dashboard | ✅ Built & tested | Matches description |
| Recurring Appointment Scheduling | ⚠️ Backend only | Advertised as a live Pro feature; delivered manually as part of the managed service (owner decision, 2026-05-29). Dashboard UI still pending. |
| Custom AI Persona & Branding | ✅ Built | AI agent name, system prompt, brand color, logo URL |
| Up to 3 service types / 5 technicians (Starter) | ✅ Built | Enforced at plan level |

**✅ SMS consent compliance — resolved (verified 2026-05-29):**
The marketing site demo widget consent copy is now correct and matches the approved A2P campaign: the checkbox is clearly **optional** ("customers can submit the form and receive service without checking it"). The demo form's submit handler was also fixed so the message it records reflects the actual checkbox state (previously it always logged "SMS consent given" regardless).

---

## API Reference

### Auth
| Endpoint | Notes |
|---|---|
| `POST /api/auth/login` | `{username, password}` → tokens |
| `POST /api/auth/refresh` | `{refresh_token}` → new token pair |
| `POST /api/auth/set-password` | Token-based, auto-login on success |
| `POST /api/auth/forgot-password` | Always 200 (prevents enumeration) |

### Contact Form (Public)
`POST /contact/submit?business_id=`

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
  "sms_consent": true
}
```
Phone normalized to E.164 on submission. `sms_consent: true` required for SMS reply.

### Public Endpoints (no auth)
- `POST /contact/submit?business_id=` — contact form
- `GET /embed/{slug}/contact` — embeddable widget iframe
- `POST /webhook/sms/inbound` — Twilio inbound handler
- `GET /schedule/tech/{token}` — technician daily schedule
- `GET /cal/{token}[/google|/ical|/outlook|/yahoo]` — calendar links

### Admin Triggers
- `POST /api/admin/trigger/reminders`
- `POST /api/admin/trigger/otw-prompts`
- `POST /api/admin/trigger/morning-kickoffs`
- `GET /api/admin/scheduler/status`

---

## Local Development

```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload  # http://localhost:8000

# Frontend
cd frontend/dashboard && npm install && npm run dev  # http://localhost:5173
```

---

## Common Pitfalls

- **Git from bash** — never run git commands from the bash sandbox (Windows filesystem lock files). All git commands in Ryan's PowerShell terminal, one per line.
- **Inbound SMS not routing** — webhook must be set on the Twilio number itself, not just the Messaging Service. Active Numbers → click number → Messaging → "A MESSAGE COMES IN".
- **SMS agent loses context** — lookup uses E.164 phone match. If contact submission was hard-deleted (not just status-closed), context is lost. Close submissions by changing status, not deleting, during active booking conversations.
- **Wrong LLM_MODEL** — silently causes "Error" status on contact submissions. Check startup log for `LLM model validated OK`.
- **Migrations** — always `ALTER TABLE ADD COLUMN IF NOT EXISTS` in `run_migrations()`. Never Alembic.
- **Slot timezone** — all slots stored in UTC, displayed in business local time. Naive datetimes from the agent are treated as business local time before UTC conversion.
- **On-call timezone** — rotation day-of-week + after-hours window evaluate in business-local time, not UTC. If `/api/oncall/current` returns the wrong tech, check `business.timezone`.
- **Customer-facing phone display** — use `app/utils/phone.format_phone_display()` for any phone shown to customers → `(321) 386-7604`. The tech emergency alert intentionally stays E.164 (`+1…`) since it's tap-to-dial only.

---

## Changelog

### 2026-05-29 — On-Call & Emergency Dispatch (Tested + Hardened)
- On-call rotation + override + fallback tested end-to-end via `/api/oncall/current` and the dashboard card
- **Timezone fix:** rotation + after-hours now evaluate in business-local time (was UTC) — `routers/oncall.py`, `services/oncall_notifier.py`
- Fixed on-call config save (empty-string `rolling_start_date` → 422)
- Emergency dispatch normalizes tech phone to E.164
- Emergency dispatch now creates an `emergency`-status appointment (dedicated Emergency Service type, on-call tech, no auto-notifications, excluded from reminder/OTW/kickoff jobs)
- SMS agent collects the service address in chat for emergencies; address flows to the tech alert + appointment
- Soft-deleted customers skipped in the emergency phone lookup
- `emergency` status: red dashboard badge, filter button, Mark Complete enabled
- Customer-facing phone numbers formatted `(321) 386-7604` (SMS agent, contact responder, notification templates); new `app/utils/phone.py`. Tech alert stays E.164.
- Full test plan + results: `docs/on-call-emergency-testing.md`

### 2026-05-29 — Testing Plan Completion & Bug Fixes
- Embed form JS payload was missing address fields entirely (root cause of address never saving)
- Tech schedule: completed appointments filtered out; city added to address display
- SMS bookings now populate `problem_description` from contact form submission
- Contact submission phone lookup: fixed timezone-aware vs naive datetime comparison
- Customer enrichment on booking: email, address, city, state, zip all now populated
- Edit Details modal: async technician loading + int/string type coercion fix
- Testing plan: Steps 1–5, 7–8 ✅ | Step 6 ⏳ (no-appointments kickoff, pending tomorrow)

### 2026-05-29 — SMS Booking Agent (End-to-End Working)
- Full flow tested and confirmed: contact form → AI SMS → text-to-book → confirmed appointment
- Phone normalized to E.164 at contact form submission
- Live DB lookup on every inbound SMS for agent context (replaces unreliable seeding)
- Mandatory `check_availability` on every agent turn
- Initial slot offer capped at exactly 2
- Timezone fix: slots in business local time; naive datetimes treated as local not UTC
- SMS bookings: `confirmed` status, no duplicate confirmation SMS
- `SMS_AGENT_MODEL` = Sonnet; `LLM_MODEL` = Haiku (contact responder only)
- Twilio phone number field in Settings (platform admin)

### 2026-05-28 — Problem Description, Tech Schedule, Soft Delete, Compliance
- Problem description on contact form and appointments
- Tech daily schedule page (public, mobile, per-tech token)
- Morning kickoff: 2h trigger, full day summary, no-appointments variant
- Soft delete for appointments, customers, contact submissions
- SMS consent gate (A2P compliance — optional checkbox, approved campaign)
- Contact responder channel awareness

### 2026-05-27 — Auth, Billing, Impersonation
- Forgot-password flow, platform admin impersonation, first-login setup wizard
- Stripe billing fully configured and tested
- Notification templates, on-call rotation + override

### 2026-05-26 — Core Platform
- Address fields, phone E.164, appointment confirmation SMS
- Reminder scheduler, admin manual triggers, Developer Tools panel
- Calendar invite links
