"""Espace client PulsePro : connexion, onboarding, tableau de bord, modifications, abonnement.

Toutes les routes « client » sont publiques côté jeton admin (voir PUBLIC_ROUTES) et
protégées par leur propre session : en-tête `X-Client-Session`, obtenue en échangeant
soit un lien de connexion envoyé par email (usage unique, 30 min), soit le lien
d'onboarding permanent du client (`Business.onboarding_token`).

Les routes « admin » (préfixe /businesses/… et /client-requests/…) restent derrière
le jeton administrateur du cockpit.
"""
import base64
import datetime
import hashlib
import json
import os
import re
import secrets
import urllib.parse
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from backend.models.database import (
    Business, ClientMedia, ClientRequest, ClientSession, SiteDailyStat, get_db,
)
from backend.agents.manager import display_business_name
from backend.services.client_onboarding import empty_profile, ensure_token, merge_profile, onboarding_progress
from backend.services.plans import PLAN_CATALOG

router = APIRouter()

LOGIN_TTL = datetime.timedelta(minutes=30)
SESSION_TTL = datetime.timedelta(days=30)
# Vue « comme le client » depuis le cockpit : lien à usage unique très court, session limitée.
ADMIN_VIEW_LINK_TTL = datetime.timedelta(minutes=5)
ADMIN_SESSION_TTL = datetime.timedelta(hours=2)
SESSION_KINDS = ("session", "admin_session")
MAX_LOGIN_LINKS_PER_HOUR = 5
MAX_MEDIA_BYTES = 10 * 1024 * 1024
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
PHONE_RE = re.compile(r"^(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
MEDIA_KINDS = {"logo": 1, "devanture": 6, "equipe": 8, "realisation": 20}
REQUEST_CATEGORIES = {"horaires", "actualite", "photos", "textes", "autre"}
REQUEST_STATUSES = {"nouvelle", "en_cours", "terminee"}
SOCIAL_NETWORKS = ("instagram", "facebook", "tiktok", "linkedin")
MAX_SERVICES, MAX_SERVICE_LEN = 15, 60
WIZARD_STEPS = 7  # bienvenue, établissement, services & réseaux, horaires, photos, aperçu, forfait
TRACK_EVENTS = {"visit": "visits", "call": "calls", "whatsapp": "whatsapp", "directions": "directions", "form": "forms"}
# Provenance des visites (calculée dans le navigateur à partir de utm_source ou du référent).
SOURCE_LABELS = {
    "google": "Google (recherche)", "gbp": "Fiche Google", "facebook": "Facebook", "instagram": "Instagram",
    "tiktok": "TikTok", "linkedin": "LinkedIn", "qr": "QR code", "email": "E-mail", "sms": "SMS",
    "autre_moteur": "Autre moteur", "autre_site": "Autre site", "campagne": "Campagne", "direct": "Accès direct",
}
SOURCE_RE = re.compile(r"^[a-z_]{1,20}$")
MAX_AVG_TICKET = 100000
PLAN_TAGS = {
    "starter": "L'essentiel pour être trouvé",
    "pro": "Pour développer sa clientèle locale",
    "elite": "Visibilité maximale, accompagnement dédié",
}

# Signature des formats d'image acceptés (on ne se fie pas au type annoncé par le navigateur).
_MAGIC = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"RIFF", "image/webp"),
)


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def frontend_url() -> str:
    return (os.getenv("PUBLIC_BASE_URL") or os.getenv("FRONTEND_URL") or "https://pme-local-pulse.web.app").rstrip("/")


def space_url(**params) -> str:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    return f"{frontend_url()}/espace/" + (f"?{query}" if query else "")


def _new_token(db: Session, business_id: str, kind: str, ttl: datetime.timedelta) -> str:
    token = secrets.token_urlsafe(32)
    db.add(ClientSession(token_hash=_hash(token), business_id=business_id, kind=kind, expires_at=_now() + ttl))
    return token


# ──────────────────────────────────────────────────────────────────────────────
# Session client
# ──────────────────────────────────────────────────────────────────────────────

def client_business(request: Request, db: Session = Depends(get_db)) -> Business:
    token = request.headers.get("x-client-session", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Session expirée, reconnecte-toi.")
    row = db.query(ClientSession).filter(ClientSession.token_hash == _hash(token),
                                         ClientSession.kind.in_(SESSION_KINDS)).first()
    if not row or row.expires_at < _now():
        raise HTTPException(status_code=401, detail="Session expirée, reconnecte-toi.")
    b = db.query(Business).filter(Business.id == row.business_id).first()
    if not b:
        raise HTTPException(status_code=401, detail="Espace client introuvable.")
    return b


def send_login_email(to: str, business_name: str, link: str) -> bool:
    """Envoie le lien de connexion via SMTP (mêmes variables que les alertes). False si non configuré."""
    import smtplib
    from email.message import EmailMessage

    host = os.getenv("SMTP_HOST")
    if not host:
        print(f"[ESPACE CLIENT] SMTP non configuré : lien non envoyé à {to}")
        return False
    msg = EmailMessage()
    msg["Subject"] = "Ton lien de connexion à ton espace PulsePro"
    msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "contact@pulsepro.fr"))
    msg["To"] = to
    msg.set_content(
        f"Bonjour,\n\nVoici ton lien de connexion à l'espace client de {business_name} :\n\n{link}\n\n"
        "Il est valable 30 minutes et ne fonctionne qu'une fois. Si tu n'as rien demandé, ignore ce message.\n\n"
        "L'équipe PulsePro"
    )
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=20) as server:
            server.starttls()
            if os.getenv("SMTP_USER"):
                server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            server.send_message(msg)
        return True
    except Exception as exc:
        print(f"[ESPACE CLIENT] envoi du lien échoué ({exc})")
        return False


