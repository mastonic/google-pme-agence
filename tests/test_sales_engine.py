import datetime
import unittest

from backend.services.sales_engine import (
    build_outreach_sequence,
    build_sales_snapshot,
    derive_next_action,
)


class SalesEngineTests(unittest.TestCase):
    def setUp(self):
        self.biz = {
            "name": "Café Test",
            "rating": 4.7,
            "user_ratings_total": 128,
            "digital_health_score": 38,
            "opportunity_score": 82,
            "website": "https://example.com",
            "website_audit": {
                "score": 41,
                "issues": [
                    {"title": "Appel en 1 clic absent", "severity": "high"},
                    {"title": "Schema LocalBusiness absent", "severity": "medium"},
                ],
            },
            "generated_html": True,
            "owner_email": "contact@example.com",
            "crm_stage": "prospect",
        }

    def test_snapshot_uses_observed_gaps(self):
        snapshot = build_sales_snapshot(self.biz)
        self.assertEqual(snapshot["opportunity_score"], 82)
        labels = [x["label"] for x in snapshot["proposed"]]
        self.assertIn("Conversion", labels)

    def test_sequence_is_human_validated_four_steps(self):
        seq = build_outreach_sequence(self.biz, "https://demo.local/test")
        self.assertEqual(len(seq), 4)
        self.assertEqual(seq[0]["channel"], "email")
        self.assertEqual(seq[1]["channel"], "phone")
        self.assertIn("https://demo.local/test", seq[0]["content"])

    def test_next_action_prefers_demo_then_contact_then_outreach(self):
        now = datetime.datetime(2026, 9, 22, 8, 0, 0)
        no_demo = {**self.biz, "generated_html": False}
        self.assertEqual(derive_next_action(no_demo, now)["action"], "generate_demo")

        no_contact = {**self.biz, "owner_email": None}
        self.assertEqual(derive_next_action(no_contact, now)["action"], "enrich_contact")

        ready = {**self.biz, "outreach_status": "not_started"}
        self.assertEqual(derive_next_action(ready, now)["action"], "start_outreach")

    def test_opt_out_blocks_followup(self):
        data = {**self.biz, "prospecting_opt_out": True}
        self.assertEqual(derive_next_action(data)["action"], "none")


if __name__ == "__main__":
    unittest.main()
