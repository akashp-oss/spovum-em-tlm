# BangOps — Information Architecture (IA) & Database Schema

*Structural specifications for the BangOps web dashboard, database schema, role-based visibility, and system interaction models.*

---

## 1. System Topology Overview

BangOps operates on a two-tier interaction philosophy:
- **Write / Action Layer (100% Chat-First):** Team members log sickness, start focus timers, log hours, and query vendors directly via **Google Chat micro-agents**.
- **Read / Radiator Layer (Web Dashboard):** A clean, low-maintenance dashboard designed to answer questions visually in under 5 seconds.

```
                              ┌──────────────────────────┐
                              │  Google Chat Interface   │
                              │ (1:1 DMs with Personal   │
                              │       Agent Bot)         │
                              └────────────┬─────────────┘
                                           │
                                  Bidirectional API
                                           │
                                           ▼
┌──────────────────────────┐     ┌──────────────────────────┐
│    BangOps Dashboard     │<───>│   Supabase Cloud DB      │
│  (Next.js / Tailwind CSS)│     │  (Postgres 15 + Realtime)│
│  • Room 1: Today         │     └──────────────────────────┘
│  • Room 2: Projects      │                   ▲
│  • Room 3: Vendors       │                   │ Auto-updates
│  • (Founder Mode Toggle) │                   │
└──────────────────────────┘     ┌─────────────┴────────────┐
                                 │ Personal Google Sheets   │
                                 │ (Resource_Name.xlsx)     │
                                 └──────────────────────────┘
```

---

## 2. Web Dashboard — Exactly Three Rooms

### Room 1: Today (The Operational Pulse)
*The default view anyone opens to check studio availability and active focus.*
- **Block A: Who is Out Today:**
  - Names of team members marked sick or on leave + return date.
  - Sub-owner stand-in chips (e.g., *"Akash Pai (Sick) → Covered by: Sarah K."*).
- **Block B: My Active Projects:**
  - Filtered automatically to projects where the logged-in user is Lead Owner or Sub-Owner.
  - Health status chip (`Green`, `Amber`, `Red`), upcoming deadline, and Drive link.
- **Block C: Needs Attention (Founder & Lead Alert):**
  - Projects untouched for > 7 days (`last_update_at`).
  - Projects where a lead owner reported sick and the sub-owner declined coverage (escalated).

---

### Room 2: Master Projects Directory
*The single source of truth for all active client contracts.*
- **Table Columns:**
  1. `Project Name` (`<Client>: <Project>`, e.g. `STC: BPillar`, `Essent: Air Purifier`).
  2. `Team` (Industrial Design, Marketing, Engineering, or Hybrid).
  3. `Lead Owner` (Avatar + name).
  4. `Sub-Owner` (Avatar + name).
  5. `Status` (`Active`, `Blocked`, `Waiting on Vendor`, `Done`).
  6. `Health` (`Green`, `Amber`, `Red`).
  7. `Drive Link` (One-click jump to the client asset folder).
  8. `Last Activity` (Days since last logged sprint).
  9. `Credits Burned` *(Visible only in Founder Mode)*: Burned hours vs. monthly package budget.
- **Interactions:**
  - Fast search by client name or project keyword.
  - Filter by Team (`Industrial Design` | `Marketing` | `Engineering`).
  - Filter by Status (`Active` | `Blocked`).

---

### Room 3: Vendor Directory (Fabrication & Prototyping)
*Eliminates the founder bottleneck and dense quote spreadsheet parsing.*
- **Filter Bar:**
  - **Process Tag:** `SLA 3D Print`, `SLS 3D Print`, `FDM`, `CNC Machining`, `Sheet Metal`, `Injection Moulding`, `PCB Fabrication`.
  - **Material Tag:** `ABS`, `Aluminium 6061`, `Nylon PA12`, `Stainless Steel`, `FR4`.
  - **Price Band:** `Budget ($)`, `Balanced ($$)`, `Premium ($$$)`.
  - **Min Quality Rating:** `★ 1` to `★ 5`.
  - **Location:** `Bangalore`, `Coimbatore`, `Shenzhen`, `Mumbai`.
- **Vendor Cards / Table Row:**
  - Vendor Name & primary contact (phone/email).
  - Typical Lead Time (e.g. `3–5 business days`).
  - **Key Insights & Warnings:** (e.g. *"Best value for large ABS panels; 3DE excludes freight; avoid BOTAAT for large front enclosures due to 2x price markup"*).
  - Past Quote Benchmark Links (Direct link to reference PDF or sheet).

---

## 3. Database Schema (Supabase Postgres)

### Table 1: `people`
```sql
CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    team TEXT NOT NULL CHECK (team IN ('industrial_design', 'marketing', 'engineering', 'admin')),
    role TEXT NOT NULL DEFAULT 'team_member' CHECK (role IN ('team_member', 'founder', 'lead')),
    google_chat_id TEXT,
    personal_sheet_url TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'on_leave', 'sick')),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Table 2: `projects`
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_name TEXT NOT NULL,
    project_name TEXT NOT NULL,
    project_code TEXT UNIQUE NOT NULL, -- e.g. "STC: BPillar"
    team TEXT NOT NULL,
    lead_owner_id UUID REFERENCES people(id),
    sub_owner_id UUID REFERENCES people(id),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'blocked', 'waiting_on_vendor', 'completed')),
    health TEXT DEFAULT 'green' CHECK (health IN ('green', 'amber', 'red')),
    drive_link TEXT,
    credit_budget INT DEFAULT 0, -- Total credits allocated in plan
    credits_burned NUMERIC DEFAULT 0,
    last_update_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Table 3: `vendors`
```sql
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    processes TEXT[] NOT NULL, -- e.g. ['SLA 3D Print', 'CNC Machining']
    materials TEXT[] NOT NULL, -- e.g. ['ABS', 'Aluminium 6061']
    city TEXT,
    typical_lead_time_days INT,
    price_band TEXT CHECK (price_band IN ('budget', 'balanced', 'premium')),
    quality_rating INT CHECK (quality_rating BETWEEN 1 AND 5),
    notes TEXT, -- Critical learnings, pricing spread warnings
    contact_name TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    quote_folder_link TEXT,
    last_used_at TIMESTAMPTZ
);
```

### Table 4: `daily_logs`
```sql
CREATE TABLE daily_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES people(id),
    project_id UUID REFERENCES projects(id),
    log_date DATE NOT NULL DEFAULT CURRENT_DATE,
    hours_spent NUMERIC NOT NULL,
    task_description TEXT NOT NULL,
    formatted_client_log TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. Role-Based Permissions

| View / Field | Team Member | Founder |
|---|---|---|
| **View Today Availability & Leaves** | ✅ Yes | ✅ Yes |
| **View Active Projects, Owners & Drive Links** | ✅ Yes | ✅ Yes |
| **Search & Filter Vendors, Ratings, Notes** | ✅ Yes | ✅ Yes |
| **View Client Commercial Rates & Total Package Hours** | ❌ Hidden | ✅ Visible |
| **Create New Client Project & Assign Owners** | ❌ Read Only | ✅ Full Edit |
| **Add / Edit Vendor Pricing Benchmarks** | ✅ Yes | ✅ Yes |
