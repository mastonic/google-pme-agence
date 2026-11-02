"""Showreel de motion design (44 s, ou calé sur la voix off) envoyé avec la démo.

Étape « Motion Director » du pipeline : une vidéo dynamique qui accroche dès la première
seconde, enchaîne typographie animée, transitions, compteurs et une présentation des
formules, puis finit sur un appel à l'action.

Rendu local (Pillow + ffmpeg embarqué), sans API vidéo payante. Voix off ElevenLabs
(voiceover.py, facultative) et musique générée avec ducking (soundtrack.py).

Règle : seuls les faits fournis (fiche Google, catalogue de formules) sont affichés.
Aucune réalisation, client, récompense ni note inventés : le showreel montre le style et
le rythme, il ne prétend pas à des preuves que nous n'avons pas.
"""
import io
import math
import os
import random
import tempfile
import urllib.parse

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from backend.services.photo_proxy import upstream_headers, validate_photo_url

WIDTH, HEIGHT, FPS = 1280, 720, 24
TRANSITION = 0.6  # secondes de fondu entre deux scènes
BG_TOP, BG_BOTTOM = (6, 12, 26), (14, 30, 62)
BLUE, AMBER, WHITE, MUTED = (59, 130, 246), (245, 158, 11), (255, 255, 255), (148, 163, 184)
CARD = (22, 36, 62)
OK_GREEN, ALERT_RED = (52, 211, 153), (239, 68, 68)

_font_cache: dict = {}


FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")


def _font(size: int, bold: bool = False):
    """DejaVu embarquée dans le dépôt : accents garantis, même sans polices système (Cloud Run)."""
    key = (size, bold)
    if key not in _font_cache:
        path = os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# ─────────────────────────────────────────────────────────────────────────────
#  Storyboard : contenu uniquement à partir des faits fournis
# ─────────────────────────────────────────────────────────────────────────────

