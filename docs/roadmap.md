# SCS Platform — Build Roadmap

> This file is part of the Space Coast Studios project documentation.
> Tracks completed features, next priorities, blocked items, and nice-to-haves.
> **Update this file** after each build session.

## 24. Build Roadmap

### Completed This Session (2026-05-31 session 2)
1. ✅ **Recurring appointments UI** — enhanced the existing Recurring Series tab: expandable rows, edit modal, appointment history, Generate Now button. Full CRUD + history in `AppointmentsPage.jsx`.
2. ✅ **Demo page polish** — `marketing-site/demo.html` fully polished: contact widget iframe auto-resize (ResizeObserver added to `embed.py`), all-screenshot 2x2 notification cards, 2x2 real-flow panels (emergency + kickoff), unified card titles, green badge, no em dashes. Ready for first demo calls pending A6.5 readiness test.
3. ✅ **Action plan A6.5** — end-to-end demo readiness test checklist added to `docs/action-plan-gtm-and-booking-widget.md`, triggered by CSA finalization.
4. ✅ **AI model selection guide** — added to Section 22 + per-item tags in Platform Capability Checklist.docx and SCS Platform Roadmap.docx.

### Next Session Priorities
1. ✅ **Test on-call rotation + override** -- DONE 2026-05-29.
2. ✅ **Recurring appointments UI** -- DONE 2026-05-31.
3. ✅ **Build self-scheduling booking widget** -- DONE 2026-05-30 (Phase 1 internal-only).
4. ✅ **Demo-page polish** -- DONE 2026-05-31.
5. ✅ **Platform rebrand to Launchpad** -- DONE 2026-06-01. Branding applied across all files; CSA v3 sent to Anjali Sareen for review.
6. **Screenshot refresh** -- populate Launchpad Demo tenant with appointments, retake all notification + flow screenshots, update demo page. Do while waiting for CSA review.
7. **A6.5 end-to-end demo readiness test** -- trigger: CSA attorney review complete + screenshots updated. Gate before first live prospect demo call.
8. **Start outreach (Track A)** -- prospect tracker loaded, templates ready. Begin cold email now; CSA review does not need to be complete to start outreach, only to sign.

### Pending Tests (High Priority -- before first client goes live)
- **Recurring appointments end-to-end** -- ⚠️ HIGH PRIORITY. UI and backend built (2026-05-31) but never tested end-to-end. Must confirm: create schedule → generate instances → appointments appear in feed → notifications fire correctly → disabling schedule stops generation. Run during A6.5 test.
- **Review requests** -- ✅ Confirmed working (2026-06-01). Tech replies YES to complete prompt, review request SMS fires and link works. NOTE: demo tenant Google Review URL is set to `https://www.spacecoaststudios.com` (placeholder). Must set a real Google Review URL on the demo tenant before any prospect demo, and on every new client tenant at onboarding. Set via dashboard Settings → Google Review URL.

### Roadmap (later)
- ~~Plan enforcement (service type + technician caps)~~ -- OBSOLETE as of 2026-06-10: single-tier pricing has no caps; nothing to enforce.
- **Delete business (platform admin)** — `/businesses` page currently only supports deactivating tenants. Add a hard-delete option (with confirmation modal) for platform admins to fully remove test/junk tenants from the DB. Useful for cleaning up after smoke tests.
- **Platform-admin activity log (cross-tenant)** — platform-admin-only view of activity across all businesses (lead submissions, bookings, SMS sent/received, notification fires, errors) with tenant/date filters. Backend already logs notifications (`NotificationLog`) + SMS conversations; this surfaces them in one searchable screen.
- Visual calendar view (day/week/month) in dashboard
- Customer portal (magic link login, view/reschedule)
- Usage/analytics dashboard across tenants
- Emergency contact form routing (wire urgency detection to on-call dispatch)
- Notification template text audit and improvement
- Custom URL shortener for review links
- Quote / estimate workflow (request → estimate → quote → approve → schedule) — makes estimate-first trades (tree, pressure washing, roofing) a great fit

