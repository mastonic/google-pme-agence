"""Balisage SEO / AEO / GEO des démos générées.

Injecté côté code (et non demandé au LLM) pour garantir la présence des balises.
Règle : uniquement des données réelles fournies par Google Places. Aucune note,
aucun avis, aucun horaire n'est inventé. `aggregateRating` n'est pas émis : Google
n'accepte les notes agrégées que pour des avis affichés sur la page elle-même.
"""
import datetime
import html as html_lib
import json
import re
import unicodedata

SCHEMA_TYPE_BY_GOOGLE_TYPE = {
    "plumber": "Plumber",
    "electrician": "Electrician",
    "roofing_contractor": "RoofingContractor",
    "locksmith": "Locksmith",
    "painter": "HousePainter",
    "general_contractor": "GeneralContractor",
    "hvac_contractor": "HVACBusiness",
    "moving_company": "MovingCompany",
    "restaurant": "Restaurant",
    "cafe": "CafeOrCoffeeShop",
    "bakery": "Bakery",
    "hair_care": "HairSalon",
    "beauty_salon": "BeautySalon",
    "dentist": "Dentist",
    "doctor": "Physician",
    "pharmacy": "Pharmacy",
    "car_repair": "AutoRepair",
    "hotel": "Hotel",
    "lodging": "LodgingBusiness",
}


def schema_type_for(google_types) -> str:
    for t in google_types or []:
        if t in SCHEMA_TYPE_BY_GOOGLE_TYPE:
            return SCHEMA_TYPE_BY_GOOGLE_TYPE[t]
    return "LocalBusiness"


def _esc(value) -> str:
    return html_lib.escape(str(value or ""), quote=True)


def _truncate(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _city(address: str) -> str:
    """Dernier segment « 97200 Fort-de-France » → « Fort-de-France » (best effort)."""
    parts = [p.strip() for p in (address or "").split(",") if p.strip()]
    if not parts:
        return ""
    return re.sub(r"^\d{4,5}\s*", "", parts[-1]).strip()


def build_head_tags(biz: dict, sector_label: str) -> str:
    name = biz.get("name") or "Commerce"
    address = biz.get("address") or ""
    phone = biz.get("phone") or biz.get("business_phone") or ""
    city = _city(address)
    lat, lng = biz.get("latitude"), biz.get("longitude")
    place_id = biz.get("business_id") or biz.get("id") or ""

    title = f"{name} — {sector_label}" + (f" à {city}" if city else "")
    description = _truncate(
        f"{name}, {sector_label.lower()}" + (f" à {city}" if city else "")
        + (f" ({address})" if address else "") + ". Contact et demande de devis par téléphone.",
        160,
    )

    tags = [
        f"<title>{_esc(title)}</title>",
        f'<meta name="description" content="{_esc(description)}">',
        '<meta name="robots" content="index, follow">',
        '<meta property="og:type" content="website">',
        '<meta property="og:locale" content="fr_FR">',
        f'<meta property="og:title" content="{_esc(title)}">',
        f'<meta property="og:description" content="{_esc(description)}">',
    ]
    if lat is not None and lng is not None:
        tags += [
            f'<meta name="geo.position" content="{lat};{lng}">',
            f'<meta name="ICBM" content="{lat}, {lng}">',
        ]
    if address:
        tags.append(f'<meta name="geo.placename" content="{_esc(address)}">')
    if place_id:
        tags.append(f'<link rel="alternate" href="https://www.google.com/maps/place/?q=place_id:{_esc(place_id)}">')

    schema = {
        "@context": "https://schema.org",
        "@type": schema_type_for(biz.get("types") or biz.get("category") or []),
        "name": name,
        "address": {"@type": "PostalAddress", "streetAddress": address},
        "areaServed": city or None,
    }
    if phone:
        schema["telephone"] = phone
    if lat is not None and lng is not None:
        schema["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lng}
    if place_id:
        schema["sameAs"] = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    schema = {k: v for k, v in schema.items() if v is not None}

    payload = json.dumps(schema, ensure_ascii=False).replace("</", "<\\/")
    tags.append(f'<script type="application/ld+json">{payload}</script>')
    return "\n".join(tags)


def inject_seo_head(page: str, biz: dict, sector_label: str) -> str:
    """Remplace title/description existants et insère les balises dans <head>."""
    if not page:
        return page
    out = re.sub(r"<title[^>]*>.*?</title>", "", page, flags=re.I | re.S)
    out = re.sub(r'<meta[^>]+name=["\']description["\'][^>]*>', "", out, flags=re.I)
    out = re.sub(r'<meta[^>]+name=["\']robots["\'][^>]*>', "", out, flags=re.I)

    if re.search(r"<html\b[^>]*\blang=", out, flags=re.I) is None:
        out = re.sub(r"<html\b", '<html lang="fr"', out, count=1, flags=re.I)

    head_block = build_head_tags(biz, sector_label)
    if re.search(r"<head\b[^>]*>", out, flags=re.I):
        out = re.sub(r"(<head\b[^>]*>)", lambda m: m.group(1) + "\n" + head_block, out, count=1, flags=re.I)
    else:
        out = re.sub(r"(<html\b[^>]*>)", lambda m: m.group(1) + "\n<head>\n" + head_block + "\n</head>", out,
                     count=1, flags=re.I)

    if re.search(r'<meta[^>]+name=["\']viewport["\']', out, flags=re.I) is None:
        out = re.sub(r"(<head\b[^>]*>)",
                     lambda m: m.group(1) + '\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                     out, count=1, flags=re.I)
    return out


def vercel_project_slug(project_name: str) -> str:
    """Même normalisation que VercelDeployTool (nom de projet → sous-domaine)."""
    normalized = unicodedata.normalize("NFKD", project_name or "local-pulse-site")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "-", normalized).strip("-._").lower()
    clean = re.sub(r"-{2,}", "-", clean)[:90]
    return clean or "local-pulse-site"


def build_robots_txt(sitemap_url: str | None = None) -> str:
    lines = ["User-agent: *", "Allow: /"]
    if sitemap_url:
        lines.append(f"Sitemap: {sitemap_url}")
    return "\n".join(lines) + "\n"


def build_sitemap_xml(url: str, when: datetime.date | None = None) -> str:
    when = when or datetime.date.today()
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{_esc(url)}</loc><lastmod>{when.isoformat()}</lastmod></url>\n"
        "</urlset>\n"
    )


def build_llms_txt(biz: dict, sector_label: str) -> str:
    name = biz.get("name") or "Commerce"
    address = biz.get("address") or ""
    phone = biz.get("phone") or biz.get("business_phone") or ""
    lines = [
        f"# {name}",
        "",
        f"> {name} est un(e) {sector_label.lower()}" + (f" situé(e) à {address}." if address else "."),
        "",
        "## Informations",
        f"- Activité : {sector_label}",
    ]
    if address:
        lines.append(f"- Adresse : {address}")
    if phone:
        lines.append(f"- Téléphone : {phone}")
    if biz.get("rating") and biz.get("user_ratings_total"):
        lines.append(f"- Avis Google : {biz['rating']}/5 ({int(biz['user_ratings_total'])} avis)")
    lines += ["", "## Contact", "- Par téléphone ou via le formulaire de la page d'accueil."]
    return "\n".join(lines) + "\n"
