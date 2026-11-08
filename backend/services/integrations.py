"""Pack Connecté de la réceptionniste IA : webhook (Zapier / Make…), Google Sheets et Google Agenda.

- Webhook : après chaque appel, POST JSON signé (en-tête X-Pulse-Signature: sha256=<HMAC du corps>).
- Google : connexion OAuth du gérant (jeton de rafraîchissement chiffré avec INTEGRATIONS_KEY).
  * Sheets : un tableur « Appels – <commerce> » est créé dans son Drive (portée drive.file : l'application
    ne voit que les fichiers qu'elle a créés) ; une ligne par appel.
  * Agenda : l'IA propose de vrais créneaux libres (freeBusy) et réserve celui que l'appelant choisit.

Toutes les fonctions appelées pendant un appel sont « best effort » : elles ne lèvent jamais vers Twilio.

Variables d'environnement :
  INTEGRATIONS_KEY             clé Fernet (chiffrement des jetons + signature de l'état OAuth)
  GOOGLE_OAUTH_CLIENT_ID       identifiant client OAuth (Google Cloud Console, type « Application Web »)
  GOOGLE_OAUTH_CLIENT_SECRET   secret client OAuth
  GOOGLE_OAUTH_REDIRECT_URI    (facultatif) URL de retour ; défaut <site public>/integrations/google/callback
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import unicodedata
import urllib.parse
from zoneinfo import ZoneInfo

import requests

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
SHEETS_URL = "https://sheets.googleapis.com/v4/spreadsheets"
CALENDAR_URL = "https://www.googleapis.com/calendar/v3"
GOOGLE_SCOPES = [
    "openid", "email",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
]
SHEET_TAB = "Appels"
SHEET_HEADER = ["Date", "Canal", "Nom", "Téléphone", "Motif", "Urgent", "Adresse", "Créneau souhaité",
                "Rendez-vous réservé", "Précision", "Message vocal"]
STATE_TTL = 600            # secondes de validité du lien de connexion Google
DEFAULT_TZ = "Europe/Paris"
DEFAULT_SLOT_MINUTES = 60
MAX_SLOTS = 6
TIMEOUT = 8

DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
             "octobre", "novembre", "décembre"]
# Horaires par défaut si le commerce n'en a pas renseigné : du lundi au vendredi, 9 h–12 h et 14 h–18 h.
DEFAULT_HOURS = {d: [("09:00", "12:00"), ("14:00", "18:00")] for d in DAYS_FR[:5]}


class IntegrationError(Exception):
    """Erreur affichable à l'utilisateur (configuration manquante, Google refuse…)."""


# ──────────────────────────────────────────────────────────────────────────────
# Chiffrement & signature
# ──────────────────────────────────────────────────────────────────────────────

def _key() -> bytes:
    raw = os.getenv("INTEGRATIONS_KEY", "").strip()
    if not raw:
        raise IntegrationError("Connexion des applications indisponible : INTEGRATIONS_KEY n'est pas configurée.")
    try:
        key = base64.urlsafe_b64decode(raw.encode())
        if len(key) == 32:
            return raw.encode()
    except Exception:
        pass
    # Clé libre (phrase secrète) : dérivée en clé Fernet de 32 octets.
    return base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())


