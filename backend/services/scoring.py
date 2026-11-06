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


def _status(pts: float, mx: float) -> str:
    if mx <= 0 or pts <= 0:
        return "missing"
    ratio = pts / mx
    return "ok" if ratio >= 0.75 else "partial" if ratio >= 0.4 else "low"


def calculate_digital_health(data: Dict[str, Any], website_audit: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Retourne un score de santé digitale 0-100 et son détail.

    Barème (100 pts):
      Présence web 10 · Qualité du site 20 · Fiche Google Business 25
      SEO local 15 · AEO (moteurs de réponse) 10 · GEO (IA génératives) 10
      Contactabilité 10
    """
    website = bool(data.get("website"))
    rating = float(data.get("rating") or 0)
    reviews = int(data.get("user_ratings_total") or 0)
    photos = _photos_count(data)
    phone = data.get("business_phone") or data.get("phone") or data.get("formatted_phone_number")
    email = data.get("owner_email") or data.get("contact_email")
    address = data.get("address")
    categories = _categories(data)

    audited = bool(website and website_audit and website_audit.get("status") == "ok")
    checks: Dict[str, Any] = (website_audit or {}).get("checks") or {} if audited else {}
    sections: Dict[str, Any] = (website_audit or {}).get("sections") or {} if audited else {}

    def chk(key: str) -> bool:
        return bool(checks.get(key))

    criteria = []
    recommendations = []

    def add(label: str, pts: float, mx: float, detail: str, status: str | None = None):
        pts = round(max(0.0, min(mx, pts)), 1)
        criteria.append({"label": label, "pts": pts, "max": mx, "status": status or _status(pts, mx), "detail": detail})
        return pts

    def reco(icon: str, action: str, gain: float):
        if gain >= 0.5:
            recommendations.append({"icon": icon, "action": action, "gain": round(gain, 1)})

    score = 0.0

    # 1) Présence web — 10
    score_part = add("Présence web", 10.0 if website else 0.0, 10.0,
                           "Site détecté" if website else "Aucun site détecté")
    score += score_part
    if not website:
        reco("🌐", "Créer une présence web orientée conversion", 10.0)

    # 2) Qualité du site — 20 (technique + conversion + confiance de l'audit)
    if audited:
        sub = sum(float((sections.get(k) or {}).get("score") or 0) for k in ("technical", "conversion", "trust"))
        sub_max = sum(float((sections.get(k) or {}).get("max") or 0) for k in ("technical", "conversion", "trust")) or 75.0
        if not sections:  # ancien format d'audit : score global seulement
            sub, sub_max = float(website_audit.get("score") or 0), 100.0
        pts = 20.0 * sub / sub_max
        detail = f"Audit technique & conversion : {round(100 * sub / sub_max)}/100"
        if pts < 15:
            reco("🛠️", "Améliorer le site : mobile, vitesse, appel en 1 clic", 20.0 - pts)
    elif website:
        pts, detail = 8.0, "Site non audité — qualité à confirmer"
        reco("🔎", "Lancer l'audit technique, SEO, AEO et GEO du site", 12.0)
    else:
        pts, detail = 0.0, "Pas de site à auditer"
    score += add("Qualité du site", pts, 20.0, detail)

    # 3) Fiche Google Business — 25
    if rating <= 0:
        r_pts = 0.0
    elif rating >= 4.6:
        r_pts = 8.0
    elif rating >= 4.2:
        r_pts = 7.0
    elif rating >= 3.8:
        r_pts = 5.0
    elif rating >= 3.4:
        r_pts = 3.0
    else:
        r_pts = 1.0
    v_pts = _review_points(reviews, 8.0)
    p_pts = 5.0 if photos >= 10 else 3.5 if photos >= 5 else 2.0 if photos else 0.0
    c_pts = (1.0 if phone else 0) + (1.0 if address else 0) + (1.0 if categories else 0) + (1.0 if website else 0)
    gbp = r_pts + v_pts + p_pts + c_pts
    rating_txt = f"{rating:.1f}★" if rating else "sans note"
    score += add("Fiche Google Business", gbp, 25.0,
                 f"{rating_txt} · {reviews} avis · {photos} photo(s) · fiche complète {int(c_pts)}/4")
    if 0 < reviews < 50 or reviews == 0:
        reco("💬", "Augmenter le volume d'avis Google", 8.0 - v_pts)
    if photos < 10:
        reco("📸", "Renforcer les photos de la fiche Google", 5.0 - p_pts)
    if c_pts < 4:
        reco("📍", "Compléter la fiche Google (téléphone, catégorie, site)", 4.0 - c_pts)

    # 4) SEO local — 15
    if audited:
        if "seo_local" in sections:
            seo_raw = float(sections["seo_local"].get("score") or 0) / float(sections["seo_local"].get("max") or 25)
        else:
            seo_raw = ((8 if chk("title") else 0) + (7 if chk("meta_description") else 0)
                       + (5 if chk("h1") else 0) + (5 if chk("local_business_schema") else 0)) / 25
        seo = 15.0 * seo_raw
        missing = [n for k, n in (("title", "titre"), ("meta_description", "description"), ("h1", "H1"),
                                  ("local_business_schema", "schéma local")) if not chk(k)]
        detail = "Balises locales complètes" if not missing else "Manque : " + ", ".join(missing)
    elif website:
        seo, detail = 4.0, "Non audité"
    else:
        seo, detail = 0.0, "Aucun site à référencer"
    score += add("SEO local", seo, 15.0, detail)
    if seo < 11:
        reco("🔍", "Optimiser le SEO local (titres, description, schéma LocalBusiness)", 15.0 - seo)

    # 5) AEO — moteurs de réponse / assistants vocaux — 10
    if audited:
        aeo = ((3.0 if chk("faq") else 0) + (2.0 if chk("faq_schema") else 0)
               + (2.0 if chk("question_headings") else 0) + (2.0 if chk("opening_hours") else 0)
               + (1.0 if chk("structured_data") else 0))
        detail = " · ".join([
            "FAQ ✓" if chk("faq") else "FAQ ✕",
            "schéma FAQ ✓" if chk("faq_schema") else "schéma FAQ ✕",
            "horaires ✓" if chk("opening_hours") else "horaires ✕",
        ])
    elif website:
        aeo, detail = 2.0, "Non audité"
    else:
        aeo, detail = 0.0, "Aucun contenu pour les moteurs de réponse"
    score += add("AEO · moteurs de réponse", aeo, 10.0, detail)
    if aeo < 7:
        reco("🗣️", "Ajouter une FAQ structurée pour Google et les assistants vocaux", 10.0 - aeo)

    # 6) GEO — visibilité dans les IA génératives (ChatGPT, Gemini, Perplexity) — 10
    citations = 2.0 if reviews >= 50 else 1.0 if reviews >= 15 else 0.0
    if audited:
        geo = ((3.0 if chk("local_business_schema") else 1.0 if chk("structured_data") else 0)
               + (2.0 if chk("about") else 0)
               + (2.0 if (chk("social") or chk("same_as")) else 0)
               + (1.0 if chk("testimonials") else 0)
               + citations)
        detail = " · ".join([
            "données structurées ✓" if chk("structured_data") else "données structurées ✕",
            "page à propos ✓" if chk("about") else "page à propos ✕",
            f"{reviews} avis cités",
        ])
    else:
        geo = citations + (1.0 if website else 0.0)
        detail = f"Signaux limités aux avis Google ({reviews})" if not website else "Non audité"
    score += add("GEO · IA génératives", geo, 10.0, detail)
    if geo < 7:
        reco("🤖", "Rendre le commerce citable par ChatGPT et Gemini (données structurées, page à propos)", 10.0 - geo)

    # 7) Contactabilité — 10
    contact = (6.0 if phone else 0.0) + (4.0 if email else 0.0)
    score += add("Contactabilité", contact, 10.0,
                 f"{'Téléphone ✓' if phone else 'Téléphone ✕'} · {'Email ✓' if email else 'Email ✕'}")

    recommendations.sort(key=lambda r: r.get("gain", 0), reverse=True)
    return {
        "score": round(_clamp(score), 1),
        "criteria": criteria,
        "recommendations": recommendations[:5],
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
