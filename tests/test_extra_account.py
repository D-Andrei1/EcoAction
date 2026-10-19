import re

import db
from tests.helpers import AppTestCase

class Extra_AccountTests(AppTestCase):
    def test_expired_reset_link(self):
        b = self.browser()
        b.signup("reset@example.com")

        b.post("/reset", {"email" : "reset@example.com"})

        db.change("UPDATE password_resets SET expires_at = '2000-01-01 00:00:00'")

        token = re.search(r"/reset/([A-Za-z0-9_-]+)", self.outbox()[-1]).group(1)

        page = b.get(f"/reset/{token}")
        self.assertEqual(page.status,400)
        self.assertIn("expired or has already been used", page.text)

    def test_sign_up_email_is_lowered(self):
        actual_email = "Sam@Example.COM"
        saved_email = "sam@example.com"

        b = self.browser()
        b.signup(actual_email)

        b.login(saved_email)

        page = b.get("/")
        self.assertIn("Log out", page.text)

    def test_wrong_password_rate_limit(self):
        email = "sam@example.com"

        b = self.browser()
        b.signup(email)

        page = None
        for i in range(6):
            page =  b.post("/login", {"email": email, "password": "NotThePassword"} )

        self.assertEqual(page.status,429)

        row = db.query_one(
            "SELECT * FROM security_log "
            "WHERE event = ? AND email = ?",
            ("login_rate_limited", email)
        )

        self.assertIsNotNone(row)