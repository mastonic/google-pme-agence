import base64
import unittest

from backend.services.vercel_files import vercel_file
from backend.services.motion_video import build_storyboard, inject_video_block, render_video

BIZ = {
    "name": "Plomberie Dupont",
    "address": "12 rue X, 97200 Fort-de-France",
    "rating": 4.7,
    "user_ratings_total": 52,
    "website": "",
    "photos": [],
    "owner_first_name": "Marc",
}
CATALOG = [
    {"name": "Starter", "price": 49, "positioning": "Présence professionnelle"},
    {"name": "Pro", "price": 149, "positioning": "Visibilité"},
    {"name": "Elite", "price": 299, "positioning": "Croissance"},
]


def _all_text(scenes):
    parts = []
    for s in scenes:
        for key in ("title", "subtitle", "caption", "name", "cta", "website"):
            if s.get(key):
                parts.append(str(s[key]))
        parts.extend(s.get("bullets", []))
        parts.extend(f"{p['name']} {p['price']}" for p in s.get("packs", []))
    return " ".join(parts)


class StoryboardTests(unittest.TestCase):
    def test_total_duration_is_44_seconds_and_contiguous(self):
        scenes = build_storyboard(BIZ, "Artisan", CATALOG, "Demander un devis")
        self.assertEqual(scenes[0]["start"], 0)
        for prev, nxt in zip(scenes, scenes[1:]):
            self.assertEqual(prev["start"] + prev["duration"], nxt["start"])
        self.assertEqual(scenes[-1]["start"] + scenes[-1]["duration"], 44)
        self.assertEqual([s["id"] for s in scenes],
                         ["intro", "fiche", "avant", "apres", "avantages", "packs"])

    def test_only_real_facts_are_shown(self):
        text = _all_text(build_storyboard(BIZ, "Artisan", CATALOG))
        self.assertIn("52 avis", text)  # l'avis est affiché via la scène fiche (champ reviews)
        self.assertIn("Aucun site web", text)  # pas de site renseigné
        self.assertNotIn("garanti", text.lower())

    def test_existing_website_changes_the_before_message(self):
        scenes = build_storyboard(dict(BIZ, website="https://dupont.fr"), "Artisan", CATALOG)
        text = _all_text(scenes)
        self.assertNotIn("Aucun site web", text)
        self.assertIn("Un site existant", text)

    def test_packs_come_from_catalog(self):
        scenes = build_storyboard(BIZ, "Artisan", CATALOG)
        packs = next(s for s in scenes if s["id"] == "packs")["packs"]
        self.assertEqual([(p["name"], p["price"]) for p in packs],
                         [("Starter", 49), ("Pro", 149), ("Elite", 299)])


class RenderTests(unittest.TestCase):
    def test_renders_real_mp4_without_photo(self):
        scenes = build_storyboard(BIZ, "Artisan", CATALOG)
        data = render_video(scenes, None, width=320, height=180, fps=4)
        self.assertGreater(len(data), 1000)
        self.assertEqual(data[4:8], b"ftyp")  # conteneur MP4

    def test_inject_video_block_before_body_end(self):
        out = inject_video_block("<html><body>x</body></html>")
        self.assertIn('<video controls playsinline preload="metadata" src="presentation.mp4"', out)
        self.assertTrue(out.index("<video") < out.index("</body>"))

    def test_inject_video_block_without_body(self):
        self.assertIn("presentation.mp4", inject_video_block("<p>x</p>"))


class VercelFileTests(unittest.TestCase):
    def test_binary_is_sent_base64(self):
        entry = vercel_file("presentation.mp4", b"\x00\x01abc")
        self.assertEqual(entry["encoding"], "base64")
        self.assertEqual(base64.b64decode(entry["data"]), b"\x00\x01abc")

    def test_text_is_sent_as_is(self):
        self.assertEqual(vercel_file("robots.txt", "User-agent: *"),
                         {"file": "robots.txt", "data": "User-agent: *"})


if __name__ == "__main__":
    unittest.main()
