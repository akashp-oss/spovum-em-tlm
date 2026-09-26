# BangOps — AI Models, Inference Engines & Bot Architecture

*Technical evaluation of AI models, latency benchmarks, Google Chat API Card v2 capabilities, and system cost breakdown for BangOps.*

> ⚠️ **Review note (25 Sep 2026):** (1) §3.4 "Service Account proactive messaging" is **ruled out** by the no-Google-Cloud constraint. Proactive notices go through incoming webhooks instead (see [`architecture-v2-workspace-native.md`](architecture-v2-workspace-native.md) §1.5). (2) The models named here (Llama 3.1 8B, Gemini 1.5/2.0 Flash) are outdated, so re-pick them when building. (3) Cost and latency figures are unmeasured estimates. A realistic cost with a current drafting model is ~$5–30/month.

---

## 1. Multi-Tier Model Architecture

Rather than relying on a single slow, expensive model for everything, BangOps employs a **dual-tier routing architecture**:

```
                  User Input (Google Chat Webhook)
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │       TIER 1: Fast Decision Classifier       │
        │             TypeSafe Jev (~100ms)            │
        │  • Intent: Leave / Pomodoro / Vendor / Email │
        │  • Urgency scoring (0–10)                    │
        │  • Entity extraction & security guardrails   │
        └──────────────────────┬───────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 [Deterministic Action]                 [Generative Task]
 (e.g. Set Leave = True,                (e.g. Draft Client Email,
  Start Pomodoro Timer)                  Summarize Standup Rollup)
            │                                     │
            │                                     ▼
            │                   ┌──────────────────────────────────┐
            │                   │   TIER 2: Fast Generative Model  │
            │                   │    Groq (Llama-3.1) / Gemini     │
            │                   │   • Follows SOP Commandments     │
            │                   │   • Formats Timesheet Row        │
            │                   └─────────────────┬────────────────┘
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                    Google Chat Card v2 Response
```

---

## 2. In-Depth Model & Provider Analysis

### Tier 1: TypeSafe Jev (Decision & Intent Routing)
- **Role:** The ultra-fast, structured router. Used as an intelligent `if-else` statement.
- **Why Jev?**
  - Sub-100ms latency.
  - Cost: **\$0.042 per million input tokens** (Output tokens free).
  - High determinism: Returns strict structured JSON without conversational fluff.
- **Specific BangOps Uses:**
  1. Classify morning reply: *"Is this a sickness notice, work plan, or casual chit-chat?"*
  2. Guardrail check: *"Does this message contain raw API keys or passwords?"*
  3. Escalation check: *"Did the sub-owner decline covering the project? If yes, trigger founder alert."*

---

### Tier 2: Groq / Gemini Flash / Mistral (Generative Assistants)

#### Option A: Groq (running Llama 3.1 8B Instant)
- **Speed:** **~800 tokens/second** (~200–300ms total latency).
- **Pricing:** **\$0.05 / million input tokens**, **\$0.08 / million output tokens**.
- **Strength:** The fastest inference on the market. Responses appear instantly in Google Chat. Ideal for interactive Pomodoro check-ins and quick vendor summaries.

#### Option B: Mistral AI (Mistral Small / Nemo)
- **Speed:** ~400–600ms latency.
- **Pricing:** **\$0.10 – \$0.20 / million tokens**.
- **Strength:** Renowned for strict system prompt adherence and formal European writing tone. Ideal for generating client-facing emails complying with "The Spine" and the 11 Commandments.

#### Option C: Gemini 1.5/2.0 Flash
- **Speed:** ~300–500ms latency.
- **Pricing:** **\$0.075 / million tokens**.
- **Strength:** Deep native integration with Google Workspace, massive 1M context window (can digest months of raw quote sheets in a single prompt).

---

## 3. Google Chat API (Card v2 Architecture)

Google Chat on Google Workspace (`@bangid.com`) provides a first-class enterprise bot framework at **zero marginal cost**.

### Key Capabilities Used in BangOps:
1. **Interactive Cards (`CardWithId`):**
   - Renders buttons, status chips, and formatted markdown.
   - Example: A Pomodoro focus card with `[ ✅ Complete ]` and `[ ⏱ +1 Hour ]` buttons.
2. **Interactive Form Inputs:**
   - `selectionInput` (dropdowns, radio buttons, checkboxes).
   - `textInput` (capturing quick deliverable notes).
3. **Modal Dialogs:**
   - Tapping *"Search Vendor"* pops up an in-chat modal to select material, process, and price range without leaving Google Chat.
4. **Service Account Proactive Messaging:**
   - The bot can initiate direct 1:1 messages to any employee at scheduled times (e.g. 9:30 AM morning check-in) without waiting for the user to speak first.

---

## 4. Latency & Budget Breakdown (20-Person Studio)

### A. Monthly Token & Cost Projection

| Metric | Estimate |
|---|---|
| Active Users | 20 people |
| Daily Interactions per Person | 6 interactions (1 morning check-in, 3 Pomodoro sprints, 1 timesheet write, 1 ad-hoc query) |
| Total Daily Studio Interactions | 120 interactions / day |
| Tokens per Interaction | ~400 tokens (prompt + output) |
| Total Daily Tokens | ~48,000 tokens / day |
| **Total Monthly Tokens** | **~1,200,000 tokens / month** |
| **Total Monthly AI Cost** | **$0.80 – $2.50 / month** across all models combined |
| **Google Chat API Cost** | **$0.00** (Included with Google Workspace) |
| **Supabase Postgres Cost** | **$0.00** (Free Tier covers 500 MB = 10+ years) |
| **Net Operational Cost** | **< $5.00 / month total** |

### B. End-to-End Latency Benchmark

```
User types in Google Chat
  │
  ├─> Webhook receipt at backend: ~40ms
  ├─> TypeSafe Jev intent classification: ~90ms
  ├─> Supabase Postgres query: ~25ms
  ├─> Groq / Gemini Flash generation: ~320ms
  └─> Google Chat Card render: ~80ms
────────────────────────────────────────────────────
Total User Perceived Latency: ~555ms (Sub-second)
```
