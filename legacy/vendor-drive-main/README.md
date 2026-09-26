# Vendor Drive

A **shared online drive** for your team's spreadsheets, with an AI that can search across every file and even move things around for you. You put an Excel in, it stays a whole Excel; anyone you give the link + password to sees the exact same files and can ask the AI about any of them — like a private Google-Drive-plus-ChatGPT for your vendor data.

---

## Your questions, answered straight

**How do my friends get access? Do we share one thing?**
Yes — one system, one link, one password. You deploy it once (10 min, free — steps below) and get a URL like `https://vendor-drive.onrender.com`. You share that URL + the password. A friend opens the link, types the password, and they're in — **2 clicks**. They see the same drive you do and can immediately ask the AI or open any file. No installs, no accounts, no setup on their side.

**"If it's stored locally with me and the AI just reads it, that's wrong."**
Correct, and that's now fixed. Files are **not** on your laptop. Every uploaded file is stored **inside the shared database** (a free cloud Postgres from Neon). The app on Render is just a stateless window onto that database. So the data belongs to *the system*, not to any one person's computer — your laptop can be off and your friends still have full access.

**Where is it stored online, and whose?**
It's **your own** system, hosted on free infrastructure you own:
- **Render** (free) runs the app — the website everyone opens.
- **Neon** (free) is the Postgres database that holds the files themselves *and* the search index.
Both are yours, created with your email in 10 minutes. It's not Google's drive or mine — nobody else can see it without your password.

**How much space (GB)?**
The free Neon database is **0.5 GB**. Spreadsheets are tiny (a 500-row Excel is ~30–80 KB), so that's **roughly 5,000–10,000 spreadsheets** — comfortably "hundreds of Excels" with huge room to spare. If you ever outgrow it, you paste in a bigger Postgres URL (Neon's paid tiers, or any Postgres) — one line in the settings, no code change. The Home header always shows how much you've used.

**How does the AI actually search a sheet?**
When a file is uploaded, the app reads it **once** and writes a plain-text index of it — every row tagged with where it sits, e.g. `[Suppliers | row 12] Vendor Name=Latha S | Phone=9812098120`. That index is stored next to the file in the same shared database. So when anyone asks *"what's Latha's number?"*, the AI (Gemini) reads those indexed rows and answers **with the exact file, sheet and row** it found it in — for everyone, because everyone shares that one database. If the drive doesn't have the answer, it automatically searches the **web** (Tavily) instead. The original file is never changed — download it back and it's byte-for-byte your original.

---

## What the AI can do (it doesn't just "read")

