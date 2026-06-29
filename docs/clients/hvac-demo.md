# HVAC Demo Tenant (not yet provisioned)

| Field | Value |
|---|---|
| Slug | TBD |
| Business ID | TBD |
| Name | TBD (e.g. "Space Coast Air") |
| AI Agent Name | TBD |
| Brand Color | TBD |
| Twilio Number | TBD -- needs a new number purchased |
| is_demo | true |
| Provisioned | Not yet |

## Purpose
HVAC vertical demo tenant. Will power `marketing-site/hvac.html` (not yet built).
Follows the same pattern as Brevard Pool Pros (Track C parameterized onboarding seeder).

## A2P / Twilio Setup
- A new Twilio number will need to be purchased when this tenant is created
- Add to Messaging Service MG3632cd4bd3fab9bebf5460759c8234df sender pool
- Register to the approved CUSTOMER_CARE campaign (no new TCR submission needed)
- Configure number-level inbound webhook: `https://api.spacecoaststudios.com/webhook/sms/inbound` (POST)
- Note: +13213862298 was originally considered for this tenant but was reassigned to Launchpad Demo (2026-06-29)

## Setup Checklist (when ready to build HVAC vertical)
- [ ] Purchase a new Twilio number
- [ ] Add to Messaging Service sender pool + register to campaign
- [ ] Decide business name and AI agent name
- [ ] Run a seed script (clone `seed_pool_demo.py`, adapt for HVAC services/copy)
- [ ] Set the number on the tenant record in DB
- [ ] Configure number-level inbound webhook in Twilio console
- [ ] Build `marketing-site/hvac.html` (clone pool.html structure, HVAC copy)
- [ ] Test AI agent SMS flow end-to-end
- [ ] Set Google Review URL before any prospect demo
