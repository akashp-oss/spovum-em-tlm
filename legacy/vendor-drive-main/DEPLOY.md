# Deploy & share the Vendor Drive

Goal: a live URL your colleagues open, log in with one password, and use — while your laptop is off. All on free tiers. ~15 minutes, once.

You'll use three free accounts: **GitHub** (holds the code), **Neon** (the shared database), **Render** (runs the website).

---

## Step 1 — Neon (the shared database, ~3 min)

This is where the files AND the search index live, so the data belongs to the system, not to anyone's computer.

1. Go to https://neon.tech → sign up (free, no card).
2. Click **Create project** → accept the defaults → **Create**.
3. On the project dashboard, find **Connection string** and **copy it**. It looks like:
   `postgresql://user:password@ep-xxxx.aws.neon.tech/neondb?sslmode=require`
4. Keep that string handy for Step 3. (That's the whole database step — nothing to install.)

## Step 2 — GitHub (holds the code, ~4 min)

Render deploys from a Git repo. If you've never used GitHub:

1. Go to https://github.com → sign up.
2. Click **+ → New repository** → name it `vendor-drive` → choose **Private** → **Create repository**.
3. On the new repo page, click **uploading an existing file** (the link in "…or upload an existing file").
4. Drag in **all the files from this folder** (the whole `vendor-drive` folder contents — `app.py`, `static/`, everything). Do **not** upload a `.env` file if you made one.
5. Click **Commit changes**.

(If you're comfortable with git on the command line, `git init && git add . && git commit -m "vendor drive" && git push` to a new private repo does the same thing.)

## Step 3 — Render (runs it, ~5 min)

1. Go to https://render.com → sign up → **connect your GitHub** when it asks.
2. Click **New → Blueprint**.
3. Pick your `vendor-drive` repo. Render reads `render.yaml` and sets everything up.
4. It will ask you to fill in two secrets (the rest are automatic):
   - **SITE_PASSWORD** — the password you'll give your team. Pick a good one.
   - **GEMINI_API_KEY** — your key from https://aistudio.google.com/apikey
   - **TAVILY_API_KEY** — your key from https://tavily.com
   - **DATABASE_URL** — paste the Neon string from Step 1.
   *(SECRET_KEY is generated for you; PYTHON_VERSION is preset.)*
5. Click **Apply / Deploy**. Wait ~2–3 minutes for the first build.
6. You get a URL like `https://vendor-drive.onrender.com`. Open it → log in with SITE_PASSWORD. Done.

---

## Step 4 — Share with your team

Send them **two things**: the **URL** and the **password**. That's it. They open the link, type the password, and they're in — same drive, same files, 2 clicks. Nothing to install.

Tip: put the URL + password somewhere your team already looks (a pinned chat message, a shared note). Anyone with both has full access; only **delete** and **lock/unlock** re-ask for the password.

## Good to know once it's live

- **Your laptop can be off.** The site and data live on Render + Neon.
- **First visit after idle is slow.** Free Render instances sleep after ~15 min unused and take ~30–50 s to wake on the next click — a one-time delay, not downtime. (A paid instance, ~$7/mo, stays awake if that ever annoys the team.)
- **Data is safe across redeploys** because it's in Neon, not on Render's disk.
- **Storage:** Neon free is 0.5 GB ≈ thousands of spreadsheets. The Home header shows usage.

---

## Developing it live over time (the nice part)

You keep improving it without disturbing anyone:

1. Edit the code (or ask me to) and test locally: `python app.py`.
2. When happy, push the change to your GitHub repo (upload the changed file, or `git push`).
3. **Render auto-deploys** the new version in ~2 minutes. Your team just refreshes — their data is untouched (it's in Neon).

That's the whole loop: **edit → push → auto-deploy.** No downtime worth worrying about, and you can roll back to any previous deploy from Render's dashboard in one click if something's off.

**Want to try changes safely first?** Make a second Render service from the same repo pointed at a *second* free Neon database — that's a private "staging" copy to test on before your team sees it. Optional; most people just push to the one.

**Adding features later** (a real login per person, comments on a file, an audit log of who changed what, export, charts…): tell me what you want and I'll add it to the code the same way — you push, Render deploys.