From the **Ask AI** tab, in plain English — and it **actually does these**, then tells you exactly what it did (it never claims a change it didn't make):
- **Answer** — "who supplies M6 bolts?", "which file has ACME's email?" → cites the file/row.
- **Create folders** — *"create folder Q1 Quotes"* → made.
- **Move files** — *"move contacts.csv into Vendors"* → moved (unless locked).
- **Edit the real spreadsheet** — *"add vendor 5 Shenzhen Smart Care to Vendor_Feasibility, response n/a, costing n/a"* → it appends that row **into the actual .xlsx stored in the drive**. Download the file afterwards and the row is there.
- **Web fallback** — not in your files? It searches the web to answer.
- **Sort the drive** — "Help me sort" button.

You can also edit **by hand**: click a file → **＋ Add row** (fill the columns, it appends to the real sheet), or for small sheets edit cells inline and **Save changes**. Either way it changes the one shared copy in the database, so everyone sees it — same locally and deployed.

## Who can change what — the Lock + delete password

- **Unlocked** file/folder: anyone with the password can upload into it, edit it, add rows, or move it.
- **Deleting** anything **always asks for the password again** — so nobody wipes data by accident.
- **🔒 Lock** a file or folder to freeze it: once locked, nobody can move, edit, add-into, or delete it until it's unlocked. **Locking/unlocking asks for the password** — that's the admin control.

## "Will it work when deployed, and did it edit the true file?"

Yes to both, and here's why you can trust it:
- The file's **real bytes live in the database**. "Add row" / edits rewrite those bytes and re-index — so the change is in the actual .xlsx, and **Download original** proves it. This works identically on your laptop (SQLite) and deployed (Neon Postgres) because it's the same code path either way.
- The **model self-heals**: if Google retires a model name (the `404 … no longer available` you hit), the app automatically tries the next working model instead of breaking. Set `GEMINI_MODEL` in `.env` only if you want to pin one.
- The AI **cannot lie about edits**: when you give it a command, the app runs the real action and the reply is built from what actually happened — not from the model's imagination.

---

## Setup — the easy path (share with friends)

You need two free keys you already have (Gemini + Tavily) and two free accounts (Render + Neon). ~10 minutes, once.

1. **Neon** (the database): sign up free at https://neon.tech → create a project → copy the **connection string** (starts `postgresql://…`).
2. **GitHub**: put this folder in a **private** repo.
3. **Render**: https://render.com → **New → Blueprint** → pick your repo. It reads `render.yaml` automatically. When it asks for values, paste:
   - `SITE_PASSWORD` — the shared password you'll give friends
   - `SECRET_KEY` — any long random text
   - `GEMINI_API_KEY` — your key (https://aistudio.google.com/apikey)
   - `TAVILY_API_KEY` — your key (https://tavily.com)
   - `DATABASE_URL` — the Neon string from step 1
4. Deploy. You get a URL. **Share the URL + password.** Done — that's the whole system.

## Setup — try it on your own machine first (optional, 2 steps)

```bash
./setup.sh        # Mac/Linux   (Windows: double-click setup.bat)
# then set SITE_PASSWORD + paste your 2 keys in the .env it created, and:
source venv/bin/activate && python app.py   # open http://localhost:8000
```
Locally it uses a simple file database so you can kick the tires. It even runs before you add the AI keys — upload, browse, download, keyword search, folder-create and move all work; only the written AI answers wait for the Gemini key.

---

## The files in here

| File | What it does |
|---|---|
| `app.py` | The web server + every API route |
| `database.py` | The shared tables — folders, files (**bytes stored here**), team, inbox, quotas |
| `indexer.py` | Reads each file once to make it searchable — never edits it |
| `ai.py` | Keyword scan + Gemini answers + Tavily web search |
| `notify.py` | Optional email copy of pings (the in-app Inbox always works) |
| `static/index.html` | The whole interface, one file |
| `render.yaml` | One-click deploy config for Render |
| `watch.py` | Optional desktop popup for pings — you don't need it |

## If the AI button gives an error

The app never hides a real failure. When Gemini or Tavily rejects a call, the **exact reason appears in the chat** (red), e.g.:
- *"The AI key was rejected"* → your `GEMINI_API_KEY` is wrong or has a stray space/quote. Copy it fresh from https://aistudio.google.com/apikey and restart.
- *"hit its own rate/quota limit"* → that's Google/Tavily's own limit (separate from this app's daily cap) — wait a minute.
- The number next to "This app's own daily cap" is **just this app's counter**, not your Google balance — and it now only counts calls that actually **succeeded**, so a rejected key never burns it.

Tip: `python app.py` prints on startup whether each key is set. If it says `NOT SET`, the app didn't find your key in `.env`.

## Local memory (context for better follow-ups)

The Ask tab remembers your recent questions **in your own browser only** (nothing is shared or sent anywhere except back to the AI as context for your next question). So you can ask a follow-up like *"and their email?"* and it knows who you meant. "Clear chat" wipes it. It's per-person and per-device — safe by design.

## Good to know
- Auth is **one shared password**, not per-person logins — that's the design (2-click access for friends). The user menu is just for "who did what" labels and pings.
- Daily AI caps (in `.env`) mean the free tiers can never be exceeded — **no bill, ever**. Tavily's free web search (~30/day here) is the tightest limit.
- Free Render instances sleep after ~15 min idle and take ~30s to wake on the next visit — a one-time delay, not downtime. Your data is safe in Neon regardless.
