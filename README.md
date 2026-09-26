# BangOps — Operations Hub & AI Agent System

> **Bang Design** ([bangid.com](https://bangid.com)) internal studio operations hub, intelligent vendor discovery, resource tracking, and proactive agent framework.

---

## 📖 Executive Summary for Humans & AI Agents

Bang Design is a multidisciplinary design consultancy operating on a **credit subscription model** (covering UI/UX, Product Design, Industrial Design, and Engineering). 
- **1 Hour = 1 Credit**.
- Clients purchase bundles of credits (e.g., Pro 140 credits).
- ~20 team members work across multiple concurrent client projects, expending hours/credits.

### Core Problems Being Solved
1. **Vendor Intelligence:** Finding the right fabrication vendor (SLA/SLS 3D printing, CNC, sheet metal, injection moulding) without senior/founder bottlenecks or parsing complex quote comparison spreadsheets.
2. **Resource & Time Logging:** Eliminating forgotten or vague timesheet entries. Personal agents capture work progress and convert casual notes into client-ready log lines in individual Resource Sheets.
3. **Attendance & Sick Leave:** Morning check-ins gently capture attendance/sickness, automatically notifying project teammates and updating the dashboard.
4. **Cross-Team Alignment:** Connecting Industrial Design, Marketing, and Engineering asynchronously via daily agent rollups instead of low-attendance standup calls.
5. **Brand & Client SOPs:** Hardcoding the company's "Communication Commandments" ("The Spine" structure, quantifying effort, zero silence) directly into agent drafting assistants.

---

## 🚦 Current Status & Priority (updated 26 Sep 2026)

- **Where we are:** discovery and design are mostly done. Building has barely started (the Python agents are demos with no LLM calls and no Sheet writes). See [`docs/current-state-audit.md`](docs/status/current-state-audit.md).
- **v1 priority (narrowed):** (1) resource-sheet rows drafted automatically and approved in one click, (2) awareness of incoming client email, (3) SOP-quality client drafts from a plain note ("I did X, want feedback"), then copy / Gmail draft / send on approval.
- **Research:** a comparison of paid and open-source tools with pricing is in [`docs/competitive-research-2026.md`](docs/research/competitive-research-2026.md). No single product covers all three, and most self-hosted options need a Google Cloud project.
- **Proposed direction:** a Workspace-native personal agent built on **Google Apps Script** (no Cloud project, no service account, no admin console), running as each user. See [`docs/architecture-v2-workspace-native.md`](docs/architecture/architecture-v2-workspace-native.md).
- **Security:** the Chat webhook that used to be hard-coded in the demo scripts is now read from `BANGOPS_CHAT_WEBHOOK`. The old key was shared in local files before this, so rotate it.
- **Next:** UI redesign driven by research, see [`docs/design/design-brief.md`](docs/design/design-brief.md).

---

## 🗂️ Project Directory Map

Any AI model or developer navigating this codebase should use this map:

```
BangOps/
├── README.md                     # Start here: overview, status, decisions
├── CLAUDE.md                     # Context + rules for AI sessions (cloud / Claude Code)
├── .env.example                  # Env vars (never commit .env)
│
├── docs/
│   ├── status/
│   │   └── current-state-audit.md          # What's real vs on paper, contradictions, security
│   ├── research/
│   │   ├── competitive-research-2026.md    # Paid + open-source tools compared, pricing
│   │   ├── qa-interview-log.md             # Every interview Q&A and decision (living record)
│   │   ├── pain-points-analysis.md         # 18 studio bottlenecks
│   │   ├── market-research-saas-comparison.md # Monday / Linear / Notion: what to copy
│   │   └── context-discovery-log.md        # Early constraints summary
│   ├── architecture/
│   │   ├── architecture-v2-workspace-native.md # ★ Proposed v1 (Apps Script agent + Studio Brain)
│   │   ├── architecture-v1-plan.md         # Earlier blueprint (partly superseded)
│   │   ├── ai-models-and-bot-engines.md    # Models, Chat cards, costs (see review note)
│   │   └── information-architecture.md     # Dashboard IA + DB schema (later phase)
│   ├── design/
│   │   └── design-brief.md                 # ★ UI redesign brief: research refs, tokens, process
│   ├── sop/
│   │   └── communication-commandments.md   # The Spine + 11 Commandments
│   └── assets/scenario/                    # One-page scenario walkthrough (PDF/PNG/HTML)
│
├── flows/                        # Agent interaction flows (01–05 later features, 06–08 = v1)
├── prototypes/                   # HTML mock-ups (to be redesigned per design-brief)
├── samples/                      # 🔒 Local only (git-ignored): real resource sheet, vendor quotes, SOP docx
├── demo/python-agents/           # Early in-memory agent demo (reference only)
└── legacy/vendor-drive-main/     # Archived earlier vendor-search app
```

---

## ⚙️ Key Technical Decisions

> Updated 25 Sep 2026 for the no-Google-Cloud constraint. Earlier choices that no longer apply are ~~struck through~~.

| Component | Choice | Reason |
|---|---|---|
| **Runtime** | **Google Apps Script web app, "Execute as: user accessing"** | Runs as each person, so it reads their own inbox and writes their own sheet. No Cloud project, service account, or admin console. |
| **Source of truth (v1)** | **Studio Brain Google Sheet** (Clients, Projects, People, Email Examples) + each person's Resource Sheet | Zero infrastructure. ~~Postgres on Supabase~~ is deferred until the dashboard phase. |
| **Where people talk to it** | **BangOps web page** (bookmark) for chat and approvals, **Google Chat webhook cards** for notifications | A true two-way Chat bot needs a Cloud project. We can upgrade the same code later with a one-time link. |
| **AI Inference** | **Claude or Gemini API** via `UrlFetchApp`: a fast model for classification, a stronger one for client drafts | Realistic cost ~$5–30/month. ~~Groq Llama 3.1 / $1.50/mo~~ used outdated small models. |
| **Decision Routing** | Fast model structured output (TypeSafe Jev optional) | Jev needs an extra provider account. Keep it optional. |
| **Passwords / Keys** | **Excluded from Scope** | Avoids security liability and OTP friction. |
| **Language** | **100% English** | Clean standardized prompts across Design, Marketing, and Engineering. |

---

## 🤖 Daily Agent Cadence (Pomodoro & Micro-Check-ins)

1. **09:30 AM — Morning Attendance Check:**
   - Agent pings 1:1 on Google Chat: *"Good morning! Heading into the studio today?"*
   - *If Sick:* Empathetic follow-up, logs leave in personal resource sheet, alerts project teammates & founders.
   - *If Working:* Asks for key focus areas for the day.
2. **Midday — Focus Sprints & Pomodoro Tracking:**
   - 2–3 hour focus block notifications with interactive buttons (*"Done"*, *"+1 hr"*).
   - Automatically logs credits/hours.
3. **End of Day — Resource Sheet Write:**
   - Formats notes into professional line items matching the `[Project N, Hours N, Log N]` format in the employee's personal Google Sheet.