### Blocked / Pending
- **CSA attorney review** -- CSA v5 + Founding Client Pricing Addendum sent to Anjali Sareen (Uncommon Counsel) 2026-06-02 as Word files. Anjali out week of June 9; redline expected week of June 15. Also asked about Schedule A amendment cost if pricing structure changes. Must be reviewed before first client signs. Unblocks A6.5 demo readiness test.

### Pre-Client Business Operations Checklist
These items must be resolved before the first paying client goes live. None block cold outreach or demos.

- **Find an accountant** -- No accountant currently. Need a Florida CPA or bookkeeper familiar with SaaS/tech small business. Priority questions: (1) Is Launchpad subject to Florida sales tax? (2) Quarterly estimated tax setup. (3) General bookkeeping setup. Find before first client invoice is issued.
- **Florida SaaS sales tax** -- Florida taxes some software/technology services; SaaS classification is nuanced. Do not collect or not collect from first client until an accountant confirms the obligation. Do not assume either way.
- **Brevard County local business tax receipt** -- Florida has no statewide business license but Brevard County requires a local business tax receipt. Obtain before first client goes live. Typically straightforward and low cost.
- ~~**Update LLC industry in Tailor Brands**~~ -- OBSOLETE: Tailor Brands cancelled 2026-07-01; replaced with Northwest Registered Agent for registered agent services only.
- **Platform Documentation / Client Guide** -- Required to support the performance warranty in the CSA (Section 11.1 warrants that the Platform will "materially conform to the Documentation"). A short client-facing guide covering: platform features, how widgets work, SMS/email notification flows, and basic dashboard navigation. Format: PDF or web page. Not required before first client signs, but should exist before multiple clients are live. Doubles as an onboarding resource.
- **Screenshot refresh** -- populate Launchpad Demo tenant with appointments, retake all notification + flow panel screenshots, update demo page images. Do while waiting for CSA review.

### Business Development
- Founding client outreach — templates ready, advised to start now (don't wait for A2P)
- Each new client needs their own A2P Brand + Campaign registration — submit Day 1 of onboarding
- **Action plan:** `docs/action-plan-gtm-and-booking-widget.md` — two parallel tracks: (1) cold-local + online/inbound outreach to land a founding **Starter** client (no warm network), (2) build the **self-scheduling booking widget**, v1 scope = **Phase 1 internal-only** (public slug-scoped endpoints + embeddable UI reusing the existing availability engine; Google/Outlook sync deferred to Phase 2/3). Awaiting Ryan's notes on the plan before starting the widget build.

### Nice to Have (later)
- Customer portal
- Usage/analytics dashboard across tenants
- **Notification template text audit** — review and improve all SMS/email templates (confirmation, reminder, OTW, kickoff, day-complete, review request). User noted templates could be "spruced up." Covers contact form AI responder copy too.
- **Custom URL shortener** — branded short domain per client (e.g. hvac.app) for review links and schedule URLs. Low priority for now; schedule token already shortened to 16 chars. Most relevant for Google Review SMS where URL is customer-facing.
- **Voicemail + AI response** (HIGH INTEREST -- candidate for "Coming Soon" on marketing site) — Client keeps existing business number, forwards to Twilio. Twilio records voicemail, Whisper transcribes, Claude generates SMS reply to caller, dashboard logs the full call/transcript/response thread. Requires TwiML call handling as a new capability layer. Cost: ~$0.04/call with Whisper (vs ~$0.23 with Twilio native transcription -- Whisper strongly preferred for both cost and accuracy). See cost estimate from 2026-06-01 session.
- **Promotional/re-engagement SMS campaigns** — Scheduled seasonal SMS to past customer lists (HVAC tune-up, pool holiday specials, etc.). Requires A2P MIXED campaign (new campaign registration; brand stays); marketing opt-in mechanism in platform; opt-in UI on contact form. Both marketing-opt-in UX and A2P re-registration needed before launch.

---
