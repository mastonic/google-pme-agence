"""Système email : routage, accusés de réception, commandes Stripe, anti-spam, doublons, pannes.

Aucun email réel n'est envoyé : le transport SMTP est remplacé par des simulations (mocks).
"""
import datetime
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend import lead_api
from backend.main import app
from backend.models.database import EmailOutbox, InboundLead, SessionLocal
from backend.services import email_service as es

client = TestClient(app)
H = {"x-admin-token": os.environ.get("ADMIN_API_TOKEN", "test-token")}
SMTP_ENV = {"SMTP_HOST": "smtp.test.invalid", "SMTP_PORT": "465", "SMTP_SECURE": "ssl",
            "SMTP_USER": "contact@pulse-locale-pme.fr", "SMTP_PASSWORD": "secret-de-test"}
ORIGIN = {"origin": "https://pulse-locale-pme.fr"}
_n = [0]


def post(payload, ip=None, origin=ORIGIN):
    _n[0] += 1
    headers = {"x-forwarded-for": ip or f"203.0.113.{_n[0] % 250}", **(origin or {})}
    return client.post("/leads", json=payload, headers=headers)


def lead(**kw):
    base = {"source": "contact", "email": f"client{_n[0]}-{datetime.datetime.utcnow().timestamp()}@exemple.fr",
            "contact_name": "Marie Durand", "message": f"Bonjour {datetime.datetime.utcnow().isoformat()}",
            "consent": True, "elapsed_ms": 5000}
    base.update(kw)
    return base


def outbox(lead_id):
    db = SessionLocal()
    rows = {m.category: m for m in db.query(EmailOutbox).filter(EmailOutbox.lead_id == lead_id).all()}
    db.close()
    return rows


@pytest.fixture(autouse=True)
def _reset():
    lead_api._limiter.reset()
    yield


@pytest.mark.parametrize("payload,box", [
    ({"source": "contact", "product": "Contact Pulse Locale PME"}, "contact@pulse-locale-pme.fr"),          # 1 contact
    ({"source": "callback", "product": "Devis et tarifs", "phone": "0612345678"}, "devis@pulse-locale-pme.fr"),  # 2 devis
    ({"source": "callback", "product": "Démo gratuite du site", "phone": "0612345678"}, "devis@pulse-locale-pme.fr"),  # 3 démo
    ({"source": "score_tool", "score": 42}, "audit@pulse-locale-pme.fr"),                                     # 4 audit
    ({"source": "store", "kind": "support", "product": "Support commande boutique"}, "support@pulse-locale-pme.fr"),  # 7 support
    ({"source": "store", "kind": "product_info", "product": "Question produit"}, "contact@pulse-locale-pme.fr"),
])
def test_routing_and_customer_confirmation(payload, box):
    with patch.object(es, "_smtp_send", lambda msg: None), patch.dict(os.environ, SMTP_ENV):
        r = post(lead(**payload))
    assert r.status_code == 200, r.text
    mails = outbox(r.json()["id"])
    assert mails["internal"].to_addr == box
    assert mails["internal"].reply_to and "@exemple.fr" in mails["internal"].reply_to
    assert mails["customer"].reply_to == box
    assert mails["internal"].status == mails["customer"].status == "sent"
    assert "Bonjour Marie," in mails["customer"].body_text


def test_templates_subjects_and_support_reference():
    assert es.render_customer("contact")[0] == "Nous avons bien reçu votre message | Pulse Locale PME"
    assert es.render_customer("devis")[0] == "Votre demande de devis a bien été reçue"
    assert es.render_customer("audit")[0] == "Votre demande d'audit de visibilité locale"
    assert es.render_customer("support", ref="SUP-000007")[0] == "Votre demande de support a été enregistrée"
    assert "SUP-000007" in es.render_customer("support", ref="SUP-000007")[1]
    subject, text, html = es.render_customer("order", first_name="Paul", ref="CMD-1", product="Pro", amount="149,00 EUR")
    assert subject == "Confirmation de votre commande Pulse Locale PME" and "149,00 EUR" in text and "<html" in html
    with patch.object(es, "_smtp_send", lambda msg: None), patch.dict(os.environ, SMTP_ENV):
        r = post(lead(source="store", kind="support", product="Support"))
    assert r.json()["ref"].startswith("SUP-")


