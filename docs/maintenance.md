# SCS Platform — Periodic Maintenance Schedule

> This file is part of the Space Coast Studios project documentation.
> Source of truth for recurring maintenance tasks.
> **Update this file** when maintenance cadences or task IDs change.

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
| **SMS_AGENT_MODEL** | Verify `claude-sonnet-5` (or current value) is still valid at same URL | Update default in `config.py`; optionally add `SMS_AGENT_MODEL` to DO env vars to override |
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
