import unittest

from backend.agents.manager import LocalPulseManager


CATALOG = [
    {"slug":"starter","name":"Starter","price":49,"summary":"Présence web propre.","is_popular":False},
    {"slug":"pro","name":"Pro","price":149,"summary":"Visibilité locale et acquisition.","is_popular":True},
    {"slug":"elite","name":"Élite","price":299,"summary":"Croissance et automatisation.","is_popular":False},
]


class SalesEmailConversionV2Tests(unittest.TestCase):
    def manager(self, score=72):
        m = LocalPulseManager.__new__(LocalPulseManager)
        m.business_data = {
            "opportunity_score": score,
            "deployment_url": "https://demo.vercel.app",
            "plan_catalog": CATALOG,
            "payment_links": {
                "starter": "https://pay/starter",
                "pro": "https://pay/pro",
                "elite": "https://pay/elite",
            },
        }
        return m

    def test_mid_score_recommends_only_pro(self):
        m = self.manager(72)
        final = m._finalize_sales_email(
            "Bonjour,\n\nJ'ai préparé une démo pour votre établissement.\n\nBonne journée,\nLudovic\nFondateur — Pulse-PME"
        )
        self.assertIn("formule Pro à 149€ / mois", final)
        self.assertIn("https://pay/pro", final)
        self.assertNotIn("https://pay/starter", final)
        self.assertNotIn("https://pay/elite", final)
        self.assertNotIn("Starter —", final)
        self.assertNotIn("Élite —", final)

    def test_high_score_can_recommend_elite(self):
        m = self.manager(90)
        self.assertEqual(m._recommended_sales_plan()["slug"], "elite")

    def test_low_score_can_recommend_starter(self):
        m = self.manager(60)
        self.assertEqual(m._recommended_sales_plan()["slug"], "starter")

    def test_demo_is_before_checkout(self):
        final = self.manager(72)._finalize_sales_email("Bonjour,\n\nDémo prête.")
        self.assertLess(final.index("https://demo.vercel.app"), final.index("https://pay/pro"))


if __name__ == "__main__":
    unittest.main()