@router.post("/client/auth/request")
async def request_login_link(data: dict, db: Session = Depends(get_db)):
    """Demande de lien par email. Réponse identique que l'adresse soit connue ou non."""
    email = str(data.get("email") or "").strip().lower()
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise HTTPException(status_code=422, detail="Adresse e-mail invalide.")
    from sqlalchemy import func
    b = db.query(Business).filter(func.lower(Business.owner_email) == email).first()
    if b:
        recent = db.query(ClientSession).filter(
            ClientSession.business_id == b.id, ClientSession.kind == "login",
            ClientSession.created_at > _now() - datetime.timedelta(hours=1)).count()
        if recent < MAX_LOGIN_LINKS_PER_HOUR:
            token = _new_token(db, b.id, "login", LOGIN_TTL)
            db.commit()
            send_login_email(email, b.name or "ton établissement", space_url(login=token))
    return {"status": "sent"}


@router.post("/client/auth/exchange")
async def exchange_token(data: dict, db: Session = Depends(get_db)):
    """Échange un lien (connexion par email ou lien d'onboarding permanent) contre une session."""
    token = str(data.get("token") or "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Lien invalide.")
    business_id = None
    admin_view = False
    row = db.query(ClientSession).filter(ClientSession.token_hash == _hash(token),
                                         ClientSession.kind.in_(("login", "admin_view"))).first()
    if row:
        if row.used_at or row.expires_at < _now():
            raise HTTPException(status_code=401, detail="Ce lien a expiré. Demande un nouveau lien de connexion.")
        row.used_at = _now()
        business_id = row.business_id
        admin_view = row.kind == "admin_view"
    else:
        b = db.query(Business).filter(Business.onboarding_token == token).first()
        if b:
            business_id = b.id
    if not business_id:
        raise HTTPException(status_code=401, detail="Lien invalide. Demande un nouveau lien de connexion.")
    if admin_view:
        session = _new_token(db, business_id, "admin_session", ADMIN_SESSION_TTL)
        db.commit()
        return {"session": session, "admin_view": True}
    session = _new_token(db, business_id, "session", SESSION_TTL)
    db.commit()
    return {"session": session}


