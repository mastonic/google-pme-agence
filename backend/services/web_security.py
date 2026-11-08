"""Briques de sécurité web partagées (audit du 8 novembre 2026).

- safe_http_url : URL http(s) sans caractères capables de sortir d'un attribut HTML.
- client_ip / RateLimiter : limitation de débit qui résiste à un X-Forwarded-For forgé.
- SECURITY_HEADERS / SANDBOX_CSP : en-têtes ajoutés par le middleware de l'API.
- public_host_ip : résolution DNS + refus des adresses privées (anti-SSRF).
"""
from __future__ import annotations

import ipaddress
import socket
import time
from collections import OrderedDict, deque
from urllib.parse import urlparse

_UNSAFE_URL_CHARS = set('"\'<>`\\ \t\r\n')


def safe_http_url(url, https_only: bool = False) -> str:
    """Renvoie l'URL si elle est http(s) et ne peut pas casser un attribut HTML, sinon ''."""
    if not isinstance(url, str):
        return ""
    url = url.strip()
    if not url or len(url) > 2048 or any(c in _UNSAFE_URL_CHARS for c in url):
        return ""
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    allowed = ("https",) if https_only else ("http", "https")
    if parsed.scheme not in allowed or not parsed.hostname:
        return ""
    return url


def client_ip(request) -> str:
    """IP du visiteur pour la limitation de débit.

    Le premier élément de X-Forwarded-For est fourni par le client et peut être forgé.
    Les derniers éléments sont ajoutés par l'infrastructure (Firebase / Google Front End) :
    on utilise les deux derniers, ce qui inclut l'IP réelle vue par le premier proxy de confiance.
    """
    xff = request.headers.get("x-forwarded-for") or ""
    parts = [p.strip() for p in xff.split(",") if p.strip()]
    if parts:
        return ",".join(parts[-2:])
    return request.client.host if getattr(request, "client", None) else "unknown"


class RateLimiter:
    """Fenêtre glissante en mémoire, nombre de clés borné (pas de croissance illimitée)."""

    def __init__(self, max_hits: int, window_s: int, max_keys: int = 10_000):
        self.max_hits, self.window, self.max_keys = max_hits, window_s, max_keys
        self._hits: OrderedDict[str, deque] = OrderedDict()

    def hit(self, key: str) -> bool:
        """Enregistre un appel ; renvoie True si la limite est dépassée."""
        now = time.time()
        q = self._hits.pop(key, None) or deque()
        while q and now - q[0] > self.window:
            q.popleft()
        limited = len(q) >= self.max_hits
        if not limited:
            q.append(now)
        self._hits[key] = q
        while len(self._hits) > self.max_keys:
            self._hits.popitem(last=False)
        return limited

    def reset(self) -> None:
        self._hits.clear()


# En-têtes de sécurité de toutes les réponses de l'API.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}

# Contenus HTML non fiables (sites générés, démos, présentations) : origine opaque, ils ne
# peuvent ni lire le stockage ni les cookies du domaine principal, même ouverts directement.
SANDBOX_CSP = "sandbox allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation"
# Pages HTML encadrables par le cockpit / l'espace client (même origine uniquement).
FRAMEABLE_PREFIXES = ("/preview/", "/demo/", "/presentation/")


def public_host_ip(host: str) -> str:
    """Résout `host` et renvoie une IP publique ; lève ValueError si privée, locale ou réservée."""
    if not host:
        raise ValueError("hôte manquant")
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError("hôte introuvable") from exc
    ips = {info[4][0] for info in infos}
    for ip in ips:
        addr = ipaddress.ip_address(ip)
        if not addr.is_global or addr.is_multicast:
            raise ValueError("adresse non publique")
    return sorted(ips)[0]
