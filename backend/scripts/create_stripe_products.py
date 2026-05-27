"""
Create Stripe products and prices for Space Coast Studios.

Run once to set up all products/prices in Stripe, then copy the printed
price IDs into your environment variables / config.

Usage:
    STRIPE_SECRET_KEY=sk_live_... python scripts/create_stripe_products.py

Or if your .env is loaded:
    python scripts/create_stripe_products.py
"""

import os
import sys

try:
    import stripe
except ImportError:
    print("Installing stripe...")
    os.system(f"{sys.executable} -m pip install stripe --quiet")
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

print(f"Using Stripe key: {stripe.api_key[:12]}...")
print()


def create_product(name, description, metadata=None):
    product = stripe.Product.create(
        name=name,
        description=description,
        metadata=metadata or {},
    )
    print(f"  Created product: {product.name} ({product.id})")
    return product


def create_price(product_id, amount_cents, currency="usd", recurring=None, nickname=None, metadata=None):
    kwargs = dict(
        product=product_id,
        unit_amount=amount_cents,
        currency=currency,
        metadata=metadata or {},
    )
    if recurring:
        kwargs["recurring"] = recurring
    if nickname:
        kwargs["nickname"] = nickname
    price = stripe.Price.create(**kwargs)
    print(f"    Price: {price.nickname or price.id}  =>  ${amount_cents/100:,.2f}"
          + (" /month" if recurring else " one-time")
          + f"  [ID: {price.id}]")
    return price


print("=" * 60)
print("Creating Stripe products and prices...")
print("=" * 60)
print()

# ── STARTER ──────────────────────────────────────────────────────────────────
print("STARTER PLAN")
starter = create_product(
    name="Starter Plan",
    description="AI contact form, embeddable widget, up to 3 services & 5 techs, email notifications, admin dashboard.",
    metadata={"plan": "starter"},
)

starter_setup = create_price(
    starter.id, 199700, nickname="Starter — Setup Fee",
    metadata={"plan": "starter", "type": "setup"},
)
starter_monthly = create_price(
    starter.id, 24900, nickname="Starter — Monthly",
    recurring={"interval": "month"},
    metadata={"plan": "starter", "type": "monthly"},
)
starter_setup_founding = create_price(
    starter.id, 49700, nickname="Starter — Founding Setup Fee",
    metadata={"plan": "starter", "type": "setup", "offer": "founding"},
)
starter_monthly_founding = create_price(
    starter.id, 9900, nickname="Starter — Founding Monthly (3 mo)",
    recurring={"interval": "month"},
    metadata={"plan": "starter", "type": "monthly", "offer": "founding"},
)
print()

# ── PROFESSIONAL ─────────────────────────────────────────────────────────────
print("PROFESSIONAL PLAN")
professional = create_product(
    name="Professional Plan",
    description="Everything in Starter plus SMS agent, self-scheduling widget, OTW notifications, review requests, emergency dispatch, recurring scheduling, custom AI persona, priority support & monthly call.",
    metadata={"plan": "professional"},
)

pro_setup = create_price(
    professional.id, 299700, nickname="Professional — Setup Fee",
    metadata={"plan": "professional", "type": "setup"},
)
pro_monthly = create_price(
    professional.id, 39900, nickname="Professional — Monthly",
    recurring={"interval": "month"},
    metadata={"plan": "professional", "type": "monthly"},
)
pro_setup_founding = create_price(
    professional.id, 99700, nickname="Professional — Founding Setup Fee",
    metadata={"plan": "professional", "type": "setup", "offer": "founding"},
)
pro_monthly_founding = create_price(
    professional.id, 19900, nickname="Professional — Founding Monthly (3 mo)",
    recurring={"interval": "month"},
    metadata={"plan": "professional", "type": "monthly", "offer": "founding"},
)
print()

# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("=" * 60)
print("DONE. Add these to your environment variables / config:")
print("=" * 60)
print()
print("# Starter")
print(f'STRIPE_PRICE_STARTER_SETUP="{starter_setup.id}"')
print(f'STRIPE_PRICE_STARTER_MONTHLY="{starter_monthly.id}"')
print(f'STRIPE_PRICE_STARTER_SETUP_FOUNDING="{starter_setup_founding.id}"')
print(f'STRIPE_PRICE_STARTER_MONTHLY_FOUNDING="{starter_monthly_founding.id}"')
print()
print("# Professional")
print(f'STRIPE_PRICE_PRO_SETUP="{pro_setup.id}"')
print(f'STRIPE_PRICE_PRO_MONTHLY="{pro_monthly.id}"')
print(f'STRIPE_PRICE_PRO_SETUP_FOUNDING="{pro_setup_founding.id}"')
print(f'STRIPE_PRICE_PRO_MONTHLY_FOUNDING="{pro_monthly_founding.id}"')
print()
print("# Product IDs (for reference)")
print(f'STRIPE_PRODUCT_STARTER="{starter.id}"')
print(f'STRIPE_PRODUCT_PROFESSIONAL="{professional.id}"')
