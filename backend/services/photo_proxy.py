"""Proxy photo sécurisé.

Problème corrigé : l'ancien filtre `any(h in url for h in allowed)` acceptait toute URL
contenant un nom d'hôte autorisé (ex. `https://attaquant.exemple/?places.googleapis.com`),
et la clé Google était stockée dans les URLs de photos.

Désormais :
- seules les URLs https dont l'hôte est exactement autorisé sont relayées ;
- pour Places, seul le chemin `/v1/places/{id}/photos/{ref}/media` est accepté ;
- la clé Google est ajoutée côté serveur (en-tête), jamais stockée ni exposée.
"""
import os
import re
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

PLACES_HOST = "places.googleapis.com"
STATIC_HOSTS = {"images.unsplash.com", "storage.googleapis.com", "fal.media"}
FAL_SUFFIX = ".fal.media"
PLACES_MEDIA_PATH = re.compile(r"^/v1/places/[^/]+/photos/[^/]+/media$")
# storage.googleapis.com héberge n'importe quel bucket public : seuls les buckets connus sont relayés
# (falserverless = images générées par fal.ai ; GCS_PHOTO_BUCKETS pour en ajouter, séparés par des virgules).
GCS_HOST = "storage.googleapis.com"
DEFAULT_GCS_BUCKETS = ("falserverless",)
# Hôtes acceptés en redirection (Places renvoie vers googleusercontent.com).
REDIRECT_SUFFIXES = (".googleusercontent.com",)


def _gcs_buckets() -> set[str]:
    extra = [b.strip() for b in os.getenv("GCS_PHOTO_BUCKETS", "").split(",") if b.strip()]
    return set(DEFAULT_GCS_BUCKETS) | set(extra)


def build_places_photo_url(photo_name: str, max_height: int = 800, max_width: int = 1200) -> str:
    """URL proxifiée (sans clé) pour une photo Places, à partir de sa ressource `name`."""
    media = f"https://{PLACES_HOST}/v1/{photo_name}/media?maxHeightPx={max_height}&maxWidthPx={max_width}"
    return f"/photo?url={quote(media, safe='')}"


def validate_photo_url(url: str) -> tuple[bool, str]:
    """Retourne (autorisé, raison)."""
    try:
        parsed = urlparse(url or "")
    except ValueError:
        return False, "URL malformée"
    if parsed.scheme != "https":
        return False, "schéma non autorisé"
    host = (parsed.hostname or "").lower()
    if host == PLACES_HOST:
        if not PLACES_MEDIA_PATH.match(parsed.path or ""):
            return False, "chemin Places non autorisé"
        return True, "ok"
    if host == GCS_HOST:
        bucket = (parsed.path or "/").lstrip("/").split("/", 1)[0]
        if bucket not in _gcs_buckets():
            return False, "bucket non autorisé"
        return True, "ok"
    if host in STATIC_HOSTS or host.endswith(FAL_SUFFIX):
        return True, "ok"
    return False, "hôte non autorisé"


def validate_redirect_url(url: str) -> bool:
    """Cible de redirection acceptable : un hôte d'images autorisé, en https."""
    ok, _ = validate_photo_url(url)
    if ok:
        return True
    try:
        parsed = urlparse(url or "")
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(host.endswith(sfx) for sfx in REDIRECT_SUFFIXES)


def upstream_headers(url: str) -> dict:
    """En-têtes de la requête amont : la clé Google n'est envoyée qu'à Places."""
    if (urlparse(url).hostname or "").lower() == PLACES_HOST:
        return {"X-Goog-Api-Key": os.getenv("GOOGLE_MAPS_API_KEY", "")}
    return {}


def strip_api_key(url: str) -> str:
    """Retire un éventuel paramètre `key=` d'une URL (données historiques)."""
    parsed = urlparse(url)
    if not parsed.query:
        return url
    kept = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k != "key"]
    return urlunparse(parsed._replace(query=urlencode(kept)))
