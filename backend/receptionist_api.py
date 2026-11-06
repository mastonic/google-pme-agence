"""Routes du module Réceptionniste IA.

- Webhooks Twilio Voice (publics, protégés par la signature X-Twilio-Signature) :
    POST /receptionist/voice/{business_id}            appel entrant
    POST /receptionist/voice/{business_id}/turn       réponse vocale de l'appelant
    POST /receptionist/voice/{business_id}/voicemail  fin d'enregistrement (après l'essai)
    POST /receptionist/voice/{business_id}/status     statusCallback (raccroché)
    POST /receptionist/whatsapp/{business_id}         message WhatsApp entrant (même logique, texte)
- Espace client (session X-Client-Session) :
    GET  /client/space/receptionist                   statut de l'essai + statistiques
    POST /client/space/receptionist/activate          démarre l'essai gratuit de 30 jours
- Cockpit admin (jeton admin) :
    GET  /businesses/{business_id}/receptionist
    POST /businesses/{business_id}/receptionist/activate
         {"paid_active": bool, "notify_phone", "notify_email", "notify_channels": ["whatsapp","sms","email"]}
"""
import datetime
import os
import urllib.parse
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from backend.client_space_api import client_business
from backend.models.database import Business, ReceptionistAddon, ReceptionistCall, get_db
from backend.services import receptionist as rc
from backend.services.plans import (
    ADDON_CATALOG, RECEPTIONIST_ADDON, addon_ai_enabled, addon_status, days_left, start_addon_trial,
)

router = APIRouter()
MAX_SILENCES = 2


def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _xml(body: str) -> Response:
    return Response(content=body, media_type="application/xml")


def public_url(request: Request) -> str:
    """URL exacte appelée par Twilio (nécessaire à la signature), derrière proxy Cloud Run compris."""
    base = os.getenv("TWILIO_WEBHOOK_BASE_URL", "").strip().rstrip("/")
    query = request.url.query
    if base:
        return base + request.url.path + (f"?{query}" if query else "")
    proto = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip()
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}{request.url.path}" + (f"?{query}" if query else "")


async def twilio_params(request: Request) -> dict:
    """Lit le formulaire Twilio et rejette (403) toute requête non signée par Twilio."""
    raw = (await request.body()).decode("utf-8", "replace")
    params = dict(urllib.parse.parse_qsl(raw, keep_blank_values=True))
    if not rc.valid_signature(public_url(request), params, request.headers.get("x-twilio-signature", "")):
        raise HTTPException(status_code=403, detail="Signature Twilio invalide.")
    return params


def _addon(db: Session, business_id: str) -> ReceptionistAddon | None:
    return db.query(ReceptionistAddon).filter(ReceptionistAddon.business_id == business_id).first()


def _call(db: Session, business_id: str, params: dict, mode: str) -> ReceptionistCall:
    sid = params.get("CallSid") or f"nosid-{_now().timestamp()}"
    call = db.query(ReceptionistCall).filter(ReceptionistCall.call_sid == sid).first()
    if not call:
        call = ReceptionistCall(call_sid=sid, business_id=business_id, from_number=params.get("From", ""),
                                mode=mode, transcript=[], collected={})
        db.add(call)
        db.commit()
    return call


def _save(db: Session, call: ReceptionistCall) -> None:
    call.transcript, call.collected = list(call.transcript or []), dict(call.collected or {})
    flag_modified(call, "transcript")
    flag_modified(call, "collected")
    db.commit()


def finalize_call(db: Session, business: Business, call: ReceptionistCall) -> dict:
    """Clôt l'appel, calcule le résumé et prévient le gérant (une seule fois)."""
    if call.status == "completed" and call.notified:
        return call.summary or {}
    summary = rc.build_summary(business, call)
    has_request = any(t.get("role") == "caller" for t in (call.transcript or [])) or bool(call.recording_url)
    call.summary, call.urgent, call.recovered = summary, summary["urgence"], has_request
    call.status, call.ended_at = "completed", call.ended_at or _now()
    db.commit()
    # Un appel IA resté muet n'est pas notifié ; la messagerie l'est toujours (appel manqué).
    if not call.notified and (has_request or call.mode == "voicemail"):
        rc.notify_owner(business, _addon(db, business.id), summary)
        call.notified = True
        db.commit()
    return summary


def _base(business_id: str) -> str:
    return f"/receptionist/voice/{urllib.parse.quote(business_id, safe='')}"


