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
        self.assertEqual(state["plans"][2]["quota"], 10)  # Élite : usage raisonnable, 10 demandes / mois
        self.assertEqual(state["plans"][2]["annual_price"], 2990)  # 2 mois offerts

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


    # ── assistant d'onboarding ───────────────────────────────────────────

    def test_second_save_is_persisted(self):
        """Régression : merge_profile modifie le dict en place, la 2e sauvegarde était perdue."""
        h = self.login()
        self.c.put("/client/space/info", headers=h, json={"info": GOOD_INFO, "hours": HOURS})
        self.c.put("/client/space/info", headers=h, json={"info": dict(GOOD_INFO, phone="06 11 22 33 44"), "hours": HOURS})
        with self.Session() as db:
            self.assertEqual(db.get(Business, "hotel1").client_profile["contact"]["phone"], "06 11 22 33 44")

    def test_services_and_social_are_saved(self):
        h = self.login()
        body = {"info": GOOD_INFO, "hours": HOURS,
                "services": [" Chambres  doubles ", "Petit-déjeuner", "petit-déjeuner", ""],
                "social": {"instagram": "https://instagram.com/hotel", "facebook": ""}}
        state = self.c.put("/client/space/info", headers=h, json=body).json()
        self.assertEqual(state["services"], ["Chambres doubles", "Petit-déjeuner"])
        self.assertEqual(state["social"]["instagram"], "https://instagram.com/hotel")
        bad = self.c.put("/client/space/info", headers=h,
                         json=dict(body, social={"tiktok": "tiktok.com/@hotel"})).json()
        self.assertIn("social_tiktok", bad["detail"]["errors"])
        too_many = self.c.put("/client/space/info", headers=h,
                              json=dict(body, services=[f"Service {i}" for i in range(20)])).json()
        self.assertIn("services", too_many["detail"]["errors"])

    def test_wizard_progress_is_remembered(self):
        h = self.login()
        self.assertEqual(self.c.get("/client/space", headers=h).json()["wizard"], {"step": 0, "done": False})
        self.c.post("/client/space/wizard", headers=h, json={"step": 3})
        self.assertEqual(self.c.get("/client/space", headers=h).json()["wizard"], {"step": 3, "done": False})
        self.c.post("/client/space/wizard", headers=h, json={"step": 99, "done": True})
        self.assertEqual(self.c.get("/client/space", headers=h).json()["wizard"], {"step": 6, "done": True})

    def test_raw_google_name_is_displayed_cleanly(self):
        state = self.c.get("/client/space", headers=self.login()).json()
        self.assertEqual(state["info"]["business_name"], "Hôtel de la Gare")


    # ── photos du client appliquées au site existant (sans IA) ───────────

    def test_apply_client_content_to_existing_site(self):
        admin = {"Authorization": f"Bearer {ADMIN}"}
        with self.Session() as db:
            b = db.get(Business, "hotel1")
            b.generated_html = ('<html><body><nav><a>Hôtel</a></nav>'
                                '<img src="https://images.pexels.com/a.jpg"><img src="https://images.unsplash.com/b.jpg">'
                                '</body></html>')
            db.commit()
        nothing = self.c.post("/businesses/hotel1/apply-client-content", headers=admin).json()
        self.assertFalse(nothing["changed"])
        h = self.login()
        logo = self.c.post("/client/space/media", headers=h, json={"kind": "logo", "name": "l.png", "data": data_url(PNG)}).json()
        facade = self.c.post("/client/space/media", headers=h, json={"kind": "devanture", "name": "f.png", "data": data_url(PNG)}).json()
        r = self.c.post("/businesses/hotel1/apply-client-content", headers=admin).json()
        self.assertEqual((r["photos_placed"], r["logo_added"], r["changed"]), (1, True, True))
        with self.Session() as db:
            html = db.get(Business, "hotel1").generated_html
        self.assertIn(f'src="https://pp.test{facade["src"]}"', html)
        self.assertIn(f'<nav><img src="https://pp.test{logo["src"]}"', html)
        self.assertIn("unsplash.com/b.jpg", html)  # une seule photo : la 2e image reste
        again = self.c.post("/businesses/hotel1/apply-client-content", headers=admin).json()
        self.assertFalse(again["changed"])
        self.assertEqual(self.c.post("/businesses/hotel1/apply-client-content").status_code, 401)

    def test_failed_regeneration_still_applies_client_photos(self):
        from backend.models import database
        admin = {"Authorization": f"Bearer {ADMIN}"}
        with self.Session() as db:
            b = db.get(Business, "hotel1")
            b.generated_html = '<html><body><nav></nav><img src="https://images.pexels.com/a.jpg"></body></html>'
            b.status = "completed"
            db.commit()
        h = self.login()
        facade = self.c.post("/client/space/media", headers=h,
                             json={"kind": "devanture", "name": "f.png", "data": data_url(PNG)}).json()
        with patch.object(database, "SessionLocal", self.Session), \
                patch("backend.main.GoogleMapsService.get_business_details", return_value={}), \
                patch("backend.main.LocalPulseManager.run_build_crew", side_effect=RuntimeError("quota IA")):
            self.assertEqual(self.c.post("/businesses/hotel1/regenerate/site", headers=admin).json(),
                             {"status": "started"})
        with self.Session() as db:
            b = db.get(Business, "hotel1")
            self.assertEqual(b.status, "completed")
            self.assertIn(f'src="https://pp.test{facade["src"]}"', b.generated_html)

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

    # ── Vue administrateur & maintenance ─────────────────────────────────────
    def test_admin_view_link_requires_admin_and_opens_client_space(self):
        self.assertEqual(self.c.post("/businesses/hotel1/client-view").status_code, 401)
        admin = {"Authorization": f"Bearer {ADMIN}"}
        r = self.c.post("/businesses/hotel1/client-view", headers=admin)
        self.assertEqual(r.status_code, 200)
        url = r.json()["url"]
        self.assertIn("admin=1", url)
        token = url.split("login=")[1].split("&")[0]
        ex = self.c.post("/client/auth/exchange", json={"token": token})
        self.assertEqual(ex.status_code, 200)
        self.assertTrue(ex.json().get("admin_view"))
        space = self.c.get("/client/space", headers={"X-Client-Session": ex.json()["session"]})
        self.assertEqual(space.status_code, 200)
        self.assertEqual(space.json()["business_id"], "hotel1")
        # usage unique
        self.assertEqual(self.c.post("/client/auth/exchange", json={"token": token}).status_code, 401)
        # session administrateur courte (2 h) et non comptée comme connexion du client
        with self.Session() as db:
            row = db.query(ClientSession).filter(ClientSession.kind == "admin_session").one()
            self.assertLess(row.expires_at - datetime.datetime.utcnow(), datetime.timedelta(hours=2, minutes=1))
        m = self.c.get("/businesses/hotel1/maintenance", headers=admin).json()
        self.assertIsNone(m["client_access"]["last_login"])

    def test_maintenance_reports_details_and_alerts(self):
        admin = {"Authorization": f"Bearer {ADMIN}"}
        self.assertEqual(self.c.get("/businesses/hotel1/maintenance").status_code, 401)
        with self.Session() as db:
            b = db.query(Business).filter(Business.id == "hotel1").one()
            b.subscription_status = "active"
            b.plan_tier = "pro"
            db.commit()
        session = self.login()
        self.c.post("/client/space/requests", json={"cat": "horaires", "msg": "Fermé lundi prochain pour inventaire"},
                    headers=session)
        m = self.c.get("/businesses/hotel1/maintenance", headers=admin)
        self.assertEqual(m.status_code, 200)
        m = m.json()
        for key in ("alerts", "subscription", "site", "audit", "digital_health", "onboarding",
                    "requests", "stats", "client_access", "receptionist"):
            self.assertIn(key, m)
        self.assertEqual(m["subscription"]["plan"], "pro")
        self.assertEqual(m["requests"]["open"], 1)
        self.assertIsNotNone(m["client_access"]["last_login"])
        self.assertTrue(any("aucun site déployé" in a["text"] for a in m["alerts"]))
        self.assertEqual(self.c.get("/businesses/nope/maintenance", headers=admin).status_code, 404)

    # ── Provenance, formulaires, valeur, rapport mensuel ─────────────────────
    def track(self, body):
        return self.c.post("/client/track/hotel1", content=body, headers={"Content-Type": "text/plain"})

    def test_tracking_counts_sources_and_forms(self):
        self.set_live()
        for src in ("google", "google", "gbp", "inconnue!", None):
            self.track('{"e":"visit"' + (f',"src":"{src}"' if src else "") + "}")
        self.track('{"e":"form"}')
        self.track('{"e":"call"}')
        st = self.c.get("/client/space", headers=self.login()).json()
        today = st["daily"][-1]
        self.assertEqual((today["v"], today["f"], today["c"]), (5, 1, 1))
        got = {x["key"]: x["visits"] for x in st["sources"]}
        self.assertEqual(got, {"google": 2, "gbp": 1, "autre_site": 1, "direct": 1})
        self.assertEqual(st["sources"][0]["key"], "google")

    def test_inject_tracking_replaces_old_snippet(self):
        old = '<html><body>x<script>(function(){var u="https://pp.test/client/track/hotel1";})();</script></body></html>'
        html = api.inject_tracking(old, "hotel1")
        self.assertEqual(html.count("/client/track/"), 1)
        self.assertIn("data-pp-track", html)
        self.assertIn("'form'", html)
        self.assertEqual(api.inject_tracking(html, "hotel1").count("/client/track/"), 1)

    def test_avg_ticket_and_potential_value(self):
        self.set_live()
        h = self.login()
        self.assertEqual(self.c.put("/client/space/avg-ticket", json={"avg_ticket": "abc"}, headers=h).status_code, 422)
        self.assertEqual(self.c.put("/client/space/avg-ticket", json={"avg_ticket": 0}, headers=h).status_code, 422)
        r = self.c.put("/client/space/avg-ticket", json={"avg_ticket": "80,4 €"}, headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["avg_ticket"], 80)
        for e in ("call", "call", "whatsapp", "form", "directions"):
            self.track(f'{{"e":"{e}"}}')
        m = self.c.get("/businesses/hotel1/maintenance", headers={"Authorization": f"Bearer {ADMIN}"}).json()
        self.assertEqual(m["stats"]["avg_ticket"], 80)
        self.assertEqual(m["stats"]["value30"], 4 * 80)  # 2 appels + 1 WhatsApp + 1 formulaire
        self.assertIsNone(self.c.put("/client/space/avg-ticket", json={"avg_ticket": ""}, headers=h).json()["avg_ticket"])

    def test_monthly_report_preview_send_and_once_per_month(self):
        from backend.services import monthly_report as mr
        self.set_live()
        admin = {"Authorization": f"Bearer {ADMIN}"}
        today = datetime.date.today()
        period = mr.last_closed_period(today)
        start, _ = mr.month_bounds(period)
        with self.Session() as db:
            db.add(SiteDailyStat(business_id="hotel1", day=start.isoformat(), visits=40, calls=6, whatsapp=2,
                                 directions=3, forms=1, sources={"google": 30, "direct": 10}))
            b = db.get(Business, "hotel1")
            b.client_profile = {"activity": {"avg_ticket": 50}}
            db.commit()
        self.assertEqual(self.c.get(f"/businesses/hotel1/monthly-report?period=2026-13", headers=admin).status_code, 422)
        r = self.c.get(f"/businesses/hotel1/monthly-report?period={period}", headers=admin)
        self.assertEqual(r.status_code, 200, r.text)
        rep = r.json()
        self.assertEqual({m["key"]: m["value"] for m in rep["metrics"]}["visits"], 40)
        self.assertEqual(rep["contacts"], 9)
        self.assertEqual(rep["value"], 450)
        self.assertEqual(rep["sources"][0]["label"], "Google (recherche)")
        self.assertIn("40", rep["text"])
        self.assertIn("<html", rep["html"])

        sent = []
        with patch.object(mr, "send_email", lambda to, subj, text, html=None: sent.append((to, subj)) or True):
            r = self.c.post(f"/businesses/hotel1/monthly-report/send?period={period}", headers=admin)
            self.assertEqual(r.status_code, 200, r.text)
            with self.Session() as db:
                first = mr.send_monthly_reports(db, period)
                self.assertEqual(first["sent"], 0)  # déjà envoyé manuellement pour ce mois
                self.assertEqual(mr.send_monthly_reports(db, period, force=True)["sent"], 1)
        self.assertEqual(len(sent), 2)
        self.assertEqual(sent[0][0], "Gerant@Hotel.fr")

    def test_monthly_periods(self):
        from backend.services import monthly_report as mr
        self.assertEqual(mr.last_closed_period(datetime.date(2026, 1, 1)), "2025-12")
        self.assertEqual(mr.previous_period("2026-01"), "2025-12")
        self.assertEqual(mr.month_bounds("2026-02"), (datetime.date(2026, 2, 1), datetime.date(2026, 2, 28)))


if __name__ == "__main__":
    unittest.main()
