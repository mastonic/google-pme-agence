"""Showreel avant/après (motion design) généré automatiquement après le site.

Même rendu que la démo « Taxi avant/après » : 8 scènes animées dans un canvas HTML
(showreel_template.html), filmées image par image par Chromium (Playwright), puis voix
off (voiceover.py) et musique avec ducking (soundtrack.py).

L'« après » est la vraie capture du site généré (ordinateur + mobile) ; l'« avant » est la
capture du site actuel du commerce s'il en a un, sinon sa fiche Google sans site. Une scène
« galerie » montre les vraies photos : celles déposées par le client d'abord, puis celles de
sa fiche Google (scène absente s'il n'y a aucune photo).
Tous les textes viennent des données du commerce : aucune note, aucun avis, aucun
chiffre de clientèle inventés.

Si Chromium n'est pas disponible, render_showreel lève ShowreelUnavailable et l'appelant
retombe sur l'ancienne vidéo Pillow (motion_video.render_presentation).
"""
import base64
import datetime
import json
import os
import re
import subprocess
import tempfile
import unicodedata

TEMPLATE = os.path.join(os.path.dirname(__file__), "showreel_template.html")
WIDTH, HEIGHT, FPS = 1920, 1080, 30

ACCENTS = {"artisan": "#3DA9FC", "automotive": "#FF7A1A", "transport": "#FFD23F"}
DEFAULT_ACCENT = "#2EE59D"

# Durées sans voix off ; avec voix, chaque scène est allongée pour contenir sa phrase.
SCENES = [("avant", 3.6), ("cout", 4.6), ("refonte", 3.0), ("apres", 5.2),
          ("parcours", 4.6), ("comparatif", 4.0), ("pourquoi", 4.6), ("cta", 5.0)]

FLOWS = {
    "artisan": {
        "title": "Une urgence ? Vos clients vous joignent en un clic.",
        "sub": "APPEL, DEVIS, INTERVENTION : SANS FRICTION",
        "steps": [["📞", "Appel en 1 clic", "depuis Google ou le site"], ["📝", "Devis gratuit", "formulaire simple"],
                  ["🔧", "Intervention", "dans votre zone"], ["✓", "Demande reçue", "par SMS et email"]],
        "notif": ("🔧", "Nouvelle demande de devis"),
    },
    "automotive": {
        "title": "Vos clients prennent rendez-vous en 30 secondes.",
        "sub": "RENDEZ-VOUS, DEVIS, RÉPARATION",
        "steps": [["📅", "Rendez-vous", "en ligne, 24/7"], ["📝", "Devis", "avant l'intervention"],
                  ["🔧", "Réparation", "à l'atelier"], ["✓", "Confirmé", "SMS envoyé au client"]],
        "notif": ("🚗", "Nouvelle demande de rendez-vous"),
    },
    "transport": {
        "title": "Vos clients réservent en 30 secondes.",
        "sub": "MÊME À 2H DU MATIN, MÊME QUAND VOUS CONDUISEZ",
        "steps": [["📍", "Départ", "adresse du client"], ["✈️", "Arrivée", "gare, aéroport, hôpital"],
                  ["💶", "Prix estimé", "affiché avant de réserver"], ["✓", "Confirmé", "SMS envoyé au client"]],
        "notif": ("🚕", "Nouvelle course réservée"),
    },
    "generic": {
        "title": "Vos clients vous contactent en un clic.",
        "sub": "DEPUIS LEUR TÉLÉPHONE, À TOUTE HEURE",
        "steps": [["📲", "Contact", "appel ou WhatsApp"], ["📝", "Demande", "formulaire simple"],
                  ["📍", "Itinéraire", "jusqu'à chez vous"], ["✓", "Nouveau client", "notification immédiate"]],
        "notif": ("🔔", "Nouvelle demande de contact"),
    },
}

REASONS = [["🔑", "Site livré clé en main", "design, textes, photos : on fait tout"],
           ["📍", "Trouvé sur Google & l'IA", "référencement local"],
           ["📲", "Demandes 24/7", "formulaire + notifications"],
           ["🔒", "Sécurisé & maintenu", "hébergement, HTTPS, mises à jour"],
           ["💬", "Avis clients mis en avant", "la confiance avant le premier appel"],
           ["🤝", "Un interlocuteur unique", "pas de jargon, un suivi humain"]]


MAX_PHOTOS = 3
MAX_PHOTO_BYTES = 8 * 1024 * 1024


