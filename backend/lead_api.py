"""Leads entrants des sites .info / .store (outil de score, guide PDF, boutique).

POST /leads  : public (formulaires du site), validé, anti-spam léger.
GET  /admin/leads : protégé par require_admin (route absente de PUBLIC_ROUTES).
"""
import re
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.models.database import InboundLead, get_db

router = APIRouter()

SOURCES = {"score_tool", "guide_pdf", "store", "contact"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

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


class LeadIn(BaseModel):
    source: str
    email: str = Field(max_length=200)
    business_name: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    city: str | None = Field(default=None, max_length=120)
    score: int | None = Field(default=None, ge=0, le=100)
    answers: dict[str, float] | None = None
    consent: bool = False
    website: str | None = None  # pot de miel : doit rester vide

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("email invalide")
        return v

    @field_validator("source")
    @classmethod
    def _source(cls, v: str) -> str:
        if v not in SOURCES:
            raise ValueError("source inconnue")
        return v


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
        business_name=(data.business_name or "").strip() or None,
        phone=(data.phone or "").strip() or None,
        city=(data.city or "").strip() or None,
        score=data.score,
        answers=answers or None,
        consent=True,
        referrer=(request.headers.get("referer") or "")[:300] or None,
    )
    db.add(lead)
    db.commit()
    return {"ok": True, "id": lead.id}


@router.get("/admin/leads")
async def list_leads(limit: int = 200, db: Session = Depends(get_db)):
    rows = db.query(InboundLead).order_by(InboundLead.created_at.desc()).limit(min(limit, 1000)).all()
    return [
        {
            "id": r.id, "source": r.source, "email": r.email, "business_name": r.business_name,
            "phone": r.phone, "city": r.city, "score": r.score, "answers": r.answers,
            "status": r.status, "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
