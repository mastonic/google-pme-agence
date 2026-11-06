"""Onglet « Vidéo » du cockpit : génération, suivi et lecture de la présentation."""
import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.models import database
from backend.models.database import Base, Business, BusinessVideo, get_db

TOKEN = "video-test-token"
MP4 = b"\x00\x00\x00\x18ftypmp42fake-video"


class FakeManager:
    fail = False

    def __init__(self, business_data, log_queue=None):
        self.business_data = business_data

    def render_motion_video(self, site_html=None, site_url=""):
        if FakeManager.fail:
            raise RuntimeError("ffmpeg indisponible")
        return MP4, 41.6


class VideoRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        engine = create_engine(f"sqlite:///{os.path.join(self.tmp.name, 'test.db')}",
                               connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        with self.Session() as db:
            db.add(Business(id="biz1", name="Plomberie Dupont", rating=4.7, user_ratings_total=52))
            db.commit()

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        FakeManager.fail = False
        for p in (patch.dict(os.environ, {"ADMIN_API_TOKEN": TOKEN}),
                  patch.object(database, "SessionLocal", self.Session),
                  patch("backend.main.LocalPulseManager", FakeManager)):
            p.start()
            self.addCleanup(p.stop)
        self.client = TestClient(app, headers={"Authorization": f"Bearer {TOKEN}"})

    def tearDown(self):
        app.dependency_overrides.pop(get_db, None)
        self.tmp.cleanup()

    def test_no_video_yet(self):
        self.assertEqual(self.client.get("/businesses/biz1/video/status").json(), {"status": "none"})
        self.assertEqual(self.client.get("/businesses/biz1/video").status_code, 404)

    def test_generate_then_play(self):
        self.assertEqual(self.client.post("/businesses/biz1/video").json(), {"status": "running"})
        status = self.client.get("/businesses/biz1/video/status").json()
        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["seconds"], 41.6)
        resp = self.client.get("/businesses/biz1/video")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "video/mp4")
        self.assertEqual(resp.content, MP4)

    def test_failure_is_reported_and_can_be_retried(self):
        FakeManager.fail = True
        self.client.post("/businesses/biz1/video")
        status = self.client.get("/businesses/biz1/video/status").json()
        self.assertEqual(status["status"], "error")
        self.assertIn("ffmpeg", status["error"])
        FakeManager.fail = False
        self.client.post("/businesses/biz1/video")
        self.assertEqual(self.client.get("/businesses/biz1/video/status").json()["status"], "ready")

    def test_running_job_is_not_started_twice(self):
        with self.Session() as db:
            db.add(BusinessVideo(business_id="biz1", status="running"))
            db.commit()
        with patch.object(FakeManager, "render_motion_video", side_effect=AssertionError("relancé")):
            self.assertEqual(self.client.post("/businesses/biz1/video").json(), {"status": "running"})

    def test_stale_running_job_can_be_restarted(self):
        with self.Session() as db:
            db.add(BusinessVideo(business_id="biz1", status="running",
                                 updated_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1)))
            db.commit()
        self.assertEqual(self.client.get("/businesses/biz1/video/status").json()["status"], "error")
        self.client.post("/businesses/biz1/video")
        self.assertEqual(self.client.get("/businesses/biz1/video/status").json()["status"], "ready")

    def test_unknown_business(self):
        self.assertEqual(self.client.post("/businesses/nope/video").status_code, 404)

    def test_video_requires_admin_token(self):
        anonymous = TestClient(app)
        self.assertEqual(anonymous.get("/businesses/biz1/video").status_code, 401)


    def test_public_presentation_page_and_ranges(self):
        anonymous = TestClient(app)  # lien ouvert par le prospect : sans jeton admin
        self.assertEqual(anonymous.get("/presentation/biz1").status_code, 404)
        self.client.post("/businesses/biz1/video")
        page = anonymous.get("/presentation/biz1")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Plomberie Dupont", page.text)
        self.assertIn('src="/presentation/biz1/video.mp4"', page.text)
        self.assertIn("42 secondes", page.text)
        full = anonymous.get("/presentation/biz1/video.mp4")
        self.assertEqual(full.content, MP4)
        self.assertEqual(full.headers["accept-ranges"], "bytes")
        part = anonymous.get("/presentation/biz1/video.mp4", headers={"Range": "bytes=0-3"})
        self.assertEqual(part.status_code, 206)
        self.assertEqual(part.content, MP4[:4])
        self.assertEqual(part.headers["content-range"], f"bytes 0-3/{len(MP4)}")
        tail = anonymous.get("/presentation/biz1/video.mp4", headers={"Range": "bytes=-5"})
        self.assertEqual(tail.content, MP4[-5:])
        bad = anonymous.get("/presentation/biz1/video.mp4", headers={"Range": f"bytes={len(MP4)}-"})
        self.assertEqual(bad.status_code, 416)


if __name__ == "__main__":
    unittest.main()
