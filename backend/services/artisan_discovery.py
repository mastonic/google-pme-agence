"""Découverte exhaustive des artisans via Places API (New) — Text Search.

Pourquoi : `searchNearby` (utilisé par `GoogleMapsService.search_nearby_businesses`)
renvoie au maximum 20 établissements par cercle, sans pagination, triés par
importance générale. Un plombier peu populaire n'apparaît donc jamais.

Stratégie :
  1. on interroge par MÉTIER (requête texte « plombier », « serrurier »…),
     pas par « tout ce qui est autour » ;
  2. la zone est découpée en rectangles ; chaque rectangle est paginé (3 pages
     de 20 au maximum) ;
  3. si un rectangle sature (pages pleines, jeton de page restant), il est
     subdivisé en 4 jusqu'à une profondeur maximale, pour ne rien perdre.

Module volontairement pur : le transport HTTP est injecté (`transport(body) -> dict`),
ce qui le rend testable sans clé API et sans dépense.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable, Iterable

PAGE_SIZE = 20
MAX_PAGES = 3            # Text Search : pagination limitée (≈ 60 résultats par requête)
MAX_SPLIT_DEPTH = 4      # 4 niveaux de subdivision : 4^4 = 256 sous-rectangles au pire
KM_PER_DEGREE_LAT = 111.32

# Chaque métier a plusieurs formulations : les artisans se nomment différemment
# sur Google (« électricien », « dépannage électrique », « électricité générale »…).
# `included_type` est volontairement désactivé : Google rejette les types non
# supportés en Text Search (HTTP 400 « Invalid included_type »), constaté avec
# « general_contractor ». Le signal reste porté par les requêtes textuelles.
ARTISAN_TRADES = [
    {"slug": "plomberie", "queries": ["plombier", "dépannage plomberie"], "included_type": None},
    {"slug": "electricite", "queries": ["électricien", "dépannage électricité"], "included_type": None},
    {"slug": "couverture", "queries": ["couvreur", "toiture rénovation"], "included_type": None},
    {"slug": "serrurerie", "queries": ["serrurier", "dépannage serrurerie"], "included_type": None},
    {"slug": "peinture", "queries": ["peintre en bâtiment", "peintre décorateur"], "included_type": None},
    {"slug": "demenagement", "queries": ["déménageur"], "included_type": None},
    {"slug": "chauffage", "queries": ["chauffagiste", "dépannage chauffage"], "included_type": None},
    {"slug": "climatisation", "queries": ["climaticien", "installation climatisation"], "included_type": None},
    {"slug": "menuiserie", "queries": ["menuisier", "menuiserie aluminium"], "included_type": None},
    {"slug": "charpente", "queries": ["charpentier"], "included_type": None},
    {"slug": "maconnerie", "queries": ["maçon", "maçonnerie"], "included_type": None},
    {"slug": "carrelage", "queries": ["carreleur"], "included_type": None},
    {"slug": "plaquiste", "queries": ["plaquiste", "plâtrier"], "included_type": None},
    {"slug": "isolation", "queries": ["isolation thermique", "isolation combles"], "included_type": None},
    {"slug": "vitrerie", "queries": ["vitrier"], "included_type": None},
    {"slug": "ferronnerie", "queries": ["ferronnier", "serrurerie métallerie"], "included_type": None},
    {"slug": "paysagiste", "queries": ["paysagiste", "entretien espaces verts"], "included_type": None},
    {"slug": "elagage", "queries": ["élagueur"], "included_type": None},
    {"slug": "terrassement", "queries": ["terrassement", "location pelle travaux"], "included_type": None},
    {"slug": "pisciniste", "queries": ["pisciniste"], "included_type": None},
    {"slug": "cuisine_sdb", "queries": ["cuisiniste", "installateur salle de bain"], "included_type": None},
    {"slug": "portail", "queries": ["motorisation portail", "fermeture automatique"], "included_type": None},
    {"slug": "ramonage", "queries": ["ramoneur"], "included_type": None},
    {"slug": "nettoyage", "queries": ["nettoyage professionnel"], "included_type": None},
    {"slug": "renovation_generale", "queries": ["entreprise générale bâtiment", "entreprise de rénovation"], "included_type": None},
    {"slug": "depannage_domicile", "queries": ["dépannage à domicile", "artisan dépannage"], "included_type": None},
    # Cible transport : taxis (le filtre de type « taxi_stand » reste à vérifier dans la table Place types).
    {"slug": "taxi", "queries": ["taxi", "taxi conventionné", "taxi médical"], "included_type": None},
]


@dataclass(frozen=True)
class Rect:
    """Rectangle géographique (degrés décimaux)."""
    south: float
    west: float
    north: float
    east: float

    def split(self) -> list["Rect"]:
        mid_lat = (self.south + self.north) / 2
        mid_lng = (self.west + self.east) / 2
        return [
            Rect(self.south, self.west, mid_lat, mid_lng),
            Rect(self.south, mid_lng, mid_lat, self.east),
            Rect(mid_lat, self.west, self.north, mid_lng),
            Rect(mid_lat, mid_lng, self.north, self.east),
        ]

    def as_api(self) -> dict:
        return {
            "low": {"latitude": self.south, "longitude": self.west},
            "high": {"latitude": self.north, "longitude": self.east},
        }


def grid(south: float, west: float, north: float, east: float, cell_km: float = 2.0) -> list[Rect]:
    """Découpe une zone en cellules carrées d'environ `cell_km` de côté."""
    if south >= north or west >= east:
        raise ValueError("Zone invalide : sud < nord et ouest < est requis")
    if cell_km <= 0:
        raise ValueError("cell_km doit être strictement positif")

    lat_step = cell_km / KM_PER_DEGREE_LAT
    mid_lat = (south + north) / 2
    lng_step = cell_km / (KM_PER_DEGREE_LAT * max(math.cos(math.radians(mid_lat)), 1e-6))

    cells: list[Rect] = []
    lat = south
    while lat < north:
        lng = west
        while lng < east:
            cells.append(Rect(lat, lng, min(lat + lat_step, north), min(lng + lng_step, east)))
            lng += lng_step
        lat += lat_step
    return cells


