"""
Data layer for the Vendor Drive.

This is NOT a vector database and NOT a pile of shredded spreadsheet rows.
It is a plain file drive: your real Excel/CSV files are stored on disk, intact,
inside folders you make. The database here only holds *metadata* about those
files (name, folder, size) plus a plain-text INDEX of each file's contents so
the AI can search across hundreds of files and tell you which file a piece of
data lives in -- without ever destroying or reshaping your originals.

Tables:
  Folder        - a folder in the drive (like a Google Drive folder)
  StoredFile    - one uploaded file, kept as-is on disk + a text index of it
  TeamMember    - people you can @ping (attribution + inbox)
  Notification  - the in-app inbox (every ping lands here, no external service)
  SearchHistory - past AI searches, so you can re-read answers
  ApiQuota      - per-day counters so the free AI tiers can never be exceeded
"""
import os
import re
from datetime import datetime, date

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    LargeBinary,
)
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Engine ---------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/drive.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Daily ceilings so the free AI tiers can never be exceeded (no bill, ever).
REASONING_DAILY_LIMIT = int(os.getenv("REASONING_DAILY_LIMIT", "100"))
WEB_SEARCH_DAILY_LIMIT = int(os.getenv("WEB_SEARCH_DAILY_LIMIT", "30"))

# Cap how much extracted text we store/scan per file (keeps the DB and the AI
# context sane even with hundreds of big spreadsheets).
MAX_INDEX_CHARS = int(os.getenv("MAX_INDEX_CHARS", "60000"))


# --- Models ---------------------------------------------------------------
class Folder(Base):
    __tablename__ = "folders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_by = Column(String, default="")
    locked = Column(Boolean, default=False)   # locked = protected, can't be edited/deleted
    created_at = Column(DateTime, default=datetime.utcnow)


class StoredFile(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True)   # public id used in URLs
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True, index=True)
    file_name = Column(String, nullable=False)          # original name, unchanged
    blob = Column(LargeBinary)                          # the real file bytes, kept as-is
    ext = Column(String, default="")
    size_bytes = Column(Integer, default=0)
    sheet_count = Column(Integer, default=0)
    row_count = Column(Integer, default=0)
    search_text = Column(Text, default="")              # plain-text index of contents
    uploaded_by = Column(String, default="")
    locked = Column(Boolean, default=False)   # locked = protected, can't be moved/deleted
    created_at = Column(DateTime, default=datetime.utcnow)


class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    email = Column(String, default="")
    role = Column(String, default="member")
    password = Column(String, default="")     # simple per-person login password
    is_admin = Column(Boolean, default=False)  # admins can delete/lock anything, manage members


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    from_user = Column(String, default="")
    to_user = Column(String, nullable=False)
    to_email = Column(String, default="")
    action = Column(String, default="")
    file_id = Column(String, default="")     # optional: which file this is about
    message = Column(Text, default="")
    status = Column(String, default="unread")
    created_at = Column(DateTime, default=datetime.utcnow)


class SearchHistory(Base):
    __tablename__ = "search_history"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    mode = Column(String, default="ai")      # keyword | ai | web
    result = Column(Text, nullable=False)
    user = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class ApiQuota(Base):
    __tablename__ = "api_quotas"
    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String, nullable=False, index=True)        # reasoning | web_search
    usage_date = Column(String, nullable=False, index=True)  # YYYY-MM-DD
    who = Column(String, default="", index=True)             # whose usage ("user" is reserved in Postgres)
    count = Column(Integer, default=0)


# --- Setup helpers --------------------------------------------------------
def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_columns()


