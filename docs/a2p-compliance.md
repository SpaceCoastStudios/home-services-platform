# SCS Platform -- A2P 10DLC Compliance

> Reference doc split from CLAUDE.md Section 25.
> Load this doc when onboarding a new client or doing any Twilio/A2P work.
> Do NOT change the approved consent flow without re-submitting to TCR.

## 25. A2P 10DLC Compliance

### Current Status (as of May 2026)
**Campaign is APPROVED** (CUSTOMER_CARE use case). Do not change the consent flow without re-submitting to TCR — the live form must match the approved description exactly.

### Rejection History (resolved)
Rejected 5 times for "issues verifying the CTA." Ultimately approved with an **optional** checkbox and explicit "not required" language — this satisfies carriers that SMS consent is not a condition of service.

### Approved Consent Implementation
The campaign was approved with the following consent flow — **do not change any of this without updating the TCR registration**:
- Checkbox is **optional** — form submits whether or not it is checked
- Exact consent label text on form: `(Optional) I agree to receive SMS messages from [Business Name], including appointment confirmations, reminders, and service-related notifications. Msg & data rates may apply. Reply STOP to opt out at any time. Reply HELP for help. SMS consent is not required to submit this form or receive service.`
- CTA URL on file: `https://spacecoaststudios.com/#contact`
- The embed form at `/embed/{slug}/contact` uses identical consent language — **both forms must stay in sync**
- Backend behavior: `sms_consent` boolean stored on every `ContactSubmission`. SMS is only sent when `sms_consent = true`

### What Would Require a TCR Re-submission
- Changing the consent language (even minor wording changes)
- Changing the CTA URL
- Adding a new use case (e.g. marketing/promotional SMS — currently CUSTOMER_CARE only)

### Approved Campaign Details (Twilio — verified May 2026)
- Use case: `CUSTOMER_CARE`
- Opt-in keywords: START, YES
- Opt-out keywords: STOP, STOPALL, UNSUBSCRIBE, CANCEL, END, QUIT, REVOKE, OPTOUT
- Help keywords: HELP, INFO
- Embedded links: Yes | Embedded phone numbers: Yes | Age-gated: No
- **Important:** Each CLIENT business needs their own Brand + Campaign registration. SCS's registration covers SCS itself only. Client registrations are submitted Day 1 of their onboarding.
- **Additional SCS-owned demo numbers (verified 2026-06-10):** numbers for SCS's own demo tenants can be added to the existing approved CUSTOMER_CARE campaign with NO new TCR submission: buy number -> add to Messaging Service sender pool -> register number to campaign -> set number-level inbound webhook -> set `twilio_phone_number` on the tenant. Pool demo number +13213984101 was added this way and worked the same day.

### Per-Client A2P Setup Checklist
1. Purchase local number in client's area code (Twilio Console)
2. Create Messaging Service, add number to sender pool
3. Register Brand (EIN, business info) → wait for approval
4. Create Campaign (Mixed or Notifications) linked to Messaging Service
5. **Register phone number to Campaign** (separate from sender pool — this step is easy to skip)
6. Configure inbound webhook on the **phone number itself** (not just the Messaging Service):
   `https://api.spacecoaststudios.com/webhook/sms/inbound` (POST)
7. Set `twilio_phone_number` on Business record (E.164 format)

---
