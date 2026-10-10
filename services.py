"""
services.py - small helpers shared by several features.
PROVIDED COMPLETE - type it in exactly and do not change it.
"""
import os
import re
import secrets
from datetime import date
import db

def parse_date(text):
    """'2026-02-04' -> date(2026, 2, 4). Returns None if the text is not a real date."""
    try:
        return date.fromisoformat((text or "").strip())
    except ValueError:
        return None
    
def send_email(to, subject, body):
    """There is no mail server. Each email is saved as a text file in the data/outbox
    folder, so you can open it and read it exactly as the person would."""
    folder = db.data_folder("outbox")
    stamp = db.now().replace(":", "").replace(" ", "_")
    safe_to = re.sub(r"[^A-Za-z0-9@._-]", "_", to)
    path = os.path.join(folder, "%s_%s_%s.txt" % (stamp, safe_to, secrets.token_hex(3)))
    with open(path, "w", encoding="utf-8") as f:
        f.write("To: %s\nSubject: %s\n\n%s\n" % (to, subject, body))
    print("[email] '%s' to %s saved in %s" % (subject, to, path))
    return path

def preferences(user_id):
    """The user's settings (creates the default row the first time)."""
    db.execute("INSERT OR IGNORE INTO preferences (user_id) VALUES (?)", (user_id,))
    return db.query_one("SELECT * FROM preferences WHERE user_id = ?", (user_id,))

PREFERENCE_FOR_KIND = {"milestone": "notify_milestones", "report": "notify_reports",
    "challenge": "notify_challenges"}

def notify(user_id, kind, message, link=""):
    """Add an in-app notification, unless the user has switched that kind off."""
    column = PREFERENCE_FOR_KIND.get(kind)
    if column and not preferences(user_id)[column]:
        return None
    return db.execute(
        "INSERT INTO notifications (user_id, kind, message, link, is_read, created_at) "
        "VALUES (?, ?, ?, ?, 0, ?)",
        (user_id, kind, message, link, db.now()))

def audit(admin_id, action, target_type, target_id, reason=""):
    """Record an admin action in the audit log (who did what, to what, and why)."""
    return db.execute(
        "INSERT INTO audit_log (admin_id, action, target_type, target_id, reason, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (admin_id, action, target_type, target_id, reason, db.now()))