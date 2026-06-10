"""
Create the single-tier Launchpad product and prices in Stripe.

One-tier pricing restructure (June 2026):
  - Launchpad Setup:            $999 one-time
  - Launchpad Monthly:          $299/month
  - Founding Setup:             $497 one-time   (manual subscriptions only)
  - Founding Monthly:           $149/month for first 3 months (manual subscriptions only)

Run once, then copy the printed price IDs into:
  1. backend/app/config.py (STRIPE_PRICE_LAUNCHPAD_* defaults)
  2. DigitalOcean api component environment variables

Usage:
    STRIPE_SECRET_KEY=sk_live_... python scripts/create_launchpad_prices.py

The old Starter/Professional products and prices are NOT deleted.
Leave them in place (Stripe best practice); they are simply no longer sold.
"""

import os
import sys

try:
    import stripe
except ImportError:
    print("Installing stripe...")
    os.system("{0} -m pip install stripe --quiet".format(sys.executable))
    import stripe

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
if not stripe.api_key:
    sys.exit("ERROR: STRIPE_SECRET_KEY environment variable not set.")

print("Using Stripe key: {0}...".format(stripe.api_key[:12]))
print()


def create_product(name, description, metadata=None):
    product = stripe.Product.create(
        name=name,
        description=description,
        metadata=metadata or {},
    )
    print("  Created product: {0} ({1})".format(product.name, product.id))
    return product


def create_price(product_id, amount_cents, recurring=None, nickname=None, metadata=None):
    kwargs = dict(
        product=product_id,
        unit_amount=amount_cents,
        currency="usd",
        metadata=metadata or {},
    )
    if recurring:
        kwargs["recurring"] = recurring
    if nickname:
        kwargs["nickname"] = nickname
    price = stripe.Price.create(**kwargs)
    print("    Price: {0}  =>  ${1:,.2f}{2}  [ID: {3}]".format(
        price.nickname or price.id,
        amount_cents / 100,
        " /month" if recurring else " one-time",
        price.id,
    ))
    return price


print("=" * 60)
print("Creating Launchpad product and prices (single-tier)...")
print("=" * 60)
print()

launchpad = create_product(
    name="Launchpad",
    description=(
        "Fully managed AI booking platform: AI contact form responder, "
        "AI SMS booking agent, self-scheduling booking widget, SMS & email "
        "confirmations and reminders, On The Way alerts, Google review requests, "
        "emergency dispatch with on-call management, recurring scheduling, "
        "unlimited services & technicians, custom AI persona & branding, "
        "priority support and monthly check-in call."
    ),
    metadata={"plan": "launchpad"},
)

setup = create_price(
    launchpad.id, 99900, nickname="Launchpad - Setup Fee",
    metadata={"plan": "launchpad", "type": "setup"},
)
monthly = create_price(
    launchpad.id, 29900, nickname="Launchpad - Monthly",
    recurring={"interval": "month"},
    metadata={"plan": "launchpad", "type": "monthly"},
)
setup_founding = create_price(
    launchpad.id, 49700, nickname="Launchpad - Founding Setup Fee",
    metadata={"plan": "launchpad", "type": "setup", "offer": "founding"},
)
monthly_founding = create_price(
    launchpad.id, 14900, nickname="Launchpad - Founding Monthly (3 mo)",
    recurring={"interval": "month"},
    metadata={"plan": "launchpad", "type": "monthly", "offer": "founding"},
)
print()

print("=" * 60)
print("DONE. Add these to config.py and the DO env vars:")
print("=" * 60)
print()
print('STRIPE_PRICE_LAUNCHPAD_SETUP="{0}"'.format(setup.id))
print('STRIPE_PRICE_LAUNCHPAD_MONTHLY="{0}"'.format(monthly.id))
print('STRIPE_PRICE_LAUNCHPAD_SETUP_FOUNDING="{0}"'.format(setup_founding.id))
print('STRIPE_PRICE_LAUNCHPAD_MONTHLY_FOUNDING="{0}"'.format(monthly_founding.id))
print()
print('STRIPE_PRODUCT_LAUNCHPAD="{0}"'.format(launchpad.id))