@router.post("/client/auth/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("x-client-session", "").strip()
    if token:
        db.query(ClientSession).filter(ClientSession.token_hash == _hash(token)).delete()
        db.commit()
    return {"status": "ok"}


# ──────────────────────────────────────────────────────────────────────────────
# État de l'espace
# ──────────────────────────────────────────────────────────────────────────────

def _profile(b: Business) -> dict:
    return b.client_profile if isinstance(b.client_profile, dict) else empty_profile(b)


def set_profile(b: Business, profile: dict) -> None:
    """Enregistre le profil. merge_profile modifie le dict en place : sans flag_modified,
    SQLAlchemy ne voit aucun changement sur la colonne JSON et la mise à jour serait perdue."""
    b.client_profile = profile
    flag_modified(b, "client_profile")


def default_hours() -> list[dict]:
    return [{"day": d, "closed": d == "dimanche", "open": "09:00", "close": "19:00"} for d in DAYS]


def _info(b: Business, profile: dict) -> tuple[dict, list[dict]]:
    identity, contact = profile.get("identity") or {}, profile.get("contact") or {}
    activity, google = profile.get("activity") or {}, profile.get("google") or {}
    info = {
        # Nom brut de la fiche Google (souvent en capitales) : affiché proprement tant que le client ne l'a pas modifié.
        "business_name": display_business_name(identity.get("business_name") or b.name or "")
        if (identity.get("business_name") or b.name or "") == (b.name or "") else identity.get("business_name"),
        "phone": contact.get("phone") or b.business_phone or "",
        "whatsapp": contact.get("whatsapp") or "",
        "address": contact.get("address") or b.address or "",
        "maps": google.get("profile_url") or "",
        "description": activity.get("description") or "",
    }
    hours = activity.get("hours")
    if not (isinstance(hours, list) and len(hours) == 7):
        hours = default_hours()
    return info, hours


def _extras(profile: dict) -> tuple[list[str], dict, dict]:
    activity, social = profile.get("activity") or {}, profile.get("social") or {}
    services = [str(x) for x in (activity.get("services") or []) if str(x).strip()][:MAX_SERVICES]
    social = {k: str(social.get(k) or "") for k in SOCIAL_NETWORKS}
    wizard = profile.get("wizard") if isinstance(profile.get("wizard"), dict) else {}
    wizard = {"step": max(0, min(int(wizard.get("step") or 0), WIZARD_STEPS - 1)), "done": bool(wizard.get("done"))}
    return services, social, wizard


def is_live(b: Business) -> bool:
    return (b.subscription_status or "") in ("active", "trialing")


def onboarding_step(b: Business, profile: dict, media_count: int) -> int:
    """0 = éléments à fournir, 1 = préparation par l'équipe, 2 = aperçu à valider, 3 = en ligne."""
    if is_live(b):
        return 3
    if b.generated_html:
        return 2
    info, _ = _info(b, profile)
    complete = bool(info["phone"] and info["address"] and len(info["description"]) >= 20 and media_count)
    return 1 if complete else 0


def _plans() -> list[dict]:
    out = []
    for slug in ("starter", "pro", "elite"):
        p = PLAN_CATALOG[slug]
        quota = (p.get("limits") or {}).get("modifications_per_month")
        out.append({
            "slug": slug, "name": p["name"], "price": p["price"], "tag": PLAN_TAGS[slug],
            "features": p.get("features", [])[:4], "popular": slug == "pro",
            "quota": quota if isinstance(quota, int) and quota >= 0 else None,  # None = illimité
        })
    return out


def _media_url(m: ClientMedia) -> str:
    return f"/client/media/{m.id}"


def _stats(db: Session, business_id: str, days: int = 90) -> list[dict]:
    start = (_now().date() - datetime.timedelta(days=days - 1))
    rows = {r.day: r for r in db.query(SiteDailyStat).filter(
        SiteDailyStat.business_id == business_id, SiteDailyStat.day >= start.isoformat()).all()}
    out = []
    for i in range(days):
        day = (start + datetime.timedelta(days=i)).isoformat()
        r = rows.get(day)
        out.append({"date": day, "v": r.visits if r else 0, "c": r.calls if r else 0,
                    "w": r.whatsapp if r else 0, "d": r.directions if r else 0,
                    "f": (r.forms or 0) if r else 0})
    return out


def source_totals(db: Session, business_id: str, start: datetime.date, end: datetime.date) -> list[dict]:
    """Visites par provenance entre deux dates (incluses), triées par volume."""
    totals: dict[str, int] = {}
    for r in db.query(SiteDailyStat).filter(SiteDailyStat.business_id == business_id,
                                            SiteDailyStat.day >= start.isoformat(),
                                            SiteDailyStat.day <= end.isoformat()).all():
        for k, v in (r.sources or {}).items() if isinstance(r.sources, dict) else []:
            totals[k] = totals.get(k, 0) + int(v or 0)
    rows = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return [{"key": k, "label": SOURCE_LABELS.get(k, k), "visits": v} for k, v in rows]


def avg_ticket(b: Business) -> int | None:
    v = ((_profile(b).get("activity") or {}).get("avg_ticket"))
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    return v if 0 < v <= MAX_AVG_TICKET else None


def potential_value(contacts: int, ticket: int | None) -> int | None:
    """Valeur potentielle = contacts (appels + WhatsApp + formulaires) × panier moyen."""
    return contacts * ticket if ticket else None


def _request_json(r: ClientRequest) -> dict:
    return {"id": r.id, "cat": r.category, "msg": r.message, "status": r.status,
            "date": r.created_at.isoformat() + "Z" if r.created_at else None}


def space_state(db: Session, b: Business) -> dict:
    profile = _profile(b)
    info, hours = _info(b, profile)
    media = {k: [] for k in MEDIA_KINDS}
    rows = db.query(ClientMedia).filter(ClientMedia.business_id == b.id).order_by(ClientMedia.created_at).all()
    for m in rows:
        media.setdefault(m.kind, []).append({"id": m.id, "name": m.name, "size": m.size, "src": _media_url(m)})
    requests = db.query(ClientRequest).filter(ClientRequest.business_id == b.id) \
        .order_by(ClientRequest.created_at.desc()).limit(50).all()
    plan = b.plan_tier if b.plan_tier in PLAN_CATALOG else "pro"
    live = is_live(b)
    services, social, wizard = _extras(profile)
    return {
        "business_id": b.id,
        "first_name": (b.owner_first_name or "").strip(),
        "email": b.owner_email or "",
        "status": "live" if live else "onboarding",
        "step": onboarding_step(b, profile, len(rows)),
        "plan": plan,
        "plans": _plans(),
        "info": info,
        "hours": hours,
        "services": services,
        "social": social,
        "wizard": wizard,
        "media": media,
        "preview_url": f"/preview/{urllib.parse.quote(str(b.id), safe='')}" if b.generated_html else "",
        "site_url": b.deployment_url or "",
        "activated_at": b.client_signed_at.isoformat() + "Z" if b.client_signed_at else None,
        "requests": [_request_json(r) for r in requests],
        "daily": _stats(db, b.id) if live else [],
        "sources": source_totals(db, b.id, _now().date() - datetime.timedelta(days=29), _now().date()) if live else [],
        "avg_ticket": avg_ticket(b),
        "payment_ready": bool((os.getenv("STRIPE_SECRET_KEY") or "").strip()),
    }


@router.get("/client/space")
async def get_space(b: Business = Depends(client_business), db: Session = Depends(get_db)):
    return space_state(db, b)


# ──────────────────────────────────────────────────────────────────────────────
# Onboarding : informations, horaires, médias
# ──────────────────────────────────────────────────────────────────────────────

def validate_info(info: dict, hours: list) -> dict:
    """Mêmes règles que le formulaire : renvoie {champ: message}."""
    e = {}
    get = lambda k: str(info.get(k) or "").strip()
    if len(get("business_name")) < 2:
        e["business_name"] = "Nom trop court (2 caractères minimum)"
    if not PHONE_RE.match(get("phone")):
        e["phone"] = "Numéro français invalide (ex. 06 12 34 56 78)"
    if get("whatsapp") and not PHONE_RE.match(get("whatsapp")):
        e["whatsapp"] = "Numéro français invalide (ex. 06 12 34 56 78)"
    if len(get("address")) < 5:
        e["address"] = "Adresse incomplète"
    if get("maps") and not re.match(r"^https?://\S+$", get("maps")):
        e["maps"] = "Lien invalide, il doit commencer par https://"
    if len(get("description")) < 20:
        e["description"] = "Ajoute quelques mots (20 caractères minimum)"
    elif len(get("description")) > 400:
        e["description"] = "400 caractères maximum"
    ok_hours = isinstance(hours, list) and len(hours) == 7 and all(
        isinstance(h, dict) and (h.get("closed") or (
            TIME_RE.match(str(h.get("open", ""))) and TIME_RE.match(str(h.get("close", "")))
            and h["open"] < h["close"])) for h in hours)
    if not ok_hours:
        e["hours"] = "L'heure de fermeture doit être après l'heure d'ouverture"
    return e


def _refresh_progress(b: Business, profile: dict) -> None:
    progress = onboarding_progress(profile, b.plan_tier if b.plan_tier in PLAN_CATALOG else "starter")
    b.onboarding_completeness = progress["percent"]
    b.onboarding_status = "complete" if progress["complete"] else "in_progress"
    b.onboarding_updated_at = _now()


def validate_extras(services, social) -> tuple[dict, list[str], dict]:
    """Services (liste courte) et liens des réseaux sociaux. Renvoie (erreurs, services, réseaux)."""
    e = {}
    clean_services = []
    if services is not None:
        if not isinstance(services, list):
            services = []
        for x in services:
            x = re.sub(r"\s+", " ", str(x or "")).strip()
            if x and x.lower() not in (c.lower() for c in clean_services):
                clean_services.append(x[:MAX_SERVICE_LEN])
        if len(clean_services) > MAX_SERVICES:
            e["services"] = f"{MAX_SERVICES} services maximum"
    clean_social = {}
    if social is not None:
        for k in SOCIAL_NETWORKS:
            v = str((social or {}).get(k) or "").strip()
            if v and not re.match(r"^https?://\S+$", v):
                e[f"social_{k}"] = "Lien invalide, il doit commencer par https://"
            clean_social[k] = v
    return e, clean_services, clean_social


@router.put("/client/space/info")
async def save_info(data: dict, b: Business = Depends(client_business), db: Session = Depends(get_db)):
    info, hours = data.get("info") or {}, data.get("hours") or []
    errors = validate_info(info, hours)
    extra_errors, services, social = validate_extras(data.get("services"), data.get("social"))
    errors.update(extra_errors)
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Certains champs sont à corriger.", "errors": errors})
    clean = {k: str(info.get(k) or "").strip() for k in
             ("business_name", "phone", "whatsapp", "address", "maps", "description")}
    hours = [{"day": DAYS[i], "closed": bool(h.get("closed")), "open": h.get("open") or "09:00",
              "close": h.get("close") or "19:00"} for i, h in enumerate(hours)]
    incoming = {
        "identity": {"business_name": clean["business_name"]},
        "contact": {"phone": clean["phone"], "whatsapp": clean["whatsapp"], "address": clean["address"]},
        "google": {"profile_url": clean["maps"]},
        "activity": {"description": clean["description"], "hours": hours},
    }
    if data.get("services") is not None:
        incoming["activity"]["services"] = services
    if data.get("social") is not None:
        incoming["social"] = social
    profile = merge_profile(b, incoming, source="client_onboarding")
    set_profile(b, profile)
    b.business_phone = clean["phone"] or b.business_phone
    _refresh_progress(b, profile)
    db.commit()
    return space_state(db, b)


@router.post("/client/space/wizard")
async def save_wizard(data: dict, b: Business = Depends(client_business), db: Session = Depends(get_db)):
    """Mémorise l'étape de l'assistant d'onboarding, pour reprendre là où le client s'est arrêté."""
    try:
        step = int(data.get("step") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Étape invalide.")
    profile = dict(_profile(b))
    profile["wizard"] = {"step": max(0, min(step, WIZARD_STEPS - 1)), "done": bool(data.get("done"))}
    set_profile(b, profile)
    db.commit()
    return profile["wizard"]


def sniff_image(data: bytes, name: str) -> str | None:
    for magic, mime in _MAGIC:
        if data.startswith(magic) and (mime != "image/webp" or data[8:12] == b"WEBP"):
            return mime
    head = data[:512].lstrip().lower()
    if name.lower().endswith(".svg") and (head.startswith(b"<svg") or head.startswith(b"<?xml")):
        return "image/svg+xml"
    return None


def _sync_profile_media(db: Session, b: Business) -> None:
    """Expose les médias au pipeline de génération (profil client : logo + photos)."""
    rows = db.query(ClientMedia).filter(ClientMedia.business_id == b.id).order_by(ClientMedia.created_at).all()
    base = frontend_url()
    logo = next((f"{base}{_media_url(m)}" for m in rows if m.kind == "logo"), "")
    photos = [{"url": f"{base}{_media_url(m)}", "kind": m.kind, "name": m.name} for m in rows if m.kind != "logo"]
    profile = _profile(b)
    profile = dict(profile)
    profile["identity"] = dict(profile.get("identity") or {}, logo_url=logo)
    profile["media"] = dict(profile.get("media") or {}, photos=photos)
    set_profile(b, profile)
    _refresh_progress(b, profile)


@router.post("/client/space/media")
async def upload_media(data: dict, b: Business = Depends(client_business), db: Session = Depends(get_db)):
    kind = str(data.get("kind") or "")
    if kind not in MEDIA_KINDS:
        raise HTTPException(status_code=422, detail="Type de média inconnu.")
    name = re.sub(r"[^\w.\- ]", "", str(data.get("name") or "image"))[:120] or "image"
    raw = str(data.get("data") or "")
    if "," in raw and raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        content = base64.b64decode(raw, validate=True)
    except Exception:
        raise HTTPException(status_code=422, detail=f"« {name} » : fichier illisible.")
    if not content or len(content) > MAX_MEDIA_BYTES:
        raise HTTPException(status_code=413, detail=f"« {name} » refusé : 10 Mo maximum.")
    mime = sniff_image(content, name)
    if not mime:
        raise HTTPException(status_code=415, detail=f"« {name} » refusé : format non pris en charge (PNG, JPG, WebP ou SVG).")
    existing = db.query(ClientMedia).filter(ClientMedia.business_id == b.id, ClientMedia.kind == kind)
    if kind == "logo":
        existing.delete()
    elif existing.count() >= MEDIA_KINDS[kind]:
        raise HTTPException(status_code=409, detail=f"Maximum {MEDIA_KINDS[kind]} fichier(s) pour cette catégorie.")
    m = ClientMedia(id=uuid.uuid4().hex, business_id=b.id, kind=kind, name=name, mime=mime,
                    size=len(content), data=content)
    db.add(m)
    db.flush()
    _sync_profile_media(db, b)
    db.commit()
    return {"id": m.id, "name": m.name, "size": m.size, "src": _media_url(m), "kind": kind,
            "step": onboarding_step(b, _profile(b), db.query(ClientMedia).filter(ClientMedia.business_id == b.id).count())}


@router.delete("/client/space/media/{media_id}")
async def delete_media(media_id: str, b: Business = Depends(client_business), db: Session = Depends(get_db)):
    deleted = db.query(ClientMedia).filter(ClientMedia.id == media_id, ClientMedia.business_id == b.id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    _sync_profile_media(db, b)
    db.commit()
    return {"status": "deleted"}


@router.get("/client/media/{media_id}")
async def get_media(media_id: str, db: Session = Depends(get_db)):
    """Lecture publique par identifiant aléatoire (utilisé par l'aperçu et le site généré)."""
    m = db.query(ClientMedia).filter(ClientMedia.id == media_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Not found")
    headers = {"Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff"}
    if m.mime == "image/svg+xml":
        headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; sandbox"
    return Response(content=m.data, media_type=m.mime, headers=headers)


# ──────────────────────────────────────────────────────────────────────────────
# Paiement et abonnement (Stripe)
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/client/space/checkout")
async def checkout(data: dict, b: Business = Depends(client_business), db: Session = Depends(get_db)):
    import asyncio
    from backend.main import _create_stripe_checkout  # import tardif : évite l'import circulaire

    plan = str(data.get("plan") or "")
    if plan not in PLAN_CATALOG:
        raise HTTPException(status_code=422, detail="Forfait inconnu.")
    if not b.generated_html:
        raise HTTPException(status_code=409, detail="Ton aperçu n'est pas encore prêt à être validé.")
    if is_live(b):
        raise HTTPException(status_code=409, detail="Ton forfait est déjà actif.")
    ensure_token(b)
    db.commit()
    session = await asyncio.to_thread(_create_stripe_checkout, b, plan)
    return {"url": session.url}


def _stripe_customer_id(stripe, b: Business) -> str:
    if b.stripe_customer_id:
        return b.stripe_customer_id
    found = stripe.Subscription.search(query=f"metadata['business_id']:'{b.id}'", limit=1)
    data = getattr(found, "data", None) or []
    return data[0]["customer"] if data else ""


@router.post("/client/space/portal")
async def billing_portal(b: Business = Depends(client_business), db: Session = Depends(get_db)):
    import asyncio
    import stripe

    secret = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    if not secret:
        raise HTTPException(status_code=503, detail="Gestion de l'abonnement temporairement indisponible.")
    stripe.api_key = secret
    customer = await asyncio.to_thread(_stripe_customer_id, stripe, b)
    if not customer:
        raise HTTPException(status_code=404, detail="Aucun abonnement Stripe trouvé pour ton compte.")
    if not b.stripe_customer_id:
        b.stripe_customer_id = customer
        db.commit()
    portal = await asyncio.to_thread(stripe.billing_portal.Session.create,
                                     customer=customer, return_url=space_url() + "#abonnement")
    return {"url": portal.url}


# ──────────────────────────────────────────────────────────────────────────────
# Demandes de modification
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/client/space/requests")
async def create_request(data: dict, b: Business = Depends(client_business), db: Session = Depends(get_db)):
    category, message = str(data.get("cat") or ""), str(data.get("msg") or "").strip()
    if category not in REQUEST_CATEGORIES:
        raise HTTPException(status_code=422, detail="Type de demande inconnu.")
    if not 10 <= len(message) <= 1500:
        raise HTTPException(status_code=422, detail="Décris ta demande en 10 à 1500 caractères.")
    if not is_live(b):
        raise HTTPException(status_code=409, detail="Les demandes de modification s'ouvrent une fois ton site en ligne.")
    r = ClientRequest(id=uuid.uuid4().hex, business_id=b.id, category=category, message=message)
    db.add(r)
    db.commit()
    try:
        from backend.services.alerts import send_alert
        send_alert(f"[PulsePro] Demande de modification — {b.name}",
                   {"client": b.name, "type": category, "message": message})
    except Exception:
        pass
    return _request_json(r)


# ──────────────────────────────────────────────────────────────────────────────
# Statistiques du site publié
# ──────────────────────────────────────────────────────────────────────────────

@router.put("/client/space/avg-ticket")
async def save_avg_ticket(data: dict, b: Business = Depends(client_business), db: Session = Depends(get_db)):
    """Panier moyen déclaré par le client, pour estimer la valeur des contacts reçus."""
    raw = data.get("avg_ticket")
    if raw in (None, ""):
        value = None
    else:
        try:
            value = int(round(float(str(raw).replace(",", ".").replace("€", "").strip())))
        except ValueError:
            raise HTTPException(status_code=422, detail="Montant invalide.")
        if not 0 < value <= MAX_AVG_TICKET:
            raise HTTPException(status_code=422, detail=f"Indique un montant entre 1 et {MAX_AVG_TICKET} €.")
    profile = _profile(b)
    profile.setdefault("activity", {})["avg_ticket"] = value
    set_profile(b, profile)
    db.commit()
    return space_state(db, b)


@router.post("/client/track/{business_id}")
async def track(business_id: str, request: Request, db: Session = Depends(get_db)):
    """Compteur appelé par le script injecté dans les sites (navigator.sendBeacon, text/plain)."""
    try:
        payload = json.loads((await request.body())[:300] or b"{}")
    except Exception:
        payload = {}
    column = TRACK_EVENTS.get(str(payload.get("e") or ""))
    ua = request.headers.get("user-agent", "").lower()
    if not column or any(bot in ua for bot in ("bot", "crawler", "spider", "headless")):
        return Response(status_code=204)
    if not db.query(Business.id).filter(Business.id == business_id).first():
        return Response(status_code=204)
    day = _now().date().isoformat()
    row = db.query(SiteDailyStat).filter(SiteDailyStat.business_id == business_id, SiteDailyStat.day == day).first()
    if not row:
        row = SiteDailyStat(business_id=business_id, day=day, visits=0, calls=0, whatsapp=0, directions=0, forms=0)
        db.add(row)
    setattr(row, column, (getattr(row, column) or 0) + 1)
    if column == "visits":
        src = str(payload.get("src") or "direct").strip().lower()
        src = src if SOURCE_RE.match(src) and src in SOURCE_LABELS else "autre_site"
        sources = dict(row.sources) if isinstance(row.sources, dict) else {}
        sources[src] = int(sources.get(src) or 0) + 1
        row.sources = sources
        flag_modified(row, "sources")
    db.commit()
    return Response(status_code=204)


def tracking_snippet(business_id: str) -> str:
    """Script de mesure anonyme : aucun cookie, aucune donnée personnelle.

    Compte une visite par session (avec sa provenance), les clics Appeler / WhatsApp /
    itinéraire et les formulaires envoyés.
    """
    endpoint = f"{frontend_url()}/client/track/{urllib.parse.quote(str(business_id), safe='')}"
    return (
        "<script data-pp-track>(function(){var u=" + json.dumps(endpoint) + ";"
        "function s(e,x){try{var b={e:e};if(x)b.src=x;navigator.sendBeacon(u,JSON.stringify(b))}catch(_){}}"
        "function src(){try{var q=new URLSearchParams(location.search),m=(q.get('utm_source')||'').toLowerCase();"
        "if(m){if(/^(gbp|gmb|google_business|fiche|maps)/.test(m))return'gbp';"
        "if(/^(qr|qrcode|flyer|vitrine)/.test(m))return'qr';"
        "var k=['google','facebook','instagram','tiktok','linkedin','email','sms'];"
        "for(var i=0;i<k.length;i++)if(m.indexOf(k[i])===0)return k[i];return'campagne'}"
        "var r=document.referrer;if(!r)return'direct';var h=new URL(r).hostname.replace(/^www\\./,'');"
        "if(h===location.hostname)return'';"
        "if(/(^|\\.)google\\./.test(h))return'google';"
        "if(/(facebook|fb)\\.com$/.test(h)||h==='fb.me')return'facebook';"
        "if(/instagram\\.com$/.test(h))return'instagram';if(/tiktok\\.com$/.test(h))return'tiktok';"
        "if(/(linkedin\\.com|lnkd\\.in)$/.test(h))return'linkedin';"
        "if(/(bing|yahoo|duckduckgo|qwant|ecosia)\\./.test(h))return'autre_moteur';"
        "return'autre_site'}catch(_){return'direct'}}"
        "try{if(!sessionStorage.getItem('pp_v')){sessionStorage.setItem('pp_v','1');s('visit',src())}}catch(_){s('visit',src())}"
        "document.addEventListener('click',function(ev){var a=ev.target.closest&&ev.target.closest('a');if(!a)return;"
        "var h=(a.getAttribute('href')||'').toLowerCase();"
        "if(h.indexOf('tel:')===0)s('call');"
        "else if(h.indexOf('wa.me')>-1||h.indexOf('whatsapp')>-1)s('whatsapp');"
        "else if(h.indexOf('maps.')>-1||h.indexOf('/maps')>-1||h.indexOf('itineraire')>-1)s('directions')},true);"
        "document.addEventListener('submit',function(){s('form')},true)})();</script>"
    )


def inject_tracking(html: str, business_id: str) -> str:
    """Injecte le script de mesure ; remplace une ancienne version s'il y en a une."""
    if not business_id:
        return html
    while "/client/track/" in html:
        idx = html.find("/client/track/")
        start = html.rfind("<script", 0, idx)
        end = html.find("</script>", idx)
        if start == -1 or end == -1:
            break
        html = html[:start] + html[end + len("</script>"):]
    snippet = tracking_snippet(business_id)
    idx = html.lower().rfind("</body>")
    return html[:idx] + snippet + html[idx:] if idx != -1 else html + snippet


# ──────────────────────────────────────────────────────────────────────────────
# Cockpit (jeton admin)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/businesses/{business_id}/client-space")
async def admin_client_space(business_id: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    token = ensure_token(b)
    db.commit()
    requests = db.query(ClientRequest).filter(ClientRequest.business_id == b.id) \
        .order_by(ClientRequest.created_at.desc()).all()
    return {
        "login_url": space_url(t=token),
        "owner_email": b.owner_email or "",
        "smtp_ready": bool(os.getenv("SMTP_HOST")),
        "media_count": db.query(ClientMedia).filter(ClientMedia.business_id == b.id).count(),
        "status": "live" if is_live(b) else "onboarding",
        "requests": [_request_json(r) for r in requests],
    }


@router.post("/businesses/{business_id}/client-space/send-link")
async def admin_send_link(business_id: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    if not b.owner_email:
        raise HTTPException(status_code=422, detail="Aucun email client renseigné (CRM).")
    token = _new_token(db, b.id, "login", LOGIN_TTL)
    db.commit()
    if not send_login_email(b.owner_email, b.name or "ton établissement", space_url(login=token)):
        raise HTTPException(status_code=503, detail="Envoi impossible : SMTP non configuré. Copie le lien à la place.")
    return {"status": "sent", "to": b.owner_email}


@router.patch("/client-requests/{request_id}")
async def admin_update_request(request_id: str, data: dict, db: Session = Depends(get_db)):
    status = str(data.get("status") or "")
    if status not in REQUEST_STATUSES:
        raise HTTPException(status_code=422, detail="Statut inconnu.")
    r = db.query(ClientRequest).filter(ClientRequest.id == request_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    r.status = status
    r.updated_at = _now()
    db.commit()
    return _request_json(r)


# ──────────────────────────────────────────────────────────────────────────────
# Cockpit : voir l'espace comme le client + tableau de maintenance
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/businesses/{business_id}/client-view")
async def admin_client_view(business_id: str, db: Session = Depends(get_db)):
    """Lien à usage unique (5 min) ouvrant l'espace du client en mode administrateur (session 2 h)."""
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    token = _new_token(db, b.id, "admin_view", ADMIN_VIEW_LINK_TTL)
    db.commit()
    return {"url": space_url(login=token, admin="1"), "expires_in": int(ADMIN_VIEW_LINK_TTL.total_seconds())}


def _iso(d) -> str | None:
    return d.isoformat() + "Z" if d else None


def _days_since(d) -> int | None:
    return (_now() - d).days if d else None


def _sum_stats(rows: list[dict]) -> dict:
    return {k: sum(r.get(s, 0) for r in rows)
            for k, s in (("visits", "v"), ("calls", "c"), ("whatsapp", "w"), ("directions", "d"), ("forms", "f"))}


def maintenance_state(db: Session, b: Business) -> dict:
    """Informations détaillées pour la maintenance d'un client (cockpit uniquement)."""
    from backend.services.scoring import calculate_scores

    profile = _profile(b)
    plan = b.plan_tier if b.plan_tier in PLAN_CATALOG else "starter"
    progress = onboarding_progress(profile, plan)

    # Médias déposés par le client
    media_rows = db.query(ClientMedia).filter(ClientMedia.business_id == b.id).all()
    media = {k: 0 for k in MEDIA_KINDS}
    for m in media_rows:
        media[m.kind] = media.get(m.kind, 0) + 1

    # Demandes de modification
    reqs = db.query(ClientRequest).filter(ClientRequest.business_id == b.id) \
        .order_by(ClientRequest.created_at.desc()).all()
    open_reqs = [r for r in reqs if r.status != "terminee"]
    oldest_open = min((r.created_at for r in open_reqs if r.created_at), default=None)
    quota = (PLAN_CATALOG.get(plan, {}).get("limits") or {}).get("modifications_per_month")
    month_start = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = sum(1 for r in reqs if r.created_at and r.created_at >= month_start)

    # Statistiques du site : 30 derniers jours vs 30 précédents
    daily = _stats(db, b.id, days=60)
    last30, prev30 = _sum_stats(daily[30:]), _sum_stats(daily[:30])

    # Connexions du client (hors sessions ouvertes depuis le cockpit)
    sessions = db.query(ClientSession).filter(ClientSession.business_id == b.id, ClientSession.kind == "session") \
        .order_by(ClientSession.created_at.desc()).all()
    last_login = sessions[0].created_at if sessions else None

    # Santé digitale (même calcul que la carte)
    scores = calculate_scores({
        "website": b.deployment_url or b.website, "rating": b.rating or 0,
        "user_ratings_total": b.user_ratings_total or 0, "photos": b.photos or [],
        "category": b.category or [], "address": b.address or "",
        "business_phone": b.business_phone, "owner_email": b.owner_email,
    }, b.website_audit if isinstance(b.website_audit, dict) else None)

    audit = b.website_audit if isinstance(b.website_audit, dict) else {}
    monitoring = getattr(b, "monitoring", None)
    monitoring = monitoring if isinstance(monitoring, dict) else {}

    try:
        from backend.receptionist_api import receptionist_state
        receptionist = receptionist_state(db, b)
    except Exception as exc:  # module optionnel / table absente
        receptionist = {"status": "unavailable", "error": str(exc)[:120]}

    live = is_live(b)
    alerts = []

    def alert(level: str, text: str):
        alerts.append({"level": level, "text": text})

    if live and not b.deployment_url:
        alert("high", "Abonnement actif mais aucun site déployé.")
    ssl_info = monitoring.get("ssl") if isinstance(monitoring.get("ssl"), dict) else {}
    if b.deployment_url and ssl_info.get("status") == "error":
        alert("high", "Certificat SSL invalide ou expiré.")
    elif b.deployment_url and ssl_info.get("status") == "warning":
        alert("medium", f"Certificat SSL expire dans {ssl_info.get('days_left')} jour(s).")
    if (b.subscription_status or "") in ("past_due", "unpaid"):
        alert("high", f"Paiement en échec ({b.subscription_status}).")
    if (b.subscription_status or "") in ("canceled", "cancelled"):
        alert("medium", "Abonnement résilié.")
    for issue in (audit.get("issues") or [])[:8]:
        if issue.get("severity") == "high":
            alert("medium", f"Audit : {issue.get('title')}")
    if oldest_open and _days_since(oldest_open) >= 3:
        alert("medium", f"{len(open_reqs)} demande(s) en attente, la plus ancienne depuis {_days_since(oldest_open)} j.")
    if isinstance(quota, int) and quota >= 0 and this_month > quota:
        alert("low", f"Quota de modifications dépassé ce mois-ci ({this_month}/{quota}).")
    if not progress["complete"]:
        alert("low", f"Onboarding incomplet ({round(progress['percent'])} %).")
    if live and (last_login is None or _days_since(last_login) > 30):
        alert("low", "Le client ne s'est pas connecté à son espace depuis plus de 30 jours.")
    if not monitoring and b.deployment_url:
        alert("low", "Site jamais supervisé : lancez une supervision.")
    if receptionist.get("status") == "trial" and isinstance(receptionist.get("days_left"), int) \
            and receptionist["days_left"] <= 5:
        alert("low", f"Essai Réceptionniste IA : plus que {receptionist['days_left']} jour(s).")
    order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: order.get(a["level"], 3))

    return {
        "business_id": b.id,
        "name": b.name,
        "generated_at": _iso(_now()),
        "alerts": alerts,
        "subscription": {
            "plan": plan, "status": b.subscription_status or "inactive", "mrr": b.mrr_value or 0,
            "signed_at": _iso(b.client_signed_at), "stripe_customer": bool(b.stripe_customer_id),
        },
        "site": {
            "url": b.deployment_url or "", "custom_domain": b.custom_domain or "",
            "ssl_active": bool(b.domain_ssl_active), "generated_at": _iso(b.generated_at),
            "deployed_at": _iso(b.deployed_at), "updated_at": _iso(b.updated_at),
            "has_generated_html": bool(b.generated_html),
            "features": {k.replace("features_", "").replace("_active", ""): bool(getattr(b, k, False))
                         for k in ("features_booking_active", "features_menu_active", "features_click_collect_active",
                                   "features_chatbot_active", "features_seo_blog_active", "features_gmb_reviews_sync",
                                   "features_multilang_active")},
        },
        "supervision": monitoring,
        "audit": {
            "status": audit.get("status") or b.website_audit_status or "not_audited",
            "score": audit.get("score"), "grade": audit.get("grade"),
            "response_time_ms": audit.get("response_time_ms"), "http_status": audit.get("http_status"),
            "audited_at": audit.get("audited_at"), "sections": audit.get("sections") or {},
            "issues": audit.get("issues") or [], "strengths": audit.get("strengths") or [],
        },
        "digital_health": scores["digital_health"],
        "google": {"rating": b.rating, "reviews": int(b.user_ratings_total or 0),
                   "seo_score": b.seo_score, "keywords": b.keywords_tracked or []},
        "onboarding": {"percent": progress["percent"], "complete": progress["complete"],
                       "missing": progress["missing"], "media": media, "status": b.onboarding_status},
        "requests": {
            "open": len(open_reqs), "total": len(reqs), "this_month": this_month,
            "quota": quota if isinstance(quota, int) and quota >= 0 else None,
            "oldest_open_days": _days_since(oldest_open),
            "by_status": {st: sum(1 for r in reqs if r.status == st) for st in REQUEST_STATUSES},
        },
        "stats": {
            "last30": last30, "prev30": prev30,
            "sources": source_totals(db, b.id, _now().date() - datetime.timedelta(days=29), _now().date()),
            "avg_ticket": avg_ticket(b),
            "value30": potential_value(last30["calls"] + last30["whatsapp"] + last30["forms"], avg_ticket(b)),
        },
        "client_access": {
            "email": b.owner_email or "", "last_login": _iso(last_login),
            "last_login_days": _days_since(last_login),
            "logins_30d": sum(1 for x in sessions if x.created_at and _days_since(x.created_at) <= 30),
        },
        "receptionist": receptionist,
    }


@router.get("/businesses/{business_id}/maintenance")
async def admin_maintenance(business_id: str, db: Session = Depends(get_db)):
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    return maintenance_state(db, b)


# ──────────────────────────────────────────────────────────────────────────────
# Cockpit : rapport mensuel (aperçu et envoi)
# ──────────────────────────────────────────────────────────────────────────────

def _period_or_422(period: str | None) -> str | None:
    if period and not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", period):
        raise HTTPException(status_code=422, detail="Période invalide (format AAAA-MM).")
    return period or None


@router.get("/businesses/{business_id}/monthly-report")
async def admin_monthly_report(business_id: str, period: str | None = None, db: Session = Depends(get_db)):
    from backend.services.monthly_report import build_report
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    report = build_report(db, b, _period_or_422(period))
    reports = _profile(b).get("reports") if isinstance(_profile(b).get("reports"), dict) else {}
    report["last_sent_at"] = reports.get("last_sent_at")
    report["last_period"] = reports.get("last_period")
    report["smtp_ready"] = bool(os.getenv("SMTP_HOST"))
    return report


@router.post("/businesses/{business_id}/monthly-report/send")
async def admin_send_monthly_report(business_id: str, period: str | None = None, db: Session = Depends(get_db)):
    from backend.services.monthly_report import build_report, send_email
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Not found")
    if not b.owner_email:
        raise HTTPException(status_code=422, detail="Aucun email client renseigné (CRM).")
    report = build_report(db, b, _period_or_422(period))
    if not send_email(b.owner_email, report["subject"], report["text"], report["html"]):
        raise HTTPException(status_code=503, detail="Envoi impossible : SMTP non configuré ou en échec.")
    profile = _profile(b)
    reports = profile.get("reports") if isinstance(profile.get("reports"), dict) else {}
    reports.update({"last_period": report["period"], "last_sent_at": _now().isoformat() + "Z"})
    profile["reports"] = reports
    set_profile(b, profile)
    db.commit()
    return {"status": "sent", "to": b.owner_email, "period": report["period"]}
