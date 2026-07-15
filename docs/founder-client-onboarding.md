# Founder Client Onboarding Guide

Manual provisioning steps for founding clients at introductory pricing.

**Last updated:** 2026-07-15 (single-tier Launchpad pricing; was Starter/Professional)

---

## When to Use This Guide

Use this guide for founding clients who receive the introductory pricing offer: **$497 setup + $149/month for the first 3 months, then $299/month standard rate** (single-tier Launchpad plan, restructured 2026-06-10). These clients are provisioned manually rather than through the automated Stripe Checkout flow.

**Paperwork:** founding clients must sign BOTH the CSA (v6 final) AND the Founding Client Pricing Addendum (`Test Project/SCS-Founding-Client-Pricing-Addendum.docx`). The addendum requires 14-day written notice before the month-4 price transition; calendar this at onboarding (~2.5 months after go-live).

Maximum **5 founding clients** — kept intentionally small for exclusivity and manageable real-world testing.

---

## Step 1 — Create Stripe Customer & Subscription (Manual)

1. Log in to Stripe Dashboard
2. Go to **Customers → + Create customer**
   - Name: client's business name
   - Email: client's email
   - Phone: client's phone
3. Add a payment method for the customer
4. Go to **Subscriptions → + Create subscription**
   - Attach to the customer you just created
   - Add line items:
     - Founding setup price (one-time, $497): `price_1TgmTt2MJMR8rAcZ6YZo6E1P`
     - Founding monthly price ($149/mo): `price_1TgmTt2MJMR8rAcZkwbMP0rK`
   - Note the Stripe Customer ID (`cus_...`) and Subscription ID (`sub_...`)

---

## Step 2 — Create Business & Admin User in the Database

Connect to the database:
```bash
psql "postgresql://doadmin:PASSWORD@host.db.ondigitalocean.com:25060/defaultdb?sslmode=require"
```

Insert the business record:
```sql
INSERT INTO businesses (
  name, slug, plan, is_active,
  stripe_customer_id, stripe_subscription_id, subscription_status, subscription_tier,
  ai_agent_name, timezone, has_completed_setup
) VALUES (
  'Client Business Name',
  'client-slug',          -- URL-safe, lowercase, hyphens (e.g. 'peak-hvac')
  'launchpad',            -- single-tier plan (legacy 'starter'/'professional' retired 2026-06-10)
  true,
  'cus_XXXX',             -- Stripe Customer ID from Step 1
  'sub_XXXX',             -- Stripe Subscription ID from Step 1
  'active',
  'launchpad',
  'Scout',                -- AI agent name (customize per client)
  'America/New_York',
  false
) RETURNING id;
```

Note the returned `business_id`. Then create the admin user:
```sql
INSERT INTO admin_users (
  username, password_hash, role, business_id,
  email, password_reset_token, password_reset_expires
) VALUES (
  'client@email.com',
  'UNUSABLE_PASSWORD_HASH',   -- placeholder; client sets real password via token
  'admin',
  <business_id from above>,
  'client@email.com',
  encode(gen_random_bytes(48), 'base64'),   -- generates reset token
  NOW() + INTERVAL '72 hours'
) RETURNING id, password_reset_token;
```

Note the `password_reset_token`.

---

## Step 3 — Send Welcome Email

Send the client a welcome email with:
- Their username (their email address)
- Password set link: `https://dashboard.spacecoaststudios.com/set-password?token=<password_reset_token>`
- Link expires in 72 hours

Template:
```
Subject: Your Launchpad Platform is Ready

Hi [Name],

Your platform is set up and ready to go. Here's how to log in:

Username: [their email]
Set your password: https://dashboard.spacecoaststudios.com/set-password?token=<TOKEN>

This link expires in 72 hours. Once you set your password, you'll be walked through a quick setup wizard to configure your business info, branding, and AI settings.

If you have any questions, reply to this email or call/text Ryan at [your number].

Welcome aboard!
Ryan
Space Coast Studios
```

---

## Step 4 — A2P 10DLC Registration (Day 1)

Submit immediately — approval takes 2–4 weeks. Platform goes live on everything except SMS while you wait.

See `docs/a2p-compliance.md` for full campaign details and the per-client setup checklist.

Key steps:
1. Purchase a local Twilio number in the client's area code
2. Create Messaging Service + add number to sender pool
3. Register A2P Brand (client's EIN, business info)
4. Create CUSTOMER_CARE campaign
5. Register phone number to campaign
6. Configure inbound webhook on the number itself

---

## Step 5 — Platform Configuration

Once the client completes the setup wizard, finish the platform configuration:

- [ ] Set `twilio_phone_number` on the Business record in **Settings** (platform admin view)
- [ ] Configure business hours (Settings → Business Hours)
- [ ] Add service types (Services page)
- [ ] Add technicians with phone numbers (Technicians page)
- [ ] Set Google Review URL (Settings → Review Requests)
- [ ] Customize notification templates if needed (Notification Templates page)
- [ ] Verify AI persona name and system prompt (Settings)

---

## Step 6 — Smoke Test (Before Client Goes Live)

Run through the full smoke test checklist in `SCS_Onboarding_Checklist.docx`. Key tests:

**Contact form + AI flow:**
1. Go to `https://api.spacecoaststudios.com/embed/{client-slug}/contact`
2. Fill out form with a real phone number and address — check SMS consent box
3. Verify: contact submission appears in dashboard Contact Queue
4. Verify: AI reply SMS arrives with 2 slot options, correct times in local timezone
5. Reply to SMS with a slot choice
6. Verify: agent books appointment (no "hiccup"), correct time displayed in dashboard

**OTW flow (once A2P approved):**
1. Create a test appointment with a tech whose phone is your real number
2. Go to Settings → Developer Tools → Trigger Morning Kickoffs
3. Verify: kickoff SMS arrives with correct job summary and schedule URL
4. Go to Settings → Developer Tools → Trigger OTW Prompts
5. Reply YES to OTW prompt from tech phone
6. Verify: customer OTW SMS arrives, appointment → en_route
7. Reply YES to complete prompt
8. Verify: review request sent to customer, appointment → completed

**What to tell the client about SMS timing:**
> "Your platform goes live with all features within one week. SMS features require a one-time carrier registration that takes 2–4 weeks — we submit it on Day 1. Everything else (email confirmations, dashboard, contact form) works immediately while we wait."

---

## Step 7 — Transition Pricing (Month 4)

After 3 months at the founding rate ($149/mo), the client transitions to the standard rate of **$299/month** (`price_1TgmTt2MJMR8rAcZshH8T7uB`). The founding monthly price does not auto-transition -- you must manually update the subscription in Stripe at the 3-month mark.

**Calendar reminders (set both at onboarding):**
- ~2.5 months after go-live: send the client 14-day written notice of the transition (required by the Founding Client Pricing Addendum)
- Month 3: update the Stripe subscription to the standard monthly price
