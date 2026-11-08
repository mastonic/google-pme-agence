import os
os.environ.setdefault("ADMIN_API_TOKEN", "test-token")
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import Base, engine

Base.metadata.create_all(bind=engine)
client = TestClient(app)
OK = {"source": "score_tool", "email": "Jean@Plomberie.fr", "business_name": "Plomberie Test", "score": 42,
      "answers": {"fiche": 0.4}, "consent": True}


def test_post_lead_public_and_admin_list_protected():
    r = client.post("/leads", json=OK, headers={"x-forwarded-for": "1.1.1.1"})
    assert r.status_code == 200 and r.json()["ok"]
    assert client.get("/admin/leads").status_code in (401, 403)
    rows = client.get("/admin/leads", headers={"x-admin-token": "test-token"}).json()
    assert any(x["email"] == "jean@plomberie.fr" and x["score"] == 42 for x in rows)


def test_rejects_bad_email_and_missing_consent():
    assert client.post("/leads", json={**OK, "email": "nope"}, headers={"x-forwarded-for": "2.2.2.2"}).status_code == 422
    assert client.post("/leads", json={**OK, "consent": False}, headers={"x-forwarded-for": "2.2.2.3"}).status_code == 400


def test_honeypot_not_saved():
    r = client.post("/leads", json={**OK, "email": "bot@x.fr", "website": "spam"}, headers={"x-forwarded-for": "3.3.3.3"})
    assert r.status_code == 200
    rows = client.get("/admin/leads", headers={"x-admin-token": "test-token"}).json()
    assert not any(x["email"] == "bot@x.fr" for x in rows)


def test_rate_limit():
    codes = [client.post("/leads", json=OK, headers={"x-forwarded-for": "9.9.9.9"}).status_code for _ in range(6)]
    assert codes[-1] == 429


H = {"x-admin-token": "test-token"}


def test_callback_lead_with_phone_goes_to_call_column_and_funnel_updates():
    from unittest.mock import patch
    sent = []
    payload = {"source": "store", "contact_name": " Paul  Martin ", "business_name": "Plomberie Martin",
               "phone": "06 12 34 56 78", "email": "paul@plomberie-martin.fr", "city": "Trappes", "product": "Pack 50 avis (99 €)",
               "message": "Rappelez-moi après 17h", "callback_slot": "evening", "consent": True}
    with patch("backend.services.alerts.send_alert", lambda subject, body, to=None: sent.append((subject, body)) or True):
        r = client.post("/leads", json=payload, headers={"x-forwarded-for": "4.4.4.4"})
    assert r.status_code == 200, r.text
    lead_id = r.json()["id"]
    assert sent and "Paul Martin" in sent[0][0] and "Pack 50 avis" in sent[0][1]
    lead = next(x for x in client.get("/admin/leads", headers=H).json() if x["id"] == lead_id)
    assert lead["status"] == "to_call"
    assert lead["contact_name"] == "Paul Martin"
    assert lead["callback_label"] == "En fin de journée"
    assert lead["email"] == "paul@plomberie-martin.fr" and lead["source_label"] == "Boutique"

    assert client.patch(f"/admin/leads/{lead_id}", json={"status": "contacted"}).status_code in (401, 403)
    up = client.patch(f"/admin/leads/{lead_id}", headers=H,
                      json={"status": "contacted", "notes": "Rappelé, devis envoyé", "next_call_at": "2026-11-10T09:00:00Z"}).json()
    assert up["status"] == "contacted" and up["notes"] == "Rappelé, devis envoyé"
    assert up["next_call_at"].startswith("2026-11-10T09:00")
    assert client.patch(f"/admin/leads/{lead_id}", headers=H, json={"status": "bogus"}).status_code == 422
    assert client.patch("/admin/leads/999999", headers=H, json={"status": "won"}).status_code == 404


def test_lead_needs_email_and_valid_phone():
    base = {"source": "store", "consent": True}
    assert client.post("/leads", json=base, headers={"x-forwarded-for": "5.5.5.1"}).status_code == 422
    # Téléphone seul : refusé, l'email est obligatoire.
    assert client.post("/leads", json={**base, "phone": "0612345678"}, headers={"x-forwarded-for": "5.5.5.3"}).status_code == 422
    assert client.post("/leads", json={**base, "email": "a@b.fr", "phone": "12"}, headers={"x-forwarded-for": "5.5.5.2"}).status_code == 422


def test_lead_rate_limit_ignores_forged_first_forwarded_ip_and_filters_referrer():
    from backend import lead_api
    lead_api._limiter.reset()
    # Le premier élément de X-Forwarded-For change à chaque fois, l'IP réelle (fin de chaîne) non.
    codes = [client.post("/leads", json=OK, headers={"x-forwarded-for": f"10.0.0.{i}, 7.7.7.7, 8.8.8.8"}).status_code
             for i in range(6)]
    assert codes[:5] == [200] * 5 and codes[5] == 429
    lead_api._limiter.reset()
    r = client.post("/leads", json=OK, headers={"x-forwarded-for": "6.6.6.6", "referer": "javascript:alert(1)"})
    lead = next(x for x in client.get("/admin/leads", headers=H).json() if x["id"] == r.json()["id"])
    assert lead["referrer"] is None
