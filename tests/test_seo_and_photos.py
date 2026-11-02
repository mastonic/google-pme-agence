import datetime
import html
import json
import os
import re
import unittest
from unittest.mock import patch

from backend.services.artisan_discovery import (
    ARTISAN_TRADES,
    bbox_from_radius,
    haversine_m,
    select_trades,
)
from backend.services.artisan_scan import discover_artisans, to_scan_place
from backend.services.photo_proxy import (
    build_places_photo_url,
    strip_api_key,
    upstream_headers,
    validate_photo_url,
)
from backend.services.seo_head import (
    build_llms_txt,
    build_robots_txt,
    build_sitemap_xml,
    inject_seo_head,
    schema_type_for,
    vercel_project_slug,
)

PHOTO_NAME = "places/ChIJabc/photos/AelY123"
BIZ = {
    "name": 'Plomberie "Dupont" & Fils',
    "address": "12 rue de la Liberté, 97200 Fort-de-France",
    "phone": "0596 00 00 00",
    "rating": 4.7,
    "user_ratings_total": 52,
    "types": ["plumber", "point_of_interest"],
    "business_id": "ChIJabc",
    "latitude": 14.6,
    "longitude": -61.07,
}


class PhotoProxyTests(unittest.TestCase):
    def test_places_media_path_is_allowed(self):
        url = f"https://places.googleapis.com/v1/{PHOTO_NAME}/media?maxHeightPx=800"
        self.assertEqual(validate_photo_url(url), (True, "ok"))

    def test_substring_host_trick_is_rejected(self):
        ok, _ = validate_photo_url("https://attaquant.exemple/?places.googleapis.com")
        self.assertFalse(ok)
        ok, _ = validate_photo_url("https://places.googleapis.com.attaquant.exemple/v1/x")
        self.assertFalse(ok)

    def test_http_and_non_media_paths_are_rejected(self):
        self.assertFalse(validate_photo_url(f"http://places.googleapis.com/v1/{PHOTO_NAME}/media")[0])
        self.assertFalse(validate_photo_url("https://places.googleapis.com/v1/places/x")[0])
        self.assertFalse(validate_photo_url("file:///etc/passwd")[0])

    def test_static_hosts_allowed(self):
        self.assertTrue(validate_photo_url("https://images.unsplash.com/photo-1")[0])
        self.assertTrue(validate_photo_url("https://v3.fal.media/files/a.png")[0])

    def test_built_url_never_contains_the_key(self):
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "SECRET-KEY"}):
            built = build_places_photo_url(PHOTO_NAME)
        self.assertNotIn("SECRET-KEY", built)
        self.assertNotIn("key=", built)
        self.assertTrue(built.startswith("/photo?url="))

    def test_key_is_sent_only_to_places_as_header(self):
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "SECRET-KEY"}):
            self.assertEqual(upstream_headers(f"https://places.googleapis.com/v1/{PHOTO_NAME}/media"),
                             {"X-Goog-Api-Key": "SECRET-KEY"})
            self.assertEqual(upstream_headers("https://images.unsplash.com/x"), {})

    def test_legacy_key_parameter_is_stripped(self):
        legacy = f"https://places.googleapis.com/v1/{PHOTO_NAME}/media?maxHeightPx=800&key=OLD&maxWidthPx=1200"
        cleaned = strip_api_key(legacy)
        self.assertNotIn("key=", cleaned)
        self.assertIn("maxHeightPx=800", cleaned)
        self.assertIn("maxWidthPx=1200", cleaned)


