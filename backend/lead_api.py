"""Leads entrants des sites .info / .store (outil de score, guide PDF, boutique, demande de rappel).

POST  /leads               : public (formulaires du site), validé, anti-spam léger.
GET   /admin/leads         : entonnoir du cockpit (protégé par require_admin, route absente de PUBLIC_ROUTES).
PATCH /admin/leads/{id}    : changement d'étape, notes, prochain rappel (protégé).

Entonnoir : new (nouveau) → to_call (à rappeler) → contacted (rappelé) → won (gagné) | lost (perdu).
"""
import datetime
import re
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from backend.models.database import InboundLead, get_db

router = APIRouter()

SOURCES = {"score_tool", "guide_pdf", "store", "contact", "callback"}
STATUSES = ("new", "to_call", "contacted", "won", "lost")
LEGACY_STATUS = {"converted": "won"}
SOURCE_LABELS = {"score_tool": "Outil de score", "guide_pdf": "Guide PDF", "store": "Boutique",
                 "contact": "Contact", "callback": "Demande de rappel"}
CALLBACK_SLOTS = {"asap": "Dès que possible", "morning": "Le matin", "noon": "Le midi",
                  "afternoon": "L'après-midi", "evening": "En fin de journée"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{9,15}$")

# Limite simple par IP : 5 envois / 10 min (suffisant contre les robots basiques).
_WINDOW, _MAX = 600, 5
_hits: dict[str, deque] = defaultdict(deque)


def _rate_limited(ip: str) -> bool:
    now = time.time()
    q = _hits[ip]
    while q and now - q[0] > _WINDOW:
        q.popleft()
    if len(q) >= _MAX:
        return True
    q.append(now)
    return False


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
        if not self.email and not self.phone:
            raise ValueError("email ou téléphone requis")
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
        "created_at": _iso(r.created_at), "updated_at": _iso(r.updated_at),
    }


def _alert_new_lead(lead: dict) -> None:
    """Email à l'équipe (ALERT_EMAIL) : un lead à rappeler vient d'arriver. Ne lève jamais."""
    try:
        from backend.services.alerts import send_alert
        who = lead["contact_name"] or lead["business_name"] or lead["email"] or lead["phone"]
        lines = [f"{k} : {v}" for k, v in (
            ("Source", lead["source_label"]), ("Produit", lead["product"]), ("Nom", lead["contact_name"]),
            ("Commerce", lead["business_name"]), ("Ville", lead["city"]), ("Téléphone", lead["phone"]),
            ("Email", lead["email"]), ("Rappel souhaité", lead["callback_label"]), ("Score", lead["score"]),
            ("Message", lead["message"]), ("Page", lead["referrer"])) if v not in (None, "")]
        send_alert(f"Nouveau lead à rappeler : {who}", "\n".join(lines) + "\n\n→ Cockpit, onglet « Leads ».")
    except Exception as exc:
        print(f"[LEADS] alerte non envoyée ({exc})")


@router.post("/leads")
async def create_lead(data: LeadIn, request: Request, db: Session = Depends(get_db)):
    if data.website:  # robot : on fait semblant que tout va bien
        return {"ok": True}
    if not data.consent:
        raise HTTPException(400, "Consentement requis")
    ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")).split(",")[0].strip()
    if _rate_limited(ip):
        raise HTTPException(429, "Trop de demandes, réessayez plus tard")

    answers = {k[:40]: v for k, v in list((data.answers or {}).items())[:20]}
    lead = InboundLead(
        source=data.source,
        email=data.email,
        contact_name=_clean(data.contact_name),
        business_name=_clean(data.business_name),
        phone=_clean(data.phone),
        city=_clean(data.city),
        product=_clean(data.product),
        message=(data.message or "").strip() or None,
        callback_slot=data.callback_slot,
        score=data.score,
        answers=answers or None,
        consent=True,
        referrer=(request.headers.get("referer") or "")[:300] or None,
        # Un numéro laissé = une personne à rappeler : directement dans la colonne « À rappeler ».
        status="to_call" if data.phone else "new",
    )
    db.add(lead)
    db.commit()
    await run_in_threadpool(_alert_new_lead, lead_dict(lead))
    return {"ok": True, "id": lead.id}


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
