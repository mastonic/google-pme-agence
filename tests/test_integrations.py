"""Pack Connecté : chiffrement, état OAuth, webhook signé, Google Sheets, créneaux et réservation Google Agenda."""
import datetime
import hashlib
import hmac
import json
import os
import tempfile
import unittest
import urllib.parse
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import receptionist_api as api
from backend.main import app
from backend.models.database import Base, Business, ClientSession, ReceptionistAddon, ReceptionistCall, get_db
from backend.services import integrations as itg
from backend.services import receptionist as rc

TOKEN = "twilio-test-token"
BASE = "http://testserver"
KEY = "une phrase secrete de test"
TZ = ZoneInfo("Europe/Paris")


class UnitTests(unittest.TestCase):
    def setUp(self):
        p = patch.dict(os.environ, {"INTEGRATIONS_KEY": KEY})
        p.start()
        self.addCleanup(p.stop)

    def test_encrypt_roundtrip_and_fernet_key(self):
        enc = itg.encrypt("1//refresh-token")
        self.assertNotIn("refresh", enc)
        self.assertEqual(itg.decrypt(enc), "1//refresh-token")
        from cryptography.fernet import Fernet
        with patch.dict(os.environ, {"INTEGRATIONS_KEY": Fernet.generate_key().decode()}):
            self.assertEqual(itg.decrypt(itg.encrypt("x")), "x")
            with self.assertRaises(itg.IntegrationError):
                itg.decrypt(enc)  # autre clé : illisible
        with patch.dict(os.environ, {"INTEGRATIONS_KEY": ""}):
            with self.assertRaises(itg.IntegrationError):
                itg.encrypt("x")

    def test_state_signed_and_expiring(self):
        st = itg.sign_state("b1", now=1000)
        self.assertEqual(itg.verify_state(st, now=1100), "b1")
        with self.assertRaises(itg.IntegrationError):
            itg.verify_state(st, now=1000 + itg.STATE_TTL + 1)
        payload, sig = st.split(".")
        forged = itg._b64(json.dumps({"b": "autre", "e": 99999999999}).encode()) + "." + sig
        with self.assertRaises(itg.IntegrationError):
            itg.verify_state(forged, now=1100)

    def test_webhook_url_rules(self):
        self.assertTrue(itg.valid_webhook_url("https://hooks.zapier.com/hooks/catch/1/abc"))
        for bad in ("http://hooks.zapier.com/x", "https://localhost/x", "https://127.0.0.1/x", "https://10.0.0.1/x",
                    "https://metadata.google.internal/x", "ftp://a.b/c", "https://intranet/x"):
            self.assertFalse(itg.valid_webhook_url(bad), bad)

    def test_send_webhook_is_signed(self):
        sent = {}

        def post(url, data, timeout, allow_redirects, headers):
            sent.update(url=url, data=data, headers=headers)
            return SimpleNamespace(status_code=200)
        summary = {"caller": {"nom": "Paul", "telephone": "+336"}, "motif": "fuite", "urgence": True, "mode": "ai"}
        with patch.object(itg.requests, "post", post):
            self.assertEqual(itg.send_webhook("https://h.example.com/x", "s3cret",
                                              itg.webhook_payload(SimpleNamespace(id="b1", name="Plomberie"), summary)), 200)
        expected = "sha256=" + hmac.new(b"s3cret", sent["data"], hashlib.sha256).hexdigest()
        self.assertEqual(sent["headers"]["X-Pulse-Signature"], expected)
        body = json.loads(sent["data"])
        self.assertEqual(body["event"], "call.completed")
        self.assertTrue(body["call"]["urgent"])
        self.assertEqual(body["call"]["caller_name"], "Paul")

    def test_slots_follow_opening_hours_and_skip_busy(self):
        b = SimpleNamespace(client_profile={"activity": {"hours": [
            {"day": "lundi", "open": "09:00", "close": "12:00"}, {"day": "lundi", "open": "14:00", "close": "17:00"},
            {"day": "mardi", "closed": True}, {"day": "Mercredi", "open": "10:00", "close": "12:00"}]}})
        hours = itg.opening_hours(b)
        self.assertEqual(set(hours), {"lundi", "mercredi"})
        now = datetime.datetime(2026, 11, 9, 8, 0, tzinfo=TZ)  # lundi 9 novembre, 8 h
        cands = itg.candidate_slots(hours, now, 60)
        self.assertEqual(cands[0], datetime.datetime(2026, 11, 9, 10, 0, tzinfo=TZ))  # délai minimum de 2 h
        self.assertTrue(all(c.weekday() in (0, 2) for c in cands))
        busy = [(datetime.datetime(2026, 11, 9, 10, 0, tzinfo=TZ), datetime.datetime(2026, 11, 9, 11, 30, tzinfo=TZ))]
        cfg = {"google": {"refresh_token_enc": "x", "slot_minutes": 60}, "webhook": {}}
        with patch.object(itg, "access_token", lambda c: "tok"), patch.object(itg, "busy_periods", lambda *a: busy):
            slots = itg.free_slots(b, cfg, now=now.astimezone(datetime.timezone.utc))
        self.assertEqual(slots[0]["label"], "lundi 9 novembre à 14 h")   # 10 h et 11 h occupés
        self.assertNotIn("2026-11-09T10:00:00+01:00", [s["iso"] for s in slots])
        self.assertLessEqual(len(slots), itg.MAX_SLOTS)
        self.assertEqual(itg.opening_hours(SimpleNamespace(client_profile=None)), itg.DEFAULT_HOURS)

    def test_sheet_row(self):
        row = itg.sheet_row({"caller": {"nom": "Paul", "telephone": "+336"}, "motif": "fuite", "urgence": True,
                             "mode": "whatsapp", "rdv": "lundi 9 novembre à 14 h"},
                            when=datetime.datetime(2026, 11, 9, 13, 0))
        self.assertEqual(row[0], "09/11/2026 14:00")  # heure de Paris
        self.assertEqual(row[1:3], ["WhatsApp", "Paul"])
        self.assertEqual(row[5], "Oui")
        self.assertEqual(row[8], "lundi 9 novembre à 14 h")
        self.assertEqual(len(row), len(itg.SHEET_HEADER))

    def test_prompt_with_slots_allows_only_listed_bookings(self):
        b = SimpleNamespace(id="b1", name="Salon Lila", address="", category=["hair_salon"], client_profile=None)
        slots = [{"iso": "2026-11-09T14:00:00+01:00", "label": "lundi 9 novembre à 14 h"}]
        p = rc.build_system_prompt(b, {}, slots)
        self.assertIn("lundi 9 novembre à 14 h → identifiant : 2026-11-09T14:00:00+01:00", p)
        self.assertIn('"rdv": ""', p)
        self.assertNotIn("Tu ne confirmes jamais un créneau", p)
        self.assertIn("Tu ne confirmes jamais un créneau", rc.build_system_prompt(b, {}))
        # Pas de contradiction : avec l'agenda connecté, rien ne dit que les disponibilités sont inconnues.
        self.assertNotIn("toujours inconnus", p)
        self.assertNotIn("de disponibilité ni de rendez-vous", p)
        self.assertIn("tu as accès à l'agenda du gérant", p)
        self.assertIn("[creneau] Propose deux ou trois des créneaux libres", p)
        self.assertIn("toujours inconnus", rc.build_system_prompt(b, {}))
        call = SimpleNamespace(collected={"rdv": "2026-11-09T14:00:00+01:00", "_slots": slots}, transcript=[],
                               from_number="+33", mode="ai", recording_url=None)
        self.assertEqual(rc.build_summary(b, call)["rdv"], "lundi 9 novembre à 14 h")
        call.collected = {"rdv": "2026-11-10T03:00:00+01:00", "_slots": slots}   # créneau inventé : refusé
        self.assertEqual(rc.build_summary(b, call)["rdv"], "")


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        engine = create_engine(f"sqlite:///{os.path.join(self.tmp.name, 'db.sqlite')}",
                               connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        with self.Session() as db:
            db.add(Business(id="salon1", name="Salon Lila", category=["hair_salon"], owner_phone="0612345678",
                            owner_email="lila@salon.fr"))
            db.add(ClientSession(token_hash=__import__("backend.client_space_api", fromlist=["_hash"])._hash("sess"),
                                 business_id="salon1", kind="session",
                                 expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1)))
            db.commit()

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()
        app.dependency_overrides[get_db] = override_db
        self.notified, self.hooks, self.rows, self.events = [], [], [], []
        env = {"TWILIO_AUTH_TOKEN": TOKEN, "ADMIN_API_TOKEN": "adm", "INTEGRATIONS_KEY": KEY,
               "GOOGLE_OAUTH_CLIENT_ID": "cid", "GOOGLE_OAUTH_CLIENT_SECRET": "csec", "FRONTEND_URL": "https://pulse.test"}
        for p in (patch.dict(os.environ, env),
                  patch.object(rc, "notify_owner", lambda b, a, s: self.notified.append(s) or {}),
                  patch.object(itg, "send_webhook", lambda url, secret, payload: self.hooks.append((url, secret, payload)) or 200),
                  patch.object(itg, "access_token", lambda cfg: "tok"),
                  patch.object(itg, "append_row", lambda tok, sid, row: self.rows.append((sid, row))),
                  patch.object(itg, "create_event", lambda cfg, iso, title, desc: self.events.append((iso, title)) or "link")):
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("TWILIO_WEBHOOK_BASE_URL", None)
        self.c = TestClient(app)
        self.h = {"X-Client-Session": "sess"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.tmp.cleanup()

    def post(self, path, params):
        sig = rc.compute_signature(TOKEN, BASE + path, params)
        return self.c.post(path, content=urllib.parse.urlencode(params),
                           headers={"Content-Type": "application/x-www-form-urlencoded", "X-Twilio-Signature": sig})

    def test_requires_active_pack(self):
        self.assertEqual(self.c.put("/client/space/receptionist/integrations", headers=self.h,
                                    json={"webhook_url": "https://hooks.zapier.com/x"}).status_code, 409)
        state = self.c.post("/client/space/receptionist/activate", headers=self.h, json={}).json()
        self.assertEqual(state["connect"]["status"], "trial")  # offert pendant l'essai
        self.assertEqual(state["connect"]["price"], 19)

    def test_webhook_sheets_and_booking_end_to_end(self):
        self.c.post("/client/space/receptionist/activate", headers=self.h, json={})
        bad = self.c.put("/client/space/receptionist/integrations", headers=self.h, json={"webhook_url": "http://x.y"})
        self.assertEqual(bad.status_code, 422)
        st = self.c.put("/client/space/receptionist/integrations", headers=self.h,
                        json={"webhook_url": "https://hooks.zapier.com/hooks/catch/1/abc", "slot_minutes": 30}).json()
        secret = st["connect"]["webhook"]["secret"]
        self.assertEqual(len(secret), 64)
        self.assertEqual(st["connect"]["google"]["slot_minutes"], 30)
        # Google connecté (jeton chiffré) + tableur
        with self.Session() as db:
            addon = db.query(ReceptionistAddon).filter_by(business_id="salon1").one()
            cfg = itg.config(addon)
            cfg["google"].update({"refresh_token_enc": itg.encrypt("rt"), "sheet_id": "SHEET1", "email": "lila@gmail.com"})
            addon.integrations = cfg
            db.commit()
        slots = [{"iso": "2026-11-09T14:00:00+01:00", "label": "lundi 9 novembre à 14 h"},
                 {"iso": "2026-11-10T10:00:00+01:00", "label": "mardi 10 novembre à 10 h"}]
        replies = iter([
            '{"reply": "Je peux vous proposer lundi 14 h ou mardi 10 h.", "fields": {"motif": "coupe"}, "done": false}',
            '{"reply": "C\'est réservé pour lundi 9 novembre à 14 h, Paul. À bientôt !", '
            '"fields": {"rdv": "2026-11-09T14:00:00+01:00", "nom": "Paul"}, "done": true}',
        ])
        prompts = []
        with patch.object(itg, "free_slots", lambda b, cfg, now=None: slots) as _, \
                patch.object(rc, "llm_complete", lambda b, s, p: prompts.append(s) or next(replies)):
            self.post("/receptionist/voice/salon1", {"CallSid": "CA1", "From": "+33611111111"})
            self.post("/receptionist/voice/salon1/turn", {"CallSid": "CA1", "SpeechResult": "Je voudrais une coupe"})
            r = self.post("/receptionist/voice/salon1/turn", {"CallSid": "CA1", "SpeechResult": "Lundi 14 h, Paul"})
        self.assertIn("<Hangup/>", r.text)
        self.assertIn("mardi 10 novembre à 10 h → identifiant", prompts[0])
        self.assertEqual(self.events, [("2026-11-09T14:00:00+01:00", "RDV Paul – coupe")])
        self.assertEqual(self.notified[0]["rdv"], "lundi 9 novembre à 14 h")
        self.assertIn("RDV réservé : lundi 9 novembre à 14 h", rc.format_sms(SimpleNamespace(name="Salon Lila", client_profile=None, address=""), self.notified[0]))
        self.assertEqual(self.rows[0][0], "SHEET1")
        self.assertEqual(self.rows[0][1][8], "lundi 9 novembre à 14 h")
        url, sec, payload = self.hooks[0]
        self.assertEqual((url, sec), ("https://hooks.zapier.com/hooks/catch/1/abc", secret))
        self.assertEqual(payload["call"]["appointment_start"], "2026-11-09T14:00:00+01:00")
        state = self.c.get("/client/space/receptionist/integrations", headers=self.h).json()
        self.assertEqual(state["webhook"]["last_status"], 200)
        self.assertNotIn("refresh_token_enc", json.dumps(state))   # jamais exposé

    def test_failed_booking_becomes_a_wish(self):
        self.c.post("/client/space/receptionist/activate", headers=self.h, json={})
        with self.Session() as db:
            addon = db.query(ReceptionistAddon).filter_by(business_id="salon1").one()
            addon.integrations = {"google": {"refresh_token_enc": itg.encrypt("rt")}, "webhook": {}}
            db.commit()
        slots = [{"iso": "2026-11-09T14:00:00+01:00", "label": "lundi 9 novembre à 14 h"}]

        def boom(*a):
            raise itg.IntegrationError("403")
        with patch.object(itg, "free_slots", lambda b, cfg, now=None: slots), patch.object(itg, "create_event", boom), \
                patch.object(rc, "llm_complete", lambda b, s, p: '{"reply": "Réservé.", "fields": {"rdv": "2026-11-09T14:00:00+01:00"}, "done": true}'):
            self.post("/receptionist/voice/salon1", {"CallSid": "CA2", "From": "+33611111111"})
            self.post("/receptionist/voice/salon1/turn", {"CallSid": "CA2", "SpeechResult": "lundi"})
        self.assertEqual(self.notified[0]["rdv"], "")
        self.assertIn("(à confirmer)", self.notified[0]["creneau"])
        state = self.c.get("/client/space/receptionist/integrations", headers=self.h).json()
        self.assertIn("Réservation dans l'agenda", state["google"]["last_error"])

    def test_google_oauth_start_and_callback(self):
        self.c.post("/client/space/receptionist/activate", headers=self.h, json={})
        url = self.c.post("/client/space/receptionist/integrations/google/start", headers=self.h).json()["url"]
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(q["redirect_uri"], ["https://pulse.test/integrations/google/callback"])
        self.assertIn("https://www.googleapis.com/auth/calendar.events", q["scope"][0])
        self.assertEqual(q["access_type"], ["offline"])
        with patch.object(itg, "exchange_code", lambda code, ru: {"access_token": "at", "refresh_token": "rt-secret"}), \
                patch.object(itg, "userinfo_email", lambda at: "lila@gmail.com"), \
                patch.object(itg, "create_sheet", lambda at, title: ("S1", "https://docs.google.com/s/S1")):
            r = self.c.get("/integrations/google/callback", params={"code": "c", "state": q["state"][0]},
                           follow_redirects=False)
            self.assertEqual(r.status_code, 303)
            self.assertEqual(r.headers["location"], "https://pulse.test/espace/?google=ok#receptionniste")
            bad = self.c.get("/integrations/google/callback", params={"code": "c", "state": "faux.etat"},
                             follow_redirects=False)
            self.assertTrue("google=error#receptionniste" in bad.headers["location"])
        st = self.c.get("/client/space/receptionist/integrations", headers=self.h).json()
        self.assertTrue(st["google"]["connected"])
        self.assertEqual(st["google"]["email"], "lila@gmail.com")
        self.assertEqual(st["google"]["sheet_url"], "https://docs.google.com/s/S1")
        with self.Session() as db:
            stored = db.query(ReceptionistAddon).filter_by(business_id="salon1").one().integrations
            self.assertNotIn("rt-secret", json.dumps(stored))
            self.assertEqual(itg.decrypt(stored["google"]["refresh_token_enc"]), "rt-secret")
        with patch.object(itg, "revoke", lambda cfg: None):
            st = self.c.post("/client/space/receptionist/integrations/google/disconnect", headers=self.h).json()
        self.assertFalse(st["connect"]["google"]["connected"])

    def test_unchecked_calendar_scope_is_reported(self):
        self.assertEqual(itg.missing_scopes({"scope": " ".join(itg.GOOGLE_SCOPES)}), {"calendar": False, "drive": False})
        self.c.post("/client/space/receptionist/activate", headers=self.h, json={})
        url = self.c.post("/client/space/receptionist/integrations/google/start", headers=self.h).json()["url"]
        state = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["state"][0]
        tokens = {"access_token": "at", "refresh_token": "rt", "scope": "openid email " + itg.DRIVE_SCOPE}
        with patch.object(itg, "exchange_code", lambda code, ru: tokens), \
                patch.object(itg, "userinfo_email", lambda at: "lila@gmail.com"), \
                patch.object(itg, "create_sheet", lambda at, title: ("S1", "u")):
            r = self.c.get("/integrations/google/callback", params={"code": "c", "state": state}, follow_redirects=False)
        self.assertIn("google=partial", r.headers["location"])
        st = self.c.get("/client/space/receptionist/integrations", headers=self.h).json()
        self.assertFalse(st["google"]["calendar_enabled"])
        self.assertIn("l'accès à l'agenda n'a pas été coché", st["google"]["last_error"])

    def test_admin_toggle_and_elite_included(self):
        r = self.c.post("/businesses/salon1/receptionist/connect", headers={"X-Admin-Token": "adm"}, json={"paid": True})
        self.assertEqual(r.json()["connect"]["status"], "active")
        with self.Session() as db:
            b = db.query(Business).filter_by(id="salon1").one()
            b.plan_tier, b.subscription_status = "elite", "active"
            db.commit()
        st = self.c.get("/businesses/salon1/receptionist/integrations", headers={"X-Admin-Token": "adm"}).json()
        self.assertEqual(st["status"], "included")


if __name__ == "__main__":
    unittest.main()
