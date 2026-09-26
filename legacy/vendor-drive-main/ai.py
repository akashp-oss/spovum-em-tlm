"""
The AI layer -- its job is to work the DRIVE, not to "read a vendor table".

Three things it does:
  1. scan_files()      -- instant keyword search across every file's index.
                          Pure Python, NO API key, always works. This also
                          pre-filters which files the reasoning model looks at,
                          so search stays fast and free even with hundreds of
                          spreadsheets.
  2. answer_over_files -- Gemini reads the matched rows and answers in plain
                          language, citing WHICH file / sheet / row the data is
                          in so you can jump straight to the real spreadsheet.
  3. search_web        -- Tavily finds NEW vendors on the web; Gemini formats
                          them. (Gemini never touches the live web itself.)
  + organize()         -- Gemini tells you what each folder holds / what looks
                          misplaced, so it can help you sort the drive.

Keys are optional. Without them, keyword search still works; the AI features
just tell you to add a free key. One free Google account + one free Tavily
account is all it ever needs -- see README.
"""
import os
import re

_configured = False


# --- Gemini plumbing ------------------------------------------------------
# If the chosen model name is retired by Google (a 404 "no longer available to
# new users"), we automatically fall through this list instead of breaking.
# Override the first choice with GEMINI_MODEL in .env.
FALLBACK_MODELS = [
    "gemini-flash-latest", "gemini-2.0-flash",
    "gemini-2.5-flash", "gemini-1.5-flash",
]


def _configure():
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "The Google AI library isn't installed. Run:  pip install -r requirements.txt  "
            "(or: pip install google-generativeai) and restart."
        )
    key = os.getenv("GEMINI_API_KEY", "")
    if not key or key.startswith("your-"):
        raise RuntimeError(
            "No Gemini key yet. Add a free one from aistudio.google.com to .env "
            "(GEMINI_API_KEY=...) and restart. Keyword search works without it."
        )
    global _configured
    if not _configured:
        genai.configure(api_key=key)
        _configured = True
    return genai


def _generate(system, prompt, as_json=False):
    """Run one generation, self-healing across model names if one is retired."""
    genai = _configure()
    candidates, seen = [], set()
    for name in [os.getenv("GEMINI_MODEL", "gemini-flash-latest")] + FALLBACK_MODELS:
        if name and name not in seen:
            seen.add(name); candidates.append(name)
    gcfg = {"response_mime_type": "application/json"} if as_json else None
    last = None
    for name in candidates:
        try:
            model = genai.GenerativeModel(name, system_instruction=system)
            resp = model.generate_content(prompt, generation_config=gcfg) if gcfg \
                else model.generate_content(prompt)
            return resp.text or ""
        except Exception as e:
            last = e
            s = str(e).lower()
            if any(k in s for k in ("not found", "404", "no longer available",
                                    "does not exist", "not supported", "unsupported")):
                continue  # this model is gone -> try the next name
            raise
    raise last if last else RuntimeError("No Gemini model available")


# --- 1. Keyword scan (no API, always on) ----------------------------------
def _tokens(query: str):
    return [t for t in re.split(r"[^a-z0-9]+", (query or "").lower()) if len(t) >= 2]


def scan_files(files, query, max_files=15, max_lines=8):
    """
    files: list of dicts with file_id, file_name, folder, search_text.
    Returns matches sorted by relevance:
      [{file_id, file_name, folder, score, snippets:[line, ...]}]
    """
    toks = _tokens(query)
    matches = []
    for f in files:
        hay_name = (f.get("file_name") or "").lower()
        text = f.get("search_text") or ""
        low = text.lower()
        # score = token hits in name (weighted) + hits in contents
        score = 0
        for t in toks:
            if t in hay_name:
                score += 5
            score += low.count(t)
        if not toks:  # empty query -> everything, unscored
            score = 1
        if score <= 0:
            continue
        # pull the most relevant lines
        snippets = []
        if toks:
            for line in text.split("\n"):
                ll = line.lower()
                if any(t in ll for t in toks):
                    snippets.append(line.strip())
                    if len(snippets) >= max_lines:
                        break
        matches.append({
            "file_id": f.get("file_id"),
            "file_name": f.get("file_name"),
            "folder": f.get("folder") or "",
            "score": score,
            "snippets": snippets,
        })
    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches[:max_files]


