"""Vidéo de présentation animée (44 s) envoyée avec la démo.

Étape « Motion Director » du pipeline : elle explique au commerce pourquoi il est contacté,
montre l'avant / l'après, les avantages et les formules. Rendue localement (Pillow + ffmpeg
embarqué), sans API vidéo payante.

Règle : seuls des faits issus de la fiche Google et du catalogue de formules sont affichés.
Aucune note, aucun avis, aucune promesse de résultat n'est inventée.
"""
import base64
import io
import os
import tempfile
import urllib.parse

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from backend.services.photo_proxy import upstream_headers, validate_photo_url

WIDTH, HEIGHT, FPS = 1280, 720, 24
BG_TOP, BG_BOTTOM = (8, 16, 30), (16, 32, 58)
BLUE, AMBER, WHITE, MUTED = (59, 130, 246), (245, 158, 11), (255, 255, 255), (148, 163, 184)
CARD = (22, 36, 62)
OK_GREEN = (52, 211, 153)

_font_cache: dict = {}


def _font(size: int, bold: bool = False):
    key = (size, bold)
    if key not in _font_cache:
        candidates = ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
        font = None
        for name in candidates:
            try:
                font = ImageFont.truetype(name, size)
                break
            except OSError:
                continue
        _font_cache[key] = font or ImageFont.load_default(size=size)
    return _font_cache[key]


def build_storyboard(biz: dict, sector_label: str, catalog: list[dict], cta: str = "Demander un devis") -> list[dict]:
    """Découpe 44 s en six scènes. Ne renvoie que des faits fournis en entrée."""
    name = biz.get("name") or "votre commerce"
    first = (biz.get("owner_first_name") or "").strip()
    address = biz.get("address") or ""
    website = (biz.get("website") or "").strip()
    rating = float(biz.get("rating") or 0)
    reviews = int(biz.get("user_ratings_total") or 0)
    photos = len(biz.get("photos") or [])

    avant = ["Vos clients vous cherchent sur Google : votre vitrine doit répondre."]
    if not website:
        avant.insert(0, "Aucun site web pour répondre aux recherches.")
    else:
        avant.insert(0, "Un site existant qui peut être mieux mis en valeur.")
    if reviews:
        avant.append(f"Vos {reviews} avis Google méritent d'être mis en avant.")
    else:
        avant.append("Vos avis Google sont un atout à mettre en avant.")

    avantages = [
        "Visible 24h/24 quand on vous cherche sur Google",
        "Demandes de devis par téléphone et WhatsApp",
        "Vos avis et vos réalisations mis en valeur",
    ]

    packs = [
        {"name": p["name"], "price": p["price"], "positioning": p.get("positioning", "")}
        for p in catalog
    ]

    return [
        {"id": "intro", "start": 0, "duration": 6, "title": f"Bonjour{(' ' + first) if first else ''},",
         "subtitle": f"Pulse-PME a préparé une présentation pour {name}.",
         "caption": "En 44 secondes : pourquoi nous vous contactons et ce que nous proposons."},
        {"id": "fiche", "start": 6, "duration": 8, "title": "Votre fiche Google",
         "rating": rating, "reviews": reviews, "photos": photos, "website": website,
         "name": name, "address": address, "sector": sector_label,
         "caption": "Votre fiche Google est souvent la première chose que vos clients voient."},
        {"id": "avant", "start": 14, "duration": 8, "title": "Aujourd'hui", "bullets": avant,
         "caption": "Les clients qui cherchent un " + sector_label.lower() + " choisissent ceux qu'ils trouvent."},
        {"id": "apres", "start": 22, "duration": 8, "title": "Demain", "name": name, "cta": cta,
         "caption": "Une démo prête à consulter, avec vos propres photos."},
        {"id": "avantages", "start": 30, "duration": 7, "title": "Ce que cela vous apporte", "bullets": avantages,
         "caption": "Pulse-PME gère la mise en ligne et le suivi : vous gardez votre activité."},
        {"id": "packs", "start": 37, "duration": 7, "title": "Nos formules", "packs": packs,
         "caption": "Répondez à ce message pour choisir votre formule."},
    ]


def _ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


_BACKGROUND: Image.Image | None = None


