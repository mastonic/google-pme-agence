"""Declarative Agent Teams V1.

Git sources are manifest-only. Remote Python or shell is never executed.
"""
from __future__ import annotations

import json
import re
import socket
import ssl
import urllib.parse
from datetime import datetime
from typing import Any

import requests

try:
    import yaml
except Exception:
    yaml = None


SAFE_TOOLS = {
    "business_context",
    "domain_http_check",
    "dns_check",
    "ssl_check",
}

BUILTIN_MANIFESTS = [
    {
        "schema_version": 1,
        "slug": "domain-watch",
        "name": "Domain Watch",
        "description": "Vérifie domaine, DNS, HTTPS/SSL et disponibilité du site.",
        "category": "monitoring",
        "version": "1.0.0",
        "allowed_plans": ["starter", "pro", "elite"],
        "triggers": ["manual", "daily"],
        "agents": [
            {
                "id": "domain-inspector",
                "name": "Inspecteur domaine",
                "role": "Contrôle DNS et disponibilité HTTP",
                "tools": ["dns_check", "domain_http_check"],
                "prompt": "Analyse les contrôles techniques fournis. Résume les anomalies prioritaires et les actions concrètes, sans inventer.",
                "output_key": "domain_status",
            },
            {
                "id": "ssl-verifier",
                "name": "Vérificateur SSL",
                "role": "Contrôle sécurité HTTPS",
                "tools": ["ssl_check"],
                "prompt": "À partir des données SSL fournies, indique si le certificat est valide, sa date d'expiration et les risques éventuels.",
                "output_key": "ssl_status",
            },
            {
                "id": "qa",
                "name": "QA Monitoring",
                "role": "Synthèse et priorisation",
                "tools": [],
                "prompt": "Relis tous les résultats précédents et produis une synthèse courte : OK, à surveiller, urgent. Ne crée aucune donnée absente.",
                "output_key": "summary",
            },
        ],
    },
    {
        "schema_version": 1,
        "slug": "seo-local",
        "name": "SEO Local",
        "description": "Audit et plan d'action SEO local pour transformer les recherches Google en contacts.",
        "category": "seo",
        "version": "1.0.0",
        "allowed_plans": ["pro", "elite"],
        "triggers": ["manual", "weekly"],
        "agents": [
            {
                "id": "seo-auditor",
                "name": "Auditeur SEO",
                "role": "Analyse présence locale",
                "tools": ["business_context", "domain_http_check"],
                "prompt": "Analyse les données réelles du commerce et du site. Identifie 5 faiblesses SEO locales maximum, classées par impact.",
                "output_key": "audit",
            },
            {
                "id": "keyword-strategist",
                "name": "Stratège mots-clés",
                "role": "Priorise les intentions locales",
                "tools": ["business_context"],
                "prompt": "Propose des groupes de mots-clés locaux basés uniquement sur l'activité et la localisation fournies. Sépare intention forte, informationnelle et marque.",
                "output_key": "keywords",
            },
            {
                "id": "action-planner",
                "name": "Planificateur SEO",
                "role": "Transforme l'audit en actions",
                "tools": [],
                "prompt": "À partir des sorties précédentes, crée un plan d'actions sur 30 jours, priorisé par impact et effort.",
                "output_key": "plan_30_days",
            },
        ],
    },
    {
        "schema_version": 1,
        "slug": "social-media",
        "name": "Social Media Growth",
        "description": "Prépare une stratégie et des contenus sociaux cohérents avec le commerce.",
        "category": "social",
        "version": "1.0.0",
        "allowed_plans": ["elite"],
        "triggers": ["manual", "daily"],
        "agents": [
            {
                "id": "strategist",
                "name": "Stratège social",
                "role": "Définit angle, audience et format",
                "tools": ["business_context"],
                "prompt": "À partir des données réelles du commerce, définis 3 angles de contenu utiles et non répétitifs pour TikTok/Instagram/Facebook. Pas de chiffres inventés.",
                "output_key": "strategy",
            },
            {
                "id": "copywriter",
                "name": "Copywriter",
                "role": "Rédige les contenus",
                "tools": [],
                "prompt": "À partir de la stratégie précédente, rédige 3 publications prêtes à poster avec accroche, texte, CTA et hashtags sobres.",
                "output_key": "posts",
            },
            {
                "id": "creative-director",
                "name": "Directeur créatif",
                "role": "Prépare les briefs visuels",
                "tools": [],
                "prompt": "Pour chaque publication, propose un brief visuel ou vidéo vertical clair : scène, texte à l'écran, motion éventuel, plan voix off si pertinent.",
                "output_key": "creative_briefs",
            },
            {
                "id": "quality-checker",
                "name": "Contrôle qualité",
                "role": "Évite hallucinations et contenu faible",
                "tools": [],
                "prompt": "Vérifie toutes les sorties : cohérence marque, absence de faits inventés, CTA clair, pas de répétition. Retourne les corrections finales.",
                "output_key": "qa",
            },
        ],
    },
]


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ValueError("Le manifeste doit être un objet.")
    if manifest.get("schema_version") != 1:
        raise ValueError("schema_version doit être 1.")

    slug = str(manifest.get("slug") or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", slug):
        raise ValueError("slug invalide.")
    manifest["slug"] = slug

    agents = manifest.get("agents")
    if not isinstance(agents, list) or not agents or len(agents) > 12:
        raise ValueError("Une équipe doit contenir entre 1 et 12 agents.")

    seen = set()
    for agent in agents:
        if not isinstance(agent, dict):
            raise ValueError("Chaque agent doit être un objet.")
        aid = str(agent.get("id") or "").strip()
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", aid) or aid in seen:
            raise ValueError(f"Agent id invalide ou dupliqué : {aid}")
        seen.add(aid)
        prompt = str(agent.get("prompt") or "")
        if not prompt or len(prompt) > 8000:
            raise ValueError(f"Prompt invalide pour {aid}.")
        tools = agent.get("tools") or []
        if not isinstance(tools, list):
            raise ValueError(f"tools doit être une liste pour {aid}.")
        unknown = sorted(set(tools) - SAFE_TOOLS)
        if unknown:
            raise ValueError(f"Outils non autorisés pour {aid}: {', '.join(unknown)}")
        agent["tools"] = tools
        agent["output_key"] = agent.get("output_key") or aid

    manifest["name"] = str(manifest.get("name") or slug).strip()[:120]
    manifest["description"] = str(manifest.get("description") or "").strip()[:500]
    manifest["category"] = str(manifest.get("category") or "general").strip()[:64]
    manifest["version"] = str(manifest.get("version") or "1")
    manifest["triggers"] = manifest.get("triggers") or ["manual"]
    manifest["allowed_plans"] = manifest.get("allowed_plans") or []
    return manifest


def parse_manifest_text(text: str, path: str = "team.yaml") -> dict[str, Any]:
    if path.endswith(".json"):
        payload = json.loads(text)
    else:
        if yaml is None:
            raise ValueError("PyYAML n'est pas installé.")
        payload = yaml.safe_load(text)
    return validate_manifest(payload)


def github_raw_url(repo_url: str, manifest_path: str = "team.yaml", ref: str = "main") -> str:
    parsed = urllib.parse.urlparse(repo_url)
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ValueError("V1 accepte uniquement les dépôts GitHub publics.")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("URL GitHub invalide.")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise ValueError("Dépôt GitHub invalide.")
    safe_path = "/".join(urllib.parse.quote(p, safe="._-") for p in manifest_path.split("/") if p)
    if not safe_path or ".." in manifest_path.split("/"):
        raise ValueError("Chemin de manifeste invalide.")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{urllib.parse.quote(ref, safe='._-')}/{safe_path}"


def fetch_git_manifest(repo_url: str, manifest_path: str = "team.yaml", ref: str = "main") -> dict[str, Any]:
    url = github_raw_url(repo_url, manifest_path, ref)
    r = requests.get(url, timeout=10, headers={"User-Agent": "LocalPulse-AgentTeams/1.0"})
    if r.status_code == 404 and manifest_path == "team.yaml":
        url = github_raw_url(repo_url, "team.json", ref)
        r = requests.get(url, timeout=10, headers={"User-Agent": "LocalPulse-AgentTeams/1.0"})
        manifest_path = "team.json"
    r.raise_for_status()
    if len(r.text) > 250_000:
        raise ValueError("Manifeste trop volumineux.")
    return parse_manifest_text(r.text, manifest_path)


def business_context(business) -> dict[str, Any]:
    if business is None:
        return {}
    return {
        "name": getattr(business, "name", None),
        "address": getattr(business, "address", None),
        "website": getattr(business, "website", None),
        "phone": getattr(business, "business_phone", None),
        "rating": getattr(business, "rating", None),
        "reviews_count": getattr(business, "user_ratings_total", None),
        "category": getattr(business, "category", None),
        "opportunity_score": getattr(business, "opportunity_score", None),
        "digital_health_score": getattr(business, "digital_health_score", None),
        "plan_tier": getattr(business, "plan_tier", None),
    }


def _website_host(business) -> tuple[str | None, str | None]:
    website = getattr(business, "website", None) if business else None
    if not website:
        return None, None
    parsed = urllib.parse.urlparse(website if "://" in website else f"https://{website}")
    return website, parsed.hostname


def run_safe_tool(name: str, business) -> dict[str, Any]:
    if name == "business_context":
        return business_context(business)

    website, host = _website_host(business)
    if name == "domain_http_check":
        if not website:
            return {"ok": False, "reason": "Aucun site connu"}
        url = website if "://" in website else f"https://{website}"
        try:
            r = requests.get(url, timeout=8, allow_redirects=True, stream=True, headers={"User-Agent": "LocalPulse-Monitor/1.0"})
            return {
                "ok": r.status_code < 500,
                "status_code": r.status_code,
                "final_url": r.url,
                "https": r.url.startswith("https://"),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    if name == "dns_check":
        if not host:
            return {"ok": False, "reason": "Aucun domaine connu"}
        try:
            ips = sorted({row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
            return {"ok": bool(ips), "host": host, "ips": ips[:10]}
        except Exception as exc:
            return {"ok": False, "host": host, "error": str(exc)[:300]}

    if name == "ssl_check":
        if not host:
            return {"ok": False, "reason": "Aucun domaine connu"}
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=8) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
            return {
                "ok": True,
                "host": host,
                "issuer": cert.get("issuer"),
                "not_before": cert.get("notBefore"),
                "not_after": cert.get("notAfter"),
                "checked_at": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as exc:
            return {"ok": False, "host": host, "error": str(exc)[:300]}

    raise ValueError(f"Outil non autorisé : {name}")
