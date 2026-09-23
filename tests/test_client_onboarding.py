import unittest
from types import SimpleNamespace

from backend.services.client_onboarding import (
    empty_profile,
    merge_profile,
    onboarding_progress,
    agent_team_readiness,
)


class ClientOnboardingTests(unittest.TestCase):
    def business(self, plan="starter"):
        return SimpleNamespace(
            id="b1",
            name="Commerce Test",
            address="1 rue Test",
            business_phone="0102030405",
            owner_email="contact@test.fr",
            client_profile=None,
            onboarding_token=None,
            plan_tier=plan,
            website="https://example.com",
            rating=4.5,
            user_ratings_total=20,
            category=["restaurant"],
            opportunity_score=70,
            digital_health_score=40,
        )

    def test_starter_progress_detects_missing_fields(self):
        b=self.business("starter")
        p=empty_profile(b)
        result=onboarding_progress(p,"starter")
        self.assertFalse(result["complete"])
        labels={x["label"] for x in result["missing"]}
        self.assertIn("Logo", labels)
        self.assertIn("Services", labels)
        self.assertIn("Photos", labels)

    def test_client_merge_marks_provenance_verified(self):
        b=self.business()
        p=merge_profile(b, {"brand":{"tone":"chaleureux"}}, source="client_onboarding")
        self.assertEqual(p["brand"]["tone"],"chaleureux")
        self.assertTrue(p["provenance"]["brand.tone"]["verified"])

    def test_social_team_requires_brand_and_photos(self):
        b=self.business("elite")
        b.client_profile=empty_profile(b)
        result=agent_team_readiness(b,"social-media")
        self.assertFalse(result["ready"])
        labels={x["label"] for x in result["missing"]}
        self.assertIn("Ton de marque",labels)
        self.assertIn("Photos",labels)

    def test_domain_watch_has_no_onboarding_blocker(self):
        b=self.business("starter")
        b.client_profile=empty_profile(b)
        self.assertTrue(agent_team_readiness(b,"domain-watch")["ready"])


if __name__ == "__main__":
    unittest.main()