def build_storyboard(biz: dict, sector_label: str, catalog: list[dict], cta: str = "Demander un devis") -> list[dict]:
    """Sept scènes, 44 s au total."""
    name = biz.get("name") or "votre commerce"
    first = (biz.get("owner_first_name") or "").strip()
    address = biz.get("address") or ""
    website = (biz.get("website") or "").strip()
    rating = float(biz.get("rating") or 0)
    reviews = int(biz.get("user_ratings_total") or 0)
    photos = len(biz.get("photos") or [])

    before = ["Aucun site web pour répondre aux recherches." if not website
              else "Un site existant qui peut être mieux mis en valeur."]
    before.append("Vos clients vous cherchent sur Google : votre vitrine doit répondre.")
    if reviews:
        before.append(f"Vos {reviews} avis Google méritent d'être mis en avant.")

    advantages = [
        "Visible quand on vous cherche sur Google",
        "Demandes de devis par téléphone et WhatsApp",
        "Vos avis et vos réalisations mis en valeur",
    ]
    packs = [{"name": p["name"], "price": p["price"], "positioning": p.get("positioning", "")} for p in catalog]

    return [
        {"id": "hook", "start": 0, "duration": 6, "name": name, "first": first,
         "words": ["Votre", "fiche", "Google", "mérite", "mieux."],
         "subtitle": f"{first + ', ' if first else ''}Pulse-PME a préparé une démo pour {name}."},
        {"id": "fiche", "start": 6, "duration": 7, "title": "Votre fiche aujourd'hui",
         "rating": rating, "reviews": reviews, "photos": photos, "website": website,
         "name": name, "address": address},
        {"id": "avant", "start": 13, "duration": 7, "title": "Aujourd'hui", "bullets": before},
        {"id": "apres", "start": 20, "duration": 8, "title": "Demain", "name": name, "cta": cta},
        {"id": "avantages", "start": 28, "duration": 7, "title": "Ce que cela vous apporte", "bullets": advantages},
        {"id": "packs", "start": 35, "duration": 6, "title": "Nos formules", "packs": packs},
        {"id": "cta", "start": 41, "duration": 3, "title": "Pulse-PME",
         "line": "Ouvrez la démo ci-dessous. Répondez à ce message : on en parle en 10 minutes."},
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  Primitives
# ─────────────────────────────────────────────────────────────────────────────

def _ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _punch(x: float) -> float:
    """Ease-out-back : léger dépassement, pour le rebond des entrées."""
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.4, 2.4
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def _mix(color, bg, alpha):
    alpha = max(0.0, min(1.0, alpha))
    return tuple(int(color[i] * alpha + bg[i] * (1 - alpha)) for i in range(3))


_BACKDROP: Image.Image | None = None
_PARTICLES = [(random.Random(i).random(), random.Random(i + 99).random(),
               random.Random(i + 7).uniform(0.4, 1.6), random.Random(i + 3).randint(1, 3))
              for i in range(70)]


def _backdrop() -> Image.Image:
    """Dégradé et halo, calculés une fois (le flou est coûteux)."""
    global _BACKDROP
    if _BACKDROP is None:
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
        draw = ImageDraw.Draw(img)
        for y in range(0, HEIGHT, 4):
            k = y / HEIGHT
            draw.rectangle([0, y, WIDTH, y + 4],
                           fill=tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * k) for i in range(3)))
        halo = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        ImageDraw.Draw(halo).ellipse([WIDTH // 2 - 420, -260, WIDTH // 2 + 420, 420], fill=(34, 80, 160))
        _BACKDROP = Image.blend(img, halo.filter(ImageFilter.GaussianBlur(100)), 0.6)
    return _BACKDROP.copy()


def _background(t: float) -> Image.Image:
    """Fond avec particules qui dérivent."""
    img = _backdrop()
    draw = ImageDraw.Draw(img)
    for x0, y0, speed, size in _PARTICLES:
        x = (x0 * WIDTH + t * 40 * speed) % WIDTH
        y = (y0 * HEIGHT - t * 18 * speed) % HEIGHT
        draw.ellipse([x, y, x + size * 2, y + size * 2], fill=(90, 140, 220))
    return img


def _wrap(draw, text: str, font, max_width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if draw.textlength(candidate, font=font) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _text(draw, xy, text, font, fill, max_width=None, alpha=1.0, anchor="la", line_gap=1.25):
    x, y = xy
    color = _mix(fill, BG_TOP, alpha)
    lines = _wrap(draw, text, font, max_width) if max_width else [text]
    for line in lines:
        draw.text((x, y), line, font=font, fill=color, anchor=anchor)
        y += int(font.size * line_gap)
    return y


def _card(draw, box, alpha=1.0, radius=24):
    draw.rounded_rectangle(box, radius=radius, fill=_mix(CARD, BG_TOP, alpha))


def _slide(p: float, distance: int) -> int:
    """Décalage horizontal qui se résorbe (entrée par la droite)."""
    return int(distance * (1 - _ease(p)))


def _cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    w, h = size
    src = img.convert("RGB")
    ratio = max(w / src.width, h / src.height)
    src = src.resize((max(1, int(src.width * ratio)), max(1, int(src.height * ratio))))
    left, top = (src.width - w) // 2, (src.height - h) // 2
    return src.crop((left, top, left + w, top + h))


# ─────────────────────────────────────────────────────────────────────────────
#  Scènes
# ─────────────────────────────────────────────────────────────────────────────

def _scene_hook(img, draw, s, p, t_local):
    """Accroche : les mots arrivent un par un, le dernier en ambre."""
    words = s["words"]
    font = _font(84, True)
    # deux lignes : « Votre fiche Google » / « mérite mieux. » (le dernier mot en ambre)
    rows = [(words[:3], 200), (words[3:], 320)]
    index = 0
    for row_words, y_row in rows:
        x = 110
        for w in row_words:
            k = _ease((p - 0.08 * index) * 3)
            y = y_row + int(40 * (1 - _punch(k)))
            color = AMBER if index == len(words) - 1 else WHITE
            _text(draw, (x, y), w, font, color, alpha=k)
            x += int(draw.textlength(w + " ", font=font))
            index += 1
    line_w = int(WIDTH * 0.7 * _ease((p - 0.5) * 2.5))
    if line_w > 0:
        draw.rectangle([110, 440, 110 + line_w, 446], fill=BLUE)
    _text(draw, (110, 480), s["subtitle"], _font(34), MUTED, WIDTH - 220, alpha=_ease((p - 0.6) * 3))


def _scene_fiche(img, draw, s, p, t_local):
    a = _ease(p * 3)
    x = _slide(p, 220)
    _text(draw, (90, 80), "Votre fiche aujourd'hui", _font(52, True), WHITE, alpha=a)
    _card(draw, (90 + x, 170, 1190 + x, 520), alpha=a)
    _text(draw, (130 + x, 205), s["name"], _font(44, True), WHITE, 1000, alpha=_ease((p - 0.15) * 3))
    if s["rating"] and s["reviews"]:
        k = _ease((p - 0.3) * 2.5)
        stars = f"★ {round(s['rating'] * k, 1):.1f} / 5   ·   {int(s['reviews'] * k)} avis"
        color = AMBER
    else:
        stars, color = "Pas encore d'avis visibles", MUTED
    _text(draw, (130 + x, 300), stars, _font(38, True), color, alpha=_ease((p - 0.3) * 3))
    _text(draw, (130 + x, 360), f"Photos sur la fiche : {s['photos']}", _font(30), MUTED,
          alpha=_ease((p - 0.45) * 3))
    _text(draw, (130 + x, 405), f"Site web : {s['website'] or 'aucun'}", _font(30), MUTED, 1000,
          alpha=_ease((p - 0.55) * 3))
    _text(draw, (130 + x, 456), s["address"], _font(26), MUTED, 1000, alpha=_ease((p - 0.6) * 3))


def _scene_bullets(img, draw, s, p, t_local, accent):
    _text(draw, (90, 80), s["title"], _font(52, True), WHITE, alpha=_ease(p * 3))
    font = _font(34)
    y = 180
    for i, bullet in enumerate(s["bullets"]):
        lines = _wrap(draw, bullet, font, 1010)
        height = max(105, 40 + len(lines) * 42)
        k = _ease((p - 0.12 - 0.14 * i) * 3)
        x = int(180 * (1 - k))
        _card(draw, (90 + x, y, 1190 + x, y + height), alpha=k)
        draw.rectangle([90 + x, y, 104 + x, y + height], fill=_mix(accent, BG_TOP, k))
        top = y + (height - len(lines) * int(font.size * 1.25)) // 2
        _text(draw, (135 + x, top), bullet, font, WHITE, 1010, alpha=k)
        y += height + 25


def _scene_apres(img, draw, s, p, t_local, hero):
    """Démo : la fenêtre navigateur zoome, puis un curseur clique sur le bouton."""
    zoom = 0.82 + 0.18 * _punch(p * 1.6)
    w, h = int(980 * zoom), int(470 * zoom)
    x0, y0 = WIDTH // 2 - w // 2, 150 + (470 - h) // 2
    frame = (x0, y0, x0 + w, y0 + h)
    _card(draw, frame, radius=18)
    bar = int(46 * zoom)
    draw.rectangle([frame[0], frame[1], frame[2], frame[1] + bar], fill=(12, 22, 40))
    for i, col in enumerate([ALERT_RED, AMBER, OK_GREEN]):
        r = max(3, int(7 * zoom))
        cx = frame[0] + int(30 * zoom) + i * int(26 * zoom)
        cy = frame[1] + bar // 2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    if hero is not None:
        img.paste(_cover(hero, (w, h - bar)), (frame[0], frame[1] + bar))
    name_font = _font(max(18, int(50 * zoom)), True)
    name_bottom = _text(draw, (frame[0] + int(40 * zoom), frame[1] + int(230 * zoom)), s["name"],
                        name_font, WHITE, int(w * 0.85), alpha=_ease((p - 0.2) * 3), line_gap=1.15)
    bx0, by0 = frame[0] + int(40 * zoom), max(frame[1] + int(340 * zoom), name_bottom + int(20 * zoom))
    button = (bx0, by0, bx0 + int(320 * zoom), by0 + int(60 * zoom))
    draw.rounded_rectangle(button, radius=14, fill=BLUE)
    _text(draw, ((button[0] + button[2]) // 2, (button[1] + button[3]) // 2), s["cta"],
          _font(max(14, int(26 * zoom)), True), WHITE, anchor="mm", alpha=_ease((p - 0.35) * 3))
    target = (button[0] + 60, button[1] + 30)
    k = _ease((p - 0.5) * 2.2)
    cx = int(WIDTH * 0.92 + (target[0] - WIDTH * 0.92) * k)
    cy = int(HEIGHT * 0.88 + (target[1] - HEIGHT * 0.88) * k)
    draw.polygon([(cx, cy), (cx, cy + 34), (cx + 9, cy + 26), (cx + 18, cy + 40), (cx + 23, cy + 37),
                  (cx + 14, cy + 23), (cx + 24, cy + 23)], fill=WHITE, outline=(0, 0, 0))
    if p > 0.85:
        ring = int(40 * _ease((p - 0.85) * 6))
        draw.ellipse([target[0] - ring, target[1] - ring, target[0] + ring, target[1] + ring],
                     outline=BLUE, width=3)


def _scene_avantages(img, draw, s, p, t_local):
    _text(draw, (90, 80), s["title"], _font(52, True), WHITE, alpha=_ease(p * 3))
    font = _font(34)
    for i, bullet in enumerate(s["bullets"]):
        k = _ease((p - 0.1 - 0.14 * i) * 3)
        flip = max(0.06, abs(math.cos((1 - k) * math.pi / 2)))  # carte qui se retourne
        y = 200 + i * 135
        mid = 90 + 550 + int(40 * (1 - k))
        width = int(1100 * flip)
        _card(draw, (mid - width // 2, y, mid + width // 2, y + 105), alpha=min(1.0, k * 1.2))
        if k > 0.5:
            draw.text((mid - 500, y + 52), f"0{i + 1}", font=_font(44, True), fill=_mix(OK_GREEN, BG_TOP, k),
                      anchor="lm")
            _text(draw, (mid - 410, y + 52), bullet, font, WHITE, 900, alpha=k, anchor="lm")


def _scene_packs(img, draw, s, p, t_local):
    _text(draw, (90, 70), "Nos formules", _font(52, True), WHITE, alpha=_ease(p * 3))
    x = 90
    for i, pack in enumerate(s["packs"]):
        k = _ease((p - 0.1 - 0.14 * i) * 3)
        lift = int(60 * (1 - _punch(k)))
        box = (x, 170 + lift, x + 350, 580 + lift)
        _card(draw, box, alpha=k)
        if pack["name"] == "Pro":
            draw.rounded_rectangle((box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4), radius=28,
                                   outline=AMBER, width=3)
        _text(draw, (x + 30, 200 + lift), pack["name"], _font(40, True), WHITE, alpha=k)
        shown = int(pack["price"] * _ease((p - 0.2 - 0.14 * i) * 2.5))
        _text(draw, (x + 30, 265 + lift), f"{shown} € / mois", _font(42, True), AMBER, alpha=k)
        _text(draw, (x + 30, 350 + lift), pack["positioning"], _font(24), MUTED, 290, alpha=k)
        x += 380
    _text(draw, (WIDTH // 2, 640), "Répondez à ce message pour choisir votre formule.", _font(30), WHITE,
          WIDTH - 200, anchor="mm", alpha=_ease((p - 0.5) * 3))


def _scene_cta(img, draw, s, p, t_local):
    pulse = 1 + 0.04 * math.sin(t_local * 2 * math.pi * 1.5)
    _text(draw, (WIDTH // 2, 220), s["title"], _font(110, True), WHITE, anchor="mm", alpha=_ease(p * 3))
    _text(draw, (WIDTH // 2, 340), s["line"], _font(32), MUTED, WIDTH - 260, anchor="mm",
          alpha=_ease((p - 0.3) * 3))
    bw, bh = int(340 * pulse), int(74 * pulse)
    cx, cy = WIDTH // 2, 490
    draw.rounded_rectangle((cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2), radius=18,
                           fill=_mix(BLUE, BG_TOP, _ease((p - 0.5) * 3)))
    _text(draw, (cx, cy), "Répondre au message", _font(int(30 * pulse), True), WHITE, anchor="mm",
          alpha=_ease((p - 0.6) * 3))


_RENDERERS = {
    "hook": lambda img, d, s, p, t, hero: _scene_hook(img, d, s, p, t),
    "fiche": lambda img, d, s, p, t, hero: _scene_fiche(img, d, s, p, t),
    "avant": lambda img, d, s, p, t, hero: _scene_bullets(img, d, s, p, t, accent=ALERT_RED),
    "apres": _scene_apres,
    "avantages": lambda img, d, s, p, t, hero: _scene_avantages(img, d, s, p, t),
    "packs": lambda img, d, s, p, t, hero: _scene_packs(img, d, s, p, t),
    "cta": lambda img, d, s, p, t, hero: _scene_cta(img, d, s, p, t),
}


def _render_scene(scene: dict, t: float, hero: Image.Image | None) -> Image.Image:
    img = _background(t)
    draw = ImageDraw.Draw(img)
    t_local = t - scene["start"]
    p = max(0.0, min(1.0, t_local / scene["duration"]))
    _RENDERERS[scene["id"]](img, draw, scene, p, t_local, hero)
    return img


def _camera(frame: Image.Image, t_local: float) -> Image.Image:
    """Travelling lent : zoom progressif de 0 à 3 % sur chaque scène."""
    scale = 1 + 0.03 * min(1.0, t_local / 6)
    w, h = int(WIDTH / scale), int(HEIGHT / scale)
    x, y = (WIDTH - w) // 2, (HEIGHT - h) // 2
    return frame.crop((x, y, x + w, y + h)).resize((WIDTH, HEIGHT))


def _light_sweep(frame: Image.Image, progress: float) -> Image.Image:
    """Bande de lumière diagonale qui traverse l'écran pendant une transition."""
    band = Image.new("L", (WIDTH, HEIGHT), 0)
    d = ImageDraw.Draw(band)
    x = int(-300 + (WIDTH + 600) * progress)
    d.polygon([(x, 0), (x + 160, 0), (x - 240, HEIGHT), (x - 400, HEIGHT)], fill=90)
    glow = Image.new("RGB", (WIDTH, HEIGHT), (120, 170, 255))
    return Image.composite(glow, frame, band.filter(ImageFilter.GaussianBlur(40)))


def render_frame(scenes: list[dict], t: float, hero: Image.Image | None) -> Image.Image:
    """Image à l'instant t, avec fondu et balayage de lumière depuis la scène précédente."""
    idx = next((i for i, s in enumerate(scenes) if s["start"] <= t < s["start"] + s["duration"]),
               len(scenes) - 1)
    current = scenes[idx]
    into = t - current["start"]
    frame = _camera(_render_scene(current, t, hero), into)
    if idx > 0 and into < TRANSITION:
        prev = scenes[idx - 1]
        prev_frame = _camera(_render_scene(prev, prev["start"] + prev["duration"] - 1e-3, hero), prev["duration"])
        frame = Image.blend(prev_frame, frame, _ease(into / TRANSITION))
        frame = _light_sweep(frame, into / TRANSITION)
    return frame


# ─────────────────────────────────────────────────────────────────────────────
#  Photo, encodage, injection
# ─────────────────────────────────────────────────────────────────────────────

def fetch_hero_photo(photos: list) -> Image.Image | None:
    """Première photo accessible de la fiche (relayée par /photo). None si indisponible."""
    import requests

    for entry in photos or []:
        if not isinstance(entry, str):
            continue
        url = urllib.parse.unquote(entry.split("url=", 1)[1]) if entry.startswith("/photo?url=") else entry
        if not validate_photo_url(url)[0]:
            continue
        try:
            resp = requests.get(url, headers=upstream_headers(url), timeout=10)
            if resp.status_code == 200 and resp.content:
                return Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception:
            continue
    return None


def total_duration(scenes: list[dict]) -> float:
    return scenes[-1]["start"] + scenes[-1]["duration"]


def _encode(scenes: list[dict], hero: Image.Image | None, path: str, width: int, height: int, fps: int) -> None:
    import imageio_ffmpeg

    hero_small = hero.resize((int(width * 0.77), int(height * 0.65))) if hero is not None else None
    writer = imageio_ffmpeg.write_frames(
        path, (width, height), fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8,
        output_params=["-movflags", "+faststart"],
    )
    writer.send(None)
    for i in range(int(total_duration(scenes) * fps)):
        frame = render_frame(scenes, i / fps, hero_small)
        if frame.size != (width, height):
            frame = frame.resize((width, height))
        writer.send(frame.tobytes())
    writer.close()


def render_video(scenes: list[dict], hero: Image.Image | None = None, width: int = WIDTH,
                 height: int = HEIGHT, fps: int = FPS) -> bytes:
    """Encode la vidéo MP4 muette (H.264, yuv420p) et renvoie ses octets."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "presentation.mp4")
        _encode(scenes, hero, path, width, height, fps)
        with open(path, "rb") as fh:
            return fh.read()


def render_presentation(scenes: list[dict], hero: Image.Image | None = None, voice: bool = True,
                        log=None, width: int = WIDTH, height: int = HEIGHT, fps: int = FPS,
                        _voiceover=None) -> tuple[bytes, float]:
    """Vidéo complète : voix off (si disponible) + musique avec ducking. Renvoie (mp4, durée).

    Chaque couche est optionnelle : sans clé ElevenLabs, vidéo + musique ; si le mixage
    échoue, vidéo muette. Seule l'image est indispensable.
    """
    from backend.services import soundtrack, voiceover

    log = log or (lambda msg: None)
    generate = _voiceover or voiceover.generate_voiceover
    with tempfile.TemporaryDirectory() as tmp:
        voice_tracks: list[tuple[float, str]] = []
        if voice:
            try:
                scenes, voice_tracks = generate(scenes, tmp)
                log(f"🎙️ Voix off générée ({len(voice_tracks)} phrases).")
            except Exception as exc:  # voix facultative
                log(f"Voix off indisponible, vidéo sans voix : {exc}")
        silent = os.path.join(tmp, "silent.mp4")
        _encode(scenes, hero, silent, width, height, fps)
        duration = total_duration(scenes)
        final = os.path.join(tmp, "presentation.mp4")
        try:
            music = os.path.join(tmp, "music.wav")
            with open(music, "wb") as fh:
                fh.write(soundtrack.music_bed(duration, [s["start"] for s in scenes[1:]]))
            soundtrack.mix_into_video(silent, music, voice_tracks, final)
        except Exception as exc:  # bande-son facultative
            log(f"Bande-son non ajoutée : {exc}")
            final = silent
        with open(final, "rb") as fh:
            return fh.read(), duration


def inject_video_block(html: str, video_name: str = "presentation.mp4", seconds: float = 44) -> str:
    """Place la présentation juste après le premier bloc (hero). Repli : fin de <body>."""
    block = (
        '<section id="presentation" style="padding:48px 16px;text-align:center;background:#0b1424;'
        'width:100%;box-sizing:border-box;display:block;margin:0">'
        f'<h2 style="color:#fff;font-family:sans-serif;margin:0 0 16px">Présentation en {round(seconds)} secondes</h2>'
        f'<video controls playsinline preload="metadata" src="{video_name}" '
        'style="display:block;width:100%;max-width:960px;margin:0 auto;border-radius:16px"></video></section>'
    )
    marker = html.find("</section>")
    if marker != -1:
        cut = marker + len("</section>")
        return html[:cut] + block + html[cut:]
    if "</body>" in html:
        return html.replace("</body>", block + "</body>", 1)
    return html + block
