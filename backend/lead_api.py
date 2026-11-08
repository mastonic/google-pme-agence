"""Leads entrants des sites .info / .store (outil de score, guide PDF, boutique, demande de rappel).

POST  /leads               : public (formulaires du site), validé, anti-spam léger.
GET   /admin/leads         : entonnoir du cockpit (protégé par require_admin, route absente de PUBLIC_ROUTES).
PATCH /admin/leads/{id}    : changement d'étape, notes, prochain rappel (protégé).

Entonnoir : new (nouveau) → to_call (à contacter) → contacted (contacté) → quote_sent (devis envoyé)
→ won (converti) | lost (clos).

Emails : chaque demande est enregistrée, puis une notification interne (boîte selon le type :
contact@, devis@, audit@, support@) et un accusé de réception au client sont mis en file dans la
même transaction (backend/services/email_service.py). Une panne SMTP ne fait perdre aucune demande.
"""
import datetime
import re

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from backend.models.database import EmailOutbox, InboundLead, get_db
from backend.services import email_service as es
from backend.services.web_security import RateLimiter, client_ip, safe_http_url

router = APIRouter()

SOURCES = {"score_tool", "guide_pdf", "store", "contact", "callback"}
STATUSES = ("new", "to_call", "contacted", "quote_sent", "won", "lost")
# Types de demande acceptés depuis les formulaires publics (order_paid : uniquement via Stripe).
KINDS = {k for k in es.KINDS if k != "order_paid"}
ALLOWED_ORIGINS = {"https://pulse-locale-pme.fr", "https://www.pulse-locale-pme.fr", "https://pulse-locale-pme.info",
                   "https://pulse-locale-pme.store", "https://pme-local-pulse.web.app", "https://pme-local-pulse.firebaseapp.com",
                   "http://localhost:3000", "http://localhost:5173"}
DEDUPE_WINDOW = datetime.timedelta(minutes=10)
MIN_FILL_MS = 1500   # un humain met plus de 1,5 s à remplir le formulaire
log = logging.getLogger("pulse.leads")
LEGACY_STATUS = {"converted": "won"}
SOURCE_LABELS = {"score_tool": "Outil de score", "guide_pdf": "Guide PDF", "store": "Boutique",
                 "contact": "Contact", "callback": "Demande de rappel"}
