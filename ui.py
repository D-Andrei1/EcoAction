"""
ui.py - the design system: page layout, reusable components and error pages.
PROVIDED COMPLETE - type it in exactly and do not change it.
GOLDEN RULE: any text that came from a user or from the database must go through h()
before it is put into HTML. h() stops anyone injecting their own scripts (XSS).
Component functions escape the text you pass them; HTML you build yourself must use h().
"""
import html as _html
from http import HTTPStatus
from urllib.parse import quote, unquote
import security
import web
NAV = [] # menu entries: (label, path, who, order) - who is "user" or "admin"

def add_nav(label, path, who="user", order=50):
    """Features call this once to put a link in the top menu. Lower order = further left."""
    if not any(entry[1] == path for entry in NAV):
        NAV.append((label, path, who, order))
        NAV.sort(key=lambda entry: entry[3])

def h(value):
    """Escape text so it is shown as text, never run as HTML or script."""
    return _html.escape("" if value is None else str(value), quote=True)

def co2(kg, unit="kg"):
    """Format kg CO2e for people: co2(1.6) -> '1.6 kg CO2e'; co2(1600, 'tonnes') -> '1.6 t CO2e'."""
    if unit == "tonnes":
        return "%s t CO2e" % _trim(kg / 1000.0, 4)
    return "%s kg CO2e" % _trim(kg, 2)

def _trim(number, places):
    text = ("%." + str(places) + "f") % number
    return text.rstrip("0").rstrip(".") if "." in text else text

# ---------- messages ("toasts") ----------
def toast(message, kind="info"):
    role = "alert" if kind == "error" else "status"
    return ('<div class="toast toast-%s" role="%s"><span>%s</span>'
            '<button type="button" class="toast-close" aria-label="Dismiss message">&times;</button></div>'
            % (kind, role, h(message)))

def flash(request, message, kind="success"):
    """Show a toast on the NEXT page (use just before returning a redirect)."""
    request.set_cookie("flash", quote(kind + "|" + message))

def _take_flash(request):
    raw = request.cookies.get("flash")
    if not raw:
        return ""
    request.set_cookie("flash", "", max_age=0)
    kind, _, message = unquote(raw).partition("|")
    return toast(message, kind if kind in ("success", "error", "info") else "info")

# ---------- the page layout (every page uses this) ----------
def layout(request, title, body):
    token = security.csrf_token(request)
    user = request.user
    if user:
        links = []
        for label, path, who, order in NAV:
            if who == "admin" and not user["is_admin"]:
                continue
            current = request.path == path or request.path.startswith(path + "/")
            mark = ' aria-current="page"' if current else ""
            links.append('<li><a href="%s"%s>%s</a></li>' % (h(path), mark, h(label)))
        name = user["display_name"] or user["email"]
        account = ('<form method="post" action="/logout" class="account">%s<span>%s</span>%s</form>'
            % (csrf_field(request), h(name), button("Log out", "ghost")))
        nav = '<nav aria-label="Main"><ul>%s</ul></nav>%s' % ("".join(links), account)
    else:
        nav = ('<nav aria-label="Main"><ul><li><a href="/login">Log in</a></li>'
               '<li><a href="/signup">Sign up</a></li></ul></nav>')
    return """<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="csrf-token" content="%s">
<title>%s - EcoAction Hub</title>
<link rel="stylesheet" href="/static/app.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="topbar"><a class="brand" href="/">EcoAction Hub</a>%s</header>
<div id="toasts" class="toasts" aria-live="polite">%s</div>
<main id="main" tabindex="-1">
<h1>%s</h1>
%s
</main>
<script src="/static/app.js"></script>
</body>
</html>""" % (h(token), h(title), nav, _take_flash(request), h(title), body)

# ---------- components ----------
def csrf_field(request):
    return '<input type="hidden" name="csrf_token" value="%s">' % h(security.csrf_token(request))

def button(label, kind="primary", type="submit", attrs=""):
    """kind: primary | secondary | ghost | danger"""
    return '<button type="%s" class="btn btn-%s" %s>%s</button>' % (type, kind, attrs, h(label))

def link_button(label, href, kind="primary"):
    return '<a class="btn btn-%s" href="%s">%s</a>' % (kind, h(href), h(label))

def card(title, body_html, attrs=""):
    heading = "<h2>%s</h2>" % h(title) if title else ""
    return '<section class="card" %s>%s%s</section>' % (attrs, heading, body_html)

def empty_state(title, message, action_html=""):
    return ('<div class="empty"><p class="empty-title">%s</p><p>%s</p>%s</div>'
        % (h(title), h(message), action_html))

def skeleton(lines=3):
    """Grey placeholder bars shown while something loads."""
    return '<div class="skeleton" aria-hidden="true">%s</div>' % ('<span></span>' * lines)

def kpi(label, value, note=""):
    extra = '<span class="kpi-note">%s</span>' % h(note) if note else ""
    return ('<div class="kpi"><span class="kpi-label">%s</span><span class="kpi-value">%s</span>%s</div>'
        % (h(label), h(value), extra))

def badge(text, kind="neutral"):
    """kind: neutral | good | warn | bad"""
    return '<span class="badge badge-%s">%s</span>' % (kind, h(text))

