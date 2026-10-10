"""
web.py - EcoAction Hub's small web framework.
Built only from the Python standard library.
PROVIDED COMPLETE - type it in exactly and do not change it.
"""
import json
import os
import re
import traceback
from http import HTTPStatus, cookies
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from wsgiref.simple_server import WSGIServer, make_server

ROUTES = [] # every page and API: (method, pattern, handler)
BEFORE_HOOKS = [] # run before every handler; a hook may return a Response to stop early
ERROR_RENDERER = {} # ui.py puts its error-page function in here
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
STATIC_TYPES = {".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon"}

def route(method, pattern):
    """Register a handler, e.g. @route("GET", "/actions/<action_id>")"""
    regex = re.compile("^" + re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", pattern) + "$")

    def register(handler):
        ROUTES.append((method, regex, handler))
        return handler
    return register

def has_route(method, path):
    """True if some feature has registered this method + path."""
    return any(m == method and regex.match(path) for m, regex, _ in ROUTES)

def cookie_header(name, value, max_age=None):
    parts = [name + "=" + value, "Path=/", "SameSite=Lax", "HttpOnly"]

    if max_age is not None:
        parts.append("Max-Age" + str(max_age))
    return ("Set-Cookie", "; ".join(parts))

class Request:
    def __init__(self, environ):
        self.environ = environ
        self.method = environ["REQUEST_METHOD"].upper()
        self.path = environ.get("PATH_INFO") or "/"
        self.query = {k: v[0] for k, v in parse_qs(environ.get("QUERY_STRING", "")).items()}
        jar = cookies.SimpleCookie()
        try:
            jar.load(environ.get("HTTP_COOKIE", ""))
        except cookies.CookieError:
            pass
        self.cookies = {name: morsel.value for name, morsel in jar.items()}
        self.ip = environ.get("REMOTE_ADDR", "")
        self.host = environ.get("HTTP_HOST") or "127.0.0.1:8000"
        self.user = None # filled in by security.py when someone is logged in
        self.new_cookies = [] # added to whatever response is sent back
        self._body = None

    @property
    def body(self):
        if self._body is None:
            try:
                length = int(self.environ.get("CONTENT_LENGTH") or 0)
            except ValueError:
                    length = 0
            self._body = self.environ["wsgi.input"].read(length) if length > 0 else b""
        return self._body

    @property
    def form(self):
        """Fields from a submitted HTML form, as a dict of strings."""
        pairs = parse_qs(self.body.decode("utf-8", "replace"), keep_blank_values=True)
        return {k: v[0] for k, v in pairs.items()}
    
    @property
    def json(self):
        """The JSON object sent by JavaScript, or None if it was not valid JSON."""
        try:
            data = json.loads(self.body.decode("utf-8") or "{}")
        except ValueError:
            return None
        return data if isinstance(data, dict) else None
    
    def header(self, name):
        return self.environ.get("HTTP_" + name.upper().replace("-", "_"))
    
    def wants_json(self):
        return self.path.startswith("/api/")
    
    def set_cookie(self, name, value, max_age=None):
        self.new_cookies.append(cookie_header(name, value, max_age))

class Response:
    def __init__(self, body="", status=200, content_type="text/html; charset=utf-8", headers=None):
        self.body = body
        self.status = status
        self.headers = [("Content-Type", content_type)] + list(headers or [])
    def set_cookie(self, name, value, max_age=None):
        self.headers.append(cookie_header(name, value, max_age))
        return self

def html(page, status=200):
    return Response(page, status)
def json_response(data, status=200):
    return Response(json.dumps(data), status, "application/json")
def redirect(location):
    return Response("", 303, headers=[("Location", location)])


def download(data, filename, content_type):
    """data may be bytes, a str, or a generator of str (sent a piece at a time)."""
    return Response(data, 200, content_type,
    [("Content-Disposition", 'attachment; filename="' + filename + '"')])

def error(request, status):
    render = ERROR_RENDERER.get("render")
    if request.wants_json() or render is None:
        return json_response({"error": HTTPStatus(status).phrase}, status)
    return html(render(request, status), status)

@route("GET", "/static/<name>")
def serve_static(request, name):
    extension = os.path.splitext(name)[1].lower()
    path = os.path.join(STATIC_DIR, name)
    if name.startswith(".") or extension not in STATIC_TYPES or not os.path.isfile(path):
        return error(request, 404)
    with open(path, "rb") as f:
        return Response(f.read(), 200, STATIC_TYPES[extension])

def dispatch(request):
    for hook in BEFORE_HOOKS:
        early = hook(request)
        if early is not None:
            return early
    path_found = False
    for method, regex, handler in ROUTES:
        match = regex.match(request.path)
        if match:
            path_found = True
            if method == request.method:
                return handler(request, **match.groupdict())
    return error(request, 405 if path_found else 404)

def application(environ, start_response):
    request = Request(environ)
    try:
        response = dispatch(request)
    except Exception:
        traceback.print_exc()
        try:
            response = error(request, 500)
        except Exception:
            traceback.print_exc()
            response = Response("Internal Server Error", 500, "text/plain; charset=utf-8")
    phrase = HTTPStatus(response.status).phrase
    start_response(str(response.status) + " " + phrase, response.headers + request.new_cookies)
    body = response.body
    if isinstance(body, str):
        return [body.encode("utf-8")]
    if isinstance(body, bytes):
        return [body]
    return (piece.encode("utf-8") if isinstance(piece, str) else piece for piece in body)

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

def serve(host="127.0.0.1", port=8000):
    server = make_server(host, port, application, server_class=ThreadingWSGIServer)
    print("EcoAction Hub is running. Open http://%s:%d in your web browser." % (host, port))
    print("To stop it, close this window or press Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

