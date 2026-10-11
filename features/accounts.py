"""
features/accounts.py - BE1 + FE2: sign up, log in, log out and password reset.
PROVIDED COMPLETE. This is the worked example: every other feature follows the same pattern
(routes -> check the input -> use the database -> return a page, a redirect or JSON).
"""
import re
import sqlite3
from datetime import datetime, timedelta, timezone

import db
import security
import services
import ui
import web
from ui import h
from web import route

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RESET_MINUTES = 30
LOGIN_ERROR = "Email or password is incorrect."
SIGNUP_ERROR = ("We couldn't create an account with those details. "
                "If you already have an account, log in or reset your password.")


def password_problem(password, email=""):
    """The password rules. Returns what is wrong, or '' if the password is fine."""
    if len(password) < 10:
        return "Use at least 10 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return "Use at least one letter and one number."
    if email and password.lower() == email.lower():
        return "Don't use your email address as your password."
    return ""
 

def after_login(user, next_path=""):
    """Where to send someone once they are logged in. Onboarding comes first until it is done or skipped."""
    if not user["onboarding_done"] and web.has_route("GET", "/onboarding"):
        return "/onboarding"
    if next_path:
        return next_path
    if web.has_route("GET", "/dashboard"):
        return "/dashboard"
    return "/"


# ---------- home ----------
@route("GET", "/")
def home(request):
    if request.user:
        target = after_login(request.user)
        if target != "/":
            return web.redirect(target)
        body = ui.empty_state("You're logged in", "More pages appear here as features are built.")
        return web.html(ui.layout(request, "EcoAction Hub", body))
    body = ui.card("", "<p>Log the eco-friendly things you do and see the CO₂e you have saved.</p>"
                       + ui.link_button("Create an account", "/signup") + " "
                       + ui.link_button("Log in", "/login", "secondary"))
    return web.html(ui.layout(request, "Welcome to EcoAction Hub", body))


# ---------- sign up ----------
def signup_page(request, email="", errors=None):
    errors = errors or {}
    fields = (ui.field("Email", "email", email, type="email", required=True,
                       error=errors.get("email", ""), attrs='autocomplete="email"')
                       
              + ui.field("Password", "password", type="password", required=True,
                          error=errors.get("password", ""),
                          hint="At least 10 characters, with at least one letter and one number.",
                          attrs='autocomplete="new-password" minlength="10"')

              + ui.field("Confirm password", "confirm", type="password", required=True,
                         error=errors.get("confirm", ""), attrs='autocomplete="new-password"'))
    
    message = ui.toast(errors["general"], "error") if errors.get("general") else ""

    body = ui.card("", message + ui.form(request, "/signup", fields, "Create account")
                   + '<p>Already have an account? <a href="/login">Log in</a></p>')
    return ui.layout(request, "Create your account", body)

 
@route("GET", "/signup")
def signup_form(request):
    if request.user:
        return web.redirect(after_login(request.user))
    return web.html(signup_page(request))


@route("POST", "/signup")
def signup(request):
    if security.rate_limited("signup:" + request.ip, 10, 3600):
        return web.html(signup_page(request, errors={"general": ui.ERROR_TEXT[429]}), 429)
    form = request.form
    email = form.get("email", "").strip().lower()
    password = form.get("password", "")
    errors = {}
    if not EMAIL_PATTERN.match(email):
        errors["email"] = "Enter an email address like name@example.com."
    problem = password_problem(password, email)
    if problem:
        errors["password"] = problem
    if password != form.get("confirm", ""):
        errors["confirm"] = "The two passwords don't match."
    if not errors and db.query_one("SELECT id FROM users WHERE email = ?", (email,)):
        errors["general"] = SIGNUP_ERROR
    if errors:
        return web.html(signup_page(request, email, errors), 400)

    try:
        # One statement, so two people signing up at the same moment can't both become the first admin.
        user_id = db.execute(
            "INSERT INTO users (email, password_hash, is_admin, created_at) "
            "SELECT ?, ?, NOT EXISTS (SELECT 1 FROM users), ?",
            (email, security.hash_password(password), db.now()))
    except sqlite3.IntegrityError:          # someone else took the email a moment ago
        return web.html(signup_page(request, email, {"general": SIGNUP_ERROR}), 400)
    services.preferences(user_id)
    user = db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    response = web.redirect(after_login(user))
    security.start_session(response, user_id)
    ui.flash(request, "Welcome to EcoAction Hub!")
    return response


# ---------- log in / log out ----------
def login_page(request, email="", error="", next_path=""):
    fields = (ui.field("Email", "email", email, type="email", required=True, attrs='autocomplete="email"')
              + ui.field("Password", "password", type="password", required=True,
                         attrs='autocomplete="current-password"')
              + '<input type="hidden" name="next" value="%s">' % h(next_path))
    message = ui.toast(error, "error") if error else ""
    body = ui.card("", message + ui.form(request, "/login", fields, "Log in")
                   + '<p><a href="/reset">Forgotten your password?</a> | '
                     '<a href="/signup">Create an account</a></p>')
    return ui.layout(request, "Log in", body)