def encrypt(text: str) -> str:
    from cryptography.fernet import Fernet
    return Fernet(_key()).encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    from cryptography.fernet import Fernet, InvalidToken
    try:
        return Fernet(_key()).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise IntegrationError("Jeton Google illisible : reconnectez Google.") from exc


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def sign_state(business_id: str, now: float | None = None) -> str:
    payload = _b64(json.dumps({"b": business_id, "e": int((now or time.time()) + STATE_TTL),
                               "n": secrets.token_hex(6)}).encode())
    sig = _b64(hmac.new(_key(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def verify_state(state: str, now: float | None = None) -> str:
    """Renvoie le business_id si l'état est authentique et non expiré, sinon lève IntegrationError."""
    try:
        payload, sig = state.split(".", 1)
        expected = _b64(hmac.new(_key(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (ValueError, json.JSONDecodeError) as exc:
        raise IntegrationError("Lien de connexion Google invalide.") from exc
    if data.get("e", 0) < (now or time.time()):
        raise IntegrationError("Lien de connexion Google expiré : recommencez depuis votre espace.")
    return str(data["b"])


def webhook_signature(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Configuration (stockée en JSON dans ReceptionistAddon.integrations)
# ──────────────────────────────────────────────────────────────────────────────

def config(addon) -> dict:
    raw = getattr(addon, "integrations", None) if addon is not None else None
    cfg = dict(raw) if isinstance(raw, dict) else {}
    cfg["webhook"] = dict(cfg.get("webhook") or {})
    cfg["google"] = dict(cfg.get("google") or {})
    return cfg


def google_connected(cfg: dict) -> bool:
    return bool(cfg["google"].get("refresh_token_enc"))


def calendar_on(cfg: dict) -> bool:
    return google_connected(cfg) and cfg["google"].get("calendar_enabled", True)


def sheets_on(cfg: dict) -> bool:
    return google_connected(cfg) and cfg["google"].get("sheets_enabled", True) and bool(cfg["google"].get("sheet_id"))


def public_status(cfg: dict) -> dict:
    """Ce que l'interface peut afficher (jamais le jeton Google)."""
    g, w = cfg["google"], cfg["webhook"]
    return {
        "google": {
            "connected": google_connected(cfg),
            "email": g.get("email") or "",
            "connected_at": g.get("connected_at"),
            "sheets_enabled": bool(g.get("sheets_enabled", True)),
            "sheet_url": g.get("sheet_url") or "",
            "calendar_enabled": bool(g.get("calendar_enabled", True)),
            "slot_minutes": int(g.get("slot_minutes") or DEFAULT_SLOT_MINUTES),
            "timezone": g.get("timezone") or DEFAULT_TZ,
            "last_error": g.get("last_error") or "",
        },
        "webhook": {
            "url": w.get("url") or "",
            "secret": w.get("secret") or "",
            "enabled": bool(w.get("url")) and w.get("enabled", True),
            "last_status": w.get("last_status"),
            "last_at": w.get("last_at"),
        },
        "google_ready": google_oauth_ready(),
    }


def valid_webhook_url(url: str) -> bool:
    try:
        u = urllib.parse.urlparse(url)
    except ValueError:
        return False
    host = (u.hostname or "").lower()
    if u.scheme != "https" or not host or "." not in host:
        return False
    # Pas d'adresse interne (SSRF) : uniquement des noms de domaine publics.
    if host in ("localhost",) or host.endswith((".local", ".internal")) or re.fullmatch(r"[\d.]+|\[.*\]", host):
        return False
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Webhook
# ──────────────────────────────────────────────────────────────────────────────

def webhook_payload(business, summary: dict, call=None) -> dict:
    c = summary.get("caller") or {}
    return {
        "event": "call.completed",
        "business": {"id": getattr(business, "id", None), "name": getattr(business, "name", None)},
        "call": {
            "at": (getattr(call, "created_at", None) or datetime.datetime.utcnow()).isoformat() + "Z",
            "channel": summary.get("mode"),
            "caller_name": c.get("nom") or "",
            "caller_phone": c.get("telephone") or "",
            "reason": summary.get("motif") or "",
            "urgent": bool(summary.get("urgence")),
            "address": summary.get("adresse") or "",
            "requested_slot": summary.get("creneau") or "",
            "appointment": summary.get("rdv") or "",
            "appointment_start": summary.get("rdv_iso") or "",
            "detail": summary.get("precision") or "",
            "voicemail_url": summary.get("enregistrement") or "",
        },
    }


def send_webhook(url: str, secret: str, payload: dict) -> int:
    body = json.dumps(payload, ensure_ascii=False).encode()
    r = requests.post(url, data=body, timeout=TIMEOUT, allow_redirects=False, headers={
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "PulseLocalePME-Webhook/1.0",
        "X-Pulse-Signature": webhook_signature(secret, body),
    })
    return r.status_code


# ──────────────────────────────────────────────────────────────────────────────
# Google OAuth
# ──────────────────────────────────────────────────────────────────────────────

def google_oauth_ready() -> bool:
    return bool(os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip() and os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
                and os.getenv("INTEGRATIONS_KEY", "").strip())


def _client() -> tuple[str, str]:
    cid, secret = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip(), os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    if not (cid and secret):
        raise IntegrationError("Connexion Google indisponible : GOOGLE_OAUTH_CLIENT_ID / SECRET non configurés.")
    return cid, secret


def google_auth_url(business_id: str, redirect_uri: str) -> str:
    cid, _ = _client()
    return GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES), "access_type": "offline", "prompt": "consent",
        "include_granted_scopes": "true", "state": sign_state(business_id),
    })


def exchange_code(code: str, redirect_uri: str) -> dict:
    cid, secret = _client()
    r = requests.post(GOOGLE_TOKEN_URL, timeout=TIMEOUT, data={
        "code": code, "client_id": cid, "client_secret": secret,
        "redirect_uri": redirect_uri, "grant_type": "authorization_code"})
    data = r.json() if r.content else {}
    if r.status_code >= 300 or not data.get("access_token"):
        raise IntegrationError(f"Google a refusé la connexion ({data.get('error_description') or data.get('error') or r.status_code}).")
    if not data.get("refresh_token"):
        raise IntegrationError("Google n'a pas fourni d'accès permanent : retirez l'accès dans votre compte Google puis reconnectez.")
    return data


CALENDAR_SCOPES = ("https://www.googleapis.com/auth/calendar.events", "https://www.googleapis.com/auth/calendar.freebusy")
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"


def missing_scopes(token_response: dict) -> dict:
    """Google permet de décocher des accès sur l'écran de consentement : on vérifie ce qui a été accordé."""
    granted = set((token_response.get("scope") or "").split())
    if not granted:  # réponse sans champ « scope » : on ne peut pas conclure, on suppose tout accordé
        return {"calendar": False, "drive": False}
    return {"calendar": not all(s in granted for s in CALENDAR_SCOPES), "drive": DRIVE_SCOPE not in granted}


def userinfo_email(access_token: str) -> str:
    r = requests.get(GOOGLE_USERINFO_URL, timeout=TIMEOUT, headers={"Authorization": f"Bearer {access_token}"})
    return (r.json() or {}).get("email", "") if r.status_code < 300 else ""


_TOKEN_CACHE: dict[str, tuple[str, float]] = {}


def access_token(cfg: dict) -> str:
    enc = cfg["google"].get("refresh_token_enc")
    if not enc:
        raise IntegrationError("Google n'est pas connecté.")
    cached = _TOKEN_CACHE.get(enc)
    if cached and cached[1] > time.time() + 60:
        return cached[0]
    cid, secret = _client()
    r = requests.post(GOOGLE_TOKEN_URL, timeout=TIMEOUT, data={
        "client_id": cid, "client_secret": secret, "refresh_token": decrypt(enc), "grant_type": "refresh_token"})
    data = r.json() if r.content else {}
    if r.status_code >= 300 or not data.get("access_token"):
        raise IntegrationError("Accès Google expiré ou retiré : reconnectez Google.")
    _TOKEN_CACHE[enc] = (data["access_token"], time.time() + int(data.get("expires_in", 3600)))
    return data["access_token"]


def revoke(cfg: dict) -> None:
    enc = cfg["google"].get("refresh_token_enc")
    if enc:
        try:
            requests.post(GOOGLE_REVOKE_URL, params={"token": decrypt(enc)}, timeout=TIMEOUT)
        except Exception:
            pass
        _TOKEN_CACHE.pop(enc, None)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────────────────────────────────────
# Google Sheets
# ──────────────────────────────────────────────────────────────────────────────

def create_sheet(token: str, title: str) -> tuple[str, str]:
    r = requests.post(SHEETS_URL, headers=_auth(token), timeout=TIMEOUT, json={
        "properties": {"title": title, "locale": "fr_FR"},
        "sheets": [{"properties": {"title": SHEET_TAB, "gridProperties": {"frozenRowCount": 1}}}],
    })
    if r.status_code >= 300:
        raise IntegrationError(f"Création du tableur Google impossible ({r.status_code}).")
    data = r.json()
    sid = data["spreadsheetId"]
    append_row(token, sid, SHEET_HEADER)
    return sid, data.get("spreadsheetUrl") or f"https://docs.google.com/spreadsheets/d/{sid}/edit"


def append_row(token: str, sheet_id: str, row: list) -> None:
    rng = urllib.parse.quote(f"{SHEET_TAB}!A1", safe="")
    r = requests.post(f"{SHEETS_URL}/{sheet_id}/values/{rng}:append", headers=_auth(token), timeout=TIMEOUT,
                      params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}, json={"values": [row]})
    if r.status_code >= 300:
        raise IntegrationError(f"Ajout au tableur Google impossible ({r.status_code}).")


def sheet_row(summary: dict, tz: str = DEFAULT_TZ, when: datetime.datetime | None = None) -> list:
    c = summary.get("caller") or {}
    local = (when or datetime.datetime.utcnow()).replace(tzinfo=datetime.timezone.utc).astimezone(ZoneInfo(tz))
    mode = str(summary.get("mode") or "")
    canal = "WhatsApp" if mode.startswith("whatsapp") else "Messagerie" if mode == "voicemail" else "Appel"
    return [local.strftime("%d/%m/%Y %H:%M"), canal, c.get("nom") or "", c.get("telephone") or "",
            summary.get("motif") or "", "Oui" if summary.get("urgence") else "Non", summary.get("adresse") or "",
            summary.get("creneau") or "", summary.get("rdv") or "", summary.get("precision") or "",
            summary.get("enregistrement") or ""]


# ──────────────────────────────────────────────────────────────────────────────
# Google Agenda : créneaux libres et réservation
# ──────────────────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    t = unicodedata.normalize("NFKD", str(text or "").lower())
    return "".join(ch for ch in t if not unicodedata.combining(ch))


def opening_hours(business) -> dict[str, list[tuple[str, str]]]:
    """Horaires du commerce (profil client) par jour ; horaires de bureau par défaut s'ils sont absents."""
    profile = business.client_profile if isinstance(getattr(business, "client_profile", None), dict) else {}
    raw = (profile.get("activity") or {}).get("hours")
    out: dict[str, list[tuple[str, str]]] = {}
    if isinstance(raw, list):
        for h in raw:
            if not isinstance(h, dict):
                continue
            day = _norm(h.get("day"))
            day = next((d for d in DAYS_FR if _norm(d) == day), None)
            if day and not h.get("closed") and h.get("open") and h.get("close") and h["open"] < h["close"]:
                out.setdefault(day, []).append((h["open"], h["close"]))
    return out or DEFAULT_HOURS


def slot_label(start: datetime.datetime) -> str:
    h = f"{start.hour} h" + (f" {start.minute:02d}" if start.minute else "")
    return f"{DAYS_FR[start.weekday()]} {start.day} {MONTHS_FR[start.month - 1]} à {h}"


def candidate_slots(hours: dict, now_local: datetime.datetime, minutes: int, days: int = 7,
                    min_delay_hours: int = 2) -> list[datetime.datetime]:
    tz = now_local.tzinfo
    earliest = now_local + datetime.timedelta(hours=min_delay_hours)
    out = []
    for d in range(days + 1):
        day = (now_local + datetime.timedelta(days=d)).date()
        for start_s, end_s in hours.get(DAYS_FR[day.weekday()], []):
            sh, sm = map(int, start_s.split(":")[:2])
            eh, em = map(int, end_s.split(":")[:2])
            t = datetime.datetime(day.year, day.month, day.day, sh, sm, tzinfo=tz)
            end = datetime.datetime(day.year, day.month, day.day, eh, em, tzinfo=tz)
            while t + datetime.timedelta(minutes=minutes) <= end:
                if t >= earliest:
                    out.append(t)
                t += datetime.timedelta(minutes=minutes)
    return out


def _overlaps(start, end, busy) -> bool:
    return any(start < b_end and end > b_start for b_start, b_end in busy)


def busy_periods(token: str, calendar_id: str, start: datetime.datetime, end: datetime.datetime) -> list:
    r = requests.post(f"{CALENDAR_URL}/freeBusy", headers=_auth(token), timeout=TIMEOUT, json={
        "timeMin": start.isoformat(), "timeMax": end.isoformat(), "items": [{"id": calendar_id}]})
    if r.status_code >= 300:
        raise IntegrationError(f"Lecture de l'agenda Google impossible ({r.status_code}).")
    cal = (r.json().get("calendars") or {}).get(calendar_id) or {}
    return [(datetime.datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
             datetime.datetime.fromisoformat(b["end"].replace("Z", "+00:00"))) for b in cal.get("busy", [])]


def pick_spread(slots: list[datetime.datetime], limit: int = MAX_SLOTS) -> list[datetime.datetime]:
    """Au plus 2 créneaux par jour (un le matin, un l'après-midi si possible), pour proposer du choix."""
    by_day: dict = {}
    for s in slots:
        by_day.setdefault(s.date(), []).append(s)
    picked = []
    for day in sorted(by_day):
        items = by_day[day]
        morning = [s for s in items if s.hour < 12]
        after = [s for s in items if s.hour >= 12]
        picked += ([morning[0]] if morning else []) + ([after[0]] if after else [])
        if len(picked) >= limit:
            break
    return picked[:limit]


def free_slots(business, cfg: dict, now: datetime.datetime | None = None) -> list[dict]:
    """Créneaux réellement libres à proposer : [{"iso": "...", "label": "mardi 12 novembre à 10 h"}]."""
    g = cfg["google"]
    tz = ZoneInfo(g.get("timezone") or DEFAULT_TZ)
    minutes = int(g.get("slot_minutes") or DEFAULT_SLOT_MINUTES)
    now_local = (now or datetime.datetime.now(datetime.timezone.utc)).astimezone(tz)
    cands = candidate_slots(opening_hours(business), now_local, minutes)
    if not cands:
        return []
    token = access_token(cfg)
    busy = busy_periods(token, g.get("calendar_id") or "primary", cands[0], cands[-1] + datetime.timedelta(minutes=minutes))
    free = [s for s in cands if not _overlaps(s, s + datetime.timedelta(minutes=minutes), busy)]
    return [{"iso": s.isoformat(), "label": slot_label(s)} for s in pick_spread(free)]


def create_event(cfg: dict, start_iso: str, summary_text: str, description: str) -> str:
    g = cfg["google"]
    minutes = int(g.get("slot_minutes") or DEFAULT_SLOT_MINUTES)
    start = datetime.datetime.fromisoformat(start_iso)
    end = start + datetime.timedelta(minutes=minutes)
    tzname = g.get("timezone") or DEFAULT_TZ
    r = requests.post(f"{CALENDAR_URL}/calendars/{urllib.parse.quote(g.get('calendar_id') or 'primary', safe='')}/events",
                      headers=_auth(access_token(cfg)), timeout=TIMEOUT, json={
                          "summary": summary_text[:200], "description": description[:4000],
                          "start": {"dateTime": start.isoformat(), "timeZone": tzname},
                          "end": {"dateTime": end.isoformat(), "timeZone": tzname},
                          "reminders": {"useDefault": True}})
    if r.status_code >= 300:
        raise IntegrationError(f"Création du rendez-vous Google impossible ({r.status_code}).")
    return r.json().get("htmlLink", "")
