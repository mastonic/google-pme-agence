import asyncio
import os
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.database import Base, AutomationZone, AutomationRun
from backend.services.autopilot import run_autopilot


class AutopilotTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def test_zone_defaults(self):
        db = self.Session()
        zone = AutomationZone(name="Test", latitude=48.0, longitude=2.0)
        db.add(zone)
        db.commit()
        db.refresh(zone)
        self.assertTrue(zone.enabled)
        self.assertEqual(zone.radius, 1000)
        self.assertEqual(zone.min_opportunity_score, 62.0)
        self.assertEqual(zone.max_sites_per_run, 3)
        db.close()

    def test_run_model_counters_default_to_zero(self):
        db = self.Session()
        run = AutomationRun(trigger="manual")
        db.add(run)
        db.commit()
        db.refresh(run)
        self.assertEqual(run.businesses_scanned, 0)
        self.assertEqual(run.sites_generated, 0)
        self.assertEqual(run.emails_ready, 0)
        db.close()


if __name__ == "__main__":
    unittest.main()
