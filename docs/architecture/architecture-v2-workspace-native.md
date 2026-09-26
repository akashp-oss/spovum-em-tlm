# BangOps — Architecture v2: Workspace-Native Personal Agent

*Proposed 25 Sep 2026. Supersedes the conflicting parts of [`architecture-plan.md`](architecture-v1-plan.md) (Telegram, Bitwarden, service accounts, multi-language). Based on [`competitive-research-2026.md`](../research/competitive-research-2026.md) path **P2**, with P1 as an optional quick win.*

---

## 0. Why this shape

| Constraint / answer | Consequence |
|---|---|
| Google Workspace only. We *have* Cloud/Admin access but **want to avoid it** | Build on **Google Apps Script with its default project**. No service account, no OAuth client, no Cloud Console |
| Client emails arrive in **each person's own inbox** | The agent must run **as each person**, reading only their own mail. Apps Script web apps set to *"Execute as: user accessing"* do exactly this |
| "Whatever is simple and best" for where people talk to it | A **bookmarked BangOps page** (chat box + review panels). **Notifications go to Google Chat** through webhooks, which we've already proven work |
| Must stay very simple | Onboarding = open a link, click *Allow*, paste two links. Nothing to install |
| Later: a team of bots | Personal agents (run as the user) + shared bots (run as a studio account), with one shared "Studio Brain". This mirrors the Mia/Hermes Agents → Bots model |

**Upgrade path, kept open on purpose:** the same Apps Script project can later become a **real two-way Google Chat bot** by linking it to a standard Cloud project once (~10 min). Nothing we build now gets thrown away.

---

## 1. The pieces

```
                ┌───────────────────────────── Studio Brain (1 Google Sheet, founder-owned, read by all) ─┐
                │  Clients · Projects · People · Email Examples · SOP link                                 │
                └──────────────▲──────────────────────────────▲───────────────────────────────────────────┘
                               │ read                         │ read
 ┌─────────────────────────────┴───────────┐     ┌────────────┴───────────────────────────┐
 │ BangOps Web App  (Apps Script)          │     │ Shared bots (Apps Script, run as        │
 │ Execute as: USER ACCESSING              │     │ studio account, later)                  │
 │  • Chat box  "did X on STC, want fb"    │     │  • daily digest to team space           │
 │  • Today: drafted resource-log rows     │     │  • "gone quiet" watchdog (from CC/labels)│
 │  • Inbox: client mails needing reply    │     │  • vendor lookup                        │
 └──┬──────────┬───────────┬──────────┬────┘     └─────────────────────────────────────────┘
    │GmailApp  │Spreadsheet│Calendar  │UrlFetchApp
    ▼          ▼  App      ▼  App     ▼
 user's     user's own   user's    LLM API (Claude / Gemini)
 inbox      Resource     calendar   key in Script Properties
 (drafts,   Sheet
  send on   (existing
  approval) format)
    │
    └── per-user time triggers (inbox scan, evening log draft) ──► user's private Google Chat space (incoming webhook)
                                                                  card: "Client X replied — Review in BangOps"
```

### 1.1 Studio Brain (the #1 missing asset, build it first)
One Google Sheet that everybody can read and founders/leads can edit. It replaces the flat `DD_Helper` list.

| Tab | Columns | Why |
|---|---|---|
| **Clients** | client_code (`STC`), legal name, **email domains** (`stc.com.sa`), key contacts (name, email, role), tone notes ("formal, CEO reads everything"), package / credits *(founder-only view later)* | Lets the agent tell that an email or a note is about STC |
| **Projects** | project_code (`STC: BPillar`), client_code, owner email, sub-owner email, status, drive link, keywords ("b pillar, door cap, nfc") | Maps "worked on the door cap" to `STC: BPillar` |
| **People** | email, name, team, role, resource-sheet URL | Owners, CC suggestions, Commandment 11 (coordinate before promising) |
| **Email Examples** | client_code, situation (update / file follow-up / scope change / delay), subject, body, rating | Few-shot examples, so drafts sound like *Bang*, not like a chatbot |
| **SOP** | link to the Commandments doc + version | Single source for the Spine and the 11 Commandments |

### 1.2 BangOps Web App (the personal agent)
- Deployed from one Apps Script project: **Execute as → User accessing the web app**, **Who has access → Anyone within bangid.com**.
- Each person opens `https://script.google.com/a/macros/bangid.com/s/…/exec` (bookmark it), clicks **Allow** once, and pastes (a) their Resource Sheet link and (b) their personal Chat space webhook.
- It has three panels on one page:
  1. **Chat.** Free text: "Finished door cap + NFC clips, 2.5h, want client feedback on clip placement."
  2. **Today.** Drafted resource-sheet rows. Tick to approve, and they're written into the correct month tab / date row / next empty `[Project, Hours, Log]` triplet.
  3. **Inbox.** Client threads waiting on you, each with a summary, what the client is asking for, and **reply options**.
- Per-user settings live in `PropertiesService.getUserProperties()`.

