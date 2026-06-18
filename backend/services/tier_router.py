"""
Tier router — selects prospecting strategy based on digital score.

Tier 1 (score ≤ 3.0)  : "Invisible"                — no web presence
Tier 2 (score ≤ 6.0)  : "Présence fragile"          — partial presence
Tier 3 (score ≤ 8.5)  : "Présent, non optimisé"     — visible but low conversion
None   (score > 8.5)  : "Hors cible"                — already well established
"""
from __future__ import annotations


def get_tier(score_data: dict) -> int | None:
    """Return 1, 2, 3 or None based on score and secondary criteria."""
    score = float(score_data.get("score") or 0)
    if score <= 3.0:  return 1
    if score <= 6.0:  return 2
    if score <= 8.5:  return 3
    return None


def build_score_data(biz: dict) -> dict:
    """Normalize a raw business dict into the canonical scoreData shape."""
    photos = biz.get("photos") or []
    return {
        "score":             float(biz.get("potential_score") or 0),
        "has_website":       bool(biz.get("website")),
        "nb_avis":           int(biz.get("user_ratings_total") or 0),
        "note_moyenne":      float(biz.get("rating") or 0),
        "has_photos":        (len(photos) > 0) if isinstance(photos, list) else False,
        "fiche_revendiquee": bool(biz.get("fiche_revendiquee")),
    }


TIER_LABELS = {
    1: "Invisible",
    2: "Présence fragile",
    3: "Présent, non optimisé",
}
