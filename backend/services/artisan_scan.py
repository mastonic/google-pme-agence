"""Branchement de la découverte par métier (artisan_discovery) sur le format de scan existant.

Activé uniquement si ARTISAN_DISCOVERY_ENABLED=true : chaque passage complet coûte
des centaines à des milliers de requêtes Text Search (voir docs/RAPPORT_TECHNIQUE.md, §7.4).
Le format retourné est celui de `GoogleMapsService.search_nearby_businesses`, plus `trades`.
"""
import os

from backend.services.artisan_discovery import (
    bbox_from_radius,
    discover_trades,
    grid,
    haversine_m,
    make_places_transport,
    select_trades,
)

CELL_KM = 10.0


def discovery_enabled() -> bool:
    return os.getenv("ARTISAN_DISCOVERY_ENABLED", "false").strip().lower() == "true"


def to_scan_place(entry: dict) -> dict:
    """Convertit un résultat Places (New) brut en forme attendue par le scan."""
    place = entry["place"]
    display = place.get("displayName") or {}
    location = place.get("location") or {}
    return {
        "place_id": place.get("id"),
        "name": display.get("text", ""),
        "vicinity": place.get("formattedAddress", ""),
        "geometry": {"location": {"lat": location.get("latitude"), "lng": location.get("longitude")}},
        "rating": place.get("rating", 0.0),
        "user_ratings_total": place.get("userRatingCount", 0),
        "types": place.get("types", []),
        "trades": entry.get("trades", []),
    }


def discover_artisans(lat: float, lng: float, radius_m: float, query: str | None = None,
                      api_key: str | None = None) -> list[dict]:
    """Scan par métier dans le cercle (lat, lng, rayon). Lève RuntimeError si l'API échoue."""
    key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY non configurée")

    south, west, north, east = bbox_from_radius(lat, lng, radius_m)
    cell_km = min(CELL_KM, max(0.5, 2 * radius_m / 1000))
    cells = grid(south, west, north, east, cell_km=cell_km)
    result = discover_trades(make_places_transport(key), cells, select_trades(query))

    places = []
    for entry in result["places"].values():
        scan_place = to_scan_place(entry)
        loc = scan_place["geometry"]["location"]
        if loc["lat"] is None or loc["lng"] is None:
            continue
        # Le rectangle englobe le cercle : on écarte les lieux hors rayon.
        if haversine_m(lat, lng, loc["lat"], loc["lng"]) > radius_m:
            continue
        places.append(scan_place)

    if result["incomplete_cells"]:
        print(f"⚠️ Découverte artisans : {result['incomplete_cells']} cellule(s) saturée(s) à profondeur max")
    print(f"✅ Découverte artisans : {len(places)} lieux dans le rayon ({result['queries']} requêtes de base)")
    return places