def _ensure_columns():
    """Best-effort: add columns introduced after a DB was first created.

    IMPORTANT: each ALTER runs in its OWN transaction. On Postgres a single
    failed statement aborts its whole transaction, so batching these together
    let one failure silently roll back the others -- which is exactly how the
    'password' column went missing. One transaction per column prevents that.
    """
    from sqlalchemy import inspect, text
    is_pg = "postgres" in str(engine.url)
    blob_type = "BYTEA" if is_pg else "BLOB"
    wanted = {
        "folders": [("locked", "BOOLEAN DEFAULT FALSE")],
        "files": [("locked", "BOOLEAN DEFAULT FALSE"), ("blob", blob_type)],
        "team_members": [("password", "VARCHAR DEFAULT ''"), ("is_admin", "BOOLEAN DEFAULT FALSE")],
        "api_quotas": [("who", "VARCHAR DEFAULT ''")],
    }
    insp = inspect(engine)
    for table, cols in wanted.items():
        try:
            existing = {c["name"] for c in insp.get_columns(table)}
        except Exception:
            continue
        for name, ddl in cols:
            if name in existing:
                continue
            try:
                with engine.begin() as conn:   # isolated: one column, one transaction
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN "{name}" {ddl}'))
            except Exception:
                pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


# --- Quota (per-person daily share, persisted in the shared DB) -----------
# The total daily cap is split equally among the team, so no one person can use
# up everyone's allowance. Counts persist in the DB, so they survive restarts
# and browser reopens (they reset only at midnight UTC, per real usage).
def per_user_limit(total: int, member_count: int) -> int:
    return max(1, total // max(1, member_count))


def quota_status(db, kind: str, per_user: int, user: str):
    today = str(date.today())
    q = db.query(ApiQuota).filter(
        ApiQuota.kind == kind, ApiQuota.usage_date == today, ApiQuota.who == (user or "")
    ).first()
    used = q.count if q else 0
    return {"used": used, "limit": per_user, "remaining": max(0, per_user - used)}


def bump_quota(db, kind: str, user: str):
    """Count ONE successful call for this user. Called only after the real API
    call worked, so a failed/rejected key never eats into anyone's allowance."""
    today = str(date.today())
    q = db.query(ApiQuota).filter(
        ApiQuota.kind == kind, ApiQuota.usage_date == today, ApiQuota.who == (user or "")
    ).first()
    if not q:
        q = ApiQuota(kind=kind, usage_date=today, who=(user or ""), count=0)
        db.add(q)
    q.count += 1
    db.commit()
    return q.count


# --- Seed the team on first boot ------------------------------------------
# name, is_admin. Passwords are assigned as simple letters (a, b, c, …) so the
# team can log in immediately; every field is editable in the app afterwards.
SEED_MEMBERS = [
    ("Shashank Nayak", True),
    ("Abhinand A", True),
    ("Vinay Rao", True),
    ("Prashant Subhedar", True),
    ("Akash Pai", False),
    ("Shreyas Hiwale", False),
    ("Sonia Badgeri", False),
    ("Athul CH", False),
    ("Kushagra Bagdwal", False),
    ("Divyashree GM", False),
    ("Bhavana Ramesh", False),
    ("Dipanshu Raut", False),
    ("Prajin Pednekar", False),
    ("Ektaa Rajani", False),
    ("Arul Prasath KS", False),
    ("Satish Kumar", False),
]


def _letter(i):
    # a..z, then a1, b1, … so we never run out
    return chr(97 + i) if i < 26 else chr(97 + i % 26) + str(i // 26)


def seed_members(db):
    """Add any missing seed members (idempotent). Never touches existing rows'
    names or passwords, so admins can rename/repassword freely in the app."""
    # de-dupe the seed list by name, keep first admin flag
    seen, ordered = set(), []
    for name, adm in SEED_MEMBERS:
        if name not in seen:
            seen.add(name); ordered.append((name, adm))
    idx = 0
    for name, adm in ordered:
        existing = db.query(TeamMember).filter(TeamMember.name == name).first()
        if existing:
            idx += 1
            continue
        db.add(TeamMember(name=name, is_admin=adm, role="admin" if adm else "member",
                          password=_letter(idx)))
        idx += 1
    db.commit()
