> **ARCHIVED — March 2026 original pre-build specification.**
> This document describes the intended architecture before the project was built.
> Many things were built differently or not yet built (voice agent, chat widget, SQLite → PostgreSQL, Alembic → manual migrations).
> **For current architecture and status, see `CLAUDE.md` in the repo root.**

---

# Home Services Customer Management Platform — Architecture Plan

**Version:** 1.1 (MVP)
**Date:** March 28, 2026

---

## 1. Executive Summary

This document outlines the architecture for a full-stack home services platform that handles customer calls and inquiries, schedules appointments based on availability rules, and provides a management dashboard. The MVP covers four user-facing channels (AI voice agent, website chatbot, contact form auto-responder, and admin dashboard) backed by a unified scheduling engine, notification system, and calendar integration that lets customers add appointments to Google Calendar, Apple Calendar (iCal), Outlook, and other calendar apps with one click.

---

## 2. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐     │
│  │ AI Voice   │  │ Chat       │  │ Contact    │  │ Admin Dashboard    │     │
│  │ Agent      │  │ Widget     │  │ Form       │  │ (React + Tailwind) │     │
│  │ (Twilio +  │  │ (React)    │  │ (Website)  │  │                    │     │
│  │  LLM)      │  │            │  │            │  │                    │     │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └────────┬───────────┘     │
│        │               │               │                   │                 │
└────────┼───────────────┼───────────────┼───────────────────┼─────────────────┘
         │               │               │                   │
         ▼               ▼               ▼                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          API LAYER (FastAPI)                                  │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐     │
│  │ /voice/*   │  │ /chat/*    │  │ /contact/* │  │ /api/*             │     │
│  │ Twilio     │  │ WebSocket  │  │ Form       │  │ REST endpoints     │     │
│  │ webhooks   │  │ handler    │  │ handler    │  │ (CRUD + auth)      │     │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └────────┬───────────┘     │
│        │               │               │                   │                 │
│        ▼               ▼               ▼                   ▼                 │
│  ┌──────────────────────────────────────────────────────────────────────┐     │
│  │                       CORE SERVICES                                 │     │
│  │                                                                     │     │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────┐ ┌──────────────┐   │     │
│  │  │ Scheduling │ │ AI/NLP     │ │ Notification │ │ Calendar     │   │     │
│  │  │ Engine     │ │ Service    │ │ Service      │ │ Link Service │   │     │
│  │  └────────────┘ └────────────┘ └──────────────┘ └──────────────┘   │     │
│  └──────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                        │
│                                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────────┐     │
│  │ SQLite DB  │  │ LLM API    │  │ Twilio API │  │ SendGrid /         │     │
│  │ (→Postgres │  │ (OpenAI /  │  │ (Voice +   │  │ SMTP               │     │
│  │  in prod)  │  │  Anthropic)│  │  SMS)      │  │ (Email)            │     │
│  └────────────┘  └────────────┘  └────────────┘  └────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python 3.11 + FastAPI | Async support, great for AI integrations, auto-generated API docs |
| **Database** | SQLite (MVP) → PostgreSQL (prod) | Zero-config for MVP; SQLAlchemy ORM makes migration seamless |
| **ORM** | SQLAlchemy 2.0 + Alembic | Type-safe models, migration management |
| **Frontend** | React 18 + Tailwind CSS + Vite | Fast development, component reuse across dashboard and chat widget |
| **Voice** | Twilio Programmable Voice + TwiML | Industry standard, reliable telephony with webhook-based control |
| **AI/LLM** | Anthropic Claude API or OpenAI GPT-4 | Conversational understanding for voice and chat agents |
| **SMS** | Twilio Messaging | Same platform as voice — unified billing and management |
| **Email** | SendGrid or SMTP | Transactional emails for confirmations and reminders |
| **Auth** | JWT tokens + bcrypt | Simple, stateless auth for MVP |
| **Task Queue** | APScheduler (MVP) → Celery (prod) | Reminder scheduling, async notification dispatch |

---

## 4. Database Schema

### 4.1 Entity Relationship Overview

```
customers ─────────< appointments >───────── technicians
    │                    │
    │                    │
    │               service_types
    │
    └──────────< contact_submissions

admin_users          business_hours
                     blocked_times

inquiry_logs         notification_logs
```

### 4.2 Table Definitions

#### `customers`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | Unique customer ID |
| first_name | VARCHAR(100) | NOT NULL | |
| last_name | VARCHAR(100) | NOT NULL | |
| phone | VARCHAR(20) | NOT NULL, UNIQUE | Primary contact number |
| email | VARCHAR(255) | NULLABLE | |
| address | TEXT | NULLABLE | Service address |
| zip_code | VARCHAR(10) | NULLABLE | For service area matching |
| notes | TEXT | NULLABLE | Internal notes |
| created_at | DATETIME | DEFAULT NOW | |
| updated_at | DATETIME | AUTO | |

#### `service_types`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| name | VARCHAR(100) | NOT NULL | e.g., "Plumbing Repair" |
| category | VARCHAR(50) | NOT NULL | e.g., "plumbing", "electrical", "hvac" |
| description | TEXT | NULLABLE | Customer-facing description |
| duration_minutes | INTEGER | NOT NULL | Default appointment length |
| base_price | DECIMAL(10,2) | NULLABLE | Starting price (if shown to customers) |
| is_active | BOOLEAN | DEFAULT TRUE | Soft-disable services |

#### `technicians`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| name | VARCHAR(200) | NOT NULL | |
| phone | VARCHAR(20) | NULLABLE | |
| email | VARCHAR(255) | NULLABLE | |
| skills | JSON | NOT NULL | List of service_type category strings |
| is_active | BOOLEAN | DEFAULT TRUE | |

#### `business_hours`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| day_of_week | INTEGER | 0-6, NOT NULL | 0=Monday, 6=Sunday |
| open_time | TIME | NOT NULL | e.g., 08:00 |
| close_time | TIME | NOT NULL | e.g., 17:00 |
| is_active | BOOLEAN | DEFAULT TRUE | Whether the business operates this day |

#### `blocked_times`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| technician_id | INTEGER | FK → technicians, NULLABLE | NULL = block for entire business |
| start_datetime | DATETIME | NOT NULL | |
| end_datetime | DATETIME | NOT NULL | |
| reason | VARCHAR(255) | NULLABLE | e.g., "Holiday", "Training" |

#### `appointments`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| customer_id | INTEGER | FK → customers, NOT NULL | |
| technician_id | INTEGER | FK → technicians, NULLABLE | NULL until assigned |
| service_type_id | INTEGER | FK → service_types, NOT NULL | |
| scheduled_start | DATETIME | NOT NULL | |
| scheduled_end | DATETIME | NOT NULL | |
| status | VARCHAR(20) | NOT NULL | "pending", "confirmed", "in_progress", "completed", "cancelled", "no_show" |
| source | VARCHAR(20) | NOT NULL | "phone", "chat", "dashboard", "website", "contact_form" |
| address | TEXT | NULLABLE | Override customer address if different |
| notes | TEXT | NULLABLE | |
| calendar_token | VARCHAR(64) | UNIQUE, NOT NULL | Random token for secure calendar link generation |
| calendar_links_sent | BOOLEAN | DEFAULT FALSE | Whether calendar links have been delivered |
| created_at | DATETIME | DEFAULT NOW | |
| updated_at | DATETIME | AUTO | |

#### `inquiry_logs`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| customer_id | INTEGER | FK → customers, NULLABLE | Linked if identified |
| channel | VARCHAR(20) | NOT NULL | "phone", "chat" |
| summary | TEXT | NOT NULL | AI-generated summary of the inquiry |
| transcript | TEXT | NULLABLE | Full conversation transcript |
| resolved | BOOLEAN | DEFAULT FALSE | |
| created_at | DATETIME | DEFAULT NOW | |

#### `contact_submissions`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| customer_id | INTEGER | FK → customers, NULLABLE | Linked after customer match/creation |
| name | VARCHAR(200) | NOT NULL | Submitted name |
| email | VARCHAR(255) | NOT NULL | Submitted email |
| phone | VARCHAR(20) | NULLABLE | Submitted phone |
| service_requested | VARCHAR(100) | NULLABLE | Service category or free-text |
| message | TEXT | NOT NULL | Customer's inquiry message |
| preferred_date | DATE | NULLABLE | Customer's preferred appointment date |
| preferred_time | VARCHAR(20) | NULLABLE | e.g., "morning", "afternoon", "2:00 PM" |
| ai_response | TEXT | NULLABLE | The AI-generated response sent to the customer |
| ai_suggested_slots | JSON | NULLABLE | Slots the AI offered based on availability |
| status | VARCHAR(20) | DEFAULT "new" | "new", "ai_responded", "human_review", "appointment_booked", "closed" |
| appointment_id | INTEGER | FK → appointments, NULLABLE | Linked if an appointment was booked |
| responded_at | DATETIME | NULLABLE | When the auto-response was sent |
| created_at | DATETIME | DEFAULT NOW | |

#### `notification_logs`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| appointment_id | INTEGER | FK → appointments | |
| type | VARCHAR(10) | NOT NULL | "sms", "email" |
| event | VARCHAR(30) | NOT NULL | "confirmation", "reminder_24h", "reminder_1h", "cancellation" |
| sent_at | DATETIME | DEFAULT NOW | |
| status | VARCHAR(20) | NOT NULL | "sent", "failed", "delivered" |

#### `admin_users`
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTO | |
| username | VARCHAR(100) | UNIQUE, NOT NULL | |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| role | VARCHAR(20) | DEFAULT "admin" | "admin", "dispatcher", "viewer" |
| is_active | BOOLEAN | DEFAULT TRUE | |

---

## 5. API Endpoints

### 5.1 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Admin login, returns JWT |
| POST | `/api/auth/refresh` | Refresh access token |

### 5.2 Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/customers` | List customers (paginated, searchable) |
| GET | `/api/customers/{id}` | Get customer details + appointment history |
| POST | `/api/customers` | Create customer |
| PUT | `/api/customers/{id}` | Update customer |

### 5.3 Service Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/services` | List all active service types |
| POST | `/api/services` | Create service type |
| PUT | `/api/services/{id}` | Update service type |
| DELETE | `/api/services/{id}` | Soft-delete service type |

### 5.4 Technicians

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/technicians` | List technicians |
| POST | `/api/technicians` | Create technician |
| PUT | `/api/technicians/{id}` | Update technician |
| GET | `/api/technicians/{id}/schedule` | Get technician's appointment schedule |

### 5.5 Scheduling

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/availability` | Get available slots (params: service_type_id, date_range, technician_id?) |
| POST | `/api/appointments` | Book an appointment |
| PUT | `/api/appointments/{id}` | Update appointment (reschedule, change status) |
| GET | `/api/appointments` | List appointments (filterable by date, status, technician) |
| GET | `/api/appointments/{id}` | Get appointment details |
| POST | `/api/appointments/{id}/cancel` | Cancel appointment |

### 5.6 Business Hours & Blocked Times

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/business-hours` | Get all business hour rules |
| PUT | `/api/business-hours` | Update business hours (batch) |
| GET | `/api/blocked-times` | List blocked time ranges |
| POST | `/api/blocked-times` | Create a blocked time range |
| DELETE | `/api/blocked-times/{id}` | Remove a blocked time |

### 5.7 Contact Form

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contact/submit` | Public endpoint — receives contact form submissions from the website |
| GET | `/api/contact-submissions` | List all contact submissions (admin, filterable by status) |
| GET | `/api/contact-submissions/{id}` | Get submission details + AI response |
| PUT | `/api/contact-submissions/{id}` | Update status, add notes, or link to appointment |
| POST | `/api/contact-submissions/{id}/respond` | Manually send a follow-up response |

### 5.8 Calendar Links

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cal/{token}/google` | Redirects to Google Calendar "add event" URL |
| GET | `/cal/{token}/ical` | Downloads .ics file (Apple Calendar, Outlook, etc.) |
| GET | `/cal/{token}/outlook` | Redirects to Outlook.com "add event" URL |
| GET | `/cal/{token}/yahoo` | Redirects to Yahoo Calendar "add event" URL |
| GET | `/cal/{token}` | Landing page with all calendar options + appointment details |

### 5.9 Voice Agent (Twilio Webhooks)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/voice/incoming` | Twilio webhook — handles incoming calls |
| POST | `/voice/gather` | Processes speech/DTMF input during a call |
| POST | `/voice/status` | Call status callback |

### 5.10 Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/chat/ws` | WebSocket connection for real-time chat |
| GET | `/api/inquiries` | List inquiry logs |
| GET | `/api/inquiries/{id}` | Get inquiry details with transcript |

### 5.11 Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | List notification logs |
| POST | `/api/notifications/test` | Send a test notification |

---

## 6. Core Service Designs

### 6.1 Scheduling Engine

The scheduling engine is the heart of the system. It determines available time slots based on layered rules:

**Availability Calculation Algorithm:**

```
function getAvailableSlots(service_type_id, date_range):
    1. Get the service type's duration
    2. Get business hours for each day in the range
    3. Get all technicians with matching skills
    4. For each day in range:
        a. Check if business is open (business_hours table)
        b. For each qualified technician:
            i.   Get their existing appointments for the day
            ii.  Get any blocked_times overlapping the day
            iii. Generate candidate slots (e.g., every 30 min within business hours)
            iv.  Remove slots that conflict with existing appointments
            v.   Remove slots that overlap blocked times
            vi.  Remove slots where remaining time < service duration
        c. Aggregate available slots across all technicians
    5. Return slots grouped by date, each with available technician(s)
```

**Slot granularity:** 30-minute increments (configurable).

**Conflict detection:** A technician cannot have overlapping appointments. A 15-minute buffer between appointments is included by default to account for travel and wrap-up.

**Auto-assignment:** When booking, the system assigns the first available technician with the right skills. Admins can override and manually assign.

### 6.2 AI Voice Agent

The voice agent uses Twilio's Programmable Voice to receive calls and an LLM to conduct natural conversations.

**Call Flow:**

```
Customer calls → Twilio routes to /voice/incoming
    → System greets customer
    → LLM-powered conversation loop:
        1. Listen to customer speech (Twilio STT)
        2. Send transcribed text to LLM with system prompt + context
        3. LLM determines intent:
           - Schedule appointment → invoke scheduling engine
           - Ask about services/pricing → retrieve from DB and respond
           - Ask about existing appointment → look up by phone number
           - Complex/escalation → transfer to human (or take message)
        4. Convert LLM response to speech (Twilio TTS)
        5. Repeat until resolved or call ends
    → Log inquiry with transcript
    → Send confirmation SMS if appointment booked
```

**LLM System Prompt (summary):** The agent is given context about available services, pricing, business hours, and access to tool-calling functions for `check_availability`, `book_appointment`, `lookup_customer`, and `get_service_info`. This allows it to perform real actions during a conversation.

### 6.3 Chat Widget

The chat widget mirrors the voice agent's capabilities but through a text-based WebSocket interface.

**Architecture:**
- Embeddable `<script>` tag that injects a floating chat bubble on any website
- WebSocket connection to `/chat/ws` for real-time messaging
- Same LLM backend and tool-calling functions as the voice agent
- Customer identification via phone number or email (asked during chat)
- Conversation persistence so customers can return to ongoing chats

### 6.4 Contact Form Auto-Responder

When a customer submits the contact form on the website, the system processes it through an AI pipeline that generates a helpful response, suggests available appointment slots, and sends it to the customer — all within seconds.

**Submission Flow:**

```
Customer fills out contact form on website
    → POST /contact/submit (public, rate-limited, honeypot + CAPTCHA protected)
    → System creates contact_submission record (status: "new")
    → Customer match: search by email/phone → link to existing customer or create new
    → AI Processing:
        1. Analyze the message to determine intent and service type
        2. If appointment-related:
           a. Query scheduling engine for available slots matching preferences
           b. Generate response with 3-5 suggested time slots
           c. Include one-click booking links for each slot
        3. If general inquiry (pricing, service area, etc.):
           a. Retrieve relevant info from DB (services, pricing, hours)
           b. Generate helpful response with accurate business info
        4. If complex/unclear:
           a. Generate a polite acknowledgment with estimated response time
           b. Flag for human review (status: "human_review")
    → Send AI response via email (and SMS if phone provided)
    → Update status to "ai_responded"
    → Log in dashboard for admin visibility
```

**Auto-Response Email Template Structure:**
- Personalized greeting
- Direct answer to their question or suggested appointment slots
- One-click booking links (if slots were offered)
- Calendar integration links (if appointment confirmed)
- Business contact info and hours
- Note that a team member will follow up if needed

**Admin Dashboard Integration:**
- Contact submissions appear in a dedicated queue on the dashboard
- Admins can review AI responses before or after they're sent (configurable)
- Admins can manually respond, override AI suggestions, or escalate
- Submissions that result in bookings are automatically linked to the appointment

**Configuration Options (admin-settable):**
- Auto-respond immediately vs. hold for human review
- Response tone and business-specific instructions for the AI
- Maximum number of suggested slots per response
- Whether to include pricing in auto-responses
- Quiet hours (delay responses until business hours)

### 6.5 Calendar Link Service

Every appointment confirmation includes "Add to Calendar" links so customers can save their appointment to their preferred calendar app with a single click. This works without any API keys or OAuth — it uses universal calendar URL schemes and the .ics standard.

**Supported Calendar Platforms:**

| Platform | Method | How It Works |
|----------|--------|-------------|
| **Google Calendar** | URL redirect | Constructs a `calendar.google.com/calendar/render` URL with event params |
| **Apple Calendar (iCal)** | .ics file download | Generates a standard .ics (iCalendar) file that opens in Apple Calendar |
| **Microsoft Outlook** | URL redirect | Constructs an `outlook.live.com/calendar/action/compose` URL |
| **Outlook Desktop** | .ics file download | Same .ics file works for desktop Outlook |
| **Yahoo Calendar** | URL redirect | Constructs a `calendar.yahoo.com` URL with event params |
| **Any other app** | .ics file download | The .ics standard is universally supported |

**How Calendar Links Are Generated:**

Each appointment receives a unique `calendar_token` (a 64-character random string) at creation time. This token is used in public-facing URLs like `/cal/{token}/google` so that no authentication is required for the customer, but links cannot be guessed.

**iCalendar (.ics) File Contents:**

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//HomeServices//Appointment//EN
BEGIN:VEVENT
UID:{appointment_id}@homeservices.com
DTSTART:20260401T140000Z
DTEND:20260401T160000Z
SUMMARY:Plumbing Repair - HomeServices Co.
DESCRIPTION:Service: Plumbing Repair\nTechnician: John Smith\nAddress: 123 Main St
LOCATION:123 Main St, Anytown, ST 12345
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-PT1H
DESCRIPTION:Appointment reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR
```

**Calendar Landing Page (`/cal/{token}`):**

A simple, mobile-friendly page that shows:
- Appointment date, time, and duration
- Service type and technician name
- Service address
- Prominent "Add to Calendar" buttons for each platform (Google, Apple, Outlook, Yahoo)
- A "Download .ics file" fallback link
- Option to reschedule or cancel (links back to system)

**Where Calendar Links Appear:**
- Confirmation email (all platforms listed as buttons)
- Confirmation SMS (short link to the calendar landing page)
- Contact form auto-responses (when an appointment is booked)
- Dashboard appointment detail view (for admin reference)
- Reminder emails (re-include calendar links)

### 6.6 Notification Service

**Automated notification triggers:**
- **Booking confirmation** — immediately after appointment is created (SMS + email) — includes "Add to Calendar" links
- **24-hour reminder** — sent the day before the appointment (SMS + email) — re-includes calendar links
- **1-hour reminder** — sent 1 hour before (SMS only)
- **Cancellation notice** — when an appointment is cancelled (SMS + email)
- **Reschedule notice** — when date/time changes (SMS + email) — includes updated calendar links
- **Contact form auto-response** — AI-generated reply with suggested slots or answers (email + optional SMS)

**Email Template Structure (Confirmation Example):**
- Subject: "Your [Service Type] Appointment is Confirmed — [Date]"
- Appointment details (date, time, service, technician, address)
- **"Add to Your Calendar" button row:** Google Calendar | Apple Calendar | Outlook | Download .ics
- What to expect / preparation notes
- Reschedule or cancel link
- Business contact information

**SMS Template (Confirmation Example):**
- "Hi [Name]! Your [Service] appt is confirmed for [Date] at [Time]. Add to calendar: [short link to /cal/{token}]. Reply HELP for assistance."

**Implementation:** APScheduler runs a background job every 5 minutes, checking for upcoming appointments that need reminders. Notification templates are stored as configurable strings with variable placeholders (customer name, date, time, service type, technician name, address, calendar links).

---

## 7. Admin Dashboard — Key Screens

### 7.1 Dashboard Home
- Today's appointment count and upcoming schedule
- Unresolved inquiry count
- Quick stats: bookings this week, cancellation rate, popular services

### 7.2 Calendar View
- Day/week/month calendar showing all appointments
- Color-coded by service category
- Click to view/edit appointment details
- Drag to reschedule

### 7.3 Appointment Management
- List view with filters (date range, status, technician, service type)
- Create new appointment manually
- Edit, cancel, mark complete

### 7.4 Customer Directory
- Searchable customer list
- Customer detail page with appointment history and inquiry logs

### 7.5 Service Configuration
- Add/edit service types with name, category, duration, pricing
- Manage technicians and their skill assignments

### 7.6 Availability Settings
- Business hours editor (per day of week)
- Blocked times manager (create/remove blocked periods)

### 7.7 Contact Form Queue
- List of all website contact submissions with status filters (new, ai_responded, human_review, booked, closed)
- View the customer's message alongside the AI-generated response
- One-click actions: approve AI response, edit and send, convert to appointment, escalate
- Metrics: average response time, conversion rate (submission → booking)

### 7.8 Inquiry Log
- List of all voice and chat inquiries
- View transcripts and resolution status

---

## 8. Project Structure

```
home-services-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Settings and environment vars
│   │   ├── database.py             # SQLAlchemy engine and session
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── customer.py
│   │   │   ├── appointment.py
│   │   │   ├── service_type.py
│   │   │   ├── technician.py
│   │   │   ├── business_hours.py
│   │   │   ├── blocked_time.py
│   │   │   ├── inquiry.py
│   │   │   ├── contact_submission.py
│   │   │   ├── notification.py
│   │   │   └── admin_user.py
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── routers/                # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── customers.py
│   │   │   ├── appointments.py
│   │   │   ├── services.py
│   │   │   ├── technicians.py
│   │   │   ├── availability.py
│   │   │   ├── voice.py
│   │   │   ├── chat.py
│   │   │   ├── contact.py          # Contact form submission + auto-response
│   │   │   ├── calendar_links.py   # Public calendar link endpoints
│   │   │   └── notifications.py
│   │   ├── services/               # Business logic
│   │   │   ├── scheduling.py       # Availability engine
│   │   │   ├── ai_agent.py         # LLM integration + tool calling
│   │   │   ├── contact_responder.py # AI auto-response for contact form
│   │   │   ├── calendar_service.py # .ics generation + calendar URL builder
│   │   │   ├── notification.py     # SMS + email dispatch
│   │   │   └── voice_handler.py    # Twilio voice flow management
│   │   ├── templates/              # Email HTML templates
│   │   │   ├── confirmation.html   # Appointment confirmation with calendar buttons
│   │   │   ├── reminder.html       # Reminder email
│   │   │   ├── contact_response.html # Auto-response to contact form
│   │   │   └── calendar_page.html  # Calendar link landing page
│   │   └── utils/
│   │       ├── auth.py             # JWT creation/validation
│   │       ├── ics_generator.py    # iCalendar (.ics) file builder
│   │       └── twilio_client.py    # Twilio SDK wrapper
│   ├── alembic/                    # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── dashboard/                  # Admin dashboard (React app)
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   ├── services/           # API client functions
│   │   │   └── App.jsx
│   │   ├── package.json
│   │   └── vite.config.js
│   └── chat-widget/                # Embeddable chat widget
│       ├── src/
│       │   ├── ChatWidget.jsx
│       │   ├── styles.css
│       │   └── embed.js            # Self-executing embed script
│       └── package.json
├── docker-compose.yml              # Local dev environment
└── README.md
```

---

## 9. Phased Implementation Roadmap

### Phase 1 — Foundation (Week 1-2)
- Set up project structure (backend + frontend scaffolding)
- Implement database models and migrations
- Build CRUD APIs for customers, services, technicians
- Build business hours and blocked times management
- Admin authentication (JWT)
- Basic dashboard layout with navigation

### Phase 2 — Scheduling Engine + Calendar Links (Week 3)
- Implement availability calculation algorithm
- Build appointment creation with conflict detection
- Calendar token generation on appointment creation
- Calendar link service: .ics file generation, Google/Outlook/Yahoo URL builders
- Calendar landing page (`/cal/{token}`) with "Add to Calendar" buttons
- Calendar view on dashboard
- Appointment list with filters and status management

### Phase 3 — AI Voice Agent (Week 4-5)
- Twilio account setup and phone number provisioning
- Incoming call webhook handler
- LLM integration with tool-calling for scheduling actions
- Speech-to-text and text-to-speech pipeline
- Call logging and transcript storage

### Phase 4 — Chat Widget (Week 5-6)
- WebSocket server for real-time messaging
- Chat UI component (React)
- Embed script for third-party websites
- Shared AI agent logic between voice and chat

### Phase 5 — Contact Form Auto-Responder (Week 6)
- Public contact form submission endpoint with rate limiting and spam protection
- AI auto-response pipeline (analyze message → query availability → generate response)
- Contact form email templates with suggested slots and booking links
- Contact submission queue on admin dashboard
- Admin controls: review, override, or manually respond

### Phase 6 — Notifications + Calendar Integration (Week 7-8)
- Twilio SMS integration for confirmations and reminders
- Email service with HTML templates including "Add to Calendar" button rows
- Calendar links embedded in all confirmation and reminder notifications
- Contact form auto-response email delivery
- Background scheduler for automated reminder dispatch
- Notification log and dashboard view

### Phase 7 — Polish & Testing (Week 8-9)
- End-to-end testing of all booking flows (voice → appointment → calendar link → notification)
- Contact form → AI response → booking conversion flow testing
- Calendar link testing across platforms (Google, Apple, Outlook, Yahoo)
- Dashboard UX refinements
- Error handling and edge cases
- Seed data and demo mode
- Documentation

---

## 10. External Service Requirements

Before development begins, you'll need accounts for:

| Service | Purpose | Cost (MVP) |
|---------|---------|------------|
| **Twilio** | Phone number, voice calls, SMS | ~$1/mo for number + per-minute/message usage |
| **Anthropic or OpenAI** | LLM for voice/chat agent | Pay-per-token, typically $5-20/mo for MVP traffic |
| **SendGrid** (or similar) | Transactional email | Free tier covers MVP volume |

---

## 11. Key Design Decisions & Trade-offs

**SQLite for MVP:** Keeps the setup zero-dependency. The SQLAlchemy ORM means switching to PostgreSQL later requires only a connection string change and a migration step. For a single-server MVP, SQLite handles the concurrency just fine.

**Shared AI agent between voice and chat:** Both channels use the same LLM system prompt and tool-calling functions. This ensures consistent behavior and means improvements to the agent benefit both channels simultaneously.

**30-minute slot granularity:** Balances flexibility with simplicity. Most home service jobs are 1-2 hours, so 30-minute booking slots give enough precision without overwhelming the calendar.

**15-minute buffer between appointments:** Accounts for technician travel time and job wrap-up. This is configurable per service type in later iterations.

**JWT auth (not sessions):** Stateless authentication simplifies the backend and works well with the React SPA dashboard. For MVP, access + refresh token pattern is sufficient.

**Calendar links via URL schemes (no OAuth):** Rather than integrating with Google Calendar API or Microsoft Graph (which require OAuth flows and API keys), the system uses universal calendar URL schemes and the .ics standard. Google Calendar's `/render` URL, Outlook's `/compose` URL, and Yahoo's event URL all accept query parameters for event details — no authentication required from the customer. The .ics file format is supported by virtually every calendar application. This approach is zero-configuration, works immediately, and covers all major platforms without ongoing API maintenance.

**Contact form AI auto-responder with human oversight:** The system auto-responds to contact form submissions using AI, but defaults to a "respond then review" model rather than requiring pre-approval. Admins see every AI response in the dashboard and can intervene. This strikes a balance between fast customer response times (seconds, not hours) and maintaining quality control. The mode can be switched to "hold for review" for businesses that prefer manual approval.

**Token-based public URLs for calendar links and booking actions:** Rather than requiring customers to log in, appointment-specific actions (calendar links, reschedule, cancel) use unique random tokens in the URL. This is the same pattern used by services like Calendly and most appointment confirmation emails. Tokens are 64 characters long, making them effectively unguessable.

---

*This document serves as the blueprint for the Home Services Customer Management Platform MVP. Each section can be expanded as development progresses and new requirements surface.*