class SeoHeadTests(unittest.TestCase):
    def test_title_and_description_replaced_not_duplicated(self):
        page = ("<!doctype html><html><head><title>Ancien</title>"
                '<meta name="description" content="vieux"></head><body>x</body></html>')
        out = inject_seo_head(page, BIZ, "Artisan")
        self.assertEqual(len(re.findall(r"<title>", out)), 1)
        self.assertNotIn("Ancien", out)
        self.assertNotIn('content="vieux"', out)
        self.assertIn('<html lang="fr"', out)

    def test_head_is_created_when_missing(self):
        out = inject_seo_head("<html><body>Hi</body></html>", BIZ, "Artisan")
        self.assertIn("<head>", out)
        self.assertIn("<title>", out)
        self.assertIn('name="viewport"', out)

    def test_json_ld_uses_artisan_subtype_and_real_data_only(self):
        out = inject_seo_head("<html><head></head></html>", BIZ, "Artisan")
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', out, re.S)
        self.assertIsNotNone(match)
        data = json.loads(match.group(1))
        self.assertEqual(data["@type"], "Plumber")
        self.assertEqual(data["telephone"], "0596 00 00 00")
        self.assertEqual(data["geo"]["latitude"], 14.6)
        self.assertNotIn("aggregateRating", data)  # jamais de note inventée

    def test_quotes_and_script_closing_are_escaped(self):
        evil = dict(BIZ, name='</script><img src=x onerror=1>"')
        out = inject_seo_head("<html><head></head></html>", evil, "Artisan")
        self.assertNotIn("</script><img", out)
        self.assertNotIn('"><img', out)

    def test_description_is_bounded(self):
        long_biz = dict(BIZ, address="x" * 400)
        out = inject_seo_head("<html><head></head></html>", long_biz, "Artisan")
        desc = html.unescape(re.search(r'name="description" content="([^"]*)"', out).group(1))
        self.assertLessEqual(len(desc), 160)

    def test_schema_type_fallback(self):
        self.assertEqual(schema_type_for(["restaurant"]), "Restaurant")
        self.assertEqual(schema_type_for(["unknown"]), "LocalBusiness")
        self.assertEqual(schema_type_for([]), "LocalBusiness")

    def test_robots_sitemap_and_llms(self):
        self.assertIn("Sitemap: https://x.vercel.app/sitemap.xml", build_robots_txt("https://x.vercel.app/sitemap.xml"))
        sitemap = build_sitemap_xml("https://x.vercel.app/", datetime.date(2026, 1, 2))
        self.assertIn("<loc>https://x.vercel.app/</loc>", sitemap)
        self.assertIn("<lastmod>2026-01-02</lastmod>", sitemap)
        llms = build_llms_txt(BIZ, "Artisan")
        self.assertTrue(llms.startswith("# Plomberie"))
        self.assertIn("0596 00 00 00", llms)
        self.assertIn("52 avis", llms)

    def test_vercel_slug_matches_expected_normalisation(self):
        self.assertEqual(vercel_project_slug("Plomberie Dupont & Fils"), "plomberie-dupont-fils")
        self.assertEqual(vercel_project_slug(""), "local-pulse-site")


class TradeSelectionTests(unittest.TestCase):
    def test_empty_query_selects_all_trades(self):
        self.assertEqual(len(select_trades("")), len(ARTISAN_TRADES))
        self.assertEqual(len(select_trades(None)), len(ARTISAN_TRADES))

    def test_keyword_filters_trades(self):
        slugs = [t["slug"] for t in select_trades("plomb")]
        self.assertEqual(slugs, ["plomberie"])

    def test_unknown_keyword_falls_back_to_all(self):
        self.assertEqual(len(select_trades("zzzz")), len(ARTISAN_TRADES))


class GeometryTests(unittest.TestCase):
    def test_bbox_contains_circle(self):
        s, w, n, e = bbox_from_radius(14.6, -61.07, 1000)
        self.assertLess(s, 14.6)
        self.assertGreater(n, 14.6)
        self.assertLess(w, -61.07)
        self.assertGreater(e, -61.07)

    def test_haversine_known_distance(self):
        # 0,01° de latitude ≈ 1,11 km
        self.assertAlmostEqual(haversine_m(14.6, -61.0, 14.61, -61.0), 1112, delta=10)


class ScanAdapterTests(unittest.TestCase):
    def test_to_scan_place_maps_places_fields(self):
        entry = {
            "trades": ["plomberie"],
            "place": {
                "id": "P1", "displayName": {"text": "Dupont"}, "formattedAddress": "Adr",
                "location": {"latitude": 14.6, "longitude": -61.0},
                "rating": 4.5, "userRatingCount": 12, "types": ["plumber"],
            },
        }
        mapped = to_scan_place(entry)
        self.assertEqual(mapped["place_id"], "P1")
        self.assertEqual(mapped["name"], "Dupont")
        self.assertEqual(mapped["vicinity"], "Adr")
        self.assertEqual(mapped["geometry"]["location"], {"lat": 14.6, "lng": -61.0})
        self.assertEqual(mapped["user_ratings_total"], 12)
        self.assertEqual(mapped["trades"], ["plomberie"])

    def test_discover_artisans_filters_outside_radius(self):
        pages = {
            "in": {"id": "in", "displayName": {"text": "Proche"},
                   "location": {"latitude": 14.6001, "longitude": -61.0}},
            "out": {"id": "out", "displayName": {"text": "Loin"},
                    "location": {"latitude": 14.7, "longitude": -61.0}},
        }

        def fake_transport(body):
            # Chaque requête renvoie les deux lieux ; le filtre de rayon doit n'en garder qu'un.
            return {"places": list(pages.values())}

        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "K"}), \
             patch("backend.services.artisan_scan.make_places_transport", return_value=fake_transport):
            results = discover_artisans(14.6, -61.0, 500, query="plomb")
        self.assertEqual([r["place_id"] for r in results], ["in"])
        self.assertEqual(results[0]["trades"], ["plomberie"])

    def test_discover_artisans_requires_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                discover_artisans(14.6, -61.0, 500)


if __name__ == "__main__":
    unittest.main()