def _stripe_event(payment_status, sid):
    return {"id": "evt_" + sid, "type": "checkout.session.completed", "data": {"object": {
        "id": sid, "payment_status": payment_status, "amount_total": 14900, "currency": "eur",
        "customer_details": {"email": "acheteur@exemple.fr", "name": "Paul Achat"},
        "metadata": {"plan": "pro", "billing": "monthly"}}}}


def _order_rows(sid):
    db = SessionLocal()
    rows = db.query(EmailOutbox).filter(EmailOutbox.ref == sid).all()
    db.close()
    return rows


def test_stripe_paid_order_sends_once_and_unpaid_sends_nothing():
    import stripe
    sid = f"cs_test_{int(datetime.datetime.utcnow().timestamp() * 1000)}"
    with patch.object(stripe.Webhook, "construct_event", lambda *a, **k: _stripe_event("paid", sid)), \
            patch.object(es, "_smtp_send", lambda msg: None), patch.dict(os.environ, SMTP_ENV):
        for _ in range(2):  # webhook rejoué par Stripe : aucun doublon
            assert client.post("/webhook/stripe", content=b"{}", headers={"stripe-signature": "t"}).status_code == 200
    rows = _order_rows(sid)
    assert len(rows) == 2                                                      # 5 commande payée
    assert {r.to_addr for r in rows} == {"acheteur@exemple.fr", "commandes@pulse-locale-pme.fr"}
    customer = next(r for r in rows if r.category == "customer")
    assert "Votre paiement a été confirmé." in customer.body_text and "149,00 EUR" in customer.body_text
    unpaid = sid + "u"
    with patch.object(stripe.Webhook, "construct_event", lambda *a, **k: _stripe_event("unpaid", unpaid)):
        client.post("/webhook/stripe", content=b"{}", headers={"stripe-signature": "t"})
    assert _order_rows(unpaid) == []                                           # 6 commande non payée


def test_invalid_email_rejected():                                            # 8
    assert post(lead(email="pas-un-email")).status_code == 422
    assert post(lead(email="a@b.fr\r\nBcc: x@y.fr")).status_code == 422


def test_spam_protections():                                                  # 9
    db = SessionLocal()
    before = db.query(InboundLead).count()
    assert post(lead(website="http://spam")).json() == {"ok": True}          # pot de miel
    assert post(lead(elapsed_ms=200)).json() == {"ok": True}                 # rempli trop vite
    assert post(lead(), origin={"origin": "https://spam.example"}).status_code == 403
    assert db.query(InboundLead).count() == before
    db.close()
    assert post(lead(message="x" * 1501)).status_code == 422                  # message trop long


def test_double_submission_creates_one_lead_and_one_pair_of_emails():        # 10
    payload = lead(request_id="dbl" + str(int(datetime.datetime.utcnow().timestamp() * 1000)))
    with patch.object(es, "_smtp_send", lambda msg: None), patch.dict(os.environ, SMTP_ENV):
        a, b = post(payload), post(payload)
        c = post({**payload, "request_id": None})   # même contenu sans identifiant : fenêtre anti-doublon
    assert a.json()["id"] == b.json()["id"] == c.json()["id"] and b.json()["duplicate"] is True
    assert len(outbox(a.json()["id"])) == 2


def _fail(transient):
    def send(msg):
        raise es.EmailSendError("simulé", transient=transient)
    return send


def test_smtp_down_keeps_lead_and_schedules_retry_then_sends():               # 11 + 12
    with patch.object(es, "_smtp_send", _fail(True)), patch.dict(os.environ, SMTP_ENV):
        r = post(lead())
    assert r.status_code == 200
    lead_id = r.json()["id"]
    mails = outbox(lead_id)
    assert mails["internal"].status == "failed" and mails["internal"].attempts == 1
    assert mails["internal"].next_attempt_at > datetime.datetime.utcnow()
    # Le temps passe : la relance part et réussit.
    db = SessionLocal()
    db.query(EmailOutbox).filter(EmailOutbox.lead_id == lead_id).update({"next_attempt_at": datetime.datetime.utcnow()})
    db.commit()
    with patch.object(es, "_smtp_send", lambda msg: None), patch.dict(os.environ, SMTP_ENV):
        es.dispatch(db, [m.id for m in mails.values()])
    db.close()
    after = outbox(lead_id)
    assert after["internal"].status == after["customer"].status == "sent" and after["internal"].attempts == 2


def test_permanent_smtp_error_is_dead_not_retried():
    with patch.object(es, "_smtp_send", _fail(False)), patch.dict(os.environ, SMTP_ENV):
        r = post(lead())
    assert outbox(r.json()["id"])["internal"].status == "dead"


