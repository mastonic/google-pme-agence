"""Génération du site : contenus du client prioritaires, avis Google réels, pas de vidéo publiée."""
import unittest
from unittest.mock import patch

from backend.agents.manager import LocalPulseManager, client_assets, enforce_client_logo, enforce_client_photos

CLIENT = "https://pp.test/client/media/"
PROFILE = {
    "identity": {"business_name": "Hôtel de la Gare", "logo_url": CLIENT + "logo"},
    "contact": {"phone": "01 30 45 67 89", "whatsapp": "06 12 34 56 78", "address": "1 place de la Gare"},
    "activity": {
        "description": "Hôtel familial de 24 chambres.",
        "services": ["Chambres familiales", "Parking gratuit"],
        "hours": [{"day": "lundi", "closed": False, "open": "07:00", "close": "22:00"},
                  {"day": "dimanche", "closed": True, "open": "", "close": ""}],
    },
    "social": {"instagram": "https://instagram.com/hotel", "facebook": ""},
    "media": {
        "photos": [{"url": CLIENT + "equipe", "kind": "equipe"},
                   {"url": CLIENT + "chambre", "kind": "realisation"},
                   {"url": CLIENT + "facade", "kind": "devanture"}],
        "videos": [{"url": "https://pp.test/visite.mp4"}],
    },
}


def manager(**extra):
    m = LocalPulseManager.__new__(LocalPulseManager)
    m.business_data = {"name": "HOTEL", "business_id": "h1", "photos": [], "reviews": [], **extra}
    m.sector = "lodging"
    m._push_log = lambda *a, **k: None
    return m


class ClientAssetsTests(unittest.TestCase):
    def test_client_photos_first_facade_then_work_then_team(self):
        assets = client_assets({"client_profile": PROFILE})
        self.assertEqual(assets["photos"], [CLIENT + "facade", CLIENT + "chambre", CLIENT + "equipe"])
        self.assertEqual(assets["videos"], ["https://pp.test/visite.mp4"])
        self.assertEqual(assets["logo"], CLIENT + "logo")
        self.assertEqual(assets["info"]["services"], ["Chambres familiales", "Parking gratuit"])
        self.assertEqual(assets["info"]["social"], {"instagram": "https://instagram.com/hotel"})

    def test_no_profile_gives_nothing(self):
        self.assertEqual(client_assets({}), {"photos": [], "videos": [], "logo": "", "info": {}})

    def test_client_block_lists_client_data(self):
        block = manager(client_profile=PROFILE)._client_prompt_block()
        for expected in ("PRIORITAIRES", "Hôtel familial de 24 chambres.", "Chambres familiales · Parking gratuit",
                         "dimanche : fermé", "lundi : 07:00–22:00", "instagram https://instagram.com/hotel",
                         CLIENT + "logo", "https://pp.test/visite.mp4", "3 premières photos"):
            self.assertIn(expected, block)
        self.assertEqual(manager()._client_prompt_block(), "")


class ReviewsBlockTests(unittest.TestCase):
    def test_only_real_positive_reviews(self):
        m = manager(reviews=[
            {"author": "Marie Dupont", "rating": 5, "text": "Accueil parfait, chambre très propre."},
            {"author": "Paul", "rating": 2, "text": "Bruyant."},
            {"author": "Léa", "rating": 5, "text": "  "},
        ])
        block = m._reviews_prompt_block()
        self.assertIn('Marie (5★) : "Accueil parfait, chambre très propre."', block)
        self.assertNotIn("Bruyant", block)
        self.assertNotIn("Léa", block)

    def test_no_review_means_no_invented_testimonial(self):
        self.assertIn("n'invente AUCUN témoignage", manager()._reviews_prompt_block())


class PhotoPriorityTests(unittest.TestCase):
    def test_build_uses_client_then_google_photos_and_skips_paid_ai(self):
        m = manager(client_profile=PROFILE, photos=["https://maps.googleapis.com/g1"],
                    reviews=[{"photos": [{"url": "https://review.test/r1"}]}])
        captured = {}

        def fake_html(prep, all_photos=None):
            captured["photos"] = all_photos
            raise StopIteration  # on s'arrête une fois la liste construite

        with patch.dict("os.environ", {"FAL_KEY": "x", "PEXELS_API_KEY": "y"}), \
                patch.object(LocalPulseManager, "_generate_images_fal", side_effect=AssertionError("IA payante")), \
                patch.object(LocalPulseManager, "_generate_images_pexels", side_effect=AssertionError("Pexels")), \
                patch.object(LocalPulseManager, "_generate_html_streaming", side_effect=fake_html):
            with self.assertRaises(StopIteration):
                m.run_build_crew({})
        self.assertEqual(captured["photos"][:5], [CLIENT + "facade", CLIENT + "chambre", CLIENT + "equipe",
                                                  "https://maps.googleapis.com/g1", "https://review.test/r1"])


