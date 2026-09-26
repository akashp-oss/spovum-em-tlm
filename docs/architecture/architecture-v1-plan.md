# Operations Hub — Plan & Architecture (v1)

> ⚠️ **Partly superseded (25 Sep 2026)** by [`architecture-v2-workspace-native.md`](architecture-v2-workspace-native.md). No longer valid: Telegram as the primary surface, Bitwarden / Room 4 "Stack" (passwords dropped, Q7), multi-language (English only, Q9), and anything that assumes a service account or Google Cloud project. Still useful: the data-model thinking, the nudge-budget and "work facts only" rules, the soul.md idea, and the risks list.

**Goal:** One front door for projects, clients, owners, drive links, vendors, software & key ownership — kept up to date by personal agents that talk to people where they already chat.

**Hard rule for this project:** nothing goes on the dashboard unless it answers a question someone actually asked. One font. One accent colour. No decorative cards, no charts that nobody reads, no "insights" panel. Every field below has a named reason for existing.

---

## 1. The stack (what we use vs what we build)

| Layer | Choice | Why |
|---|---|---|
| Secrets (passwords, API keys) | **Bitwarden Teams** (or self-hosted Vaultwarden) | Never store secrets in our own DB. Dashboard stores *metadata only* — key name, owner, what it's used for, last rotated — plus a deep link to the vault item. |
| Database (source of truth) | **Postgres** (managed: Supabase/Neon free tier) | Real relations, real backups, real auth. Not Excel, not a file on someone's laptop. |
| Dashboard | **Custom, built by us** — Next.js + Tailwind, read-mostly | This is where we win. Small, opinionated, 4 screens max. |
| Agent runtime | **n8n** (self-hosted) for workflows + a small Python service for the agent loop | n8n gives non-devs visibility into what agents do. Python for anything n8n makes ugly. |
| Chat surface | **Telegram** (primary) or **Google Chat** (if we're on Workspace) | See §4 — WhatsApp is a trap. |
| Models | **Jev** for decisions, **Gemini Flash / Llama-3.1-8B via Groq** for text, **Gemini Flash** for translation | See §5. |
| Hosting | Pi = agents, n8n, cron. **DB = managed cloud, not the Pi.** | See §6. |

**Build vs buy verdict:** buy the vault, buy the database, build the dashboard and the agents. Do not build auth, file storage, or a chat client.

---

## 2. The data model (this IS the product)

Six tables. Nothing else in v1.

**people** — id, name, team (industrial / marketing / engineering), preferred_language, weekly_hours, telegram_id, status (active/on_leave), soul_path

**projects** — id, name, client_id, owner_id, sub_owner_id, status (not_started / active / blocked / waiting_on_vendor / done), health (green/amber/red), drive_link, deadline, last_update_at
> `last_update_at` is the most important column in the system. It is how we know a project is being neglected without anyone reporting it.

**clients** — id, name, primary_contact, notes

**vendors** — id, name, category (tags: sheet metal, injection moulding, PCB, printing…), city, typical_lead_time_days, price_band (cheap / mid / premium), quality_rating (1-5), last_used_at, last_used_by, notes, contact
> `price_band × quality_rating` is the whole point. That's the "cheap but good" vs "expensive but good" question, answerable in one filter.

**software** — id, name, what_it_does, owner_id, who_has_access, cost_per_month, renewal_date, vault_item_link
> Also covers API keys. `vault_item_link` points at Bitwarden. No secret values ever live here.

**updates** — id, person_id, project_id, type (progress / blocker / leave / vendor_note), text_original, text_english, created_at, source (agent/manual)
> Append-only log. Everything an agent learns lands here first. The dashboard reads from here.

---

## 3. The dashboard — exactly four screens

### Room 1: Today (the only screen most people open)
Three blocks, top to bottom:
1. **Who's out today** — names + return date. Nothing more.
2. **My projects** — name, status chip, deadline, days since last update. Click = detail.
3. **Needs attention** — projects red or untouched >7 days, and any unanswered blocker. Empty state is the goal.

That's it. No charts. No welcome message. No activity feed.

### Room 2: Projects
A table: name, client, owner, sub-owner, status, deadline, last update. Filter by team/owner/status. Row click opens detail: drive link, the update log, who's on it.

### Room 3: Vendors
Search + filters (category, city, price band, min quality). Results as rows: name, category, price band, quality, lead time, last used by. Row click: contact, notes, past projects.

### Room 4: Stack
Software + API keys table: name, what it does, owner, cost, renewal date, "Open in vault" button. Sortable by renewal date so nothing auto-renews unnoticed.

**No screen 5.** No settings page, no admin panel, no analytics in v1.

---

## 4. Chat surface — the WhatsApp question, answered honestly

**Do not build on WhatsApp.** Two options, both bad:
- *Unofficial libraries* (Baileys, whatsapp-web.js) — reverse-engineered WhatsApp Web. Violates ToS, non-deterministic ban risk, and the number that gets banned is somebody's real phone number. Documented, common, and it fails overnight with no recourse.
- *Official Cloud API* — legitimate, but: business-initiated messages are paid templates that must be pre-approved, and outside the 24-hour customer service window the agent literally cannot start a conversation. A proactive nudge bot is the exact use case WhatsApp charges for and restricts. Also: E2E encryption is gone on the Cloud API anyway, so the privacy argument for WhatsApp doesn't hold.

**Recommendation: Telegram.** Free, unlimited proactive messages, bots are first-class, inline keyboards + multi-select via callback buttons, file upload, voice notes (which matters for the language gap), and a 20-minute setup. The cost is asking people to install one app.

**Alternative: Google Chat** — pick this *if* the office already runs Google Workspace. It gives us genuinely generated UI: Card v2 with `selectionInput` (dropdown, radio, checkbox, MULTI_SELECT), `textInput`, `dateTimePicker`, and modal dialogs — so onboarding becomes a form, not an interrogation. Lives inside a tool people already have open. Weaker on mobile push, and non-Workspace people can't be reached.

**Decision rule:** Workspace org → Google Chat. Otherwise → Telegram.

---

## 5. Models

**Jev (TypeSafe, System One)** — structured decisions, ~100ms, $0.042/M in, output free. Use it as a smart `if`:
- "Is this message a leave request / blocker / progress update / vendor note?" → route
- "How urgent is this, 0-10?" → escalate to founder or not
- "Does this project look at risk given these signals?" → run hourly over every project, costs pennies
- "Does this text contain a credential?" → guardrail before any write
- Confidence scores decide auto-write vs ask-to-confirm.

**Generative model** (Gemini Flash / Llama-3.1-8B on Groq / Mistral Small) — only when someone actually needs prose, a PPT, an email, or a translation. Cheap tier is fine.

**Split logic:** Jev handles the thousands of tiny classifications. The expensive model runs maybe 20 times a day. Est. **$20-60/month total** for ~20 people.

---

## 6. Memory — where it lives, honestly

**Local files per person: no.** Sounds nice, fails fast — no backup, no sync, dies with a laptop, and the master agent can't read it. Asking people to paste a storage path is asking a non-technical person to make an infrastructure decision.

**Pi as the only home: also no.** Single device, office power, home internet, SD card corruption. That's a new single point of failure replacing the Excel file.

**Recommendation — two layers:**

1. **Structured memory → Postgres (managed cloud).** Every fact the agents know: people, projects, updates, vendors. Queryable, backed up, survives hardware. This is the real memory.
2. **`soul.md` per person → a private git repo, one file per person, synced to the Pi.** Version-controlled means we can see how someone's profile drifted and roll back a bad edit. Plain markdown means the person can read and correct their own file — which is the trust mechanism.

**The Pi's actual job:** run n8n, run the agent loop, run cron jobs, hold a local cache. If it dies we reflash it in an hour and lose nothing. Requirements: boot from SSD not SD card, Cloudflare Tunnel for inbound webhooks, nightly DB dump off-site.

### `soul.md` shape (this is the personalisation)

```markdown
# Akash — soul.md
## Identity
name: Akash Pai
team: industrial design
languages: English, Kannada        # agent speaks to them in these
role_in_one_line: ...

## Working style
hours_per_week: 40
peak_hours: 10:00-14:00            # agent never pings outside these
nudge_tolerance: low               # low | medium | high
prefers: short messages, no small talk

## Current context
active_projects: [P-102, P-117]
credit_budget_this_month: 30
reports_blockers_to: @founder

## Learned (agent-written, append-only)
- Responds to voice notes faster than text
- Always late on vendor follow-ups — ask on Mondays
- Hates being asked for status on Fridays
```

Two sections are human-written (Identity, Working style), one is agent-written (Learned). The person can open and edit their own file at any time. That transparency is what stops this from feeling like surveillance.

---

## 7. Agent architecture

```
 Telegram / Google Chat
        ↕
 Personal Agent  (one process, N soul.md files loaded by user id)
   - reads soul.md for tone, language, nudge frequency
   - Jev classifies incoming message → type + confidence
   - high confidence: write to `updates`, confirm briefly
   - low confidence: ask one clarifying question
   - does small tasks: draft mail, make PPT/XLSX, translate
        ↓  structured writes only
 Master / HR Agent  (scheduled, no chat surface)
   - rolls up `updates` into project health
   - detects: nobody updated P-117 in 9 days → nudge owner
   - detects: 3 people out Thursday → tell the teams
   - writes the daily digest, posts to team channels
        ↓
 Postgres  ← single source of truth
        ↓  read-only
 Dashboard
```

**Non-negotiable rules:**
- Agents write to `updates` only. They never edit `projects` directly; the master agent derives project state from updates.
- Nothing is written without either high Jev confidence or an explicit user confirmation.
- The personal agent reports *work facts* upward. It never reports behaviour, timing, or sentiment. Written into the prompt and into the soul.md contract.
- Nudge budget: max 2 proactive messages per person per day, and only when there's a concrete reason ("the vendor quote was due yesterday"), never "how's it going?".

---

## 8. Onboarding (must take under 5 minutes)

Not a questionnaire. A guided card flow — multi-select and buttons, almost no typing:
1. "Hi, I'm your assistant. What should I call you?" → text
2. "Which team?" → 3 buttons
3. "Which languages should I talk to you in?" → multi-select
4. "When are you usually working?" → 4 time-block buttons
5. "How often should I check in?" → Rarely / Only when something's due / Daily
6. "Pick the projects you're on" → multi-select from existing projects
7. Done. Everything else the agent learns by watching, and appends to `Learned`.

Then it immediately does something useful — shows their projects — so the first interaction has a payoff.

---

## 9. Rollout order

| Phase | What | Why first |
|---|---|---|
| 0 | Bitwarden rollout, all passwords + keys in | Highest risk, cheapest fix, one afternoon |
| 1 | Postgres + the 6 tables, seeded from existing Excel by hand | Nothing works without truth |
| 2 | Dashboard Room 1 + Room 2 (Today, Projects), read-only | Value visible immediately |
| 3 | Telegram bot: leave + status updates only | Solves the sick-day problem, smallest possible agent |
| 4 | Room 3 Vendors + vendor search | The industrial/engineering unlock |
| 5 | Master agent: digest + stale-project nudges | Now the data stays fresh on its own |
| 6 | Room 4 Stack, agent side-tasks (PPT/mail/XLSX) | Nice-to-have, not load-bearing |

---

## 10. Risks

1. **Nagging kills it.** Daily "what's your progress?" → people auto-reply "same" → data is confidently wrong, worse than empty. Mitigated by the nudge budget and reason-required rule.
2. **Surveillance perception**, especially for the engineering team who already feel out of the loop. Mitigated by readable soul.md + the "work facts only" rule. Get this wrong and adoption is zero.
3. **Sick people don't open chat apps.** Leave must be loggable by a teammate on someone's behalf, and broadcast automatically.
4. **Pi single point of failure.** Mitigated by DB living off the Pi.
5. **Agent hallucinating into the DB.** Mitigated by propose → confirm → write.
6. **Excel migration is manual and boring.** Someone has to sit down and clean the vendor sheet once. No tool fixes this. Budget a day.
7. **Credit system.** Not modelled in v1 on purpose — it encodes human judgement and needs to be agreed on paper before software touches it.

---

## 11. Open questions (blocking)

1. Is the office on Google Workspace? → decides Telegram vs Google Chat.
2. How does the credit system actually work — what is a credit, who allocates it, what's on a resource sheet?
3. Roughly how many vendors, and what columns does that sheet have today?
4. Two or three real examples of a vendor question someone asks out loud.
5. Who builds this — you alone, or is there engineering time available?
