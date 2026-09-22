"""Scoring commercial Local Pulse.

Deux scores indépendants:
- Digital Health (0-100): qualité de la présence digitale.
- Opportunity Score (0-100): priorité commerciale pour l'agence.

Le score d'opportunité favorise les commerces avec une demande réelle
(bonne note + volume d'avis) mais un déficit digital exploitable.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable


HIGH_VALUE_SECTORS = {
    "dentist", "dental", "doctor", "medical", "clinic", "lawyer", "attorney",
    "real_estate", "insurance", "accounting", "finance", "roofing_contractor",
    "general_contractor", "electrician", "plumber", "hvac", "car_dealer",
    "car_repair", "hotel", "lodging", "spa", "beauty_salon",
}
MEDIUM_VALUE_SECTORS = {
    "restaurant", "cafe", "bakery", "bar", "gym", "physiotherapist",
    "veterinary_care", "store", "florist", "furniture_store", "jewelry_store",
    "travel_agency", "moving_company", "cleaning", "hair_care",
}


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _categories(data: Dict[str, Any]) -> set[str]:
    raw = data.get("category") or data.get("types") or []
    if isinstance(raw, str):
        raw = [raw]
    return {str(x).strip().lower() for x in raw if x}


def _photos_count(data: Dict[str, Any]) -> int:
    photos = data.get("photos") or []
    return len(photos) if isinstance(photos, list) else int(bool(photos))


def _review_points(total: int, max_points: float) -> float:
    """Courbe logarithmique: différencie 5, 20, 100, 500 avis sans explosion."""
    if total <= 0:
        return 0.0
    # 500 avis ~= max; au-delà on plafonne.
    ratio = min(1.0, math.log10(total + 1) / math.log10(501))
    return round(max_points * ratio, 1)


def _sector_value(categories: Iterable[str]) -> tuple[float, str]:
    cats = set(categories)
    if cats & HIGH_VALUE_SECTORS:
        return 15.0, "forte"
    if cats & MEDIUM_VALUE_SECTORS:
        return 11.0, "moyenne"
    if cats:
        return 8.0, "standard"
    return 5.0, "inconnue"


def calculate_digital_health(data: Dict[str, Any], website_audit: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Retourne un score de santé digitale 0-100 et son détail."""
    website = bool(data.get("website"))
    rating = float(data.get("rating") or 0)
    reviews = int(data.get("user_ratings_total") or 0)
    photos = _photos_count(data)
    phone = data.get("business_phone") or data.get("phone") or data.get("formatted_phone_number")
    email = data.get("owner_email") or data.get("contact_email")

    criteria = []
    recommendations = []
    score = 0.0

    # Présence web — 15 pts
    web_presence = 15.0 if website else 0.0
    score += web_presence
    criteria.append({
        "label": "Présence web", "pts": web_presence, "max": 15.0,
        "status": "ok" if website else "missing",
        "detail": "Site détecté" if website else "Aucun site détecté",
    })
    if not website:
        recommendations.append({"icon": "🌐", "action": "Créer une présence web orientée conversion", "gain": 15.0})

    # Qualité du site — 35 pts. Tant qu'il n'est pas audité on ne lui attribue
    # qu'un crédit partiel, afin qu'un simple site existant ne paraisse pas excellent.
    if website and website_audit and website_audit.get("status") == "ok":
        audit_score = float(website_audit.get("score") or 0)
        quality = round(audit_score * 0.35, 1)
        q_status = "ok" if audit_score >= 75 else "partial" if audit_score >= 45 else "low"
        q_detail = f"Audit site: {audit_score:.0f}/100"
    elif website:
        quality = 14.0
        q_status = "partial"
        q_detail = "Site non audité — qualité à confirmer"
        recommendations.append({"icon": "🔎", "action": "Lancer l'audit technique et conversion du site", "gain": 21.0})
    else:
        quality = 0.0
        q_status = "missing"
        q_detail = "Pas de site à auditer"
    score += quality
    criteria.append({"label": "Qualité du site", "pts": quality, "max": 35.0, "status": q_status, "detail": q_detail})

    # Réputation Google — 15 pts
    if rating <= 0:
        rep = 0.0
    elif rating >= 4.6:
        rep = 15.0
    elif rating >= 4.2:
        rep = 13.0
    elif rating >= 3.8:
        rep = 10.0
    elif rating >= 3.4:
        rep = 6.0
    else:
        rep = 2.0
    score += rep
    criteria.append({
        "label": "Réputation Google", "pts": rep, "max": 15.0,
        "status": "ok" if rep >= 13 else "partial" if rep >= 6 else "low",
        "detail": f"{rating:.1f}/5" if rating else "Aucune note",
    })

    # Volume d'avis — 15 pts
    review_score = _review_points(reviews, 15.0)
    score += review_score
    criteria.append({
        "label": "Volume d'avis", "pts": review_score, "max": 15.0,
        "status": "ok" if reviews >= 100 else "partial" if reviews >= 15 else "low",
        "detail": f"{reviews} avis",
    })
    if 0 < reviews < 50:
        recommendations.append({"icon": "💬", "action": "Augmenter le volume d'avis clients", "gain": round(15.0 - review_score, 1)})

    # Photos / fiche Google — 10 pts
    photo_score = 10.0 if photos >= 10 else 7.0 if photos >= 5 else 4.0 if photos else 0.0
    score += photo_score
    criteria.append({
        "label": "Photos Google", "pts": photo_score, "max": 10.0,
        "status": "ok" if photos >= 10 else "partial" if photos else "missing",
        "detail": f"{photos} photo(s)",
    })
    if photos < 5:
        recommendations.append({"icon": "📸", "action": "Renforcer les photos de la fiche Google", "gain": round(10.0 - photo_score, 1)})

    # Contactabilité — 10 pts
    contact = (6.0 if phone else 0.0) + (4.0 if email else 0.0)
    score += contact
    criteria.append({
        "label": "Contactabilité", "pts": contact, "max": 10.0,
        "status": "ok" if contact >= 10 else "partial" if contact else "missing",
        "detail": f"{'Téléphone ✓' if phone else 'Téléphone ✕'} · {'Email ✓' if email else 'Email ✕'}",
    })

    recommendations.sort(key=lambda r: r.get("gain", 0), reverse=True)
    return {
        "score": round(_clamp(score), 1),
        "criteria": criteria,
        "recommendations": recommendations,
    }


