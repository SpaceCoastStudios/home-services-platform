# Launchpad by Space Coast Studios

Multi-tenant AI-powered scheduling, dispatch, and notifications platform for home service businesses.

**Platform brand:** Launchpad | **Company:** Space Coast Studios LLC | **Status:** Production, all core features built and tested.

| Component | Provider | URL |
|---|---|---|
| API / Backend | DigitalOcean App Platform | `https://api.spacecoaststudios.com` |
| Database | DigitalOcean Managed PostgreSQL 18 | NYC3 |
| Dashboard | Netlify | `https://dashboard.spacecoaststudios.com` |
| Marketing Site | Netlify | `https://spacecoaststudios.com` |

All three components auto-deploy on push to `main`.

## Documentation Map

**`CLAUDE.md` (repo root) is the master reference** for architecture, auth, multi-tenancy, billing, notifications, AI systems, and workflow rules. Start there. Topic-specific detail lives in `docs/`:

| Doc | Contents |
|---|---|
| `docs/status.md` | Capability status: built / partial / not built |
| `docs/roadmap.md` | Priorities, blocked items, completed work |
| `docs/activity-log.md` | Full session-by-session history and changelog |
| `docs/api-reference.md` | Complete endpoint tables |
| `docs/repo-structure.md` | Annotated file tree |
| `docs/maintenance.md` | Periodic maintenance schedule + diagnostics |
| `docs/a2p-compliance.md` | A2P 10DLC campaign, approved consent language |
| `docs/founder-client-onboarding.md` | Manual provisioning for founding clients |
| `docs/on-call-emergency-testing.md` | Repeatable on-call / emergency test plan |
| `docs/clients/` | Per-tenant config (one file per client) |
| `docs/archive/` | Superseded planning docs (original architecture plan, GTM action plan) |

Environment variables: CLAUDE.md Section 8. Stripe pricing and price IDs: CLAUDE.md Sections 4 and 12. Common pitfalls: CLAUDE.md Section 28. The changelog formerly kept in this README was merged into `docs/activity-log.md` on 2026-07-15.

## Quickstart (Local Development)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill in secrets
uvicorn app.main:app --reload   # http://localhost:8000

# Frontend
cd frontend/dashboard
npm install
npm run dev                      # http://localhost:5173 (proxies /api to prod API)
```

## Tech Stack

Python 3.11 + FastAPI + SQLAlchemy 2.x + PostgreSQL 18 (backend); React 18 + Vite + Tailwind (dashboard); static HTML (marketing site). SMS via Twilio (A2P 10DLC), email via SendGrid, payments via Stripe, AI via the Anthropic API (`LLM_MODEL` for the contact responder, `SMS_AGENT_MODEL` for the SMS booking agent).

## Deploy

```bash
git add <files>
git commit -m "message"
git push   # all three components auto-deploy
```

Note: in Cowork sessions, git commands are run by Ryan in his own terminal (see CLAUDE.md header for why).
