"""Réceptionniste IA : prompt par métier, urgence, essai 30 jours, TwiML, signature Twilio."""
import datetime
import os
import tempfile
import unittest
import urllib.parse
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend import receptionist_api as api
from backend.main import app
from backend.models.database import (
    Base, Business, ClientSession, ReceptionistAddon, ReceptionistCall, get_db,
)
from backend.services import plans
from backend.services import receptionist as rc

TOKEN = "twilio-test-token"
BASE = "http://testserver"
NOW = datetime.datetime(2026, 11, 1, 12, 0, 0)


def biz(**kw):
    defaults = dict(id="b1", name="", address="", category=[], client_profile=None,
                    owner_phone="06 12 34 56 78", owner_email="gerant@test.fr")
    defaults.update(kw)
    return SimpleNamespace(**defaults)


class ProfessionPromptTests(unittest.TestCase):
    def test_profession_detection(self):
        self.assertEqual(rc.detect_profession(biz(category=["electrician"])), "electricien")
        self.assertEqual(rc.detect_profession(biz(category=["plumber"])), "plombier")
        self.assertEqual(rc.detect_profession(biz(name="Salon Coiff'Elle")), "coiffeur")
        self.assertEqual(rc.detect_profession(biz(name="Taxi Trappes")), "taxi")
        self.assertEqual(rc.detect_profession(biz(category=["restaurant"])), "restaurant")
        self.assertEqual(rc.detect_profession(biz(category=["car_repair"])), "garage")
        # Secteur générique via la détection existante (SECTOR_TYPE_MAP)
        self.assertEqual(rc.detect_profession(biz(category=["roofing_contractor"])), "artisan")
        self.assertEqual(rc.detect_profession(biz(category=["lawyer"], name="Cabinet X")), "generic")
        self.assertEqual(rc.detect_profession(biz(category='["dentist"]')), "medical")

    def test_prompts_per_profession(self):
        elec = rc.build_system_prompt(biz(name="ELEC PRO 78", category=["electrician"]))
        self.assertIn("électricien", elec)
        self.assertIn("[urgence]", elec)
        self.assertIn("[adresse]", elec)
        resto = rc.build_system_prompt(biz(name="Chez Lulu", category=["restaurant"]))
        self.assertIn("combien de personnes", resto)
        self.assertNotIn("[adresse]", resto)
        taxi = rc.build_system_prompt(biz(name="Taxi Max"))
        self.assertIn("prise en charge", taxi)
        med = rc.build_system_prompt(biz(name="Dr X", category=["doctor"]))
        self.assertIn("conseil médical", med)
        generic = rc.build_system_prompt(biz(name="Société Y"))
        self.assertIn("Quel est l'objet de votre appel", generic)

    def test_prompt_uses_only_real_data(self):
        profile = {
            "contact": {"address": "3 rue des Lilas, 78190 Trappes"},
            "activity": {"description": "Dépannage électrique 7j/7", "services": ["Dépannage", "Tableau électrique"],
                         "hours": [{"day": "lundi", "closed": False, "open": "08:00", "close": "18:00"},
                                   {"day": "dimanche", "closed": True}]},
            "pricing": [{"label": "Déplacement", "price": "49 €"}],
        }
        p = rc.build_system_prompt(biz(name="ELEC PRO", category=["electrician"], client_profile=profile))
        for fact in ("3 rue des Lilas", "Tableau électrique", "lundi : 08:00–18:00", "dimanche : fermé",
                     "Déplacement : 49 €", "Dépannage électrique 7j/7"):
            self.assertIn(fact, p)

    def test_no_invented_data_when_unknown(self):
        p = rc.build_system_prompt(biz(name="Plomberie Martin", category=["plumber"]))
        known = p.split("INFORMATIONS CONNUES")[1].split("INFORMATIONS INCONNUES")[0]
        unknown = p.split("INFORMATIONS INCONNUES")[1].split("RÈGLES STRICTES")[0]
        self.assertNotIn("€", p)
        self.assertNotRegex(known, r"\d{1,2}[:h]\d{2}")   # aucun horaire par défaut
        for label in ("Tarifs", "Horaires", "Adresse", "Prestations"):
            self.assertIn(f"- {label}", unknown)
            self.assertNotIn(f"- {label} :", known)
        self.assertIn("N'invente JAMAIS de prix", p)
        self.assertIn("rappellera", p)

    def test_fallback_script_without_llm(self):
        b = biz(name="Plomberie Martin", category=["plumber"])
        with patch.object(rc, "llm_complete", side_effect=RuntimeError("quota")):
            r1 = rc.next_turn(b, [{"role": "caller", "text": "J'ai une fuite"}], {}, "J'ai une fuite")
        self.assertTrue(r1["fields"]["urgence"])
        self.assertFalse(r1["done"])
        self.assertTrue(r1["reply"].endswith("?"))
        self.assertNotIn("€", r1["reply"])