def test_crm_unavailable_returns_503_without_orphan_email():                  # 13
    from sqlalchemy.orm import Session
    rid = "crm" + str(int(datetime.datetime.utcnow().timestamp() * 1000))
    real_commit = Session.commit

    def boom(self):
        raise RuntimeError("base indisponible")
    with patch.object(Session, "commit", boom):
        r = post(lead(request_id=rid))
    assert r.status_code == 503
    db = SessionLocal()
    assert db.query(InboundLead).filter(InboundLead.request_id == rid).count() == 0
    db.close()
    assert Session.commit is real_commit
    with patch.object(es, "_smtp_send", lambda msg: None), patch.dict(os.environ, SMTP_ENV):
        assert post(lead(request_id=rid)).status_code == 200                  # nouvel essai : enregistré


def test_without_smtp_config_requests_are_kept_and_no_secret_leaks():        # 14
    env = {k: "" for k in SMTP_ENV}
    with patch.dict(os.environ, env):
        r = post(lead())
        status = es.config_status()
    assert r.status_code == 200
    mails = outbox(r.json()["id"])
    assert mails["internal"].status == "pending" and mails["internal"].attempts == 0   # attend la configuration
    with patch.dict(os.environ, SMTP_ENV):
        status = es.config_status()
    assert "secret-de-test" not in str(status) and status["smtp_password_set"] is True
    assert client.get("/admin/email/status").status_code == 401                   # diagnostic réservé à l'admin
    assert "secret-de-test" not in client.get("/admin/email/status", headers=H).text


def test_unauthorized_sender_falls_back_and_headers_cannot_be_injected():    # 15
    with patch.dict(os.environ, {**SMTP_ENV, "SMTP_FROM": "notifications@pulse-locale-pme.fr", "SMTP_ALLOWED_FROM": ""}):
        assert es.sender_address() == "contact@pulse-locale-pme.fr"
    with patch.dict(os.environ, {**SMTP_ENV, "SMTP_FROM": "notifications@pulse-locale-pme.fr",
                                 "SMTP_ALLOWED_FROM": "notifications@pulse-locale-pme.fr"}):
        assert es.sender_address() == "notifications@pulse-locale-pme.fr"
    with patch.dict(os.environ, {**SMTP_ENV, "SMTP_FROM": "boss@autre-domaine.fr", "SMTP_ALLOWED_FROM": "boss@autre-domaine.fr"}):
        assert es.sender_address() == "contact@pulse-locale-pme.fr"
    with patch.dict(os.environ, SMTP_ENV):
        msg = es.build_message("client@exemple.fr", "Sujet\r\nBcc: pirate@x.fr", "corps", reply_to="x@y.fr\nBcc: z@w.fr")
    assert "\n" not in msg["Subject"] and msg["Reply-To"] is None and msg["Bcc"] is None
    assert es.valid_email("Marie <m@x.fr>") == "" and es.mask("marie@exemple.fr") == "m***@exemple.fr"


def test_concurrent_dispatch_never_sends_twice():
    sent = []
    with patch.object(es, "_smtp_send", _fail(True)), patch.dict(os.environ, SMTP_ENV):
        r = post(lead())
    ids = [m.id for m in outbox(r.json()["id"]).values()]
    db = SessionLocal()
    db.query(EmailOutbox).filter(EmailOutbox.id.in_(ids)).update({"next_attempt_at": datetime.datetime.utcnow()})
    db.commit()
    with patch.object(es, "_smtp_send", lambda msg: sent.append(msg["To"])), patch.dict(os.environ, SMTP_ENV):
        es.dispatch(db, ids)
        es.dispatch(db, ids)
    db.close()
    assert len(sent) == 2


def test_retention_purges_old_leads_and_sent_emails():
    db = SessionLocal()
    old = datetime.datetime.utcnow() - datetime.timedelta(days=365 * 3 + 10)
    stale = InboundLead(source="contact", kind="contact", email="ancien@exemple.fr", consent=True, created_at=old)
    db.add(stale)
    db.flush()
    db.add(EmailOutbox(event_key=f"old:{stale.id}", category="internal", to_addr="contact@pulse-locale-pme.fr",
                       subject="x", body_text="x", status="sent", created_at=old))
    db.commit()
    sid = stale.id
    assert lead_api.purge_old_leads(db) >= 1 and es.purge_outbox(db, days=90) >= 1
    assert db.query(InboundLead).filter(InboundLead.id == sid).count() == 0
    db.close()
