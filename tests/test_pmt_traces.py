import datetime as dt
import os
import tempfile
import unittest

from backend.services import pmt, pmt_traces
from tests.test_pmt import TRANSPORT, sample_pmt

# Trajet fictif : ~32 km plein est depuis Versailles, un point par minute à ~48 km/h.
START = dt.datetime(2026, 10, 7, 8, 30)          # heure locale
LAT0, LON0 = 48.8049, 2.1204
STEP_LON = 0.0109                                 # ≈ 0,8 km par minute à cette latitude


def track_points(n=41, start=START, lon0=LON0):
    return [(LAT0, lon0 + i * STEP_LON, start + dt.timedelta(minutes=i)) for i in range(n)]


def expected_km(points):
    pts = [pmt_traces.Point(a, b) for a, b, _ in points]
    return sum(pmt_traces.haversine_km(p, q) for p, q in zip(pts, pts[1:]))


def utc(d):
    # Heure de Paris en octobre = UTC+2.
    return (d - dt.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")


def gpx(tracks):
    body = ""
    for name, pts in tracks:
        seg = "".join(f'<trkpt lat="{a}" lon="{b}"><time>{utc(t)}</time></trkpt>' for a, b, t in pts)
        body += f"<trk><name>{name}</name><trkseg>{seg}</trkseg></trk>"
    return (f'<?xml version="1.0"?><gpx version="1.1" creator="boitier" '
            f'xmlns="http://www.topografix.com/GPX/1/1">{body}</gpx>').encode()


class ParseTests(unittest.TestCase):
    def test_gpx_track_distance_vehicle_and_time(self):
        pts = track_points()
        trips = pmt_traces.parse_gpx(gpx([("AB-123-CD mission 4521", pts)]))
        self.assertEqual(len(trips), 1)
        t = trips[0]
        self.assertAlmostEqual(t.km, expected_km(pts), places=3)
        self.assertGreater(t.km, 30)
        self.assertEqual(t.vehicule, "AB-123-CD")
        self.assertEqual(t.reference, "4521")
        self.assertEqual(t.start, START)            # converti de UTC vers l'heure de Paris
        self.assertEqual(t.trous, 0)

    def test_gps_jump_is_ignored(self):
        pts = track_points(n=11)
        pts[5] = (LAT0 + 1.0, pts[5][1], pts[5][2])  # saut de 110 km en une minute
        t = pmt_traces.parse_gpx(gpx([("AB-123-CD", pts)]))[0]
        clean = [p for i, p in enumerate(pts) if i != 5]
        self.assertAlmostEqual(t.km, expected_km(clean), places=3)
        self.assertTrue(any("aberrant" in w for w in t.warnings))

    def test_network_gap_is_flagged(self):
        pts = track_points(n=21)
        pts = pts[:10] + [(a, b, tm + dt.timedelta(minutes=6)) for a, b, tm in pts[15:]]
        t = pmt_traces.parse_gpx(gpx([("AB-123-CD", pts)]))[0]
        self.assertEqual(t.trous, 1)
        self.assertGreater(t.km_trous, 3)

    def test_unnamed_daily_track_is_split_on_long_stops(self):
        morning = track_points(n=21)
        afternoon = [(LAT0, morning[-1][1], morning[-1][2] + dt.timedelta(minutes=40 + i)) for i in range(1)]
        back = track_points(n=21, start=morning[-1][2] + dt.timedelta(minutes=41), lon0=morning[-1][1])
        content = gpx([("", morning + afternoon + back)]).replace(b"<name></name>", b"")
        trips = pmt_traces.parse_gpx(content, "export_AB-123-CD_2026-10-07.gpx")
        self.assertEqual(len(trips), 2)
        self.assertEqual(trips[0].vehicule, "AB-123-CD")

    def test_xml_entities_are_refused(self):
        evil = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "b">]><gpx></gpx>'
        with self.assertRaises(ValueError):
            pmt_traces.parse_gpx(evil)

    def test_kml_gx_track(self):
        pts = track_points(n=11)
        whens = "".join(f"<when>{utc(t)}</when>" for _, _, t in pts)
        coords = "".join(f"<gx:coord>{b} {a} 0</gx:coord>" for a, b, _ in pts)
        kml = (f'<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">'
               f"<Document><Placemark><name>VSL-7</name><gx:Track>{whens}{coords}</gx:Track></Placemark>"
               f"</Document></kml>").encode()
        t = pmt_traces.parse_file(kml, "traces.kml")[0]
        self.assertEqual(t.vehicule, "VSL-7")
        self.assertAlmostEqual(t.km, expected_km(pts), places=3)

    def test_csv_points_grouped_by_vehicle(self):
        rows = ["Immatriculation;Date heure;Latitude;Longitude"]
        for a, b, t in track_points(n=11):
            rows.append(f"AB-123-CD;{t.strftime('%d/%m/%Y %H:%M:%S')};{str(a).replace('.', ',')};{str(b).replace('.', ',')}")
        for a, b, t in track_points(n=6):
            rows.append(f"EF-456-GH;{t.strftime('%d/%m/%Y %H:%M:%S')};{a};{b}")
        trips = pmt_traces.parse_file("\n".join(rows).encode(), "points.csv")
        by_vehicle = {t.vehicule: t for t in trips}
        self.assertEqual(set(by_vehicle), {"AB-123-CD", "EF-456-GH"})
        self.assertGreater(by_vehicle["AB-123-CD"].km, by_vehicle["EF-456-GH"].km)

    def test_csv_trip_summary(self):
        content = ("Véhicule;Début;Fin;Distance (km);Mission\n"
                   "AB-123-CD;07/10/2026 08:30;07/10/2026 09:10;31,8;M-77\n").encode("cp1252")
        t = pmt_traces.parse_file(content, "courses.csv")[0]
        self.assertEqual((t.km, t.reference, t.start), (31.8, "M-77", START))

    def test_unknown_csv(self):
        with self.assertRaises(ValueError):
            pmt_traces.parse_file(b"a;b\n1;2\n", "x.csv")