def _context_from_matches(matches, max_chars=14000):
    blocks = []
    for m in matches:
        loc = f"{m['folder']}/" if m["folder"] else ""
        head = f"### FILE: {loc}{m['file_name']}"
        body = "\n".join(m["snippets"]) if m["snippets"] else "(matched on file name)"
        blocks.append(head + "\n" + body)
    ctx = "\n\n".join(blocks)
    return ctx[:max_chars] if len(ctx) > max_chars else ctx


# --- 2. Reasoned answer over the matched files ----------------------------
def answer_over_files(query, matches, history=""):
    """Gemini answers the question and cites which file/sheet/row the data is in.
    `history` is a short transcript of the recent Q&A so follow-ups make sense."""
    if not matches:
        return ("Nothing in the drive matched that. Try different words, or upload "
                "the file it should be in.")
    context = _context_from_matches(matches)
    sys = (
        "You are the search-and-analysis assistant for a team's drive of vendor "
        "spreadsheets. Use ONLY the file excerpts below as your source of facts.\n"
        "- Answer directly and practically. If the user asks you to compare, rank, or "
        "pick (best price, best fit, most feasible vendor, etc.), reason over the rows "
        "and give a clear recommendation with the numbers behind it.\n"
        "- For every fact, name the exact file it came from (and the sheet/row tag like "
        "[Sheet1 | row 12] when present) so they can open it.\n"
        "- If a needed value is missing or blank in the data, say so plainly rather than "
        "guessing. Never invent contact details, prices, or vendors.\n"
        "- Be concise; use short bullet points only when they genuinely help.\n"
        "- IMPORTANT: You are ANSWERING only. You did NOT create folders, move files, or "
        "edit any spreadsheet in this reply. Never claim you performed such actions here. "
        "If the user asked you to DO something, tell them to phrase it as a direct command "
        "(e.g. 'add a row to <file>: ...') or use the buttons.\n"
    )
    if history:
        sys += "\nEARLIER IN THIS CONVERSATION (for context on follow-ups):\n" + history + "\n"
    sys += "\nFILE EXCERPTS:\n" + context
    return _generate(sys, query) or "No answer."


def explain_error(e) -> str:
    """Turn a raw Gemini/Tavily exception into a plain, actionable message."""
    s = str(e).lower()
    if "api key not valid" in s or "api_key_invalid" in s or "invalid api key" in s or "permission_denied" in s or "401" in s or "403" in s:
        return ("The AI key was rejected. Double-check GEMINI_API_KEY (or TAVILY_API_KEY) "
                "in your .env — copy it fresh from the provider, no quotes or spaces, then restart.")
    if "deadline" in s or "timeout" in s or "timed out" in s or "unavailable" in s or "503" in s:
        return "The AI provider timed out or was briefly unavailable. Try again in a moment."
    if "quota" in s or "resource_exhausted" in s or "429" in s or "rate limit" in s:
        return ("The provider says you've hit its own rate/quota limit right now (this is "
                "Google/Tavily's limit, separate from this app's daily cap). Wait a minute and "
                "retry, or check your usage in Google AI Studio / Tavily.")
    if "billing" in s or "balance" in s or "payment" in s:
        return ("The provider reports a billing/balance problem on the key. Check the account "
                "for that key (Gemini free tier needs no card; Tavily free tier has monthly credits).")
    return "AI call failed: " + str(e)[:300]


