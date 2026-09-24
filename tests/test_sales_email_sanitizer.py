import unittest

from backend.agents.manager import LocalPulseManager


class SalesEmailSanitizerTests(unittest.TestCase):
    def manager(self):
        m = LocalPulseManager.__new__(LocalPulseManager)
        m.business_data = {
            "deployment_url": "https://demo.vercel.app",
            "payment_links": {
                "starter": "https://example.com/starter",
                "pro": "https://example.com/pro",
                "elite": "https://example.com/elite",
            },
            "plan_catalog": [
                {"slug":"starter","name":"Starter","price":49,"positioning":"Présence professionnelle","features":["Site","SSL","Maintenance"]},
                {"slug":"pro","name":"Pro","price":149,"positioning":"Visibilité locale","features":["SEO","Google","Avis"]},
                {"slug":"elite","name":"Élite","price":299,"positioning":"Croissance","features":["SEO avancé","Chatbot","Automatisation"]},
            ],
        }
        return m

    def test_removes_line_labels_and_brackets(self):
        raw = '''Bonjour,
L5: J'ai créé votre site internet : il est beau, professionnel et prêt à être mis en ligne maintenant.
L6: Pulse-PME gère absolument tout au quotidien, sans que vous n'ayez à toucher à quoi que ce soit.
[
Bonne journée,
Ludovic
Fondateur — Pulse-PME
]'''
        cleaned = self.manager()._sanitize_sales_email(raw)
        self.assertNotIn("L5:", cleaned)
        self.assertNotIn("L6:", cleaned)
        self.assertNotIn("\n[\n", "\n" + cleaned + "\n")
        self.assertIn("Pulse-PME gère absolument tout", cleaned)

    def test_artifact_detector_flags_line_markers(self):
        m = self.manager()
        self.assertTrue(m._sales_email_has_artifacts("L6: test"))
        self.assertTrue(m._sales_email_has_artifacts("Bonjour\n[\nSuite"))
        self.assertFalse(m._sales_email_has_artifacts("Bonjour,\nVotre site est prêt."))

    def test_finalize_keeps_clean_email_and_ctas(self):
        m = self.manager()
        raw = "Bonjour,\n\nVotre site est prêt à être découvert.\n\nBonne journée,\nLudovic\nFondateur — Pulse-PME"
        final = m._finalize_sales_email(raw)
        self.assertNotIn("L1:", final)
        self.assertIn("https://demo.vercel.app", final)
        self.assertIn("formule Starter à 49€ / mois", final)
        self.assertIn("Bonne journée,", final)


if __name__ == "__main__":
    unittest.main()
