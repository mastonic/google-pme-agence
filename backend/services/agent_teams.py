"""Declarative Agent Teams V1.

Git sources are manifest-only. Remote Python or shell is never executed.
"""
from __future__ import annotations

import json
import re
import socket
import ipaddress
import ssl
import urllib.parse
from datetime import datetime, timezone
from typing import Any

import requests

from backend.services.agent_prompts_v2 import MISSIONS, PROMPT_VERSION, temperature_for

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
                "prompt": MISSIONS["domain-inspector"],
                "prompt_version": f"domain_inspector@{PROMPT_VERSION}",
                "temperature": temperature_for("domain-inspector"),
                "output_key": "domain_status",
            },
            {
                "id": "ssl-verifier",
                "name": "Vérificateur SSL",
                "role": "Contrôle sécurité HTTPS",
                "tools": ["ssl_check"],
                "prompt": MISSIONS["ssl-verifier"],
                "prompt_version": f"ssl_verifier@{PROMPT_VERSION}",
                "temperature": temperature_for("ssl-verifier"),
                "output_key": "ssl_status",
            },
            {
                "id": "qa",
                "name": "QA Monitoring",
                "role": "Synthèse et priorisation",
                "tools": [],
                "prompt": MISSIONS["qa"],
                "prompt_version": f"qa_monitoring@{PROMPT_VERSION}",
                "temperature": temperature_for("qa"),
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
                "prompt": MISSIONS["seo-auditor"],
                "prompt_version": f"seo_auditeur@{PROMPT_VERSION}",
                "temperature": temperature_for("seo-auditor"),
                "output_key": "audit",
            },
            {
                "id": "keyword-strategist",
                "name": "Stratège mots-clés",
                "role": "Priorise les intentions locales",
                "tools": ["business_context"],
                "prompt": MISSIONS["keyword-strategist"],
                "prompt_version": f"seo_mots_cles@{PROMPT_VERSION}",
                "temperature": temperature_for("keyword-strategist"),
                "output_key": "keywords",
            },
            {
                "id": "action-planner",
                "name": "Planificateur SEO",
                "role": "Transforme l'audit en actions",
                "tools": [],
                "prompt": MISSIONS["action-planner"],
                "prompt_version": f"seo_planificateur@{PROMPT_VERSION}",
                "temperature": temperature_for("action-planner"),
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
                "prompt": MISSIONS["strategist"],
                "prompt_version": f"social_stratege@{PROMPT_VERSION}",
                "temperature": temperature_for("strategist"),
                "output_key": "strategy",
            },
            {
                "id": "copywriter",
                "name": "Copywriter",
                "role": "Rédige les contenus",
                "tools": [],
                "prompt": MISSIONS["copywriter"],
                "prompt_version": f"social_copywriter@{PROMPT_VERSION}",
                "temperature": temperature_for("copywriter"),
                "output_key": "posts",
            },
            {
                "id": "creative-director",
                "name": "Directeur créatif",
                "role": "Prépare les briefs visuels",
                "tools": [],
                "prompt": MISSIONS["creative-director"],
                "prompt_version": f"social_directeur_creatif@{PROMPT_VERSION}",
                "temperature": temperature_for("creative-director"),
                "output_key": "creative_briefs",
            },
            {
                "id": "quality-checker",
                "name": "Contrôle qualité",
                "role": "Évite hallucinations et contenu faible",
                "tools": [],
                "prompt": MISSIONS["quality-checker"],
                "prompt_version": f"social_qa@{PROMPT_VERSION}",
                "temperature": temperature_for("quality-checker"),
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
        agent["prompt_version"] = str(agent.get("prompt_version") or f"{aid}@v1")
        try:
            temp = float(agent.get("temperature", 0.1))
        except (TypeError, ValueError):
            raise ValueError(f"temperature invalide pour {aid}.")
        if temp < 0 or temp > 1:
            raise ValueError(f"temperature hors limites pour {aid}.")
        agent["temperature"] = temp

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


def _ensure_public_host(host: str | None):
    if not host:
        raise ValueError("Aucun domaine connu")
    infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    addresses = sorted({row[4][0] for row in infos})
    if not addresses:
        raise ValueError("Domaine sans adresse IP")
    for raw in addresses:
        ip = ipaddress.ip_address(raw)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("Adresse réseau privée/interne refusée")
    return addresses


def run_safe_tool(name: str, business) -> dict[str, Any]:
    if name == "business_context":
        return business_context(business)

    website, host = _website_host(business)
    if name == "domain_http_check":
        if not website:
            return {"ok": False, "reason": "Aucun site connu"}
        url = website if "://" in website else f"https://{website}"
        try:
            _ensure_public_host(host)
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
            ips = _ensure_public_host(host)
            return {"ok": bool(ips), "host": host, "ips": ips[:10]}
        except Exception as exc:
            return {"ok": False, "host": host, "error": str(exc)[:300]}

    if name == "ssl_check":
        if not host:
            return {"ok": False, "reason": "Aucun domaine connu"}
        try:
            _ensure_public_host(host)
            ctx = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=8) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
            not_after = cert.get("notAfter")
            days_remaining = None
            if not_after:
                try:
                    expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    days_remaining = int((expiry - datetime.now(timezone.utc)).total_seconds() // 86400)
                except Exception:
                    days_remaining = None
            sans = [value for kind, value in cert.get("subjectAltName", []) if kind == "DNS"]
            return {
                "ok": True,
                "host": host,
                "issuer": cert.get("issuer"),
                "not_before": cert.get("notBefore"),
                "not_after": not_after,
                "days_remaining": days_remaining,
                "subject_alt_names": sans,
                "covers_www": (f"www.{host}" in sans) if host and sans else None,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            return {"ok": False, "host": host, "error": str(exc)[:300]}

    raise ValueError(f"Outil non autorisé : {name}")
