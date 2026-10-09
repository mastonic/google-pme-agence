import datetime as dt
import os
import tempfile
import unittest

from backend.services import pmt, pmt_auth, pmt_equipe
from tests.test_pmt import TRANSPORT, sample_pmt

DAY = dt.date(2026, 10, 7)
VALID = {"attestation_prefectorale_fin": "2029-01-01", "afgsu2_fin": "2028-06-30", "declare_ars_le": "2024-01-10"}


def member(qualif, **over):
    return pmt_equipe.snapshot(f"id-{qualif}", {"nom": qualif, "qualification": qualif, **VALID, **over})


def codes(mode, crew):
    return {c["code"] for c in pmt_equipe.check_crew(mode, crew, DAY)}


class RulesTests(unittest.TestCase):
    def test_compliant_ambulance_crew(self):
        self.assertEqual(codes("ambulance", [member("DEA"), member("auxiliaire")]), set())

    def test_ambulance_needs_two_and_a_dea(self):
        self.assertIn("EQUIPAGE_INCOMPLET", codes("ambulance", [member("DEA")]))
        self.assertIn("EQUIPAGE_SANS_DEA", codes("ambulance", [member("auxiliaire"), member("conducteur")]))
        self.assertIn("EQUIPAGE_QUALIFICATION", codes("ambulance", [member("DEA"), member("stagiaire")]))

    def test_vsl_single_qualified_driver(self):
        self.assertEqual(codes("tap", [member("auxiliaire")]), set())
        self.assertIn("EQUIPAGE_QUALIFICATION", codes("tap", [member("conducteur")]))

    def test_expired_documents_at_transport_date(self):
        expired = member("DEA", afgsu2_fin="2026-09-30")
        self.assertIn("EQUIPIER_NON_CONFORME", codes("ambulance", [expired, member("auxiliaire")]))
        # Même équipier, transport antérieur à l'expiration : conforme ce jour-là.
        self.assertEqual({c["code"] for c in pmt_equipe.check_crew(
            "ambulance", [expired, member("auxiliaire")], dt.date(2026, 9, 1))}, set())

    def test_ended_contract(self):
        self.assertIn("EQUIPIER_NON_CONFORME",
                      codes("ambulance", [member("DEA", contrat_fin="2026-10-01"), member("DEA")]))

    def test_compliance_status_and_soon(self):
        self.assertEqual(pmt_equipe.compliance({**VALID}, DAY)["status"], "ok")
        soon = pmt_equipe.compliance({**VALID, "afgsu2_fin": "2026-11-15"}, DAY)
        self.assertEqual(soon["status"], "bientot")
        self.assertEqual(pmt_equipe.compliance({}, DAY)["status"], "non_conforme")

    def test_afgsu_four_years(self):
        self.assertEqual(pmt_equipe.afgsu_end_from_obtention("15/03/2024"), "2028-03-15")

    def test_crew_checks_flow_into_dossier(self):
        transport = {**TRANSPORT, "equipage_detail": [member("auxiliaire"), member("conducteur")]}
        found = {c["code"] for c in pmt.validate_pmt(sample_pmt(), transport, today=dt.date(2026, 10, 9))}
        self.assertIn("EQUIPAGE_SANS_DEA", found)
        self.assertNotIn("EQUIPAGE", found)


class EquipeApiTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from backend.models.database import Base, PmtUser, get_db
        from backend.routers.pmt import router
        from backend.routers.pmt_auth import router as auth_router
        from backend.routers.pmt_equipe import router as equipe_router
        from backend.routers.pmt_rejets import router as rejets_router

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
        db.add(PmtUser(email="gerant@a.fr", password_hash=pmt_auth.hash_password("Gerant-Pass-1"),
                       role="client", business_id="amb-a"))
        db.commit()
        db.close()

        def override():
            s = Session()
            try:
                yield s
            finally:
                s.close()

        app = FastAPI()
        for r in (auth_router, equipe_router, rejets_router, router):
            app.include_router(r)
        app.dependency_overrides[get_db] = override
        self.client = TestClient(app)
        self.gerant = self.login("gerant@a.fr", "Gerant-Pass-1")

    def tearDown(self):
        os.environ.pop("PMT_AUTH_SECRET", None)
        os.environ.pop("PMT_SCAN_DIR", None)
        self.tmp.cleanup()

    def login(self, email, password):
        r = self.client.post("/pmt/auth/login", json={"email": email, "password": password})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def add(self, nom, qualif, **over):
        r = self.client.post("/pmt/equipe", headers=self.gerant, json={"nom": nom, "qualification": qualif, **VALID, **over})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_register_alerts_and_crew_on_dossier(self):
        dea = self.add("Diallo", "DEA")
        aux = self.add("Morel", "auxiliaire", afgsu2_fin="2026-10-01")   # expirée
        alerts = self.client.get("/pmt/equipe/alertes", headers=self.gerant).json()
        self.assertEqual((alerts["salaries_actifs"], alerts["non_conformes"]), (2, 1))

        v = self.client.post("/pmt/vouchers", headers=self.gerant, json={
            "data": sample_pmt(), "transport": {**TRANSPORT, "equipage_ids": [dea["id"], aux["id"]]}}).json()
        self.assertEqual(v["transport"]["equipage"], "DIALLO / MOREL")
        self.assertEqual(v["readiness"], "bloquant")
        self.assertIn("EQUIPIER_NON_CONFORME", {c["code"] for c in v["checks"]})

        # AFGSU renouvelée : le dossier non exporté est recontrôlé tout seul.
        r = self.client.put(f"/pmt/equipe/{aux['id']}", headers=self.gerant, json={"afgsu2_fin": "2030-10-01"})
        self.assertEqual(r.json()["dossiers_recontroles"], 1)
        again = self.client.get(f"/pmt/vouchers/{v['id']}", headers=self.gerant).json()
        self.assertNotIn("EQUIPIER_NON_CONFORME", {c["code"] for c in again["checks"]})

    def test_employee_access_is_limited(self):
        dea = self.add("Diallo", "DEA")
        r = self.client.post(f"/pmt/equipe/{dea['id']}/acces", headers=self.gerant,
                             json={"email": "k.diallo@a.fr", "password": "Equipier-Pass-1"})
        self.assertTrue(r.json()["a_un_acces"])
        emp = self.login("k.diallo@a.fr", "Equipier-Pass-1")

        # L'équipier saisit un bon : il est mis d'office dans l'équipage.
        v = self.client.post("/pmt/vouchers", headers=emp, json={"data": sample_pmt(), "transport": TRANSPORT}).json()
        self.assertEqual(v["transport"]["equipage_ids"], [dea["id"]])
        self.assertEqual(v["business_id"], "amb-a")
        # Il complète la course, mais ne valide pas, n'exporte pas, ne supprime pas.
        self.assertEqual(self.client.patch(f"/pmt/vouchers/{v['id']}", headers=emp,
                                           json={"transport": {**TRANSPORT, "km_aller": 30}}).status_code, 200)
        self.assertEqual(self.client.patch(f"/pmt/vouchers/{v['id']}", headers=emp,
                                           json={"status": "validated"}).status_code, 403)
        self.assertEqual(self.client.post("/pmt/export", headers=emp, json={}).status_code, 403)
        self.assertEqual(self.client.delete(f"/pmt/vouchers/{v['id']}", headers=emp).status_code, 403)
        self.assertEqual(self.client.get("/pmt/rejets", headers=emp).status_code, 403)
        self.assertEqual(self.client.get("/pmt/equipe/alertes", headers=emp).status_code, 403)
        # Il voit ses collègues pour choisir un coéquipier, sans leurs données RH.
        colleague = self.client.get("/pmt/equipe", headers=emp).json()[0]
        self.assertNotIn("afgsu2_fin", colleague)

    def test_leaving_employee_loses_access(self):
        dea = self.add("Diallo", "DEA")
        self.client.post(f"/pmt/equipe/{dea['id']}/acces", headers=self.gerant,
                         json={"email": "k.diallo@a.fr", "password": "Equipier-Pass-1"})
        emp = self.login("k.diallo@a.fr", "Equipier-Pass-1")
        self.client.put(f"/pmt/equipe/{dea['id']}", headers=self.gerant, json={"actif": False})
        self.assertEqual(self.client.get("/pmt/vouchers", headers=emp).status_code, 401)

    def test_manager_creates_only_employee_accounts_for_own_company(self):
        r = self.client.post("/pmt/auth/users", headers=self.gerant, json={
            "email": "e@a.fr", "password": "Equipier-Pass-1", "role": "employe", "business_id": "amb-b"})
        self.assertEqual((r.status_code, r.json()["business_id"]), (200, "amb-a"))
        self.assertEqual([u["email"] for u in self.client.get("/pmt/auth/users", headers=self.gerant).json()],
                         ["e@a.fr"])


if __name__ == "__main__":
    unittest.main()
