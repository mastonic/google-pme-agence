import datetime as dt
import os
import tempfile
import unittest
from unittest import mock

from backend.services import pmt, pmt_auth, pmt_planning
from tests.test_pmt import sample_pmt

VALID = {"attestation_prefectorale_fin": "2029-01-01", "afgsu2_fin": "2028-06-30", "declare_ars_le": "2024-01-10"}


def mission(mid, heure, crew, vehicule="AB-123-CD", mode="ambulance", status="planifiee"):
    return {"id": mid, **pmt_planning.normalize_mission({"date": "2026-10-07", "heure_prevue": heure,
                                                         "equipage_ids": crew, "vehicule": vehicule, "mode": mode}),
            "status": status, "events": []}


class RulesTests(unittest.TestCase):
    EMP = {"dea": {"nom": "Diallo", "qualification": "DEA", **VALID},
           "aux": {"nom": "Morel", "qualification": "auxiliaire", **VALID},
           "old": {"nom": "Petit", "qualification": "DEA", **VALID, "afgsu2_fin": "2026-01-01"}}

    def test_overlap_same_crew_and_vehicle(self):
        a = mission("a", "08:30", ["dea", "aux"])
        b = mission("b", "09:00", ["dea", "aux"])
        c = mission("c", "11:00", ["dea", "aux"])
        out = pmt_planning.conflicts([a, b, c], self.EMP)
        self.assertTrue(any("DIALLO" in x or "Diallo" in x for x in out["a"]))
        self.assertTrue(any("Véhicule" in x for x in out["b"]))
        self.assertEqual(out["c"], [])

    def test_crew_rules_and_expired_documents_at_planning(self):
        out = pmt_planning.conflicts([mission("a", "08:30", ["aux"]), mission("b", "14:00", ["old", "aux"],
                                                                              vehicule="EF-456-GH")], self.EMP)
        self.assertTrue(any("deux équipiers" in x for x in out["a"]))
        self.assertTrue(any("AFGSU" in x for x in out["b"]))

    def test_cancelled_missions_do_not_conflict(self):
        a = mission("a", "08:30", ["dea", "aux"])
        b = mission("b", "08:30", ["dea", "aux"], status="annulee")
        self.assertEqual(pmt_planning.conflicts([a, b], self.EMP)["a"], [])

    def test_transitions(self):
        m = mission("a", "08:30", ["dea", "aux"])
        m = pmt_planning.apply_action(m, "depart", "x", at=dt.datetime(2026, 10, 7, 8, 34), km_compteur=1000)
        self.assertEqual(m["status"], "en_cours")
        with self.assertRaises(pmt_planning.TransitionError):
            pmt_planning.apply_action(m, "accepter", "x")
        m = pmt_planning.apply_action(m, "arrivee", "x")
        m = pmt_planning.apply_action(m, "retour", "x", km_compteur=1064.5)
        self.assertEqual(m["status"], "terminee")
        self.assertEqual(pmt_planning.odometer_km(m), 64.5)
        self.assertEqual(pmt_planning.transport_from_mission(m)["heure_depart"], "08:34")
        with self.assertRaises(pmt_planning.TransitionError):
            pmt_planning.apply_action(m, "annuler", "x")


