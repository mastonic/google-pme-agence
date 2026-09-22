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


if __name__ == "__main__":
    unittest.main()
