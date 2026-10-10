"""
db.py - SQLite database helpers (SQLite is built into Python).
PROVIDED COMPLETE - type it in exactly and do not change it.
Always pass values separately using ? placeholders, never by joining strings:
db.query("SELECT * FROM actions WHERE user_id = ?", (user_id,))
That is what stops SQL injection.
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS = {"path": os.path.join(BASE_DIR, "data", "ecoaction.db")}

def use_database(path):
    """Tests call this so they use a throwaway database, not the real one."""
    SETTINGS["path"] = path

def data_folder(name):
    """A folder next to the database (e.g. 'outbox', 'reports'), created if needed."""
    folder = os.path.join(os.path.dirname(SETTINGS["path"]), name)
    os.makedirs(folder, exist_ok=True)
    return folder

def now():
    """The current time (UTC) as text, e.g. '2026-02-04 09:15:00'."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def connect():
    os.makedirs(os.path.dirname(SETTINGS["path"]), exist_ok=True)
    conn = sqlite3.connect(SETTINGS["path"], timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def query(sql, params=()):
    """Run a SELECT. Returns a list of dicts, one per row."""
    conn = connect()
    try:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()

def query_one(sql, params=()):
    """Run a SELECT that should find one row. Returns a dict, or None."""
    rows = query(sql, params)
    return rows[0] if rows else None

def execute(sql, params=()):
    """Run an INSERT. Returns the id of the new row."""
    conn = connect()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
def change(sql, params=()):
    """Run an UPDATE or DELETE. Returns how many rows were changed."""
    conn = connect()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

@contextmanager
def transaction():
    """Several statements that must all succeed together:
    with db.transaction() as conn:
    conn.execute(...)
    conn.execute(...)
    """
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Create any missing tables from schema.sql. Safe to run every time the app starts."""
    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as f:
        script = f.read()
        conn = connect()
    try:
        conn.executescript(script)
        conn.commit()
    finally:
        conn.close()