class UrgencyTests(unittest.TestCase):
    def test_urgent_keywords(self):
        for t in ("J'ai une grosse fuite d'eau", "Coupure de courant chez moi", "La chaudière est en PANNE",
                  "C'est une urgence", "Je suis bloqué dehors", "ça sent le gaz", "plus d'électricité"):
            self.assertTrue(rc.detect_urgency(t), t)

    def test_not_urgent(self):
        for t in ("Je voudrais un devis pour une salle de bain", "Réserver pour 4 personnes samedi",
                  "Ce n'est pas urgent", "pas d'urgence, la semaine prochaine", "Bonjour", ""):
            self.assertFalse(rc.detect_urgency(t), t)


class TrialTests(unittest.TestCase):
    def test_trial_lifecycle(self):
        s = SimpleNamespace(trial_started_at=None, trial_ends_at=None, paid_active=False)
        self.assertEqual(plans.addon_status(None), "inactive")
        self.assertEqual(plans.addon_status(s, NOW), "inactive")
        plans.start_addon_trial(s, NOW)
        self.assertEqual(s.trial_ends_at - s.trial_started_at, datetime.timedelta(days=30))
        self.assertEqual(plans.addon_status(s, NOW), "trial")
        self.assertEqual(plans.days_left(s, NOW), 30)
        self.assertEqual(plans.days_left(s, NOW + datetime.timedelta(days=29, hours=1)), 1)
        later = NOW + datetime.timedelta(days=30, seconds=1)
        self.assertEqual(plans.addon_status(s, later), "expired")
        self.assertEqual(plans.days_left(s, later), 0)
        self.assertFalse(plans.addon_ai_enabled(s, later))
        # Réactiver ne relance pas l'essai
        plans.start_addon_trial(s, later)
        self.assertEqual(plans.addon_status(s, later), "expired")
        s.paid_active = True
        self.assertEqual(plans.addon_status(s, later), "active")
        self.assertTrue(plans.addon_ai_enabled(s, later))
        self.assertIn(plans.RECEPTIONIST_ADDON, plans.ADDON_CATALOG)


