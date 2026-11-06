import os
import subprocess
import unittest

from backend.services import showreel as S
from backend.services.voiceover import audio_duration, build_script, retime, voice_cues

CATALOG = [{"name": "Starter", "price": 49}, {"name": "Pro", "price": 149}, {"name": "Elite", "price": 299}]
PLOMBIER = {"name": "Plomberie Martin", "address": "8 rue de la Gare, 78190 Trappes", "rating": 4.8,
            "user_ratings_total": 63, "website": "", "photos": [], "owner_first_name": "Karim"}
SITE = "<html><body style='margin:0'><h1 style='background:#0b2440;color:#fff;padding:80px'>Plomberie Martin</h1>" \
       + "<p style='height:1500px'>Prestations</p></body></html>"


class BuildShowreelTests(unittest.TestCase):
    def test_facts_only_from_business(self):
        d = S.build_showreel(PLOMBIER, "artisan", CATALOG, new_url="https://plomberie-martin.vercel.app/")
        self.assertEqual(d["city"], "Trappes")
        self.assertEqual(d["new_url"], "plomberie-martin.vercel.app")
        self.assertEqual(d["accent"], "#3DA9FC")
        self.assertIn("63 avis Google à mettre en avant", d["problems"])
        self.assertIn("Aucun site web", d["problems"])
        self.assertLessEqual(len(d["problems"]), 4)
        self.assertEqual(d["min_price"], 49)
        self.assertEqual([s["id"] for s in d["scenes"]],
                         ["avant", "cout", "refonte", "apres", "parcours", "comparatif", "pourquoi", "cta"])
        for prev, nxt in zip(d["scenes"], d["scenes"][1:]):
            self.assertAlmostEqual(prev["start"] + prev["duration"], nxt["start"], places=2)

    def test_no_reviews_no_rating_claim(self):
        d = S.build_showreel(dict(PLOMBIER, user_ratings_total=0, rating=0), "artisan", CATALOG)
        self.assertFalse(any("avis" in p for p in d["problems"]))
        self.assertNotIn("avis", " ".join(l["text"] for l in build_script(d["scenes"])))

    def test_http_site_flagged_and_flow_by_sector(self):
        d = S.build_showreel(dict(PLOMBIER, website="http://garage-leroy.fr/"), "automotive", CATALOG)
        self.assertEqual(d["website_label"], "garage-leroy.fr")
        self.assertFalse(d["secure"])
        self.assertIn("« Site non sécurisé » (http)", d["problems"])
        self.assertEqual(d["flow"][0][1], "Rendez-vous")
        self.assertEqual(S.build_showreel(PLOMBIER, "beauty", CATALOG)["flow"], S.FLOWS["generic"]["steps"])

    def test_voice_script_for_each_scene(self):
        d = S.build_showreel(PLOMBIER, "artisan", CATALOG, brand="HoldMasto")
        lines = {l["scene"]: l["text"] for l in build_script(d["scenes"])}
        self.assertEqual(len(lines), 8)
        self.assertEqual(lines["avant"], "Karim, aujourd'hui, Plomberie Martin n'a pas encore de site web.")
        self.assertIn("vos 63 avis", lines["cout"])
        self.assertIn("urgence", lines["parcours"])
        self.assertIn("HoldMasto", lines["pourquoi"])
        self.assertIn("49 euros", lines["cta"])

    def test_retime_keeps_animation_minimum(self):
        d = S.build_showreel(PLOMBIER, "artisan", CATALOG)
        timed = retime(d["scenes"], {"refonte": 1.0, "cout": 7.0})
        self.assertEqual(next(s for s in timed if s["id"] == "refonte")["duration"], 3.0)
        self.assertGreater(next(s for s in timed if s["id"] == "cout")["duration"], 7.0)


def _chromium_ok():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            pw.chromium.launch().close()
        return True
    except Exception:
        return False


@unittest.skipUnless(_chromium_ok(), "Chromium (Playwright) indisponible")
class RenderShowreelTests(unittest.TestCase):
    def test_render_with_voice_and_music(self):
        import imageio_ffmpeg

        def fake_voice(scenes, workdir):
            path = os.path.join(workdir, "vo.mp3")
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi",
                            "-i", "sine=frequency=440:duration=1", "-ac", "1", path], check=True)
            timed = retime(scenes, {"avant": audio_duration(path)})
            return timed, [(voice_cues(timed)["avant"], path)]

        d = S.build_showreel(PLOMBIER, "artisan", CATALOG)
        data, seconds = S.render_showreel(d, SITE, width=480, height=270, fps=2, _voiceover=fake_voice)
        self.assertEqual(data[4:8], b"ftyp")
        self.assertAlmostEqual(seconds, 34.6, places=1)
        tmp = "/tmp/_showreel_test.mp4"
        with open(tmp, "wb") as fh:
            fh.write(data)
        info = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", tmp], capture_output=True, text=True).stderr
        self.assertIn("Audio: aac", info)
        self.assertIn("480x270", info)


if __name__ == "__main__":
    unittest.main()
