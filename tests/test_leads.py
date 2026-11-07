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
