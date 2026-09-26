# BangOps — Competitive Research: Who Is Already Solving This? (Sep 2026)

*Research done 25 Sep 2026, before picking a solution. The goal is to see what already exists, what it costs, and which option fits our hard constraints. The older [`market-research-saas-comparison.md`](market-research-saas-comparison.md) only looked at project-management tools (Monday, Linear, Notion). This doc covers the tools that actually target our problem: AI agents that watch email, draft replies, and fill in timesheets.*

---

## 1. The problem we're comparing against

The tools below are judged on the pain points you named, in priority order:

1. **Resource-sheet amnesia.** People forget to log work. We want the agent to already know what someone worked on.
2. **Client email awareness.** The agent should know when a client has emailed and help reply to it.
3. **SOP-quality drafting.** "I did X, want feedback." The agent works out the project and client, offers options, and drafts a Spine-compliant email. Then you copy it, or it sends after approval.
4. **Very simple for 20 people.** Something you download, a plugin, or a script on top of Google Workspace.

**Hard constraints:**
- Google Workspace only. **No Google Cloud Console project, no service account, no Admin Console work.**
- A human approves anything client-facing.
- Later we want to grow into a "team of bots", so today's choice shouldn't block that.

> **Why the no-GCP constraint matters so much:** almost every self-hosted tool that reads Gmail or writes Google Sheets needs an OAuth client, and an OAuth client lives in a Google Cloud project. That one constraint removes most self-hosted options unless we use one of three escape hatches: (a) a SaaS vendor's own already-verified Google app, (b) **Google Apps Script with its default project**, or (c) Google's own built-in AI (Gemini, Workspace Studio).

---

## 2. The landscape: six categories

### A. Google-native AI (you may already be paying for it)

| Product | What it does for us | Price | Fits no-GCP? |
|---|---|---|---|
| **Gemini in Gmail / Docs / Sheets** | Side-panel drafting and summarising inside Gmail. | Bundled in Business Standard ($14/user/mo annual) and above | ✅ Yes, nothing to set up |
| **Gems (custom Gemini assistants)** | A "Bang SOP Writer" Gem with the Commandments and a client directory attached as Drive files. It can be shared org-wide and **opened from the Gmail side panel**. | Included | ✅ Yes |
| **Google Workspace Studio (formerly Flows)** | No-code agents. Triggers: *new email arrives*, schedule, new Sheet row, calendar event. Actions: read/send Gmail, read/write Sheets, create Docs, **run a Gem**, call webhooks. | Included in Business Standard / Plus / Enterprise | ✅ Yes |

- **Strengths:** zero install, zero extra cost, and it already has permission to read the inbox. "New client email → summarise → suggest reply → notify" can be built in an afternoon.
- **Weaknesses:** Gemini-only. We have limited control over memory, and there's no durable "what did I do today" context. Studio is new, so quotas and edge cases aren't well documented. Community reports say Gems in the *side panel* sometimes can't see their knowledge files, so **this needs testing**. It has no idea what our resource sheet format is unless we teach it.
- **Verdict:** could be the cheapest win for pain points 2 and 3, **if your plan is Business Standard or above**. It doesn't fix pain point 1 on its own.

### B. AI email assistants (drafts in your voice)

| Product | Model | Price (per user/mo) | 20 users/mo | Notes |
|---|---|---|---|---|
| **Fyxer** | SaaS, Gmail/Outlook | $30 Starter / $50 Pro ($22.50 / $37.50 annual) | $450–1,000 | Learns your tone from past mail, drafts before you open, sorts the inbox, meeting notetaker. |
| **Superhuman** | SaaS email client | $25–40 | $500–800 | Premium email client; the good AI features are on the $40 tier. |
| **Shortwave** | SaaS Gmail client | $24–36 (Business / Premier, annual) | $480–720 | Strong AI search across your mail history. Free plan removed. |
| **Inbox Zero** | **Open source** (self-host) or hosted | Free self-hosted / $18 hosted | $0 + infra, or $360 | Triage, drafts in your voice, "who went quiet" tracking. Self-hosting needs your own Google OAuth client, which **means a GCP project**. |
| **Open-source Gmail Chrome extensions** (e.g. `vaeho/gmail-ai-extension`, `aiden-guan/gmail-intelligence`) | Browser extension, bring your own API key | Free + API tokens | ~$5–20 of API usage | They read Gmail from the page, **not through the API, so no GCP needed**. They break when Gmail changes its page layout. Mostly hobby-grade. |