CALLBACK_SLOTS = {"asap": "Dès que possible", "morning": "Le matin", "noon": "Le midi",
                  "afternoon": "L'après-midi", "evening": "En fin de journée"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{9,15}$")

# Limite par IP : 5 envois / 10 min (IP fournie par l'infrastructure, pas par le client).
_WINDOW, _MAX = 600, 5
_limiter = RateLimiter(max_hits=_MAX, window_s=_WINDOW)


def _rate_limited(ip: str) -> bool:
    return _limiter.hit(ip)


def _safe_referrer(value: str | None) -> str | None:
    """Ne conserve que des URL http(s) : jamais de javascript: ou data: affichable dans le cockpit."""
    return safe_http_url((value or "")[:300]) or None


def _clean(v: str | None) -> str | None:
    v = re.sub(r"\s+", " ", v or "").strip()
    return v or None


class LeadIn(BaseModel):
    source: str
    email: str | None = Field(default=None, max_length=200)
    contact_name: str | None = Field(default=None, max_length=120)
    business_name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    city: str | None = Field(default=None, max_length=120)
    product: str | None = Field(default=None, max_length=160)
    message: str | None = Field(default=None, max_length=1500)
    callback_slot: str | None = Field(default=None, max_length=20)
    score: int | None = Field(default=None, ge=0, le=100)
    answers: dict[str, float] | None = None
    consent: bool = False
    website: str | None = None  # pot de miel : doit rester vide
    kind: str | None = Field(default=None, max_length=20)        # type de demande (routage email)
    request_id: str | None = Field(default=None, max_length=64)  # identifiant de soumission (anti-doublon)
    elapsed_ms: int | None = Field(default=None, ge=0)           # temps de remplissage (anti-robot)

    @field_validator("kind")
    @classmethod
    def _kind(cls, v: str | None) -> str | None:
        return v if v in KINDS else None

    @field_validator("request_id")
    @classmethod
    def _rid(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v if re.fullmatch(r"[A-Za-z0-9_-]{8,64}", v) else None

    @field_validator("email")
    @classmethod
    def _email(cls, v: str | None) -> str | None:
        v = (v or "").strip().lower()
        if not v:
            return None
        if not EMAIL_RE.match(v):
            raise ValueError("email invalide")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        if not v:
            return None
        if not PHONE_RE.match(re.sub(r"[\s.\-()]", "", v)):
            raise ValueError("téléphone invalide")
        return v

    @field_validator("source")
    @classmethod
    def _source(cls, v: str) -> str:
        if v not in SOURCES:
            raise ValueError("source inconnue")
        return v

    @field_validator("callback_slot")
    @classmethod
    def _slot(cls, v: str | None) -> str | None:
        return v if v in CALLBACK_SLOTS else None

    @model_validator(mode="after")
    def _reachable(self):
        # L'email est obligatoire (tous les formulaires l'exigent) : réponse écrite et confirmation.
        if not self.email:
            raise ValueError("email requis")
        return self


def _iso(dt) -> str | None:
    return dt.isoformat() + "Z" if dt else None


def lead_dict(r: InboundLead) -> dict:
    status = LEGACY_STATUS.get(r.status or "new", r.status or "new")
    return {
        "id": r.id, "source": r.source, "source_label": SOURCE_LABELS.get(r.source, r.source),
        "status": status if status in STATUSES else "new",
        "contact_name": r.contact_name, "business_name": r.business_name, "email": r.email, "phone": r.phone,
        "city": r.city, "product": r.product, "message": r.message,
        "callback_slot": r.callback_slot, "callback_label": CALLBACK_SLOTS.get(r.callback_slot or ""),
        "score": r.score, "answers": r.answers, "referrer": r.referrer, "notes": r.notes or "",
        "next_call_at": _iso(r.next_call_at), "business_id": r.business_id,
        "kind": r.kind, "kind_label": es.KINDS.get(r.kind or "", (None, None))[1], "site": r.site,
        "ref": es.ticket_ref(r.id, r.kind or "") if r.id else None,
        "created_at": _iso(r.created_at), "updated_at": _iso(r.updated_at),
    }


def default_kind(source: str, product: str | None) -> str:
    """Type de demande quand le formulaire ne l'indique pas (anciens formulaires)."""
    p = (product or "").lower()
    if source == "score_tool":
        return "audit"
    if source == "guide_pdf":
        return "guide"
    if source == "contact" or p.startswith(("contact", "question")):
        return "contact"
    if "support" in p:
        return "support"
    if p.startswith(("démo", "demo", "réceptionniste")):
        return "demo"
    if "audit" in p:
        return "audit"
    return "devis"


def site_of(request: Request) -> str:
    """Site d'origine d'après l'en-tête Origin (ou Referer)."""
    raw = request.headers.get("origin") or request.headers.get("referer") or ""
    m = re.match(r"https?://(?:www\.)?([^/:]+)", raw)
    host = m.group(1).lower() if m else ""
    if host.endswith("pulse-locale-pme.info"):
        return "info"
    if host.endswith("pulse-locale-pme.store"):
        return "store"
    if host.endswith(("pulse-locale-pme.fr", "pme-local-pulse.web.app", "pme-local-pulse.firebaseapp.com")):
        return "fr"
    return "autre"


def _dispatch(ids: list[int]) -> None:
    es.dispatch_in_new_session(ids)


@router.post("/leads")
async def create_lead(data: LeadIn, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    ip = client_ip(request)
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in ALLOWED_ORIGINS:
        log.warning("leads.abuse reason=foreign_origin origin=%s", origin[:80])
        raise HTTPException(403, "Origine non autorisée")
    if data.website:  # robot (pot de miel) : on fait semblant que tout va bien
        log.warning("leads.abuse reason=honeypot")
        return {"ok": True}
    if data.elapsed_ms is not None and data.elapsed_ms < MIN_FILL_MS:
        log.warning("leads.abuse reason=too_fast elapsed_ms=%s", data.elapsed_ms)
        return {"ok": True}
    if not data.consent:
        raise HTTPException(400, "Consentement requis")
    if _rate_limited(ip):
        log.warning("leads.abuse reason=rate_limited")
        raise HTTPException(429, "Trop de demandes, réessayez plus tard")

    kind = data.kind or default_kind(data.source, data.product)
    message = (data.message or "").strip() or None
    # Anti-doublon : même identifiant de soumission (double clic, retry) ou même demande récente.
    if data.request_id:
        dup = db.query(InboundLead).filter(InboundLead.request_id == data.request_id).first()
        if dup:
            log.info("leads.duplicate reason=request_id lead=%s", dup.id)
            return {"ok": True, "id": dup.id, "ref": es.ticket_ref(dup.id, dup.kind or kind), "duplicate": True}
    key = es.dedupe_key(data.email or "", kind, f"{data.product or ''}|{message or ''}")
    recent = (db.query(InboundLead).filter(InboundLead.dedupe_key == key,
                                           InboundLead.created_at > datetime.datetime.utcnow() - DEDUPE_WINDOW).first())
    if recent:
        log.info("leads.duplicate reason=same_request lead=%s", recent.id)
        return {"ok": True, "id": recent.id, "ref": es.ticket_ref(recent.id, recent.kind or kind), "duplicate": True}

    answers = {k[:40]: v for k, v in list((data.answers or {}).items())[:20]}
    lead = InboundLead(
        source=data.source,
        kind=kind,
        site=site_of(request),
        request_id=data.request_id,
        dedupe_key=key,
        email=data.email,
        contact_name=_clean(data.contact_name),
        business_name=_clean(data.business_name),
        phone=_clean(data.phone),
        city=_clean(data.city),
        product=_clean(data.product),
        message=message,
        callback_slot=data.callback_slot,
        score=data.score,
        answers=answers or None,
        consent=True,
        referrer=_safe_referrer(request.headers.get("referer")),
        # Un numéro laissé = une personne à rappeler : directement dans la colonne « À contacter ».
        status="to_call" if data.phone else "new",
    )
    try:
        db.add(lead)
        db.flush()
        # Emails mis en file dans la MÊME transaction que la demande : rien n'est perdu si le SMTP tombe,
        # et aucun email ne part si la demande n'a pas pu être enregistrée.
        rows = [es.send_internal_notification(db, lead), es.send_customer_confirmation(db, lead)]
        db.commit()
    except Exception as exc:
        db.rollback()
        log.error("leads.store_failed kind=%s reason=%s", kind, type(exc).__name__)
        raise HTTPException(503, "Service momentanément indisponible, réessayez dans un instant.")
    log.info("leads.created lead=%s kind=%s site=%s", lead.id, kind, lead.site)
    ids = [r.id for r in rows if r is not None]
    background.add_task(_dispatch, ids)
    return {"ok": True, "id": lead.id, "ref": es.ticket_ref(lead.id, kind)}


@router.get("/admin/email/status")
async def email_status(db: Session = Depends(get_db)):
    """Diagnostic du système email (aucun secret) et état de la file d'envoi."""
    from sqlalchemy import func
    counts = dict(db.query(EmailOutbox.status, func.count(EmailOutbox.id)).group_by(EmailOutbox.status).all())
    failures = (db.query(EmailOutbox).filter(EmailOutbox.status.in_(("failed", "dead")))
                .order_by(EmailOutbox.id.desc()).limit(20).all())
    return {"config": es.config_status(), "outbox": counts,
            "recent_failures": [{"id": r.id, "event": r.event_key, "kind": r.kind, "to": es.mask(r.to_addr),
                                 "status": r.status, "attempts": r.attempts, "error": r.last_error,
                                 "next_attempt_at": _iso(r.next_attempt_at)} for r in failures]}


@router.post("/admin/email/flush")
async def email_flush(db: Session = Depends(get_db)):
    """Relance immédiate des emails en attente (cockpit)."""
    return es.dispatch(db, limit=100)


@router.get("/admin/leads")
async def list_leads(limit: int = 200, db: Session = Depends(get_db)):
    rows = db.query(InboundLead).order_by(InboundLead.created_at.desc()).limit(min(limit, 1000)).all()
    return [lead_dict(r) for r in rows]


class LeadUpdate(BaseModel):
    status: str | None = None
    notes: str | None = Field(default=None, max_length=5000)
    next_call_at: str | None = None  # ISO 8601 ; "" pour effacer


@router.patch("/admin/leads/{lead_id}")
async def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(InboundLead).filter(InboundLead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead introuvable")
    if data.status is not None:
        if data.status not in STATUSES:
            raise HTTPException(422, "Étape inconnue")
        lead.status = data.status
    if data.notes is not None:
        lead.notes = data.notes.strip() or None
    if data.next_call_at is not None:
        if not data.next_call_at:
            lead.next_call_at = None
        else:
            try:
                dt = datetime.datetime.fromisoformat(data.next_call_at.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(422, "Date de rappel invalide")
            lead.next_call_at = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt
    lead.updated_at = datetime.datetime.utcnow()
    db.commit()
    return lead_dict(lead)


LEAD_RETENTION_YEARS = 3


def purge_old_leads(db: Session, years: int = LEAD_RETENTION_YEARS) -> int:
    """Politique de conservation (RGPD) : demandes sans activité depuis `years` ans supprimées.
    Les commandes payées relèvent des pièces comptables (Stripe / facturation), pas de cette table."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=365 * years)
    q = db.query(InboundLead).filter(InboundLead.created_at < cutoff,
                                     (InboundLead.updated_at.is_(None)) | (InboundLead.updated_at < cutoff))
    n = q.delete(synchronize_session=False)
    db.commit()
    if n:
        log.info("leads.purged count=%d years=%d", n, years)
    return n
