# Founder Client Onboarding Guide

Manual provisioning steps for founding clients at introductory pricing.

**Last updated:** 2026-05-29

---

## When to Use This Guide

Use this guide for founding clients who receive the introductory pricing offer ($497/$997 setup, $99/$199/month for first 3 months). These clients are provisioned manually rather than through the automated Stripe Checkout flow.

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
     - Founding setup price (one-time): `price_1TbXKN2MJMR8rAcZvreEPLwo` (Starter) or `price_1TbXKO2MJMR8rAcZ9MRzpF2s` (Pro)
     - Founding monthly price: `price_1TbXKN2MJMR8rAcZF8PV52FQ` (Starter $99) or `price_1TbXKO2MJMR8rAcZMiHThRka` (Pro $199)
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
  'professional',         -- 'starter' or 'professional'
  true,
  'cus_XXXX',             -- Stripe Customer ID from Step 1
  'sub_XXXX',             -- Stripe Subscription ID from Step 1
  'active',
  'professional',
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
Subject: Your Space Coast Studios Platform is Ready

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

See the **A2P 10DLC Checklist** in the README for the full step-by-step.

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

After 3 months at the founding rate, Stripe automatically bills at the standard rate ($249/month Starter or $399/month Professional) because the founding monthly prices do not have trial period limits — you must manually update the subscription in Stripe at the 3-month mark.

**Calendar reminder:** Set a reminder for Month 3 to either:
- Update the Stripe subscription to the standard monthly price, OR
- Communicate the price change to the client before it takes effect