- **Strengths:** drafting quality is excellent. "Who went quiet" tracking maps directly to Commandment 1 ("never go dark").
- **Weaknesses:** none of them know our **projects, credits, owners, or the Spine**. They learn *your* voice, not the studio's SOP. None of them touch the resource sheet. The paid ones cost $450–1,000/mo for 20 people.
- **Verdict:** good ideas to copy (pre-drafted replies, "gone quiet" alerts), but none is a complete answer.

### C. Automatic time tracking (the "it should know what I worked on" category)

| Product | How it knows | Price (per user/mo) | 20 users/mo |
|---|---|---|---|
| **Timely** (Memory + AutoSheet) | A desktop tracker records apps, sites and docs. AI drafts a timesheet for one-click approval. | $9–22 annual ($11–28 monthly) | $180–560 |
| **Rize** | A background tracker assigns time to client/project from window titles and URLs. **No approval step.** | $29.99/seat (Team) | ~$600 |
| **Memtime** | Local activity timeline you drag into a timesheet. | ~€10–20 | $200–400 |

- **Strengths:** this is the only category that truly fixes "people forget." Timely's *draft, then human approves* model is the right pattern.
- **Weaknesses:** it's desktop monitoring. [`qa-interview-log.md` Q30](qa-interview-log.md) already flagged that surveillance kills trust and doesn't work for off-screen work (sketching, handling physical prototypes, vendor visits). It categorises by *app* (SolidWorks: 2h), not by the *story* a client wants to read ("Added NFC + face-unlock clips"). It doesn't write into our `[Project, Hours, Log]` Google Sheet format.
- **Verdict:** copy the idea (**draft the timesheet from signals, human approves**) but use gentler signals: chat messages, sent emails, calendar, Drive file activity. No screen or app tracking.

### D. Agency operations platforms (PSA: replace the resource sheet entirely)

| Product | Price (per user/mo) | 20 users/mo | Notes |
|---|---|---|---|
| **Productive.io** | $9 Essential / $24 Professional / custom | $180–480+ | The most agency-native option, with growing AI features. Covers time, budgets, and resourcing. |
| **Scoro** | ~$20–50 | $400–1,000 | Deep finance and reporting. |
| **Float / Runn** | ~$7–12 | $140–240 | Capacity planning only. |

- **Verdict:** these solve credit accounting properly but bring back the **Monday.com problem**: a heavy tool nobody opens ([Q21](qa-interview-log.md)). They're worth knowing about as a *later* reporting layer. They're not the input method.

### E. Hosted AI agent platforms (build your own agent on someone else's infrastructure)

| Product | Price (per seat/mo) | 20 users/mo | Google access | Fits no-GCP? |
|---|---|---|---|---|
| **Claude Team** (Anthropic) | $20 annual / $25 monthly (standard seat). Premium $100/$125 | $400–500 | Gmail, Drive and Calendar connectors. **Shared Projects** (upload the SOP, client list and past emails once, and everyone uses them). Org-wide skills. | ✅ Each user connects with Anthropic's app. An admin *may* need to allow it if third-party apps are restricted. |
| **Dust** | Free seat; Pro $24–30; Max $120–150 (credit-based) | $0–600 | Drive, Gmail (via connectors), MCP | ✅ Same as above |
| **Lindy** | $29.99 (3k credits) → $199.99 | $600+ and credits burn quickly | Gmail, Calendar, hundreds of apps | ✅ Same as above |

- **Strengths:** you can have something working within days. The model quality is the best available. The "shared project with SOP + client context" pattern is **exactly what pain point 3 needs**.
- **Weaknesses:** per-seat pricing grows with headcount. The agent can *draft* emails, but automatically writing structured rows into each person's resource sheet is awkward. It's a general assistant, not a studio workflow. Credit-metered plans (Dust, Lindy) make costs unpredictable.

### F. Open-source agent frameworks (self-hosted, e.g. on the office Raspberry Pi)

