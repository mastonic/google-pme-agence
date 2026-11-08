"""Régressions SEO multi-domaines : redirections Firebase, propriété des pages, API préservées.

Ces tests lisent uniquement la configuration (pas de build) : ils tournent en quelques ms.
Le contrôle des exports (canoniques, sitemaps, H1, liens) est fait par
landing-site/scripts/check-seo.mjs après chaque build.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "landing-site" / "app"
ORIGINS = {"fr": "https://pulse-locale-pme.fr", "info": "https://pulse-locale-pme.info", "store": "https://pulse-locale-pme.store"}
SITE_OF = {"pulse-locale-info": "info", "pulse-locale-store": "store"}
# Dossiers de app/ qui ne produisent pas de page publique du .fr.
NOT_PAGES = {"components", "seo", "local", "info", "store", "admin", "llms.txt"}


def owner_of(path: str) -> str:
    if path == "/info" or path.startswith("/info/"):
        return "info"
    if path == "/store" or path.startswith("/store/"):
        return "store"
    return "fr"


def fr_sections():
    """Premiers segments des pages du .fr (dossiers de app/ contenant une page)."""
    out = set()
    for d in APP.iterdir():
        if d.is_dir() and d.name not in NOT_PAGES and not d.name.startswith(("(", "_", "[")) and any(d.rglob("page.tsx")):
            out.add(d.name)
    return out


def resolve(redirects, path):
    """Applique la première redirection qui correspond (même sémantique que Firebase pour ces règles)."""
    for r in redirects:
        if "source" in r and r["source"] == path:
            return r["type"], r["destination"]
        if "regex" in r:
            m = re.match(r["regex"].replace("(?P<", "(?P<"), path)
            if m:
                dest = r["destination"]
                for k, v in m.groupdict().items():
                    dest = dest.replace(":" + k, v or "")
                return r["type"], dest
    return None


def load(name):
    return json.loads((ROOT / name).read_text())


def test_main_site_redirects_secondary_sections_permanently():
    reds = load("firebase.json")["hosting"]["redirects"]
    for path in ["/info", "/info/", "/info/guides/plombier/", "/info/articles/receptionniste-ia-artisan/"]:
        assert resolve(reds, path) == (301, ORIGINS["info"] + ("/info/" if path in ("/info", "/info/") else path)), path
    assert resolve(reds, "/store/fiche-google-optimisee/") == (301, ORIGINS["store"] + "/store/fiche-google-optimisee/")
    for path in ["/", "/agence-seo-local-yvelines/", "/zones/yvelines/versailles/", "/espace/", "/app/", "/leads"]:
        assert resolve(reds, path) is None, f"{path} ne doit pas être redirigé sur le .fr"


def test_secondary_sites_keep_root_fix_and_redirect_foreign_pages():
    cfg = load("firebase.multisite.json")
    sections = fr_sections()
    assert {"agence-seo-local-yvelines", "agence-seo-local-eure-et-loir", "zones", "methode", "a-propos", "mentions-legales"} <= sections
    for h in cfg["hosting"]:
        site = SITE_OF[h["site"]]
        reds = h["redirects"]
        # Correctif page blanche React #423 : la racine redirige (302) vers la section native.
        assert resolve(reds, "/") == (302, f"/{site}/"), h["site"]
        # Chaque page du .fr est redirigée en 301 vers le .fr, chemin conservé.
        for sec in sections:
            assert resolve(reds, f"/{sec}/") == (301, f"{ORIGINS['fr']}/{sec}/"), (h["site"], sec)
            assert resolve(reds, f"/{sec}/a/b/") == (301, f"{ORIGINS['fr']}/{sec}/a/b/"), (h["site"], sec)
        other = "store" if site == "info" else "info"
        assert resolve(reds, f"/{other}/x/") == (301, f"{ORIGINS[other]}/{other}/x/")
        # Les pages propres au site ne sont jamais redirigées.
        assert resolve(reds, f"/{site}/") is None
        assert resolve(reds, f"/{site}/x/") is None


def test_cloud_run_rewrites_preserved_everywhere():
    main = load("firebase.json")["hosting"]["rewrites"]
    api = {r["source"] for r in main if "run" in r}
    assert {"/leads", "/webhook/stripe", "/create-checkout-session", "/client/**", "/integrations/**"} <= api
    for h in load("firebase.multisite.json")["hosting"]:
        assert api <= {r["source"] for r in h["rewrites"] if "run" in r}, h["site"]
    # Aucune redirection ne doit intercepter une route API.
    for reds in [load("firebase.json")["hosting"]["redirects"]] + [h["redirects"] for h in load("firebase.multisite.json")["hosting"]]:
        for src in api:
            assert resolve(reds, src.replace("/**", "/x")) is None, src


def test_domains_ts_matches_test_ownership():
    src = (APP / "seo" / "domains.ts").read_text()
    for key, origin in ORIGINS.items():
        assert f"{key}: '{origin}'" in src
    assert owner_of("/info/guides/") == "info" and owner_of("/store/") == "store" and owner_of("/zones/") == "fr"
