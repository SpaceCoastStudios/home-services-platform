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

### A3. Build the prospect list (target ~40–60 to start)
- **Sources:** Google Maps / Google Business search ("HVAC near Cocoa FL", "plumber Melbourne FL"), Yelp, Brevard County contractor listings, Nextdoor/local FB business pages.
- **Capture per prospect (simple spreadsheet):** business name, owner name (if findable), phone, email, website URL, Google review count/rating, whether they have an after-hours/contact form, notes.
- **Prioritize:** businesses with a website but an obvious response gap (no chat, no after-hours messaging, mediocre review velocity) — they feel the pain you solve.
- *Tip:* test their own responsiveness — submit a contact form or call after hours. A slow reply is your opener.

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
- [ ] Ensure the demo-page CTA path is clear (it currently has no "book a call" button — consider adding a Calendly link on `/demo.html` so an inbound visitor can self-book a demo).

### A6. Demo-call playbook
- Open with their pain (the response gap you found).
- Walk the **live demo page**: submit the real contact widget → show the AI reply concept → the dashboard → notification examples → emergency dispatch.
- Be honest about tiers: Starter = lead capture + AI responder + notifications + dashboard (live today); self-scheduling widget is Professional and shipping soon.
- Present pricing + the **founding 5-spot** offer; set the A2P timeline expectation ("platform live in days; SMS features 2–4 weeks after carrier registration, which we start Day 1").
- Close to next step: send CSA + Stripe link (or manual founding provisioning).

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

### A9. Targets / metrics
- Prospect list: 40–60 built in week 1.
- Outreach: 10–15/week sustained.
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
- [ ] Add the widget to Starter/Pro embed install instructions.
- [ ] Update Capability Checklist: Online Self-Booking ⚠️ → ✅; marketing claims now fully accurate.
- [ ] Move "Self-scheduling booking widget" on the roadmap from Near-Term → Completed.
- [ ] Do the deferred demo-page polish pass (iframe sizing, live examples).

### Phase 2 / 3 (later, not v1)
- **Phase 2:** Google Calendar two-way sync (OAuth, push bookings + pull busy times).
- **Phase 3:** Outlook/Exchange sync.

---

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
