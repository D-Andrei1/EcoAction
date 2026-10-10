"""
tests/test_accounts.py - tests for BE1 + FE2.   PROVIDED COMPLETE (use it as your example).
"""
import re

import db
from tests.helpers import AppTestCase


class AccountTests(AppTestCase):

    def test_sign_up_log_out_and_log_in_again(self):
        b = self.browser()
        page = b.signup()
        self.assertEqual(page.status, 200)
        self.assertIn("Log out", page.text)
        b.post("/logout")
        self.assertNotIn("Log out", b.get("/").text)
        page = b.login()
        self.assertIn("Log out", page.text)

    def test_first_account_is_admin_and_second_is_not(self):
        self.browser().signup("first@example.com")
        self.browser().signup("second@example.com")
        users = db.query("SELECT email, is_admin FROM users ORDER BY id")
        self.assertEqual([u["is_admin"] for u in users], [1, 0])

    def test_wrong_password_gives_generic_message_and_keeps_email(self):
        self.browser().signup()
        page = self.browser().login(password="wrongpass999")
        self.assertEqual(page.status, 400)
        self.assertIn("Email or password is incorrect.", page.text)
        self.assertIn('value="sam@example.com"', page.text)
        unknown = self.browser().login(email="nobody@example.com")
        self.assertIn("Email or password is incorrect.", unknown.text)
        failed = db.query_one("SELECT COUNT(*) AS n FROM security_log WHERE event = 'login_failed'")
        self.assertEqual(failed["n"], 2)

    def test_weak_password_is_refused(self):
        page = self.browser().signup(password="short1")
        self.assertEqual(page.status, 400)
        self.assertIn("Use at least 10 characters.", page.text)

    def test_reset_link_works_once_only(self):
        self.browser().signup()
        b = self.browser()
        b.post("/reset", {"email": "sam@example.com"})
        token = re.search(r"/reset/([A-Za-z0-9_-]+)", self.outbox()[-1]).group(1)
        page = b.post("/reset/" + token, {"password": "newgreen456", "confirm": "newgreen456"})
        self.assertIn("Password changed", page.text)
        again = b.post("/reset/" + token, {"password": "another789x", "confirm": "another789x"})
        self.assertEqual(again.status, 400)
        self.assertIn("expired or has already been used", again.text)
        self.assertIn("Log out", self.browser().login(password="newgreen456").text)

    def test_reset_request_answer_is_the_same_for_unknown_emails(self):
        self.browser().signup()
        known = self.browser().post("/reset", {"email": "sam@example.com"})
        unknown = self.browser().post("/reset", {"email": "nobody@example.com"})
        self.assertEqual(known.status, unknown.status)
        self.assertIn("If an account exists", unknown.text)
        self.assertEqual(len(self.outbox()), 1)

    def test_post_without_the_right_csrf_token_is_refused(self):
        b = self.browser()
        b._csrf = lambda: "not-the-right-token"      # pretend a trick website sent the form
        page = b.post("/login", {"email": "sam@example.com", "password": "greenpass123"})
        self.assertEqual(page.status, 403)
