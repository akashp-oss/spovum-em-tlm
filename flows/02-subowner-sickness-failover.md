# Flow 02: Sub-Owner Sickness Failover Protocol

*Autonomous capacity routing when a primary project owner reports sick.*

---

## 1. Sequence Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Event as Leave Event (from Flow 01)
    participant Master as Master Orchestrator
    participant DB as Supabase DB
    participant SubOwner as Sub-Owner (Google Chat)
    participant Founders as Founders Space (Google Chat)

    Event->>Master: Owner Akash Pai is SICK
    Master->>DB: Query active projects where lead_owner = Akash
    DB-->>Master: Project "STC: BPillar" (Sub-Owner: Sarah K.)
    
    Master->>SubOwner: Nudge Card: "Akash is out sick today on STC: BPillar. Can you cover?"
    
    alt Sub-Owner Accepts Coverage
        SubOwner->>Master: Click [ ✅ I Can Cover ]
        Master->>DB: Set temp_active_lead = Sarah K.
        Master->>SubOwner: "Thanks Sarah! Here is the Drive folder and yesterday's log: [Drive Link]"
    else Sub-Owner at Capacity
        SubOwner->>Master: Click [ ❌ My Plate is Full ]
        Master->>Founders: ⚠️ ALERT: "Akash is sick on STC: BPillar. Sarah is at full capacity. Immediate founder reallocation required!"
        Founders->>Master: Reassign to [ John D. ]
        Master->>DB: Update lead assignment
    end
```

---

## 2. Google Chat Interactive Card UI

### Sub-Owner Stand-in Request Card
```
┌──────────────────────────────────────────────┐
│  ⚠️ Project Coverage Request                 │
├──────────────────────────────────────────────┤
│ Hey Sarah, Akash is out sick today.          │
│                                              │
│ Project: STC: BPillar                        │
│ Next Milestone: Enclosure CAD Review         │
│ Drive Folder: drive.google.com/...           │
│                                              │
│ Do you have capacity to cover urgent tasks   │
│ on this project today?                       │
│                                              │
│ [ ✅ Yes, I Can Cover ]  [ ❌ Plate is Full ]│
└──────────────────────────────────────────────┘
```

### Founder Escalation Card (Triggered if Sub-owner declines)
```
┌──────────────────────────────────────────────┐
│  🚨 Urgent Project Coverage Alert            │
├──────────────────────────────────────────────┤
│ Project: STC: BPillar                        │
│ Lead Owner: Akash Pai (Out Sick)             │
│ Sub-Owner: Sarah K. (Declined - At Capacity) │
│                                              │
│ Action Required: Please assign a temporary   │
│ lead or notify client of schedule shift.     │
│                                              │
│ [ 🔄 Reassign to Colleague ] [ 📩 View Thread]│
└──────────────────────────────────────────────┘
```
