# SCS Platform -- Complete API Reference

> Reference doc split from CLAUDE.md Section 16.
> Update this file when new endpoints are added or existing ones change.
> The actual router files in `backend/app/routers/` are always authoritative.

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
