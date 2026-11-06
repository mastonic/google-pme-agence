import unittest

from backend.services.scoring import calculate_scores


class ScoringTests(unittest.TestCase):
    def test_good_business_with_digital_gap_becomes_priority(self):
        strong = calculate_scores({
            "website": "",
            "rating": 4.7,
            "user_ratings_total": 180,
            "photos": [1, 2, 3, 4, 5],
            "business_phone": "0596000000",
            "address": "Fort-de-France",
            "category": ["restaurant"],
        })
        weak = calculate_scores({
            "website": "",
            "rating": 2.8,
            "user_ratings_total": 2,
            "photos": [],
            "address": "Fort-de-France",
            "category": ["restaurant"],
        })
        self.assertGreater(strong["opportunity"]["score"], weak["opportunity"]["score"])

    def test_a_good_existing_site_reduces_digital_gap(self):
        data = {
            "website": "https://example.com",
            "rating": 4.6,
            "user_ratings_total": 120,
            "photos": [1] * 10,
            "business_phone": "0596000000",
            "address": "Trinité",
            "category": ["dentist"],
        }
        poor = calculate_scores(data, {"status": "ok", "score": 30})
        good = calculate_scores(data, {"status": "ok", "score": 90})
        self.assertGreater(poor["opportunity"]["score"], good["opportunity"]["score"])
        self.assertLess(poor["digital_health"]["score"], good["digital_health"]["score"])

    def test_scores_are_bounded(self):
        scores = calculate_scores({})
        self.assertGreaterEqual(scores["digital_health"]["score"], 0)
        self.assertLessEqual(scores["digital_health"]["score"], 100)
        self.assertGreaterEqual(scores["opportunity"]["score"], 0)
        self.assertLessEqual(scores["opportunity"]["score"], 100)

    def test_breakdown_covers_google_business_seo_aeo_geo(self):
        data = {"website": "https://example.com", "rating": 4.7, "user_ratings_total": 120,
                "photos": [1] * 10, "business_phone": "0596", "address": "Le Robert", "category": ["bakery"]}
        rich_checks = {k: True for k in ("title", "meta_description", "h1", "local_business_schema", "faq",
                                         "faq_schema", "question_headings", "opening_hours", "structured_data",
                                         "about", "social", "testimonials")}
        rich = calculate_scores(data, {"status": "ok", "score": 90, "checks": rich_checks,
                                       "sections": {"technical": {"score": 25, "max": 25},
                                                    "seo_local": {"score": 25, "max": 25},
                                                    "conversion": {"score": 30, "max": 30},
                                                    "trust": {"score": 20, "max": 20}}})["digital_health"]
        poor = calculate_scores(data, {"status": "ok", "score": 20, "checks": {},
                                       "sections": {"technical": {"score": 10, "max": 25},
                                                    "seo_local": {"score": 0, "max": 25},
                                                    "conversion": {"score": 5, "max": 30},
                                                    "trust": {"score": 0, "max": 20}}})["digital_health"]
        labels = [c["label"] for c in rich["criteria"]]
        for expected in ("Fiche Google Business", "SEO local", "AEO · moteurs de réponse", "GEO · IA génératives"):
            self.assertIn(expected, labels)
        self.assertEqual(sum(c["max"] for c in rich["criteria"]), 100)
        by = lambda d, l: next(c["pts"] for c in d["criteria"] if c["label"] == l)
        for l in ("SEO local", "AEO · moteurs de réponse", "GEO · IA génératives"):
            self.assertGreater(by(rich, l), by(poor, l))
        self.assertGreaterEqual(rich["score"], 90)

    def test_old_audit_without_checks_still_scores(self):
        d = calculate_scores({"website": "https://x.fr"}, {"status": "ok", "score": 60})["digital_health"]
        self.assertTrue(0 <= d["score"] <= 100)


if __name__ == "__main__":
    unittest.main()
