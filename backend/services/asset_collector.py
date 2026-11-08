"""Collecte des contenus publics d'un commerce AVANT la génération des actifs numériques.

Pourquoi : un commerce sans site web (ex. « Fruity Boule ») a souvent son logo, sa carte
et ses produits sur Facebook / Instagram. Sans cette étape, le pipeline n'avait que la
fiche Google, puis basculait sur des images IA ou Pexels.

Étapes :
1. Trouver les pages Facebook / Instagram (liens du site, sinon Perplexity).
2. Récupérer profil, couverture et photos via Apify (APIFY_TOKEN déjà utilisé pour Maps).
3. Télécharger les images (les URLs fbcdn / cdninstagram expirent) et dédoublonner.
4. Trier chaque image avec Gemini Vision : logo, devanture, produit, menu, equipe, rejet ;
   lire les produits et prix sur les images de carte.

Le résultat est stocké par main.store_collected_assets() dans ClientMedia : les photos
apparaissent dans l'espace client (le client peut les retirer) et passent en priorité
dans la génération via client_assets().
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import urllib.parse

import requests

from backend.services.enrichment import PerplexityService, _safe_website_url

APIFY_BASE = "https://api.apify.com/v2/acts"
FB_PAGES_ACTOR = "apify~facebook-pages-scraper"
FB_PHOTOS_ACTOR = "apify~facebook-photos-scraper"
IG_PROFILE_ACTOR = "apify~instagram-profile-scraper"

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGES = int(os.getenv("ASSET_COLLECTOR_MAX_IMAGES", "24"))
VISION_MODEL = os.getenv("ASSET_COLLECTOR_VISION_MODEL", "gemini-3.8-flash")
KINDS = ("logo", "devanture", "produit", "menu", "equipe", "ambiance", "rejet")

FB_RE = re.compile(r"https?://(?:www\.|m\.|web\.)?(?:facebook|fb)\.com/[^\s\"'<>]+", re.I)
IG_RE = re.compile(r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)", re.I)
_FB_SKIP = ("sharer", "share.php", "plugins", "dialog", "tr?", "/policy", "/help", "login")

_MAGIC = ((b"\x89PNG", "image/png"), (b"\xff\xd8\xff", "image/jpeg"), (b"RIFF", "image/webp"),
          (b"GIF8", "image/gif"))


# ── 1. Trouver les réseaux ──────────────────────────────────────────────────

def clean_facebook_url(url: str) -> str:
    url = (url or "").strip().rstrip("/")
    if not url or not FB_RE.match(url) or any(s in url.lower() for s in _FB_SKIP):
        return ""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/")
    if not path or path == "/":
        return ""
    if path.startswith("/profile.php"):
        return f"https://www.facebook.com{path}?{parsed.query}" if parsed.query else ""
    return f"https://www.facebook.com{path}"


def instagram_username(url: str) -> str:
    m = IG_RE.match((url or "").strip())
    if not m:
        return ""
    user = m.group(1).strip(".")
    return "" if user.lower() in {"p", "reel", "explore", "accounts", "stories"} else user


def social_links_from_html(html: str) -> dict:
    out = {}
    for raw in FB_RE.findall(html or ""):
        fb = clean_facebook_url(raw)
        if fb:
            out.setdefault("facebook", fb)
    for m in IG_RE.finditer(html or ""):
        user = instagram_username(m.group(0))
        if user:
            out.setdefault("instagram", f"https://www.instagram.com/{user}")
    return out


def find_social_urls(name: str, address: str, website: str = "", known: dict | None = None) -> dict:
    """Retourne {"facebook": url, "instagram": url} (clés absentes si introuvable)."""
    found = {k: v for k, v in (known or {}).items() if k in ("facebook", "instagram") and v}
    site = _safe_website_url(website)
    if site and len(found) < 2:
        try:
            resp = requests.get(site, timeout=8, headers={"User-Agent": "Mozilla/5.0 LocalPulse"})
            if resp.status_code < 400:
                for k, v in social_links_from_html(resp.text).items():
                    found.setdefault(k, v)
        except requests.RequestException:
            pass
    perplexity = PerplexityService()
    if len(found) < 2 and perplexity.enabled:
        for k, v in _perplexity_socials(perplexity, name, address).items():
            found.setdefault(k, v)
    if found.get("facebook"):
        found["facebook"] = clean_facebook_url(found["facebook"])
    if found.get("instagram"):
        user = instagram_username(found["instagram"])
        found["instagram"] = f"https://www.instagram.com/{user}" if user else ""
    return {k: v for k, v in found.items() if v}


def _perplexity_socials(p: PerplexityService, name: str, address: str) -> dict:
    prompt = (f"Trouve la page Facebook officielle et le compte Instagram officiel du commerce "
              f"« {name} » situé à : {address}. Vérifie que le nom ET la ville correspondent. "
              'Réponds UNIQUEMENT en JSON : {"facebook": "", "instagram": ""}. '
              "Chaîne vide si tu n'es pas sûr. N'invente jamais d'URL.")
    try:
        resp = requests.post(p.URL, timeout=40,
                             headers={"Authorization": f"Bearer {p.key}", "Content-Type": "application/json"},
                             json={"model": p.model, "temperature": 0.1, "messages": [
                                 {"role": "system", "content": "Tu ne renvoies que du JSON valide."},
                                 {"role": "user", "content": prompt}]})
        if resp.status_code != 200:
            return {}
        data = p._extract_json(resp.json()["choices"][0]["message"]["content"])
        return {k: str(data.get(k) or "").strip() for k in ("facebook", "instagram") if data.get(k)}
    except Exception as e:  # noqa: BLE001 — la collecte ne doit jamais bloquer la génération
        print(f"Perplexity socials failed: {e}")
        return {}


# ── 2. Apify ────────────────────────────────────────────────────────────────

def _apify(actor: str, payload: dict, timeout: int = 150) -> list:
    token = os.getenv("APIFY_TOKEN")
    if not token:
        return []
    try:
        resp = requests.post(f"{APIFY_BASE}/{actor}/run-sync-get-dataset-items", json=payload,
                             params={"token": token, "timeout": timeout - 10, "memory": 1024},
                             timeout=timeout)
        if resp.status_code not in (200, 201):
            print(f"Apify {actor} erreur {resp.status_code}: {resp.text[:200]}")
            return []
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception as e:  # noqa: BLE001
        print(f"Apify {actor} échec : {e}")
        return []


def _first(d: dict, *keys) -> str:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.startswith("http"):
            return v
    return ""


def collect_facebook(page_url: str, photo_limit: int = 20) -> dict:
    out = {"images": [], "info": {}}
    pages = _apify(FB_PAGES_ACTOR, {"startUrls": [{"url": page_url}]})
    if pages:
        p = pages[0]
        logo = _first(p, "profilePictureUrl", "profilePhoto", "profilePicture")
        cover = _first(p, "coverPhotoUrl", "coverPhoto")
        if logo:
            out["images"].append({"url": logo, "hint": "logo", "source": "facebook"})
        if cover:
            out["images"].append({"url": cover, "hint": "cover", "source": "facebook"})
        intro = p.get("intro") or p.get("about") or p.get("description") or ""
        info = p.get("info") if isinstance(p.get("info"), list) else []
        out["info"] = {k: v for k, v in {
            "description": intro if isinstance(intro, str) else "",
            "phone": p.get("phone") or "",
            "email": p.get("email") or "",
            "address": p.get("address") or "",
            "hours": p.get("businessHours") or p.get("hours") or "",
            "categories": p.get("categories") or [],
            "about_lines": [str(x) for x in info][:10],
        }.items() if v}
    for item in _apify(FB_PHOTOS_ACTOR, {"startUrls": [{"url": page_url}], "resultsLimit": photo_limit}):
        url = _first(item, "image", "imageUrl", "url_image", "photoUrl")
        if url:
            out["images"].append({"url": url, "hint": (item.get("text") or "")[:120], "source": "facebook"})
    return out


def collect_instagram(profile_url: str, post_limit: int = 12) -> dict:
    out = {"images": [], "info": {}}
    user = instagram_username(profile_url)
    if not user:
        return out
    items = _apify(IG_PROFILE_ACTOR, {"usernames": [user], "resultsLimit": post_limit})
    if not items:
        return out
    p = items[0]
    logo = _first(p, "profilePicUrlHD", "profilePicUrl")
    if logo:
        out["images"].append({"url": logo, "hint": "logo", "source": "instagram"})
    for post in (p.get("latestPosts") or [])[:post_limit]:
        url = _first(post, "displayUrl") if isinstance(post, dict) else ""
        if url:
            out["images"].append({"url": url, "hint": (post.get("caption") or "")[:120], "source": "instagram"})
    if p.get("biography"):
        out["info"]["description"] = p["biography"]
    return out


# ── 3. Téléchargement ───────────────────────────────────────────────────────

def sniff(data: bytes) -> str | None:
    for magic, mime in _MAGIC:
        if data.startswith(magic) and (mime != "image/webp" or data[8:12] == b"WEBP"):
            return mime
    return None


def download_image(url: str) -> tuple[bytes, str] | None:
    try:
        resp = requests.get(url, timeout=15, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code >= 400:
            return None
        data = resp.raw.read(MAX_IMAGE_BYTES + 1, decode_content=True)
        if not data or len(data) > MAX_IMAGE_BYTES or len(data) < 4000:  # < 4 Ko : icône / pixel
            return None
        mime = sniff(data)
        return (data, mime) if mime else None
    except Exception:  # noqa: BLE001
        return None


# ── 4. Tri Gemini Vision ────────────────────────────────────────────────────

VISION_PROMPT = """Tu tries les images publiques d'un commerce local « {name} » pour construire son site.
Indice de la source : « {hint} ».
Classe l'image dans UNE catégorie :
- logo : logo ou visuel d'identité de la marque
- menu : carte, menu, tarifs, affiche de prix
- produit : produit, plat, boisson, réalisation en gros plan
- devanture : façade, enseigne, stand, camion, local vu de l'extérieur
- equipe : personne(s) du commerce au travail
- ambiance : intérieur, salle, événement
- rejet : flou, mème, capture d'écran, texte promotionnel sans intérêt, sans rapport avec le commerce, ou de mauvaise qualité
Si c'est un menu, liste les produits lisibles avec leur prix exact (n'invente rien).
Réponds UNIQUEMENT en JSON :
{{"kind": "...", "quality": 1-5, "alt": "description courte en français", "menu_items": [{{"name": "", "price": ""}}]}}"""


def _vision_model():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        return genai.GenerativeModel(VISION_MODEL)
    except Exception as e:  # noqa: BLE001
        print(f"Gemini Vision indisponible : {e}")
        return None


def parse_vision_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        data = {}
    kind = data.get("kind") if data.get("kind") in KINDS else "produit"
    try:
        quality = max(1, min(5, int(data.get("quality") or 3)))
    except (TypeError, ValueError):
        quality = 3
    items = [{"name": str(i.get("name")).strip(), "price": str(i.get("price") or "").strip()}
             for i in (data.get("menu_items") or []) if isinstance(i, dict) and str(i.get("name") or "").strip()]
    return {"kind": kind, "quality": quality, "alt": str(data.get("alt") or "")[:160], "menu_items": items[:40]}


def classify_image(model, name: str, data: bytes, mime: str, hint: str) -> dict:
    fallback = {"kind": "logo" if hint == "logo" else "produit", "quality": 3, "alt": "", "menu_items": []}
    if model is None:
        return fallback
    try:
        resp = model.generate_content([VISION_PROMPT.format(name=name, hint=hint or "aucun"),
                                       {"mime_type": mime, "data": data}])
        return parse_vision_json(getattr(resp, "text", ""))
    except Exception as e:  # noqa: BLE001
        print(f"Gemini Vision échec : {e}")
        return fallback


# ── Orchestration ───────────────────────────────────────────────────────────

def collect_assets(name: str, address: str, website: str = "", known_social: dict | None = None,
                   log=print) -> dict:
    """Collecte complète. Ne lève jamais : renvoie un dict éventuellement vide.

    {"social": {...}, "images": [{"data", "mime", "kind", "alt", "source", "quality"}],
     "menu": [...], "info": {...}, "collected_at": iso}
    """
    social = find_social_urls(name, address, website, known_social)
    log(f"🔗 Réseaux trouvés : {', '.join(f'{k} {v}' for k, v in social.items()) or 'aucun'}")
    raw, info = [], {}
    if social.get("facebook"):
        fb = collect_facebook(social["facebook"])
        raw += fb["images"]
        info.update(fb["info"])
    if social.get("instagram"):
        ig = collect_instagram(social["instagram"])
        raw += ig["images"]
        for k, v in ig["info"].items():
            info.setdefault(k, v)

    model = _vision_model()
    images, menu, seen = [], [], set()
    for item in raw[: MAX_IMAGES * 2]:
        if len(images) >= MAX_IMAGES:
            break
        got = download_image(item["url"])
        if not got:
            continue
        data, mime = got
        digest = hashlib.sha1(data).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        c = classify_image(model, name, data, mime, item.get("hint", ""))
        if c["kind"] == "rejet" or c["quality"] <= 1:
            continue
        menu += c["menu_items"]
        images.append({"data": data, "mime": mime, "kind": c["kind"], "alt": c["alt"],
                       "source": item["source"], "quality": c["quality"]})

    # Le meilleur logo d'abord ; puis par qualité.
    images.sort(key=lambda i: (i["kind"] != "logo", -i["quality"]))
    dedup_menu, names = [], set()
    for it in menu:
        key = it["name"].lower()
        if key not in names:
            names.add(key)
            dedup_menu.append(it)
    counts = {}
    for i in images:
        counts[i["kind"]] = counts.get(i["kind"], 0) + 1
    log(f"📸 {len(images)} images réelles retenues sur {len(raw)} trouvées "
        f"({', '.join(f'{k} {v}' for k, v in counts.items()) or 'aucune'}) ; {len(dedup_menu)} produits lus sur la carte")
    return {"social": social, "images": images, "menu": dedup_menu, "info": info,
            "collected_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"}
