"""Audit léger d'un site prospect, sans dépendance externe supplémentaire.

L'objectif n'est pas de remplacer Lighthouse mais de détecter rapidement les
signaux utiles à la vente Local Pulse: technique, SEO local et conversion.
"""
from __future__ import annotations

import datetime
import re
import time
from html import unescape
from urllib.parse import urlparse

import requests


USER_AGENT = "Mozilla/5.0 (compatible; LocalPulseAudit/1.0; +https://local-pulse)"
MAX_HTML_BYTES = 2_000_000


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url
    return url


def _has(pattern: str, text: str) -> bool:
    return bool(re.search(pattern, text, flags=re.I | re.S))


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", unescape(m.group(1))).strip()[:180]


def _grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "E"


def audit_website(url: str, timeout: int = 10) -> dict:
    normalized = _normalize_url(url)
    audited_at = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    if not normalized:
        return {
            "status": "no_website", "score": 0, "grade": "E",
            "issues": [{"severity": "high", "title": "Aucun site", "recommendation": "Créer un site orienté conversion locale."}],
            "audited_at": audited_at,
        }

    try:
        started = time.perf_counter()
        response = requests.get(
            normalized,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
    except Exception as exc:
        return {
            "status": "error", "url": normalized, "score": 0, "grade": "E",
            "error": str(exc)[:250], "audited_at": audited_at,
            "issues": [{"severity": "high", "title": "Site inaccessible", "recommendation": "Vérifier la disponibilité, le DNS et l'hébergement."}],
        }

    raw = response.content[:MAX_HTML_BYTES]
    try:
        html = raw.decode(response.encoding or "utf-8", errors="ignore")
    except Exception:
        html = raw.decode("utf-8", errors="ignore")
    lower = html.lower()
    final_url = response.url
    parsed = urlparse(final_url)

    checks = {
        "reachable": 200 <= response.status_code < 400,
        "https": parsed.scheme == "https",
        "fast_response": elapsed_ms <= 2500,
        "viewport": _has(r'<meta[^>]+name=["\']viewport["\']', html),
        "title": bool(_extract_title(html)),
        "meta_description": _has(r'<meta[^>]+name=["\']description["\'][^>]+content=', html) or _has(r'<meta[^>]+content=[^>]+name=["\']description["\']', html),
        "h1": _has(r"<h1\b", html),
        "local_business_schema": "localbusiness" in lower or "restaurant" in lower and "application/ld+json" in lower,
        "phone_cta": _has(r'href=["\']tel:', html),
        "whatsapp": "wa.me/" in lower or "api.whatsapp.com" in lower,
        "form": _has(r"<form\b", html),
        "booking": any(k in lower for k in ("réserver", "reserver", "reservation", "rendez-vous", "prendre rendez", "booking")),
        "cta": any(k in lower for k in ("demander un devis", "contactez-nous", "contactez nous", "appelez", "réserver", "prendre rendez", "commander")),
        "social": any(k in lower for k in ("instagram.com/", "facebook.com/", "linkedin.com/", "tiktok.com/")),
        "testimonials": any(k in lower for k in ("avis client", "témoignage", "temoignage", "nos clients", "google reviews")),
        "legal": any(k in lower for k in ("mentions légales", "mentions legales", "politique de confidentialité", "privacy policy")),
        "contact_context": any(k in lower for k in ("adresse", "contact", "horaires", "nous trouver")),
    }

    technical = (
        (10 if checks["reachable"] else 0)
        + (7 if checks["https"] else 0)
        + (5 if checks["fast_response"] else 0)
        + (3 if checks["viewport"] else 0)
    )
    seo = (
        (8 if checks["title"] else 0)
        + (7 if checks["meta_description"] else 0)
        + (5 if checks["h1"] else 0)
        + (5 if checks["local_business_schema"] else 0)
    )
    conversion = (
        (8 if checks["phone_cta"] else 0)
        + (5 if checks["whatsapp"] else 0)
        + (7 if checks["form"] else 0)
        + (5 if checks["booking"] else 0)
        + (5 if checks["cta"] else 0)
    )
    trust = (
        (5 if checks["social"] else 0)
        + (5 if checks["testimonials"] else 0)
        + (5 if checks["legal"] else 0)
        + (5 if checks["contact_context"] else 0)
    )
    score = float(technical + seo + conversion + trust)

    issue_specs = [
        ("https", "high", "HTTPS absent", "Passer tout le site en HTTPS."),
        ("viewport", "high", "Mobile non optimisé", "Ajouter un viewport responsive et vérifier l'affichage mobile."),
        ("meta_description", "medium", "Meta description absente", "Ajouter une description locale claire et orientée clic."),
        ("local_business_schema", "medium", "Schema LocalBusiness absent", "Ajouter des données structurées LocalBusiness adaptées au commerce."),
        ("phone_cta", "high", "Appel en 1 clic absent", "Ajouter un bouton téléphone visible, surtout sur mobile."),
        ("form", "medium", "Formulaire de contact absent", "Ajouter un formulaire court de demande de devis/contact."),
        ("cta", "high", "CTA commercial faible", "Ajouter un appel à l'action principal visible au-dessus de la ligne de flottaison."),
        ("testimonials", "medium", "Preuve sociale faible", "Mettre en avant les avis et témoignages clients."),
        ("legal", "low", "Pages légales non détectées", "Ajouter les mentions légales et la politique de confidentialité."),
    ]
    issues = [
        {"severity": severity, "title": title, "recommendation": recommendation}
        for key, severity, title, recommendation in issue_specs
        if not checks.get(key)
    ]
    if elapsed_ms > 2500:
        issues.append({"severity": "medium", "title": "Réponse serveur lente", "recommendation": "Optimiser l'hébergement, les images et le cache."})

    strengths = []
    if checks["https"]:
        strengths.append("HTTPS actif")
    if checks["viewport"]:
        strengths.append("Base mobile détectée")
    if checks["phone_cta"]:
        strengths.append("Appel en 1 clic")
    if checks["local_business_schema"]:
        strengths.append("Données structurées locales")
    if checks["testimonials"]:
        strengths.append("Preuve sociale visible")

    return {
        "status": "ok" if checks["reachable"] else "http_error",
        "url": normalized,
        "final_url": final_url,
        "http_status": response.status_code,
        "response_time_ms": elapsed_ms,
        "title": _extract_title(html),
        "score": score,
        "grade": _grade(score),
        "sections": {
            "technical": {"score": technical, "max": 25},
            "seo_local": {"score": seo, "max": 25},
            "conversion": {"score": conversion, "max": 30},
            "trust": {"score": trust, "max": 20},
        },
        "checks": checks,
        "issues": issues,
        "strengths": strengths,
        "audited_at": audited_at,
    }
