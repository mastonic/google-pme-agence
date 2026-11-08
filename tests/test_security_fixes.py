"""Régressions de sécurité (audit du 8 novembre 2026)."""
import os
from unittest.mock import patch

os.environ.setdefault("ADMIN_API_TOKEN", "test-token")

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402
from backend.models.database import Business, SessionLocal  # noqa: E402
from backend.services import photo_proxy  # noqa: E402
from backend.services.web_security import safe_http_url  # noqa: E402

client = TestClient(app)


def _ensure_columns():
    """La base de test locale peut précéder la migration de démarrage : on ajoute la colonne si besoin."""
    from sqlalchemy import inspect, text
    from backend.models.database import engine
    cols = {c["name"] for c in inspect(engine).get_columns("businesses")}
    if "do_not_contact" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE businesses ADD COLUMN do_not_contact INTEGER DEFAULT 0"))


_ensure_columns()


def _business(bid="sec-biz", name="Plomberie <script>x</script>"):
    db = SessionLocal()
    b = db.query(Business).filter(Business.id == bid).first() or Business(id=bid)
    b.name, b.generated_html, b.do_not_contact = name, "<html><body><nav></nav></body></html>", False
    db.merge(b)
    db.commit()
    db.close()
    return bid


def test_api_docs_disabled_and_security_headers():
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code in (401, 404)
    r = client.get("/status")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" in r.headers


def test_cors_does_not_reflect_foreign_origin():
    r = client.get("/status", headers={"Origin": "https://evil.example"})
    assert r.headers.get("access-control-allow-origin") != "https://evil.example"
    assert r.headers.get("access-control-allow-credentials") != "true"
    ok = client.get("/status", headers={"Origin": "https://pulse-locale-pme.fr"})
    assert ok.headers.get("access-control-allow-origin") == "https://pulse-locale-pme.fr"


def test_preview_is_sandboxed_and_demo_escapes_name():
    bid = _business()
    r = client.get(f"/preview/{bid}")
    assert "sandbox" in r.headers["content-security-policy"] and "allow-same-origin" not in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "SAMEORIGIN"
    d = client.get(f"/demo/{bid}")
    assert "<script>x</script>" not in d.text and "&lt;script&gt;" in d.text
    assert "/pricing?" not in d.text and f"/buy/{bid}/" in d.text


def test_photo_proxy_rejects_html_and_foreign_buckets():
    assert photo_proxy.validate_photo_url("https://storage.googleapis.com/evil-bucket/x.html")[0] is False
    assert photo_proxy.validate_photo_url("https://storage.googleapis.com/falserverless/a.png")[0] is True
    assert photo_proxy.validate_redirect_url("https://lh3.googleusercontent.com/p/x") is True
    assert photo_proxy.validate_redirect_url("https://evil.example/x") is False

    class Up:
        status_code, headers = 200, {"content-type": "text/html"}
        def close(self): pass
    with patch("requests.get", lambda *a, **k: Up()):
        r = client.get("/photo", params={"url": "https://images.unsplash.com/x"})
    assert r.status_code == 502


def test_client_urls_cannot_break_out_of_attributes():
    from backend.agents.manager import enforce_client_logo, enforce_client_photos
    evil = 'https://x/l.png" onerror="alert(1)'
    assert safe_http_url(evil) == "" and safe_http_url("javascript:alert(1)") == ""
    html = "<html><body><nav></nav><img src='https://other/a.jpg'></body></html>"
    assert "onerror" not in enforce_client_logo(html, evil, 'Nom "piégé"')
    assert "onerror" not in enforce_client_photos(html, [evil])[0]
    assert 'alt="Nom &quot;piégé&quot;"' in enforce_client_logo(html, "https://cdn.example/logo.png", 'Nom "piégé"')


def test_public_onboarding_sanitizes_profile():
    from backend.services.client_onboarding import sanitize_profile_input
    clean = sanitize_profile_input({"identity": {"logo_url": 'https://x/a.png" onerror="y'},
                                    "media": {"photos": [{"url": "javascript:alert(1)"}, {"url": "https://ok.example/p.jpg"}]},
                                    "admin": {"plan": "elite"}})
    assert clean["identity"]["logo_url"] == "" and "admin" not in clean
    assert clean["media"]["photos"] == [{"url": "https://ok.example/p.jpg"}]


def test_prospect_opt_out_link_is_signed_and_blocks_emails():
    from backend.services.prospect_optout import opt_out_signature
    bid = _business("sec-optout", "Boulangerie Test")
    assert client.get(f"/prospects/stop/{bid}", params={"s": "faux"}).status_code == 400
    assert client.get(f"/prospects/stop/{bid}", params={"s": opt_out_signature(bid)}).status_code == 200
    db = SessionLocal()
    assert db.query(Business).filter(Business.id == bid).first().do_not_contact is True
    db.close()


def test_checkout_success_url_has_no_permanent_token():
    import inspect
    from backend import main
    src = inspect.getsource(main._create_stripe_checkout)
    assert "{CHECKOUT_SESSION_ID}" in src and "&t=" not in src
