# Bang Design Operations & Agent Discovery Log

*Single source of truth summarizing user requirements, Q&A decisions, constraints, and operational architecture.*

---

## 1. Company & Team Context
- **Company:** Bang Design ([bangid.com](https://bangid.com))
- **Business Model:** Design subscription service across Industrial Design, Marketing, and Engineering.
- **Credit System:** **1 Hour = 1 Credit**. Clients buy credit bundles (e.g., Pro 140 credits). Team members burn credits against specific client projects.
- **Team Size:** ~20 members across Industrial Design, Marketing, and Engineering.
- **Founders' Role:** Founders negotiate initial client deals, scope packages, and assign project owners/teams.

---

## 2. Infrastructure & Tooling Decisions
- **Chat Platform:** **Google Chat** via paid Google Workspace domain (`@bangid.com`).
  - Native Google Chat API with interactive cards (buttons, modals, forms).
  - Free API tier with zero cost per message.
- **Language Decision:** **English only**. No multi-language translation needed (team understands and writes English comfortably).
- **Security & Passwords:** **Dropped from scope**. Passwords & API keys won't be managed by this custom dashboard due to OTP friction and security liability.
- **AI Models & Latency:**
  - Fast, cheap APIs: **Mistral** (Nemo / Small), **Groq** (Llama 3.1 8B, ultra-low latency <300ms), or **Gemini Flash**.
  - **TypeSafe Jev** for lightweight intent classification & routing decisions.
  - Overall monthly AI cost estimate: **$1.50 – $3.00/month** for the entire 20-person company.
- **Hosting / Backend:**
  - Core database: Managed Postgres (e.g., Neon / Supabase free tier).
  - Agent / Webhook server: Lightweight Python FastAPI/Flask service (can run on local Raspberry Pi / Render / Cloudflare Tunnel).

---

## 3. Daily Agent Cadence & Time Tracking (Pomodoro / Micro-Check-ins)
1. **Morning Check-in:**
   - Gentle, human-like check-in: *"Coming into the studio today?"*
   - **If Sick / Away:** Empathetic confirmation, asks if anything urgent needs coverage, auto-alerts project teammates/founders, marks status on the dashboard.
   - **If Working:** Asks what key project/task they are focusing on today and estimated hours.
2. **Work Tracking / Pomodoro Stopwatch:**
   - Lightweight progress nudges every 2–3 hours or a Pomodoro-style timer card in Google Chat (e.g., *"Start 2h focus block on Enclosure CAD"* -> tap *"Complete"* or *"Need +1h"*).
   - Automatically logs credits/hours spent without making employees fill tedious forms.
3. **Client-Facing Timesheet Formatting:**
   - Translates casual employee updates into crisp, professional deliverable logs for the client-visible Resource Sheet.

---

## 4. Vendor Intelligence (Industrial Design & Engineering)
- **Pain Point:** 4+ vendors quoted per project (e.g., `3D_Print_Vendors_Quote_Comparison.xlsx` with SLA ABS, CNC, sheet metal, injection moulding). Huge price swings (e.g., one part 2x more expensive at BOTAAT vs Design Roots).
- **Current Bottleneck:** Junior engineers ask founders/seniors verbally or make expensive quote mistakes.
- **Goal:** Intelligent vendor lookup on the dashboard:
  - Filter by Process / Material (SLA, SLS, FDM, Sheet Metal, CNC, PCBs).
  - Price Band (Cheap / Mid / Premium) vs Quality Rating (1–5) vs Turnaround Time.
  - Historical quote benchmarks & part notes (e.g., "Best for large enclosures", "Fast turnaround for brackets").
