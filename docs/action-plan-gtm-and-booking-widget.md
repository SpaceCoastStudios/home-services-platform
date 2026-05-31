# SCS Action Plan — First Client (GTM) + Self-Scheduling Booking Widget

*Created 2026-05-29 · Owner: Ryan · Two parallel tracks: land a founding Starter client while building the self-scheduling widget so the platform is Professional-ready.*

---

## Status snapshot (start of plan)

- **Platform:** production-deployed, multi-tenant, 36/48 capabilities built. Starter tier has **zero functional gaps**.
- **Only live tenant:** Space Coast Studios Demo (slug `default`). `seed_peak_hvac.py` is an unused template.
- **Marketing site + unlisted demo page:** live (`/` and `/demo.html`).
- **A2P 10DLC:** approved for SCS itself. **Each client needs their own Brand + Campaign (2–4 weeks, carrier-controlled).**
- **CSA:** attorney shortlisted; Ryan selecting + signing week of **June 1, 2026**. CSA must be attorney-reviewed before the first client signs.
- **Founding offer:** 5 spots — Starter $497 setup + $99/mo (3 mo) then $249; Pro $997 + $199/mo (3 mo) then $399.
- **Living docs to keep current:** CLAUDE.md, README, Capability Checklist, Roadmap, **and `SCS_Onboarding_Checklist.docx`** (review now — many features shipped since last update).
- **Prospect list:** 55 businesses loaded into `SCS Prospect Tracker.xlsx` (HVAC 20, Landscaping 20, Roofing 15).

---

## Track A — Land the First (Founding Starter) Client

**Goal:** sign 1 founding Starter client. Channels: **cold local outreach** + **online/inbound**. (No warm network — see neighbor note at the end.)

**Why Starter first:** it's complete and tested today, it's a forgiving real-world shakeout, and it generates revenue + a reference/testimonial without waiting on the widget.

### A1. Define the target customer (ICP)
- **Trade:** HVAC and plumbing first — highest "missed lead = lost money" pain, emergency/after-hours fit, clear ROI story.
- **Profile:** owner-operator or small shop (1–8 techs) on the Space Coast (Brevard County: Melbourne, Palm Bay, Cocoa, Merritt Island, Titusville, Rockledge, Viera). Has a website + Google Business listing but slow/no after-hours response.
- **Disqualifiers:** large franchises (already have ServiceTitan/Housecall Pro), businesses with no web presence (harder to embed/demonstrate value).

### A2. Confirm pre-outreach assets are ready
- [ ] Sales one-pagers exist (`SCS_SalesSheet_HVAC.docx`, Landscaping, Roofing in Test Project root) — review/refresh for current pricing.
- [ ] Demo page live and rendering (`spacecoaststudios.com/demo.html`) — **done**.
- [ ] CSA attorney-reviewed — **pending (week of June 1)**; not required to start outreach, required before signing.
- [ ] Stripe founding-client manual provisioning path ready (`docs/founder-client-onboarding.md`) — exists.
- [ ] A short demo flow rehearsed (see A6).

### A3. Prospect list + tracker (list loaded ✅)
Your **55 businesses** (HVAC 20, Landscaping 20, Roofing 15) are loaded into **`SCS Prospect Tracker.xlsx`** (Test Project root) — one file that is the prospect list, outreach log, and pipeline, with a live Dashboard tab.
- **Enrichment pass (do first, per prospect):** owner name (only 2/55 known), email (13 missing), website, Google Business rating + review count, and the **Response Gap?** flag — the gap is our strongest opener.
- **Fit (1–5)** is pre-seeded by trade (HVAC 5, Landscaping 3, Roofing 2 — roofing is lower-fit: project-based, long cycle, less recurring/emergency). Adjust per prospect; set **Priority** High/Med/Low to decide work order.
- **New trade sheets added** to the tracker (Plumbing, Septic, Pool Service, House Cleaning, Tree Service, Pressure Washing) — ready-to-fill tabs. Compile **Plumbing, Septic, Pool Service, House Cleaning** first (cleanest fit); hold Tree/Pressure Washing until the quote/estimate workflow ships.
- **Flags pre-noted in the tracker:** Paradise Air & Heat / Cool Rays share a phone (verify same company); Paradise Dumpsters tagged "Sell online booking" (may already have booking).
- **Sources to expand the list:** Google Maps / Google Business, Yelp, Brevard contractor listings, Nextdoor/FB.
- *Tip:* test each prospect's own responsiveness (after-hours form/call) — a slow reply is your opener.