| Project | License / maturity | What it is | Fits us? |
|---|---|---|---|
| **OpenClaw** | MIT, non-profit foundation, very popular (~68k★) | A personal agent that lives in your chat app (WhatsApp, Telegram, Slack, **Google Chat**, Teams…). It has memory, runs tools and shell commands, and handles Gmail workflows. | ❌ **Its Google Chat channel needs a GCP project, a service account JSON key, and a public HTTPS endpoint**, which breaks our constraint. It's also powerful (shell access), so it's risky to hand to 20 non-technical people. |
| **Hermes Agent** (Nous Research) | MIT, active | An agent with persistent memory, self-created "skills", scheduling, and a messaging gateway for 20+ platforms (Telegram, Slack, WhatsApp, Email, Signal…). Desktop app for macOS/Windows. | ⚠️ Great "brain" for a later team of bots. Google Chat isn't a first-class channel, and Gmail/Sheets access still needs an OAuth client (GCP). |
| **Mia Multiplayer** ([the repo you linked](https://github.com/luislozanogmia/miamultiplayer)) | MIT, **4★, early**, Electron desktop app | Humans → private **Agents** (full access: files, memory) → shareable **Bots** (restricted). Wraps Hermes Agent plus browser automation. Two modes: Managed (their budget-capped model) or Standalone (your own OpenRouter/Anthropic/OpenAI key). | ⚠️ **The concept is exactly our long-term vision** (a personal agent per person, and shared bots for the team). But it only ships for **macOS (Apple silicon) and Ubuntu, with no Windows build**, it's very early, and it has no Google Workspace integration. **Copy the model; don't adopt the code.** |
| **n8n** (+ community "n8nClaw") | Fair-code (not OSI), mature, self-host | A visual workflow builder with Gmail, Sheets and Google Chat nodes plus AI agent nodes. | ⚠️ Excellent for visible, predictable automations, but the Google nodes need an OAuth client, which **means a GCP project**. |

---

## 3. Head-to-head against our four pain points

✅ = solves it well · ⚠️ = partly · ❌ = no

| Option | 1. Knows what I worked on | 2. Watches client email | 3. SOP drafts with project context | 4. Simple, no GCP | Cost for 20/mo |
|---|---|---|---|---|---|
| Gemini + Gems + Workspace Studio | ❌ | ✅ | ⚠️ (Gem holds SOP; project context is manual) | ✅ | **$0 extra** (if Standard+) |
| Fyxer / Superhuman / Shortwave | ❌ | ✅ | ⚠️ (your voice, not our SOP) | ✅ | $450–1,000 |
| Timely / Rize | ✅ (via monitoring) | ❌ | ❌ | ⚠️ (desktop install) | $180–600 |
| Productive / Scoro | ⚠️ (manual entry, better UI) | ❌ | ❌ | ⚠️ (heavy) | $180–1,000 |
| Claude Team / Dust | ⚠️ (if you tell it) | ✅ (connector) | ✅ (shared project) | ✅ | $400–600 |
| OpenClaw / Hermes / n8n (self-host) | ⚠️ | ✅ | ✅ | ❌ (needs GCP) | ~$10–40 API |
| Mia Multiplayer | ⚠️ | ❌ | ⚠️ | ❌ (no Windows) | API only |
| **Custom build on Apps Script** (see §5) | ✅ (chat log + sent mail + calendar → draft rows) | ✅ | ✅ | ✅ | **~$5–30 API** |

**What this shows:** no single product covers all four. Every product that does 2 and 3 well ignores 1. The one that does 1 relies on monitoring. The self-hosted options that could do all three hit the GCP wall.

---

## 4. What's worth copying from each

| From | Copy this |
|---|---|
| Timely AutoSheet | **Draft the timesheet, human approves.** Never ask people to type logs from scratch. |
| Fyxer / Inbox Zero | Replies **already drafted** before you open the email. A **"gone quiet"** tracker (who's waiting on us). |
| Claude Projects / Gems | One **shared studio brain** (SOP + client directory + tone examples) used by every personal agent. |
| Workspace Studio | Trigger on "new email from a client domain" with **no infrastructure**. |
| Mia / Hermes | Two tiers: **private Agent per person** (full context) and **shared Bots** (restricted, team-wide). Agents that learn "skills" over time. |
| Productive | Credits burned vs. package as a first-class number, founder-only. |

---

## 5. The feasible paths, given no GCP (options, not a decision yet)

| Path | What it looks like | Build effort | Running cost | Main risk |
|---|---|---|---|---|
| **P1: Configure, don't build** | A shared **Gem** or **Claude Project** holding SOP + client directory + resource-sheet format, plus a **Workspace Studio flow** on new client email. Timesheet logging is still semi-manual. | 1–3 days | $0 (Gemini) or ~$400–500 (Claude Team) | Doesn't fully fix resource-sheet amnesia. Tied to the vendor's features. |
| **P2: Custom Workspace-native app** | One **Google Apps Script web app** ("BangOps"), opened via a bookmark link and running *as each user*: a chat box where you type "did X on STC", it detects the project, writes your resource-sheet row, offers email options, and creates a **Gmail draft** (send on approval). Time triggers watch your inbox. Notifications go to Google Chat through the incoming webhooks we already use. Brain = the Claude or Gemini API via `UrlFetchApp`. **No GCP, no service account, no admin console.** | 2–4 weeks for v1 | ~$5–30/mo API | Apps Script quotas (6-min runs, trigger limits). The UI is a web page, not a native Google Chat bot. A real two-way Chat bot needs a GCP project. |
| **P3: Open-source agent host** | Hermes/OpenClaw on the Pi, reached over Telegram/WhatsApp. | 1–2 weeks + ongoing ops | ~$10–40/mo API | **Breaks the no-GCP rule** for Gmail/Sheets. Security of a shell-capable agent. Adds another chat app. |
| **P1 → P2 hybrid** | Use P1 *now* for email drafting (this week) while P2 is built for timesheets and inbox awareness. Later, move P2's brain to a server (Hermes-style) for the team of bots. | — | — | Two systems running for a few weeks. |

> ⚠️ **Things to prove in a 1-day spike before committing to P2:** (1) a domain-shared Apps Script web app set to *"Execute as: user accessing"* can read that user's Gmail and write their Sheet without GCP; (2) whether users see an "unverified app" screen; (3) whether time-driven triggers created per user survive, and how many run per day; (4) whether a Gem opened from the Gmail side panel actually reads its Drive knowledge files.

---

## Sources

- Mia Multiplayer: https://github.com/luislozanogmia/miamultiplayer
- OpenClaw: https://openclaw.ai/ · Google Chat channel requirements: https://docs.openclaw.ai/channels/googlechat · https://www.stack-junkie.com/blog/openclaw-google-chat-setup-guide
- Hermes Agent: https://github.com/nousresearch/hermes-agent · https://hermes-agent.nousresearch.com/docs/
- n8n self-hosted assistant template: https://n8n.io/workflows/13717-run-a-self-hosted-multi-channel-ai-assistant-with-claude-gemini-and-gmail/
- Inbox Zero: https://www.getinboxzero.com/ · https://openalternative.co/inboxzero
- Fyxer pricing: https://gmelius.com/blog/fyxer-ai-review · https://get-alfred.ai/blog/fyxer-pricing
- Superhuman vs Shortwave: https://zapier.com/blog/shortwave-vs-superhuman/ · https://aitoolpick.org/blog/superhuman-pricing-2026/
- Timely: https://www.capterra.com/p/131584/Timely/ · https://aiproductivity.ai/tools/timely/
- Rize: https://rize.io/teams · https://rize.io/solutions/agencies
- Productive / Scoro / Float: https://noloco.io/blog/productive-vs-scoro · https://www.agencyhandy.com/client-portal/productive-io-pricing/
- Claude Team: https://support.claude.com/en/articles/9266767-what-is-the-team-plan · https://justinmckelvey.com/blog/claude-team-plan
- Dust: https://dust.tt/home/pricing
- Lindy: https://www.nocode.mba/articles/lindy-ai-pricing
- Google Workspace / Gemini pricing: https://workspace.google.com/pricing · https://www.eesel.ai/blog/gemini-workspace-pricing
- Workspace Studio: https://workspaceupdates.googleblog.com/2025/12/workspace-studio.html · https://www.itgenius.com/blog/google-workspace-studio-ai-agents/
- Gems sharing / side panel / in Studio: https://workspaceupdates.googleblog.com/2025/09/gem-sharing-gemini-app-workspace.html · https://workspaceupdates.googleblog.com/2025/07/gems-in-the-side-panel-of-google-workspace-apps.html · https://workspaceupdates.googleblog.com/2026/04/use-your-gems-in-your-google-workspace-studio-flows.html
- Apps Script and Cloud projects: https://developers.google.com/apps-script/advanced/chat · https://developers.google.com/apps-script/add-ons/how-tos/publish-add-on-overview
- Gmail AI extensions (open source): https://github.com/vaeho/gmail-ai-extension · https://github.com/aiden-guan/gmail-intelligence

*Prices are list prices found in Sep 2026 and change often. Check them before buying.*