# --- 3. Web search for NEW vendors ----------------------------------------
def search_web(query, drive_hint=""):
    try:
        from tavily import TavilyClient
    except ImportError:
        raise RuntimeError("The Tavily library isn't installed. Run: pip install -r requirements.txt and restart.")
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if not tavily_key or tavily_key.startswith("your-"):
        raise RuntimeError(
            "No Tavily key yet. Add a free one from tavily.com to .env "
            "(TAVILY_API_KEY=...) and restart."
        )
    tv = TavilyClient(api_key=tavily_key)
    raw = tv.search(query=f"{query} supplier manufacturer contact",
                    search_depth="advanced", max_results=8, include_answer=False)
    snippets = []
    for r in raw.get("results", []):
        snippets.append(
            f"TITLE: {r.get('title','')}\nURL: {r.get('url','')}\n"
            f"CONTENT: {(r.get('content') or '')[:900]}"
        )
    web_context = "\n\n---\n\n".join(snippets) or "(no web results -- try other terms)"
    sys = (
        "You are a sourcing assistant. From the raw web results below, extract REAL "
        "vendors. Only use phone/email/website that literally appear in the results; "
        "never invent them. For each vendor use:\n"
        "VENDOR: ...\nCOMPANY: ...\nPHONE: (only if present)\nEMAIL: (only if present)\n"
        "WEBSITE: ...\nWHAT THEY OFFER: ...\nSOURCE: (which URL)\n\n"
        "End with a short SOURCING TIPS section. If a listing has no contact info, "
        "still list it and say 'visit website'.\n\nWEB RESULTS:\n" + web_context
    )
    return _generate(sys, query) or "No results."


# --- 4. Help sort the drive ----------------------------------------------
def organize(folder_blocks):
    """folder_blocks: text summary of folders and the files (+ column headers) in them."""
    sys = (
        "You help a user tidy a drive of spreadsheets. Given the folders and the files "
        "in each, briefly say what each folder appears to hold, point out files that "
        "look misplaced or duplicated, and suggest a cleaner folder structure. Be "
        "concise and practical."
    )
    return _generate(sys, folder_blocks) or ""


# --- 5. Turn a plain-English command into concrete actions ----------------
def plan(message, files, folders, history=""):
    """
    Ask the model to convert an instruction into a JSON list of actions the app
    can actually execute. Returns [] for questions or if parsing fails, so the
    caller can fall back to answering. NEVER guesses actions the user didn't ask
    for. The app (not the model) reports what actually happened, so it can't lie.
    Allowed ops:
      {"op":"create_folder","name": "..."}
      {"op":"move_file","file":"<existing file name>","folder":"<folder name or 'root'>"}
      {"op":"add_row","file":"<existing file name>","values":{"<column>":"<value>", ...}}
    """
    import json
    file_list = "\n".join(f"- {f['file_name']} (columns: {f.get('columns','?')})" for f in files) or "(none)"
    folder_list = ", ".join(fo["name"] for fo in folders) or "(none)"
    sys = (
        "You convert a user's instruction about their spreadsheet drive into a JSON array "
        "of actions to execute. Output JSON ONLY: {\"actions\":[ ... ]}.\n"
        "Allowed action objects:\n"
        '  {"op":"create_folder","name":"..."}\n'
        '  {"op":"move_file","file":"<exact existing file name>","folder":"<folder name, or \'root\'>"}\n'
        '  {"op":"add_row","file":"<exact existing file name>","values":{"<column header>":"<value>"}}\n'
        "Rules:\n"
        "- Use ONLY the exact file names and folders listed below. Match 'the only file' / vague "
        "references to the actual file name.\n"
        "- For add_row, map the user's details onto the file's real column headers. Use 'n/a' where "
        "the user says n/a; leave unknown columns out.\n"
        "- Include ONLY actions the user explicitly asked for, in order. If the message is a QUESTION "
        "or asks for analysis (not a change), return {\"actions\":[]}.\n"
        f"\nFILES:\n{file_list}\nFOLDERS: {folder_list}\n"
    )
    if history:
        sys += "\nRecent context:\n" + history + "\n"
    try:
        raw = _generate(sys, message, as_json=True)
        data = json.loads(raw)
        acts = data.get("actions") if isinstance(data, dict) else data
        return acts if isinstance(acts, list) else []
    except Exception:
        return []
