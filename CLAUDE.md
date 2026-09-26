# CLAUDE.md — context for AI sessions working on BangOps

BangOps is Bang Design's (bangid.com, ~20-person design studio, 1 credit = 1 hour) personal-agent system. Start with [`README.md`](README.md), then [`docs/status/current-state-audit.md`](docs/status/current-state-audit.md).

## Current priority (v1)
1. Resource-sheet rows **drafted automatically, approved in one click**, never typed from scratch.
2. Awareness of incoming client email (each person's own inbox).
3. SOP-quality client emails from a plain note ("I did X, want feedback") → project detected → options → draft → copy / Gmail draft / send on approval.

## Hard constraints
- Google Workspace only. **No Google Cloud project, no service account, no Admin Console work** by default. The proposed runtime is a Google Apps Script web app running as the accessing user ([`docs/architecture/architecture-v2-workspace-native.md`](docs/architecture/architecture-v2-workspace-native.md)).
- A human approves anything client-facing. Nothing is sent automatically.
- No screen or app monitoring. Signals only (chat notes, sent mail, calendar).
- English only. Passwords and secrets are out of scope as a feature.
- **Never commit secrets.** Webhooks and API keys come from environment variables or Script Properties (see `.env.example`).

## How to work here
- **Research-driven.** Back decisions with a comparison against real products and cite sources (see [`docs/research/competitive-research-2026.md`](docs/research/competitive-research-2026.md)). Record new user answers in [`docs/research/qa-interview-log.md`](docs/research/qa-interview-log.md).
- **UI work follows [`docs/design/design-brief.md`](docs/design/design-brief.md):** research references first, a 4 px spacing scale, one accent, no emoji, one job per screen.
- Communication rules for any drafted email: [`docs/sop/communication-commandments.md`](docs/sop/communication-commandments.md) (the Spine + 11 Commandments).
- `demo/python-agents/` is a reference demo only (in-memory, no LLM calls). Don't treat it as the production base.
- `legacy/` is an archived, unrelated earlier app.

## Open questions (still to ask the user)
Workspace plan tier (does it include Gemini/Studio?) · Claude vs Gemini API · who maintains the Studio Brain sheet · go-ahead for the 1-day Apps Script spike.
