# BangOps — Current State Audit (25 Sep 2026)

*An honest inventory of what's in this folder: what's real, what's only on paper, what contradicts itself, and what's missing for the new priority (email awareness + resource-sheet automation).*

---

## 1. What has actually been done

| Area | Status | Evidence |
|---|---|---|
| Discovery interviews | ✅ **Solid.** 43 Q&As covering team, credits, sheets, vendors, SOP, sick leave, email, memory | [`qa-interview-log.md`](../research/qa-interview-log.md) |
| Pain-point catalogue | ✅ Done (18 pain points) | [`pain-points-analysis.md`](../research/pain-points-analysis.md) |
| Communication SOP | ✅ Converted to markdown (v0.9 draft, not yet mandatory) | [`communication-commandments.md`](../sop/communication-commandments.md) |
| Resource sheet format | ✅ Understood. Monthly tabs, one row per day, `Date / Leave / Total Hours` then up to ~22 `[Project N, Hours N, Log N]` triplets. Project list lives in the `DD_Helper` tab (`Client: Project`) | [`samples/Resource_Akash_Pai.xlsx`](../../samples/Resource_Akash_Pai.xlsx) |
| Flow specs | ✅ 5 flows with sequence diagrams + card mock-ups (check-in, sick failover, pomodoro logging, vendors, SOP drafting) | [`flows/`](../../flows) |
| HTML prototypes | ✅ Dashboard + onboarding click-throughs (visual only) | [`prototypes/`](../../prototypes) |
| One-page scenario | ✅ PDF/PNG walkthrough | [`BangOps_Scenario_Walkthrough.pdf`](../assets/scenario/BangOps_Scenario_Walkthrough.pdf) |
| Google Chat push | ✅ **Proven live.** Incoming-webhook cards post to a Chat space (one-way only) | `send_clean_card.py`, `send_demo_cards.py` |
| Python agents | ⚠️ **Demo only.** `PersonalAgent`, `HRAgent`, `AgentCoordinator` use hard-coded in-memory projects, **make no LLM calls**, and **write nothing to Google Sheets**. `FileInspector` reads the local `.xlsx` only | [`agents/`](../../demo/python-agents/agents), `run_agent_cli.py` |
| Vendor Drive (legacy) | ⚠️ A separate earlier app: FastAPI + Gemini search over uploaded spreadsheets (Render + Neon). Not connected to BangOps | [`legacy/vendor-drive-main/`](../../legacy/vendor-drive-main) |
| Email agent (Gmail watch / reply) | ❌ **Talked about only** (Q35–Q41). No flow file, no code | — |
| Database, dashboard, real bot | ❌ Not started | — |

**Bottom line:** discovery and design are about 80% done, and building is about 5% done. Nothing yet takes real input from a person and writes real output.

---

## 2. Contradictions between docs (need to be resolved)

| Topic | Says A | Says B | Current truth (from the latest interview answers) |
|---|---|---|---|
| Chat surface | `architecture-plan.md`: **Telegram** primary | README / Q4: **Google Chat** | Google Chat, but a two-way Chat bot needs a GCP project (Q33), which you now rule out |
| Proactive DMs | `ai-models-and-bot-engines.md` §3.4: "Service Account proactive messaging" | Q42 + your brief: **no service account, no GCP** | Service accounts are ruled out, so that section is invalid |
| Passwords | `architecture-plan.md`: Bitwarden, "Room 4 Stack", phase 0 | Q7: **dropped from scope** | Dropped |
| Dashboard | `architecture-plan.md`: 4 rooms | `information-architecture.md`: 3 rooms | 3 rooms (and it's lower priority now) |
| AI cost | README / models doc: **$1.50–3/mo** | `architecture-plan.md`: **$20–60/mo** | Realistic figure is **~$5–30/mo** with a current mid-tier model drafting emails. The $1.50 figure assumed tiny 8B models |
| Models named | Llama 3.1 8B, Gemini 1.5/2.0 Flash | — | These are **outdated** (2024-era). Re-pick when building |
| Latency claims | "~555ms end-to-end" | — | Unmeasured estimates. Treat as targets, not facts |
| Language | `architecture-plan.md` / soul.md: multi-language, translation | Q9: **English only** | English only |
| Credit system | `architecture-plan.md` §10.7: "not modelled in v1" | IA doc: `credits_burned` column | Undecided |

---

## 3. Security issues found (fix now)

1. 🔴 **A live Google Chat webhook URL (with `key` and `token`) was hard-coded** in the demo scripts (now `demo/python-agents/`). Fixed 26 Sep: it is read from `BANGOPS_CHAT_WEBHOOK`, but the old key still needs rotating. Anyone who gets these files can post into that Chat space. **Action:** delete that webhook in the space's *Apps & integrations* settings, make a new one, and load it from an environment variable or `.env` file that's never shared or committed.
2. 🟡 `legacy/vendor-drive-main/venv/` (most of the folder's ~224 MB) and `data/drive.db` are in the project tree. If this ever becomes a git repo, add a `.gitignore` for them.
3. 🟡 The email-watching ideas (Q35–Q41) would read client mail. Decide the **privacy contract** before building: whose inbox, read-only or not, what gets stored, and who can see summaries.

---

## 4. What's missing for the new priority

What you asked for on 25 Sep 2026: *know what we're working on → know when a client emails → help reply with SOP-quality drafts → approve → send or copy. Very simple for everyone.*

| Needed | Exists? |
|---|---|
| **Client & project directory** (client name, email domains, contacts, project codes, owner / sub-owner, tone notes) | ❌ Only a flat `DD_Helper` list of `Client: Project` strings. **This is the #1 missing data asset.** The agent can't tell which project a message is about without it |
| **Email-examples library** (good past emails per client, to learn studio tone) | ❌ |
| Flow: "I did X, want feedback" → project detection → options → draft → approve | ⚠️ Flow 05 covers drafting but not project detection, options, or send-on-approval |
| Flow: inbound client email → summary → suggested actions → reply draft | ❌ (only in Q40/Q41 prose) |
| Flow: auto-drafted resource-sheet rows from the day's signals → approve | ⚠️ Flow 03 relies on pomodoro timers. No "draft from signals" approach |
| Decision on where the agent lives, given no GCP | ❌ See [`competitive-research-2026.md`](../research/competitive-research-2026.md) §5 |

---

## 5. Recommended cleanup (low effort)

- Mark `architecture-plan.md` as **superseded** where it conflicts (Telegram, Bitwarden, Room 4, multi-language).
- Remove the service-account section from `ai-models-and-bot-engines.md` and replace the outdated model names.
- Keep `agents/` as a reference demo. It shouldn't become the production base unless we pick a Python server path.