def fetch_photos(urls: list[str], limit: int = MAX_PHOTOS, timeout: int = 10) -> list[str]:
    """Télécharge les premières photos utilisables et les renvoie en data URL (ordre conservé)."""
    import requests

    out, seen = [], set()
    for url in urls:
        if len(out) >= limit:
            break
        if not isinstance(url, str) or not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        try:
            resp = requests.get(url, timeout=timeout)
            mime = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            if resp.ok and mime in ("image/jpeg", "image/png", "image/webp") and 0 < len(resp.content) <= MAX_PHOTO_BYTES:
                out.append(f"data:{mime};base64," + base64.b64encode(resp.content).decode())
        except Exception:
            continue
    return out


class ShowreelUnavailable(RuntimeError):
    """Chromium/Playwright absent : l'appelant utilise la vidéo Pillow."""


def _city(address: str) -> str:
    m = re.search(r"\b\d{5}\s+([^,]+)", address or "")
    return m.group(1).strip() if m else ""


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40] or "votre-commerce"


def _problems(website: str, reviews: int, photos: int) -> list[str]:
    out = []
    if not website:
        out += ["Aucun site web", "Pas de demande de devis en ligne"]
    else:
        if website.startswith("http://"):
            out.append("« Site non sécurisé » (http)")
        out.append("Un site qui peut faire bien plus")
    if reviews:
        out.append(f"{reviews} avis Google à mettre en avant")
    if not photos:
        out.append("Aucune photo sur la fiche Google")
    out.append("Des clients qui appellent ailleurs")
    return out[:4]


def build_showreel(biz: dict, sector: str, catalog: list[dict], brand: str | None = None,
                   new_url: str = "", photos: list[str] | None = None) -> dict:
    """Données du showreel (textes, couleurs, scènes) à partir des seules données du commerce.

    `photos` : vraies photos déjà téléchargées (data URL, voir fetch_photos) pour la scène galerie.
    """
    gallery = [ph for ph in (photos or []) if ph][:MAX_PHOTOS]
    name = (biz.get("name") or "votre commerce").strip()
    website = (biz.get("website") or "").strip()
    rating = float(biz.get("rating") or 0)
    reviews = int(biz.get("user_ratings_total") or 0)
    photos = len(biz.get("photos") or [])
    city = _city(biz.get("address") or "")
    flow = FLOWS.get(sector, FLOWS["generic"])
    prices = sorted(int(p["price"]) for p in catalog if p.get("price"))
    brand = brand or os.environ.get("VIDEO_BRAND", "").strip() or "Pulse-PME"
    order = list(SCENES)
    if gallery:  # vraies photos juste après la présentation du nouveau site
        order.insert([sid for sid, _ in order].index("apres") + 1, ("galerie", 4.4))
    start, scenes = 0.0, []
    for sid, dur in order:
        scenes.append({"id": sid, "start": round(start, 2), "duration": dur, "min": dur})
        start += dur
    label = re.sub(r"^https?://", "", website).rstrip("/") if website else ""
    # Faits recopiés dans chaque scène : voiceover.build_script n'écrit qu'à partir d'eux.
    facts = {"avant": {"name": name, "first": (biz.get("owner_first_name") or "").strip(), "website": bool(website)},
             "cout": {"website": bool(website), "reviews": reviews},
             "parcours": {"sector": sector}, "pourquoi": {"brand": brand},
             "galerie": {"name": name, "count": len(gallery)},
             "cta": {"min_price": prices[0] if prices else 0}}
    for s in scenes:
        s.update(facts.get(s["id"], {}))
    return {
        "name": name, "first": (biz.get("owner_first_name") or "").strip(), "city": city,
        "sector": sector, "accent": ACCENTS.get(sector, DEFAULT_ACCENT), "brand": brand,
        "slug": _slug(name), "website": website, "website_label": label,
        "secure": website.startswith("https://") if website else False,
        "rating": rating, "rating_fr": f"{rating:.1f}".replace(".", ","), "reviews": reviews, "photos": photos,
        "search": f"{name} {city}".strip(),
        "problems": _problems(website, reviews, photos),
        "year": str(datetime.date.today().year),
        "new_url": re.sub(r"^https?://", "", new_url).rstrip("/") or f"{_slug(name)}.vercel.app",
        "flow_title": flow["title"], "flow_sub": flow["sub"], "flow": flow["steps"],
        "notif_icon": flow["notif"][0],
        "notif": [flow["notif"][1], f"{name}{' · ' + city if city else ''}"],
        "reasons": REASONS,
        "min_price": prices[0] if prices else 0,
        "cta_line": (f"Formules à partir de {prices[0]} € / mois. On s'occupe de tout." if prices
                     else "On s'occupe de tout, de A à Z."),
        "cta_button": "RÉPONDEZ À CE MESSAGE →",
        "gallery": gallery,
        "scenes": scenes,
    }


