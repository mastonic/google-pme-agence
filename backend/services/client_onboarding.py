"""Client onboarding + central business context for all agents."""
from __future__ import annotations
import datetime, secrets
from typing import Any
from backend.services.plans import PLAN_CATALOG

BASE_REQUIRED = [
    ("identity.logo_url", "Logo"),
    ("identity.business_name", "Nom commercial"),
    ("contact.phone", "Téléphone"),
    ("contact.email", "Email"),
    ("contact.address", "Adresse"),
    ("activity.services", "Services"),
    ("activity.hours", "Horaires"),
    ("goals.primary", "Objectif principal"),
]
PLAN_EXTRA = {
    "starter": [("media.photos", "Photos")],
    "pro": [
        ("media.photos", "Photos"),
        ("google.profile_url", "Fiche Google"),
        ("activity.service_areas", "Zones desservies"),
        ("goals.primary", "Objectif principal"),
    ],
    "elite": [
        ("media.photos", "Photos"),
        ("google.profile_url", "Fiche Google"),
        ("activity.service_areas", "Zones desservies"),
        ("brand.tone", "Ton de marque"),
        ("social", "Réseaux sociaux"),
        ("faq", "FAQ"),
        ("content.constraints", "Contraintes / éléments à éviter"),
    ],
}

def empty_profile(business=None) -> dict[str, Any]:
    return {
        "identity": {
            "business_name": getattr(business, "name", "") or "",
            "logo_url": "",
            "colors": [],
        },
        "contact": {
            "phone": getattr(business, "business_phone", "") or "",
            "email": getattr(business, "owner_email", "") or "",
            "address": getattr(business, "address", "") or "",
        },
        "activity": {"description": "", "services": [], "hours": {}, "service_areas": []},
        "brand": {"tone": "", "tagline": ""},
        "media": {"photos": [], "videos": []},
        "goals": {"primary": "", "secondary": []},
        "google": {"profile_url": "", "access_granted": False},
        "social": {"instagram": "", "facebook": "", "tiktok": "", "linkedin": ""},
        "faq": [],
        "content": {"constraints": [], "claims_to_avoid": []},
        "provenance": {},
    }

MAX_PROFILE_BYTES = 100_000
PROFILE_KEYS = ("identity", "contact", "activity", "brand", "media", "goals", "google", "social", "faq", "content")


def sanitize_profile_input(incoming) -> dict[str, Any]:
    """Profil envoyé par un formulaire public : sections connues uniquement, taille bornée,
    URL (logo, photos, vidéos, réseaux, fiche Google) en http(s) sans caractère dangereux."""
    import json as _json
    from backend.services.web_security import safe_http_url
    if not isinstance(incoming, dict):
        raise ValueError("profil invalide")
    if len(_json.dumps(incoming, default=str)) > MAX_PROFILE_BYTES:
        raise ValueError("profil trop volumineux")
    clean = {k: v for k, v in incoming.items() if k in PROFILE_KEYS and isinstance(v, (dict, list))}
    ident = clean.get("identity")
    if isinstance(ident, dict) and "logo_url" in ident:
        ident["logo_url"] = safe_http_url(ident.get("logo_url"))
    media = clean.get("media")
    if isinstance(media, dict):
        for kind in ("photos", "videos"):
            items = media.get(kind)
            if isinstance(items, list):
                out = []
                for it in items[:50]:
                    if isinstance(it, dict):
                        url = safe_http_url(it.get("url"))
                        if url:
                            out.append({**{k: v for k, v in it.items() if isinstance(v, (str, int, float, bool))}, "url": url})
                    elif safe_http_url(it):
                        out.append(safe_http_url(it))
                media[kind] = out
    social = clean.get("social")
    if isinstance(social, dict):
        clean["social"] = {k: safe_http_url(v) for k, v in social.items() if isinstance(k, str)}
    google = clean.get("google")
    if isinstance(google, dict) and "profile_url" in google:
        google["profile_url"] = safe_http_url(google.get("profile_url"))
    return clean


def merge_profile(business, incoming: dict[str, Any] | None = None, source="client_onboarding") -> dict[str, Any]:
    profile = business.client_profile if isinstance(getattr(business, "client_profile", None), dict) else empty_profile(business)
    incoming = incoming or {}
    def deep(dst, src, path=""):
        for k, v in src.items():
            p = f"{path}.{k}" if path else k
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                deep(dst[k], v, p)
            else:
                dst[k] = v
                profile.setdefault("provenance", {})[p] = {
                    "source": source, "verified": source == "client_onboarding",
                    "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
                }
    deep(profile, incoming)
    return profile

def _get(data, path):
    cur=data
    for part in path.split("."):
        if not isinstance(cur, dict): return None
        cur=cur.get(part)
    return cur

def onboarding_requirements(plan: str) -> list[dict[str, Any]]:
    seen=set(); out=[]
    for path,label in BASE_REQUIRED + PLAN_EXTRA.get(plan, PLAN_EXTRA["starter"]):
        if path in seen: continue
        seen.add(path); out.append({"path":path,"label":label})
    return out

def onboarding_progress(profile: dict[str, Any], plan: str) -> dict[str, Any]:
    req=onboarding_requirements(plan)
    missing=[]
    for item in req:
        value=_get(profile,item["path"])
        if value in (None,"",[],{}): missing.append(item)
    total=len(req); done=total-len(missing)
    pct=round(done/total*100,1) if total else 100.0
    return {"percent":pct,"complete":not missing,"missing":missing,"required":req}

def ensure_token(business) -> str:
    if not business.onboarding_token:
        business.onboarding_token=secrets.token_urlsafe(32)
    return business.onboarding_token

def agent_business_context(business) -> dict[str, Any]:
    profile = business.client_profile if isinstance(business.client_profile, dict) else empty_profile(business)
    return {
        "business_id": business.id,
        "name": business.name,
        "address": business.address,
        "website": business.website,
        "rating": business.rating,
        "reviews_count": business.user_ratings_total,
        "phone": business.business_phone,
        "owner_email": business.owner_email,
        "category": business.category or [],
        "plan_tier": business.plan_tier,
        "opportunity_score": business.opportunity_score,
        "digital_health_score": business.digital_health_score,
        "client_profile": profile,
        "onboarding": onboarding_progress(profile, business.plan_tier or "starter"),
    }


TEAM_REQUIRED = {
    "domain-watch": [],
    "seo-local": [
        ("activity.services", "Services"),
        ("activity.service_areas", "Zones desservies"),
        ("contact.address", "Adresse"),
        ("goals.primary", "Objectif principal"),
    ],
    "social-media": [
        ("activity.services", "Services"),
        ("brand.tone", "Ton de marque"),
        ("media.photos", "Photos"),
        ("goals.primary", "Objectif principal"),
    ],
}

def agent_team_readiness(business, team_slug: str) -> dict[str, Any]:
    profile = business.client_profile if isinstance(getattr(business, "client_profile", None), dict) else empty_profile(business)
    required = TEAM_REQUIRED.get(team_slug, [])
    missing = []
    for path, label in required:
        value = _get(profile, path)
        if value in (None, "", [], {}):
            missing.append({"path": path, "label": label})
    return {"ready": not missing, "missing": missing}