class MatchingTests(unittest.TestCase):
    def trip(self, vehicule="AB-123-CD", start=START, km=32.0, ref=""):
        return {"key": f"{vehicule}{start}", "vehicule": vehicule, "start": start.isoformat(), "km": km,
                "reference": ref, "trous": 0}

    def voucher(self, vid, **transport):
        return {"id": vid, "transport": {**TRANSPORT, **transport}}

    def test_vehicle_and_departure_time(self):
        trips = [self.trip(start=START), self.trip(start=START.replace(hour=14))]
        vouchers = [self.voucher("v-matin", vehicule="AB 123 CD", heure_depart="08:25"),
                    self.voucher("v-aprem", vehicule="AB-123-CD", heure_depart="14:05")]
        result = pmt_traces.assign(trips, vouchers)
        self.assertEqual(result["v-matin"][0], trips[0]["key"])
        self.assertEqual(result["v-aprem"][0], trips[1]["key"])

    def test_other_vehicle_or_day_never_matches(self):
        self.assertEqual(pmt_traces.trip_score(self.trip(vehicule="ZZ-999-ZZ"),
                                               self.voucher("v", vehicule="AB-123-CD")), 0)
        self.assertEqual(pmt_traces.trip_score(self.trip(start=START + dt.timedelta(days=1)),
                                               self.voucher("v")), 0)

    def test_ambiguous_day_is_left_to_user(self):
        trips = [self.trip(vehicule="", start=START), self.trip(vehicule="", start=START.replace(hour=15))]
        self.assertEqual(pmt_traces.assign(trips, [self.voucher("v")]), {})

    def test_apply_fills_km_without_manual_entry(self):
        t = pmt_traces.apply_to_transport({"date_transport": "2026-10-07"}, self.trip(km=31.84))
        self.assertEqual((t["km_geoloc"], t["km_aller"], t["vehicule"], t["heure_depart"]),
                         (31.8, 31.8, "AB-123-CD", "08:30"))
        kept = pmt_traces.apply_to_transport({"km_aller": 35}, self.trip(km=31.84))
        self.assertEqual(kept["km_aller"], 35)      # km facturés conservés : le contrôle signalera l'écart

    def test_trace_with_gaps_raises_warning(self):
        transport = {**TRANSPORT, "km_geoloc": 32, "trace": {"trous": 2}}
        codes = {c["code"] for c in pmt.validate_pmt(sample_pmt(), transport, today=dt.date(2026, 10, 9))}
        self.assertIn("TRACE_TROUS", codes)


class TracesApiTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from backend.models.database import Base, get_db
        from backend.routers.pmt import router
        from backend.routers.pmt_auth import get_current_user
        from backend.routers.pmt_traces import router as traces_router
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
        app.include_router(traces_router)
        app.include_router(router)
        app.dependency_overrides[get_db] = override
        self.user = CurrentUser(2, "a@amb-a.fr", "client", "amb-a")
        app.dependency_overrides[get_current_user] = lambda: self.user
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("PMT_SCAN_DIR", None)
        self.tmp.cleanup()

    def test_import_attaches_trace_and_fills_km(self):
        transport = {"date_transport": "2026-10-07", "heure_depart": "08:30", "vehicule": "AB-123-CD",
                     "equipage": "x"}
        v = self.client.post("/pmt/vouchers", json={"data": sample_pmt(), "transport": transport}).json()
        other = self.client.post("/pmt/vouchers", json={
            "data": sample_pmt(), "transport": {**transport, "vehicule": "EF-456-GH"}}).json()
        pts = track_points()
        r = self.client.post("/pmt/traces/import", files={"file": ("export.gpx", gpx([("AB-123-CD", pts)]),
                                                                    "application/gpx+xml")})
        self.assertEqual(r.status_code, 200, r.text)
        summary = r.json()
        self.assertEqual((summary["importees"], summary["rattachees"]), (1, 1))
        self.assertEqual([d["id"] for d in summary["dossiers_sans_trace"]], [other["id"]])

        filled = self.client.get(f"/pmt/vouchers/{v['id']}").json()
        km = round(expected_km(pts), 1)
        self.assertEqual(filled["transport"]["km_geoloc"], km)
        self.assertEqual(filled["transport"]["km_aller"], km)
        self.assertNotIn("KM", {c["code"] for c in filled["checks"]})

        # Réimport : pas de doublon.
        again = self.client.post("/pmt/traces/import", files={"file": ("export.gpx", gpx([("AB-123-CD", pts)]),
                                                                        "application/gpx+xml")}).json()
        self.assertEqual(again["doublons_ignores"], 1)

        # Rattachement manuel au dossier du second véhicule, puis détachement.
        key = self.client.get("/pmt/traces").json()[0]["key"]
        self.client.post(f"/pmt/traces/{key}/attach", json={"voucher_id": other["id"]})
        self.assertIsNone(self.client.get(f"/pmt/vouchers/{v['id']}").json()["transport"].get("trace"))
        self.assertEqual(self.client.get(f"/pmt/vouchers/{other['id']}").json()["transport"]["km_geoloc"], km)
        self.client.post(f"/pmt/traces/{key}/detach")
        self.assertIsNone(self.client.get(f"/pmt/vouchers/{other['id']}").json()["transport"]["km_geoloc"])

    def test_other_company_cannot_see_traces(self):
        self.client.post("/pmt/traces/import", files={"file": ("e.gpx", gpx([("AB-123-CD", track_points())]),
                                                               "application/gpx+xml")})
        key = self.client.get("/pmt/traces").json()[0]["key"]
        from backend.services.pmt_auth import CurrentUser
        self.user = CurrentUser(3, "b@amb-b.fr", "client", "amb-b")
        self.assertEqual(self.client.get("/pmt/traces").json(), [])
        self.assertEqual(self.client.delete(f"/pmt/traces/{key}").status_code, 404)

    def test_bad_file(self):
        r = self.client.post("/pmt/traces/import", files={"file": ("x.gpx", b"<gpx", "application/gpx+xml")})
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
