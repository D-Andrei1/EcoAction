"""tests/test_styleguide.py - tests for FE1."""
from tests.helpers import AppTestCase
class StyleguideTests(AppTestCase):
    def test_admin_sees_every_component(self):
        b = self.browser()
        b.signup() # the first account is an admin
        page = b.get("/styleguide")
        self.assertEqual(page.status, 200)
        for piece in ["btn-primary", "btn-danger", 'class="empty"', 'class="skeleton"', 'class="kpi"',
                      "badge-good", 'aria-invalid="true"', "<dialog", "data-open-modal", "showToast"]:
            self.assertIn(piece, page.text)

    def test_other_people_are_kept_out(self):
        self.browser().signup("admin@example.com")
        member = self.browser()
        member.signup("member@example.com")
        self.assertEqual(member.get("/styleguide").status, 403)
        self.assertIn("/login", self.browser().get("/styleguide").url)

    def test_unknown_address_gives_the_404_page(self):
        page = self.browser().get("/no-such-page")
        self.assertEqual(page.status, 404)
        self.assertIn("find that page", page.text) # the ' in couldn't is sent as &#x27;
        self.assertIn("EcoAction Hub", page.text)

    def test_field_is_linked_with_error_message(self):
        b = self.browser()
        b.signup()
        page = b.get("/styleguide")
        self.assertEqual(page.status,200)
        self.assertIn('aria-describedby="f-field-error"', page.text)
        self.assertIn('id="f-field-error"', page.text)