# ──────────────────────────────────────────────────────────────────────────────
# Webhooks Twilio
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/receptionist/voice/{business_id}")
async def receptionist_incoming(business_id: str, request: Request, db: Session = Depends(get_db)):
    params = await twilio_params(request)
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        return _xml(rc.twiml_hangup("Ce numéro n'est pas disponible pour le moment. Merci de rappeler plus tard."))
    if not addon_ai_enabled(_addon(db, business_id)):
        _call(db, business_id, params, mode="voicemail")
        return _xml(rc.twiml_voicemail(b, f"{_base(business_id)}/voicemail"))
    call = _call(db, business_id, params, mode="ai")
    hello = rc.greeting(b)
    call.transcript = [{"role": "assistant", "text": hello}]
    _save(db, call)
    return _xml(rc.twiml_gather(hello, f"{_base(business_id)}/turn"))


@router.post("/receptionist/voice/{business_id}/turn")
async def receptionist_turn(business_id: str, request: Request, db: Session = Depends(get_db)):
    params = await twilio_params(request)
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        return _xml(rc.twiml_hangup("Au revoir."))
    call = _call(db, business_id, params, mode="ai")
    speech = (params.get("SpeechResult") or "").strip()
    transcript, collected = list(call.transcript or []), dict(call.collected or {})

    if not speech:
        collected["_silence"] = collected.get("_silence", 0) + 1
        call.collected = collected
        _save(db, call)
        if collected["_silence"] > MAX_SILENCES:
            finalize_call(db, b, call)
            return _xml(rc.twiml_hangup("Je ne vous entends pas. Vous pouvez rappeler à tout moment. Au revoir."))
        return _xml(rc.twiml_gather("Je vous écoute, que puis-je noter pour vous ?", f"{_base(business_id)}/turn"))

    transcript.append({"role": "caller", "text": speech})
    result = rc.next_turn(b, transcript, collected, speech)
    for key, value in (result.get("fields") or {}).items():
        if value not in ("", None) or key == "_pending":
            collected[key] = value
    reply = str(result["reply"]).strip()
    transcript.append({"role": "assistant", "text": reply})
    call.transcript, call.collected, call.turns = transcript, collected, (call.turns or 0) + 1
    _save(db, call)

    if result.get("done") or call.turns >= rc.MAX_TURNS:
        if not result.get("done"):
            reply += " Merci, j'ai bien tout noté, vous serez rappelé très vite. Au revoir !"
        finalize_call(db, b, call)
        return _xml(rc.twiml_hangup(reply))
    return _xml(rc.twiml_gather(reply, f"{_base(business_id)}/turn"))


@router.post("/receptionist/voice/{business_id}/voicemail")
async def receptionist_voicemail(business_id: str, request: Request, db: Session = Depends(get_db)):
    params = await twilio_params(request)
    b = db.query(Business).filter(Business.id == business_id).first()
    if b:
        call = _call(db, business_id, params, mode="voicemail")
        if params.get("RecordingUrl"):
            call.recording_url = params["RecordingUrl"]
            db.commit()
        finalize_call(db, b, call)
    return _xml(rc.twiml_hangup("Merci, votre message a bien été transmis. Au revoir."))


@router.post("/receptionist/voice/{business_id}/status")
async def receptionist_status_callback(business_id: str, request: Request, db: Session = Depends(get_db)):
    params = await twilio_params(request)
    b = db.query(Business).filter(Business.id == business_id).first()
    call = db.query(ReceptionistCall).filter(ReceptionistCall.call_sid == params.get("CallSid", "")).first()
    if b and call and params.get("CallStatus", "completed") in ("completed", "busy", "no-answer", "failed", "canceled"):
        finalize_call(db, b, call)  # l'appelant a raccroché en cours de conversation
    return Response(status_code=204)


WHATSAPP_IDLE = datetime.timedelta(hours=6)


@router.post("/receptionist/whatsapp/{business_id}")
async def receptionist_whatsapp(business_id: str, request: Request, db: Session = Depends(get_db)):
    """Message WhatsApp d'un client : même qualification que l'appel, réponse en <Message>."""
    params = await twilio_params(request)
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        return _xml(rc.twiml())
    sender = (params.get("From") or "").removeprefix("whatsapp:")
    text = (params.get("Body") or "").strip()
    if not addon_ai_enabled(_addon(db, business_id)):
        call = ReceptionistCall(call_sid=f"wa-{uuid.uuid4().hex}", business_id=business_id, from_number=sender,
                                mode="whatsapp_message", transcript=[{"role": "caller", "text": text}] if text else [],
                                collected={})
        db.add(call)
        db.commit()
        finalize_call(db, b, call)
        name = rc.business_facts(b)["name"]
        return _xml(rc.twiml_message(f"Merci pour votre message, {name} vous recontacte rapidement."))

    call = (db.query(ReceptionistCall)
            .filter(ReceptionistCall.business_id == business_id, ReceptionistCall.mode == "whatsapp",
                    ReceptionistCall.from_number == sender, ReceptionistCall.status == "in_progress",
                    ReceptionistCall.created_at >= _now() - WHATSAPP_IDLE)
            .order_by(ReceptionistCall.created_at.desc()).first())
    if not call:
        call = ReceptionistCall(call_sid=f"wa-{uuid.uuid4().hex}", business_id=business_id, from_number=sender,
                                mode="whatsapp", transcript=[], collected={})
        db.add(call)
        db.commit()
    if not text:
        return _xml(rc.twiml_message("Bonjour, que puis-je noter pour vous ?"))
    transcript, collected = list(call.transcript or []), dict(call.collected or {})
    transcript.append({"role": "caller", "text": text})
    result = rc.next_turn(b, transcript, collected, text)
    for key, value in (result.get("fields") or {}).items():
        if value not in ("", None) or key == "_pending":
            collected[key] = value
    reply = str(result["reply"]).strip()
    transcript.append({"role": "assistant", "text": reply})
    call.transcript, call.collected, call.turns = transcript, collected, (call.turns or 0) + 1
    _save(db, call)
    if result.get("done") or call.turns >= rc.MAX_TURNS:
        finalize_call(db, b, call)
    return _xml(rc.twiml_message(reply))


