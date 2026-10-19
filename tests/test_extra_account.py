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

