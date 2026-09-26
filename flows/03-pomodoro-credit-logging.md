# Flow 03: Pomodoro Focus Timer & Credit Logging

*Lightweight 2–3 hour focus sprints in Google Chat with automated timesheet logging.*

---

## 1. Sequence Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant User as Team Member (Google Chat)
    participant Bot as Personal Agent Bot
    participant Timer as Background Cron / Worker
    participant LLM as Groq / Gemini Flash
    participant Sheet as Personal Google Sheet

    User->>Bot: "Starting 2.5 hours on STC BPillar door cap 3D CAD"
    Bot->>Timer: Set reminder for T + 2.5 hours
    Bot->>User: "Timer started for 2.5h on STC: BPillar! 🎯"

    Note over User,Timer: 2.5 Hours Pass...

    Timer->>Bot: Trigger timer completion
    Bot->>User: Interactive Card: "How did the 2.5h sprint go on STC: BPillar?"
    
    User->>Bot: "Finished door cap and added NFC sensor mount clips"
    Bot->>LLM: Format into client-facing deliverable log
    LLM-->>Bot: "Completed door cap CAD modeling and integrated NFC sensor mounting bracket."
    
    Bot->>Sheet: Append to today's row: [STC: BPillar | 2.5 | Formatted Log]
    Bot->>User: "Logged 2.5 credits on your Resource Sheet! ✅"
```

---

## 2. Google Chat Interactive Card UI

### A. Focus Sprint Completion Prompt
```
┌──────────────────────────────────────────────┐
│  ⏱️ Sprint Complete • STC: BPillar (2.5h)     │
├──────────────────────────────────────────────┤
│ Your 2.5-hour focus block is complete.       │
│ Did you wrap up your planned CAD milestones? │
│                                              │
│ [ ✅ Complete & Log ]    [ ⏱️ Need +1 Hour ] │
│ [ 🔄 Switch Project ]    [ ❌ Discard Timer ]│
└──────────────────────────────────────────────┘
```

### B. Auto-Formatted Timesheet Write Confirmation
```
┌──────────────────────────────────────────────┐
│  📊 Credits Logged Successfully              │
├──────────────────────────────────────────────┤
│ Appended to Resource_Akash_Pai.xlsx:         │
│                                              │
│ • Date: 19 Sep 2026                          │
│ • Project: STC: BPillar                      │
│ • Hours: 2.5 Credits                         │
│ • Client Log: "Completed door cap CAD        │
│   modeling and integrated NFC sensor mount." │
│                                              │
│ Today's Total: 5.5 / 7.0 Credits             │
└──────────────────────────────────────────────┘
```