### A4. Cold outreach sequence (email-led, phone follow-up)
- **Cadence (per prospect, ~10 business days):**
  1. Day 0 — Email #1: personalized opener (reference their business + the specific gap you noticed), 1-line value prop, link to the demo page, soft CTA ("worth a 15-min look?").
  2. Day 2 — Phone call / voicemail referencing the email.
  3. Day 5 — Email #2: short, lead with a concrete outcome ("never miss an after-hours AC lead again"), mention the 5-spot founding offer (scarcity).
  4. Day 9 — Email #3 "breakup" ("should I close your file?").
- **Assets:** adapt the existing founding-client outreach templates (per project notes). Keep emails <120 words, one CTA, link to `/demo.html`.
- **Volume target:** 10–15 fresh outreaches/week + follow-ups. Track replies → demos booked.
- **Compliance:** cold *email* to businesses is fine (CAN-SPAM: include who you are + an opt-out). Do **not** cold-*text* prospects — your A2P campaign is CUSTOMER_CARE, not sales.

### A5. Online / inbound setup (runs alongside cold outreach)
- [ ] **SCS Google Business Profile** — create/optimize so "Space Coast Studios" is findable and credible.
- [ ] **Marketing-site SEO basics** — title/meta already decent; ensure local keywords ("Space Coast / Brevard home service booking platform"), add a couple of trade-specific landing angles if time allows.
- [ ] **Local Facebook groups / Nextdoor** — participate authentically; soft-mention when relevant (avoid spam).
- [ ] **Light paid test (optional, low budget):** Google Search ads on "[trade] scheduling software" + local geo, or FB ads targeting local home-service owners → demo page. Cap spend; treat as learning, not lifeline.
- [ ] Inbound self-booking on the **main site** is already covered (Get a Demo / Schedule a Free Demo → `#contact`, plus the Calendly under “Prefer to talk first?”). **Add a “Schedule a call” CTA (Calendly link) to the standalone `/demo.html`** so a prospect sent straight to the demo page can also self-book.