class EnforcementTests(unittest.TestCase):
    """Le modèle peut ignorer la liste : les photos et le logo du client sont imposés après coup."""

    HTML = ('<html><head></head><body><nav><a>Hôtel</a></nav>'
            '<section style="background:url(\'https://images.unsplash.com/hero.jpg\')"></section>'
            '<img src="https://images.pexels.com/a.jpg" alt="a"><img src="https://x.test/icon-star.svg">'
            '<img src="https://images.unsplash.com/b.jpg"></body></html>')

    def test_missing_client_photos_replace_first_images_in_order(self):
        out, n = enforce_client_photos(self.HTML, [CLIENT + "facade", CLIENT + "chambre"])
        self.assertEqual(n, 2)
        self.assertIn(f"url('{CLIENT}facade')", out)          # hero en fond CSS
        self.assertIn(f'src="{CLIENT}chambre"', out)
        self.assertIn("icon-star.svg", out)                   # icônes intactes
        self.assertIn("unsplash.com/b.jpg", out)               # au-delà : inchangé

    def test_photos_already_used_are_not_duplicated(self):
        html = self.HTML.replace("https://images.pexels.com/a.jpg", CLIENT + "facade")
        out, n = enforce_client_photos(html, [CLIENT + "facade"])
        self.assertEqual((n, out), (0, html))

    def test_no_client_photo_leaves_html_untouched(self):
        self.assertEqual(enforce_client_photos(self.HTML, []), (self.HTML, 0))

    def test_logo_added_in_nav_once(self):
        out = enforce_client_logo(self.HTML, CLIENT + "logo", "Hôtel")
        self.assertIn(f'<nav><img src="{CLIENT}logo" alt="Hôtel"', out)
        self.assertEqual(enforce_client_logo(out, CLIENT + "logo"), out)

    def test_generation_uses_client_contacts_and_places_photos(self):
        m = manager(client_profile=PROFILE, address=None, phone="01 00 00 00 00")
        m.sector_profile = {"label": "Hôtel", "sections": ["hero"], "special_instructions": "",
                            "cta_primary": "Réserver", "cta_secondary": "Voir"}
        m.site_design = {"label": "Hôtel"}
        m.design_brief = {}
        m._disabled_providers = set()
        captured = {}

        def fake_stream(self, provider, prompt, system):
            captured["prompt"] = prompt
            yield "<!DOCTYPE html><html><body><nav></nav><img src='https://images.unsplash.com/x.jpg'></body></html>"

        with patch.object(LocalPulseManager, "_stream_provider", fake_stream), \
                patch("backend.agents.manager.build_design_prompt_directive", return_value=""):
            html = m._generate_html_streaming({}, all_photos=[CLIENT + "facade"])
        self.assertIn("Tél : 01 30 45 67 89", captured["prompt"])      # téléphone du client, pas Google
        self.assertIn("wa.me/+33612345678", captured["prompt"])          # WhatsApp du client
        self.assertIn(CLIENT + "facade", html)
        self.assertIn(f'src="{CLIENT}logo" alt="Hôtel de la Gare"', html)


class DeployWithoutVideoTests(unittest.TestCase):
    def test_site_is_published_without_presentation_video(self):
        m = manager()
        m.sector_profile = {"label": "Hôtel"}
        m.business_id = "h1"
        sent = {}

        class FakeTool:
            def _run(self, html, name, extra_files=None):
                sent.update(html=html, files=extra_files)
                return "https://hotel.vercel.app"

        with patch("backend.agents.tools.VercelDeployTool", FakeTool):
            m.run_deploy_crew("<html><head></head><body><p>site</p></body></html>")
        self.assertNotIn("presentation.mp4", sent["files"])
        self.assertNotIn("<video", sent["html"])


if __name__ == "__main__":
    unittest.main()
