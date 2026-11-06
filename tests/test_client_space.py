"""Espace client PulsePro : connexion, onboarding, médias, demandes, statistiques."""
import base64
import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import client_space_api as api
from backend.main import app
from backend.models.database import Base, Business, ClientSession, SiteDailyStat, get_db

ADMIN = "admin-token-space"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
GOOD_INFO = {
    "business_name": "Hôtel de la Gare", "phone": "01 30 45 67 89", "whatsapp": "",
    "address": "1 place de la Gare, 78190 Trappes", "maps": "",
    "description": "Hôtel familial de 24 chambres, à deux pas de la gare de Trappes.",
}
HOURS = [{"day": d, "closed": False, "open": "08:00", "close": "20:00"} for d in api.DAYS]


def data_url(content: bytes, mime="image/png") -> str:
    return f"data:{mime};base64," + base64.b64encode(content).decode()


class ClientSpaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        engine = create_engine(f"sqlite:///{os.path.join(self.tmp.name, 'db.sqlite')}",
                               connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        with self.Session() as db:
            db.add(Business(id="hotel1", name="HÔTEL DE LA GARE", owner_email="Gerant@Hotel.fr",
                            owner_first_name="Sam", onboarding_token="onb-token-123",
                            generated_html="<html><body>site</body></html>", plan_tier="free",
                            subscription_status="inactive"))
            db.commit()

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.sent = []
        for p in (patch.dict(os.environ, {"ADMIN_API_TOKEN": ADMIN, "PUBLIC_BASE_URL": "https://pp.test"}),
                  patch.object(api, "send_login_email", lambda to, name, link: self.sent.append((to, link)) or True)):
            p.start()
            self.addCleanup(p.stop)
        self.c = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(get_db, None)
        self.tmp.cleanup()

    def login(self, token="onb-token-123"):
        r = self.c.post("/client/auth/exchange", json={"token": token})
        self.assertEqual(r.status_code, 200, r.text)
        return {"X-Client-Session": r.json()["session"]}

    def set_live(self):
        with self.Session() as db:
            b = db.get(Business, "hotel1")
            b.subscription_status, b.plan_tier = "active", "pro"
            db.commit()

    # ── connexion ────────────────────────────────────────────────────────

    def test_space_requires_session(self):
        self.assertEqual(self.c.get("/client/space").status_code, 401)
        self.assertEqual(self.c.get("/client/space", headers={"X-Client-Session": "faux"}).status_code, 401)

    def test_onboarding_link_opens_a_session(self):
        state = self.c.get("/client/space", headers=self.login()).json()
        self.assertEqual(state["status"], "onboarding")
        self.assertEqual(state["step"], 2)  # site déjà généré : aperçu à valider
        self.assertEqual(state["first_name"], "Sam")
        self.assertEqual(state["preview_url"], "/preview/hotel1")
        self.assertEqual([p["slug"] for p in state["plans"]], ["starter", "pro", "elite"])
        self.assertIsNone(state["plans"][2]["quota"])  # Élite : illimité

    def test_email_link_is_single_use_and_case_insensitive(self):
        self.assertEqual(self.c.post("/client/auth/request", json={"email": "gerant@hotel.fr"}).json(),
                         {"status": "sent"})
        to, link = self.sent[0]
        self.assertEqual(to, "gerant@hotel.fr")
        self.assertTrue(link.startswith("https://pp.test/espace/?login="))
        token = link.split("login=")[1]
        self.login(token)
        self.assertEqual(self.c.post("/client/auth/exchange", json={"token": token}).status_code, 401)

    def test_unknown_email_gets_same_answer_and_no_mail(self):
        self.assertEqual(self.c.post("/client/auth/request", json={"email": "x@y.fr"}).json(), {"status": "sent"})
        self.assertEqual(self.sent, [])

    def test_login_links_are_rate_limited(self):
        for _ in range(8):
            self.c.post("/client/auth/request", json={"email": "gerant@hotel.fr"})
        self.assertEqual(len(self.sent), api.MAX_LOGIN_LINKS_PER_HOUR)

    def test_expired_login_link_is_refused(self):
        with self.Session() as db:
            db.add(ClientSession(token_hash=api._hash("old"), business_id="hotel1", kind="login",
                                 expires_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=1)))
            db.commit()
        self.assertEqual(self.c.post("/client/auth/exchange", json={"token": "old"}).status_code, 401)

    def test_logout_ends_session(self):
        h = self.login()
        self.c.post("/client/auth/logout", headers=h)
        self.assertEqual(self.c.get("/client/space", headers=h).status_code, 401)

    # ── onboarding ───────────────────────────────────────────────────────

    def test_info_is_validated_then_saved(self):
        h = self.login()
        bad = self.c.put("/client/space/info", headers=h, json={"info": dict(GOOD_INFO, phone="12"), "hours": HOURS})
        self.assertEqual(bad.status_code, 422)
        self.assertIn("phone", bad.json()["detail"]["errors"])
        state = self.c.put("/client/space/info", headers=h, json={"info": GOOD_INFO, "hours": HOURS}).json()
        self.assertEqual(state["info"]["description"], GOOD_INFO["description"])
        self.assertEqual(state["hours"][0]["open"], "08:00")
        with self.Session() as db:
            profile = db.get(Business, "hotel1").client_profile
        self.assertEqual(profile["contact"]["phone"], "01 30 45 67 89")

    def test_hours_must_close_after_opening(self):
        hours = [dict(h) for h in HOURS]
        hours[2]["close"] = "07:00"
        r = self.c.put("/client/space/info", headers=self.login(), json={"info": GOOD_INFO, "hours": hours})
        self.assertIn("hours", r.json()["detail"]["errors"])

    def test_media_upload_read_delete(self):
        h = self.login()
        up = self.c.post("/client/space/media", headers=h,
                         json={"kind": "devanture", "name": "facade.png", "data": data_url(PNG)}).json()
        img = self.c.get(up["src"])
        self.assertEqual(img.headers["content-type"], "image/png")
        self.assertEqual(img.content, PNG)
        with self.Session() as db:
            photos = db.get(Business, "hotel1").client_profile["media"]["photos"]
        self.assertEqual(photos[0]["url"], f"https://pp.test{up['src']}")
        self.assertEqual(self.c.delete(f"/client/space/media/{up['id']}", headers=h).status_code, 200)
        self.assertEqual(self.c.get(up["src"]).status_code, 404)

    def test_media_rejects_non_images_and_replaces_logo(self):
        h = self.login()
        bad = self.c.post("/client/space/media", headers=h,
                          json={"kind": "logo", "name": "x.png", "data": data_url(b"<html>nope</html>")})
        self.assertEqual(bad.status_code, 415)
        for _ in range(2):
            self.c.post("/client/space/media", headers=h, json={"kind": "logo", "name": "logo.png", "data": data_url(PNG)})
        self.assertEqual(len(self.c.get("/client/space", headers=h).json()["media"]["logo"]), 1)

    def test_other_client_cannot_delete_my_media(self):
        h = self.login()
        up = self.c.post("/client/space/media", headers=h,
                         json={"kind": "equipe", "name": "a.png", "data": data_url(PNG)}).json()
        with self.Session() as db:
            db.add(Business(id="other", name="Autre", onboarding_token="other-token"))
            db.commit()
        r = self.c.delete(f"/client/space/media/{up['id']}", headers=self.login("other-token"))
        self.assertEqual(r.status_code, 404)

    def test_checkout_returns_stripe_url(self):
        class FakeSession:
            url = "https://checkout.stripe.test/s"
        with patch("backend.main._create_stripe_checkout", return_value=FakeSession()) as create:
            r = self.c.post("/client/space/checkout", headers=self.login(), json={"plan": "pro"})
        self.assertEqual(r.json(), {"url": "https://checkout.stripe.test/s"})
        self.assertEqual(create.call_args.args[1], "pro")

    # ── site en ligne ────────────────────────────────────────────────────

    def test_requests_only_once_live(self):
        h = self.login()
        msg = {"cat": "horaires", "msg": "Fermé le 11 novembre, réouverture le 12."}
        self.assertEqual(self.c.post("/client/space/requests", headers=h, json=msg).status_code, 409)
        self.set_live()
        with patch("backend.services.alerts.send_alert"):
            created = self.c.post("/client/space/requests", headers=h, json=msg).json()
        self.assertEqual(created["status"], "nouvelle")
        state = self.c.get("/client/space", headers=h).json()
        self.assertEqual(state["status"], "live")
        self.assertEqual(state["requests"][0]["msg"], msg["msg"])
        admin = {"Authorization": f"Bearer {ADMIN}"}
        done = self.c.patch(f"/client-requests/{created['id']}", headers=admin, json={"status": "terminee"})
        self.assertEqual(done.json()["status"], "terminee")

    def test_tracking_counts_events_into_daily_stats(self):
        for e in ("visit", "visit", "call", "whatsapp", "directions", "nimporte"):
            r = self.c.post("/client/track/hotel1", content=f'{{"e":"{e}"}}', headers={"Content-Type": "text/plain"})
            self.assertEqual(r.status_code, 204)
        self.c.post("/client/track/hotel1", content='{"e":"visit"}', headers={"User-Agent": "Googlebot"})
        self.set_live()
        today = self.c.get("/client/space", headers=self.login()).json()["daily"][-1]
        self.assertEqual((today["v"], today["c"], today["w"], today["d"]), (2, 1, 1, 1))
        with self.Session() as db:
            self.assertEqual(db.query(SiteDailyStat).count(), 1)

    def test_tracking_script_is_injected_once(self):
        html = api.inject_tracking("<html><body><p>x</p></body></html>", "hotel1")
        self.assertIn("https://pp.test/client/track/hotel1", html)
        self.assertLess(html.index("sendBeacon"), html.index("</body>"))
        self.assertEqual(api.inject_tracking(html, "hotel1"), html)

    # ── cockpit ──────────────────────────────────────────────────────────

    def test_admin_view_needs_admin_token_and_gives_login_link(self):
        self.assertEqual(self.c.get("/businesses/hotel1/client-space").status_code, 401)
        r = self.c.get("/businesses/hotel1/client-space", headers={"Authorization": f"Bearer {ADMIN}"}).json()
        self.assertEqual(r["login_url"], "https://pp.test/espace/?t=onb-token-123")
        self.assertEqual(r["status"], "onboarding")


if __name__ == "__main__":
    unittest.main()
