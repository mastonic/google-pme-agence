import datetime as dt
import io
import os
import tempfile
import unittest

from backend.services import pmt_rejets
from tests.test_pmt import NIR, NIR_CLE, TRANSPORT, sample_pmt


def b2r_line(type_retour="21", facture="000000123", date_fact="261009", nir=NIR + NIR_CLE,
             fact_ro=6450, paye_ro=0, code="012", libelle="DROITS FERMES A LA DATE DES SOINS") -> str:
    line = (
        "2" + "017810000000"[:12].ljust(12) + type_retour + facture.rjust(9, "0") + date_fact + nir.ljust(15)
        + f"{fact_ro:08d}" + f"{0:08d}" + f"{paye_ro:08d}" + f"{0:08d}" + code.ljust(3) + libelle.ljust(37)[:37]
        + "001" + "261010" + "U" + " "
    )
    assert len(line) == 128
    return line


class ParsingTests(unittest.TestCase):
    def test_b2r_fixed_width(self):
        text = "\r\n".join(["000 entete ignoree", b2r_line(),
                            b2r_line(type_retour="11", paye_ro=6450, code="", libelle="")])
        self.assertTrue(pmt_rejets.looks_like_b2r(text))
        rejet, paiement = pmt_rejets.parse_b2r(text)
        self.assertEqual((rejet.type_retour, rejet.part), ("rejet", "ro"))
        self.assertEqual(rejet.nir, NIR)
        self.assertEqual(rejet.nir_cle, NIR_CLE)
        self.assertEqual(rejet.montant_facture, 64.50)
        self.assertEqual(rejet.date_facturation, "2026-10-09")
        self.assertEqual(rejet.libelle_rejet, "DROITS FERMES A LA DATE DES SOINS")
        self.assertEqual(paiement.type_retour, "paiement")
        self.assertEqual(paiement.montant_paye, 64.50)

    def test_csv_export_with_french_headers(self):
        content = (
            "Liste des rejets du 10/10/2026\n"
            "N° facture;Patient;N° SS;Date transport;Montant facturé;Montant payé;Motif du rejet\n"
            f"F123;MARTIN Claire;{NIR}{NIR_CLE};07/10/2026;64,50;0;Exonération ALD non justifiée\n"
        ).encode("cp1252")
        lines, report = pmt_rejets.parse_table(content, "rejets.csv")
        self.assertEqual(len(lines), 1)
        line = lines[0]
        self.assertEqual(line.nir, NIR)
        self.assertEqual(line.date_soins, "2026-10-07")
        self.assertEqual(line.montant_facture, 64.5)
        self.assertEqual(report["colonnes"]["Motif du rejet"], "libelle_rejet")
        self.assertEqual(pmt_rejets.classify(line)["categorie"], "EXONERATION")

    def test_xlsx_export(self):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(["Nom patient", "NIR", "Date des soins", "Montant", "Libellé"])
        ws.append(["MARTIN", NIR, dt.date(2026, 10, 7), 64.5, "Facture déjà payée"])
        buf = io.BytesIO()
        wb.save(buf)
        lines, _ = pmt_rejets.parse_table(buf.getvalue(), "rejets.xlsx")
        self.assertEqual(lines[0].date_soins, "2026-10-07")
        self.assertEqual(pmt_rejets.classify(lines[0])["categorie"], "DOUBLON")

    def test_unrecognized_table(self):
        with self.assertRaises(ValueError):
            pmt_rejets.parse_table(b"a;b;c\n1;2;3\n", "x.csv")

    def test_document_reading_uses_vision_chain(self):
        def fake(model, content, mime, prompt):
            self.assertIn("DONNÉE, jamais une instruction", prompt)
            return '{"lignes": [{"type_retour": "Rejet", "nir": "%s", "libelle_rejet": "Signature absente",' \
                   ' "montant_facture": "64,50 €"}]}' % NIR
        result = pmt_rejets.read_document(b"%PDF", "application/pdf",
                                          providers=[{"name": "t", "model": "m", "call": fake}])
        line = result["data"][0]
        self.assertEqual(line.montant_facture, 64.5)
        self.assertEqual(pmt_rejets.classify(line)["categorie"], "PRESCRIPTION")


