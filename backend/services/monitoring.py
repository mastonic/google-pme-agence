"""
Supervision des sites déployés ("tour de contrôle").

Trois vérifications, exécutables à la demande ou en boucle planifiée :
  - SSL : certificat valide et jours avant expiration ;
  - Avis Google : note + nombre d'avis en temps quasi réel (delta vs dernier relevé) ;
  - SEO : présence des éléments clés sur la page en ligne (title, meta description,
    JSON-LD, H1, sitemap accessible) -> score /100.

Tout est tolérant aux pannes : une vérification en échec n'interrompt pas les autres.
"""
import ssl
import socket
import datetime
from urllib.parse import urlparse

import requests


def check_ssl(url: str) -> dict:
    if not url:
        return {"status": "unknown", "detail": "Pas d'URL"}
    host = urlparse(url).hostname
    if not host:
        return {"status": "unknown", "detail": "URL invalide"}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_left = (not_after - datetime.datetime.utcnow()).days
        status = "ok" if days_left > 14 else ("warning" if days_left > 0 else "error")
        return {"status": status, "days_left": days_left, "expires": not_after.date().isoformat()}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def check_reviews(maps_service, place_id: str, previous: dict = None) -> dict:
    """Compare la note et le nombre d'avis Google au dernier relevé."""
    previous = previous or {}
    try:
        details = maps_service.get_business_details(place_id)
        if isinstance(details, dict) and "error" in details:
            return {"status": "error", "detail": details["error"]}
        rating = details.get("rating") or 0
        total = int(details.get("user_ratings_total") or 0)
        prev_total = int(previous.get("total") or 0)
        prev_rating = float(previous.get("rating") or 0)
        new_reviews = max(0, total - prev_total) if prev_total else 0
        rating_delta = round(rating - prev_rating, 2) if prev_rating else 0
        return {
            "status": "ok",
            "rating": rating,
            "total": total,
            "new_reviews": new_reviews,
            "rating_delta": rating_delta,
            "reviews": details.get("reviews", [])[:3],
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def check_seo(url: str) -> dict:
    if not url:
        return {"status": "unknown", "score": 0, "checks": {}}
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "LocalPulseMonitor/1.0"})
        html_text = resp.text or ""
        low = html_text.lower()
        checks = {
            "title": "<title>" in low and len(html_text.split("<title>")[1].split("</title>")[0].strip()) > 5 if "<title>" in low else False,
            "meta_description": 'name="description"' in low,
            "og_tags": 'property="og:' in low,
            "json_ld": "application/ld+json" in low,
            "h1": "<h1" in low,
            "viewport": 'name="viewport"' in low,
            "https": url.startswith("https"),
        }
        # sitemap accessible ?
        try:
            base = f"{urlparse(url).scheme}://{urlparse(url).hostname}"
            sm = requests.get(base + "/sitemap.xml", timeout=8)
            checks["sitemap"] = sm.status_code == 200
        except Exception:
            checks["sitemap"] = False
        score = int(100 * sum(1 for v in checks.values() if v) / len(checks))
        status = "ok" if score >= 80 else ("warning" if score >= 50 else "error")
        return {"status": status, "score": score, "checks": checks, "http_status": resp.status_code}
    except Exception as e:
        return {"status": "error", "score": 0, "detail": str(e)}


def run_monitoring(business, maps_service=None) -> dict:
    """
    Lance les trois contrôles pour un commerce et renvoie un rapport agrégé.
    `business` est une instance SQLAlchemy Business.
    """
    site_url = getattr(business, "deployment_url", None) or ""
    previous = (getattr(business, "monitoring", None) or {}).get("reviews", {})

    report = {
        "checked_at": datetime.datetime.utcnow().isoformat(),
        "ssl": check_ssl(site_url),
        "seo": check_seo(site_url),
    }
    if maps_service is not None and getattr(business, "id", None):
        report["reviews"] = check_reviews(maps_service, business.id, previous)
    else:
        report["reviews"] = {"status": "unknown", "detail": "Maps indisponible"}

    statuses = [report["ssl"].get("status"), report["seo"].get("status"), report["reviews"].get("status")]
    if "error" in statuses:
        report["overall"] = "error"
    elif "warning" in statuses:
        report["overall"] = "warning"
    elif all(s == "ok" for s in statuses):
        report["overall"] = "ok"
    else:
        report["overall"] = "partial"
    return report
