import asyncio
import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base, Business
from backend.services.autopilot import generate_and_deploy


class FakeManager:
    def __init__(self, data):
        self.data = data

    def run_design_crew(self):
        return {"template": "test"}

    def run_prep_crew(self):
        return {
            "report": "rapport",
            "copywriting": "copy",
            "ai_photos": [],
            "design": {},
        }

    def run_build_crew(self, prep):
        return {"html": "<html><body>ok</body></html>", "email": "draft"}

    def run_deploy_crew(self, html):
        return "https://demo-test.vercel.app"

    def run_email_only(self, prep):
        raise RuntimeError("email provider unavailable")


class FakeMaps:
    def get_business_details(self, business_id):
        return {
            "name": "Test Business",
            "formatted_address": "1 rue Test",
            "website": "",
            "types": ["restaurant"],
            "photos": [],
        }


class AutopilotWarningTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def test_email_failure_after_vercel_is_warning_not_project_error(self):
        db = self.Session()
        biz = Business(
            id="b1",
            name="Test Business",
            address="1 rue Test",
            rating=4.5,
            user_ratings_total=20,
            category=["restaurant"],
            status="scanned",
        )
        db.add(biz)
        db.commit()
        db.refresh(biz)

        with patch("backend.services.autopilot.GoogleMapsService", return_value=FakeMaps()), \
             patch("backend.services.autopilot.LocalPulseManager", FakeManager), \
             patch.dict(os.environ, {"VERCEL_API_TOKEN": "test", "AUTOPILOT_AUTO_DEPLOY": "true"}):
            result = asyncio.run(generate_and_deploy(biz, db))

        db.refresh(biz)
        self.assertTrue(result["generated"])
        self.assertTrue(result["deployed"])
        self.assertFalse(result["email_ready"])
        self.assertIsNotNone(result["warning"])
        self.assertEqual(biz.status, "completed")
        self.assertEqual(biz.deployment_url, "https://demo-test.vercel.app")
        self.assertEqual(biz.email_status, "warning")
        self.assertIsNotNone(biz.automation_warning_at)
        self.assertIsNone(biz.automation_error_at)
        db.close()


if __name__ == "__main__":
    unittest.main()