def _background() -> Image.Image:
    """Dégradé + halo statiques, calculés une seule fois (le flou est coûteux)."""
    global _BACKGROUND
    if _BACKGROUND is None:
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
        draw = ImageDraw.Draw(img)
        for y in range(0, HEIGHT, 4):
            k = y / HEIGHT
            color = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * k) for i in range(3))
            draw.rectangle([0, y, WIDTH, y + 4], fill=color)
        halo = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        ImageDraw.Draw(halo).ellipse([WIDTH // 2 - 380, -220, WIDTH // 2 + 380, 380], fill=(30, 70, 140))
        halo = halo.filter(ImageFilter.GaussianBlur(90))
        _BACKGROUND = Image.blend(img, halo, 0.55)
    return _BACKGROUND.copy()


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
    fill = tuple(int(c * alpha + BG_TOP[i] * (1 - alpha)) for i, c in enumerate(fill))
    lines = _wrap(draw, text, font, max_width) if max_width else [text]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill, anchor=anchor)
        y += int(font.size * line_gap)
    return y


def _card(draw, box, alpha=1.0, radius=24):
    x0, y0, x1, y1 = box
    color = tuple(int(c * alpha + BG_TOP[i] * (1 - alpha)) for i, c in enumerate(CARD))
    draw.rounded_rectangle(box, radius=radius, fill=color)


def _scene_intro(img, draw, s, p):
    _text(draw, (WIDTH // 2, 250), s["title"], _font(74, True), WHITE, WIDTH - 160,
          alpha=_ease(p * 2), anchor="mm")
    _text(draw, (WIDTH // 2, 380), s["subtitle"], _font(38), MUTED, WIDTH - 200,
          alpha=_ease((p - 0.25) * 2), anchor="mm")
    _text(draw, (WIDTH // 2, 520), s["caption"], _font(28), BLUE, WIDTH - 200,
          alpha=_ease((p - 0.5) * 2), anchor="mm")


def _scene_fiche(img, draw, s, p):
    a = _ease(p * 2)
    _text(draw, (90, 80), s["title"], _font(52, True), WHITE, alpha=a)
    _card(draw, (90, 170, 1190, 500), alpha=a)
    _text(draw, (130, 205), s["name"], _font(44, True), WHITE, 1000, alpha=_ease((p - 0.15) * 2))
    if s["rating"] and s["reviews"]:
        stars = f"★ {s['rating']:.1f} / 5   ·   {s['reviews']} avis"
        color = AMBER
    else:
        stars, color = "Pas encore d'avis visibles", MUTED
    _text(draw, (130, 300), stars, _font(36, True), color, alpha=_ease((p - 0.3) * 2))
    _text(draw, (130, 355), f"Photos sur la fiche : {s['photos']}", _font(30), MUTED, alpha=_ease((p - 0.45) * 2))
    site = s["website"] or "Aucun site web"
    _text(draw, (130, 400), f"Site web : {site}", _font(30), MUTED, 1000, alpha=_ease((p - 0.55) * 2))
    _text(draw, (130, 450), s["address"], _font(26), MUTED, 1000, alpha=_ease((p - 0.6) * 2))
    _text(draw, (WIDTH // 2, 600), s["caption"], _font(30), WHITE, WIDTH - 200,
          alpha=_ease((p - 0.4) * 2), anchor="mm")


def _scene_bullets(img, draw, s, p, accent):
    _text(draw, (90, 80), s["title"], _font(52, True), WHITE, alpha=_ease(p * 2))
    font = _font(34)
    text_width = 1010
    y = 190
    for i, bullet in enumerate(s["bullets"]):
        lines = _wrap(draw, bullet, font, text_width)
        height = max(105, 40 + len(lines) * 42)  # carte adaptée au nombre de lignes
        a = _ease((p - 0.1 - 0.12 * i) * 2.5)
        _card(draw, (90, y, 1190, y + height), alpha=a)
        draw.rectangle([90, y, 104, y + height], fill=tuple(int(c * a + BG_TOP[j] * (1 - a)) for j, c in enumerate(accent)))
        line_h = int(font.size * 1.25)
        block_top = y + (height - len(lines) * line_h) // 2  # bloc de texte centré verticalement
        _text(draw, (135, block_top), bullet, font, WHITE, text_width, alpha=a, anchor="la", line_gap=1.25)
        y += height + 25
    _text(draw, (WIDTH // 2, 660), s["caption"], _font(28), WHITE, WIDTH - 200,
          alpha=_ease((p - 0.5) * 2), anchor="mm")


def _scene_apres(img, draw, s, p, hero):
    a = _ease(p * 2)
    _text(draw, (90, 70), s["title"], _font(52, True), WHITE, alpha=a)
    frame = (120, 150, 1160, 610)
    _card(draw, frame, alpha=a, radius=18)
    draw.rectangle([frame[0], frame[1], frame[2], frame[1] + 46], fill=(12, 22, 40))
    for i, col in enumerate([(239, 68, 68), (245, 158, 11), (52, 211, 153)]):
        draw.ellipse([frame[0] + 20 + i * 26, frame[1] + 16, frame[0] + 34 + i * 26, frame[1] + 30], fill=col)
    if hero is not None:
        pic = _cover(hero, (frame[2] - frame[0], 470 - 46))
        img.paste(pic, (frame[0], frame[1] + 46))
    _text(draw, (frame[0] + 40, frame[1] + 300), s["name"], _font(54, True), WHITE, 1000,
          alpha=_ease((p - 0.2) * 2))
    button = (frame[0] + 40, frame[1] + 380, frame[0] + 360, frame[1] + 440)
    draw.rounded_rectangle(button, radius=14, fill=BLUE)
    _text(draw, ((button[0] + button[2]) // 2, (button[1] + button[3]) // 2), s["cta"], _font(26, True), WHITE,
          anchor="mm", alpha=_ease((p - 0.35) * 2))
    _text(draw, (WIDTH // 2, 660), s["caption"], _font(28), MUTED, WIDTH - 200,
          alpha=_ease((p - 0.5) * 2), anchor="mm")


def _scene_packs(img, draw, s, p):
    _text(draw, (90, 70), s["title"], _font(52, True), WHITE, alpha=_ease(p * 2))
    x = 90
    for i, pack in enumerate(s["packs"]):
        a = _ease((p - 0.1 - 0.15 * i) * 2.5)
        box = (x, 170, x + 350, 560)
        _card(draw, box, alpha=a)
        _text(draw, (x + 30, 200), pack["name"], _font(40, True), WHITE, alpha=a)
        _text(draw, (x + 30, 265), f"{pack['price']} € / mois", _font(42, True), AMBER, alpha=a)
        _text(draw, (x + 30, 350), pack["positioning"], _font(24), MUTED, 290, alpha=a)
        x += 380
    _text(draw, (WIDTH // 2, 620), s["caption"], _font(30), WHITE, WIDTH - 200, anchor="mm",
          alpha=_ease((p - 0.4) * 2))


def _cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    w, h = size
    src = img.convert("RGB")
    ratio = max(w / src.width, h / src.height)
    src = src.resize((int(src.width * ratio), int(src.height * ratio)))
    left, top = (src.width - w) // 2, (src.height - h) // 2
    return src.crop((left, top, left + w, top + h))


def render_frame(scenes: list[dict], t: float, hero: Image.Image | None, accent=BLUE) -> Image.Image:
    img = _background()
    draw = ImageDraw.Draw(img)
    scene = next((s for s in scenes if s["start"] <= t < s["start"] + s["duration"]), scenes[-1])
    p = (t - scene["start"]) / scene["duration"]
    kind = scene["id"]
    if kind == "intro":
        _scene_intro(img, draw, scene, p)
    elif kind == "fiche":
        _scene_fiche(img, draw, scene, p)
    elif kind == "avant":
        _scene_bullets(img, draw, scene, p, accent=(239, 68, 68))
    elif kind == "apres":
        _scene_apres(img, draw, scene, p, hero)
    elif kind == "avantages":
        _scene_bullets(img, draw, scene, p, accent=OK_GREEN)
    elif kind == "packs":
        _scene_packs(img, draw, scene, p)
    return img


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


def render_video(scenes: list[dict], hero: Image.Image | None = None, width: int = WIDTH,
                 height: int = HEIGHT, fps: int = FPS) -> bytes:
    """Encode la vidéo MP4 (H.264, yuv420p) et renvoie ses octets."""
    import imageio_ffmpeg

    total = scenes[-1]["start"] + scenes[-1]["duration"]
    hero_small = hero.resize((width, height)) if hero is not None else None
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "presentation.mp4")
        writer = imageio_ffmpeg.write_frames(
            path, (width, height), fps=fps, codec="libx264",
            pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8,
            output_params=["-movflags", "+faststart"],
        )
        writer.send(None)
        frames = int(total * fps)
        for i in range(frames):
            t = i / fps
            frame = render_frame(scenes, t, hero_small, accent=BLUE)
            if frame.size != (width, height):
                frame = frame.resize((width, height))
            writer.send(frame.tobytes())
        writer.close()
        with open(path, "rb") as fh:
            return fh.read()


def inject_video_block(html: str, video_name: str = "presentation.mp4") -> str:
    """Place la présentation vidéo en haut de la démo : juste après le premier bloc (hero).

    Repli : fin de <body> si la page n'a pas de section.
    """
    block = (
        '<section id="presentation" style="padding:48px 16px;text-align:center;background:#0b1424">'
        '<h2 style="color:#fff;font-family:sans-serif;margin:0 0 16px">Présentation en 44 secondes</h2>'
        f'<video controls playsinline preload="metadata" src="{video_name}" '
        'style="width:100%;max-width:960px;border-radius:16px"></video></section>'
    )
    marker = html.find("</section>")
    if marker != -1:
        cut = marker + len("</section>")
        return html[:cut] + block + html[cut:]
    if "</body>" in html:
        return html.replace("</body>", block + "</body>", 1)
    return html + block
