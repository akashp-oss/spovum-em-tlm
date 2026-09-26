# Flow 05: SOP & Email Drafting Assistant

*Hardcoding "The Spine" and the 11 Communication Commandments into agent drafts.*

---

## 1. Sequence Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant User as Team Member (Google Chat)
    participant Bot as Personal Agent Bot
    participant SOP as SOP Prompt Injection ("The Spine" + 11 Commandments)
    participant LLM as Mistral AI / Groq

    User->>Bot: "Draft an email to Nexa client: Sent new landing page designs, changed nav to match mobile flow, takes 6 credits"
    Bot->>SOP: Load Commandments (Spine: What / Why / Benefit; Quantify effort; Next step)
    Bot->>LLM: Generate email applying strict SOP guidelines
    LLM-->>Bot: Formatted professional draft
    
    Bot->>User: Displays draft in Google Chat Card with [ Copy ] and [ Revise ] buttons
```

---

## 2. Google Chat Interactive Card UI

### Client Email Draft Card
```
┌──────────────────────────────────────────────┐
│  ✉️ SOP Email Draft • Nexa Marketing         │
├──────────────────────────────────────────────┤
│ Subject: Project Update: Revised Landing     │
│          Page Navigation & Mobile IA         │
│                                              │
│ Dear Nexa Team,                              │
│                                              │
│ [WHAT]                                       │
│ We have completed the revised landing page   │
│ layouts and updated the top navigation bar.  │
│                                              │
│ [WHY]                                        │
│ This redesign directly aligns the desktop    │
│ hierarchy with the new mobile user flows     │
│ discussed in our review.                     │
│                                              │
│ [BENEFIT & EFFORT]                           │
│ This change streamlines device onboarding    │
│ and eliminates drop-off. Total effort logged │
│ is 6 hours (6 credits) against your monthly  │
│ package.                                     │
│                                              │
│ [NEXT STEP]                                  │
│ Please review the attached Figma prototype:  │
│ [Figma Link]. Could you confirm sign-off by  │
│ Thursday 3 PM so we can initiate export?     │
│                                              │
│ [ 📋 Copy Draft ]      [ 🔄 Make Shorter ]   │
└──────────────────────────────────────────────┘
```
