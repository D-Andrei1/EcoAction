"""
tests/helpers.py - makes testing easy.
PROVIDED COMPLETE - type it in exactly and do not change it.
Every test class that inherits AppTestCase gets:
    * its own running copy of the app, and
    * a brand-new empty database for every single test.
self.browser() gives a pretend web browser that keeps cookies and sends the CSRF token.
"""

import http.cookiejar
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from wsgiref.simple_server import WSGIRequestHandler, make_server

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import app # noqa: E402
import db # noqa: E402
import security # noqa: E402
import web # noqa: E402

security.PASSWORD_ITERATIONS = 1000 # quick password hashing - tests only!
app.load_features()

class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass

class Page:
    def __init__(self, status, url, raw):
        self.status = status
        self.url = url
        self.text = raw.decode("utf-8", "replace")

    @property
    def json(self):
        return json.loads(self.text)

class Browser:
    def __init__(self, base):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def cookie(self, name):
        for item in self.jar:
            if item.name == name:
                return item.value
        return ""

    def _csrf(self):
        if not self.cookie("csrf"):
            self.get("/")
        return self.cookie("csrf")

    def request(self, method, path, form=None, json_body=None):
        headers, body = {}, None
        if method != "GET":
            headers["X-CSRF-Token"] = self._csrf()
            body = b""
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif form is not None:
            body = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(self.base + path, data=body, headers=headers, method=method)
        try:
            with self.opener.open(req) as reply:
                return Page(reply.status, reply.geturl(), reply.read())
        except urllib.error.HTTPError as problem:
            return Page(problem.code, problem.geturl(), problem.read())

    def get(self, path):
        return self.request("GET", path)
    
    def post(self, path, form=None):
        return self.request("POST", path, form=form or {})
    
    def post_json(self, path, data, method="POST"):
        return self.request(method, path, json_body=data)
    
    def signup(self, email="sam@example.com", password="greenpass123"):
        return self.post("/signup", {"email": email, "password": password, "confirm": password})
    
    def login(self, email="sam@example.com", password="greenpass123"):
        return self.post("/login", {"email": email, "password": password})

class AppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server("127.0.0.1", 0, web.application,
                                 server_class=web.ThreadingWSGIServer, handler_class=QuietHandler)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        db.use_database(os.path.join(self.folder.name, "test.db"))
        db.init_db()
        security.reset_rate_limits()

    def tearDown(self):
        self.folder.cleanup()

    def browser(self):
        return Browser(self.base)
    
    def outbox(self):
        """The text of every email 'sent' during this test, oldest first."""
        folder = db.data_folder("outbox")
        texts = []
        for name in sorted(os.listdir(folder)):
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                texts.append(f.read())
        return texts