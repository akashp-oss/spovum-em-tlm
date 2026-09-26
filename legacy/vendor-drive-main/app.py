"""
Vendor Drive -- a shared drive for your spreadsheets, with an AI that can
search across all of them.

Run:  python app.py     (then open http://localhost:8000)

The idea, kept deliberately simple:
  * A file is stored AS-IS. Uploading an Excel keeps the Excel -- it is not
    shredded into database rows. Make folders, drop hundreds of files in,
    download any of them back untouched.
  * The AI works the drive: it searches every file's contents and tells you
    which file / sheet / row a piece of data is in, finds new vendors on the
    web, and can help sort your folders.
  * One shared password = full access. Share the password, they're in.
  * Only DELETE is locked -- it asks for the password again (admin action).
  * Pings land in an in-app Inbox. No Telegram, no bots, no external setup.
    The only thing you ever add is a free Gemini + Tavily key for the AI.
"""
import os
import re
import uuid
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import List

from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
_env_found = load_dotenv(dotenv_path=_ENV_PATH, override=True, encoding="utf-8-sig")

from fastapi import (
    Depends, FastAPI, File, Form, HTTPException, Header, UploadFile, Request, Cookie,
    Response,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session as DBSession
from itsdangerous import URLSafeSerializer

from database import (
    Folder, StoredFile, TeamMember, Notification, SearchHistory,
    get_db, init_db, quota_status, bump_quota, per_user_limit, seed_members,
    REASONING_DAILY_LIMIT, WEB_SEARCH_DAILY_LIMIT,
)
import indexer
import ai as ai_layer
from notify import notify_member

# --- Config ---------------------------------------------------------------
SITE_PASSWORD = os.getenv("SITE_PASSWORD", "changeme123")
SECRET = os.getenv("SECRET_KEY", "vendor-drive-" + SITE_PASSWORD)
serializer = URLSafeSerializer(SECRET)
BASE_DIR = Path(__file__).resolve().parent
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)


@contextmanager
def _tempfile_from(blob: bytes, ext: str):
    """Write bytes to a short-lived temp file so path-based readers can use them.
    Files live IN THE DATABASE, not on disk -- this is just a scratch copy."""
    tf = tempfile.NamedTemporaryFile(suffix=ext or ".dat", delete=False)
    try:
        tf.write(blob or b"")
        tf.flush(); tf.close()
        yield tf.name
    finally:
        try:
            os.remove(tf.name)
        except Exception:
            pass


def lifespan_startup():
    # Never let a startup hiccup crash-loop the whole site. If something here
    # fails, the app still boots and surfaces the error per-request instead.
    try:
        init_db()
        db = next(get_db())
        try:
            seed_members(db)
        finally:
            db.close()
    except Exception as e:
        print(f"[STARTUP] non-fatal: {e}")


app = FastAPI(title="Vendor Drive")


@app.on_event("startup")
def _startup():
    lifespan_startup()


app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# --- Auth: each person logs in as their own account -----------------------
def check_auth(token: str = Cookie(None), db: DBSession = Depends(get_db)):
    """Returns the logged-in user {id, name, admin}, or 401.

    A session is only valid if it carries a real account id (uid) that still
    exists. This rejects the old shared-password cookies AND deleted accounts,
    so nobody can act anonymously and renames/role changes take effect at once.
    """
    if not token:
        raise HTTPException(401, "Please log in")
    try:
        data = serializer.loads(token)
    except Exception:
        raise HTTPException(401, "Invalid session")
    uid = data.get("uid")
    if data.get("ok") is not True or not uid:
        raise HTTPException(401, "Please log in")
    m = db.query(TeamMember).filter(TeamMember.id == uid).first()
    if not m:
        raise HTTPException(401, "Your account no longer exists — log in again.")
    return {"id": m.id, "name": m.name, "admin": bool(m.is_admin)}


def require_admin(user=Depends(check_auth)):
    if not user.get("admin"):
        raise HTTPException(403, "Admins only.")
    return user


