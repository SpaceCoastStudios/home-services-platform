# Launchpad Demo (SCS Default Tenant)

| Field | Value |
|---|---|
| Slug | `default` |
| Business ID | 1 |
| Name | Launchpad Demo |
| AI Agent Name | Scout |
| is_demo | true |
| Provisioned | Platform seed (always exists) |

## Critical Notes

- **Tenant #1 serves double duty:** it is SCS's own lead intake AND the generic demo tenant.
  - `marketing-site/index.html` `#contact` form submits to `business_id=1`
  - `marketing-site/booking-demo.html` (A2P reviewer page) points at it
- **Never rebrand this tenant as a trade-specific demo company.** Vertical demos get their own tenants.
- **Never point the marketing site contact form at any other business_id.**
- Google Review URL is set to `https://www.spacecoaststudios.com` (placeholder -- set a real URL before any live demo).

## A2P / Twilio Setup
- Uses SCS's main approved CUSTOMER_CARE campaign
- Twilio number set via dashboard Settings -> Twilio Phone Number (platform admin only)

## Default Credentials (dev/demo only -- never use in production)
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Platform admin (`business_id = NULL`) |