class PlanningApiTests(unittest.TestCase):
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
        from backend.routers.pmt_planning import router as planning_router

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
        for r in (auth_router, equipe_router, planning_router, router):
            app.include_router(r)
        app.dependency_overrides[get_db] = override
        self.client = TestClient(app)
        self.g = self.login("gerant@a.fr", "Gerant-Pass-1")
        self.dea = self.client.post("/pmt/equipe", headers=self.g, json={"nom": "Diallo", "qualification": "DEA", **VALID}).json()
        self.aux = self.client.post("/pmt/equipe", headers=self.g, json={"nom": "Morel", "qualification": "auxiliaire", **VALID}).json()
        self.client.post(f"/pmt/equipe/{self.dea['id']}/acces", headers=self.g,
                         json={"email": "dea@a.fr", "password": "Equipier-Pass-1"})
        self.e = self.login("dea@a.fr", "Equipier-Pass-1")

    def tearDown(self):
        os.environ.pop("PMT_AUTH_SECRET", None)
        os.environ.pop("PMT_SCAN_DIR", None)
        self.tmp.cleanup()

    def login(self, email, password):
        r = self.client.post("/pmt/auth/login", json={"email": email, "password": password})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": f"Bearer {r.json()['token']}"}

    def plan(self, heure="08:30", **over):
        r = self.client.post("/pmt/planning/missions", headers=self.g, json={
            "date": "2026-10-07", "heure_prevue": heure, "patient_nom": "Martin", "vehicule": "AB-123-CD",
            "adresse_depart": "Domicile", "adresse_arrivee": "CH Versailles", "type_trajet": "aller",
            "equipage_ids": [self.dea["id"], self.aux["id"]], **over})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def act(self, headers, mid, action, **extra):
        return self.client.post(f"/pmt/planning/missions/{mid}/action", headers=headers, json={"action": action, **extra})

    def test_full_day_cycle(self):
        m = self.plan()
        # Avant publication, l'équipier ne voit rien et ne peut rien valider.
        self.assertEqual(self.client.get("/pmt/planning/mes-missions?date=2026-10-07", headers=self.e).json()["missions"], [])
        self.assertEqual(self.act(self.e, m["id"], "depart").status_code, 403)

        self.client.post("/pmt/planning/jour/publier", headers=self.g, json={"date": "2026-10-07"})
        mine = self.client.get("/pmt/planning/mes-missions?date=2026-10-07", headers=self.e).json()["missions"]
        self.assertEqual([x["id"] for x in mine], [m["id"]])

        self.assertEqual(self.act(self.e, m["id"], "accepter").json()["status"], "acceptee")
        self.assertEqual(self.act(self.e, m["id"], "depart", km_compteur=1000).json()["status"], "en_cours")
        self.assertEqual(self.act(self.e, m["id"], "arrivee").status_code, 200)
        # Une étape déjà passée est refusée.
        self.assertEqual(self.act(self.e, m["id"], "depart").status_code, 409)
        # Clôture refusée tant qu'une mission n'est pas terminée.
        self.assertEqual(self.client.post("/pmt/planning/jour/valider", headers=self.g,
                                          json={"date": "2026-10-07"}).status_code, 409)

        done = self.act(self.e, m["id"], "retour", km_compteur=1031).json()
        self.assertEqual((done["status"], done["km_compteur"]), ("terminee", 31.0))
        # Retour validé : dossier créé avec l'heure réelle de départ et l'équipage.
        v = self.client.get(f"/pmt/vouchers/{done['voucher_id']}", headers=self.g).json()
        self.assertEqual(v["transport"]["date_transport"], "2026-10-07")
        self.assertEqual(len(v["transport"]["equipage_ids"]), 2)
        self.assertEqual(v["data"]["beneficiaire"]["nom"], "MARTIN")

        # Le bon photographié ensuite complète ce dossier, sans doublon.
        fake = {"data": pmt.normalize_pmt(sample_pmt()), "provider": "test"}
        with mock.patch.object(pmt, "extract_pmt", return_value=fake):
            r = self.client.post("/pmt/extract", headers=self.e, data={"mission_id": m["id"]},
                                 files={"file": ("bon.jpg", b"\xff\xd8 photo", "image/jpeg")})
        self.assertEqual(r.json()["id"], done["voucher_id"])
        self.assertEqual(len(self.client.get("/pmt/vouchers", headers=self.g).json()), 1)

        closed = self.client.post("/pmt/planning/jour/valider", headers=self.g, json={"date": "2026-10-07"}).json()
        self.assertEqual(closed["status"], "valide")
        # Journée validée : plus de modification.
        self.assertEqual(self.client.put(f"/pmt/planning/missions/{m['id']}", headers=self.g,
                                         json={"heure_prevue": "09:00"}).status_code, 409)

    def test_employee_restrictions(self):
        m = self.plan()
        other = self.plan(heure="14:00", equipage_ids=[self.aux["id"]], vehicule="VSL-2", mode="tap")
        self.client.post("/pmt/planning/jour/publier", headers=self.g, json={"date": "2026-10-07"})
        self.assertEqual(self.act(self.e, other["id"], "depart").status_code, 403)   # pas sa mission
        self.assertEqual(self.act(self.e, m["id"], "annuler").status_code, 403)      # réservé au gérant
        self.assertEqual(self.client.get("/pmt/planning/jour?date=2026-10-07", headers=self.e).status_code, 403)
        self.assertEqual(self.client.post("/pmt/planning/missions", headers=self.e,
                                          json={"date": "2026-10-07", "heure_prevue": "10:00"}).status_code, 403)

    def test_day_view_reports_conflicts(self):
        self.plan(heure="08:30")
        self.plan(heure="09:00")
        day = self.client.get("/pmt/planning/jour?date=2026-10-07", headers=self.g).json()
        self.assertEqual(day["status"], "brouillon")
        self.assertTrue(all(m["problemes"] for m in day["missions"]))
        self.assertEqual(day["resume"]["total"], 2)


if __name__ == "__main__":
    unittest.main()