def build_text_search_body(query: str, rect: Rect, included_type: str | None = None,
                           page_token: str | None = None) -> dict:
    """Corps de requête `places:searchText`. Seul `pageToken` varie entre les pages."""
    body: dict = {
        "textQuery": query,
        "pageSize": PAGE_SIZE,
        "languageCode": "fr",
        "regionCode": "FR",
        "locationRestriction": {"rectangle": rect.as_api()},
    }
    if included_type:
        body["includedType"] = included_type  # non strict : n'exclut aucun résultat
    if page_token:
        body["pageToken"] = page_token
    return body


Transport = Callable[[dict], dict]


def _fetch_rect(transport: Transport, query: str, rect: Rect, included_type: str | None,
                ) -> tuple[list[dict], bool]:
    """Pagine une requête sur un rectangle. Renvoie (résultats, saturé)."""
    places: list[dict] = []
    token: str | None = None
    for _ in range(MAX_PAGES):
        data = transport(build_text_search_body(query, rect, included_type, token)) or {}
        places.extend(data.get("places") or [])
        token = data.get("nextPageToken")
        if not token:
            return places, False
    # Pages épuisées avec un jeton restant : il reste des résultats non lus.
    return places, True


def discover_rect(transport: Transport, query: str, rect: Rect,
                  included_type: str | None = None, depth: int = 0) -> tuple[list[dict], int]:
    """Renvoie (résultats, nombre de rectangles restés incomplets à profondeur max)."""
    places, saturated = _fetch_rect(transport, query, rect, included_type)
    if not saturated:
        return places, 0
    if depth >= MAX_SPLIT_DEPTH:
        return places, 1

    collected: list[dict] = []
    incomplete = 0
    for sub in rect.split():
        sub_places, sub_incomplete = discover_rect(transport, query, sub, included_type, depth + 1)
        collected.extend(sub_places)
        incomplete += sub_incomplete
    return collected, incomplete


PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
# Champs minimum : téléphone et site relèvent de SKU plus chers, ils se récupèrent
# ensuite via Place Details uniquement pour les commerces retenus.
PLACES_FIELD_MASK = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.location",
    "places.rating", "places.userRatingCount", "places.types", "nextPageToken",
])


def make_places_transport(api_key: str, timeout: int = 15) -> Transport:
    """Transport HTTP réel vers `places:searchText` (Places API New)."""
    import requests

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": PLACES_FIELD_MASK,
    }

    def transport(body: dict) -> dict:
        response = requests.post(PLACES_TEXT_SEARCH_URL, headers=headers, json=body, timeout=timeout)
        data = response.json()
        if response.status_code != 200:
            message = (data.get("error") or {}).get("message", "erreur inconnue")
            raise RuntimeError(f"Places searchText HTTP {response.status_code} : {message}")
        return data

    return transport


def discover_trades(transport: Transport, cells: Iterable[Rect],
                    trades: list[dict] | None = None) -> dict:
    """Parcourt tous les métiers × formulations × cellules.

    Renvoie un dict :
      - `places` : {place_id: {"place": <résultat brut>, "trades": [slugs]}} dédupliqué
      - `incomplete_cells` : nombre de cellules encore saturées à profondeur max
      - `queries` : nombre de requêtes de base lancées (hors subdivisions)
    """
    trades = ARTISAN_TRADES if trades is None else trades
    cells = list(cells)
    found: dict[str, dict] = {}
    incomplete_total = 0
    queries_run = 0

    for trade in trades:
        for query in trade["queries"]:
            for cell in cells:
                queries_run += 1
                places, incomplete = discover_rect(transport, query, cell, trade.get("included_type"))
                incomplete_total += incomplete
                for place in places:
                    place_id = place.get("id")
                    if not place_id:
                        continue
                    entry = found.setdefault(place_id, {"place": place, "trades": []})
                    if trade["slug"] not in entry["trades"]:
                        entry["trades"].append(trade["slug"])

    return {"places": found, "incomplete_cells": incomplete_total, "queries": queries_run}


def bbox_from_radius(lat: float, lng: float, radius_m: float) -> tuple[float, float, float, float]:
    """Rectangle (sud, ouest, nord, est) englobant le cercle de rayon `radius_m`."""
    if radius_m <= 0:
        raise ValueError("radius_m doit être strictement positif")
    d_lat = (radius_m / 1000) / KM_PER_DEGREE_LAT
    d_lng = (radius_m / 1000) / (KM_PER_DEGREE_LAT * max(math.cos(math.radians(lat)), 1e-6))
    return lat - d_lat, lng - d_lng, lat + d_lat, lng + d_lng


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance orthodromique en mètres."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def select_trades(query: str | None, trades: list[dict] | None = None) -> list[dict]:
    """Filtre les métiers par un mot-clé libre (ex. « plomb »). Vide → tous les métiers."""
    trades = ARTISAN_TRADES if trades is None else trades
    term = (query or "").strip().lower()
    if not term:
        return list(trades)
    matched = [
        t for t in trades
        if term in t["slug"].lower() or any(term in q.lower() for q in t["queries"])
    ]
    return matched or list(trades)


def trades_for_metier(metier: str | None, trades: list[dict] | None = None) -> list[dict]:
    """Métiers à interroger pour une saisie libre (« plombier », « boulangerie »…).

    Un métier connu garde ses formulations ; sinon la saisie elle-même devient la
    requête Text Search. Contrairement à `select_trades`, une saisie inconnue ne
    déclenche jamais le scan de tous les métiers.
    """
    term = (metier or "").strip()
    if not term:
        return []
    low = term.lower()
    trades = ARTISAN_TRADES if trades is None else trades
    matched = [t for t in trades if low == t["slug"].lower() or any(low == q.lower() for q in t["queries"])]
    if not matched:
        matched = [t for t in trades if any(low in q.lower() for q in t["queries"])]
    if matched:
        return matched
    slug = re.sub(r"[^a-z0-9]+", "_", low).strip("_") or "metier"
    return [{"slug": slug, "queries": [term[:80]], "included_type": None}]