### A6. Demo-call playbook (full 15-min script in `SCS Cold Email Sequence.docx`)
The high-value flow: **the prospect drives the customer experience on the demo page themselves, then you screen-share the dashboard** (the part they can't self-serve).
- **0–2 min:** anchor their pain in their own words (the response gap you found).
- **2–6 min:** they fill out the booking widget on the demo page using their own cell → the confirmation text lands on their phone (the "aha").
- **6–11 min:** you reveal the dashboard — **Contacts queue → SMS Conversations → the Appointment that was just created** (tech auto-assigned, address + problem description in the detail row). There is no "notification log" screen — demonstrate notifications by showing the real text landing + the appointment it's attached to.
- **11–13 min:** trade-specific closer — emergency dispatch (HVAC/plumbing/septic) or recurring scheduling (pool/cleaning).
- **13–15 min:** pricing + **5-spot founding** offer; A2P timeline expectation ("platform live in days; SMS features 2–4 weeks after carrier registration, which we start Day 1"); close to CSA + provisioning.
- **Demo prerequisite:** the demo page must be polished first (see Roadmap — realistic sample notifications + iframe sizing) before running live demos.

### A6.5. End-to-end demo readiness test
**Trigger: CSA attorney review complete.** This is the gate before sending the demo link to any real prospect or booking a live call. Run it once when the CSA is signed off — you'll be in "ready to close" mode and need to know the full flow works cold.

**What to test (~30 min):**
1. Open `spacecoaststudios.com/demo.html` in a fresh browser (incognito, no cached state).
2. **Contact widget (Section 1):** submit a test inquiry — real name/email, a test phone number, check the SMS consent box, pick a service, describe a problem. Verify: no scroll bar, form submits cleanly, success state appears.
3. **Dashboard — Contacts queue:** submission appears, AI response shows (auto-send or draft depending on demo tenant setting), response copy reads naturally.
4. **Booking widget (Section 2):** book a slot — pick service, day, time, fill in details, confirm. Verify: success screen shows, no errors, iframe auto-resizes.
5. **Dashboard — Appointments:** new booking appears with correct service, tech auto-assigned, address populated, confirmation SMS + email fired (check the demo number).
6. **Dashboard — Recurring tab:** open the Recurring Series tab, verify it loads cleanly (even if empty on demo).
7. **Tech schedule page:** grab a technician's schedule link from the dashboard (Technicians → copy the schedule URL), open it on mobile — verify it renders and the active-day or day-off state looks right.
8. **Notification screenshots (Section 3):** scroll through the demo page — confirm all 4 screenshot images load, the two full-flow panels (emergency + kickoff) render without distortion.
9. **Dry run the A6 script:** run the full 15-min demo solo, timed. Confirm the "aha" moment (their own text landing) works and the dashboard screen-share flow is smooth.
10. **Clean up:** cancel/delete the test appointment, note any rough edges to fix before the first real call.

**If anything breaks:** fix it before outreach resumes. Log it here.

### A7. Close + contract
- [ ] CSA signed (attorney-reviewed version).
- [ ] Payment: founding client → manual provisioning per `docs/founder-client-onboarding.md`; or standard → Stripe Checkout.
- [ ] Collect: business info, logo, brand color, services, technicians, hours, Google review URL.

### A8. Onboard (Day 1 actions)
- [ ] **Submit A2P Brand + Campaign registration immediately** (longest pole — 2–4 weeks).
- [ ] Provision tenant; have client set password → setup wizard.
- [ ] Configure services, technicians, hours, AI persona, notification templates.
- [ ] Install the embed contact widget on their site.
- [ ] Email notifications live immediately; SMS activates on A2P approval.
- [ ] Run the smoke-test checklist (`SCS_Onboarding_Checklist.docx`).
- [ ] Keep `SCS_Onboarding_Checklist.docx` current as we build — review it now (many features shipped since it was last updated) and update it as onboarding steps change.

### A9. Targets / metrics (tracked in the Dashboard tab of `SCS Prospect Tracker.xlsx`)
- Prospect list: 55 loaded; enrich + add plumbing.
- Outreach: 10–15 new touches/week sustained.
- Leading indicator: demos booked (target 2–4 to land 1 founding client).
- Goal: **1 signed founding Starter client.**

---

## Track B — Self-Scheduling Booking Widget (Professional)

**Recommended scope for v1: Phase 1 — internal-only.** The widget books against the platform's own availability engine; **no external Google/Outlook sync** in v1. Rationale: the availability engine, technician auto-assignment, buffers, and business hours are already built — Phase 1 reuses all of it and gets you a demoable, sellable Professional feature fastest. Calendar sync (Phase 2 Google, Phase 3 Outlook) is a meaningful add but introduces OAuth + two-way-sync complexity that shouldn't gate your first Pro sale.

**Current reality (verified):** `embed.py` serves only the contact form. `/api/availability` exists but is JWT-protected. So v1 needs **new public, slug-scoped endpoints** plus the widget UI.

### B1. Backend — public booking config + availability endpoints
- [ ] `GET /embed/{slug}/booking-config` — returns business name, brand color, active services (with duration + price), booking settings (slot granularity, min lead time, max advance days). Mirror the existing `contact-config` pattern.
- [ ] `GET /embed/{slug}/availability?service_id=&date_range=` — **public** wrapper around the existing `services/scheduling.get_available_slots` logic, scoped by slug (no JWT). Returns open slots in the business's local timezone.
- [ ] Reuse the internal availability engine — do not duplicate the slot math.

### B2. Backend — public booking creation endpoint
- [ ] `POST /embed/{slug}/book` — **public**, slug-scoped. Accepts service, chosen slot, customer name/phone/email/address, optional problem description.
- [ ] Server-side validation: slot still open (re-check at submit), within lead-time/advance limits, valid service.
- [ ] Reuse appointment-creation logic: find/create customer (skip soft-deleted), auto-assign technician, generate `calendar_token`, set `status="confirmed"`, `source="booking_widget"`.
- [ ] Fire the existing confirmation SMS + email (+ calendar links) — same path as other bookings.
- [ ] Normalize phone to E.164; format customer-facing copy with `format_phone_display`.
- [ ] **Spam/abuse protection:** basic rate limiting per IP/phone, honeypot field, and re-validate the slot to prevent double-booking races.

### B3. Frontend — the embeddable widget
- [ ] `GET /embed/{slug}/booking` — self-contained HTML page (same pattern as `/embed/{slug}/contact`), brand-colored, embeddable via one `<iframe>`.
- [ ] **Flow:** select service → pick date (calendar) → see open time slots → enter contact + address → review → confirm → success state.
- [ ] Post a `scs_booking_submitted` `postMessage` to the parent (for iframe auto-resize, like the contact form).
- [ ] Mobile-responsive; graceful "no slots available" and error states.

### B4. Integrate + test
- [ ] Embed the live widget into **demo-page section 2** (replace the "Coming Soon" card).
- [ ] End-to-end test on the Space Coast Studios demo tenant: book a slot → confirm appointment appears in dashboard with correct tech/time/timezone → confirmation SMS + email + calendar link fire → slot disappears from availability.
- [ ] Edge cases: lead-time cutoff, fully-booked day, buffer enforcement, double-submit, timezone correctness.

### B5. Ship + reconcile docs
- [ ] Add the widget to embed install instructions (rolls into the Track C onboarding runbook below).
- [ ] Update Capability Checklist: Online Self-Booking ⚠️ → ✅; marketing claims now fully accurate.
- [ ] Move "Self-scheduling booking widget" on the roadmap from Near-Term → Completed.
- [ ] Do the deferred demo-page polish pass (iframe sizing, live examples).

### Phase 2 / 3 (later, not v1)
- **Phase 2:** Google Calendar two-way sync (OAuth, push bookings + pull busy times).
- **Phase 3:** Outlook/Exchange sync.

---

## Track C — Onboarding Template + Install Runbook (post-widget milestone)

Once the platform is production-ready / semi-complete (after the widget), build the repeatable onboarding kit to cut per-client build time — “onboarding on steroids.” Two layers:

1. **Install / onboarding runbook (docs):** step-by-step stand-up for every component — A2P, Twilio number, services, hours, notification templates, AI persona, embed install, smoke test. Supersizes `SCS_Onboarding_Checklist.docx`.
2. **Parameterized onboarding seeder (automation — the real time-saver):** generalize `seed_peak_hvac.py` into a vertical-aware template. Feed it business name + trade + a few specifics, and it provisions sensible defaults (standard service types + durations, tuned notification templates, a starter AI persona, default hours). The client's setup wizard then just adjusts specifics instead of building from scratch.

Scope this against a **stable target** (post-widget) so we templatize a finished product, not a moving one.

## Sequencing & how the tracks interact

- **This week:** Ryan selects + signs the attorney (week of June 1) and starts building the prospect list (A3). Claude starts Track B (B1–B2 backend).
- **Track A** can run fully in parallel — outreach doesn't depend on the widget. Sell Starter honestly now.
- **Track B** makes you Professional-ready. Aim to have the widget demoable on `/demo.html` before Pro-focused outreach ramps.
- **Shared dependency:** A2P registration is per-client and slow — always Day 1 of onboarding, regardless of track.

---

## Note on the neighbor (HVAC owner across the street)

Reasonable to be cautious about a close-proximity first client. Two low-risk options that don't put the relationship at stake:

1. **Ask for feedback, not a sale.** "I built a tool for home-service businesses — no pitch, I'd just value 15 minutes of your honest take as someone in the trade." You gain real practitioner feedback and possibly a warm referral, with no vendor relationship or money involved.
2. **Ask for introductions.** Even friendly-not-close neighbors will often refer you to other HVAC/plumbing owners they know. A referral from a peer beats a cold email every time.

Only consider them as an actual client if *they* express interest first — and if so, keep it clean with the signed CSA and clear founding-client terms, same as anyone else.
