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
        for key in ("title", "subtitle", "line", "name", "cta", "website"):
            if s.get(key):
                parts.append(str(s[key]))
        parts.extend(s.get("bullets", []))
        parts.extend(s.get("words", []))
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
                         ["hook", "fiche", "avant", "apres", "avantages", "packs", "cta"])

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


class FontTests(unittest.TestCase):
    def test_bundled_font_renders_accents(self):
        from backend.services.motion_video import _font
        from PIL import Image, ImageDraw
        font = _font(40, True)
        def ink(text):
            img = Image.new("L", (600, 80), 0)
            ImageDraw.Draw(img).text((10, 10), text, font=font, fill=255)
            return img.getbbox()
        # un caractère accentué doit dessiner plus que sa base seule
        self.assertGreater(ink("é")[2] - ink("é")[0], 5)
        self.assertNotEqual(ink("été"), ink("ete"))
        self.assertTrue(hasattr(font, "path"), "police chargée depuis un fichier, pas la police de secours")


class VoiceoverScriptTests(unittest.TestCase):
    def test_one_line_per_scene_from_real_facts(self):
        from backend.services.voiceover import build_script
        lines = build_script(build_storyboard(BIZ, "Artisan", CATALOG))
        self.assertEqual([l["scene"] for l in lines],
                         ["hook", "fiche", "avant", "apres", "avantages", "packs", "cta"])
        text = " ".join(l["text"] for l in lines)
        self.assertIn("Marc, voici ce que nous avons préparé pour Plomberie Dupont.", text)
        self.assertIn("4,7 sur 5, avec 52 avis", text)
        self.assertIn("Sans site web", text)
        self.assertIn("à partir de 49 euros", text)

    def test_no_rating_is_invented(self):
        from backend.services.voiceover import build_script
        biz = dict(BIZ, rating=0, user_ratings_total=0, owner_first_name="")
        text = " ".join(l["text"] for l in build_script(build_storyboard(biz, "Artisan", CATALOG)))
        self.assertNotIn("sur 5", text)
        self.assertTrue(text.startswith("Voici ce que nous avons préparé"))

    def test_retime_fits_voice_and_stays_contiguous(self):
        from backend.services.voiceover import VOICE_LEAD, VOICE_TAIL, retime, voice_cues
        scenes = build_storyboard(BIZ, "Artisan", CATALOG)
        timed = retime(scenes, {"avant": 9.0, "cta": 1.0})
        self.assertEqual(timed[0]["start"], 0)
        for prev, nxt in zip(timed, timed[1:]):
            self.assertAlmostEqual(prev["start"] + prev["duration"], nxt["start"], places=2)
        avant = next(s for s in timed if s["id"] == "avant")
        self.assertGreaterEqual(avant["duration"], VOICE_LEAD + 9.0 + VOICE_TAIL - 0.01)
        self.assertEqual(next(s for s in timed if s["id"] == "cta")["duration"], 4.0)  # minimum visuel
        self.assertAlmostEqual(voice_cues(timed)["avant"], avant["start"] + VOICE_LEAD)


class GoogleTtsTests(unittest.TestCase):
    def _response(self, audio=b"ID3fake"):
        import base64
        from unittest.mock import MagicMock
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"audioContent": base64.b64encode(audio).decode()}
        return resp

    def test_synthesize_uses_french_female_voice_and_bearer_token(self):
        from unittest.mock import patch
        from backend.services.voiceover import DEFAULT_VOICE, synthesize
        with patch("requests.post", return_value=self._response()) as post:
            self.assertEqual(synthesize("Bonjour.", token="tok"), b"ID3fake")
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["json"]["voice"], {"languageCode": "fr-FR", "name": DEFAULT_VOICE})
        self.assertEqual(kwargs["json"]["audioConfig"]["audioEncoding"], "MP3")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer tok")
        self.assertEqual(kwargs["params"], {})

    def test_synthesize_with_api_key(self):
        from unittest.mock import patch
        from backend.services.voiceover import synthesize
        with patch("requests.post", return_value=self._response()) as post:
            synthesize("Bonjour.", api_key="k")
        self.assertEqual(post.call_args.kwargs["params"], {"key": "k"})
        self.assertNotIn("Authorization", post.call_args.kwargs["headers"])

    def test_api_error_is_raised_for_silent_fallback(self):
        from unittest.mock import MagicMock, patch
        from backend.services.voiceover import synthesize
        with patch("requests.post", return_value=MagicMock(status_code=403, text="API disabled")):
            with self.assertRaisesRegex(RuntimeError, "403"):
                synthesize("Bonjour.", token="tok")


class SoundtrackTests(unittest.TestCase):
    def test_music_bed_is_valid_wav_of_requested_length(self):
        import io, wave
        from backend.services.soundtrack import music_bed
        with wave.open(io.BytesIO(music_bed(3.0, [1.5], sample_rate=8000))) as w:
            self.assertEqual(w.getframerate(), 8000)
            self.assertAlmostEqual(w.getnframes() / 8000, 3.0, places=2)

    def test_presentation_has_audio_with_fake_voice(self):
        import os, subprocess, imageio_ffmpeg
        from backend.services.motion_video import render_presentation
        from backend.services.voiceover import audio_duration, retime, voice_cues

        def fake_voice(scenes, workdir):
            path = os.path.join(workdir, "vo.mp3")
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "lavfi",
                            "-i", "sine=frequency=440:duration=1", "-ac", "1", path], check=True)
            timed = retime(scenes, {"hook": audio_duration(path)})
            return timed, [(voice_cues(timed)["hook"], path)]

        scenes = build_storyboard(BIZ, "Artisan", CATALOG)
        data, seconds = render_presentation(scenes, None, width=320, height=180, fps=4, _voiceover=fake_voice)
        self.assertEqual(data[4:8], b"ftyp")
        self.assertGreaterEqual(seconds, 30)
        tmp = "/tmp/_pres_test.mp4"
        open(tmp, "wb").write(data)
        info = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", tmp], capture_output=True, text=True).stderr
        self.assertIn("Audio: aac", info)

    def test_voice_failure_still_gives_video(self):
        from backend.services.motion_video import render_presentation
        def broken(scenes, workdir):
            raise RuntimeError("quota")
        logs = []
        data, _ = render_presentation(build_storyboard(BIZ, "Artisan", CATALOG), None, log=logs.append,
                                      width=320, height=180, fps=4, _voiceover=broken)
        self.assertEqual(data[4:8], b"ftyp")
        self.assertTrue(any("quota" in m for m in logs))

    def test_inject_shows_real_duration(self):
        self.assertIn("Présentation en 37 secondes", inject_video_block("<p>x</p>", seconds=36.7))


if __name__ == "__main__":
    unittest.main()