# ──────────────────────────────────────────────────────────────────────────────
# Statut, statistiques, activation
# ──────────────────────────────────────────────────────────────────────────────

def receptionist_state(db: Session, b: Business) -> dict:
    addon = _addon(db, b.id)
    q = db.query(ReceptionistCall).filter(ReceptionistCall.business_id == b.id)
    since = _now() - datetime.timedelta(days=30)
    recent = q.order_by(ReceptionistCall.created_at.desc()).limit(10).all()
    catalog = ADDON_CATALOG[RECEPTIONIST_ADDON]
    return {
        "addon": RECEPTIONIST_ADDON,
        "name": catalog["name"],
        "price": catalog["price"],
        "trial_days": catalog["trial_days"],
        "status": addon_status(addon),
        "days_left": days_left(addon),
        "trial_started_at": addon.trial_started_at.isoformat() + "Z" if addon and addon.trial_started_at else None,
        "trial_ends_at": addon.trial_ends_at.isoformat() + "Z" if addon and addon.trial_ends_at else None,
        "twilio_number": os.getenv("TWILIO_PHONE_NUMBER", ""),
        "notify_channels": rc.notify_channels(addon),
        "forward_code": f"**61*{os.getenv('TWILIO_PHONE_NUMBER', '')}#" if os.getenv("TWILIO_PHONE_NUMBER") else "",
        "stats": {
            "received": q.count(),
            "recovered": q.filter(ReceptionistCall.recovered.is_(True)).count(),
            "urgent": q.filter(ReceptionistCall.urgent.is_(True)).count(),
            "recovered_30d": q.filter(ReceptionistCall.recovered.is_(True), ReceptionistCall.created_at >= since).count(),
        },
        "recent_calls": [
            {"at": c.created_at.isoformat() + "Z" if c.created_at else None, "from": c.from_number, "mode": c.mode,
             "urgent": bool(c.urgent), "recovered": bool(c.recovered), "summary": c.summary}
            for c in recent
        ],
    }


def activate(db: Session, b: Business, data: dict | None = None, admin: bool = False) -> dict:
    data = data or {}
    addon = _addon(db, b.id)
    if not addon:
        addon = ReceptionistAddon(business_id=b.id)
        db.add(addon)
    start_addon_trial(addon, _now())
    for key in ("notify_phone", "notify_email"):
        if isinstance(data.get(key), str) and data[key].strip():
            setattr(addon, key, data[key].strip())
    if isinstance(data.get("notify_channels"), list):
        chans = [c for c in data["notify_channels"] if c in rc.NOTIFY_CHANNELS]
        if chans:
            addon.notify_channels = list(dict.fromkeys(chans))
    if admin and "paid_active" in data:
        addon.paid_active = bool(data["paid_active"])
    db.commit()
    return receptionist_state(db, b)


@router.get("/client/space/receptionist")
async def client_receptionist(b: Business = Depends(client_business), db: Session = Depends(get_db)):
    return receptionist_state(db, b)


@router.post("/client/space/receptionist/activate")
async def client_receptionist_activate(request: Request, b: Business = Depends(client_business),
                                       db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        data = {}
    return activate(db, b, data if isinstance(data, dict) else {})


def _admin_business(db: Session, business_id: str) -> Business:
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Business introuvable")
    return b


@router.get("/businesses/{business_id}/receptionist")
async def admin_receptionist(business_id: str, db: Session = Depends(get_db)):
    return receptionist_state(db, _admin_business(db, business_id))


@router.post("/businesses/{business_id}/receptionist/activate")
async def admin_receptionist_activate(business_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        data = {}
    return activate(db, _admin_business(db, business_id), data if isinstance(data, dict) else {}, admin=True)