@route("GET", "/login")
def login_form(request):
    if request.user:
        return web.redirect(after_login(request.user))
    return web.html(login_page(request, next_path=security.safe_next(request.query.get("next", ""))))


@route("POST", "/login")
def login(request):
    form = request.form
    email = form.get("email", "").strip().lower()
    next_path = security.safe_next(form.get("next", ""))
    if (security.rate_limited("login-ip:" + request.ip, 20, 600)
            or security.rate_limited("login-email:" + email, 5, 600)):
        security.log_event("login_rate_limited", email, request.ip)
        return web.html(login_page(request, email, ui.ERROR_TEXT[429], next_path), 429)
    user = db.query_one("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,))
    stored = user["password_hash"] if user else security.dummy_hash()
    if not security.verify_password(form.get("password", ""), stored) or not user:
        security.log_event("login_failed", email, request.ip)
        return web.html(login_page(request, email, LOGIN_ERROR, next_path), 400)
    response = web.redirect(after_login(user, next_path))
    security.start_session(response, user["id"])
    return response


@route("POST", "/logout")
def logout(request):
    response = web.redirect("/")
    security.end_session(request, response)
    ui.flash(request, "You've been logged out.", "info")
    return response


# ---------- password reset ----------
def reset_request_page(request):
    fields = ui.field("Email", "email", type="email", required=True, attrs='autocomplete="email"')
    body = ui.card("", "<p>Enter your email and we'll send you a link to choose a new password.</p>"
                   + ui.form(request, "/reset", fields, "Send reset link"))
    return ui.layout(request, "Reset your password", body)


@route("GET", "/reset")
def reset_request_form(request):
    return web.html(reset_request_page(request))


@route("POST", "/reset")
def reset_request(request):
    email = request.form.get("email", "").strip().lower()
    if security.rate_limited("reset:" + request.ip, 5, 3600):
        security.log_event("reset_rate_limited", email, request.ip)
    else:
        user = db.query_one("SELECT id FROM users WHERE email = ? AND is_active = 1", (email,))
        if user:
            token = security.new_token()
            expires = datetime.now(timezone.utc) + timedelta(minutes=RESET_MINUTES)
            db.execute("INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
                       (user["id"], security.token_hash(token), expires.strftime("%Y-%m-%d %H:%M:%S")))
            link = "http://%s/reset/%s" % (request.host, token)
            services.send_email(email, "Reset your EcoAction Hub password",
                                "Open this link to choose a new password:\n%s\n\n"
                                "It works once and stops working after %d minutes.\n"
                                "If you didn't ask for this, you can ignore this email."
                                % (link, RESET_MINUTES))
    # Always the same answer, so nobody can find out which emails have accounts.
    body = ui.card("", "<p>If an account exists for that email, we've sent a link to reset the password. "
                       "The link works once and stops working after 30 minutes.</p>"
                       "<p class='hint'>This version of the app saves emails as files in the "
                       "<strong>data/outbox</strong> folder instead of sending them.</p>")
    return web.html(ui.layout(request, "Check your email", body))


def usable_reset(token):
    return db.query_one("SELECT * FROM password_resets "
                         "WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?",
                         (security.token_hash(token), db.now()))


def reset_dead_end(request):
    security.log_event("reset_token_invalid", "", request.ip)
    body = ui.empty_state("This link has expired or has already been used",
                          "Reset links work once and stop working after 30 minutes.",
                          ui.link_button("Send a new link", "/reset"))
    return web.html(ui.layout(request, "Link not valid", body), 400)


def new_password_page(request, token, error=""):
    fields = (ui.field("New password", "password", type="password", required=True, error=error,
                       hint="At least 10 characters, with at least one letter and one number.",
                       attrs='autocomplete="new-password" minlength="10"')
              + ui.field("Confirm new password", "confirm", type="password", required=True,
                         attrs='autocomplete="new-password"'))
    return ui.layout(request, "Choose a new password",
                     ui.card("", ui.form(request, "/reset/" + token, fields, "Save new password")))


@route("GET", "/reset/<token>")
def reset_form(request, token):
    if not usable_reset(token):
        return reset_dead_end(request)
    return web.html(new_password_page(request, token))


@route("POST", "/reset/<token>")
def reset_password(request, token):
    reset = usable_reset(token)
    if not reset:
        return reset_dead_end(request)
    password = request.form.get("password", "")
    user = db.query_one("SELECT email FROM users WHERE id = ?", (reset["user_id"],))
    problem = password_problem(password, user["email"])
    if not problem and password != request.form.get("confirm", ""):
        problem = "The two passwords don't match."
    if problem:
        return web.html(new_password_page(request, token, problem), 400)
    new_hash = security.hash_password(password)
    with db.transaction() as conn:
        claimed = conn.execute("UPDATE password_resets SET used_at = ? WHERE id = ? AND used_at IS NULL",
                                (db.now(), reset["id"])).rowcount
        if claimed == 1:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, reset["user_id"]))
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (reset["user_id"],))
    if claimed != 1:
        return reset_dead_end(request)
    security.log_event("password_reset_done", user["email"], request.ip)
    ui.flash(request, "Password changed. Please log in with your new password.")
    return web.redirect("/login")
