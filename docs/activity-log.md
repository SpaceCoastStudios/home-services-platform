# SCS Platform — Activity Log

> This file is part of the Space Coast Studios project documentation.
> Append-only session history. Add new entries at the TOP under "## Session Log".
> **After every session:** add a dated entry here summarizing what was built, changed, or decided.
> Do NOT add session history to CLAUDE.md — it goes here.

## 30. Activity Log

### Features Built by Session

**2026-07-01 (Appointments UI: column sorting + Active/History split — screenshot-readiness pass, part 1):**
- **Context:** Prepping for a round of publicly-visible screenshots (marketing/sales use). Reviewed the Appointments screen and flagged three things before shooting screenshots: limited sorting, no separation of final-status appointments from active ones, and overall visual polish. This session covers the first two; visual/style polish is a separate follow-up session.
- **Confirmed backend has no per-column sort or multi-status filter:** appointment endpoints live in `backend/app/routers/availability.py` (not a dedicated `appointments.py`) — `GET /api/appointments` only supports a single exact-match `status` filter and a `sort` param of `upcoming | newest | oldest` (date-based only), `limit=200` default. Both features below were implemented client-side against the already-fetched list rather than adding new backend query params — simplest fix, no API changes, safe at current per-tenant appointment volumes.
- **Per-column sorting** (`frontend/dashboard/src/pages/AppointmentsPage.jsx`): added clickable column headers (Date/Time, Customer, Service, Technician, Status) via a new `SortHeader` component with asc/desc chevron indicators. New `colSort` state holds `{ key, dir }` and takes precedence over the existing base sort (Upcoming/Newest/Oldest) when set; clicking a base-sort button clears `colSort` so the two controls don't fight each other. Sort comparators live in a `COLUMN_ACCESSORS` map (case-insensitive string compare for text columns, timestamp compare for date).
- **Active / History split:** new `apptView` state ('active' | 'history') renders as a toggle above the existing status-filter row. Active = emergency/pending/confirmed/in_progress/en_route; History = completed/cancelled/no_show (`ACTIVE_STATUSES` / `HISTORY_STATUSES` constants). The status-filter button row now scopes to whichever view is selected (`FILTER_OPTIONS_BY_VIEW`) instead of showing all 8 statuses at once. Switching view resets the status filter to "All" within that view. Filtering happens client-side against the fetched list (`viewFilteredAppointments`), same 200-row fetch limit caveat as above.
- **Verification:** parsed the edited file with `@babel/parser` (already vendored in `node_modules` — sandbox couldn't run a native Vite/esbuild build due to Windows-binary/Linux-sandbox mismatch, a pre-existing environment limitation, not a code issue). Confirmed zero NUL bytes and correct file ending per the truncation rule below. Manual review of the diff confirmed table headers, view toggle, and filter scoping wire up correctly.
- **Files changed:** `frontend/dashboard/src/pages/AppointmentsPage.jsx`.
- **Next up:** visual/style polish pass across the dashboard (colors, card treatment, typography) before final screenshots — Ryan wants to look at HTML mockups of a couple of directions first.

**2026-07-01 (Q3 dependency audit + Stripe v15 upgrade + PyJWT fix + SendGrid/Twilio migration):**
- **Quarterly dependency audit (automated task trigger):** Kicked off the Q3 2026 audit. Key findings: Stripe needed upgrade to v15 (breaking change); PyJWT 2.13.0 introduced `sub`-as-string enforcement; SendGrid had silently migrated under Twilio branding, leaving the production API key invalid. All three resolved this session.
- **Stripe upgraded to v15.3.0** (`requirements.txt`, `billing.py`): Stripe v15 drops `StripeObject`'s `dict` inheritance — `.get()` on raw response objects now raises `AttributeError`. Fixed in three places in `backend/app/routers/billing.py`: (1) webhook handler — `event["data"]["object"].to_dict()` before accessing keys; (2) `_provision_tenant` — `sub.to_dict()` after `Subscription.retrieve()`; (3) `get_checkout_session` — `session.to_dict()` after `Session.retrieve()`. Verified end-to-end: Stripe Checkout → webhook → tenant provisioned (business #5 created in DB).
- **requirements.txt corruption repaired:** A previous `pip freeze > requirements.txt` in PowerShell had written the file as UTF-16 and captured wrong system-Python packages (no sqlalchemy, no psycopg2, etc.), causing DO deploys to fail with `ModuleNotFoundError`. Fixed by writing the file from scratch via a bash Python script using `io.open(..., "w", encoding="utf-8")` with the correct, manually verified package list. Confirmed: zero NUL bytes, sqlalchemy present, stripe==15.3.0.
- **Full billing smoke test passed:** $2 test checkout completed on live site; DO logs confirmed tenant provisioned, welcome email delivered. Test subscription (sub_1ToOYz2MJMR8rAcZZMKlM3th) needs to be cancelled and the $2 charge refunded in Stripe Dashboard.
- **PyJWT 2.13.0 breaking change fixed** (`utils/auth.py`, `routers/auth.py`): PyJWT 2.10+ enforces RFC 7519 — the `sub` claim must be a string (StringOrURI), not an integer. `build_token_data` was encoding `user.id` (int) directly, causing `InvalidClaimError` on decode. Symptom: login returned 200 but every subsequent API call returned 401, bouncing the dashboard back to the login screen. Fix: `"sub": str(user.id)` on encode; `AdminUser.id == int(payload.get("sub"))` on DB lookups in both `get_current_user` and the `/refresh` endpoint. Dashboard login confirmed working post-deploy.
- **SendGrid/Twilio migration discovered and resolved** (`SENDGRID_API_KEY` env var): SendGrid is now branded under Twilio. The migration created a fresh account state — no API keys existed, causing all outbound emails to fail with 401 Unauthorized. Resolution: (1) domain authentication was already verified (em6518.spacecoaststudios.com Verified) — the DKIM/SPF CNAME records in GoDaddy carried over automatically, so `noreply@spacecoaststudios.com` needed no changes; (2) created new "SCS Production" API key with Full Access in the Twilio/SendGrid dashboard; (3) updated `SENDGRID_API_KEY` in DigitalOcean App Platform env vars; (4) triggered a password reset email to confirm — status 202 and email received. Note: `noreply@spacecoaststudios.com` does NOT need a real GoDaddy mailbox — domain authentication covers sending rights.
- **SendGrid plan note:** Account is currently on a free trial (100 emails/day, expires ~August 30, 2026). Must upgrade to Essentials plan before first paying client goes live.
- **Roadmap addition:** "Delete business (platform admin)" — `/businesses` page only supports deactivating tenants; add a hard-delete with confirmation modal for cleaning up test/junk tenants. Added to `docs/roadmap.md`.
- **Pending (carry to next session):** (1) Anthropic SMS agent smoke test — text Brevard Pool Pros number, confirm booking agent responds (last remaining audit item); (2) cancel Stripe test subscription + refund $2 charge; (3) commit roadmap + activity log (`git add docs/roadmap.md docs/activity-log.md`, commit `docs: Q3 2026 audit + SendGrid fix + delete-business roadmap item`).
- **Files changed:** `backend/requirements.txt`, `backend/app/routers/billing.py`, `backend/app/utils/auth.py`, `backend/app/routers/auth.py`, `docs/roadmap.md`, `docs/activity-log.md`.

**2026-06-10 (single-tier pricing restructure + vertical GTM decision + index.html corruption repair):**
- **Strategy session:** Full platform/business analysis delivered. Decisions made: (1) adopt single-tier pricing -- one "Launchpad" plan at $999 setup + $299/mo, founding offer $497 + $149/mo x3 months then $299; (2) verticalize GTM marketing one trade at a time, Pool Service first then HVAC (platform unchanged -- marketing/demo assets become trade-specific); (3) voicemail AI kept on roadmap as future standalone/wedge product; (4) apartment/property-management pivot evaluated and rejected.
- **CRITICAL FIX -- index.html truncation:** Discovered `marketing-site/index.html` at HEAD was truncated mid-JavaScript (last 41 bytes missing: closing braces + `</script></body></html>`). Introduced in commit `02ece40` and present in all commits since (~June 1) -- the page's entire bottom script block (Stripe checkout buttons + demo form handler) was likely failing to parse on the LIVE site. Repaired by grafting the intact tail from `e0ad5e6`. **CLAUDE.md itself had the same problem**: truncated mid-bullet since commit `3b3b0bb` (2026-05-30), ~2.8KB of the 2026-05-28 activity log missing; recovered from `6f3e42b`. (Note: the recovered final line documents the old pre-2026-05-29 git workflow; the header rule -- Ryan runs all git commands -- is current.) Root cause: file-tool writes on the Windows mount do not truncate -- a shorter rewrite leaves the file at its old length padded with NUL bytes (same family as the 2026-05-29 f-string corruption). **New rule: edit existing repo files via bash Python scripts (read/replace/write), not the Edit/Write tools. After any sizeable edit, verify: no NUL bytes, file ends with expected content.**
- **Backend single-plan changes:** `config.py` -- STRIPE_PRICE_STARTER_*/PRO_* replaced with STRIPE_PRICE_LAUNCHPAD_SETUP/MONTHLY (+ founding, defaults empty until script run). `billing.py` -- PLAN_PRICES now launchpad+test; LEGACY_PLAN_ALIASES maps starter/professional to launchpad; checkout 503s if price IDs unconfigured; provision default plan "launchpad".
- **New script:** `backend/scripts/create_launchpad_prices.py` -- creates the Launchpad product + 4 prices in Stripe, prints IDs for config.py + DO env vars. Ryan must run this BEFORE pushing.
- **Marketing site:** pricing section rewritten to one centered card ($999 + $299/mo, full feature list, `data-checkout-plan="launchpad"`); promo banner updated to $497/$149 founding terms; "which plan fits" line replaced; Starter/Professional widget-choice copy in features section reworded; truncated JS tail restored.
- **Dashboard:** `BillingPage.jsx` TIER_LABELS gains `launchpad`, legacy labels marked "(legacy)". `OnboardingPage.jsx` -- single Launchpad plan option ($999 + $299/mo), mini/full plan values removed, service/tech caps removed, monthly check-in shown for all.
- **Schedule A draft:** `Test Project/SCS-Schedule-A-Single-Tier-DRAFT.docx` -- single-plan Schedule A + summary-of-changes section for Anjali, sent with the signed engagement letter. Founding addendum terms to update to $497/$149/$299.
- **Docs:** README + CLAUDE.md Sections 1-header, 3, 4, 8, 12, 24, 26 updated for single-tier pricing.
- **DEPLOY SEQUENCING (critical):** (1) Ryan runs `create_launchpad_prices.py`; (2) paste IDs into `config.py` defaults + README/CLAUDE.md tables; (3) set `STRIPE_PRICE_LAUNCHPAD_SETUP`/`STRIPE_PRICE_LAUNCHPAD_MONTHLY` env vars on DO api component; (4) THEN push everything in one commit. Push is urgent once ready -- the live site checkout JS is currently broken (see truncation fix above).
- **Pool vertical built (same day, session 2):**
  - `marketing-site/pool.html` (new, unlisted/noindex): pool-edition demo page; live contact + booking widgets pointed at slug `brevard-pool-pros`; new "Recurring Weekly Service" section with schedule mockup; communications + tech schedule sections pool-flavored. **Wording audit done:** all feature claims use "recurring scheduling / daily schedule / stop list" language -- "route-based scheduling" is NOT built (deferred roadmap item) and must not be implied. Colloquial owner-day uses of "route" are OK.
  - `backend/scripts/seed_pool_demo.py` (new): provisions the Brevard Pool Pros demo tenant via the production API (business + Marina persona + hours + 5 pool services + 2 techs + 4 customers with fictional 555 numbers + 3 weekly recurring schedules; creates NO appointments, fires NO notifications; re-run safe). Ryan runs it locally -- the Cowork sandbox proxy blocks API writes. This is the seed of the Track C parameterized onboarding seeder.
  - Test Project root docs updated (outside repo, no commit needed): `SCS_SalesSheet_Pool.docx`/`.pdf` (new, cloned from Landscaping design, pool copy, no em dashes), `SCS Cold Email Sequence.docx` (single founding offer $497/$149/$299 everywhere, Founding_Offer tier-choice removed, pool variant links to /pool.html, honesty notes updated to single plan), `SCS_Onboarding_Checklist.docx` (Professional-only stars and plan field removed).
- **Still to do (vertical GTM):** run `seed_pool_demo.py` (Ryan); pool screenshots once tenant is live; demo-tenant Google Review URL still placeholder; then HVAC vertical (re-point a copy of pool.html structure at an HVAC tenant); Platform Capability Checklist + Roadmap docx have no pricing refs (verified) but should gain the single-tier note on next regeneration.
- **Files changed:** `backend/app/config.py`, `backend/app/routers/billing.py`, `backend/scripts/create_launchpad_prices.py` (new), `marketing-site/index.html`, `frontend/dashboard/src/pages/BillingPage.jsx`, `frontend/dashboard/src/pages/OnboardingPage.jsx`, `README.md`, `CLAUDE.md`.
- **Pool tenant + number LIVE (session 3):** Ryan ran `seed_pool_demo.py` (tenant provisioned, widgets verified in pool blue); bought Twilio number **+13213984101**, added to Messaging Service sender pool, registered to the existing CUSTOMER_CARE campaign (no new TCR submission needed -- confirmed), number-level inbound webhook set, Messaging Service defers to sender's webhook, fallback webhook left empty (correct -- fallback is for a separate emergency endpoint). Number set on the tenant; **Marina SMS agent verified live same day.**
- **Tech OTW YES-reply scoping fix shipped** (`sms_webhook.py`): handler now resolves the business owning the inbound number and scopes the tech lookup to that tenant; cross-tenant fallback only when no owner. Fixes duplicate-tech-phone flakiness across demo tenants.
- **Demo logistics decisions:** (1) tenant #1 stays as SCS lead intake + generic demo -- NOT converted to HVAC (the marketing-site #contact form and the A2P reviewer page point at it); (2) HVAC vertical = new dedicated tenant + hvac.html, same recipe as pool; (3) each vertical demo tenant gets its own cheap number on the same campaign; (4) demo.html retires from active outreach use once hvac.html exists.
- **DEPLOYED + VERIFIED same day:** pushed as `4633e80`; Ryan ran the price script (product `prod_Ug8lLmR2lobv8S`), set DO env vars, archived old Stripe products. Checkout verified end-to-end on the live site: $1,298 first payment then $299/mo. Live-site checkout JS confirmed fixed. Price IDs backfilled into config.py defaults + README/CLAUDE.md tables in a follow-up commit.

**2026-05-31 (session 2 — recurring UI + demo page polish):**
- **Recurring appointments dashboard UI** — enhanced `AppointmentsPage.jsx` Recurring Series tab: clickable expandable rows revealing address, notes, start/end dates; Edit modal for frequency, day/time, tech, end date, address, notes; appointment history panel showing upcoming (next 5) and past (last 5) per schedule loaded alongside schedules; "Generate appointments now" button triggering `POST /api/recurring/{id}/generate` with a toast. `generateRecurringSchedule` added to `api.js` imports. No backend changes needed.
- **AI model selection guide** — added to CLAUDE.md Section 22 with Haiku/Sonnet/Opus decision rules; Platform Capability Checklist.docx and SCS Platform Roadmap.docx updated with per-item model tags on all AI features; roadmap gains a callout box with the full guide.
- **Action plan A6.5** — end-to-end demo readiness test (10-step checklist) added to `docs/action-plan-gtm-and-booking-widget.md` as a gate before sending the demo link to any prospect, triggered by CSA attorney sign-off.
- **Demo page major polish** (`marketing-site/demo.html`):
  - Contact widget iframe auto-resize: `ResizeObserver` + `scs_contact_resize` postMessage added to `backend/app/routers/embed.py`; demo page listener added. Contact iframe starting height raised to 900px.
  - Badge changed from orange to green; header reworded to remove "not screenshots" (since screenshots are used); copy updated to "your website / your dashboard."
  - All 4 notification overview cards replaced with real screenshots: `Customer Appointment Confirmation Text.png`, `Reminder Text.png`, `Customer on the way text.png`, `Customer Review Request.png`. Fixed 2-column 2x2 grid.
  - "See the Real Flows" 2x2 panels: Emergency AI Dispatch Flow (`Emergency Text Thread.jpg`) + Emergency Tech Alert (`Emergency Text Tech Message.png`) on top row; Morning Kickoff (`Tech Daily Kickoff thread 1.png`) + Full OTW Day Cycle (`Tech Daily Kickoff thread 2.png`) on bottom row. All full natural height, rounded corners.
  - Section 4 redesigned: morning kickoff SMS screenshot (`Tech Kickoff Thread with schedule link.png`) + schedule page mockup side by side.
  - Unified card titles across all cards: `0.9rem`, bold, dark navy, centered, no emojis, no uppercase.
  - Screenshot cards: `object-fit:contain; background:#111827; height:220px` for even card heights without cropping.
  - Em dashes removed throughout. Saved as standing memory note.
- **Files committed**: `AppointmentsPage.jsx`, `embed.py`, `demo.html`, all screenshot images.

**2026-05-31 (outreach assets finalized — non-code):**
- **Cold-email sequence revised** (`SCS Cold Email Sequence.docx`, Test Project root): demo CTA now "try the booking and contact widgets your customers would actually use"; removed the "90-second demo" line; every email's opt-out reworded to natural language with a CAN-SPAM **mailing-address footer** (`{{Mailing_Address}}` placeholder); Email #2 founding offer is now a **`{{Founding_Offer}}` merge field** (Starter vs Pro, chosen per prospect); added a full **15-minute demo-call script** (prospect drives the demo page themselves, then Ryan screen-shares the dashboard: Contacts queue → SMS Conversations → the created Appointment — there is no "notification log" screen).
- **Action plan A6** (`docs/action-plan-gtm-and-booking-widget.md`) rewritten to match the new screen-share demo flow + the demo-page-polish gate.
- **Roadmap** (`SCS Platform Roadmap.docx` + this file): demo-page polish reframed as a **pre-demo prerequisite**; added **platform-admin cross-tenant activity log** to Later/Growth.
- **Fixed a broken working-tree file:** `frontend/dashboard/src/pages/AppointmentsPage.jsx` had a truncated/unclosed edit (missing closing `</div>)}`, would have failed the build); reverted via `git checkout --` after clearing a stale `.git/index.lock`. No intended changes lost.
- Outreach is otherwise ready to send pending Ryan filling `{{Your_Phone}}` + `{{Mailing_Address}}` and the demo-page polish pass.


**2026-06-01 (competitive positioning strategy + roadmap additions):**
- **Competitive positioning reframe** -- Launchpad repositioned as the customer-facing communication layer, complementary to (not competing with) Jobber/Housecall Pro/other FSM tools. Those platforms are back-office (invoicing, job costing, quoting); Launchpad is the customer front door (AI contact response, SMS booking, OTW flow, review requests, emergency dispatch). Positioning angle: "Works alongside whatever tool you already use." Invoicing explicitly de-prioritized.
- **Pricing strategy** -- One-tier simplification under consideration (Starter/Pro split adds friction for a complementary tool). Multiple locations = add-on discount, not a tier feature. No pricing changes before first prospect conversations (cold emails going out).
- **Voicemail + AI response added to roadmap (HIGH INTEREST)** -- Client keeps existing number, forwards to Twilio. Twilio records voicemail; Whisper transcribes; Claude generates SMS reply; dashboard logs full thread. Whisper preferred (~$0.04/call vs ~$0.23 with Twilio transcription). "Coming Soon" candidate for marketing site once fleshed out. Do NOT promise to prospects until built.
- **Promotional/re-engagement SMS added to roadmap** -- Seasonal SMS to past customer lists (HVAC tune-up, pool holiday specials). Requires A2P MIXED campaign (new campaign, brand stays) + marketing opt-in mechanism. A2P update: edit existing campaign to change use case type generally requires a new campaign submission; ~2-4 week approval. Hold off on demo campaign update until feature is near-built.
- **Cold email reframe notes** -- Emails are already well-targeted on customer communication pain. Two suggested updates: (1) "booking & instant-response systems" in the core opener could be tightened to "automated customer communication system"; (2) demo call script (13-15 min mark) should add: "If you're already using Jobber or Housecall Pro for invoicing, this runs alongside it -- it's the customer communication layer those tools don't have."
- **A2P re-engagement guidance** -- Changing use case from CUSTOMER_CARE to MIXED requires a new campaign submission (~2-4 weeks), not an edit. Brand registration stays. Hold off on updating demo Twilio campaign until re-engagement feature is near-ready.

**2026-06-01 (Launchpad rebrand + CSA v2/v3 + attorney engagement):**
- **Attorney selected:** Anjali Sareen, Uncommon Counsel (Altamonte Springs, FL). Licensed in FL/NY/CA, AIGP-certified, specializes in SaaS contracts and AI law. Flat fee $1,050 for initial review + redline. Ryan sending v3 CSA today.
- **CSA v2** -- fixed three issues found in audit: (1) Section 12.5 wrong AI provider "OpenAI" changed to "Anthropic, PBC"; (2) Schedule A pricing updated to match Stripe ($1,997/$249 Starter, $2,997/$399 Pro); (3) name corrected from "Ryan Usser" to "Ryan Ussery" throughout.
- **CSA v3** -- added "Launchpad" as the platform brand name in Section 1.1 ("branded as 'Launchpad'") and Schedule A title updated to "SCHEDULE A: LAUNCHPAD SERVICES AND PRICING."
- **Three questions sent to Anjali:** (1) 6-month initial term -- marketing copy "no long contracts" removed but flagging for her awareness; (2) "Launchpad" platform name -- is v3 language sufficient or should it be strengthened?; (3) SMS consent text says "Space Coast Studios" per A2P approval -- if product is "Launchpad by SCS," does consent need updating? Would that require TCR re-submission?
- **Platform rebranded as Launchpad** (product name; Space Coast Studios LLC remains company/legal entity; no DBA filed):
  - `marketing-site/index.html` -- title, meta, hero copy, nav, footer updated. "Launchpad by Space Coast Studios" in footer; "Launchpad" in headlines.
  - `marketing-site/booking-demo.html`, `demo.html`, `privacy.html`, `terms.html` -- all updated.
  - `frontend/dashboard/src/components/Layout.jsx` -- platform admin header now shows "Launchpad."
  - `frontend/dashboard/src/pages/` -- WelcomePage, SetupPage, ForgotPasswordPage, SetPasswordPage: "Welcome to Space Coast Studios" → "Welcome to Launchpad."
  - `backend/app/routers/auth.py` -- password reset email subject/body updated.
  - `backend/app/routers/billing.py` -- welcome email subject/body updated.
  - `CLAUDE.md` Section 1 -- added platform branding note; corrected Ryan's last name.
  - `README.md` -- title updated to "Launchpad by Space Coast Studios."
  - SMS consent text intentionally left as "Space Coast Studios" -- A2P approved language, cannot change without TCR re-submission.
- **Marketing site em dashes removed** -- all 31 em dashes across `index.html` replaced with contextually appropriate punctuation.
- **Marketing copy updated** -- "no long contracts or complicated onboarding" changed to "No complicated onboarding." (removed the contract duration claim to match the 6-month initial term in the CSA).
- **Demo tenant renamed** -- "Space Coast Studios Demo" updated to "Launchpad Demo" via dashboard Settings. Widget headers now show the correct brand.
- **Action plan updated** -- `docs/action-plan-gtm-and-booking-widget.md` reflects current status, Track B marked complete, A6.5 updated with screenshot pre-test checklist.
- **Next steps:** populate Launchpad Demo with appointments for screenshot refresh; await Anjali's redline; then run A6.5 end-to-end test; then first prospect demo call.
- **Files committed:** `CLAUDE.md`, `README.md`, `marketing-site/index.html`, `marketing-site/booking-demo.html`, `marketing-site/demo.html`, `marketing-site/privacy.html`, `marketing-site/terms.html`, `frontend/dashboard/src/components/Layout.jsx`, `frontend/dashboard/src/pages/WelcomePage.jsx`, `frontend/dashboard/src/pages/SetupPage.jsx`, `frontend/dashboard/src/pages/ForgotPasswordPage.jsx`, `frontend/dashboard/src/pages/SetPasswordPage.jsx`, `backend/app/routers/auth.py`, `backend/app/routers/billing.py`. CSA v2 and v3 saved to Test Project/ (outside repo).

**2026-05-30 (automated CLAUDE.md context-sync run — no code changes):**
- Scheduled daily maintenance run. Reviewed `git log` (HEAD `3b3b0bb`, 20:03 today): today's GTM groundwork (109-prospect tracker, competitor battlecard, 5-touch cold-email sequence) and booking widget Phase 1 (shipped + tested) are already captured in this log and reflected in Sections 21–26. No new commits since the last update — nothing to reclassify in the capability/roadmap/A2P/CSA sections.
- **Flag for Ryan:** an uncommitted, apparently-truncated edit to `frontend/dashboard/src/pages/AppointmentsPage.jsx` is sitting in the working tree (closing `</div>)}` removed, no trailing newline — looks like a stray/broken edit that would fail the build). Left untouched (this context task makes no code changes). Recommend reverting: `git checkout -- frontend/dashboard/src/pages/AppointmentsPage.jsx`.
- **Commit note:** per the git-workflow rule atop this file, the sandbox cannot run git (a stale `.git/index.lock` is present and unremovable here), so this CLAUDE.md update must be committed by Ryan from his terminal.

**2026-05-30 (GTM / Track A groundwork — sales assets, non-code):**
- **Prospect tracker expanded + scored** — `SCS Prospect Tracker.xlsx` (and a working copy `SCS Prospect Tracker Updated.xlsx`) in the Test Project root now holds **109 prospects** across 6 trade tabs: HVAC/Landscaping/Roofing (original 55 on the `Prospects` tab) + **Plumbing (13), Septic (14), Pool Service (19), House Cleaning (8)**; Tree Service + Pressure Washing tabs exist but intentionally empty (held until the quote/estimate workflow ships). Every prospect carries owner/email/website/GBP rating+reviews/Response-Gap notes, plus a computed **Priority** (57 High / 27 Medium / 25 Low, color-coded) and **Next Action**. Dashboard tab aggregates counts across all trade sheets.
- **Scoring logic:** High = clear response gap + fit ≥4 (or a low-rating-but-busy "response-gap signal"); DIY-tool shops (Housecall Pro/Jobber/etc.) auto-set Low "skip/example"; roofing dropped to Low (estimate-first). Standouts: **Pool Service 15/19 High** (strongest founding pool), ARK Plumbing & Septic flagged as a "broken ServiceTitan" swoop-in.
- **Competitor battlecard** — `SCS Competitor Comparison.xlsx` (Test Project root): side-by-side matrix of ServiceTitan, Housecall Pro, Jobber, Workiz, Service Fusion + SCS across ~19 data points, with **web-verified pricing (May 2026)** and a Notes/Positioning tab. Three positioning wedges: **done-for-you vs DIY, AI-first (included not add-on), and local.** Includes objection scripts.
- **Cold email sequence** — `SCS Cold Email Sequence.docx` (Test Project root): core 3-email cadence (opener → outcome+founding offer → breakup) + **5 trade-specific Email #1 variants** (HVAC, Pool, Plumbing, Septic, House Cleaning) + "already have a system" rebuttal + phone/voicemail script. CAN-SPAM compliant; merge-field driven.
- **New trades fact-checked** as plentiful in Brevard (web search): tree, pool, pressure washing, septic, house cleaning — all confirmed. Pool service + house cleaning flagged as best recurring-revenue fits (drove elevating the Recurring UI to top build priority).
- All four files live in the Test Project root (outside the repo) — saved on Ryan's computer, not part of git pushes.


**2026-06-02 (escalation alerts + on-call bug fixes):**
- **Emergency dispatch failure root cause:** Investigated via code review — dispatch failed because the weekly rolling rotation had no entry for today (on-call config was in day_of_week mode with no Tuesday entry, and no fallback phone configured). The dispatch logic does NOT check appointment status (en_route/scheduled) — only the rotation config. User hypothesis was incorrect.
- **Escalated SMS conversation:** Confirmed the conversation WAS recorded. It appeared in the Escalated tab (not default Active tab) because `convo.status = "escalated"` is always set when `emergency_dispatch` tool fires, regardless of dispatch success.
- **On-call banner bug fixed** (`OnCallPage.jsx`): The "No on-call tech assigned" banner was always showing for weekly rolling rotations. Root cause: the `activeTech` local computation returned `null` for the `weekly_rolling` branch. Fixed by calling `getCurrentOnCall(businessId)` alongside `getOnCallConfig` at load time and using the server-computed result. Banner now handles rotation/override/fallback states correctly.
- **Week position UI improved** (`OnCallPage.jsx`): Replaced the 0-indexed number input ("0 = Week 1") with a "Week in Rotation" dropdown showing "Week 1" through "Week 8". Display label changed from "Week position N" to "Week N". Weekly rolling cycles automatically via modulo (4 techs → Week 5 = Week 1).
- **Escalation alerts built** (`models/oncall.py`, `main.py`, `routers/oncall.py`, `services/notifications.py`, `services/sms_agent.py`, `OnCallPage.jsx`): Three new fields on `oncall_configs` — `escalation_sms_phone`, `escalation_email`, `escalation_notify_oncall`. `send_escalation_alert()` added to `notifications.py` — fires all configured channels simultaneously, falls back to `fallback_phone` → `business.phone`. Wired into `sms_agent.py` for both `escalate_to_human` and `emergency_dispatch`. On-Call Settings page gains an "Escalation Alerts" section with SMS phone input, email input, and on-call tech toggle. Amber warning shows if no escalation contacts configured.
- **Files changed:** `frontend/dashboard/src/pages/OnCallPage.jsx`, `backend/app/models/oncall.py`, `backend/app/main.py`, `backend/app/routers/oncall.py`, `backend/app/services/notifications.py`, `backend/app/services/sms_agent.py`.

**2026-06-02 (daily health check + demo tenant name fix):**
- **Daily health check scheduled task** (`scs-daily-health-check`) created — runs 7am daily; checks site availability + response times for all 3 URLs, API functionality (auth, booking widget config, contact widget, scheduler), config.py model string sanity, and sends ntfy.sh push alert for Critical/High findings. Silent on clean runs. ntfy.sh channel: `scs-health-q8m3x5k2` (install ntfy app, subscribe to that topic). Task includes setup instructions on first run.
- **Demo tenant business name fixed** — `/embed/default/booking-config` was returning `"business_name":"Space Coast Studios Demo"` instead of `"Launchpad Demo"`. Root cause: the previous rename via the dashboard Businesses edit modal had a transient save failure (network/navigation issue); the code itself is correct. Fixed via direct API call (`PUT /api/businesses/1 {"name":"Launchpad Demo"}`). Verified: endpoint now returns correct name. No code changes needed.

**2026-05-30 (Cowork automated maintenance tasks):**
- Created 4 Cowork scheduled tasks covering all periodic maintenance items from Section 23:
  - `scs-quarterly-llm-model-check` — runs Jan/Apr/Jul/Oct 1 at 9am; fetches Anthropic docs, validates `LLM_MODEL` + `SMS_AGENT_MODEL`, auto-updates `config.py` if deprecated, provides DO env var + git instructions
  - `scs-quarterly-dependency-audit` — same quarterly schedule; checks key Python + npm packages for outdated versions and CVEs, delivers prioritized update list with commands
  - `scs-monthly-infrastructure-check` — runs 1st of every month at 9am; reminds Ryan to check DO DB backups, Twilio balance (>$20), SendGrid bounce/spam rates
  - `scs-annual-maintenance-reminder` — runs Jan 1 at 9am; covers JWT/SECRET key rotation, domain renewal, SSL cert, Stripe price ID review, CSA template review
- Task files stored at `C:\Users\Ryan\Documents\Claude\Scheduled\<task-id>\SKILL.md`
- Section 23 updated with full task table and first-run instructions

**2026-05-30 (self-scheduling booking widget — Phase 1, shipped + tested):**
- New public, slug-scoped endpoints in `routers/embed.py`: `GET /embed/{slug}/booking-config`, `GET /embed/{slug}/availability`, `POST /embed/{slug}/book`, and `GET /embed/{slug}/booking` (embeddable widget UI). Reuse `services/scheduling.get_available_slots` + `auto_assign_technician` + `send_confirmation`. Honeypot field + slot re-validation guard against spam/double-booking; the internal "Emergency Service" type is excluded from public booking.
- Widget UX: service → day → time → details → confirm; brand-colored; iframe-resize `postMessage`; "Book another" reset on the success screen.
- Embedded live into `marketing-site/demo.html` section 2 (pill flipped to Live) with an auto-resize listener.
- Tested end-to-end on the demo tenant: bookings create confirmed appointments with assigned tech + problem description, fire confirmation SMS/email, render correct local time, and consume capacity correctly (a slot drops off once all qualified techs are booked). New-customer creation + soft-deleted-skip verified.
- Files: `backend/app/routers/embed.py`, `marketing-site/demo.html`.

**2026-05-29 (on-call testing + emergency dispatch hardening):**
- **On-call timezone fix** — rotation (day-of-week + weekly-rolling) and the after-hours window now evaluate in business-local time (`business.timezone`) instead of UTC, in both `routers/oncall.py` and `services/oncall_notifier.py` via a new `_business_local_now()` helper. Previously returned the wrong tech in the evening once UTC passed midnight. Verified: Friday rotation correctly returns Friday's tech at 4:30 PM local.
- **On-call config save bug** — `OnCallPage.jsx` sent `rolling_start_date: ""` (empty string) in day-of-week mode → 422 on the PUT → "Failed to save settings." Now sends `null`.
- **Emergency dispatch phone normalization** — `dispatch_emergency` normalizes both from- and to-numbers to E.164, so a tech stored as bare 10-digit still gets the alert.
- **Emergency → appointment** — `emergency_dispatch` now creates an `emergency`-status appointment (dedicated "Emergency Service" type, on-call tech, scheduled now, no automated notifications). Excluded from reminder/OTW/kickoff scheduler jobs. Soft-deleted customers skipped in the phone lookup.
- **In-chat address capture** — the agent's `emergency_dispatch` tool gained a `service_address` field; the prompt instructs the AI to confirm/collect the service address before dispatching. Address flows into the tech alert SMS (new `Address:` line in the default emergency template) and into the appointment.
- **Dashboard** — `emergency` status renders a bold red badge, is selectable/filterable, and "Mark Complete" works on it (`AppointmentsPage.jsx`).
- **Customer-facing phone formatting** — new `app/utils/phone.py` `format_phone_display()` → `(321) 386-7604`, applied to SMS agent replies, contact responder (prompt + email + context block), and notification templates (`{{business_phone}}` + email footer). Tech emergency alert intentionally kept in E.164.
- **Testing** — on-call rotation/override + emergency dispatch fully tested end-to-end (see `docs/on-call-emergency-testing.md`).
- Files: `routers/oncall.py`, `services/oncall_notifier.py`, `services/scheduler.py`, `services/sms_agent.py`, `services/contact_responder.py`, `services/template_renderer.py`, `models/notification_template.py`, `utils/phone.py` (new), `frontend/dashboard/src/pages/OnCallPage.jsx`, `frontend/dashboard/src/pages/AppointmentsPage.jsx`.

**2026-05-26 (major dev day — 15 commits):**
- Customer form: split address into street/city/state/zip; fixed `[object Object]` rendering bug
- Timezone display fix; booking confirmation SMS now fires on appointment creation
- Phone numbers auto-normalized to E.164 before Twilio send
- Customer inline edit added to dashboard
- Email calendar buttons + SMS business name fix in template renderer
- Reminder scheduler overhauled: noon local time for next open business day, 30-min interval, idempotent
- Admin router with manual trigger endpoints (reminders, OTW prompts, OTW kickoffs)
- Developer Tools panel in Settings page
- Stripe billing fully configured: products + prices created, IDs in config and app.yaml
- README added with infrastructure overview, pricing, and Stripe config

**2026-05-27 (audit and polish):**
- Forgot-password flow (backend + frontend): `POST /api/auth/forgot-password`, `ForgotPasswordPage.jsx`
- `set-password` now returns JWT tokens for auto-login
- Platform admin impersonation: backend endpoint + `localStorage` stash/restore pattern + amber banner
- Noisy DB migration errors fixed (`ALTER TABLE ADD COLUMN IF NOT EXISTS`)
- First-login setup wizard (`/setup`, 3-step, per-step auto-save, `has_completed_setup` gate)
- `GET /api/businesses/me` — business admin self-service endpoint
- `PUT /api/businesses/{id}` opened to business admins (with protected field list)
- Full platform audit: marketing site cleanup (removed placeholder phone, fixed API_URL ordering, clarified founding offer renewal prices, fixed error email), README synced with all new features
- Documentation consolidated: all .md files merged into single CLAUDE.md, `HomeServices_Architecture_Plan.md` archived to `docs/archive/`, `SCS_PROJECT_CONTEXT.md` deleted
- Stripe prices verified: confirmed all four standard price IDs in README/billing.py match actual amounts in Stripe dashboard ($1,997 setup, $249/mo, $2,997 setup, $399/mo)
- Scheduled task `scs-context-update` updated: now targets CLAUDE.md (was SCS_PROJECT_CONTEXT.md), section references corrected, added limitation warning explaining it only captures git commits — non-code events (A2P status, attorney responses, client signups) require manual input
- End-of-session habit established: say "Update CLAUDE.md with everything that happened today" to capture the full session, or "Update CLAUDE.md — [specific event]" for non-code updates (e.g. A2P approved, client signed)

**2026-05-28 (problem description + tech schedule feature — Pass 1):**
- `Appointment` model: added `problem_description` (Text, nullable) and `media_urls` (JSONB, nullable). Migration in `run_migrations()`.
- `Technician` model: added `schedule_token` (String 64, unique, default=`secrets.token_urlsafe(48)`). Migration backfills existing techs.
- `NotificationLog` model: made `appointment_id` nullable (was NOT NULL); added `technician_id` FK (nullable). Needed for "no appointments today" kickoff variant.
- `ContactSubmission` model: added `problem_description` (Text, nullable). Schema + endpoint updated. Migration added.
- `AppointmentResponse` schema: added `problem_description`, `media_urls`, `recurring_schedule_id`.
- `ContactFormSubmit` / `ContactSubmissionResponse` schemas: added `problem_description`.
- New router: `GET /schedule/tech/{token}` — public mobile-first daily schedule page for a single tech. No login. Shows all today's appointments (time, service, customer first name, address link, problem description). Dynamic query — no nightly cron.
- `embed.py` contact form: added "Describe the problem" textarea (200 char max, live character counter with near-limit/at-limit color warnings). `problem_description` sent in payload to `/contact/submit`.
- `AppointmentsPage.jsx`: expandable table rows — clicking a row with detail data reveals address (Google Maps link), problem description (amber icon), notes. Added `ChevronDown/Up`, `MapPin`, `FileText`, `AlertCircle` icons.
- Morning kickoff overhaul (`scheduler.py` + `notifications.py`):
  - **Removed 7am floor** — early texts are fine.
  - **Trigger: 2 hours before first appointment** (±15 min window, prevents re-firing every run).
  - **Techs WITH appointments**: numbered daily summary showing time, service, customer first name, short address, truncated problem description (~50 chars). Public schedule page URL at bottom. "Reply YES when heading to stop 1."
  - **Techs WITHOUT appointments**: fires once between 7–8 AM local. "Good morning [Name]! No appointments scheduled for you today. Enjoy your day off! 🌴". Logged to `notification_logs` with `appointment_id=NULL` keyed to `technician_id` + today date.
  - New `_build_kickoff_body()` helper formats the multi-appointment message.
  - New `send_otw_morning_no_appointments()` function handles the no-jobs variant.

**2026-05-27 (automated daily check — end of day):**
- No new commits since session-close update. CLAUDE.md current. Date stamp updated.

### Pending Monitoring Items
- **A2P approval:** ✅ APPROVED (CUSTOMER_CARE use case). See Section 25 for full verified campaign details. No further action needed unless consent language or CTA URL changes.
- **Morning kickoff delivery:** Kickoff now fires 2 hours before first appointment (±15 min window), no time-of-day floor. Techs with no appointments get a "day off" text between 7–8 AM local. If a tech reports missing kickoff: check (1) appointment exists and is not cancelled/completed, (2) scheduler.py `_send_otw_morning_kickoffs` ran, (3) `notification_logs` for an existing `otw_morning_kickoff` entry. Use admin manual trigger to force-send.
- **Contact responder SMS — mostly resolved:** File corruption caused a SyntaxError on deploy (2026-05-29); fixed by rewrite. SMS now sends full content (480-char cap, full slot dates). Remaining item: set `twilio_phone_number` on demo business via Settings so inbound replies route to the AI booking agent.
- **Soft delete:** All three soft-delete models (`appointments`, `customers`, `contact_submissions`) use a `deleted_at` TIMESTAMP column (not a boolean — set to current UTC time on delete, `NULL` = active). Dashboard UI shows delete buttons with confirmation modal; records disappear from all list views and availability checks immediately. No hard-delete path — recovery requires direct DB access if needed.

---

**2026-05-29 (SMS booking agent — full end-to-end flow):**
- Contact form address fields (street, city, state, zip) added to model, schema, migration, embed form HTML, and JS payload (payload was missing — root cause of address never saving)
- Phone normalized to E.164 at contact form submission time so inbound Twilio webhook lookup matches
- SMS agent `_tool_create_booking` signature fixed (was missing `contact_submission` param — caused TypeError/hiccup on every booking attempt)
- Live DB lookup: inbound webhook now looks up most recent contact submission by phone on every reply and passes to agent — replaces unreliable conversation seeding approach
- Customer enrichment: after booking, customer record populated with email, address, city, state, zip from contact submission
- Timezone fix: slots displayed in business local timezone (was UTC); naive datetimes in create_booking treated as business local time, not UTC
- Duplicate confirmation SMS removed (agent reply handles confirmation naturally)
- SMS bookings set to `confirmed` status (was `pending`) so kickoff/OTW flows include them
- Mandatory check_availability on every agent turn (prevents booking stale slots)
- Initial slot offer reduced to exactly 2 (was 3) to reduce stale-slot risk
- `SMS_AGENT_MODEL` added to config (defaults to `claude-sonnet-4-6`); `LLM_MODEL` now only used by contact form responder
- Twilio Phone Number field added to Settings page (platform admin only) with save + confirmation
- `twilio_phone_number` added to `BusinessResponse` schema so field persists on page load
- Git workflow corrected: all git commands run by Ryan in his terminal, one per line

**2026-05-29 (contact responder SMS fixes + Twilio Settings UI):**
- Contact responder SMS cap increased 300 -> 480 chars (~3 segments); AI now instructed to keep SMS replies under 400 chars and include full dates in slot suggestions (e.g. "Friday, May 30 at 6:30 PM").
- File corruption issue resolved: Edit tool corrupts files containing multi-byte Unicode chars (bullets, em-dashes) in f-strings on the Windows filesystem mount. Workaround: use `.format()` string methods and write files via bash Python script, not the Edit/Write tools.
- `SettingsPage.jsx`: added Twilio Phone Number section (platform admin only). Shows Phone icon, E.164 input, Save button, green confirmation line. Required so platform admins can assign a Twilio number to a business without touching the DB directly.
- Git workflow corrected: Claude must NOT run git commands from bash. All `git add`/`git commit`/`git push` go to Ryan's terminal, one command per line.

**2026-05-28 (Pass 2 — technician UI, soft delete, contact responder fixes):**
- `85321e1` — **Edit Details modal** in AppointmentsPage: "Edit Details" option in 3-dot row menu opens a modal to set `problem_description`, address, technician, and notes directly from the dashboard. Added `problem_description` to `AppointmentUpdate` schema so PUT endpoint accepts it.
- `fab4375` — `schedule_token` added to `TechnicianResponse` schema (was missing; API wasn't returning it so frontend couldn't build schedule page URLs).
- `030ef7e` — **Schedule token shortened**: `token_urlsafe(12)` → 16-char token. Tech schedule URL drops from ~115 chars to ~66 chars (much cleaner in SMS). `run_migrations()` auto-regenerates any existing long tokens on deploy.
- `80bdb60` — Fix `customer.name` → `customer.full_name` in tech schedule page and morning kickoff SMS. `Customer` model has `first_name`/`last_name` columns with a `full_name` property — there is no `.name` field. Was causing 500 on the tech schedule page.
- `50744c3` — Tech SMS day-complete message now uses first name only (`tech.name.split()[0]`). "That's a wrap, Tyler!" not "That's a wrap, Tyler Durden!" Matches the casual tone of employee messages.
- `4ca79a0` — **Technician first/last name split in UI** (frontend-only). Form splits existing `name` on open, joins on save. Last name optional, first name required. Underlying model still stores a single `name` column.
- `9cf3d06` — **Soft delete** (appointments, customers, contact submissions):
  - Added `is_deleted` boolean (default `False`) to `Appointment`, `Customer`, `ContactSubmission` models. Migrations in `run_migrations()`.
  - All list endpoints + availability engine filter `is_deleted = False`.
  - Dashboard: delete buttons added to AppointmentsPage, CustomersPage, ContactsPage row menus.
  - Embed contact form now resets to blank after successful submission.
  - Contact responder session fix: resolved a DB session/context issue causing AI responder failures.
- `6b75ba7` — Fix LLM model string in `config.py` default + startup health check added to `main.py` (validates model at boot, logs prominent WARNING if unreachable). See Section 22.
- `2a7e9bf` — Added Section 23: Periodic Maintenance Schedule to CLAUDE.md.
- `8743402` — **Contact responder channel awareness + SMS truncation fix**:
  - AI reply now references only the customer's preferred contact channel. Pref "text" → "reply to this text"; "email" → "reply to this email"; "call" → mentions business phone, says we'll call. No more channel mismatches.
  - SMS truncation overhaul: old code took first paragraph (~155 chars — usually just the greeting "Hi Name,"). New code skips greeting lines (short line ending with comma), joins remaining paragraphs, caps at 300 chars (~2 SMS segments). Leads with actual useful content.
- **SMS consent compliance (A2P):**
  - `sms_consent: bool` column added to `ContactSubmission` model + migration (default `False`).
  - Schema (`ContactFormSubmit`, `ContactSubmissionResponse`) and contact router updated to save it.
  - SMS only sent when `sms_consent = True` — never assumed.
  - Embed form consent checkbox made **optional** (no `required` attribute) per approved A2P campaign. Exact approved consent language: `(Optional) I agree to receive SMS messages... SMS consent is not required to submit this form or receive service.`
  - Inline form hint: when "text" selected but consent unchecked → `"To receive your reply by text, check the SMS consent box below. Without consent, we'll send your response by email instead."` Hint disappears when both are selected.
- **Single-channel send logic:** Contact responder now sends via exactly one channel — text+consent=SMS only, everything else=email only. Prevents duplicate messages and language mismatches.
- **`pref` scope bug fix:** `pref` was computed inside `_call_llm` (local scope) but referenced in `_process` after the call returned → `NameError`. Fixed by computing `pref` and `sms_consented` at the top of `_process` and passing `pref` into `_call_llm` as a parameter.
- **A2P section corrected in CLAUDE.md:** Campaign is APPROVED with optional checkbox. Section now shows exact Twilio-verified campaign details (use case, keywords, consent language).
- **Periodic Maintenance Schedule added** (Section 23): monthly/quarterly/annual/event-triggered task tables + quick diagnostic reference.
- **Git workflow note added to CLAUDE.md header:** Claude handles `git add` + `git commit` via Bash; Ryan only needs to run `git push`.
