# Client & Tenant Files

This folder contains per-client configuration notes for every tenant on the Launchpad platform.

## How to use

- **When onboarding a new client:** create a new file here named `[slug].md` (e.g. `brevard-hvac-pro.md`)
- **Do NOT add client-specific info to CLAUDE.md** -- it goes here
- **CLAUDE.md Section 11** has the multi-tenancy architecture; this folder has the per-client facts

## Template for new clients

```markdown
# [Business Name]

| Field | Value |
|---|---|
| Slug | `slug-here` |
| Business ID | TBD (set after provisioning) |
| AI Agent Name | Name |
| Brand Color | #hex |
| Twilio Number | +1XXXXXXXXXX |
| is_demo | true / false |
| Provisioned | YYYY-MM-DD |

## A2P / Twilio Setup
- Campaign: [existing CUSTOMER_CARE / new campaign name]
- Number registered to campaign: yes/no
- Inbound webhook: set / not set
- Status: pending / approved / live

## Notes
- ...
```

## Active Tenants
| Slug | Name | Status | File |
|---|---|---|---|
| `default` | Launchpad Demo (SCS lead intake) | Live | [scs-launchpad-demo.md](scs-launchpad-demo.md) |
| `brevard-pool-pros` | Brevard Pool Pros | Live (demo) | [brevard-pool-pros.md](brevard-pool-pros.md) |