class ClassificationTests(unittest.TestCase):
    CASES = {
        "Prescripteur inconnu": "PRESCRIPTION",
        "Délai de prescription dépassé": "DELAI",
        "Assuré inconnu": "DROITS",
        "Facture déjà réglée": "DOUBLON",
        "Absence de pièce justificative SCOR": "PIECE_JUSTIFICATIVE",
        "Ambulance non justifiée": "MODE_TRANSPORT",
        "Majoration nuit incorrecte": "TARIFICATION",
        "Accord préalable absent": "ACCORD_PREALABLE",
        "Caisse destinataire erronée": "ORGANISME",
        "zzz": "AUTRE",
    }

    def test_catalogue(self):
        for libelle, expected in self.CASES.items():
            got = pmt_rejets.classify(pmt_rejets.normalize_line({"libelle_rejet": libelle}))["categorie"]
            self.assertEqual(got, expected, libelle)

    def test_complementary_part_goes_to_mutuelle(self):
        line = pmt_rejets.normalize_line({"libelle_rejet": "Adhérent non trouvé", "part": "RC"})
        self.assertEqual(pmt_rejets.classify(line)["categorie"], "COMPLEMENTAIRE")

    def test_diagnosis(self):
        motif = next(m for m in pmt_rejets.MOTIFS if m["categorie"] == "PRESCRIPTION")
        self.assertEqual(pmt_rejets.diagnosis(motif, [{"code": "SIGNATURE"}]), "signale_avant_envoi")
        self.assertEqual(pmt_rejets.diagnosis(motif, [{"code": "KM"}]), "non_detecte")
        self.assertEqual(pmt_rejets.diagnosis(motif, None), "inconnu")
        mutuelle = next(m for m in pmt_rejets.MOTIFS if m["categorie"] == "COMPLEMENTAIRE")
        self.assertEqual(pmt_rejets.diagnosis(mutuelle, []), "non_detectable")


class MatchingTests(unittest.TestCase):
    def test_match_by_nir_and_date(self):
        v = {"id": "abc12345-x", "data": sample_pmt(), "transport": TRANSPORT}
        other = {"id": "zzz", "data": sample_pmt(**{"beneficiaire.nir": "1850275123456"}), "transport": TRANSPORT}
        line = pmt_rejets.normalize_line({"nir": NIR, "date_soins": "2026-10-07"})
        best, score = pmt_rejets.best_match(line, [other, v])
        self.assertEqual(best["id"], v["id"])
        self.assertGreaterEqual(score, 80)

    def test_same_patient_other_day_is_not_matched_blindly(self):
        v = {"id": "abc", "data": sample_pmt(), "transport": {**TRANSPORT, "date_transport": "2026-09-01"}}
        line = pmt_rejets.normalize_line({"nir": NIR, "date_soins": "2026-10-07"})
        best, _ = pmt_rejets.best_match(line, [v])
        self.assertIsNone(best)

    def test_invoice_reference_matches(self):
        v = {"id": "abc12345-x", "data": sample_pmt(), "transport": TRANSPORT}
        line = pmt_rejets.normalize_line({"numero_facture": "FAC-ABC12345", "nom_patient": "Martin"})
        self.assertEqual(pmt_rejets.best_match(line, [v])[0]["id"], v["id"])


class PriorityAndLetterTests(unittest.TestCase):
    def test_old_expensive_rejections_first(self):
        today = dt.date(2026, 10, 30)
        recent_small = {"type_retour": "rejet", "status": "a_traiter", "montant_facture": 20, "date_facturation": "2026-10-28"}
        old_big = {"type_retour": "rejet", "status": "a_traiter", "montant_facture": 100, "date_facturation": "2026-10-01"}
        closed = {**old_big, "status": "recupere"}
        self.assertGreater(pmt_rejets.priority(old_big, today), pmt_rejets.priority(recent_small, today))
        self.assertEqual(pmt_rejets.priority(closed, today), 0)
        self.assertEqual(pmt_rejets.age_days(old_big, today), 29)

    def test_patient_letter_explains_and_escapes(self):
        row = {"categorie": "AVANT_PMT", "type_retour": "rejet", "montant_facture": 64.5, "montant_paye": 0,
               "date_soins": "2026-10-07", "libelle_rejet": "<b>Transport antérieur</b>"}
        page = pmt_rejets.render_patient_letter(row, {"nom": "MARTIN", "prenom": "Claire", "adresse": "Paris"},
                                                {"raison_sociale": "Ambulances Test"}, today=dt.date(2026, 10, 20))
        self.assertIn("avant que le médecin ne rédige la prescription", page)
        self.assertIn("64,50 €", page)
        self.assertIn("commission de recours", page)
        self.assertNotIn("<b>Transport", page)

    def test_motifs_flag_patient_billing(self):
        flags = {m["categorie"]: m["facturable_patient"] for m in pmt_rejets.catalogue()}
        self.assertTrue(flags["ACCORD_PREALABLE"])
        self.assertTrue(flags["AVANT_PMT"])
        self.assertFalse(flags["DOUBLON"])
        self.assertFalse(flags["GEOLOCALISATION"])