class SignatureTests(unittest.TestCase):
    def test_signature_matches_twilio_reference(self):
        # Exemple de la documentation Twilio (« Validating requests »).
        url = "https://mycompany.com/myapp.php?foo=1&bar=2"
        params = {"CallSid": "CA1234567890ABCDE", "Caller": "+12349013030", "Digits": "1234",
                  "From": "+12349013030", "To": "+18005551212"}
        self.assertEqual(rc.compute_signature("12345", url, params), "0/KCTR6DLpKmkAf8muzZqo1nDgQ=")
        self.assertTrue(rc.valid_signature(url, params, "0/KCTR6DLpKmkAf8muzZqo1nDgQ=", "12345"))
        self.assertFalse(rc.valid_signature(url, params, "bad", "12345"))
        self.assertFalse(rc.valid_signature(url, params, "0/KCTR6DLpKmkAf8muzZqo1nDgQ=", ""))


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        engine = create_engine(f"sqlite:///{os.path.join(self.tmp.name, 'db.sqlite')}",
                               connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        with self.Session() as db:
            db.add(Business(id="elec1", name="ELEC PRO 78", category=["electrician"],
                            owner_phone="06 12 34 56 78", owner_email="gerant@elec.fr"))
            db.commit()

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.notified = []
        for p in (patch.dict(os.environ, {"TWILIO_AUTH_TOKEN": TOKEN, "ADMIN_API_TOKEN": "adm"}),
                  patch.object(rc, "notify_owner", lambda b, a, s: self.notified.append(s) or {"sms": True})):
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("TWILIO_WEBHOOK_BASE_URL", None)
        self.c = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.tmp.cleanup()

    def post(self, path, params, sign=True):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if sign:
            headers["X-Twilio-Signature"] = rc.compute_signature(TOKEN, BASE + path, params)
        return self.c.post(path, content=urllib.parse.urlencode(params), headers=headers)

    def start_trial(self, ends_in_days=30):
        with self.Session() as db:
            db.add(ReceptionistAddon(business_id="elec1", trial_started_at=datetime.datetime.utcnow(),
                                     trial_ends_at=datetime.datetime.utcnow() + datetime.timedelta(days=ends_in_days)))
            db.commit()

    def test_rejects_unsigned_and_bad_signature(self):
        params = {"CallSid": "CA1", "From": "+33611111111"}
        self.assertEqual(self.post("/receptionist/voice/elec1", params, sign=False).status_code, 403)
        r = self.c.post("/receptionist/voice/elec1", content=urllib.parse.urlencode(params),
                        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Twilio-Signature": "forged"})
        self.assertEqual(r.status_code, 403)
        with patch.dict(os.environ, {"TWILIO_AUTH_TOKEN": ""}):
            self.assertEqual(self.post("/receptionist/voice/elec1", params).status_code, 403)

    def test_ai_call_flow(self):
        self.start_trial()
        r = self.post("/receptionist/voice/elec1", {"CallSid": "CA1", "From": "+33611111111"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/xml", r.headers["content-type"])
        self.assertIn('<Gather input="speech" language="fr-FR"', r.text)
        self.assertIn("/receptionist/voice/elec1/turn", r.text)
        self.assertIn("Elec Pro 78", r.text)

        replies = iter([
            '{"reply": "Je note. À quelle adresse ?", "fields": {"motif": "coupure de courant", "urgence": true}, "done": false}',
            '```json\n{"reply": "Merci Paul, le gérant vous rappelle très vite. Au revoir !", '
            '"fields": {"adresse": "3 rue des Lilas Trappes", "nom": "Paul", "creneau": "aujourd\'hui"}, "done": true}\n```',
        ])
        with patch.object(rc, "llm_complete", lambda b, s, p: next(replies)):
            r = self.post("/receptionist/voice/elec1/turn",
                          {"CallSid": "CA1", "From": "+33611111111", "SpeechResult": "Plus de courant dans la maison"})
            self.assertIn("<Gather", r.text)
            self.assertIn("À quelle adresse", r.text)
            r = self.post("/receptionist/voice/elec1/turn",
                          {"CallSid": "CA1", "From": "+33611111111", "SpeechResult": "3 rue des Lilas, je suis Paul"})
        self.assertIn("<Hangup/>", r.text)
        self.assertNotIn("<Gather", r.text)

        self.assertEqual(len(self.notified), 1)
        s = self.notified[0]
        self.assertEqual(s["motif"], "coupure de courant")
        self.assertTrue(s["urgence"])
        self.assertTrue(s["rappel"])
        self.assertEqual(s["caller"], {"nom": "Paul", "telephone": "+33611111111"})
        self.assertEqual(s["creneau"], "aujourd'hui")

        # Status callback après raccroché : pas de double notification
        self.assertEqual(self.post("/receptionist/voice/elec1/status",
                                   {"CallSid": "CA1", "CallStatus": "completed"}).status_code, 204)
        self.assertEqual(len(self.notified), 1)

        state = self.c.get("/businesses/elec1/receptionist", headers={"X-Admin-Token": "adm"}).json()
        self.assertEqual(state["status"], "trial")
        self.assertEqual(state["stats"], {"received": 1, "recovered": 1, "urgent": 1, "recovered_30d": 1})

    def test_caller_hangs_up_midway_is_still_notified(self):
        self.start_trial()
        self.post("/receptionist/voice/elec1", {"CallSid": "CA2", "From": "+33622222222"})
        with patch.object(rc, "llm_complete", side_effect=RuntimeError("down")):
            r = self.post("/receptionist/voice/elec1/turn", {"CallSid": "CA2", "SpeechResult": "J'ai une fuite"})
        self.assertIn("<Gather", r.text)
        self.post("/receptionist/voice/elec1/status", {"CallSid": "CA2", "CallStatus": "completed"})
        self.assertEqual(len(self.notified), 1)
        self.assertTrue(self.notified[0]["urgence"])

    def test_expired_trial_plays_voicemail_without_ai(self):
        self.start_trial(ends_in_days=-1)
        with patch.object(rc, "llm_complete", side_effect=AssertionError("LLM interdit après l'essai")):
            r = self.post("/receptionist/voice/elec1", {"CallSid": "CA3", "From": "+33633333333"})
            self.assertIn("<Record", r.text)
            self.assertIn("/receptionist/voice/elec1/voicemail", r.text)
            self.assertNotIn("<Gather", r.text)
            r = self.post("/receptionist/voice/elec1/voicemail",
                          {"CallSid": "CA3", "From": "+33633333333", "RecordingUrl": "https://api.twilio.com/rec/RE1"})
        self.assertIn("<Hangup/>", r.text)
        self.assertEqual(self.notified[0]["mode"], "voicemail")
        self.assertEqual(self.notified[0]["enregistrement"], "https://api.twilio.com/rec/RE1")
        with self.Session() as db:
            call = db.query(ReceptionistCall).filter_by(call_sid="CA3").one()
            self.assertTrue(call.recovered)

    def test_never_activated_uses_voicemail(self):
        r = self.post("/receptionist/voice/elec1", {"CallSid": "CA4", "From": "+33644444444"})
        self.assertIn("<Record", r.text)

    def test_whatsapp_inbound_conversation(self):
        self.start_trial()
        replies = iter([
            '{"reply": "Quelle adresse ?", "fields": {"motif": "panne de courant"}, "done": false}',
            '{"reply": "Merci, on vous recontacte vite.", "fields": {"adresse": "Trappes"}, "done": true}',
        ])
        with patch.object(rc, "llm_complete", lambda b, s, p: next(replies)):
            r = self.post("/receptionist/whatsapp/elec1", {"From": "whatsapp:+33655555555", "Body": "Panne de courant"})
            self.assertIn("<Message>Quelle adresse ?</Message>", r.text)
            r = self.post("/receptionist/whatsapp/elec1", {"From": "whatsapp:+33655555555", "Body": "A Trappes"})
        self.assertIn("recontacte", r.text)
        self.assertEqual(len(self.notified), 1)
        self.assertEqual(self.notified[0]["adresse"], "Trappes")
        self.assertTrue(self.notified[0]["urgence"])
        with self.Session() as db:
            self.assertEqual(db.query(ReceptionistCall).filter_by(mode="whatsapp").count(), 1)
        self.assertEqual(self.post("/receptionist/whatsapp/elec1", {"From": "whatsapp:+33655555555", "Body": "x"},
                                   sign=False).status_code, 403)

    def test_whatsapp_after_trial_just_forwards(self):
        self.start_trial(ends_in_days=-1)
        with patch.object(rc, "llm_complete", side_effect=AssertionError("pas d'IA")):
            r = self.post("/receptionist/whatsapp/elec1", {"From": "whatsapp:+33655555555", "Body": "Devis tableau"})
        self.assertIn("<Message>", r.text)
        self.assertEqual(self.notified[0]["motif"], "Devis tableau")

    def test_admin_sets_channels(self):
        state = self.c.post("/businesses/elec1/receptionist/activate", headers={"X-Admin-Token": "adm"},
                            json={"notify_channels": ["email", "bogus"], "paid_active": True}).json()
        self.assertEqual(state["notify_channels"], ["email"])
        self.assertEqual(state["status"], "active")

    def test_unknown_business_hangs_up(self):
        r = self.post("/receptionist/voice/nope", {"CallSid": "CA5"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("<Hangup/>", r.text)

    def test_client_activation_and_status(self):
        from backend import client_space_api as cs
        with self.Session() as db:
            db.add(ClientSession(token_hash=cs._hash("sess-1"), business_id="elec1", kind="session",
                                 expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1)))
            db.commit()
        h = {"X-Client-Session": "sess-1"}
        self.assertEqual(self.c.get("/client/space/receptionist").status_code, 401)
        self.assertEqual(self.c.get("/client/space/receptionist", headers=h).json()["status"], "inactive")
        state = self.c.post("/client/space/receptionist/activate", headers=h, json={}).json()
        self.assertEqual(state["status"], "trial")
        self.assertEqual(state["days_left"], 30)
        # Le client ne peut pas s'auto-déclarer payant
        state = self.c.post("/client/space/receptionist/activate", headers=h, json={"paid_active": True}).json()
        self.assertEqual(state["status"], "trial")

    def client_session(self):
        from backend import client_space_api as cs
        with self.Session() as db:
            db.add(ClientSession(token_hash=cs._hash("sess-2"), business_id="elec1", kind="session",
                                 expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1)))
            db.commit()
        return {"X-Client-Session": "sess-2"}

    def test_client_settings_onboarding_and_simulator(self):
        h = self.client_session()
        body = {"settings": {"agent_name": "Léa", "voice": "homme"}, "onboarded": True}
        self.assertEqual(self.c.put("/client/space/receptionist/settings", headers=h, json=body).status_code, 409)
        self.assertEqual(self.c.post("/client/space/receptionist/test", headers=h, json={}).status_code, 409)
        state = self.c.post("/client/space/receptionist/activate", headers=h, json={}).json()
        self.assertFalse(state["onboarded"])
        self.assertEqual(state["notify_phone"], "06 12 34 56 78")
        self.assertEqual(state["options"]["detected_profession"], "electricien")
        bad = self.c.put("/client/space/receptionist/settings", headers=h, json={"notify_phone": "12"})
        self.assertEqual(bad.status_code, 422)
        state = self.c.put("/client/space/receptionist/settings", headers=h,
                           json={**body, "notify_phone": "07 11 22 33 44", "notify_channels": ["sms", "email"]}).json()
        self.assertTrue(state["onboarded"])
        self.assertEqual(state["settings"]["agent_name"], "Léa")
        self.assertEqual(state["settings"]["voice"], "homme")
        self.assertEqual(state["notify_channels"], ["sms", "email"])
        self.assertEqual(state["notify_phone"], "07 11 22 33 44")
        # Un réglage partiel ne réinitialise pas les autres
        state = self.c.put("/client/space/receptionist/settings", headers=h,
                           json={"settings": {"extra_info": "Devis gratuit"}}).json()
        self.assertEqual(state["settings"]["agent_name"], "Léa")

        # L'appel réel utilise les réglages (voix masculine, prénom)
        r = self.post("/receptionist/voice/elec1", {"CallSid": "CA9", "From": "+33611111111"})
        self.assertIn("Polly.Remi-Neural", r.text)
        self.assertIn("Je suis Léa", r.text)

        # Simulateur : salutation, puis échange jusqu'au résumé, sans notification ni appel stocké
        first = self.c.post("/client/space/receptionist/test", headers=h, json={}).json()
        self.assertIn("Je suis Léa", first["reply"])
        replies = iter([
            '{"reply": "Où êtes-vous ?", "fields": {"motif": "panne"}, "done": false}',
            '{"reply": "Merci, au revoir !", "fields": {"adresse": "Trappes", "nom": "Paul"}, "done": true}',
        ])
        with patch.object(rc, "llm_complete", lambda b, s, p: next(replies)):
            t1 = self.c.post("/client/space/receptionist/test", headers=h,
                             json={"message": "Plus de courant", "history": [{"role": "assistant", "text": first["reply"]}]}).json()
            self.assertFalse(t1["done"])
            self.assertTrue(t1["collected"]["urgence"])
            t2 = self.c.post("/client/space/receptionist/test", headers=h,
                             json={"message": "Trappes, Paul", "collected": t1["collected"],
                                   "history": [{"role": "caller", "text": "Plus de courant"},
                                               {"role": "assistant", "text": t1["reply"]}]}).json()
        self.assertTrue(t2["done"])
        self.assertEqual(t2["summary"]["adresse"], "Trappes")
        self.assertIn("URGENT", t2["notification"])
        self.assertEqual(self.notified, [])
        with self.Session() as db:
            self.assertEqual(db.query(ReceptionistCall).filter_by(mode="test").count(), 0)

    def test_elite_client_gets_ai_without_trial(self):
        with self.Session() as db:
            b = db.query(Business).filter_by(id="elec1").one()
            b.plan_tier, b.subscription_status = "elite", "active"
            db.commit()
        r = self.post("/receptionist/voice/elec1", {"CallSid": "CE1", "From": "+33611111111"})
        self.assertIn("<Gather", r.text)          # IA, pas la messagerie
        state = self.c.get("/businesses/elec1/receptionist", headers={"X-Admin-Token": "adm"}).json()
        self.assertEqual(state["status"], "active")
        self.assertTrue(state["included_in_plan"])
        self.assertEqual(state["included_calls"], 100)
        ok = self.c.put("/businesses/elec1/receptionist/settings", headers={"X-Admin-Token": "adm"},
                        json={"settings": {"agent_name": "Léa"}})
        self.assertEqual(ok.status_code, 200)

    def test_trial_capped_at_60_calls_then_voicemail(self):
        self.start_trial()
        with self.Session() as db:
            for i in range(59):
                db.add(ReceptionistCall(call_sid=f"old{i}", business_id="elec1", mode="ai", transcript=[], collected={}))
            db.commit()
        # 60e prise en charge : une conversation WhatsApp, qui va ensuite à son terme malgré le plafond
        with patch.object(rc, "llm_complete", lambda b, s, p: '{"reply": "Où ?", "fields": {}, "done": false}'):
            r = self.post("/receptionist/whatsapp/elec1", {"From": "whatsapp:+33655555555", "Body": "fuite"})
            self.assertIn("Où ?", r.text)
            state = self.c.get("/businesses/elec1/receptionist", headers={"X-Admin-Token": "adm"}).json()
            self.assertTrue(state["trial_limit_reached"])
            self.assertEqual(state["trial_calls"], 60)
            r = self.post("/receptionist/whatsapp/elec1", {"From": "whatsapp:+33655555555", "Body": "Trappes"})
            self.assertIn("Où ?", r.text)
        r = self.post("/receptionist/voice/elec1", {"CallSid": "C62", "From": "+33622222222"})
        self.assertIn("<Record", r.text)                     # au-delà : simple messagerie
        self.assertNotIn("<Gather", r.text)
        # payé : plus de plafond d'essai
        with self.Session() as db:
            db.query(ReceptionistAddon).filter_by(business_id="elec1").update({"paid_active": True})
            db.commit()
        r = self.post("/receptionist/voice/elec1", {"CallSid": "C63", "From": "+33633333333"})
        self.assertIn("<Gather", r.text)

    def test_admin_diagnostic(self):
        env = {"TWILIO_ACCOUNT_SID": "AC1", "TWILIO_PHONE_NUMBER": "+33900000000",
               "TWILIO_WEBHOOK_BASE_URL": "https://api.pulsepro.fr"}
        with patch.dict(os.environ, env):
            d = self.c.get("/businesses/elec1/receptionist/diagnostic", headers={"X-Admin-Token": "adm"}).json()
        self.assertTrue(d["ready"])
        self.assertEqual(d["webhooks"]["voice_incoming"], "https://api.pulsepro.fr/receptionist/voice/elec1")
        self.assertEqual(d["webhooks"]["relay_websocket"], "wss://api.pulsepro.fr/receptionist/relay/elec1")
        self.assertEqual(self.c.get("/businesses/elec1/receptionist/diagnostic").status_code, 401)

    def test_relay_engine_websocket(self):
        from starlette.websockets import WebSocketDisconnect
        self.start_trial()
        with patch.dict(os.environ, {"RECEPTIONIST_ENGINE": "relay"}):
            r = self.post("/receptionist/voice/elec1", {"CallSid": "CR1", "From": "+33611111111"})
        self.assertIn("<ConversationRelay", r.text)
        self.assertIn('url="ws://testserver/receptionist/relay/elec1"', r.text)
        path = "/receptionist/relay/elec1"
        with self.assertRaises(WebSocketDisconnect):
            with self.c.websocket_connect(path, headers={"X-Twilio-Signature": "forged"}) as ws:
                ws.receive_json()
        sig = rc.compute_signature(TOKEN, "ws://testserver" + path, {})
        replies = iter(['{"reply": "Merci Paul, au revoir !", "fields": {"motif": "fuite", "nom": "Paul"}, "done": true}'])
        with patch.object(rc, "llm_complete", lambda b, s, p: next(replies)), \
                patch.object(api, "_hangup_delay", lambda text: 0):
            with self.c.websocket_connect(path, headers={"X-Twilio-Signature": sig}) as ws:
                ws.send_json({"type": "setup", "callSid": "CR1", "from": "+33611111111"})
                ws.send_json({"type": "prompt", "voicePrompt": "J'ai une fuite", "last": True})
                self.assertEqual(ws.receive_json(), {"type": "text", "token": "Merci Paul, au revoir !", "last": True})
                self.assertEqual(ws.receive_json(), {"type": "end"})
        self.assertEqual(len(self.notified), 1)
        self.assertEqual(self.notified[0]["motif"], "fuite")
        self.assertTrue(self.notified[0]["urgence"])


class SettingsTests(unittest.TestCase):
    def test_normalize_settings(self):
        s = rc.normalize_settings({"voice": "robot", "profession": "nope", "agent_name": "  Léa   Martin  ",
                                   "forward_modes": ["always", "bogus", "always"], "greeting": "x" * 999})
        self.assertEqual(s["voice"], "femme")
        self.assertEqual(s["profession"], "")
        self.assertEqual(s["agent_name"], "Léa Martin")
        self.assertEqual(s["forward_modes"], ["always"])
        self.assertEqual(len(s["greeting"]), 400)
        self.assertEqual(rc.normalize_settings(None), rc.DEFAULT_SETTINGS)

    def test_settings_shape_prompt_greeting_and_questions(self):
        b = biz(name="Société Y")
        st = {"agent_name": "Léa", "profession": "plombier", "extra_info": "Devis gratuit sous 48 h.",
              "custom_question": "Êtes-vous propriétaire ou locataire ?"}
        p = rc.build_system_prompt(b, st)
        self.assertIn("Tu t'appelles Léa", p)
        self.assertIn("plomberie", p)
        self.assertIn("Devis gratuit sous 48 h.", p)
        self.assertIn("[precision] Êtes-vous propriétaire", p)
        self.assertLess(p.index("[precision]"), p.index("[nom]"))
        self.assertIn("Je suis Léa", rc.greeting(b, st))
        # Mention IA obligatoire (AI Act) : ajoutée si le message personnalisé l'omet, conservée sinon.
        g = rc.greeting(b, {"greeting": "Allô, ici Y !"})
        self.assertTrue(g.startswith("Allô, ici Y !") and "intelligence artificielle" in g)
        self.assertEqual(rc.greeting(b, {"greeting": "Bonjour, assistante virtuelle de Y."}), "Bonjour, assistante virtuelle de Y.")
        self.assertIn("intelligence artificielle", rc.default_greeting(b, st))
        # Script de secours : la question personnalisée est posée avant le nom
        col = {"urgence": False, "motif": "fuite", "adresse": "Trappes", "creneau": "demain"}
        with patch.object(rc, "llm_complete", side_effect=RuntimeError("down")):
            r = rc.next_turn(b, [], col, "", st)
        self.assertEqual(r["reply"], st["custom_question"])

    def test_slow_llm_falls_back_to_script(self):
        import time
        b = biz(name="Plomberie Martin", category=["plumber"])

        def slow(*a):
            time.sleep(1)
            return '{"reply": "trop tard", "fields": {}, "done": false}'
        with patch.object(rc, "llm_complete", slow):
            t0 = time.monotonic()
            r = rc.next_turn(b, [], {}, "J'ai une fuite", timeout=0.1)
        self.assertLess(time.monotonic() - t0, 0.8)
        self.assertNotEqual(r["reply"], "trop tard")
        self.assertTrue(r["fields"]["urgence"])

    def test_truncated_json_still_gives_reply(self):
        raw = '{"reply": "Quelle est l\'adresse exacte ?", "fields": {"motif": "fuite", "adres'
        d = rc._parse_llm_json(raw)
        self.assertEqual(d["reply"], "Quelle est l'adresse exacte ?")
        self.assertFalse(d["done"])
        self.assertIsNone(rc._parse_llm_json('{"fields": {'))

    def test_gemini_fast_json_minimal_thinking_with_fallback(self):
        calls = []

        class R:
            def __init__(self, code, body):
                self.status_code, self._b, self.text = code, body, str(body)

            def json(self):
                return self._b

        def post(url, params, json, timeout):
            calls.append(json["generationConfig"])
            if json["generationConfig"].get("thinkingConfig", {}).get("thinkingLevel") == "minimal":
                return R(400, {"error": "thinking level not supported"})
            return R(200, {"candidates": [{"content": {"parts": [
                {"text": "réflexion", "thought": True}, {"text": '{"reply": "Bonjour", "fields": {}, "done": false}'}]}}]})
        rc._thinking_ok.clear()
        with patch.dict(os.environ, {"GEMINI_API_KEY": "k"}), patch.object(rc.requests, "post", post):
            self.assertEqual(rc.gemini_fast("sys", "p"), '{"reply": "Bonjour", "fields": {}, "done": false}')
            self.assertEqual(calls[0]["responseMimeType"], "application/json")
            self.assertEqual(calls[1]["thinkingConfig"], {"thinkingLevel": "low"})
            calls.clear()
            rc.gemini_fast("sys", "p")            # réglage accepté mémorisé : un seul appel
            self.assertEqual(len(calls), 1)
        rc._thinking_ok.clear()

    def test_voice_and_forward_codes(self):
        self.assertIn("Remi", rc.say_voice({"voice": "homme"}))
        self.assertIn('voice="Polly.Remi-Neural"', rc.twiml_gather("x", "/a", rc.say_voice({"voice": "homme"})))
        codes = rc.forward_codes("+33912345678", {"forward_modes": ["no_answer", "busy"]})
        self.assertEqual([c["activate"] for c in codes], ["**61*+33912345678#", "**67*+33912345678#"])
        self.assertEqual(codes[0]["deactivate"], "##61#")
        self.assertEqual(rc.forward_codes("", None), [])

    def test_relay_twiml(self):
        x = rc.twiml_relay("wss://api.test/receptionist/relay/b1", "Bonjour & bienvenue", {}, action="/end")
        self.assertIn("<Connect action=\"/end\"", x)
        self.assertIn('url="wss://api.test/receptionist/relay/b1"', x)
        self.assertIn('welcomeGreeting="Bonjour &amp; bienvenue"', x)
        self.assertIn('language="fr-FR"', x)
        with patch.dict(os.environ, {"RECEPTIONIST_ENGINE": "relay"}):
            self.assertEqual(rc.engine(), "relay")
        with patch.dict(os.environ, {"RECEPTIONIST_ENGINE": ""}):
            self.assertEqual(rc.engine(), "gather")


class NotificationTests(unittest.TestCase):
    def test_sms_format_and_graceful_failures(self):
        b = biz(name="ELEC PRO", category=["electrician"])
        call = SimpleNamespace(collected={"motif": "panne", "nom": "Paul", "_pending": None},
                               transcript=[{"role": "caller", "text": "panne"}], from_number="+33611111111",
                               mode="ai", recording_url=None)
        s = rc.build_summary(b, call)
        sms = rc.format_sms(b, s)
        self.assertTrue(sms.startswith("🚨 URGENT"))
        self.assertIn("Paul +33611111111", sms)
        self.assertEqual(rc.to_e164("06 12 34 56 78"), "+33612345678")
        with patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": "", "TWILIO_PHONE_NUMBER": ""}):
            self.assertFalse(rc.send_sms("0612345678", "x"))
        with patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "AC1", "TWILIO_AUTH_TOKEN": "t", "TWILIO_PHONE_NUMBER": "+33900000000"}), \
                patch.object(rc.requests, "post", side_effect=ConnectionError("réseau")):
            self.assertFalse(rc.send_sms("0612345678", "x"))
        addon = SimpleNamespace(notify_channels=["whatsapp", "sms", "email"], notify_phone=None, notify_email=None)
        with patch.object(rc, "send_sms", side_effect=RuntimeError("boom")), \
                patch.object(rc, "send_whatsapp", side_effect=RuntimeError("boom")), \
                patch("backend.services.alerts.send_alert", side_effect=RuntimeError("smtp")):
            self.assertEqual(rc.notify_owner(b, addon, s), {"whatsapp": False, "sms": False, "email": False})

    def test_channels_default_and_whatsapp_payload(self):
        self.assertEqual(rc.notify_channels(None), ["whatsapp", "sms"])
        self.assertEqual(rc.notify_channels(SimpleNamespace(notify_channels=["email", "fax"])), ["email"])
        self.assertEqual(rc.notify_channels(SimpleNamespace(notify_channels=[])), ["whatsapp", "sms"])
        sent = []

        class Ok:
            status_code = 201
        env = {"TWILIO_ACCOUNT_SID": "AC1", "TWILIO_AUTH_TOKEN": "t", "TWILIO_PHONE_NUMBER": "+33900000000",
               "TWILIO_WHATSAPP_NUMBER": "+14155238886"}
        with patch.dict(os.environ, env), patch.object(rc.requests, "post", lambda url, data, **k: sent.append(data) or Ok()):
            b = biz(name="ELEC PRO")
            s = {"urgence": False, "caller": {"nom": "", "telephone": "+336"}, "motif": "x", "mode": "ai"}
            self.assertEqual(rc.notify_owner(b, None, s), {"whatsapp": True, "sms": True})
        self.assertEqual(sent[0]["From"], "whatsapp:+14155238886")
        self.assertEqual(sent[0]["To"], "whatsapp:+33612345678")
        self.assertEqual(sent[1]["From"], "+33900000000")
        with patch.dict(os.environ, {**env, "TWILIO_WHATSAPP_NUMBER": ""}):
            self.assertFalse(rc.send_whatsapp("0612345678", "x"))


if __name__ == "__main__":
    unittest.main()


class PricingTests(unittest.TestCase):
    def test_elite_includes_receptionist_and_annual_price(self):
        self.assertEqual(plans.ADDON_CATALOG[plans.RECEPTIONIST_ADDON]["price"], 39)
        self.assertEqual(plans.ADDON_CATALOG[plans.RECEPTIONIST_ADDON]["included_calls"], 100)
        self.assertEqual(plans.ADDON_CATALOG[plans.RECEPTIONIST_ADDON]["trial_calls"], 60)
        self.assertEqual(plans.ADDON_CATALOG[plans.RECEPTIONIST_ADDON]["extra_call_price_ttc"], 1.0)
        self.assertEqual(plans.annual_price("pro"), 1490)
        elite = SimpleNamespace(plan_tier="elite", subscription_status="active")
        pro = SimpleNamespace(plan_tier="pro", subscription_status="active")
        unpaid = SimpleNamespace(plan_tier="elite", subscription_status="inactive")
        self.assertTrue(plans.plan_includes_addon(elite))
        self.assertFalse(plans.plan_includes_addon(pro))
        self.assertFalse(plans.plan_includes_addon(unpaid))
        self.assertEqual(plans.addon_status(None, included=True), "active")
        self.assertTrue(plans.addon_ai_enabled(None, included=True))
        b = SimpleNamespace(plan_tier=None, mrr_value=0)
        plans.apply_plan_features(b, "pro", "annual")
        self.assertAlmostEqual(b.mrr_value, 124.17, places=2)
