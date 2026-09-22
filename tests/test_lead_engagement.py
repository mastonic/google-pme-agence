import datetime
import unittest

from backend.services.lead_engagement import calculate_lead_heat, default_onboarding_checklist, onboarding_progress


class LeadEngagementTests(unittest.TestCase):
    def test_repeated_demo_views_raise_temperature(self):
        now = datetime.datetime(2026, 9, 22, 8, 0)
        cold = calculate_lead_heat({"opportunity_score": 70, "demo_views": 0}, now)
        hot = calculate_lead_heat({
            "opportunity_score": 82,
            "demo_views": 4,
            "demo_interest_clicks": 1,
            "last_demo_view_at": now,
        }, now)
        self.assertGreater(hot["score"], cold["score"])
        self.assertEqual(hot["temperature"], "hot")

    def test_onboarding_progress(self):
        checklist = default_onboarding_checklist()
        p = onboarding_progress(checklist)
        self.assertEqual(p["total"], 7)
        self.assertEqual(p["done"], 1)
        for item in checklist:
            item["done"] = True
        self.assertTrue(onboarding_progress(checklist)["completed"])


if __name__ == "__main__":
    unittest.main()
