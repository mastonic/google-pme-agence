"""Discover public social accounts and photo candidates for a selected business.

Discovery does NOT grant copyright permission to republish photos. Only media
explicitly approved by the business owner should be used in generated websites.
The optional Apify actor is configured by SOCIAL_PHOTOS_APIFY_ACTOR_ID.
"""
import os
import re
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
import requests


SOCIAL_HOSTS = {
    "instagram.com": "instagram",
    "www.instagram.com": "instagram",
    "facebook.com": "facebook",
    "www.facebook.com": "facebook",
    "m.facebook.com": "facebook",
}
BLOCKED_HANDLES = {"explore", "reels", "reel", "p", "stories", "share", "sharer", "login", "help"}


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.urls.append(href)


def discover_official_accounts(website: str) -> list[dict]:
    """Find accounts linked FROM the official website; never guess handles."""
    parsed = urlparse(website or "")
    if parsed.scheme != "https" or not parsed.hostname:
        return []
    # Avoid fetching private/local addresses and arbitrary IP literals.
    import ipaddress
    try:
        ipaddress.ip_address(parsed.hostname)
        return []
    except ValueError:
        pass
    if parsed.hostname.lower() in {"localhost"} or not "." in parsed.hostname:
        return []
    # Reject hostnames resolving to private, loopback or metadata networks.
    import socket
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(
            not ipaddress.ip_address(info[4][0]).is_global for info in addresses
        ):
            return []
    except (socket.gaierror, ValueError):
        return []
    try:
        response = requests.get(
            website, timeout=8, allow_redirects=False,
            headers={"User-Agent": "PulseLocaleBusinessEnrichment/1.0"},
        )
        if response.status_code != 200 or "text/html" not in response.headers.get("Content-Type", ""):
            return []
        if len(response.content) > 1_000_000:
            return []
        parser = _Links()
        parser.feed(response.text)
    except (requests.RequestException, ValueError):
        return []
    accounts = []
    seen = set()
    for href in parser.urls:
        url = urljoin(website, href)
        p = urlparse(url)
        platform = SOCIAL_HOSTS.get((p.hostname or "").lower())
        segments = [s for s in p.path.split("/") if s]
        if p.scheme != "https" or not platform or not segments:
            continue
        handle = segments[0].lstrip("@")
        if handle.lower() in BLOCKED_HANDLES or not re.fullmatch(r"[\\w.\\-]{2,80}", handle):
            continue
        canonical = f"https://{p.hostname}/{handle}/"
        if canonical not in seen:
            seen.add(canonical)
            accounts.append({"platform": platform, "url": canonical, "handle": handle,
                             "source": website, "verified": "linked_from_official_website"})
    return accounts[:8]


def discover_apify_photo_candidates(accounts: list[dict]) -> list[dict]:
    """Optional configured Apify actor. Candidate photos are NEVER auto-approved."""
    token = os.getenv("APIFY_TOKEN", "")
    actor = os.getenv("SOCIAL_PHOTOS_APIFY_ACTOR_ID", "").strip()
    if not token or not re.fullmatch(r"[A-Za-z0-9_~./-]{3,120}", actor):
        return []
    urls = [a["url"] for a in accounts if a.get("platform") in {"instagram", "facebook"}]
    if not urls:
        return []
    try:
        response = requests.post(
            f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items",
            headers={"Authorization": f"Bearer {token}"},
            json={"directUrls": urls[:5], "resultsLimit": 12},
            params={"timeout": 60, "memory": 512},
            timeout=70,
        )
        response.raise_for_status()
        rows = response.json()
    except (requests.RequestException, ValueError):
        return []
    if not isinstance(rows, list):
        return []
    candidates = []
    for row in rows[:40]:
        if not isinstance(row, dict):
            continue
        source = row.get("url") or row.get("postUrl") or row.get("inputUrl") or ""
        source_host = (urlparse(source).hostname or "").lower()
        if source_host not in SOCIAL_HOSTS:
            continue
        # Do not treat arbitrary posts as belonging to this business: only
        # accept actor records that expose the matched account handle.
        owner = str(row.get("ownerUsername") or row.get("username") or "").lstrip("@").lower()
        if not owner or not any(
            a["platform"] == SOCIAL_HOSTS[source_host] and a["handle"].lower() == owner
            for a in accounts
        ):
            continue
        photo = row.get("displayUrl") or row.get("imageUrl") or row.get("image")
        if not isinstance(photo, str) or urlparse(photo).scheme != "https":
            continue
        candidates.append({
            "url": photo, "source_url": source, "platform": SOCIAL_HOSTS[source_host],
            "owner": owner, "rights_status": "unverified", "approved_for_site": False,
        })
    return candidates[:20]


def discover_social_media(website: str) -> dict:
    accounts = discover_official_accounts(website)
    return {"accounts": accounts, "photo_candidates": discover_apify_photo_candidates(accounts)}