def _data_url(jpeg: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(jpeg).decode()


def _capture(browser, html: str | None, url: str | None, width: int, height: int,
             max_height: int, timeout_ms: int = 15000) -> bytes | None:
    """Capture pleine page (hauteur bornée) d'un HTML ou d'une URL ; None en cas d'échec."""
    page = browser.new_page(viewport={"width": width, "height": height})
    try:
        if html:
            page.set_content(html, wait_until="load", timeout=timeout_ms)
        else:
            try:
                page.goto(url, wait_until="load", timeout=timeout_ms)
            except Exception:
                # Site lent ou scripts tiers interminables : on se contente du DOM chargé.
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(2500)
        page.wait_for_timeout(800)  # animations d'entrée, polices
        full = page.evaluate("document.documentElement.scrollHeight") or height
        return page.screenshot(type="jpeg", quality=80,
                               clip={"x": 0, "y": 0, "width": width, "height": min(int(full), max_height)},
                               full_page=True)
    except Exception:
        return None
    finally:
        page.close()


def render_frames(data: dict, site_html: str | None, out_path: str, width: int = WIDTH,
                  height: int = HEIGHT, fps: int = FPS, log=None) -> None:
    """Filme le canvas image par image vers un MP4 muet."""
    import imageio_ffmpeg
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ShowreelUnavailable("playwright non installé") from exc
    log = log or (lambda m: None)
    try:
        pw = sync_playwright().start()
    except Exception as exc:
        raise ShowreelUnavailable(f"playwright indisponible : {exc}") from exc
    try:
        try:
            browser = pw.chromium.launch(args=["--no-sandbox"])
        except Exception as exc:
            raise ShowreelUnavailable(f"Chromium indisponible : {exc}") from exc
        images = {}
        if site_html:
            desk = _capture(browser, site_html, None, 1440, 900, 6000)
            mob = _capture(browser, site_html, None, 390, 844, 6000)
            images.update(desk=desk and _data_url(desk), mob=mob and _data_url(mob))
        if data.get("website"):
            old = _capture(browser, None, data["website"], 1440, 900, 900)
            images["old"] = old and _data_url(old)
            log("📸 Capture du site actuel " + ("réussie." if old else "impossible, fiche Google utilisée."))
        page = browser.new_page(viewport={"width": width, "height": height})
        with open(TEMPLATE, encoding="utf-8") as fh:
            page.set_content(fh.read(), wait_until="load")
        page.evaluate("d => window.setup(d)", dict(data, images=images))
        total = data["scenes"][-1]["start"] + data["scenes"][-1]["duration"]
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "image2pipe",
               "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path]
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for i in range(int(total * fps)):
                page.evaluate("t => window.render(t)", i / fps)
                ff.stdin.write(page.screenshot(type="jpeg", quality=90))
        finally:
            ff.stdin.close()
            err = ff.stderr.read().decode(errors="ignore")
            ff.wait()
        if ff.returncode != 0:
            raise RuntimeError(f"encodage vidéo impossible : {err[-300:]}")
        browser.close()
    finally:
        pw.stop()


def render_showreel(data: dict, site_html: str | None = None, voice: bool = True, log=None,
                    width: int = WIDTH, height: int = HEIGHT, fps: int = FPS,
                    _voiceover=None) -> tuple[bytes, float]:
    """Showreel complet (image + voix off + musique). Renvoie (mp4, durée en secondes)."""
    from backend.services import soundtrack, voiceover

    log = log or (lambda m: None)
    generate = _voiceover or voiceover.generate_voiceover
    with tempfile.TemporaryDirectory() as tmp:
        tracks: list[tuple[float, str]] = []
        if voice:
            try:
                data["scenes"], tracks = generate(data["scenes"], tmp)
                log(f"🎙️ Voix off générée ({len(tracks)} phrases).")
            except Exception as exc:
                log(f"Voix off indisponible, showreel sans voix : {exc}")
        silent = os.path.join(tmp, "silent.mp4")
        render_frames(data, site_html, silent, width, height, fps, log)
        duration = data["scenes"][-1]["start"] + data["scenes"][-1]["duration"]
        final = os.path.join(tmp, "showreel.mp4")
        try:
            music = os.path.join(tmp, "music.wav")
            with open(music, "wb") as fh:
                fh.write(soundtrack.music_bed(duration, [s["start"] for s in data["scenes"][1:]]))
            soundtrack.mix_into_video(silent, music, tracks, final)
        except Exception as exc:
            log(f"Bande-son non ajoutée : {exc}")
            final = silent
        with open(final, "rb") as fh:
            return fh.read(), duration


def dump(data: dict) -> str:
    """Données lisibles (débogage, tests)."""
    return json.dumps(data, ensure_ascii=False, indent=1)
