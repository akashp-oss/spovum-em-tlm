# Bang Design Operations & Agent — Q&A Interview Log

*Living record of every question asked, the raw and rephrased user answers, decisions, and system specifications.*

---

### Q1: Team Size
- **Question:** Roughly how many total team members across Industrial Design, Marketing, and Engineering will be using this system?
- **User Answer:** Around 20.
- **Key Decision / Takeaway:** Small, nimble team (~20 people). No need for bloated enterprise software; low-overhead architecture will succeed.

---

### Q2: Primary Chat Surface
- **Question:** Where does your team do most of their day-to-day chatting right now (e.g., WhatsApp, Slack, Teams, Telegram, Discord)?
- **User Answer:** Most of them use WhatsApp and Google Chat.
- **Key Decision / Takeaway:** Team already works across WhatsApp and Google Chat.

---

### Q3: Credit-Based System
- **Question:** Could you briefly explain how your "credit-based system" works for allocating people across projects?
- **User Answer:** Subscription model for design ([bangid.com/plans](https://bangid.com/plans/)). Packages bundle UI/UX, product design, industrial design, and engineering into credits. On average, **1 hour = 1 credit**. Each team member tracks their hours on their own resource sheet.
- **Key Decision / Takeaway:** Time accounting is directly tied to client revenue (1 credit = 1 hour). Precision in logging work deliverables without employee friction is essential.

---

### Q4: Google Workspace Infrastructure
- **Question:** Is your Google Chat tied to a paid Google Workspace domain (e.g. `@bangid.com`) where every single team member has an active company account?
- **User Answer:** Yes.
- **Key Decision / Takeaway:** Unlocks native Google Chat API integration. Google Chat has **zero API cost**, allows interactive Card v2 UI (buttons, forms, timer triggers), and requires zero new app installations for team members.

---

### Q5: Vendor Sourcing & Quoting Complexity
- **Question:** Roughly how many vendors are currently in your Excel sheet, and what are the main materials or fabrication processes you use them for?
- **User Answer / Sample Provided:** Provided sample spreadsheet `3D_Print_Vendors_Quote_Comparison.xlsx`. There are many vendors (e.g., SLA ABS 3D printing across Design Roots, Makenica, 3DE Tech, BOTAAT). High complexity with part-by-part quotes, lead times, and massive price spreads on specific components. Need a fast search/filter way instead of reading dense spreadsheets.
- **Key Decision / Takeaway:** Vendor lookup tool must filter by Process / Material / Price Band / Quality Rating / Lead Time, surface part-specific cost drivers, and link to past quotes.

---

### Q6: Senior & Founder Bottleneck on Vendors
- **Question:** When an industrial designer or engineer needs a quote or fabrication today, do they usually just ask a senior colleague verbally/on WhatsApp to recommend someone, or does each person hunt on their own?
- **User Answer:** Yes, they usually ask the senior/founder or make mistakes.
- **Key Decision / Takeaway:** The system must act as an institutional memory agent so junior engineers can find proven, cost-effective vendors without bothering founders or picking the wrong supplier.

---

### Q7: Passwords & Secret Management
- **Question:** Do you already use a password manager anywhere in the company, or are 100% of credentials and API keys sitting in ad-hoc sheets and chats right now?
- **User Answer:** No password manager. Requested to **drop passwords/secrets from scope** as a feature entirely because logins often require OTP approvals anyway.
- **Key Decision / Takeaway:** Scoped out. Avoids security liabilities, vault sync bugs, and OTP friction.

---

### Q8: Sick Leave & Morning Check-in Workflow
- **Question:** When someone falls sick or needs sudden leave, what is the simplest way you want them to trigger it?
- **User Answer:** Morning push check-in from their personalized agent asking if they are coming to office. Agent should be conversational and human-like (not a wall of text). If user says "No, I'm sick today", agent asks a gentle follow-up ("What's the issue?"), logs the leave, and has a unique "soul" tailored to the person.
- **Key Decision / Takeaway:** Morning proactive check-in handles attendance and sickness gracefully. Teammates and founders are automatically kept in the loop.

---

### Q9: Language Barrier & Communication Medium
- **Question:** What languages do your engineering team members feel most comfortable communicating in, and would voice notes help?
- **User Answer:** **Forget about language translation / barrier**. Keep everything in **English**. Reading and writing English is not an issue for the engineering team; they only find spoken English harder. All UI and bot interactions will be in English.
- **Key Decision / Takeaway:** 100% English across the board. Greatly simplifies agent prompts and database schema.

---

### Q10: Bots, Models, Latency & Cost
- **Question:** Discussion regarding bot creator tools, custom API keys, and model performance.
- **User Answer:** Wants to know if Google Chat can connect to custom bot engines using different API keys (Mistral, Grok, TypeSafe Jev, etc.), if it's expensive per message, and needs low latency so the team doesn't experience frustrating delays.
- **Key Decision / Takeaway:**
  - Google Chat API = \$0.
  - LLM costs = ~\$1.50–\$3.00/month across 20 users using Groq/Mistral/Gemini Flash.
  - Sub-second latency (~300–600ms) with Groq / Flash ensures immediate responsiveness.

---

### Q11: Project Assignments & Resource Tracking
- **Question:** When a client buys a credit package, who decides project assignments and how are hours logged?
- **User Answer:** Founders scope the project and assign initial teams. Hours are logged in individual "Resource Sheets" (Excel/Google Sheets). Team members frequently forget to log hours or write vague entries. The client later inspects this sheet to see credits burned and tasks completed.
- **Key Decision / Takeaway:** The agent should interview employees conversationally, translate rough tasks into professional deliverable bullet points, and log them.

---

### Q12: Daily Check-in Cadence & Pomodoro Focus Tracking
- **Question:** At what time of day should the agent check in to capture hours and project work?
- **User Answer:**
  - Check-in happens in the **morning** to understand what they are working on and estimated completion time.
  - Follow-up check-ins every **2 to 3 hours**.
  - Include a **Pomodoro stopwatch-style card/feature** that tracks time blocks and updates credits based on active focus sessions.
- **Key Decision / Takeaway:** Combines morning planning with periodic 2–3 hour Pomodoro focus tracking directly in Google Chat.

---

### Q13: Sheet Destination & Review Flow
- **Question:** When the agent summarizes an employee's daily hours/credits, should it write directly into the client-facing Google Sheet or require founder review?
- **User Answer:**
  - Do **not** write directly to the client-facing sheet (that has its own review process).
  - During employee onboarding, the user pastes the link to **their personal Resource Google Sheet**.
  - The agent automatically updates that user's personal Resource Sheet without needing extra approval steps.
- **Key Decision / Takeaway:** Agent targets the individual employee's Google Sheet (stored during onboarding). No founder bottleneck required for individual sheet updates.

---

### Q14: Personal Resource Sheet Schema & Format
- **Question:** What are the exact column headers currently in your team's personal Resource Google Sheets?
- **User Answer / Sample Provided:** Uploaded `Resource_Akash_Pai.xlsx`.
- **Key Analysis & Structure Discovered:**
  - Organized by monthly tabs (`Sep 2026`, `Oct 2026`, etc.) + a `Monthly Summary` tab.
  - Row per day: `Date`, `Leave` (Boolean), `Total Hours`.
  - Repeating triplets for each project worked during that day:
    - `[Project N, Hours N, Log N]` (e.g., `STC: BPillar`, `2.5`, `Adding NFC+Face Unlock Clips+Changes`).
  - Standard project syntax: `<ClientName>: <Project/Task>` (e.g. `STC: BPillar`, `Essent: Air Purifier`, `Nexa: NEXA Marketing`, `SpOvum: UXUICollaterals`, `Z_Admin: General`).
  - Internal codes: `Z_Admin: General` for standup meetings, `Z_Marketing: General`, etc.
- **Key Decision / Takeaway:** The personal agent knows the active monthly sheet, locates today's date row, sets `Leave` status if absent, and appends `[Project, Hours, Log]` slots directly into their sheet via Google Sheets API.

---

### Q15: Central Master Project Directory
- **Question:** Is there a master list of active client projects and their `<Client>: <Project>` codes somewhere, or should the dashboard maintain that central project directory?
- **User Answer:** No, there is no master list currently. That is a core root cause of confusion—projects are scattered, people don't know who owns what or the progress across teams. We need a visual, simplified UX to manage projects rather than Excel sheets.
- **Key Decision / Takeaway:** The dashboard will serve as the single source of truth for all projects (Project Name, Client, Lead Owner, Sub-Owner, Team, Progress/Health, Drive Link, and Total Credits Burned vs Package Budget).

---

### Q16: Backend Hosting — Supabase Free Plan vs. Raspberry Pi
- **Question:** Raspberry Pi power/internet reliability vs. hosting backend on Supabase free tier.
- **User Answer:** Raspberry Pi has 24/7 power and internet in the office, but user is asking if Supabase free plan would have enough storage or if a Pi is necessary.
- **Key Analysis & Decision:**
  - **Supabase Free Tier has 500 MB database storage.**
  - For 20 people logging 3 tasks/day (~1,800 rows/month), annual data generation is only **~5 to 10 MB/year**. 500 MB will comfortably last **over 10+ years for free**.
  - **Verdict:** Host Postgres database on **Supabase Free Tier** (zero maintenance, 99.9% uptime, accessible from anywhere, automated cloud backups).
  - The Raspberry Pi can serve as a local cron runner/bot worker if desired, but isn't a bottleneck.

---

### Q17: Database & Agent Lookup Latency (Supabase Speed)
- **Question:** How fast will Supabase load information when someone asks the agent to find a vendor?
- **User Answer:** User is concerned about latency and whether the dashboard or agent will feel sluggish.
- **Key Analysis & Performance Benchmarks:**
  - **Supabase Query Latency:** Querying indexed vendor rows takes **15ms – 35ms** (0.03s) if hosted in the nearest AWS region (e.g., `ap-south-1` Mumbai).
  - **AI Model Speed:** Using Groq or Gemini Flash generates the response in **200ms – 400ms**.
  - **Total Roundtrip in Google Chat / Dashboard:** **~500ms to 800ms (under 1 second)**.
  - Sub-second performance feels snappy and instantaneous to the user.

---

### Q18: Communication Standards & SOP Enforcement (The Commandments)
- **Question:** What specific tasks do team members need help drafting, and what standards apply?
- **User Answer / Sample Provided:** Uploaded `Draft SOP for Communication.docx` ("The Communication Commandments", v0.9, 15 Sept 2026). Employees often fail to adhere to these rules, but an AI agent can enforce them consistently.
- **Core Rules Extracted:**
  - **The Spine Structure:**
    1. *What I have done* (or about to do).
    2. *Why I did it* (the reason/logic).
    3. *How it benefits the customer* (clear value or next step).
  - **The 11 Commandments:**
    1. *Never go dark* (same-day acknowledgement; mandatory next-morning file download check).
    2. *Follow the Spine* in every email.
    3. *Professional adult tone* (no slang, no emoji clutter).
    4. *Zero typos/errors*.
    5. *Flag schedule impact immediately* (state extra hours and affected milestone).
    6. *Quantify effort* (always cite estimated hours/credits).
    7. *Short, frequent updates* over delayed perfection.
    8. *End with a clear next step or question*.
    9. *Assume a new reader* (self-contained context).
    10. *When in doubt, send the update*.
    11. *Coordinate internally before promising dates*.
- **Key Decision / Takeaway:** The personal agent’s email drafting tool will be explicitly pre-conditioned with these 11 Commandments and "The Spine" architecture.

---

### Q19: Daily Meetings vs. Async Agent Check-in & System Scope
- **Question:** How to handle cross-team alignment (Design, Marketing, Engineering) without long meetings?
- **User Answer:** Team started a daily progress meeting, but attendance is spotty and people just talk casually without tracking real milestone progress. Having the agent ask questions asynchronously is much easier and more reliable. Also, this project is much broader than just a "Vendor Dashboard"—it is an entire operations hub/system. User wants to organize the folder and rename it appropriately.
- **Key Decision / Takeaway:** Replace or augment daily standups with an automated async agent check-in + roll-up digest. Rename/structure the project from "VendorDashboard" to an all-in-one operations hub (e.g. `BangOps` or `StudioHub`).

---

### Q20: Project Branding & Repository Architecture
- **Question:** What to call this system, and how to structure the subfolders for AI and human readability?
- **User Answer:** Call it **BangOps**. User updated the folder name from `VendorDashboard` to `BangOps`. Create only the essential subfolders needed now so any AI model or user navigating the repository immediately knows what the project is about and where every answer is.
- **Key Implementation:**
  - Organized root into 4 essential folders: `/docs`, `/samples`, `/prototypes`, `/legacy`.
  - Created master [`README.md`](../../README.md) as a complete system map and executive briefing.
  - Converted communication commandments from docx to readable markdown in [`docs/communication-commandments.md`](../sop/communication-commandments.md).

---

### Q21: Monday.com & Existing SaaS Tool Experience
- **Question:** Have you or your team tried off-the-shelf SaaS tools (like Monday.com, ClickUp, Notion, or Linear), and what made them fail or feel overwhelming?
- **User Answer:** The studio does have **Monday.com**, but only a few people (mainly founders) touch it, and strictly for one large client with outsourced contractors. The rest of the 20-person in-house team does not use it for daily projects or resource tracking.
- **Key Analysis & Takeaway:** Confirms classic enterprise SaaS abandonment: heavy tools like Monday.com require high administrative effort, don't fit credit-based time accounting, don't solve vendor lookup or sickness check-ins, and team members stop opening them. Proactive chat-first micro-agents completely bypass this UI friction.

---

### Q22: Sickness Failover & Sub-Owner Protocol
- **Question:** When the main owner of a project is marked sick or on leave, how should the sub-owner take over?
- **User Answer:** If the project owner is sick, the agent automatically detects active projects they lead and sends a conversational prompt to the designated sub-owner: *"Owner is out sick today on [Project]. Are you able to cover it?"*
  - If Sub-Owner says **Yes** ("Plate is clear, I can handle it"): Agent temporarily activates them as lead and shares latest notes/files.
  - If Sub-Owner says **No** ("My plate is full today"): Agent immediately escalates to the founders so they can step in or reassign without client deliveries slipping.
- **Key Decision / Takeaway:** Fully autonomous failover protocol with human confirmation and instant founder escalation on capacity blockers.

---

### Q23: Role-Based Dashboard Visibility & Studio Resources Tab
- **Question:** Should all 20 team members have open access to all projects and vendors, or are certain tabs founder-only?
- **User Answer:**
  - **Founder-Only:** Client commercial credit balances, revenue contract details, and billing rates.
  - **Open to Everyone:** All projects (owners, sub-owners, status, Drive links) and structured vendor pricing, quality ratings, and benchmark quotes.
  - **Studio Resources Tab:** Idea parked for v2. Core v1 focus is solving the operational problems directly.

---

### Q24: Architectural Strategy — Heavy Kanban Dashboard vs. Chat-First Personal Agents + Minimal Hub
- **Question:** Which is the superior option: a full-fledged dashboard with Kanban boards, or personal chat agents with a lightweight information hub?
- **User Strategic Request:** Assess whether a full-fledged dashboard or personal agents best solve the studio's problems based on the accumulated context.
- **Architectural Verdict:** 
  - **Heavy Kanban dashboards fail:** Monday.com already proved that in this studio. Requiring 20 creative and technical people to manage cards, columns, and tickets results in rapid tool fatigue and abandonment.
  - **Winning Model:** **"Chat-First for Input, Lean Dashboard for Visibility"**. 
    - Input happens 100% in Google Chat where people already are (2-second check-ins, Pomodoro buttons, sick leaves).
    - The dashboard is a clean, read-mostly "Information Radiator" (Today's availability, Master Project Directory, and Vendor Directory).

---

### Q25: Research Documentation & Flow Specification
- **Question:** Create dedicated research documents and flow files for future design phases.
- **User Deliverables Generated:**
  - `docs/pain-points-analysis.md`: Detailed catalog of all 18 operational bottlenecks at Bang Design.
  - `docs/market-research-saas-comparison.md`: Monday.com, Linear, Notion, Airtable, ClickUp analysis + feature theft matrix.
  - `docs/ai-models-and-bot-engines.md`: TypeSafe Jev, Groq, Mistral, Gemini Flash latency, pricing, and Google Chat API Card v2 architecture.
  - `docs/information-architecture.md`: 3-Room dashboard IA, Supabase Postgres schema, and role-based permissions.
  - `flows/01-morning-checkin-and-leave.md`: Sequence flow + Card UI for morning check-in and sick leaves.
  - `flows/02-subowner-sickness-failover.md`: Autonomous project re-routing to sub-owners + founder capacity alerts.
  - `flows/03-pomodoro-credit-logging.md`: 2.5-hour focus timer prompts + auto-writing into `Resource_Name.xlsx`.
  - `flows/04-vendor-search-and-quoting.md`: Fabrication supplier discovery with 3D print quote benchmark alerts.
  - `flows/05-sop-communication-drafting.md`: Client email generator pre-conditioned with "The Spine" & 11 Commandments.

---

### Q26: Live Google Chat Card Demo & Design Tone
- **Test:** Successfully dispatched live Google Chat Card v2 into user's private Google Chat space via webhook.
- **User Feedback:**
  - Surprised and impressed that it works live.
  - Initial card had too much text, tacky emojis, and lacked conversational tone.
  - Wants zero text bloat, no AI slop emojis, personalized voice, and interactive two-way follow-up replies.
- **Key Technical Note on Two-Way Replies:**
  - An *Incoming Webhook* is a one-way notification pipe.
  - A *Google Chat App (Bot)* has an interactive HTTP webhook endpoint so that when a user clicks a button or replies in natural language, the backend receives the event, triggers the LLM/Jev classifier, and updates the message conversationally.

---

### Q27: Studio-Wide Deployment & Onboarding (Zero-Touch Setup)
- **Question:** How does onboarding work for all 20 employees? Do founders need to configure each laptop individually, or can it be done via a single link?
- **User Concern:** Fear of having to manually configure webhooks and spaces on 20 different machines.
- **Architectural Solution (Domain-Level Google Chat App):**
  - **Zero touch required on employee laptops.**
  - Because Bang Design is on a paid Google Workspace domain (`@bangid.com`), the bot is installed once at the domain level.
  - **Option 1 (Proactive):** The bot automatically pops up as a 1:1 Direct Message (DM) in every employee's Google Chat inbox.
  - **Option 2 (Single Link):** Founders send one link (`chat.google.com/dm/bangops-bot`). When an employee clicks it, the bot initiates a 2-minute interactive card-based onboarding directly inside their chat.

---

### Q28: Custom AI Model Pluggability & Google Drive Deep-Scanning
- **Question:** Can we connect ANY custom AI model, will responses be instant, and can the agent search/read Excel files buried inside Google Drive folders?
- **Key Technical Verdicts:**
  1. **Any AI Model is Supported:** The backend is a standard API router. You can swap between Groq (Llama 3.1), Mistral, DeepSeek, Claude, Gemini, or custom fine-tuned models hosted on OpenPipe/RunPod simply by changing an API key in `.env`.
  2. **Instant Response Latency:** Fast inference engines (Groq/Flash) reply in **~300ms–600ms**, delivering sub-second replies inside Google Chat.
  3. **Google Drive & Excel Deep-Scanning:** Using native Google Drive & Sheets APIs with domain-wide access, the agent can search folders, read binary `.xlsx` / Google Sheets on the fly, extract cell data, and answer questions directly in the chat with source citations.

---

### Q29: Google Drive API & Spreadsheet Scanning Pricing
- **Question:** Does enabling Google Drive API access to search and read company spreadsheets cost extra?
- **Pricing Breakdown & Verdict:**
  - **Google Drive / Sheets API Cost:** **$0.00 (100% Free)**. Included with your existing Google Workspace subscription with massive generous quotas (20,000 queries / 100 sec).
  - **AI Model Token Cost:** Reading a typical 50–100 row spreadsheet extracts ~1,500 tokens. On Groq / Gemini Flash / Mistral, 1,500 tokens costs **~$0.0001 (less than 1 paisa)** per lookup.
  - **Net Extra Cost:** **Virtually zero ($0)**.

---

### Q30: Desktop Notifications & Screen/Activity Tracking Analysis
- **Question:** How to handle someone forgetting to open Google Chat (OS push notifications), and can we install a desktop app that captures screens hourly to track work?
- **Analysis & Strategic Recommendation:**
  1. **Native OS Push Notifications:** Google Chat has official native desktop apps (Windows/Mac) and mobile apps (Android/iOS) that trigger standard Windows toast notifications even when the browser is closed.
  2. **The "Screen Monitoring" Trap:** Taking hourly screenshots (like Hubstaff/Time Doctor) creates extreme employee resentment, damages trust, and fails for physical designers (who sketch on paper, inspect 3D prototypes, or review physical parts off-screen).
  3. **Privacy-Preserving Alternative (Window/App Focus Tracker):** A lightweight background tray app (`BangOps Companion`) that tracks only the active application name (e.g., *SolidWorks: 2.5h*, *Figma: 1.5h*) without capturing screens or keystrokes, prompting a 1-click end-of-day summary (*"Log 2.5h SolidWorks to STC BPillar?"*).

---

### Q31: 24/7 Google Chat Bot Architecture & Message Trigger
- **Question:** Can an agent run 24/7 on Google Chat that wakes up and responds whenever an employee texts it in 1:1 DMs?
- **Technical Architecture & Confirmation:**
  - **Yes, 100% native.** This is the standard Google Chat App webhook model.
  - The agent backend runs as a lightweight service (hosted 24/7 on Google Cloud Run, Render, or the office Raspberry Pi).
  - Whenever any team member sends a message in their 1:1 chat (at any hour), Google Chat fires an instant HTTP event to the server.
  - The AI model processes the text and replies inside Google Chat in ~300ms–500ms.
  - When no one is chatting, it uses zero CPU and costs \$0.

---

### Q32: Single-Page End-to-End Scenario PDF (Front-End Chat vs. Back-End Systems)
- **Question:** Provide a single-page PDF scenario illustrating how an employee chats with the agent side-by-side with backend execution explanations for each phase.
- **Deliverable Generated:**
  - File: [`BangOps_Scenario_Walkthrough.pdf`](../assets/scenario/BangOps_Scenario_Walkthrough.pdf) (Strictly 1 Page A4).
  - Layout: Side-by-side comparative grid:
    1. *Phase 1 (09:30 AM):* Morning Check-in & Focus Locking vs. Cron Trigger, Jev Intent Classification, Supabase status update, and local timer.
    2. *Phase 2 (12:00 PM):* Sprint Wrap-up & Timesheet Logging vs. Groq Llama-3.1 deliverable rewriting, Google Sheets API authentication, appending to `Resource_Akash_Pai.xlsx`, and Supabase credit burn counters.
    3. *Phase 3 (02:30 PM):* Google Drive & Vendor Procurement Query vs. Drive API scanning `3D_Print_Vendors_Quote_Comparison.xlsx`, part-level spread isolation, and vendor contact retrieval.
    4. *Phase 4 (Anytime/24h):* Sick Leave Notice & Sub-Owner Stand-in vs. Automated `Leave = True` write, active project lookup, sub-owner stand-in prompt card, and founder capacity escalation.

---

### Q33: Bypassing Google Cloud Project & Tailscale Connectivity
- **Question:** Can this agent be enabled WITHOUT a Google Cloud Project (e.g. connecting Google Chat to a Raspberry Pi via Tailscale)?
- **Technical Analysis & Workarounds:**
  1. **The Tailscale Reality:** Tailscale is a private VPN. Google's public cloud servers cannot reach a private `100.x.y.z` Tailscale IP directly unless using **Tailscale Funnel** (which gives the Raspberry Pi a public HTTPS URL with free SSL).
  2. **Push-Only (Webhooks):** Requires **ZERO Google Cloud Project**. A Python script on a Pi can push cards to spaces anytime.
  3. **Two-Way DMs via Google Apps Script (Zero-GCP Alternative):** Using a free Google Apps Script (`script.google.com`) deployed as a Chat App. It intercepts 1:1 messages inside Workspace without ever touching Google Cloud Console, and forwards them to the Pi.
  4. **Official GCP Chat App:** Takes ~3 minutes, requires no credit card, and is 100% free for internal Workspace apps.

---

### Q34: Google Apps Script Multi-User Deployment Scope
- **Question:** If avoiding Google Cloud Console via Google Apps Script, does the script need to be installed on each employee's account individually, or enabled automatically domain-wide?
- **Technical Architecture & Confirmation:**
  - **Deployed ONCE for the entire domain.** Never installed per user.
  - The script is set to **"Available to everyone in Bang Design"**.
  - When any of the 20 team members sends a message, Google Chat passes their identity (`e.user.email`, `e.user.displayName`) to the single Apps Script.
  - The script relays the user's email and message to the Raspberry Pi over Tailscale Funnel.
  - The Pi identifies the employee automatically and updates their individual Resource Sheet.

---

### Q35: Autonomous Gmail Monitoring, 3-Day Silence Alerts & Email-to-Task Conversion
- **Question:** How can the system proactively read user emails to (1) alert when a client conversation has gone silent for 3 days, and (2) extract actionable tasks from incoming emails?
- **Technical Architecture & Workflow:**
  1. **Gmail API / Workspace Service Account:** Operates with domain-wide read-only Gmail access or a scheduled Apps Script cron trigger running every few hours.
  2. **3-Day Client Silence Watchdog (Commandment 1):** Scans active client threads. If `last_message_timestamp < NOW() - 72h` without closure, the agent proactively pings the project lead on Google Chat: *"It's been 3 days since the last note to [Client]. Want me to draft a Spine update?"*.
  3. **AI Email-to-Task Extraction:** TypeSafe Jev / Groq analyzes incoming client emails for actionable requests (e.g. CAD changes, render requests), calculates estimated credit impact (Commandment 6), and presents a 1-tap Google Chat Card to add it to the team's sprint.

---

### Q36: Individual Mailbox Access vs. Domain-Wide Multi-User Email Scanning
- **Question:** If the Apps Script runs on `bang@bangid.com`, will it read everyone else's emails automatically?
- **Security & Privacy Analysis:**
  - Standard `GmailApp` in Apps Script only accesses the mailbox of the account running it (`bang@bangid.com`). Google restricts standard scripts from peeking into other colleagues' private inboxes.
  - **Path 1 (CC / Shared Group):** If `bang@bangid.com` (or a studio alias like `projects@bangid.com`) is CC'd on client communications, this single script monitors 100% of client threads studio-wide.
  - **Path 2 (Domain-Wide Delegation):** In Google Workspace Admin Console (`admin.google.com`), an admin grants a single Service Account read-only permission (`gmail.readonly`) to inspect client threads across all `@bangid.com` user accounts.

---

### Q37: Email Watchdog Utility vs. Core Studio Problems
- **Observation:** User successfully ran the script and received the live card in Google Chat. Noted that opening one's own email is easy, and asked if installing scripts on every account is needed.
- **Architectural Reality:**
  - **Zero per-user installs:** Nobody ever installs scripts on 20 individual machines. In enterprise Workspace, a single Service Account handles it domain-wide.
  - **Pragmatic Priority Check:** For an individual, checking your own email is simple. The real studio breakdown occurs when *colleagues* miss client emails or fall sick without anyone knowing.
  - However, email monitoring carries privacy friction. The highest-leverage, zero-friction wins remain:
    1. Proactive morning attendance & sickness failover to sub-owners.
    2. 1-click Pomodoro credit logging into `Resource_Akash_Pai.xlsx`.
    3. Instant 3D print & fabrication vendor intelligence.

---

### Q38: 1-Click OAuth Authorization Button During Onboarding
- **Question:** Can onboarding simply send an embedded button/link that requests all necessary permissions and sets up the user in 1 click?
- **Technical Mechanism (Standard OAuth 2.0 Flow):**
  - **Yes, standard OAuth Web Flow.** The bot sends a card with `[ 🔗 Connect your Google Account ]`.
  - Clicking the button opens the standard Google Consent screen (*"BangOps wants access to Sheets & Gmail"*).
  - The employee clicks **Allow** (takes 5 seconds). Google redirects to the backend with an OAuth token stored in Supabase.
  - **Alternative (Domain-Wide Admin Install):** In Google Workspace, an admin can also do a "Domain Install" from Workspace Marketplace once, granting permissions to all 20 users without individual clicks.

---

### Q39: Centralized Agent Execution vs. Distributed Script Copies
- **Question:** Does the link install separate scripts inside each user's Google account, and how do Grok/Gemini agents trigger it?
- **Architectural Clarification:**
  - **No code is installed in user accounts.** The button simply grants permission (an OAuth token) to the centralized backend running on the Raspberry Pi / cloud.
  - **Single Central Brain (Grok/Gemini):** The AI models run on the central server. When an action occurs (morning check-in, sprint completion, vendor query), Grok/Gemini decides the action and uses that employee's permission token to write to their sheet or read their thread.
  - **Zero Maintenance Overhead:** Updating an AI prompt or adding a feature is done in ONE central file, instantly updating behavior for all 20 employees without touching their accounts.

---

### Q40: Autonomous Client Asks Extraction & Daily Follow-Up Loop
- **Question:** Can the agent scan client emails daily, extract open deliverables/asks, cross-check progress, and proactively nudge employees to confirm if they updated the client?
- **Workflow & Architectural Execution:**
  1. **Daily Email Parsing:** Every morning, the central agent scans active client threads via Gmail API.
  2. **Action Item Extraction:** Groq / Gemini Flash extracts concrete client asks (e.g., *"Share revised STEP file"*, *"Update pricing breakdown"*).
  3. **Progress Cross-Check:** Checks if an outgoing email was sent resolving the ask, or checks logged hours in `Resource_Name.xlsx`.
  4. **Proactive Google Chat Card:** If unfulfilled, the agent pings the assigned designer with a concise card: *"John asked for the updated STEP file on Tuesday. Have you sent this over yet?"* with 1-tap responses (`[ Sent ]`, `[ Still in Progress ]`, `[ Blocked ]`).
  5. **Auto-Remediation:** If blocked or in progress, the agent offers to draft a proactive "in-progress" note to prevent client silence (enforcing SOP Commandment 1 & 7).

---

### Q41: Real-Time Evening Client Feedback Digestion & Recommended Next Steps
- **Question:** If a client sends feedback in the evening, can the AI automatically notify the team, summarize the feedback, and recommend exact next steps?
- **Workflow & Architectural Execution:**
  1. **Real-Time Trigger (Gmail Pub/Sub or 15-min Poll):** Detects incoming email from an active client domain after hours.
  2. **AI Feedback Synthesis (Groq / Gemini Flash):** Extracts key feedback points, maps to project code (`STC: BPillar`), estimates credit/timeline impact, and devises structured next steps.
  3. **Proactive Google Chat Card:** Alerts the lead designer and founders with a 3-bullet summary + recommended actions.
  4. **1-Tap Same-Day Acknowledgement (SOP Commandment 1):** Provides an instant button to dispatch a professional "Received & Scheduled" email to the client so they are never left wondering overnight.

---

### Q42: Zero Google Cloud & Zero Service Account Architecture
- **Question:** How can the entire system run if the user refuses to use Google Cloud Console and Service Accounts?
- **Analysis & Viable Zero-Cloud Solutions:**
  1. **Google Apps Script as the Sole Google Engine:**
     - Uses native `GmailApp`, `SpreadsheetApp`, and `UrlFetchApp`.
     - Zero Google Cloud Console. Zero Service Accounts. Runs directly inside Google Drive / Workspace for free.
     - Scheduled triggers run automatically inside Google's infrastructure.
     - Pushes rich cards to Google Chat spaces via standard incoming webhooks.
  2. **Interactive Responses via Web App Endpoints:**
     - Deploy Apps Script as a "Web App" (`doGet`/`doPost`).
     - Card buttons link to the Web App URL for 1-tap state updates without GCP bot registration.
  3. **Alternative: Telegram Bot:**
     - Pure zero-cloud setup. 30-second token from `@BotFather`.
     - Full two-way interactive buttons, voice notes, and 24/7 DMs running on the Raspberry Pi without any enterprise Google permissions.

---

### Q43: Long-Term Memory Architecture & Context Window Scaling (Day 1 vs. Month 5)
- **Question:** Where is memory stored, and won't 5 months of daily/hourly updates overflow the model's context window, slow down responses, and become expensive?
- **Core Engineering Solution (Tiered Memory Architecture):**
  - **The Anti-Pattern:** Naive agents dump raw chat history into giant files and re-feed months of text into every prompt. Latency and costs explode.
  - **BangOps Tiered Memory Architecture:**
    1. *Tier 1: Profile Memory (`soul.md`):* Constant ~500 tokens (Name, working hours, active projects, tone). Never grows out of control.
    2. *Tier 2: Structured State (Postgres / Google Sheets):* Hourly logs are stored as database rows, not chat history. When the agent checks in, it queries ONLY today's date row via SQL (`WHERE date = CURRENT_DATE`). Context size is identical on Day 1 and Day 180 (~800 tokens).
    3. *Tier 3: On-Demand Semantic RAG (Long-Term Recall):* Past historical files (old quotes, specs from 5 months ago) are indexed in embeddings. The model retrieves only the top 2 relevant paragraphs on-demand when explicitly asked.
  - **System Guarantee:** Prompt payload remains flat at ~800 tokens. Latency remains fixed at ~300ms and total monthly cost stays <$3/mo permanently.

---

### Q44: Re-scoped v1 Brief (25 Sep 2026)
- **User Brief:** Research before choosing a solution. Main pain points: (1) the resource sheet is hard to maintain and people forget to fill it; (2) the agent should know what people are working on and when a client has emailed; (3) help writing SOP-quality emails: "I did this, want feedback" → the agent knows the project and client → offers options → drafts → copy/paste, or send on approval if integrated. It must be very simple (a download, a plugin, or a script on top of Google Workspace). No service account, Google Cloud Console, or Admin Console. Later this grows into a team of bots.
- **Reference shared:** [luislozanogmia/miamultiplayer](https://github.com/luislozanogmia/miamultiplayer) (Humans → Agents → Bots, Electron + Hermes Agent).
- **Output:** [`competitive-research-2026.md`](competitive-research-2026.md), [`current-state-audit.md`](../status/current-state-audit.md).

---

### Q45: Google Cloud / Admin Console Constraint, Clarified
- **Answer:** Has access, but **wants to avoid it** (zero setup complexity, nothing to maintain there).
- **Takeaway:** Default to Google Apps Script with its default project. A one-time Cloud link stays available as an *optional* upgrade (e.g. a native two-way Chat bot), not a requirement.

---

### Q46: Where Client Emails Arrive
- **Answer:** **Each person's own inbox.**
- **Takeaway:** Email awareness must run *as each user* (per-user authorization and triggers). A single shared-mailbox script (Q36 Path 1) wouldn't see most threads, and domain-wide delegation is ruled out.

---

### Q47: Agent Surface & Workspace Plan
- **Answer:** Surface: "whatever is simple and the best." Workspace plan: not specified.
- **Decision (proposed):** a bookmarked **BangOps web app** (Apps Script) for chat and approvals, plus **Google Chat webhook cards** for notifications. Gemini Gems / Workspace Studio are an optional quick win *if* the plan is Business Standard or above (**still to confirm**).
- **Output:** [`architecture-v2-workspace-native.md`](../architecture/architecture-v2-workspace-native.md), flows [06](../../flows/06-work-note-to-client-email.md), [07](../../flows/07-inbound-client-email.md), [08](../../flows/08-auto-drafted-resource-log.md).