### 1.3 Signals, not surveillance
The agent drafts the timesheet from things that already exist. It **never uses screenshots, app tracking, or keystrokes**:
- what you told it in the chat box (primary),
- emails you **sent** today to client domains (Gmail search `in:sent after:today`),
- calendar events with client names or domains,
- *(optional, later)* Drive files you edited today in project folders.

Then it asks you to approve. **Nothing goes into the sheet without a tick.** (This is Timely's AutoSheet pattern without the desktop tracker.)

### 1.4 Brain (LLM)
- Called through `UrlFetchApp`. The API key is stored in **Script Properties**: users of the web app can't see it, only editors of the script can.
- Two tiers: a small fast model for classification (which project? is this email an ask, an FYI, or a scope change?) and a stronger model for client-facing drafts. Current Anthropic options: **Claude Haiku 4.5** (fast) and **Claude Sonnet 5** (drafts), or Gemini equivalents. The provider is behind one function, so it can be swapped.
- **Realistic cost:** 20 people × (~10 classifications + ~3 drafts per day) ≈ **$5–30/month**. Measure it in the pilot.
- Privacy: client email text is sent to the model provider. Use a commercial API with no training on our data, and send the minimum (the latest message plus a short thread summary, not the whole history).

### 1.5 Notifications
Apps Script can't DM people in Chat without a Chat app, so each person creates **one private space** ("BangOps · Akash"), adds an **incoming webhook** (Space → Apps & integrations → Webhooks), and pastes the URL during onboarding. Cards contain an **"Open in BangOps"** button that deep-links to the right item (`…/exec?item=<id>`). All two-way interaction happens on the web page.

### 1.6 Sending
- **Copy** button: always available.
- **Create draft**: `GmailApp` creates a draft *in the same thread*, addressed to the right contacts, with suggested CCs (Commandment 11). You review it in Gmail.
- **Send on approval**: one button, which sends the draft. Never automatic.

---

## 2. Core flows (v1)

| # | Flow | File |
|---|---|---|
| 06 | "I did X, want feedback" → detect project → options → draft → approve/copy/send | [`flows/06-work-note-to-client-email.md`](../../flows/06-work-note-to-client-email.md) |
| 07 | Client emails you → summary + asks → Chat ping → reply options → draft | [`flows/07-inbound-client-email.md`](../../flows/07-inbound-client-email.md) |
| 08 | End of day → rows drafted from signals → approve → written to Resource Sheet | [`flows/08-auto-drafted-resource-log.md`](../../flows/08-auto-drafted-resource-log.md) |

Flows 01–05 stay valid as *later* features. Their "service account" and "bot DM" parts should be read as "webhook card + web app".

---

## 3. Build order

| Step | What | Done when |
|---|---|---|
| **0. Spike (1 day)** | A tiny web app, run as the accessing user by 2 colleagues: reads their Gmail, writes their Sheet, calls the LLM, installs a trigger, posts to their webhook | Checks: no "unverified app" wall; triggers fire; runtime OK |
| **0b. Quick win (optional, same week)** | If our plan includes Gemini: a shared **"Bang SOP Writer" Gem** with the Commandments + Studio Brain attached, usable from Gmail's side panel | Team can draft Spine emails today while v1 is being built |
| **1. Studio Brain** | Fill Clients / Projects / People for active accounts; collect 10–20 good past emails | Every active project has domains, owner, keywords |
| **2. Flow 06** | Chat → project detection → options → draft → copy / Gmail draft | 3 pilot users use it for real client mail for a week |
| **3. Flow 08** | Evening draft of resource rows → approve → write to sheet | Pilot users stop filling the sheet by hand |
| **4. Flow 07** | Inbox trigger for client domains → Chat card → reply options | No client mail waits >1 working day unseen |
| **5. Roll out to 20** | Onboarding page + a 2-minute Loom | ≥80% weekly active after 3 weeks |
| **Later** | Morning check-in + sick failover (01/02), "gone quiet" watchdog, vendor bot (04), founder credits view, optional upgrade to native Chat bot or a server-hosted brain | — |

---

## 4. Known limits (be honest)

- **Apps Script quotas.** 6 minutes per execution; per-user caps on trigger runtime and URL fetches (Workspace limits are much higher than consumer ones). Inbox scans must be incremental (only new threads since the last run). *Verify exact numbers in the spike.*
- **Not a chat app.** Replies happen on a web page, not inside Google Chat. If the team finds that annoying, do the one-time Cloud link (§0) to turn the same code into a Chat bot.
- **Per-user onboarding is required** because mail is per-user. That's about 2 minutes each; there's no admin-level alternative without domain-wide delegation, which we're avoiding.
- **Resource sheets vary.** People may have edited their copies. The writer must look up headers by name, not fixed column numbers.
- **The SOP is v0.9 (a draft).** The agent follows whatever version is linked in the Studio Brain.

---

## 5. Open decisions

1. LLM provider for v1 (Claude vs Gemini API). The recommendation is to start with one and keep the swap point.
2. Workspace plan tier (decides whether step 0b is free).
3. Who owns the Studio Brain upkeep. **A project doesn't exist until a founder adds it there.**
4. Do we log time only from approved rows, or also track "unapproved drafts" as a nudge metric?
5. Privacy contract wording, to be shared with the team *before* rollout (see §1.3–1.4).
