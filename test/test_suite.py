import unittest
from src.generator.email_engine import generate_dot_trick_emails, generate_plus_address_emails
from src.adapters.adapters import CodeBuddyAdapter, GoRouterAdapter, TabiAIAdapter
from src.injector.db_injector import DatabaseInjector

class TestSuite(unittest.TestCase):
    def test_dot_engine(self):
        dots = generate_dot_trick_emails("masteruser", "gmail.com", 10)
        self.assertEqual(len(dots), 10)
        for d in dots:
            self.assertTrue(d.endswith("@gmail.com"))
            self.assertEqual(d.split("@")[0].replace(".", ""), "masteruser")

    def test_plus_engine(self):
        plus = generate_plus_address_emails("masteruser", "proton.me", "gh", 5)
        self.assertEqual(len(plus), 5)
        self.assertEqual(plus[0], "masteruser+gh01@proton.me")

    def test_adapters(self):
        cb = CodeBuddyAdapter()
        gr = GoRouterAdapter()
        tb = TabiAIAdapter()
        self.assertEqual(cb.unit_type, "credits")
        self.assertEqual(gr.unit_type, "usd_balance")
        self.assertEqual(tb.unit_type, "usd_balance")

if __name__ == "__main__":
    unittest.main()
