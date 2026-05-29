# On-Call & Emergency Dispatch — Test Plan & Results

**Last run:** 2026-05-29 · **Tester:** Ryan · **Business under test:** demo (business_id = 1)
**Result:** ✅ All tests passed. Two bugs found and fixed during testing (on-call timezone; on-call config save).

This document is the repeatable test plan for the on-call routing and emergency dispatch features. Re-run it after any change to `routers/oncall.py`, `services/oncall_notifier.py`, `services/sms_agent.py`, or `services/scheduler.py`.

---

## Prerequisites

- On-call enabled for the business (Settings tab on `/oncall`).
- At least 2 technicians with valid phone numbers (10-digit or E.164 both fine — dispatch normalizes).
- `twilio_phone_number` set on the business (Settings page, platform admin).
- A phone you control to send the inbound "customer" SMS, and a phone you can watch for the tech alert.

### How to call the authenticated API (PowerShell)

```powershell
$base = "https://api.spacecoaststudios.com"
$login = Invoke-RestMethod -Method POST -Uri "$base/api/auth/login" -ContentType "application/json" -Body '{"username":"admin","password":"admin123"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Method GET -Uri "$base/api/oncall/current?business_id=1" -Headers $headers | ConvertTo-Json
```

---

## Test 1 — On-Call Rotation + Override

Run the override path first — it is timezone-immune and gives the cleanest signal.

| # | Step | Expected | 2026-05-29 result |
|---|---|---|---|
| A | With a day-of-week rotation set (e.g. Freddy=Friday, Tyler=Saturday) and no override, call `GET /api/oncall/current` on a Friday | Returns **Freddy**, `"source": "rotation"` | ✅ Freddy, `source=rotation`, `after_hours=false` (4:30 PM local) |
| B | Set a manual override to the other tech (Tyler), 24h | `/current` returns **Tyler**, `"source": "override"`; dashboard card turns amber with "Manual override" badge | ✅ Tyler, override |
| C | Clear the override | `/current` returns **Freddy** again, `"source": "rotation"`; card returns to blue | ✅ Freddy, rotation |
| D | (Optional) Clear rotation + override, set a fallback phone/name | `/current` returns the fallback, `"source": "fallback"` | Not re-run this session (logic unchanged) |

**Timezone note:** rotation day-of-week and the after-hours window are evaluated in **business-local time** (`business.timezone`). Before the 2026-05-29 fix they used UTC, so an evening test in Florida (UTC already past midnight) returned the *next* day's tech.

---

## Test 2 — Emergency Dispatch

The emergency SMS path does **not** check after-hours — it dispatches any time.

| # | Step | Expected | 2026-05-29 result |
|---|---|---|---|
| 1 | From a customer phone, text the business Twilio number an emergency (e.g. "My AC died, 95° inside, elderly mother — emergency!") | AI replies with 1–2 qualifying questions | ✅ |
| 2 | Answer the questions | AI confirms, then **asks for / confirms the service address** | ✅ (found an associated address and asked to confirm) |
| 3 | Confirm the address | On-call tech receives 🚨 alert with customer name, **phone (E.164)**, **address**, issue summary | ✅ Freddy alerted with full address + issue |
| 4 | — | Customer receives "a technician has been alerted and will contact you shortly" + the conversation is marked `escalated` | ✅ |
| 5 | Check the Appointments page | New **emergency**-status appointment (red badge), assigned to the on-call tech, with the address + problem description in the detail row | ✅ (after frontend deploy + hard refresh) |
| 6 | Confirm no automated texts | **No** confirmation / OTW / reminder SMS fires for the emergency appointment | ✅ (excluded from scheduler jobs) |

**Verify the true appointment status** (the dashboard `<select>` can mislead if the frontend bundle is stale):

```powershell
Invoke-RestMethod -Method GET -Uri "$base/api/appointments?start_date=2026-05-29&end_date=2026-05-29&business_id=1" -Headers $headers | ConvertTo-Json -Depth 5
```

The Emergency Service row's `status` should read `"emergency"`, `source` `"emergency_sms"`.

---

## Notes & Known Behaviors

- **Name from a prior record:** the agent learns the customer name from the most recent (non-deleted) contact submission matching the phone. A soft-deleted *customer* won't be reused for the appointment (the emergency lookup skips soft-deleted customers and creates a fresh one), but a lingering *contact submission* with the same phone still supplies the name. In production, distinct customers won't share a number, so this is not a concern. For a clean test, use a phone with no prior history.
- **Emergency fee:** if enabled in on-call Settings, the AI discloses the fee and waits for the customer to reply YES before dispatching. (Not yet tested — planned follow-up.)
- **Tech alert phone format:** intentionally E.164 (`+1…`) — tap-to-dial works fine and it's machine-facing. All *customer-facing* phone numbers are formatted `(321) 386-7604`.

## Follow-ups

- Test the emergency-fee disclosure flow (enable fee, confirm AI asks for YES before dispatch).
- Align the SMS booking flow (`_tool_create_booking`) to also skip soft-deleted customers in its phone lookup (currently unfiltered, same pattern as the emergency lookup that was fixed).
