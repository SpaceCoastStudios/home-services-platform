# SCS Platform -- Repository Structure

> Reference doc split from CLAUDE.md Section 7.
> Update this file when files are added, moved, or removed.
> The actual filesystem is always authoritative -- this doc provides context on what each file does.

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
