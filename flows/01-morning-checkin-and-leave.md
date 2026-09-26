# Flow 01: Morning Check-in & Sickness Reporting

*The daily automated check-in initiated by the personal agent on Google Chat.*

---

## 1. Sequence Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Cron as Cron Trigger (09:30 AM)
    participant Bot as Personal Agent Bot
    participant User as Team Member (Google Chat)
    participant Jev as TypeSafe Jev (Classifier)
    participant DB as Supabase DB
    participant Sheet as Personal Resource Sheet

    Cron->>Bot: Trigger morning routine for user
    Bot->>User: "Good morning Akash! Heading into the studio today?"
    
    alt User is Working
        User->>Bot: "Yes, in studio today. Working on Enclosure CAD for STC BPillar."
        Bot->>Jev: Classify Intent
        Jev-->>Bot: { intent: "working", project: "STC: BPillar", task: "Enclosure CAD" }
        Bot->>DB: Set status = 'active', today_focus = 'STC: BPillar'
        Bot->>User: "Awesome. Have a great focus day! I'll check back in 2–3 hours."
    else User is Sick / On Leave
        User->>Bot: "No, feeling sick with a fever today. Can't make it."
        Bot->>Jev: Classify Intent
        Jev-->>Bot: { intent: "sick_leave", reason: "fever" }
        Bot->>DB: Set status = 'sick', leave_date = CURRENT_DATE
        Bot->>Sheet: Write Leave = True, Total Hours = 0 on today's row
        Bot->>User: "Take care and rest up Akash! I've marked your sheet and alerted your project teammates."
        Note over Bot,DB: Triggers Flow 02 (Sub-Owner Sickness Failover)
    end
```

---

## 2. Google Chat Interactive Card UI

### A. Morning Check-in Card (Pushed at 09:30 AM)
```
┌──────────────────────────────────────────────┐
│  ☀️ BangOps Assistant • Morning Check-in     │
├──────────────────────────────────────────────┤
│ Good morning Akash! Heading into the studio  │
│ today?                                       │
│                                              │
│ [ 🏢 Yes, In Studio ]   [ 🏠 Remote ]        │
│ [ 🤒 Sick Leave ]       [ 🏖 Personal Leave ]│
└──────────────────────────────────────────────┘
```

### B. Sick Leave Confirmation Card
```
┌──────────────────────────────────────────────┐
│  🤒 Leave Recorded                           │
├──────────────────────────────────────────────┤
│ Rest up Akash! We've got your back today.    │
│                                              │
│ • Resource Sheet: Marked Leave = True (0h)   │
│ • Active Projects: STC: BPillar, Nexa        │
│ • Sub-owner Sarah has been alerted to cover. │
│                                              │
│ Need to pass a quick voice/text note to team?│
│ [ ✍️ Add a Quick Note ]                       │
└──────────────────────────────────────────────┘
```
