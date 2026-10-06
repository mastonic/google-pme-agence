import os
import tempfile
import unittest

from backend.services import pmt_auth
from tests.test_pmt import TRANSPORT, sample_pmt

ADMIN_PW = "Admin-Pass-2026"
CLIENT_PW = "Client-Pass-2026"


class TokenTests(unittest.TestCase):
    def test_password_hash_roundtrip(self):
        h = pmt_auth.hash_password("abc123def456")
        self.assertTrue(pmt_auth.verify_password("abc123def456", h))
        self.assertFalse(pmt_auth.verify_password("wrong", h))
        self.assertFalse(pmt_auth.verify_password("x", "garbage"))

    def test_password_policy(self):
        self.assertIsNotNone(pmt_auth.password_problem("court1"))
        self.assertIsNotNone(pmt_auth.password_problem("seulementdeslettres"))
        self.assertIsNone(pmt_auth.password_problem(ADMIN_PW))

    def test_token_signature_and_expiry(self):
        token = pmt_auth.issue_token(7, 1, ttl=60, now=1000)
        self.assertEqual(pmt_auth.read_token(token, now=1030)["sub"], 7)
        self.assertIsNone(pmt_auth.read_token(token, now=1061))
        header, payload, sig = token.split(".")
        self.assertIsNone(pmt_auth.read_token(f"{header}.{payload}.{sig[:-2]}xx", now=1030))
        self.assertIsNone(pmt_auth.read_token("pas-un-jeton"))

    def test_throttle(self):
        t = pmt_auth.LoginThrottle(max_attempts=2, lockout=10)
        t.fail("k", now=0)
        self.assertFalse(t.locked("k", now=1))
        t.fail("k", now=1)
        self.assertTrue(t.locked("k", now=2))
        self.assertFalse(t.locked("k", now=12))


class AuthApiTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from backend.models.database import Base, PmtUser, get_db
        from backend.routers.pmt import router
        from backend.routers.pmt_auth import router as auth_router

        os.environ["PMT_AUTH_SECRET"] = "secret-de-test"
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["PMT_SCAN_DIR"] = self.tmp.name
        pmt_auth.throttle = pmt_auth.LoginThrottle()
        import backend.routers.pmt_auth as auth_module
        auth_module.pmt_auth.throttle = pmt_auth.throttle

        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        db.add(PmtUser(email="admin@agence.fr", password_hash=pmt_auth.hash_password(ADMIN_PW), role="admin"))
        db.commit()
        db.close()

        def override():
            s = Session()
            try:
                yield s
            finally:
                s.close()

        app = FastAPI()
        app.include_router(auth_router)
        app.include_router(router)
        app.dependency_overrides[get_db] = override
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("PMT_AUTH_SECRET", None)
        os.environ.pop("PMT_SCAN_DIR", None)
        self.tmp.cleanup()

    def login(self, email, password):
        r = self.client.post("/pmt/auth/login", json={"email": email, "password": password})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def make_client(self, admin, email, business):
        r = self.client.post("/pmt/auth/users", headers=admin, json={
            "email": email, "password": CLIENT_PW, "role": "client", "business_id": business})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_routes_require_login(self):
        self.assertEqual(self.client.get("/pmt/vouchers").status_code, 401)
        self.assertEqual(self.client.get("/pmt/export/options").status_code, 401)
        self.assertEqual(self.client.get("/pmt/vouchers", headers={"Authorization": "Bearer faux"}).status_code, 401)

    def test_wrong_password_and_lockout(self):
        for _ in range(pmt_auth.MAX_FAILED_ATTEMPTS):
            r = self.client.post("/pmt/auth/login", json={"email": "admin@agence.fr", "password": "mauvais"})
            self.assertEqual(r.status_code, 401)
        r = self.client.post("/pmt/auth/login", json={"email": "admin@agence.fr", "password": ADMIN_PW})
        self.assertEqual(r.status_code, 429)

    def test_client_only_sees_own_company(self):
        admin = self.login("admin@agence.fr", ADMIN_PW)
        self.make_client(admin, "a@amb-a.fr", "amb-a")
        self.make_client(admin, "b@amb-b.fr", "amb-b")
        a = self.login("a@amb-a.fr", CLIENT_PW)
        b = self.login("b@amb-b.fr", CLIENT_PW)

        # Le client A tente de créer un dossier pour B : il est rattaché à A quand même.
        va = self.client.post("/pmt/vouchers", headers=a, json={
            "business_id": "amb-b", "data": sample_pmt(), "transport": TRANSPORT}).json()
        self.assertEqual(va["business_id"], "amb-a")

        self.assertEqual(len(self.client.get("/pmt/vouchers", headers=a).json()), 1)
        self.assertEqual(self.client.get("/pmt/vouchers", headers=b).json(), [])
        self.assertEqual(self.client.get("/pmt/vouchers", headers=b, params={"business_id": "amb-a"}).json(), [])
        self.assertEqual(self.client.get(f"/pmt/vouchers/{va['id']}", headers=b).status_code, 404)
        self.assertEqual(self.client.get(f"/pmt/vouchers/{va['id']}/fiche", headers=b).status_code, 404)
        self.assertEqual(self.client.patch(f"/pmt/vouchers/{va['id']}", headers=b, json={"status": "draft"}).status_code, 404)
        self.assertEqual(self.client.delete(f"/pmt/vouchers/{va['id']}", headers=b).status_code, 404)
        self.assertEqual(self.client.post("/pmt/export", headers=b, json={"scope": "tous"}).status_code, 404)
        self.assertEqual(self.client.get("/pmt/stats", headers=b).json()["total"], 0)

        # L'admin voit tout.
        self.assertEqual(len(self.client.get("/pmt/vouchers", headers=admin).json()), 1)

    def test_client_cannot_manage_accounts_or_purge(self):
        admin = self.login("admin@agence.fr", ADMIN_PW)
        self.make_client(admin, "a@amb-a.fr", "amb-a")
        a = self.login("a@amb-a.fr", CLIENT_PW)
        self.assertEqual(self.client.get("/pmt/auth/users", headers=a).status_code, 403)
        self.assertEqual(self.client.post("/pmt/scans/purge", headers=a).status_code, 403)

    def test_client_profiles_are_private(self):
        admin = self.login("admin@agence.fr", ADMIN_PW)
        self.make_client(admin, "a@amb-a.fr", "amb-a")
        self.make_client(admin, "b@amb-b.fr", "amb-b")
        a = self.login("a@amb-a.fr", CLIENT_PW)
        b = self.login("b@amb-b.fr", CLIENT_PW)
        shared = self.client.post("/pmt/export/profiles", headers=admin, json={"name": "Commun"}).json()
        own = self.client.post("/pmt/export/profiles", headers=a, json={"name": "Profil A"}).json()
        self.assertEqual(own["business_id"], "amb-a")
        names_b = {p["name"] for p in self.client.get("/pmt/export/profiles", headers=b).json()}
        self.assertEqual(names_b, {"Commun"})
        self.assertEqual(self.client.delete(f"/pmt/export/profiles/{own['id']}", headers=b).status_code, 404)
        self.assertEqual(self.client.delete(f"/pmt/export/profiles/{shared['id']}", headers=b).status_code, 404)

    def test_disabling_or_password_change_revokes_sessions(self):
        admin = self.login("admin@agence.fr", ADMIN_PW)
        user = self.make_client(admin, "a@amb-a.fr", "amb-a")
        a = self.login("a@amb-a.fr", CLIENT_PW)
        self.assertEqual(self.client.get("/pmt/auth/me", headers=a).status_code, 200)
        self.client.patch(f"/pmt/auth/users/{user['id']}", headers=admin, json={"password": "Nouveau-Pass-99"})
        self.assertEqual(self.client.get("/pmt/auth/me", headers=a).status_code, 401)
        a = self.login("a@amb-a.fr", "Nouveau-Pass-99")
        self.client.patch(f"/pmt/auth/users/{user['id']}", headers=admin, json={"active": False})
        self.assertEqual(self.client.get("/pmt/auth/me", headers=a).status_code, 401)

    def test_account_validation(self):
        admin = self.login("admin@agence.fr", ADMIN_PW)
        bad = self.client.post("/pmt/auth/users", headers=admin, json={
            "email": "x@y.fr", "password": "court", "role": "client", "business_id": "b"})
        self.assertEqual(bad.status_code, 400)
        no_company = self.client.post("/pmt/auth/users", headers=admin, json={
            "email": "x@y.fr", "password": CLIENT_PW, "role": "client"})
        self.assertEqual(no_company.status_code, 400)


if __name__ == "__main__":
    unittest.main()