def _described(name, hint, error):
    ids, extra = [], ""
    if hint:
        ids.append("f-%s-hint" % name)
        extra += '<p class="hint" id="f-%s-hint">%s</p>' % (h(name), h(hint))
    if error:
        ids.append("f-%s-error" % name)
        extra += '<p class="field-error" id="f-%s-error">%s</p>' % (h(name), h(error))
    aria = ' aria-describedby="%s"' % " ".join(ids) if ids else ""
    if error:
        aria += ' aria-invalid="true"'
    return aria, extra

def field(label, name, value="", type="text", required=False, error="", hint="", attrs=""):
    aria, extra = _described(name, hint, error)
    need = " required" if required else ""
    return ('<div class="field"><label for="f-%s">%s</label>'
            '<input id="f-%s" name="%s" type="%s" value="%s"%s%s %s>%s</div>'
            % (h(name), h(label), h(name), h(name), type, h(value), need, aria, attrs, extra))

def select_field(label, name, options, selected="", required=False, error="", hint="", attrs=""):
    """options: list of (value, text) pairs."""
    aria, extra = _described(name, hint, error)
    need = " required" if required else ""
    items = "".join('<option value="%s"%s>%s</option>'
                    % (h(v), " selected" if str(v) == str(selected) else "", h(t)) for v, t in options)
    return ('<div class="field"><label for="f-%s">%s</label>'
            '<select id="f-%s" name="%s"%s%s %s>%s</select>%s</div>'
            % (h(name), h(label), h(name), h(name), need, aria, attrs, items, extra))

def textarea_field(label, name, value="", rows=3, required=False, error="", hint="", attrs=""):
    aria, extra = _described(name, hint, error)
    need = " required" if required else ""
    return ('<div class="field"><label for="f-%s">%s</label>'
            '<textarea id="f-%s" name="%s" rows="%d"%s%s %s>%s</textarea>%s</div>'
            % (h(name), h(label), h(name), h(name), rows, need, aria, attrs, h(value), extra))

def checkbox(label, name, checked=False):
    return ('<div class="field check"><input type="checkbox" id="f-%s" name="%s" value="1"%s>'
            '<label for="f-%s">%s</label></div>'
            % (h(name), h(name), " checked" if checked else "", h(name), h(label)))

def form(request, action, inner_html, submit_label, method="post", attrs=""):
    """A form with the CSRF token already included."""
    token = csrf_field(request) if method == "post" else ""
    return ('<form method="%s" action="%s" %s>%s%s<div class="form-actions">%s</div></form>'
            % (method, h(action), attrs, token, inner_html, button(submit_label)))

def confirm_form(request, action, label, question, kind="danger"):
    """A one-button form that asks 'Are you sure?' first (used for delete, hide, etc.)."""
    return ('<form method="post" action="%s" class="inline" data-confirm="%s">%s%s</form>'
            % (h(action), h(question), csrf_field(request), button(label, kind)))

def modal(modal_id, title, body_html):
    """A dialog box. Open it with: <button type="button" data-open-modal="the-id">..."""
    return ('<dialog id="%s" class="modal" aria-labelledby="%s-title"><h2 id="%s-title">%s</h2>%s'
            '<div class="form-actions">'
            '<button type="button" class="btn btn-ghost" data-close-modal>Close</button>'
            '</div></dialog>' % (h(modal_id), h(modal_id), h(modal_id), h(title), body_html))

def table(headers, rows, caption=""):
    """rows are lists of cells that are ALREADY safe HTML (use h() on user text)."""
    head = "".join('<th scope="col">%s</th>' % h(x) for x in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % cell for cell in row) for row in rows)
    cap = "<caption>%s</caption>" % h(caption) if caption else ""
    return ('<div class="table-wrap"><table>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
            % (cap, head, body))

def pagination(page, has_next, base_path):
    """Previous / Next links. base_path is the page address without ?page=."""
    joiner = "&" if "?" in base_path else "?"
    parts = []
    if page > 1:
        parts.append('<a class="btn btn-secondary" href="%s%spage=%d">Previous</a>'
                    % (h(base_path), joiner, page - 1))
    if has_next:
        parts.append('<a class="btn btn-secondary" href="%s%spage=%d">Next</a>'
                    % (h(base_path), joiner, page + 1))
    return '<nav class="pager" aria-label="Pages">%s</nav>' % "".join(parts) if parts else ""

# ---------- error pages (404, 500 ...) ----------
ERROR_TEXT = {
    400: "Something in that request wasn't right. Please go back and try again.",
    403: "You don't have permission to do that. If you think you should, log in again.",
    404: "We couldn't find that page.",
    405: "That page can't be used that way.",
    429: "Too many attempts. Please wait a few minutes and try again.",
    500: "Something went wrong on our side. Please try again.",
}
def error_page(request, status):
    message = ERROR_TEXT.get(status, "Something went wrong.")
    body = empty_state(HTTPStatus(status).phrase, message, link_button("Go to the home page", "/", "secondary"))
    return layout(request, "Sorry - %s" % HTTPStatus(status).phrase, body)

web.ERROR_RENDERER["render"] = error_page