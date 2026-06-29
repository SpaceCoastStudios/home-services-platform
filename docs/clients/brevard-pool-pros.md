# Brevard Pool Pros

| Field | Value |
|---|---|
| Slug | `brevard-pool-pros` |
| Business ID | (check DB -- provisioned via seed script) |
| Name | Brevard Pool Pros |
| AI Agent Name | Marina |
| Brand Color | `#0891b2` |
| Twilio Number | `+13213984101` |
| is_demo | true |
| Provisioned | 2026-06-10 via `backend/scripts/seed_pool_demo.py` |

## Purpose
Pool service vertical demo tenant. Used by `marketing-site/pool.html`.
Track C parameterized onboarding seeder -- this tenant is the first instance of the pattern.

## A2P / Twilio Setup
- Added to SCS's existing approved CUSTOMER_CARE campaign (no new TCR submission needed)
- Number in Messaging Service sender pool: yes
- Number registered to campaign: yes
- Number-level inbound webhook: `https://api.spacecoaststudios.com/webhook/sms/inbound` (POST)
- Messaging Service set to defer to sender's webhook
- Fallback webhook: intentionally empty
- Status: Live -- Marina SMS agent verified 2026-06-10

## Twilio Numbers -- Pool Demo
Two numbers purchased for SCS demo use, both on the approved CUSTOMER_CARE campaign (Messaging Service MG3632cd4bd3fab9bebf5460759c8234df):

| Number | Role | Inbound Webhook |
|---|---|---|
| `+13213984101` | **Active -- Brevard Pool Pros tenant** | Set at number level (verified live 2026-06-10) |
| `+13213862298` | **Reserved -- HVAC demo tenant (not yet provisioned)** | Not yet configured |

**Recommendation:** Keep `+13213984101` on the pool tenant (proven working). Use `+13213862298` when the HVAC demo tenant is created. If the pool tenant DB record was updated to `+13213862298`, revert it to `+13213984101` and configure the inbound webhook on `+13213984101` instead -- Marina was verified on that number.

## Seeding
Run `python backend/scripts/seed_pool_demo.py` locally (not from Cowork sandbox -- proxy blocks API writes).
Script is re-run safe. Creates: business + Marina persona + hours + 5 pool services + 2 techs + 4 customers (fictional 555 numbers) + 3 weekly recurring schedules. Does NOT create appointments or fire notifications.

## Notes
- Google Review URL: placeholder -- set a real URL before prospect demos
- Wording audit done: no "route-based scheduling" language (feature not built); "recurring weekly service / stop list / daily schedule" language is correct