def calculate_opportunity_score(
    data: Dict[str, Any],
    digital_health: Dict[str, Any] | float,
    website_audit: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Score de priorité commerciale 0-100.

    Pondération:
      demande/réputation 30
      déficit digital     30
      contactabilité      15
      valeur secteur      15
      confiance données   10

    Une mauvaise note ou un volume d'avis quasi nul applique une pénalité:
    Local Pulse cherche un BON commerce mal équipé digitalement, pas un commerce
    structurellement faible.
    """
    dh = float(digital_health.get("score", 0) if isinstance(digital_health, dict) else digital_health)
    rating = float(data.get("rating") or 0)
    reviews = int(data.get("user_ratings_total") or 0)
    categories = _categories(data)
    phone = data.get("owner_phone") or data.get("business_phone") or data.get("phone") or data.get("formatted_phone_number")
    email = data.get("owner_email") or data.get("contact_email")
    website = data.get("website")

    # 1) Demande / preuve marché — 30
    if rating >= 4.6:
        rating_signal = 12.0
    elif rating >= 4.2:
        rating_signal = 11.0
    elif rating >= 3.8:
        rating_signal = 8.0
    elif rating >= 3.4:
        rating_signal = 4.0
    elif rating > 0:
        rating_signal = 1.0
    else:
        rating_signal = 0.0
    demand = round(rating_signal + _review_points(reviews, 18.0), 1)

    # 2) Déficit digital exploitable — 30
    digital_gap = round((100.0 - _clamp(dh)) * 0.30, 1)

    # 3) Contactabilité — 15
    contactability = 0.0
    if phone:
        contactability += 7.0
    if email:
        contactability += 6.0
    if website:
        contactability += 2.0

    # 4) Valeur économique du secteur — 15
    sector_value, sector_band = _sector_value(categories)

    # 5) Confiance / complétude — 10
    confidence = 0.0
    confidence += 2.0 if data.get("address") else 0.0
    confidence += 2.0 if rating > 0 else 0.0
    confidence += 2.0 if reviews > 0 else 0.0
    confidence += 2.0 if categories else 0.0
    confidence += 2.0 if (website or phone or _photos_count(data)) else 0.0

    raw = demand + digital_gap + contactability + sector_value + confidence

    # Garde-fous qualité business.
    penalty = 1.0
    penalty_reasons = []
    if rating and rating < 3.2:
        penalty *= 0.72
        penalty_reasons.append("note Google faible")
    if reviews < 3:
        penalty *= 0.82
        penalty_reasons.append("preuve de demande insuffisante")

    score = round(_clamp(raw * penalty), 1)
    if score >= 78:
        label = "hot"
    elif score >= 62:
        label = "strong"
    elif score >= 45:
        label = "medium"
    else:
        label = "low"

    components = [
        {"label": "Demande & réputation", "score": demand, "max": 30.0},
        {"label": "Déficit digital", "score": digital_gap, "max": 30.0},
        {"label": "Contactabilité", "score": contactability, "max": 15.0},
        {"label": "Valeur secteur", "score": sector_value, "max": 15.0, "detail": sector_band},
        {"label": "Confiance données", "score": confidence, "max": 10.0},
    ]

    return {
        "score": score,
        "label": label,
        "components": components,
        "penalty": round(penalty, 2),
        "penalty_reasons": penalty_reasons,
        "sector_band": sector_band,
        "website_audit_score": (website_audit or {}).get("score"),
    }


def calculate_scores(data: Dict[str, Any], website_audit: Dict[str, Any] | None = None) -> Dict[str, Any]:
    digital = calculate_digital_health(data, website_audit)
    opportunity = calculate_opportunity_score(data, digital, website_audit)
    return {"digital_health": digital, "opportunity": opportunity}
