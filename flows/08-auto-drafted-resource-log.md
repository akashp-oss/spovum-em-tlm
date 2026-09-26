# Flow 08: Auto-Drafted Resource Log (approve, don't type)

*Fixes "resource-sheet amnesia." The agent writes today's rows from signals that already exist, and the person approves them in one click. Replaces the timer-heavy Flow 03 as the default. Pomodoro timers become optional.*

---

## 1. Signals used (no screen or app tracking)

| Signal | Source | Example → row |
|---|---|---|
| Chat notes to the agent | BangOps chat | "door cap + NFC clips, 2.5h" → `STC: BPillar · 2.5 · Completed door cap CAD and added NFC sensor mounting clips` |
| Client emails sent today | Gmail `in:sent after:<today>` to client domains | Sent files to Essent → `Essent: Air Purifier · ? · Shared onboarding screen files for review` |
| Calendar events | CalendarApp, today | "Stand-up" 30 min → `Z_Admin: General · 0.5 · StandUp Meet` |
| *(later)* Drive edits | Files modified today in project folders | "Nexa dashboard v4.fig" → hint for `Nexa: NEXA Marketing` |

Hours come **only** from what the person said or from calendar durations. Otherwise the field is left blank and highlighted. **Hours are never invented.**

## 2. Sequence

```mermaid
sequenceDiagram
    autonumber
    participant T as Trigger 17:30 (runs as user)
    participant S as Signals (chat log, sent mail, calendar)
    participant L as LLM
    participant C as Private Chat space
    participant U as User (BangOps page → Today)
    participant R as User's Resource Sheet

    T->>S: Collect today's signals
    T->>L: Merge into rows [project_code, hours|null, client-ready log], dedupe
    T->>C: "Today's log is ready: 4 rows, 6.5h, 1 missing hours. [Review]"
    U->>U: Edit / tick rows
    U->>R: Approve → write to month tab, today's row, next empty triplet; set Total Hours
```

## 3. Writing into the existing sheet format
- Find the tab named for the month (`Sep 2026`) and the row where `Date` = today.
- Find columns by **header name** (`Project N`, `Hours N`, `Log N`), not by position.
- Fill the next empty triplet. Never overwrite a filled one. If the same project already has a row today, offer to **merge** instead.
- Set `Total Hours` if it's a plain value. If it's a formula, leave it alone.
- `project_code` must match an entry in the Studio Brain Projects tab, which is what the sheet's dropdowns expect.
- Log text style: past tense, specific, client-readable, ≤ 90 characters (matches the existing entries like "Settings Screen + Changes to error states + Replacing Renders").

## 4. Nudges
- 17:30 card. If nothing is approved by 10:00 the next morning, send one reminder. Then stop.
- A missed day stays in the "Today" panel as "Yesterday, not logged" so it can be approved later.
- Leave days (from Flow 01, later) → write `Leave = TRUE`, 0 hours.
