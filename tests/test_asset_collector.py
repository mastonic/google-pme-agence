import unittest
from unittest.mock import patch

from backend.agents.manager import web_collected_prompt
from backend.services import asset_collector as ac
from backend.services.apify_maps import ApifyMapsService

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 5000


class SocialUrlTests(unittest.TestCase):
    def test_extracts_and_cleans_social_links(self):
        html = ('<a href="https://www.facebook.com/sharer/sharer.php?u=x">x</a>'
                '<a href="https://m.facebook.com/fruityboule/">fb</a>'
                '<a href="https://instagram.com/p/abc">post</a>'
                '<a href="https://www.instagram.com/fruity.boule/">ig</a>')
        self.assertEqual(ac.social_links_from_html(html), {
            "facebook": "https://www.facebook.com/fruityboule",
            "instagram": "https://www.instagram.com/fruity.boule"})

    def test_rejects_non_page_urls(self):
        self.assertEqual(ac.clean_facebook_url("https://facebook.com/"), "")
        self.assertEqual(ac.clean_facebook_url("https://evil.com/facebook.com/x"), "")
        self.assertEqual(ac.instagram_username("https://instagram.com/explore"), "")


class VisionParseTests(unittest.TestCase):
    def test_parses_menu_and_clamps(self):
        out = ac.parse_vision_json('ok {"kind": "menu", "quality": 9, "alt": "Carte", '
                                   '"menu_items": [{"name": "Bubble tea mangue", "price": "5,50 €"}, {"name": ""}]}')
        self.assertEqual(out["kind"], "menu")
        self.assertEqual(out["quality"], 5)
        self.assertEqual(out["menu_items"], [{"name": "Bubble tea mangue", "price": "5,50 €"}])

    def test_unknown_kind_falls_back(self):
        self.assertEqual(ac.parse_vision_json("pas de json")["kind"], "produit")


class CollectTests(unittest.TestCase):
    @patch.object(ac, "_vision_model", return_value=None)
    @patch.object(ac, "download_image", return_value=(JPEG, "image/jpeg"))
    @patch.object(ac, "_apify")
    @patch.object(ac, "find_social_urls", return_value={"facebook": "https://www.facebook.com/fruityboule"})
    def test_collect_dedupes_and_puts_logo_first(self, _f, apify, _d, _v):
        apify.side_effect = [
            [{"profilePictureUrl": "https://scontent.fbcdn.net/logo.jpg", "intro": "Bar à fruits"}],
            [{"image": "https://scontent.fbcdn.net/1.jpg"}],
        ]
        out = ac.collect_assets("Fruity Boule", "Fort-de-France", log=lambda *_: None)
        self.assertEqual(len(out["images"]), 1)  # même contenu → dédoublonné
        self.assertEqual(out["images"][0]["kind"], "logo")
        self.assertEqual(out["info"]["description"], "Bar à fruits")

    def test_sniff_rejects_html(self):
        self.assertIsNone(ac.sniff(b"<html>"))


class IntegrationTests(unittest.TestCase):
    def test_apify_maps_keeps_photos(self):
        out = ApifyMapsService._normalize({"title": "Fruity Boule", "imageUrls": ["https://lh3.googleusercontent.com/a"],
                                           "categoryName": "Bar à jus"})
        self.assertEqual(out["photos"], ["https://lh3.googleusercontent.com/a"])
        self.assertEqual(out["types"], ["Bar à jus"])

    def test_prompt_block_lists_menu(self):
        block = web_collected_prompt({"client_profile": {"web_collected": {
            "menu": [{"name": "Smoothie", "price": "4 €"}], "social": {"facebook": "https://www.facebook.com/x"}}}})
        self.assertIn("Smoothie — 4 €", block)
        self.assertIn("facebook https://www.facebook.com/x", block)
        self.assertEqual(web_collected_prompt({}), "")


if __name__ == "__main__":
    unittest.main()


class StoreTests(unittest.TestCase):
    def test_store_respects_client_logo_and_replaces_old_web_media(self):
        import tempfile, os
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.models.database import Base, Business, ClientMedia
        from backend.client_space_api import store_collected_assets
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        engine = create_engine(f"sqlite:///{os.path.join(tmp.name, 'db.sqlite')}")
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        b = Business(id="b1", name="Fruity Boule", client_profile={})
        db.add(b)
        db.add(ClientMedia(id="m0", business_id="b1", kind="logo", name="mon-logo.png",
                           mime="image/png", size=4, data=b"\x89PNG"))
        db.commit()
        result = {"images": [{"data": JPEG, "mime": "image/jpeg", "kind": "logo", "source": "facebook"},
                             {"data": JPEG, "mime": "image/jpeg", "kind": "menu", "source": "facebook"}],
                  "menu": [{"name": "Smoothie", "price": "4 €"}], "social": {"facebook": "https://www.facebook.com/x"},
                  "collected_at": "2026-11-08T00:00:00Z"}
        self.assertEqual(store_collected_assets(db, b, result), {"realisation": 1})
        store_collected_assets(db, b, result)  # relance : pas de doublon
        db.commit()
        rows = db.query(ClientMedia).filter_by(business_id="b1").all()
        self.assertEqual(sorted(r.name for r in rows), ["mon-logo.png", "web-facebook-menu-2.jpg"])
        self.assertEqual(b.client_profile["social"]["facebook"], "https://www.facebook.com/x")
        self.assertEqual(len(b.client_profile["media"]["photos"]), 1)
