"""Routes du module Réceptionniste IA.

- Webhooks Twilio Voice (publics, protégés par la signature X-Twilio-Signature) :
    POST /receptionist/voice/{business_id}            appel entrant
    POST /receptionist/voice/{business_id}/turn       réponse vocale de l'appelant
    POST /receptionist/voice/{business_id}/voicemail  fin d'enregistrement (après l'essai)
    POST /receptionist/voice/{business_id}/status     statusCallback (raccroché)
    POST /receptionist/whatsapp/{business_id}         message WhatsApp entrant (même logique, texte)
    POST /receptionist/voice/{business_id}/relay-end  fin de session ConversationRelay (moteur relay)
    WS   /receptionist/relay/{business_id}            ConversationRelay : texte en temps réel (moteur relay)
- Espace client (session X-Client-Session) :
    GET  /client/space/receptionist                   statut de l'essai, réglages, statistiques
    POST /client/space/receptionist/activate          démarre l'essai gratuit de 30 jours
    PUT  /client/space/receptionist/settings          réglages de l'agent (+ fin d'onboarding)
    POST /client/space/receptionist/test              simulateur de conversation (aucun appel, aucun SMS)
- Cockpit admin (jeton admin) : mêmes routes sous /businesses/{business_id}/receptionist[...]
    POST .../activate {"paid_active": bool, "notify_phone", "notify_email", "notify_channels": [...]}
    GET  .../diagnostic  configuration Twilio et URLs des webhooks à coller dans la console
"""
import asyncio
import datetime
import os
import urllib.parse
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from backend.client_space_api import client_business, frontend_url
from backend.models.database import Business, ReceptionistAddon, ReceptionistCall, get_db
from backend.services import integrations as itg
from backend.services import receptionist as rc
from backend.services.plans import (
    ADDON_CATALOG, CONNECT_ADDON, RECEPTIONIST_ADDON, addon_ai_enabled, addon_status, days_left, plan_includes_addon,
    start_addon_trial,
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


# ──────────────────────────────────────────────────────────────────────────────
# Pack Connecté (Google Agenda, Google Sheets, webhook)
# ──────────────────────────────────────────────────────────────────────────────

def connect_status(b: Business, addon: ReceptionistAddon | None) -> str:
    """included (Élite) | active (souscrit) | trial (offert pendant l'essai) | inactive."""
    if plan_includes_addon(b, CONNECT_ADDON):
        return "included"
    if addon is not None and addon.connect_paid:
        return "active"
    if addon_status(addon) == "trial":
        return "trial"
    return "inactive"


def connect_enabled(b: Business, addon: ReceptionistAddon | None) -> bool:
    return connect_status(b, addon) != "inactive"


def _save_integrations(db: Session, addon: ReceptionistAddon, cfg: dict) -> None:
    addon.integrations = cfg
    flag_modified(addon, "integrations")
    db.commit()


def _note_error(db: Session, addon: ReceptionistAddon, cfg: dict, where: str, exc: Exception) -> None:
    print(f"[RECEPTIONNISTE] Pack Connecté – {where} : {exc}")
    cfg["google"]["last_error"] = f"{where} : {str(exc)[:160]}"
    try:
        _save_integrations(db, addon, cfg)
    except Exception:
        db.rollback()


def booking_slots(db: Session, b: Business, collected: dict) -> list[dict] | None:
    """Créneaux libres proposés à l'IA, lus une seule fois par appel (gardés dans collected["_slots"])."""
    if "_slots" in collected:
        return collected["_slots"] or None
    addon = _addon(db, b.id)
    cfg = itg.config(addon)
    slots: list[dict] = []
    if connect_enabled(b, addon) and itg.calendar_on(cfg):
        try:
            slots = itg.free_slots(b, cfg)
            print(f"[RECEPTIONNISTE] Agenda : {len(slots)} créneau(x) libre(s) proposé(s)")
        except Exception as exc:
            _note_error(db, addon, cfg, "Lecture de l'agenda", exc)
    collected["_slots"] = slots
    return slots or None


def book_appointment(db: Session, b: Business, summary: dict) -> None:
    """Crée l'événement Google Agenda du créneau choisi ; en cas d'échec, le RDV redevient un simple souhait."""
    if not summary.get("rdv_iso"):
        return
    addon = _addon(db, b.id)
    cfg = itg.config(addon)
    if not (connect_enabled(b, addon) and itg.calendar_on(cfg)):
        summary["rdv"] = summary["rdv_iso"] = ""
        return
    c = summary.get("caller") or {}
    title = f"RDV {c.get('nom') or 'client'} – {summary.get('motif') or 'demande'}"[:120]
    desc = rc.format_sms(b, summary) + "\n\nRéservé par votre réceptionniste IA Pulse Locale PME."
    try:
        itg.create_event(cfg, summary["rdv_iso"], title, desc)
    except Exception as exc:
        _note_error(db, addon, cfg, "Réservation dans l'agenda", exc)
        summary["creneau"] = summary.get("creneau") or f"{summary['rdv']} (à confirmer)"
        summary["rdv"] = summary["rdv_iso"] = ""


def push_integrations(db: Session, b: Business, call: ReceptionistCall, summary: dict) -> dict:
    """Ligne Google Sheets + webhook après chaque appel. Ne lève jamais."""
    done = {}
    try:
        addon = _addon(db, b.id)
        if not connect_enabled(b, addon):
            return done
        cfg = itg.config(addon)
        if itg.sheets_on(cfg):
            try:
                itg.append_row(itg.access_token(cfg), cfg["google"]["sheet_id"],
                               itg.sheet_row(summary, cfg["google"].get("timezone") or itg.DEFAULT_TZ, call.created_at))
                done["sheets"] = True
            except Exception as exc:
                _note_error(db, addon, cfg, "Ajout au tableur", exc)
                done["sheets"] = False
        hook = cfg["webhook"]
        if hook.get("url") and hook.get("enabled", True):
            try:
                status = itg.send_webhook(hook["url"], hook.get("secret") or "", itg.webhook_payload(b, summary, call))
            except Exception as exc:
                print(f"[RECEPTIONNISTE] webhook en échec ({exc})")
                status = 0
            hook["last_status"], hook["last_at"] = status, _now().isoformat() + "Z"
            cfg["webhook"] = hook
            _save_integrations(db, addon, cfg)
            done["webhook"] = 200 <= status < 300
    except Exception as exc:
        print(f"[RECEPTIONNISTE] Pack Connecté indisponible ({exc})")
    return done


def finalize_call(db: Session, business: Business, call: ReceptionistCall) -> dict:
    """Clôt l'appel, calcule le résumé et prévient le gérant (une seule fois)."""
    if call.status == "completed" and call.notified:
        return call.summary or {}
    summary = rc.build_summary(business, call)
    has_request = any(t.get("role") == "caller" for t in (call.transcript or [])) or bool(call.recording_url)
    if not call.notified and has_request:
        book_appointment(db, business, summary)  # Pack Connecté : rendez-vous dans Google Agenda
    call.summary, call.urgent, call.recovered = summary, summary["urgence"], has_request
    call.status, call.ended_at = "completed", call.ended_at or _now()
    db.commit()
    # Un appel IA resté muet n'est pas notifié ; la messagerie l'est toujours (appel manqué).
    if not call.notified and (has_request or call.mode == "voicemail"):
        rc.notify_owner(business, _addon(db, business.id), summary)
        call.notified = True
        db.commit()
        push_integrations(db, business, call, summary)  # Pack Connecté : Google Sheets + webhook
    return summary


def _base(business_id: str) -> str:
    return f"/receptionist/voice/{urllib.parse.quote(business_id, safe='')}"


AI_CALL_MODES = ("ai", "whatsapp")


def trial_calls_used(db: Session, b: Business, addon: ReceptionistAddon | None) -> int:
    """Appels (ou conversations WhatsApp) pris en charge par l'IA depuis le début de l'essai."""
    if addon is None or not addon.trial_started_at:
        return 0
    return (db.query(ReceptionistCall)
            .filter(ReceptionistCall.business_id == b.id, ReceptionistCall.mode.in_(AI_CALL_MODES),
                    ReceptionistCall.created_at >= addon.trial_started_at)
            .count())


def ai_allowed(db: Session, b: Business, addon: ReceptionistAddon | None, ongoing: bool = False) -> bool:
    """L'IA répond-elle ? Essai : 30 jours ET 60 appels maximum (au-delà : simple messagerie).
    Une conversation déjà commencée va toujours à son terme."""
    included = plan_includes_addon(b)
    if not addon_ai_enabled(addon, included=included):
        return False
    if included or addon_status(addon) == "active" or ongoing:
        return True
    return trial_calls_used(db, b, addon) < ADDON_CATALOG[RECEPTIONIST_ADDON]["trial_calls"]


def _settings(db: Session, business_id: str) -> dict:
    return rc.addon_settings(_addon(db, business_id))


def apply_turn(db: Session, b: Business, call: ReceptionistCall, text: str, settings: dict,
               timeout: float | None = None) -> tuple[str, bool]:
    """Un tour de conversation (voix ou WhatsApp) : LLM, champs collectés, sauvegarde. → (réponse, terminé)."""
    transcript, collected = list(call.transcript or []), dict(call.collected or {})
    transcript.append({"role": "caller", "text": text})
    slots = booking_slots(db, b, collected)
    result = rc.next_turn(b, transcript, collected, text, settings, timeout=timeout, slots=slots)
    for key, value in (result.get("fields") or {}).items():
        if value not in ("", None) or key == "_pending":
            collected[key] = value
    reply = str(result["reply"]).strip()
    transcript.append({"role": "assistant", "text": reply})
    call.transcript, call.collected, call.turns = transcript, collected, (call.turns or 0) + 1
    _save(db, call)
    done = bool(result.get("done")) or call.turns >= rc.MAX_TURNS
    if done and not result.get("done"):
        reply += " Merci, j'ai bien tout noté, vous serez rappelé très vite. Au revoir !"
    return reply, done


def _ws_base(request_like) -> str:
    """wss://hôte public de l'API (ConversationRelay exige une URL WebSocket sécurisée)."""
    base = os.getenv("TWILIO_WEBHOOK_BASE_URL", "").strip().rstrip("/")
    if not base:
        proto = request_like.headers.get("x-forwarded-proto", request_like.url.scheme).split(",")[0].strip()
        host = request_like.headers.get("x-forwarded-host") or request_like.headers.get("host") or request_like.url.netloc
        base = f"{proto}://{host}"
    return base.replace("https://", "wss://", 1).replace("http://", "ws://", 1)


# ──────────────────────────────────────────────────────────────────────────────
# Webhooks Twilio
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/receptionist/voice/{business_id}")
async def receptionist_incoming(business_id: str, request: Request, db: Session = Depends(get_db)):
    params = await twilio_params(request)
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        return _xml(rc.twiml_hangup("Ce numéro n'est pas disponible pour le moment. Merci de rappeler plus tard."))
    addon = _addon(db, business_id)
    settings = rc.addon_settings(addon)
    voice = rc.say_voice(settings)
    if not ai_allowed(db, b, addon):
        _call(db, business_id, params, mode="voicemail")
        return _xml(rc.twiml_voicemail(b, f"{_base(business_id)}/voicemail", voice))
    call = _call(db, business_id, params, mode="ai")
    hello = rc.greeting(b, settings)
    call.transcript = [{"role": "assistant", "text": hello}]
    _save(db, call)
    if rc.engine() == "relay":
        ws_url = f"{_ws_base(request)}/receptionist/relay/{urllib.parse.quote(business_id, safe='')}"
        return _xml(rc.twiml_relay(ws_url, hello, settings, action=f"{_base(business_id)}/relay-end"))
    return _xml(rc.twiml_gather(hello, f"{_base(business_id)}/turn", voice))


@router.post("/receptionist/voice/{business_id}/turn")
async def receptionist_turn(business_id: str, request: Request, db: Session = Depends(get_db)):
    params = await twilio_params(request)
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        return _xml(rc.twiml_hangup("Au revoir."))
    settings = _settings(db, business_id)
    voice = rc.say_voice(settings)
    call = _call(db, business_id, params, mode="ai")
    speech = (params.get("SpeechResult") or "").strip()

    if not speech:
        collected = dict(call.collected or {})
        collected["_silence"] = collected.get("_silence", 0) + 1
        call.collected = collected
        _save(db, call)
        if collected["_silence"] > MAX_SILENCES:
            finalize_call(db, b, call)
            return _xml(rc.twiml_hangup("Je ne vous entends pas. Vous pouvez rappeler à tout moment. Au revoir.", voice))
        return _xml(rc.twiml_gather("Je vous écoute, que puis-je noter pour vous ?", f"{_base(business_id)}/turn", voice))

    reply, done = await run_in_threadpool(apply_turn, db, b, call, speech, settings, rc.VOICE_LLM_TIMEOUT)
    if done:
        await run_in_threadpool(finalize_call, db, b, call)
        return _xml(rc.twiml_hangup(reply, voice))
    return _xml(rc.twiml_gather(reply, f"{_base(business_id)}/turn", voice))


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
    return _xml(rc.twiml_hangup("Merci, votre message a bien été transmis. Au revoir.", rc.say_voice(_settings(db, business_id))))


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
    ongoing = (db.query(ReceptionistCall)
               .filter(ReceptionistCall.business_id == business_id, ReceptionistCall.mode == "whatsapp",
                       ReceptionistCall.from_number == sender, ReceptionistCall.status == "in_progress",
                       ReceptionistCall.created_at >= _now() - WHATSAPP_IDLE).first() is not None)
    if not ai_allowed(db, b, _addon(db, business_id), ongoing=ongoing):
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
    # Réponse dans la requête (CPU alloué par Cloud Run), IA bornée à 11 s : Twilio attend au plus 15 s.
    # Une tâche de fond après la réponse tourne avec un CPU bridé sur Cloud Run (≈ 1 min de latence).
    reply, done = await run_in_threadpool(apply_turn, db, b, call, text, _settings(db, business_id),
                                          rc.TEXT_LLM_TIMEOUT)
    if done:
        await run_in_threadpool(finalize_call, db, b, call)
    return _xml(rc.twiml_message(reply))


# ──────────────────────────────────────────────────────────────────────────────
# Moteur « relay » : Twilio ConversationRelay (RECEPTIONIST_ENGINE=relay)
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/receptionist/voice/{business_id}/relay-end")
async def receptionist_relay_end(business_id: str, request: Request, db: Session = Depends(get_db)):
    """Action du <Connect> : la session ConversationRelay est terminée → on raccroche."""
    params = await twilio_params(request)
    b = db.query(Business).filter(Business.id == business_id).first()
    call = db.query(ReceptionistCall).filter(ReceptionistCall.call_sid == params.get("CallSid", "")).first()
    if b and call:
        finalize_call(db, b, call)
    return _xml(rc.twiml("<Hangup/>"))


def _hangup_delay(text: str) -> float:
    """Laisse la synthèse vocale finir la dernière phrase avant de clore la session."""
    return min(15.0, 1.5 + 0.065 * len(text))


@router.websocket("/receptionist/relay/{business_id}")
async def receptionist_relay(websocket: WebSocket, business_id: str, db: Session = Depends(get_db)):
    """Twilio envoie des messages JSON (setup, prompt, interrupt…) ; on répond par des messages text/end."""
    path = websocket.url.path
    signature = websocket.headers.get("x-twilio-signature", "")
    base = _ws_base(websocket)
    candidates = {base + path, base.replace("wss://", "https://", 1).replace("ws://", "http://", 1) + path}
    if not any(rc.valid_signature(u, {}, signature) for u in candidates):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    b = db.query(Business).filter(Business.id == business_id).first()
    settings = _settings(db, business_id)
    call = None
    try:
        while True:
            msg = await websocket.receive_json()
            kind = msg.get("type")
            if kind == "setup":
                call = _call(db, business_id, {"CallSid": msg.get("callSid", ""), "From": msg.get("from", "")}, mode="ai")
            elif kind == "prompt" and b is not None:
                text = str(msg.get("voicePrompt") or "").strip()
                if not text:
                    continue
                if call is None:
                    call = _call(db, business_id, {}, mode="ai")
                reply, done = await run_in_threadpool(apply_turn, db, b, call, text, settings, rc.VOICE_LLM_TIMEOUT)
                await websocket.send_json({"type": "text", "token": reply, "last": True})
                if done:
                    await run_in_threadpool(finalize_call, db, b, call)
                    await asyncio.sleep(_hangup_delay(reply))
                    await websocket.send_json({"type": "end"})
            elif kind == "error":
                print(f"[RECEPTIONNISTE] ConversationRelay : {msg.get('description')}")
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # ne jamais laisser l'appel sans résumé
        print(f"[RECEPTIONNISTE] relay interrompu ({exc})")
    finally:
        if b is not None and call is not None:
            try:
                finalize_call(db, b, call)
            except Exception as exc:
                print(f"[RECEPTIONNISTE] résumé relay impossible ({exc})")


# ──────────────────────────────────────────────────────────────────────────────
# Statut, statistiques, activation
# ──────────────────────────────────────────────────────────────────────────────

def _iso(dt) -> str | None:
    return dt.isoformat() + "Z" if dt else None


def receptionist_state(db: Session, b: Business) -> dict:
    addon = _addon(db, b.id)
    settings = rc.addon_settings(addon)
    q = db.query(ReceptionistCall).filter(ReceptionistCall.business_id == b.id, ReceptionistCall.mode != "test")
    since = _now() - datetime.timedelta(days=30)
    recent = q.order_by(ReceptionistCall.created_at.desc()).limit(10).all()
    catalog = ADDON_CATALOG[RECEPTIONIST_ADDON]
    included = plan_includes_addon(b)
    month_start = _now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    calls_month = q.filter(ReceptionistCall.created_at >= month_start, ReceptionistCall.recovered.is_(True)).count()
    trial_used = trial_calls_used(db, b, addon)
    number = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    detected = rc.detect_profession(b)
    return {
        "addon": RECEPTIONIST_ADDON,
        "name": catalog["name"],
        "price": catalog["price"],
        "trial_days": catalog["trial_days"],
        "status": addon_status(addon, included=included),
        "days_left": days_left(addon, included=included),
        "included_in_plan": included,
        "included_calls": catalog["included_calls"],
        "trial_calls": catalog["trial_calls"],
        "trial_calls_used": trial_used,
        "trial_limit_reached": addon_status(addon, included=included) == "trial" and trial_used >= catalog["trial_calls"],
        "extra_call_price": catalog["extra_call_price"],
        "extra_call_price_ttc": catalog["extra_call_price_ttc"],
        "calls_this_month": calls_month,
        "trial_started_at": _iso(addon.trial_started_at) if addon else None,
        "trial_ends_at": _iso(addon.trial_ends_at) if addon else None,
        "onboarded": bool(addon and addon.onboarded_at),
        "onboarded_at": _iso(addon.onboarded_at) if addon else None,
        "twilio_number": number,
        "whatsapp_number": os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip().removeprefix("whatsapp:"),
        "notify_channels": rc.notify_channels(addon),
        "notify_phone": (addon.notify_phone if addon else None) or b.owner_phone or "",
        "notify_email": (addon.notify_email if addon else None) or b.owner_email or "",
        "settings": settings,
        "default_greeting": rc.default_greeting(b, settings),
        "questions": [q_ for _, q_ in rc.questions_for(b, settings)],
        "forward_code": f"**61*{number}#" if number else "",
        "forward_codes": rc.forward_codes(number, settings),
        "options": {
            "voices": [{"id": k, "label": v["label"]} for k, v in rc.VOICES.items()],
            "professions": [{"id": k, "label": v["metier"] or "Autre activité"} for k, v in rc.PROFESSIONS.items()],
            "detected_profession": detected,
            "forward_modes": [{"id": k, "label": v["label"]} for k, v in rc.FORWARD_MODES.items()],
            "channels": list(rc.NOTIFY_CHANNELS),
        },
        "connect": {
            "status": connect_status(b, addon),
            "price": ADDON_CATALOG[CONNECT_ADDON]["price"],
            **itg.public_status(itg.config(addon)),
        },
        "engine": rc.engine(),
        "stats": {
            "received": q.count(),
            "recovered": q.filter(ReceptionistCall.recovered.is_(True)).count(),
            "urgent": q.filter(ReceptionistCall.urgent.is_(True)).count(),
            "recovered_30d": q.filter(ReceptionistCall.recovered.is_(True), ReceptionistCall.created_at >= since).count(),
        },
        "recent_calls": [
            {"at": _iso(c.created_at), "from": c.from_number, "mode": c.mode,
             "urgent": bool(c.urgent), "recovered": bool(c.recovered), "summary": c.summary}
            for c in recent
        ],
    }


def _ensure_addon(db: Session, b: Business) -> ReceptionistAddon:
    addon = _addon(db, b.id)
    if not addon:
        addon = ReceptionistAddon(business_id=b.id)
        db.add(addon)
    return addon


def _apply_notify(addon: ReceptionistAddon, data: dict) -> None:
    for key in ("notify_phone", "notify_email"):
        if isinstance(data.get(key), str):
            setattr(addon, key, data[key].strip() or None)
    if isinstance(data.get("notify_channels"), list):
        chans = [c for c in data["notify_channels"] if c in rc.NOTIFY_CHANNELS]
        if chans:
            addon.notify_channels = list(dict.fromkeys(chans))


def activate(db: Session, b: Business, data: dict | None = None, admin: bool = False) -> dict:
    data = data or {}
    addon = _ensure_addon(db, b)
    start_addon_trial(addon, _now())
    _apply_notify(addon, data)
    if admin and "paid_active" in data:
        addon.paid_active = bool(data["paid_active"])
    db.commit()
    return receptionist_state(db, b)


def update_settings(db: Session, b: Business, data: dict) -> dict:
    """Enregistre les réglages de l'agent. {"settings": {...}, notify_*, "onboarded": true}."""
    if addon_status(_addon(db, b.id), included=plan_includes_addon(b)) == "inactive":
        raise HTTPException(status_code=409, detail="Activez d'abord la Réceptionniste IA.")
    addon = _ensure_addon(db, b)  # formule Élite : la ligne de réglages peut ne pas encore exister
    if isinstance(data.get("settings"), dict):
        merged = {**rc.addon_settings(addon), **data["settings"]}
        addon.settings = rc.normalize_settings(merged)
        flag_modified(addon, "settings")
    phone = data.get("notify_phone")
    if isinstance(phone, str) and phone.strip() and not rc.to_e164(phone):
        raise HTTPException(status_code=422, detail="Numéro de téléphone invalide (ex. 06 12 34 56 78).")
    _apply_notify(addon, data)
    if data.get("onboarded") is True and not addon.onboarded_at:
        addon.onboarded_at = _now()
    elif data.get("onboarded") is False:
        addon.onboarded_at = None
    db.commit()
    return receptionist_state(db, b)


MAX_TEST_MESSAGES = 30


def simulate(db: Session, b: Business, data: dict, admin: bool = False) -> dict:
    """Simulateur : même IA, même prompt, mêmes réglages qu'au téléphone. Rien n'est envoyé ni stocké.

    Entrée : {"history": [{"role": "caller"|"assistant", "text"}], "collected": {}, "message": "",
              "settings": {...brouillon facultatif...}}
    """
    addon = _addon(db, b.id)
    if not admin and not addon_ai_enabled(addon, included=plan_includes_addon(b)):
        raise HTTPException(status_code=409, detail="Le test est disponible pendant l'essai ou l'abonnement.")
    settings = rc.addon_settings(addon)
    if isinstance(data.get("settings"), dict):
        settings = rc.normalize_settings({**settings, **data["settings"]})
    message = str(data.get("message") or "").strip()[:500]
    if not message:
        return {"reply": rc.greeting(b, settings), "collected": {}, "done": False, "summary": None,
                "notification": None}
    history = [
        {"role": "caller" if h.get("role") == "caller" else "assistant", "text": str(h.get("text") or "")[:500]}
        for h in (data.get("history") or []) if isinstance(h, dict)
    ][-MAX_TEST_MESSAGES:]
    collected = data.get("collected") if isinstance(data.get("collected"), dict) else {}
    call = ReceptionistCall(call_sid="test", business_id=b.id, from_number="", mode="test",
                            transcript=history, collected=dict(collected))
    history = history + [{"role": "caller", "text": message}]
    slots = booking_slots(db, b, collected)  # test : les vrais créneaux sont proposés, rien n'est réservé
    result = rc.next_turn(b, history, dict(collected), message, settings, slots=slots)
    for key, value in (result.get("fields") or {}).items():
        if value not in ("", None) or key == "_pending":
            collected[key] = value
    reply = str(result["reply"]).strip()
    turns = sum(1 for h in history if h["role"] == "caller")
    done = bool(result.get("done")) or turns >= rc.MAX_TURNS
    summary = notification = None
    if done:
        call.transcript, call.collected = history + [{"role": "assistant", "text": reply}], collected
        summary = rc.build_summary(b, call)
        summary["mode"] = "ai"
        notification = rc.format_sms(b, summary)
    return {"reply": reply, "collected": collected, "done": done, "summary": summary, "notification": notification}


def diagnostic(request: Request, b: Business) -> dict:
    """Ce qu'il faut configurer côté Twilio, et ce qui manque."""
    # Twilio appelle directement Cloud Run (*.run.app) : Firebase Hosting ne relaie pas /receptionist/**
    # ni les WebSockets. On prend donc l'hôte Cloud Run (Host), et non x-forwarded-host (domaine Firebase).
    proto = request.headers.get("x-forwarded-proto", request.url.scheme).split(",")[0].strip()
    host = request.headers.get("host") or request.url.netloc
    if host.endswith(".run.app"):
        proto = "https"
    base = os.getenv("TWILIO_WEBHOOK_BASE_URL", "").strip().rstrip("/") or f"{proto}://{host}"
    bid = urllib.parse.quote(b.id, safe="")
    env = {k: bool(os.getenv(k, "").strip()) for k in (
        "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER", "TWILIO_WHATSAPP_NUMBER",
        "TWILIO_WEBHOOK_BASE_URL")}
    missing = [k for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER") if not env[k]]
    return {
        "env": env,
        "missing": missing,
        "ready": not missing,
        "engine": rc.engine(),
        "public_base_url": base,
        "https": base.startswith("https://"),
        "webhooks": {
            "voice_incoming": f"{base}/receptionist/voice/{bid}",
            "voice_status": f"{base}/receptionist/voice/{bid}/status",
            "whatsapp_incoming": f"{base}/receptionist/whatsapp/{bid}",
            "relay_websocket": base.replace("https://", "wss://", 1).replace("http://", "ws://", 1) + f"/receptionist/relay/{bid}",
        },
    }


async def _json(request: Request) -> dict:
    try:
        data = await request.json()
    except Exception:
        data = {}
    return data if isinstance(data, dict) else {}


@router.get("/client/space/receptionist")
async def client_receptionist(b: Business = Depends(client_business), db: Session = Depends(get_db)):
    return receptionist_state(db, b)


@router.post("/client/space/receptionist/activate")
async def client_receptionist_activate(request: Request, b: Business = Depends(client_business),
                                       db: Session = Depends(get_db)):
    return activate(db, b, await _json(request))


@router.put("/client/space/receptionist/settings")
async def client_receptionist_settings(request: Request, b: Business = Depends(client_business),
                                       db: Session = Depends(get_db)):
    return update_settings(db, b, await _json(request))


@router.post("/client/space/receptionist/test")
async def client_receptionist_test(request: Request, b: Business = Depends(client_business),
                                   db: Session = Depends(get_db)):
    data = await _json(request)
    return await run_in_threadpool(simulate, db, b, data)


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
    return activate(db, _admin_business(db, business_id), await _json(request), admin=True)


@router.put("/businesses/{business_id}/receptionist/settings")
async def admin_receptionist_settings(business_id: str, request: Request, db: Session = Depends(get_db)):
    return update_settings(db, _admin_business(db, business_id), await _json(request))


@router.post("/businesses/{business_id}/receptionist/test")
async def admin_receptionist_test(business_id: str, request: Request, db: Session = Depends(get_db)):
    b = _admin_business(db, business_id)
    data = await _json(request)
    return await run_in_threadpool(simulate, db, b, data, True)


@router.get("/businesses/{business_id}/receptionist/diagnostic")
async def admin_receptionist_diagnostic(business_id: str, request: Request, db: Session = Depends(get_db)):
    return diagnostic(request, _admin_business(db, business_id))


# ──────────────────────────────────────────────────────────────────────────────
# Pack Connecté : routes
# ──────────────────────────────────────────────────────────────────────────────

def google_redirect_uri() -> str:
    """URL de retour déclarée dans Google Cloud Console (site public, réécrite vers l'API par Firebase)."""
    return (os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
            or f"{frontend_url()}/integrations/google/callback")


def _connect_addon(db: Session, b: Business) -> ReceptionistAddon:
    addon = _addon(db, b.id)
    if not connect_enabled(b, addon):
        raise HTTPException(status_code=409, detail=(
            f"Le Pack Connecté ({ADDON_CATALOG[CONNECT_ADDON]['price']} € HT / mois) n'est pas actif : "
            "il est offert pendant l'essai de la réceptionniste et inclus dans la formule Élite."))
    return addon or _ensure_addon(db, b)


def update_integrations(db: Session, b: Business, data: dict) -> dict:
    addon = _connect_addon(db, b)
    cfg = itg.config(addon)
    if "webhook_url" in data:
        url = str(data.get("webhook_url") or "").strip()
        if url and not itg.valid_webhook_url(url):
            raise HTTPException(status_code=422, detail="Adresse de webhook invalide : une URL https publique est attendue.")
        cfg["webhook"]["url"] = url
        if url and not cfg["webhook"].get("secret"):
            cfg["webhook"]["secret"] = uuid.uuid4().hex + uuid.uuid4().hex
        cfg["webhook"]["enabled"] = bool(url)
    g = cfg["google"]
    for key in ("sheets_enabled", "calendar_enabled"):
        if isinstance(data.get(key), bool):
            g[key] = data[key]
    if "slot_minutes" in data:
        try:
            minutes = int(data["slot_minutes"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="Durée de rendez-vous invalide.")
        if minutes not in (15, 20, 30, 45, 60, 90, 120):
            raise HTTPException(status_code=422, detail="Durée de rendez-vous : 15, 20, 30, 45, 60, 90 ou 120 minutes.")
        g["slot_minutes"] = minutes
    if isinstance(data.get("timezone"), str) and data["timezone"].strip():
        try:
            itg.ZoneInfo(data["timezone"].strip())
        except Exception:
            raise HTTPException(status_code=422, detail="Fuseau horaire inconnu (ex. Europe/Paris, America/Martinique).")
        g["timezone"] = data["timezone"].strip()
    cfg["google"] = g
    _save_integrations(db, addon, cfg)
    return receptionist_state(db, b)


def google_start(db: Session, b: Business) -> dict:
    _connect_addon(db, b)
    try:
        return {"url": itg.google_auth_url(b.id, google_redirect_uri())}
    except itg.IntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def google_disconnect(db: Session, b: Business) -> dict:
    addon = _addon(db, b.id)
    if addon is not None:
        cfg = itg.config(addon)
        itg.revoke(cfg)
        cfg["google"] = {k: v for k, v in cfg["google"].items()
                         if k in ("sheets_enabled", "calendar_enabled", "slot_minutes", "timezone")}
        _save_integrations(db, addon, cfg)
    return receptionist_state(db, b)


def webhook_test(db: Session, b: Business) -> dict:
    addon = _connect_addon(db, b)
    cfg = itg.config(addon)
    if not cfg["webhook"].get("url"):
        raise HTTPException(status_code=409, detail="Renseignez d'abord l'adresse du webhook.")
    sample = {"caller": {"nom": "Client test", "telephone": "+33600000000"}, "motif": "Test du webhook",
              "urgence": False, "adresse": "", "creneau": "", "precision": "", "rdv": "", "rdv_iso": "", "mode": "ai"}
    try:
        status = itg.send_webhook(cfg["webhook"]["url"], cfg["webhook"]["secret"], itg.webhook_payload(b, sample))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Webhook injoignable ({str(exc)[:120]}).")
    cfg["webhook"]["last_status"], cfg["webhook"]["last_at"] = status, _now().isoformat() + "Z"
    _save_integrations(db, addon, cfg)
    return {"status": status, "ok": 200 <= status < 300}


@router.get("/client/space/receptionist/integrations")
async def client_integrations(b: Business = Depends(client_business), db: Session = Depends(get_db)):
    return receptionist_state(db, b)["connect"]


@router.put("/client/space/receptionist/integrations")
async def client_integrations_update(request: Request, b: Business = Depends(client_business),
                                     db: Session = Depends(get_db)):
    return update_integrations(db, b, await _json(request))


@router.post("/client/space/receptionist/integrations/google/start")
async def client_google_start(b: Business = Depends(client_business), db: Session = Depends(get_db)):
    return google_start(db, b)


@router.post("/client/space/receptionist/integrations/google/disconnect")
async def client_google_disconnect(b: Business = Depends(client_business), db: Session = Depends(get_db)):
    return await run_in_threadpool(google_disconnect, db, b)


@router.post("/client/space/receptionist/integrations/webhook/test")
async def client_webhook_test(b: Business = Depends(client_business), db: Session = Depends(get_db)):
    return await run_in_threadpool(webhook_test, db, b)


def _finish_google(db: Session, code: str, state: str) -> str:
    """Échange le code Google, chiffre le jeton, crée le tableur. Renvoie le statut pour l'espace client."""
    business_id = itg.verify_state(state)
    b = db.query(Business).filter(Business.id == business_id).first()
    if not b:
        raise itg.IntegrationError("Commerce introuvable.")
    addon = _connect_addon(db, b)
    tokens = itg.exchange_code(code, google_redirect_uri())
    cfg = itg.config(addon)
    g = cfg["google"]
    g.update({"refresh_token_enc": itg.encrypt(tokens["refresh_token"]),
              "email": itg.userinfo_email(tokens["access_token"]),
              "connected_at": _now().isoformat() + "Z", "last_error": ""})
    g.setdefault("sheets_enabled", True)
    g.setdefault("calendar_enabled", True)
    missing = itg.missing_scopes(tokens)
    problems = []
    if missing["calendar"]:
        g["calendar_enabled"] = False
        problems.append("l'accès à l'agenda n'a pas été coché sur l'écran Google : déconnectez puis reconnectez "
                        "en cochant « voir vos disponibilités » et « créer des événements »")
    if missing["drive"]:
        g["sheets_enabled"] = False
        problems.append("l'accès au tableur n'a pas été coché")
    if problems:
        g["last_error"] = "Connexion incomplète : " + " ; ".join(problems) + "."
    if not g.get("sheet_id") and not missing["drive"]:
        try:
            name = rc.business_facts(b)["name"]
            g["sheet_id"], g["sheet_url"] = itg.create_sheet(tokens["access_token"], f"Appels – {name}")
        except Exception as exc:
            g["last_error"] = f"Tableur : {str(exc)[:160]}"
    cfg["google"] = g
    _save_integrations(db, addon, cfg)
    return "ok" if not g.get("last_error") else "partial"


@router.get("/integrations/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Retour de Google après autorisation (public : l'état signé identifie le commerce)."""
    params = request.query_params
    def target(status: str) -> str:
        return f"{frontend_url()}/espace/?google={status}#receptionniste"
    if params.get("error"):
        return RedirectResponse(target("refused"), status_code=303)
    try:
        status = await run_in_threadpool(_finish_google, db, params.get("code", ""), params.get("state", ""))
    except (itg.IntegrationError, HTTPException) as exc:
        detail = getattr(exc, "detail", None) or str(exc)
        print(f"[RECEPTIONNISTE] connexion Google refusée : {detail}")
        return RedirectResponse(target("error"), status_code=303)
    return RedirectResponse(target(status), status_code=303)


@router.get("/businesses/{business_id}/receptionist/integrations")
async def admin_integrations(business_id: str, db: Session = Depends(get_db)):
    return receptionist_state(db, _admin_business(db, business_id))["connect"]


@router.post("/businesses/{business_id}/receptionist/connect")
async def admin_connect_toggle(business_id: str, request: Request, db: Session = Depends(get_db)):
    """Active ou coupe le Pack Connecté payant d'un commerce : {"paid": true|false}."""
    b = _admin_business(db, business_id)
    addon = _ensure_addon(db, b)
    addon.connect_paid = bool((await _json(request)).get("paid"))
    db.commit()
    return receptionist_state(db, b)
