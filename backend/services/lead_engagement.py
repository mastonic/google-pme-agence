"""Signaux d'engagement commercial Local Pulse.

Le score de chaleur combine fit commercial et comportement sur la démo.
Il ne prédit pas une vente: il sert uniquement à prioriser les relances.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict


def calculate_lead_heat(data: Dict[str, Any], now: datetime.datetime | None = None) -> Dict[str, Any]:
    now = now or datetime.datetime.utcnow()
    opportunity = max(0.0, min(100.0, float(data.get("opportunity_score") or 0)))
    views = max(0, int(data.get("demo_views") or 0))
    clicks = max(0, int(data.get("demo_interest_clicks") or 0))
    last_view = data.get("last_demo_view_at")

    score = opportunity * 0.60
    score += min(views, 4) * 6.0
    score += min(clicks, 1) * 12.0

    recent = False
    if isinstance(last_view, str):
        try:
            last_view = datetime.datetime.fromisoformat(last_view.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            last_view = None
    if isinstance(last_view, datetime.datetime):
        age = now - last_view
        if age.total_seconds() >= 0 and age <= datetime.timedelta(days=7):
            score += 4.0
            recent = True

    score = round(min(100.0, score), 1)
    if score >= 80:
        temperature = "hot"
    elif score >= 60:
        temperature = "warm"
    elif score >= 40:
        temperature = "cool"
    else:
        temperature = "cold"

    reasons = []
    if opportunity >= 70:
        reasons.append("fort potentiel commercial")
    if views >= 2:
        reasons.append(f"démo consultée {views} fois")
    if clicks > 0:
        reasons.append("clic d'intérêt sur la démo")
    if recent:
        reasons.append("activité récente")

    return {
        "score": score,
        "temperature": temperature,
        "reasons": reasons,
        "demo_views": views,
        "interest_clicks": clicks,
        "recent_view": recent,
    }


def default_onboarding_checklist() -> list[dict]:
    return [
        {"key": "offer", "label": "Offre validée avec le client", "done": True},
        {"key": "billing", "label": "Facturation / paiement configuré", "done": False},
        {"key": "contact", "label": "Coordonnées et interlocuteur confirmés", "done": False},
        {"key": "brand_assets", "label": "Logo, photos et éléments de marque récupérés", "done": False},
        {"key": "google_business", "label": "Accès Google Business Profile récupéré si nécessaire", "done": False},
        {"key": "domain", "label": "Domaine ou sous-domaine validé", "done": False},
        {"key": "production", "label": "Site / actifs validés pour mise en production", "done": False},
    ]


def onboarding_progress(checklist: list[dict] | None) -> dict:
    items = checklist or []
    if not items:
        return {"done": 0, "total": 0, "percent": 0, "completed": False}
    done = sum(1 for x in items if x.get("done"))
    total = len(items)
    return {
        "done": done,
        "total": total,
        "percent": round(done / total * 100),
        "completed": done == total,
    }
