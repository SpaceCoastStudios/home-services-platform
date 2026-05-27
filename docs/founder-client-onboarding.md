# Founder Client Onboarding — Manual Process Guide

This guide covers how to manually onboard a founding client who has agreed to the introductory
pricing offer. Since the Stripe Checkout flow creates the tenant automatically at full price, founding clients
are handled out-of-band so you can apply discounted prices. This is a one-time setup per client and
takes about 10 minutes.

---

## Overview

The flow is:
1. Create the client in Stripe with a custom subscription at founding prices
2. Create the Business + Admin User record in the platform database
3. Send the client their set-password link

---

## Step 1 — Create the Customer and Subscription in Stripe

### 1a. Create a Customer

1. Go to [Stripe Dashboard → Customers](https://dashboard.stripe.com/customers)
2. Click **+ Add customer**
3. Fill in:
   - **Email** — the client's email address
   - **Name** — the owner's full name
   - **Phone** — the client's phone number
   - **Description** — e.g. `Founding client – Starter`
   - **Address** — billing address (optional but recommended)
4. Click **Add customer**

### 1b. Create a Subscription with Founding Prices

1. Open the customer you just created
2. Click **+ Create subscription**
3. Under **Product or price**, search for the founding price products:
   - **Starter founding**: one-time setup $497 + $99/month  
   - **Professional founding**: one-time setup $997 + $199/month
   
   > **Note:** These prices must exist in your Stripe product catalog. If they don't yet, go to
   > **Products → + Add product** and create them first, then come back.

4. Add both line items (setup fee + monthly):
   - Click **Add another item**, search for and select the appropriate monthly price
5. Set **Billing start date** to today
6. Under **Payment collection**, choose **Charge automatically**
7. Click **Start subscription**

### 1c. Record the IDs

Copy these two values from the subscription detail page — you'll need them in Step 2:
- **Customer ID** — format `cus_XXXXXXXXXX` (in the Customer panel on the right)
- **Subscription ID** — format `sub_XXXXXXXXXX` (at the top of the subscription detail)

---

## Step 2 — Create the Business and Admin User in the Platform

There are two methods: using the Django-style admin (if available) or directly via a database command.

### Method A — Via the Platform Admin Dashboard (Recommended once the admin panel exists)

> This section will be updated once a platform admin Create Business UI is built.

### Method B — Via the Backend API (current approach)

Use the platform's existing admin endpoints. You'll need your own platform admin JWT token.

#### 2a. Get your admin token

```bash
curl -X POST https://api.spacecoaststudios.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "YOUR_ADMIN_USERNAME", "password": "YOUR_ADMIN_PASSWORD"}'
```

Copy the `access_token` from the response.

#### 2b. Create the Business

```bash
curl -X POST https://api.spacecoaststudios.com/api/businesses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Client Business Name",
    "slug": "client-business-slug",
    "email": "client@example.com",
    "phone": "3215550100",
    "address": "123 Main St, Melbourne, FL 32901",
    "plan": "starter",
    "stripe_customer_id": "cus_XXXXXXXXXX",
    "stripe_subscription_id": "sub_XXXXXXXXXX",
    "subscription_tier": "starter",
    "subscription_status": "active",
    "is_active": true
  }'
```

Note the returned `id` (e.g. `5`) — you'll use it in the next step.

> **Slug rules:** lowercase letters, numbers, and hyphens only. Must be unique. Example:
> `smith-hvac-cooling` for "Smith HVAC & Cooling".

#### 2c. Create the Admin User

```bash
curl -X POST https://api.spacecoaststudios.com/api/businesses/5/admin-users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "username": "client@example.com",
    "email": "client@example.com",
    "role": "admin"
  }'
```

> If this endpoint doesn't exist yet, use Method C below.

### Method C — Direct Database (via DO console or psql)

SSH into the database or use the DigitalOcean managed DB query editor.

```sql
-- 1. Insert the business
INSERT INTO businesses (
  name, slug, email, phone, address,
  stripe_customer_id, stripe_subscription_id,
  subscription_tier, subscription_status,
  is_active, is_demo, created_at
) VALUES (
  'Smith HVAC & Cooling',
  'smith-hvac-cooling',
  'owner@smithhvac.com',
  '3215550100',
  '123 Main St, Melbourne, FL 32901',
  'cus_XXXXXXXXXX',
  'sub_XXXXXXXXXX',
  'starter',
  'active',
  true,
  false,
  NOW()
) RETURNING id;

-- Note the returned id (e.g. 5)

-- 2. Generate a reset token (do this in Python to get a secure token)
-- Run this in any Python shell:
--   import secrets; print(secrets.token_urlsafe(48))
-- Copy the output as YOUR_TOKEN_VALUE below

-- 3. Insert the admin user
INSERT INTO admin_users (
  business_id, username, email, password_hash, role,
  is_active, password_reset_token, password_reset_expires, created_at
) VALUES (
  5,                              -- business id from above
  'owner@smithhvac.com',          -- username = email
  'owner@smithhvac.com',
  'UNUSABLE_HASH',                -- will be replaced when they set their password
  'admin',
  true,
  'YOUR_TOKEN_VALUE',             -- token from secrets.token_urlsafe(48)
  NOW() + INTERVAL '72 hours',   -- link expires in 72 hours
  NOW()
);
```

---

## Step 3 — Send the Set-Password Email

Once the admin user record exists with a valid `password_reset_token`, send the client their
welcome email manually.

The set-password URL is:

```
https://dashboard.spacecoaststudios.com/set-password?token=YOUR_TOKEN_VALUE
```

**Email template:**

> Subject: Welcome to Space Coast Studios — Set up your account
>
> Hi [Owner Name],
>
> Your Space Coast Studios dashboard for **[Business Name]** is ready!
>
> Click the link below to set your password and log in:
> https://dashboard.spacecoaststudios.com/set-password?token=YOUR_TOKEN_VALUE
>
> This link expires in 72 hours.
>
> Once you're in, I'll schedule your onboarding call to walk you through the full setup.
>
> Welcome aboard!
> Ryan
> Space Coast Studios
> ryan@spacecoaststudios.com

---

## Step 4 — Post-Onboarding Checklist

After the client logs in, make sure these are configured in their Settings page:

- [ ] Business name, logo, and brand color
- [ ] Twilio phone number assigned (update `twilio_phone_number` in the DB or admin panel)
- [ ] Business hours set
- [ ] At least one service type created
- [ ] At least one technician added
- [ ] Google Review URL set (for automated review requests)
- [ ] Notification templates reviewed and customized
- [ ] AI persona configured (Professional plan)
- [ ] Contact form / booking widget embedded on their website

---

## Troubleshooting

### "Invalid or missing link" on set-password page

The token may have expired (72-hour window) or already been used. Generate a new one:

```python
import secrets
print(secrets.token_urlsafe(48))
```

Then update the DB:

```sql
UPDATE admin_users
SET password_reset_token = 'NEW_TOKEN',
    password_reset_expires = NOW() + INTERVAL '72 hours'
WHERE email = 'client@example.com';
```

And resend the email with the new token.

### Client can't receive SMS

The Twilio number's "A message comes in" webhook must point to:
`https://api.spacecoaststudios.com/webhook/sms/inbound`

See the main README for full Twilio configuration instructions.

### Password was set but client can't log in

Verify the `username` in `admin_users` matches exactly what they're typing (it's the email address,
case-sensitive in login).

---

## Creating Founding Prices in Stripe (One-time Setup)

If the founding price products don't exist yet in your Stripe catalog:

1. Go to **Products → + Add product**
2. Create **"Starter Setup Fee (Founding)"**: one-time, $497
3. Create **"Starter Monthly (Founding)"**: recurring monthly, $99
4. Create **"Professional Setup Fee (Founding)"**: one-time, $997
5. Create **"Professional Monthly (Founding)"**: recurring monthly, $199

You don't need to wire these into the checkout API — they're used only for manual subscriptions.

---

*Last updated: May 2026*
