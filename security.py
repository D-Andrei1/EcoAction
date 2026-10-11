"""
security.py - passwords, log-in sessions, CSRF protection, rate limiting and access checks.
PROVIDED COMPLETE - type it in exactly and do not change it.
"""
import hashlib
import hmac
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import quote
import db
import web
PASSWORD_ITERATIONS = 600000 # tests lower this so they run quickly
SESSION_DAYS = 14
SESSION_COOKIE = "sid"
CSRF_COOKIE = "csrf"

# ---------- passwords (PBKDF2-SHA256, built into Python) ----------
def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                bytes.fromhex(salt), PASSWORD_ITERATIONS).hex()
    return "pbkdf2_sha256$%d$%s$%s" % (PASSWORD_ITERATIONS, salt, digest)

def verify_password(password, stored):
    try:
        algorithem, iterations, salt, digest = stored.split("$")
        iterations = int(iterations)
    except (ValueError, AttributeError):
        return False
    if algorithem != "pbkdf2_sha256":
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                bytes.fromhex(salt), iterations).hex()
    return hmac.compare_digest(check, digest)

_dummy = {}

def dummy_hash():
    """Checked when an email is unknown, so a wrong email takes as long as a wrong password."""
    if PASSWORD_ITERATIONS not in _dummy:
        _dummy[PASSWORD_ITERATIONS] = hash_password(secrets.token_hex(8))
    return _dummy[PASSWORD_ITERATIONS]

# ---------- tokens ----------
def new_token():
    """A long random value nobody can guess (used for sessions, reset links, story links)."""
    return secrets.token_urlsafe(32)

def token_hash(token):
    """Store only this, never the token itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def log_event(event, email="", ip=""):
    db.execute("INSERT INTO security_log (event, email, ip, created_at) VALUES (?, ?, ?, ?)",
    (event, email, ip, db.now()))

# ---------- sessions ----------
def start_session(response, user_id):
    token = new_token()
    expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
               (token_hash(token), user_id, db.now(), expires))
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400)
    return response

def end_session(request, response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        db.change("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))
    response.set_cookie(SESSION_COOKIE, "", max_age=0)
    return response

def load_session(request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        user = db.query_one(
            "SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ? AND sessions.expires_at > ? AND users.is_active = 1",
            (token_hash(token), db.now()))
        if user:
            del user["password_hash"]
            request.user = user
    return None

# ---------- CSRF protection ----------
def csrf_token(request):
    token = request.cookies.get(CSRF_COOKIE)
    if not token:
        token = new_token()
        request.cookies[CSRF_COOKIE] = token
        request.set_cookie(CSRF_COOKIE, token)
    return token

def check_csrf(request):
    """Every POST must carry the CSRF token (forms: hidden field; JavaScript: X-CSRF-Token header)."""
    if request.method in ("GET", "HEAD"):
        return None
    sent = request.header("X-CSRF-Token") or request.form.get("csrf_token", "")
    expected = request.cookies.get(CSRF_COOKIE, "")
    if not expected or not hmac.compare_digest(sent, expected):
        return web.error(request, 403)
    return None

# ---------- rate limiting ----------
_hits = {}
_lock = threading.Lock()
def rate_limited(key, limit, window_seconds):
    """Counts this use of `key`. True if it has now been used more than `limit` times
    in the last `window_seconds` seconds (so the caller should refuse)."""
    moment = time.monotonic()
    with _lock:
        recent = [t for t in _hits.get(key, []) if moment - t < window_seconds]
        recent.append(moment)
        _hits[key] = recent
        return len(recent) > limit
    
def reset_rate_limits():
    """Tests use this to start from a clean slate."""
    with _lock:
        _hits.clear()

# ---------- access checks (the "route guards") ----------
def safe_next(path):
    """Only allow redirects to our own pages (stops 'open redirect' tricks)."""
    if path and path.startswith("/") and not path.startswith("//") and "\\" not in path:
        return path
    return ""

def login_required(handler):
    @wraps(handler)
    def guarded(request, **kwargs):
        if request.user is None:
            if request.wants_json():
                return web.json_response({"error": "Please log in."}, 401)
            return web.redirect("/login?next=" + quote(request.path))
        return handler(request, **kwargs)
    return guarded

def admin_required(handler):
    @wraps(handler)
    def guarded(request, **kwargs):
        if request.user is None:
            return login_required(handler)(request, **kwargs)
        if not request.user['is_admin']:
            return web.error(request, 403)
        return handler(request, **kwargs)
    return guarded

web.BEFORE_HOOKS.append(load_session)
web.BEFORE_HOOKS.append(check_csrf)
