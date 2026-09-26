# Flow 04: Vendor Search & Quoting Intelligence

*Searching fabrication suppliers, materials, lead times, and avoiding pricing traps directly from chat or dashboard.*

---

## 1. Sequence Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant User as Designer / Engineer
    participant Bot as Agent / Dashboard Search
    participant DB as Supabase Postgres
    participant LLM as Groq / Gemini Flash

    User->>Bot: "Who is the best vendor for SLA ABS 3D printing for a large front panel?"
    Bot->>DB: Query vendors where 'SLA 3D Print' in processes AND 'ABS' in materials
    DB-->>Bot: Returns [Design Roots, Makenica, 3DE Tech, BOTAAT] + quote benchmark notes
    
    Bot->>LLM: Filter and highlight cost drivers & warnings
    LLM-->>Bot: Structured summary with specific warnings on BOTAAT's 2x markup on large panels
    
    Bot->>User: Renders Vendor Comparison Card with direct links to past quote files
```

---

## 2. Google Chat Interactive Card UI

### Vendor Recommendation Card
```
┌──────────────────────────────────────────────┐
│  🔍 Vendor Recommendation • SLA ABS 3D Print │
├──────────────────────────────────────────────┤
│ 🏆 Best Pick: Design Roots                   │
│ • Price: Budget ($) | Quality: ★★★★☆ (4.5)   │
│ • Lead Time: 3–4 Days | City: Bangalore      │
│ • Quoted Rate: ₹37,940 for large front panel │
│ • Contact: +91 98450 XXXXX (Mr. Ramesh)      │
│                                              │
│ ⚠️ Important Benchmark Warning:              │
│ Avoid BOTAAT for large enclosure panels.     │
│ In recent quotes, BOTAAT priced the front    │
│ panel at ₹81,240 (over 2x more expensive).   │
│                                              │
│ [ 📁 View Past Quotes ]  [ ✉️ Draft RFQ Email ]│
└──────────────────────────────────────────────┘
```