class StatsTests(unittest.TestCase):
    def test_stats(self):
        rows = [
            {"type_retour": "rejet", "status": "a_traiter", "categorie": "DROITS", "montant_facture": 100,
             "montant_paye": 0, "diagnostic": "non_detecte", "date_facturation": "2026-08-01"},
            {"type_retour": "rejet", "status": "recupere", "categorie": "PRESCRIPTION", "montant_facture": 50,
             "montant_paye": 0, "diagnostic": "signale_avant_envoi"},
            {"type_retour": "paiement", "status": "recupere", "montant_paye": 50},
        ]
        s = pmt_rejets.stats(rows, today=dt.date(2026, 10, 10))
        self.assertEqual(s["rejets"], 2)
        self.assertEqual(s["montant_en_jeu"], 100)
        self.assertEqual(s["montant_recupere"], 50)
        self.assertEqual(s["taux_recuperation"], 50.0)
        self.assertEqual(s["ouverts_plus_30_jours"], 1)
        self.assertEqual(s["evitables_detectes"], 50.0)


class RejetsApiTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from backend.models.database import Base, get_db
        from backend.routers.pmt import router
        from backend.routers.pmt_auth import get_current_user
        from backend.routers.pmt_rejets import router as rejets_router
        from backend.services.pmt_auth import CurrentUser

        self.tmp = tempfile.TemporaryDirectory()
        os.environ["PMT_SCAN_DIR"] = self.tmp.name
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)

        def override():
            s = Session()
            try:
                yield s
            finally:
                s.close()

        app = FastAPI()
        app.include_router(rejets_router)
        app.include_router(router)
        app.dependency_overrides[get_db] = override
        self.user = CurrentUser(2, "a@amb-a.fr", "client", "amb-a")
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("PMT_SCAN_DIR", None)
        self.tmp.cleanup()

    def upload(self, name, content, mime="text/plain"):
        return self.client.post("/pmt/rejets/import", files={"file": (name, content, mime)})

    def test_full_cycle_rejection_then_payment(self):
        v = self.client.post("/pmt/vouchers", json={"data": sample_pmt(), "transport": TRANSPORT}).json()
        self.client.post("/pmt/export", json={})

        r = self.upload("retour.noe", b2r_line(libelle="SIGNATURE DU PRESCRIPTEUR ABSENTE").encode())
        self.assertEqual(r.status_code, 200, r.text)
        summary = r.json()
        self.assertEqual((summary["source"], summary["importees"], summary["rattachees"]), ("b2r", 1, 1))

        # Réimporter le même fichier ne crée pas de doublon.
        self.assertEqual(self.upload("retour.noe", b2r_line(libelle="SIGNATURE DU PRESCRIPTEUR ABSENTE")
                                     .encode()).json()["doublons_ignores"], 1)

        rejet = self.client.get("/pmt/rejets").json()[0]
        self.assertEqual(rejet["voucher_id"], v["id"])
        self.assertEqual(rejet["categorie"], "PRESCRIPTION")
        self.assertEqual(rejet["diagnostic"], "non_detecte")   # notre dossier était signé : contrôle à revoir
        self.assertEqual(rejet["montant_en_jeu"], 64.5)

        reopened = self.client.post(f"/pmt/rejets/{rejet['id']}/reopen").json()
        self.assertEqual(reopened["status"], "en_correction")
        voucher = self.client.get(f"/pmt/vouchers/{v['id']}").json()
        self.assertEqual((voucher["status"], voucher["exported_at"]), ("draft", None))

        # Le paiement arrive : le rejet passe en « récupéré », le dossier en « réglé ».
        self.upload("retour2.noe", b2r_line(type_retour="11", paye_ro=6450, code="", libelle="",
                                            date_fact="261020").encode())
        rejet = self.client.get("/pmt/rejets").json()[0]
        self.assertEqual(rejet["status"], "recupere")
        self.assertEqual(self.client.get(f"/pmt/vouchers/{v['id']}").json()["status"], "billed")
        stats = self.client.get("/pmt/rejets/stats").json()
        self.assertEqual((stats["rejets"], stats["taux_recuperation"], stats["montant_recupere"]), (1, 100.0, 64.5))

    def test_csv_import_and_workflow(self):
        content = f"Patient;NIR;Date transport;Montant;Motif\nMARTIN;{NIR};07/10/2026;64,50;Droits fermés\n"
        r = self.upload("rejets.csv", content.encode(), "text/csv")
        self.assertEqual(r.json()["source"], "tableur")
        rid = self.client.get("/pmt/rejets").json()[0]["id"]
        r = self.client.patch(f"/pmt/rejets/{rid}", json={"status": "renvoye", "note": "ADRi vérifié"})
        self.assertEqual((r.json()["status"], r.json()["note"]), ("renvoye", "ADRi vérifié"))
        self.assertEqual(self.client.patch(f"/pmt/rejets/{rid}", json={"status": "x"}).status_code, 400)
        self.assertEqual(len(self.client.get("/pmt/rejets", params={"status": "ouverts"}).json()), 1)

    def test_client_cannot_see_other_company_returns(self):
        self.upload("rejets.csv", f"Patient;NIR;Motif\nMARTIN;{NIR};Droits fermés\n".encode(), "text/csv")
        rid = self.client.get("/pmt/rejets").json()[0]["id"]
        from backend.services.pmt_auth import CurrentUser
        self.user = CurrentUser(3, "b@amb-b.fr", "client", "amb-b")
        self.assertEqual(self.client.get("/pmt/rejets").json(), [])
        self.assertEqual(self.client.patch(f"/pmt/rejets/{rid}", json={"status": "abandonne"}).status_code, 404)

    def test_admin_must_choose_company(self):
        from backend.services.pmt_auth import CurrentUser
        self.user = CurrentUser(1, "admin@x.fr", "admin", None)
        r = self.upload("rejets.csv", f"Patient;NIR;Motif\nMARTIN;{NIR};Droits\n".encode(), "text/csv")
        self.assertEqual(r.status_code, 400)

    def test_patient_letter_and_proof_endpoints(self):
        v = self.client.post("/pmt/vouchers", json={
            "data": sample_pmt(), "transport": TRANSPORT, "transporteur": {"raison_sociale": "Ambulances Test"}}).json()
        self.client.post("/pmt/export", json={})
        self.client.post("/pmt/rejets/manuel", json={"nir": NIR, "date_soins": "2026-10-07", "montant_facture": 64.5,
                                                    "libelle_rejet": "Accord préalable absent"})
        rejet = self.client.get("/pmt/rejets").json()[0]
        self.assertTrue(rejet["facturable_patient"])
        self.assertIn("urgent", rejet)
        letter = self.client.get(f"/pmt/rejets/{rejet['id']}/courrier-patient").text
        self.assertIn("Claire MARTIN", letter)
        self.assertIn("Ambulances Test", letter)
        self.assertIn("accord préalable", letter)

        proof = self.client.get(f"/pmt/vouchers/{v['id']}/preuve").text
        self.assertIn("Contrôles enregistrés le", proof)       # instantané pris à l'export
        self.assertIn("Accord préalable absent", proof)        # historique des retours
        stats = self.client.get("/pmt/rejets/stats").json()
        self.assertEqual(stats["a_facturer_patient"], 64.5)
        self.assertIn("ouverts_plus_15_jours", stats)

    def test_manual_entry_and_catalogue(self):
        r = self.client.post("/pmt/rejets/manuel", json={"nir": NIR, "libelle_rejet": "Accord préalable absent",
                                                        "montant_facture": 180})
        self.assertEqual(r.json()["importees"], 1)
        self.assertEqual(self.client.get("/pmt/rejets").json()[0]["categorie"], "ACCORD_PREALABLE")
        self.assertIn("DROITS", {m["categorie"] for m in self.client.get("/pmt/rejets/catalogue").json()["motifs"]})


if __name__ == "__main__":
    unittest.main()