@app.get("/", response_class=HTMLResponse)
async def root():
    return (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/api/accounts")
def accounts(db: DBSession = Depends(get_db)):
    """Public: the list of names for the login dropdown (no passwords)."""
    return [{"id": m.id, "name": m.name, "admin": bool(m.is_admin)}
            for m in db.query(TeamMember).order_by(TeamMember.name).all()]


@app.post("/api/login")
async def login(req: Request, db: DBSession = Depends(get_db)):
    d = await req.json()
    name = (d.get("name") or "").strip()
    password = d.get("password") or ""
    m = db.query(TeamMember).filter(TeamMember.name == name).first()
    if not m or (m.password or "") != password:
        raise HTTPException(401, "Wrong name or password")
    token = serializer.dumps({"ok": True, "uid": m.id, "name": m.name, "admin": bool(m.is_admin)})
    resp = JSONResponse({"ok": True, "name": m.name, "admin": bool(m.is_admin)})
    resp.set_cookie("token", token, httponly=True, samesite="lax", max_age=86400 * 30)
    return resp


@app.post("/api/logout")
async def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("token")
    return resp


@app.get("/api/check")
async def check(token: str = Cookie(None), db: DBSession = Depends(get_db)):
    try:
        d = serializer.loads(token)
        uid = d.get("uid")
        if d.get("ok") and uid:
            m = db.query(TeamMember).filter(TeamMember.id == uid).first()
            if m:
                return {"ok": True, "name": m.name, "admin": bool(m.is_admin)}
    except Exception:
        pass
    return {"ok": False}


# --- Folders --------------------------------------------------------------
def _key_ready(name):
    v = os.getenv(name, "")
    return bool(v) and not v.startswith("your-")


def _per_user_cap(db, kind):
    """Each member's daily share of the team's total AI budget."""
    n = db.query(TeamMember).count() or 1
    total = REASONING_DAILY_LIMIT if kind == "reasoning" else WEB_SEARCH_DAILY_LIMIT
    return per_user_limit(total, n)


def _folder_name(db, fid):
    if not fid:
        return ""
    f = db.query(Folder).filter(Folder.id == fid).first()
    return f.name if f else ""


@app.get("/api/folders")
def list_folders(_=Depends(check_auth), db: DBSession = Depends(get_db)):
    out = []
    for f in db.query(Folder).order_by(Folder.name).all():
        count = db.query(StoredFile).filter(StoredFile.folder_id == f.id).count()
        out.append({"id": f.id, "name": f.name, "file_count": count,
                    "locked": bool(f.locked),
                    "created_by": f.created_by or "", "created_at": str(f.created_at or "")})
    root_count = db.query(StoredFile).filter(StoredFile.folder_id.is_(None)).count()
    return {"folders": out, "root_file_count": root_count}


@app.post("/api/folders")
async def create_folder(req: Request, user=Depends(check_auth), db: DBSession = Depends(get_db)):
    d = await req.json()
    name = (d.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Folder name required")
    existing = db.query(Folder).filter(Folder.name == name).first()
    if existing:
        return {"id": existing.id, "name": existing.name}
    f = Folder(name=name, created_by=user["name"])
    db.add(f); db.commit(); db.refresh(f)
    return {"id": f.id, "name": f.name}


@app.put("/api/folders/{fid}")
async def rename_folder(fid: int, req: Request, _=Depends(check_auth), db: DBSession = Depends(get_db)):
    d = await req.json()
    f = db.query(Folder).filter(Folder.id == fid).first()
    if not f:
        raise HTTPException(404)
    if f.locked:
        raise HTTPException(423, "This folder is locked. Unlock it first.")
    name = (d.get("name") or "").strip()
    if name:
        f.name = name; db.commit()
    return {"id": f.id, "name": f.name}


@app.put("/api/folders/{fid}/lock")
def lock_folder(fid: int, _=Depends(require_admin), db: DBSession = Depends(get_db)):
    """Toggle a folder's lock. Admins only."""
    f = db.query(Folder).filter(Folder.id == fid).first()
    if not f:
        raise HTTPException(404)
    f.locked = not bool(f.locked); db.commit()
    return {"id": f.id, "locked": f.locked}


@app.delete("/api/folders/{fid}")
def delete_folder(fid: int, _=Depends(require_admin), db: DBSession = Depends(get_db)):
    """Deletes the folder AND the files inside it. Admins only; blocked if locked."""
    f = db.query(Folder).filter(Folder.id == fid).first()
    if not f:
        raise HTTPException(404)
    if f.locked:
        raise HTTPException(423, "This folder is locked. Unlock it first.")
    files = db.query(StoredFile).filter(StoredFile.folder_id == fid).all()
    if any(sf.locked for sf in files):
        raise HTTPException(423, "This folder has locked files inside. Unlock them first.")
    for sf in files:
        db.delete(sf)
    db.delete(f); db.commit()
    return {"ok": True, "deleted_files": len(files)}


# --- Files ----------------------------------------------------------------
def file_out(f, db):
    return {
        "file_id": f.file_id,
        "file_name": f.file_name,
        "folder_id": f.folder_id,
        "folder_name": _folder_name(db, f.folder_id),
        "ext": f.ext,
        "size_bytes": f.size_bytes,
        "size_h": _human_size(f.size_bytes),
        "sheet_count": f.sheet_count,
        "row_count": f.row_count,
        "uploaded_by": f.uploaded_by or "",
        "locked": bool(f.locked),
        "created_at": str(f.created_at or ""),
        "download_url": f"/api/files/{f.file_id}/download",
    }


def _human_size(n):
    n = n or 0
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


@app.post("/api/files/upload")
async def upload_files(files: List[UploadFile] = File(...),
                       folder_id: str = Form(""), uploaded_by: str = Form(""),
                       user=Depends(check_auth), db: DBSession = Depends(get_db)):
    """Store each file AS-IS in the shared database and index its contents."""
    uploaded_by = user["name"]   # attribute to the real logged-in person
    fid_folder = int(folder_id) if (folder_id or "").isdigit() else None
    if fid_folder:
        target = db.query(Folder).filter(Folder.id == fid_folder).first()
        if not target:
            fid_folder = None
        elif target.locked:
            raise HTTPException(423, f"Folder “{target.name}” is locked. Unlock it to add files.")

    saved = []
    for uf in files:
        content = await uf.read()
        pub_id = uuid.uuid4().hex[:12]
        ext = os.path.splitext(uf.filename or "")[1].lower() or ".dat"
        with _tempfile_from(content, ext) as tmp:
            search_text, sheets, rows = indexer.build_index(tmp, ext)
        sf = StoredFile(
            file_id=pub_id, folder_id=fid_folder,
            file_name=uf.filename or f"file{ext}", blob=content,
            ext=ext, size_bytes=len(content), sheet_count=sheets, row_count=rows,
            search_text=search_text, uploaded_by=uploaded_by,
        )
        db.add(sf); db.commit(); db.refresh(sf)
        saved.append(file_out(sf, db))
    return {"ok": True, "count": len(saved), "files": saved}


@app.get("/api/files")
def list_files(folder_id: str = "", q: str = "",
               _=Depends(check_auth), db: DBSession = Depends(get_db)):
    """No q -> files in a folder (or all). With q -> keyword matches everywhere."""
    if q.strip():
        return {"matches": _keyword_matches(db, q)}
    query = db.query(StoredFile)
    if folder_id == "root":
        query = query.filter(StoredFile.folder_id.is_(None))
    elif folder_id.isdigit():
        query = query.filter(StoredFile.folder_id == int(folder_id))
    files = query.order_by(StoredFile.created_at.desc()).all()
    return {"files": [file_out(f, db) for f in files]}


@app.get("/api/files/{file_id}/download")
def download_file(file_id: str, _=Depends(check_auth), db: DBSession = Depends(get_db)):
    f = db.query(StoredFile).filter(StoredFile.file_id == file_id).first()
    if not f or f.blob is None:
        raise HTTPException(404, "File not found")
    quoted = f.file_name.replace('"', "")
    return Response(content=f.blob, media_type="application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="{quoted}"'})


@app.get("/api/files/{file_id}/preview")
def preview_file(file_id: str, _=Depends(check_auth), db: DBSession = Depends(get_db)):
    f = db.query(StoredFile).filter(StoredFile.file_id == file_id).first()
    if not f or f.blob is None:
        raise HTTPException(404, "File not found")
    with _tempfile_from(f.blob, f.ext) as tmp:
        data = indexer.preview(tmp, f.ext)
    data["file"] = file_out(f, db)
    return data


@app.put("/api/files/{file_id}/move")
async def move_file(file_id: str, req: Request, _=Depends(check_auth), db: DBSession = Depends(get_db)):
    d = await req.json()
    f = db.query(StoredFile).filter(StoredFile.file_id == file_id).first()
    if not f:
        raise HTTPException(404)
    if f.locked:
        raise HTTPException(423, "This file is locked. Unlock it first.")
    fid = d.get("folder_id")
    dest = int(fid) if str(fid).isdigit() else None
    if dest:
        df = db.query(Folder).filter(Folder.id == dest).first()
        if df and df.locked:
            raise HTTPException(423, f"Folder “{df.name}” is locked. Unlock it first.")
    f.folder_id = dest
    db.commit()
    return file_out(f, db)


@app.put("/api/files/{file_id}/lock")
def lock_file(file_id: str, _=Depends(require_admin), db: DBSession = Depends(get_db)):
    """Toggle a file's lock. Admins only."""
    f = db.query(StoredFile).filter(StoredFile.file_id == file_id).first()
    if not f:
        raise HTTPException(404)
    f.locked = not bool(f.locked); db.commit()
    return {"file_id": f.file_id, "locked": f.locked}


@app.delete("/api/files/{file_id}")
def delete_file(file_id: str, user=Depends(check_auth), db: DBSession = Depends(get_db)):
    f = db.query(StoredFile).filter(StoredFile.file_id == file_id).first()
    if not f:
        raise HTTPException(404)
    if not user["admin"] and (f.uploaded_by or "") != user["name"]:
        raise HTTPException(403, "You can only delete files you uploaded. Ask an admin to remove this one.")
    if f.locked and not user["admin"]:
        raise HTTPException(423, "This file is locked. An admin can unlock it.")
    db.delete(f); db.commit()
    return {"ok": True}


# --- Editing the actual spreadsheet (in the shared DB) --------------------
EDITABLE_EXT = {".xlsx", ".xlsm", ".xltx", ".xls", ".csv", ".tsv"}


def _edit_blob(db, f, mutate):
    """Apply `mutate(path)` to the file's real bytes, then re-index. The file is
    stored in the DB, so this changes it for everyone — locally and deployed."""
    with _tempfile_from(f.blob, f.ext) as tmp:
        mutate(tmp)
        with open(tmp, "rb") as fh:
            new = fh.read()
        text, sheets, rows = indexer.build_index(tmp, f.ext)
    f.blob = new
    f.size_bytes = len(new)
    f.search_text = text
    f.sheet_count = sheets
    f.row_count = rows
    db.commit()


@app.post("/api/files/{file_id}/row")
async def add_row(file_id: str, req: Request, _=Depends(check_auth), db: DBSession = Depends(get_db)):
    d = await req.json()
    f = db.query(StoredFile).filter(StoredFile.file_id == file_id).first()
    if not f:
        raise HTTPException(404)
    if f.locked:
        raise HTTPException(423, "This file is locked. Unlock it first.")
    if f.ext not in EDITABLE_EXT:
        raise HTTPException(400, "Rows can only be added to spreadsheets or CSV files.")
    values = d.get("values") or {}
    if not any(str(v).strip() for v in values.values()):
        raise HTTPException(400, "Give at least one value for the new row.")
    try:
        _edit_blob(db, f, lambda p: indexer.append_row(p, f.ext, values))
    except Exception as e:
        raise HTTPException(400, f"Could not add the row: {e}")
    return {"ok": True, "file": file_out(f, db)}


@app.put("/api/files/{file_id}/table")
async def save_table(file_id: str, req: Request, _=Depends(check_auth), db: DBSession = Depends(get_db)):
    """Replace the first sheet's data with an edited grid (headers + rows)."""
    d = await req.json()
    f = db.query(StoredFile).filter(StoredFile.file_id == file_id).first()
    if not f:
        raise HTTPException(404)
    if f.locked:
        raise HTTPException(423, "This file is locked. Unlock it first.")
    if f.ext not in EDITABLE_EXT:
        raise HTTPException(400, "Only spreadsheets or CSV files can be edited.")
    headers = d.get("headers") or []
    rows = d.get("rows") or []
    if not headers:
        raise HTTPException(400, "No columns to save.")
    try:
        _edit_blob(db, f, lambda p: indexer.write_table(p, f.ext, headers, rows))
    except Exception as e:
        raise HTTPException(400, f"Could not save the sheet: {e}")
    return {"ok": True, "file": file_out(f, db)}


# --- Search ---------------------------------------------------------------
def _all_file_dicts(db):
    return [{"file_id": f.file_id, "file_name": f.file_name,
             "folder": _folder_name(db, f.folder_id), "search_text": f.search_text or ""}
            for f in db.query(StoredFile).all()]


def _keyword_matches(db, query):
    return ai_layer.scan_files(_all_file_dicts(db), query, max_files=40, max_lines=6)


@app.post("/api/search")
async def search(req: Request, me=Depends(check_auth), db: DBSession = Depends(get_db)):
    d = await req.json()
    query = (d.get("query") or "").strip()
    mode = d.get("mode", "ai")
    user = me["name"]
    if not query:
        raise HTTPException(400, "Type something to search for")

    # Keyword: instant, free, no key.
    if mode == "keyword":
        matches = _keyword_matches(db, query)
        return {"mode": mode, "query": query, "result": None, "matches": matches}

    # Web: Tavily + Gemini, quota-capped.
    if mode == "web":
        if not _key_ready("TAVILY_API_KEY"):
            raise HTTPException(400, "No Tavily key yet. Add a free one from tavily.com to .env and restart. Keyword search works without it.")
        if not _key_ready("GEMINI_API_KEY"):
            raise HTTPException(400, "Web search also needs the free Gemini key in .env (it formats the results).")
        if quota_status(db, "web_search", _per_user_cap(db, "web_search"), user)["remaining"] <= 0:
            raise HTTPException(429, "You've used your web-search share for today. It resets at midnight (UTC).")
        try:
            result = ai_layer.search_web(query)
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(502, ai_layer.explain_error(e))
        bump_quota(db, "web_search", user)
        _save_history(db, query, mode, result, user)
        return {"mode": mode, "query": query, "result": result, "matches": None}

    # AI (default): keyword pre-filter, then Gemini answers + cites files.
    if not _key_ready("GEMINI_API_KEY"):
        raise HTTPException(400, "No Gemini key yet. Add a free one from aistudio.google.com to .env and restart. Keyword search works without it.")
    if quota_status(db, "reasoning", _per_user_cap(db, "reasoning"), user)["remaining"] <= 0:
        raise HTTPException(429, "You've used your AI share for today. Keyword search still works; it resets at midnight (UTC).")
    matches = ai_layer.scan_files(_all_file_dicts(db), query, max_files=15, max_lines=8)
    try:
        result = ai_layer.answer_over_files(query, matches)
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, ai_layer.explain_error(e))
    bump_quota(db, "reasoning", user)
    _save_history(db, query, mode, result, user)
    return {"mode": mode, "query": query, "result": result, "matches": matches}


def _save_history(db, query, mode, result, user):
    entry = SearchHistory(query=query, mode=mode, result=result, user=user)
    db.add(entry); db.commit()


@app.get("/api/search/history")
def search_hist(_=Depends(check_auth), db: DBSession = Depends(get_db)):
    return [{"id": s.id, "query": s.query, "mode": s.mode, "result": s.result,
             "user": s.user, "created_at": str(s.created_at)}
            for s in db.query(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(30).all()]


@app.post("/api/ai/organize")
async def ai_organize(user=Depends(check_auth), db: DBSession = Depends(get_db)):
    if not _key_ready("GEMINI_API_KEY"):
        raise HTTPException(400, "No Gemini key yet. Add a free one from aistudio.google.com to .env and restart.")
    if quota_status(db, "reasoning", _per_user_cap(db, "reasoning"), user["name"])["remaining"] <= 0:
        raise HTTPException(429, "You've used your AI share for today.")
    # Build a compact folder->files summary (with column headers) for the model.
    blocks = []
    folders = db.query(Folder).order_by(Folder.name).all()
    groups = {None: []}
    for fo in folders:
        groups[fo.id] = []
    for f in db.query(StoredFile).all():
        groups.setdefault(f.folder_id, []).append(f)
    for fid_key, files in groups.items():
        fname = _folder_name(db, fid_key) or "(no folder / root)"
        lines = [f"FOLDER: {fname}"]
        for f in files:
            head = (f.search_text or "").split("\n", 1)[0][:160]
            lines.append(f"  - {f.file_name} [{f.row_count} rows] {head}")
        if len(lines) > 1:
            blocks.append("\n".join(lines))
    if not blocks:
        return {"result": "The drive is empty -- upload some files first."}
    try:
        result = ai_layer.organize("\n\n".join(blocks)[:14000])
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, ai_layer.explain_error(e))
    bump_quota(db, "reasoning", user["name"])
    return {"result": result}


# --- AI assistant: answers AND does things (create folder, move, web) -----
def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _find_file(db, query):
    """Best file by name match."""
    qn = _norm(query)
    if not qn:
        return None
    best, best_score = None, 0
    for f in db.query(StoredFile).all():
        fn = _norm(f.file_name)
        score = 0
        if qn in fn or fn in qn:
            score = 90
        else:
            qt = set(re.split(r"[^a-z0-9]+", query.lower())) - {""}
            ft = set(re.split(r"[^a-z0-9]+", f.file_name.lower())) - {""}
            if qt and ft:
                score = int(100 * len(qt & ft) / len(qt))
        if score > best_score:
            best, best_score = f, score
    return best if best_score >= 50 else None


def _find_folder(db, name):
    nn = _norm(name)
    if not nn:
        return None
    for f in db.query(Folder).order_by(Folder.name).all():
        fn = _norm(f.name)
        if nn == fn or nn in fn or fn in nn:
            return f
    return None


ROOT_WORDS = {"root", "nofolder", "allfiles", "home", "main"}


def _history_text(ctx, max_turns=4, max_chars=2000):
    """Build a short transcript from the client's recent Q&A turns (safe + capped)."""
    if not isinstance(ctx, list):
        return ""
    lines = []
    for turn in ctx[-max_turns:]:
        if not isinstance(turn, dict):
            continue
        q = str(turn.get("q", "")).strip()
        a = str(turn.get("a", "")).strip()
        if q:
            lines.append("User: " + q[:400])
        if a:
            lines.append("Assistant: " + a[:600])
    return "\n".join(lines)[-max_chars:]


COMMAND_VERBS = ("create", "make", "new folder", "add", "move", "put", "throw",
                 "rename", "delete", "remove", "organi", "sort", "tidy", "insert", "append")


def _looks_like_command(msg):
    low = msg.lower().strip()
    if low.endswith("?"):
        return False
    # Only treat it as a command (and spend the extra planning AI call) when it
    # STARTS with an action verb. Questions that merely mention "add"/"move"
    # stay single-call and fast.
    first = low.split()
    first = first[0] if first else ""
    return first in ("create", "make", "new", "add", "move", "put", "throw",
                     "rename", "delete", "remove", "organise", "organize",
                     "sort", "tidy", "insert", "append")


def _columns_for(f):
    for line in (f.search_text or "").split("\n"):
        if "columns:" in line.lower():
            return line.split("columns:", 1)[1].strip()
    return ""


def _exec_action(db, act, user):
    """Execute ONE planned action for real; return a truthful one-line result."""
    op = (act.get("op") or "").lower()
    if op == "create_folder":
        name = (act.get("name") or "").strip()
        if not name:
            return None
        if db.query(Folder).filter(Folder.name == name).first():
            return f"Folder “{name}” already existed."
        db.add(Folder(name=name, created_by=user)); db.commit()
        return f"Created folder “{name}”."
    if op == "move_file":
        f = _find_file(db, act.get("file", ""))
        if not f:
            return f"Couldn't find a file matching “{act.get('file','')}” to move."
        if f.locked:
            return f"“{f.file_name}” is locked — didn't move it."
        target = act.get("folder", "")
        if not target or _norm(target) in ROOT_WORDS:
            f.folder_id = None; db.commit()
            return f"Moved “{f.file_name}” to the top level."
        dest = _find_folder(db, target)
        note = ""
        if not dest:
            dest = Folder(name=target, created_by=user); db.add(dest); db.commit(); db.refresh(dest)
            note = f" (created folder “{target}”)"
        if dest.locked:
            return f"Folder “{dest.name}” is locked — didn't move “{f.file_name}”."
        f.folder_id = dest.id; db.commit()
        return f"Moved “{f.file_name}” into “{dest.name}”{note}."
    if op == "add_row":
        f = _find_file(db, act.get("file", ""))
        if not f:
            return f"Couldn't find a file matching “{act.get('file','')}” to add a row to."
        if f.locked:
            return f"“{f.file_name}” is locked — didn't add a row."
        if f.ext not in EDITABLE_EXT:
            return f"“{f.file_name}” isn't a spreadsheet I can add rows to."
        values = act.get("values") or {}
        if not any(str(v).strip() for v in values.values()):
            return "No values were given for the new row."
        try:
            _edit_blob(db, f, lambda p: indexer.append_row(p, f.ext, values))
        except Exception as e:
            return f"Couldn't add the row to “{f.file_name}”: {e}"
        cells = ", ".join(f"{k}={v}" for k, v in values.items() if str(v).strip())
        return f"Added a row to “{f.file_name}” — {cells}."
    return None


@app.post("/api/assistant")
async def assistant(req: Request, me=Depends(check_auth), db: DBSession = Depends(get_db)):
    d = await req.json()
    msg = (d.get("message") or "").strip()
    user = me["name"]
    history = _history_text(d.get("context"))
    if not msg:
        raise HTTPException(400, "Ask me something")

    # A short, single-clause command we can handle without the AI. Longer /
    # multi-step instructions ("make a folder AND move X AND add vendor 5…")
    # skip these and go to the planner below.
    simple = len(msg) <= 60 and " and " not in msg.lower()

    # 1) "create folder X" / "make a folder called X"
    m = re.match(r"^(?:create|make|new|add)\s+(?:a\s+)?folder\s+(?:called\s+|named\s+)?[\"']?(.+?)[\"']?[.!]?$", msg, re.I)
    if m and simple:
        name = m.group(1).strip()
        existing = db.query(Folder).filter(Folder.name == name).first()
        if existing:
            return {"reply": f"Folder “{name}” already exists.", "did": "none", "refresh": False, "sources": []}
        db.add(Folder(name=name, created_by=user)); db.commit()
        return {"reply": f"Created folder “{name}”.", "did": "create_folder", "refresh": True, "sources": []}

    # 2) "move <file> to <folder>"
    m = re.match(r"^move\s+(.+?)\s+(?:to|into)\s+(.+?)[.!]?$", msg, re.I)
    if m and simple:
        fq, target = m.group(1).strip(), m.group(2).strip()
        f = _find_file(db, fq)
        if not f:
            return {"reply": f"I couldn't find a file matching “{fq}”.", "did": "none", "refresh": False, "sources": []}
        if f.locked:
            return {"reply": f"“{f.file_name}” is locked — unlock it first, then I can move it.", "did": "none", "refresh": False, "sources": []}
        if _norm(target) in ROOT_WORDS:
            f.folder_id = None; db.commit()
            return {"reply": f"Moved “{f.file_name}” out to the top level.", "did": "move", "refresh": True, "sources": []}
        dest = _find_folder(db, target)
        if not dest:
            return {"reply": f"There's no folder called “{target}”. Say “create folder {target}” first, then move it.", "did": "none", "refresh": False, "sources": []}
        if dest.locked:
            return {"reply": f"Folder “{dest.name}” is locked — unlock it first.", "did": "none", "refresh": False, "sources": []}
        f.folder_id = dest.id; db.commit()
        return {"reply": f"Moved “{f.file_name}” into “{dest.name}”.", "did": "move", "refresh": True, "sources": []}

    # 2.5) A fuller command ("make folder X, put the file in it, add vendor 5 …").
    #      Let the model plan concrete actions; WE execute them and report only
    #      what actually happened — so it can never claim an edit it didn't make.
    if _key_ready("GEMINI_API_KEY") and _looks_like_command(msg):
        if quota_status(db, "reasoning", _per_user_cap(db, "reasoning"), user)["remaining"] > 0:
            files_info = [{"file_name": f.file_name, "columns": _columns_for(f)}
                          for f in db.query(StoredFile).all()]
            folders_info = [{"name": fo.name} for fo in db.query(Folder).all()]
            try:
                actions = ai_layer.plan(msg, files_info, folders_info, history)
            except Exception:
                actions = []
            if actions:
                bump_quota(db, "reasoning", user)
                results = []
                for act in actions[:12]:
                    r = _exec_action(db, act, user)
                    if r:
                        results.append(r)
                if results:
                    reply = "Done:\n- " + "\n- ".join(results)
                    _save_history(db, msg, "action", reply, user)
                    return {"reply": reply, "did": "action", "refresh": True, "sources": []}
            # nothing actionable -> fall through and just answer

    # 3) Otherwise: answer from the drive; fall back to the web if it's not there.
    matches = ai_layer.scan_files(_all_file_dicts(db), msg, max_files=15, max_lines=8)
    if matches:
        if not _key_ready("GEMINI_API_KEY"):
            # No AI key yet — still useful: return the keyword hits.
            return {"reply": f"Found {len(matches)} file(s) that mention that (add a free Gemini key for a written answer):",
                    "did": "keyword", "refresh": False, "sources": matches}
        if quota_status(db, "reasoning", _per_user_cap(db, "reasoning"), user)["remaining"] <= 0:
            raise HTTPException(429, "You've used your AI share for today. Keyword search still works; it resets at midnight (UTC).")
        try:
            reply = ai_layer.answer_over_files(msg, matches, history)
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(502, ai_layer.explain_error(e))
        bump_quota(db, "reasoning", user)
        _save_history(db, msg, "ai", reply, user)
        return {"reply": reply, "did": "answer", "refresh": False, "sources": matches}

    # nothing in the drive -> web
    if _key_ready("TAVILY_API_KEY") and _key_ready("GEMINI_API_KEY"):
        if quota_status(db, "web_search", _per_user_cap(db, "web_search"), user)["remaining"] <= 0:
            raise HTTPException(429, "Nothing in the drive matched, and you've used your web-search share for today.")
        try:
            reply = ai_layer.search_web(msg)
        except Exception as e:
            raise HTTPException(502, ai_layer.explain_error(e))
        bump_quota(db, "web_search", user)
        _save_history(db, msg, "web", reply, user)
        return {"reply": "Nothing in the drive matched, so here's what I found on the web:\n\n" + reply,
                "did": "web", "refresh": False, "sources": None}

    return {"reply": "Nothing in the drive matched that, and web search needs the free Gemini + Tavily keys in .env. Try different words, or upload the file it should be in.",
            "did": "none", "refresh": False, "sources": []}


# --- Team & Ping ----------------------------------------------------------
def _admin_count(db):
    return db.query(TeamMember).filter(TeamMember.is_admin == True).count()


def _member_out(m, show_secret):
    o = {"id": m.id, "name": m.name, "email": m.email or "", "is_admin": bool(m.is_admin)}
    if show_secret:
        o["password"] = m.password or ""
    return o


@app.get("/api/team")
def list_team(me=Depends(check_auth), db: DBSession = Depends(get_db)):
    # Admins can see/manage passwords; everyone else just sees names.
    return [_member_out(m, me["admin"])
            for m in db.query(TeamMember).order_by(TeamMember.name).all()]


@app.post("/api/team")
async def add_member(req: Request, me=Depends(require_admin), db: DBSession = Depends(get_db)):
    """Admins add or update a member (name, password, admin flag)."""
    d = await req.json()
    name = (d.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Name required")
    m = db.query(TeamMember).filter(TeamMember.name == name).first()
    if not m and d.get("id"):
        m = db.query(TeamMember).filter(TeamMember.id == d.get("id")).first()
    if m:
        if "name" in d and name:
            m.name = name
        if "email" in d:
            m.email = (d.get("email") or "").strip()
        if d.get("password"):
            m.password = d.get("password")
        if "is_admin" in d:
            new_admin = bool(d.get("is_admin"))
            # safety net: never let the last admin be demoted
            if m.is_admin and not new_admin and _admin_count(db) <= 1:
                raise HTTPException(400, "This is the only admin — make someone else an admin first.")
            m.is_admin = new_admin
            m.role = "admin" if m.is_admin else "member"
        db.commit()
        return _member_out(m, True)
    m = TeamMember(name=name, email=(d.get("email") or "").strip(),
                   password=(d.get("password") or "x"), is_admin=bool(d.get("is_admin")),
                   role="admin" if d.get("is_admin") else "member")
    db.add(m); db.commit(); db.refresh(m)
    return _member_out(m, True)


@app.delete("/api/team/{mid}")
def remove_member(mid: int, me=Depends(require_admin), db: DBSession = Depends(get_db)):
    m = db.query(TeamMember).filter(TeamMember.id == mid).first()
    if not m:
        raise HTTPException(404)
    if m.id == me["id"]:
        raise HTTPException(400, "You can't remove your own account.")
    # safety net: the team can never be left with zero admins
    if m.is_admin and _admin_count(db) <= 1:
        raise HTTPException(400, "Can't remove the last admin. Make someone else an admin first.")
    db.delete(m); db.commit()
    return {"ok": True}


@app.post("/api/me/password")
async def change_my_password(req: Request, me=Depends(check_auth), db: DBSession = Depends(get_db)):
    """Any logged-in user changes their OWN password."""
    d = await req.json()
    new = (d.get("new_password") or "").strip()
    if len(new) < 1:
        raise HTTPException(400, "Pick a password.")
    m = db.query(TeamMember).filter(TeamMember.id == me["id"]).first()
    if not m:
        raise HTTPException(404)
    m.password = new; db.commit()
    return {"ok": True}


@app.get("/api/export.zip")
def export_zip(me=Depends(require_admin), db: DBSession = Depends(get_db)):
    """Admin-only: download every stored file as a zip (backup / escape hatch)."""
    import io
    import zipfile
    buf = io.BytesIO()
    used = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in db.query(StoredFile).all():
            if f.blob is None:
                continue
            folder = _folder_name(db, f.folder_id)
            path = (folder + "/" if folder else "") + f.file_name
            base, dot, ext = path.rpartition(".")
            n = 1
            while path in used:  # avoid collisions
                path = f"{base} ({n}){dot}{ext}" if dot else f"{path} ({n})"
                n += 1
            used.add(path)
            z.writestr(path, f.blob)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="vendor-drive-backup.zip"'})


@app.post("/api/ping")
async def ping(req: Request, me=Depends(check_auth), db: DBSession = Depends(get_db)):
    d = await req.json()
    member = db.query(TeamMember).filter(TeamMember.id == d.get("to_member_id")).first()
    if not member:
        raise HTTPException(404, "Team member not found")
    file_name = ""
    file_id = (d.get("file_id") or "")
    if file_id:
        f = db.query(StoredFile).filter(StoredFile.file_id == file_id).first()
        file_name = f.file_name if f else ""
    action = d.get("action", "info_share")
    message = d.get("message", "")
    from_user = me["name"]

    notif = Notification(from_user=from_user, to_user=member.name,
                         to_email=member.email or "", action=action,
                         file_id=file_id, message=message)
    db.add(notif); db.commit()
    delivered = notify_member(member, action, from_user, message, file_name)
    return {"ok": True, "to": member.name, "delivered": delivered}


@app.get("/api/notifications")
def list_notifications(user: str = "", _=Depends(check_auth), db: DBSession = Depends(get_db)):
    q = db.query(Notification).order_by(Notification.created_at.desc())
    if user:
        q = q.filter((Notification.to_user == user) | (Notification.from_user == user))
    return [{"id": n.id, "from_user": n.from_user, "to_user": n.to_user,
             "action": n.action, "file_id": n.file_id, "message": n.message,
             "status": n.status, "created_at": str(n.created_at or "")}
            for n in q.limit(50).all()]


@app.put("/api/notifications/{nid}/read")
def mark_read(nid: int, _=Depends(check_auth), db: DBSession = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == nid).first()
    if n:
        n.status = "read"; db.commit()
    return {"ok": True}


# --- Stats ----------------------------------------------------------------
@app.get("/api/stats")
def stats(me=Depends(check_auth), db: DBSession = Depends(get_db)):
    total_bytes = sum((f.size_bytes or 0) for f in db.query(StoredFile).all())
    members = db.query(TeamMember).count() or 1
    return {
        "file_count": db.query(StoredFile).count(),
        "folder_count": db.query(Folder).count(),
        "total_size_h": _human_size(total_bytes),
        "member_count": members,
        "me": me["name"],
        "is_admin": me["admin"],
        "search_count": db.query(SearchHistory).count(),
        # per-person daily share (persisted; resets midnight UTC)
        "reasoning_quota": quota_status(db, "reasoning", _per_user_cap(db, "reasoning"), me["name"]),
        "web_search_quota": quota_status(db, "web_search", _per_user_cap(db, "web_search"), me["name"]),
        "gemini_ready": bool(os.getenv("GEMINI_API_KEY", "")) and not os.getenv("GEMINI_API_KEY", "").startswith("your-"),
        "tavily_ready": bool(os.getenv("TAVILY_API_KEY", "")) and not os.getenv("TAVILY_API_KEY", "").startswith("your-"),
    }


if __name__ == "__main__":
    import uvicorn

    def _mask(v):
        if not v or v.startswith("your-"):
            return "NOT SET"
        return v[:4] + "..." + v[-2:] if len(v) > 8 else "set"

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    print("\n  Vendor Drive")
    print(f"  .env loaded: {'yes' if _env_found else 'NO -- not found at ' + _ENV_PATH}")
    print(f"  SITE_PASSWORD: {'set' if SITE_PASSWORD != 'changeme123' else 'DEFAULT (changeme123)'}")
    print(f"  GEMINI_API_KEY: {_mask(os.getenv('GEMINI_API_KEY',''))}   (keyword search works without it)")
    print(f"  TAVILY_API_KEY: {_mask(os.getenv('TAVILY_API_KEY',''))}")
    print(f"  Open: http://localhost:{port}\n")
    uvicorn.run("app:app", host=host, port=port, reload=(os.getenv("RELOAD", "1") == "1"))
