"""Réceptionniste IA : répond aux appels que le gérant ne peut pas prendre.

Principe : le gérant active le renvoi d'appel « sur non-réponse » de sa ligne vers un
numéro Twilio. Twilio appelle nos webhooks (voir backend/receptionist_api.py) :

1. appel entrant  → message d'accueil + <Gather input="speech" language="fr-FR">
2. chaque réponse → le LLM (même chaîne de providers que le reste de l'app) formule la
   question suivante et extrait les champs utiles (motif, adresse, créneau…)
3. fin d'appel    → résumé structuré JSON envoyé au gérant par SMS (Twilio) et email.

Règle d'or : le prompt est construit UNIQUEMENT à partir des données réelles du commerce.
Aucun prix, aucune disponibilité n'est inventé : à défaut, on prend un message et on
promet un rappel.

Tous les appels externes (LLM, SMS, email) sont isolés dans des fonctions facilement
remplaçables en test et ne lèvent jamais d'exception vers Twilio.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import unicodedata
from xml.sax.saxutils import escape, quoteattr

import requests

from backend.agents.manager import LocalPulseManager, display_business_name

MAX_TURNS = 8
VOICE = os.getenv("RECEPTIONIST_VOICE", "Polly.Lea")
LANG = "fr-FR"

# ──────────────────────────────────────────────────────────────────────────────
# Configuration par métier
# ──────────────────────────────────────────────────────────────────────────────
# Chaque question correspond à un champ du résumé. L'ordre est celui de la conversation.
Q_URGENCE = ("urgence", "Est-ce une urgence ?")
Q_NOM = ("nom", "Puis-je avoir votre nom ?")
Q_TEL = ("telephone", "À quel numéro le rappeler, si ce n'est pas celui-ci ?")

PROFESSIONS = {
    "plombier": {
        "label": "plombier", "metier": "plomberie",
        "questions": [Q_URGENCE, ("motif", "Quel est le problème : fuite, canalisation bouchée, chauffe-eau… ?"),
                      ("adresse", "À quelle adresse se trouve l'intervention ?"),
                      ("creneau", "Quand souhaitez-vous l'intervention ?"), Q_NOM, Q_TEL],
    },
    "electricien": {
        "label": "électricien", "metier": "électricité",
        "questions": [Q_URGENCE, ("motif", "Quel est le problème : panne, coupure, installation, mise aux normes… ?"),
                      ("adresse", "À quelle adresse se trouve l'intervention ?"),
                      ("creneau", "Quand souhaitez-vous l'intervention ?"), Q_NOM, Q_TEL],
    },
    "serrurier": {
        "label": "serrurier", "metier": "serrurerie",
        "questions": [Q_URGENCE, ("motif", "Êtes-vous bloqué dehors, ou s'agit-il d'un changement de serrure ?"),
                      ("adresse", "À quelle adresse ?"), ("creneau", "Pour quand ?"), Q_NOM, Q_TEL],
    },
    "chauffagiste": {
        "label": "chauffagiste", "metier": "chauffage et climatisation",
        "questions": [Q_URGENCE, ("motif", "Quel appareil est concerné et que se passe-t-il ?"),
                      ("adresse", "À quelle adresse ?"), ("creneau", "Quand souhaitez-vous le passage ?"), Q_NOM, Q_TEL],
    },
    "artisan": {
        "label": "artisan", "metier": "travaux",
        "questions": [Q_URGENCE, ("motif", "Quel type d'intervention ou de travaux souhaitez-vous ?"),
                      ("adresse", "À quelle adresse ?"), ("creneau", "Quand souhaitez-vous l'intervention ?"), Q_NOM, Q_TEL],
    },
    "coiffeur": {
        "label": "salon", "metier": "coiffure et beauté",
        "questions": [("motif", "Quelle prestation souhaitez-vous ?"),
                      ("creneau", "Quel jour et quelle heure vous arrangeraient ?"), Q_NOM, Q_TEL],
    },
    "restaurant": {
        "label": "restaurant", "metier": "restauration",
        "questions": [("motif", "Souhaitez-vous réserver une table, commander, ou autre chose ?"),
                      ("creneau", "Pour quel jour, quelle heure et combien de personnes ?"), Q_NOM, Q_TEL],
    },
    "taxi": {
        "label": "taxi", "metier": "transport de personnes",
        "questions": [("adresse", "Quelle est l'adresse de prise en charge ?"),
                      ("motif", "Quelle est votre destination ?"),
                      ("creneau", "Pour quel jour et quelle heure ?"), Q_NOM, Q_TEL],
    },
    "garage": {
        "label": "garage", "metier": "réparation automobile",
        "questions": [Q_URGENCE, ("motif", "Quel est le véhicule et quel est le problème ?"),
                      ("creneau", "Quand souhaitez-vous déposer le véhicule ?"), Q_NOM, Q_TEL],
    },
    "medical": {
        "label": "cabinet", "metier": "santé",
        # Jamais de conseil médical : orientation 15/112 en cas d'urgence vitale.
        "questions": [("motif", "Quel est le motif de votre appel ? Pour une urgence vitale, composez le 15."),
                      ("creneau", "Quelles disponibilités pour un rendez-vous ?"), Q_NOM, Q_TEL],
        "extra_rules": ["Ne donne JAMAIS de conseil médical. Urgence vitale : dis d'appeler le 15 ou le 112."],
    },
    "hebergement": {
        "label": "établissement", "metier": "hébergement",
        "questions": [("motif", "Souhaitez-vous réserver ou avez-vous une question sur un séjour ?"),
                      ("creneau", "Pour quelles dates et combien de personnes ?"), Q_NOM, Q_TEL],
    },
    "commerce": {
        "label": "commerce", "metier": "commerce",
        "questions": [("motif", "Que puis-je noter pour vous ?"), Q_NOM, Q_TEL],
    },
    "generic": {
        "label": "entreprise", "metier": "",
        "questions": [("motif", "Quel est l'objet de votre appel ?"),
                      ("creneau", "Quand êtes-vous joignable ou disponible ?"), Q_NOM, Q_TEL],
    },
}

# Types Google → métier fin (avant le secteur générique de LocalPulseManager).
GOOGLE_TYPE_PROFESSION = {
    "plumber": "plombier", "electrician": "electricien", "locksmith": "serrurier",
    "hvac_contractor": "chauffagiste", "roofing_contractor": "artisan", "painter": "artisan",
    "general_contractor": "artisan", "moving_company": "artisan",
    "hair_care": "coiffeur", "hair_salon": "coiffeur", "beauty_salon": "coiffeur",
    "barber_shop": "coiffeur", "nail_salon": "coiffeur", "spa": "coiffeur",
    "taxi_stand": "taxi", "car_repair": "garage",
}
NAME_KEYWORDS = [
    ("plomb", "plombier"), ("electri", "electricien"), ("serrur", "serrurier"),
    ("chauffag", "chauffagiste"), ("climatis", "chauffagiste"), ("coiff", "coiffeur"),
    ("barber", "coiffeur"), ("taxi", "taxi"), ("vtc", "taxi"), ("garage", "garage"),
    ("carross", "garage"), ("pizz", "restaurant"), ("restaurant", "restaurant"),
]
SECTOR_PROFESSION = {
    "artisan": "artisan", "beauty": "coiffeur", "restaurant": "restaurant", "cafe": "restaurant",
    "transport": "taxi", "automotive": "garage", "medical": "medical", "lodging": "hebergement",
    "retail": "commerce",
}

URGENT_KEYWORDS = (
    "urgence", "urgent", "panne", "fuite", "coupure", "inondation", "inonde", "degat des eaux",
    "plus de courant", "plus d'electricite", "plus d'eau", "plus de chauffage", "court-circuit",
    "odeur de gaz", "gaz", "fumee", "etincelle", "bloque dehors", "enferme", "porte claquee",
    "en panne", "accident", "tout de suite", "immediatement", "au plus vite",
)


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c)).replace("’", "'")


NEGATED_URGENCY = re.compile(r"(pas|rien) (d'|de |une |un |du |tres |si )?(urgen\w*|presse\w*)|sans urgence|aucune urgence")


def detect_urgency(text: str) -> bool:
    t = NEGATED_URGENCY.sub(" ", _norm(text))
    return any(re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", t) for k in URGENT_KEYWORDS)


def _types(business) -> list[str]:
    cat = getattr(business, "category", None)
    if isinstance(cat, str):
        try:
            cat = json.loads(cat)
        except ValueError:
            cat = [cat]
    return [str(t) for t in (cat or []) if t] if isinstance(cat, list) else []


def detect_sector(business) -> str:
    """Secteur via la détection existante du générateur de sites (SECTOR_TYPE_MAP)."""
    return LocalPulseManager._detect_sector(None, _types(business))


def detect_profession(business) -> str:
    for t in _types(business):
        if t in GOOGLE_TYPE_PROFESSION:
            return GOOGLE_TYPE_PROFESSION[t]
    name = _norm(getattr(business, "name", ""))
    for kw, prof in NAME_KEYWORDS:
        if kw in name:
            return prof
    return SECTOR_PROFESSION.get(detect_sector(business), "generic")


def profession_config(profession: str) -> dict:
    return PROFESSIONS.get(profession) or PROFESSIONS["generic"]


# ──────────────────────────────────────────────────────────────────────────────
# Données réelles du commerce
# ──────────────────────────────────────────────────────────────────────────────

def business_facts(business) -> dict:
    """Uniquement ce qui est réellement stocké. Rien n'est complété par défaut."""
    profile = business.client_profile if isinstance(getattr(business, "client_profile", None), dict) else {}
    identity, contact = profile.get("identity") or {}, profile.get("contact") or {}
    activity = profile.get("activity") or {}

    hours = []
    raw_hours = activity.get("hours")
    if isinstance(raw_hours, list):
        for h in raw_hours:
            if not isinstance(h, dict) or not h.get("day"):
                continue
            if h.get("closed"):
                hours.append(f"{h['day']} : fermé")
            elif h.get("open") and h.get("close"):
                hours.append(f"{h['day']} : {h['open']}–{h['close']}")

    pricing = profile.get("pricing") or activity.get("pricing") or activity.get("prices") or []
    if isinstance(pricing, dict):
        pricing = [f"{k} : {v}" for k, v in pricing.items() if str(v).strip()]
    elif isinstance(pricing, list):
        pricing = [
            (f"{p.get('label') or p.get('name')} : {p.get('price')}" if isinstance(p, dict) else str(p))
            for p in pricing if (p.get("price") if isinstance(p, dict) else str(p).strip())
        ]
    else:
        pricing = []

    return {
        "name": display_business_name(identity.get("business_name") or business.name or "") or "l'entreprise",
        "address": contact.get("address") or business.address or "",
        "description": activity.get("description") or "",
        "services": [str(s) for s in (activity.get("services") or []) if str(s).strip()],
        "service_areas": [str(s) for s in (activity.get("service_areas") or []) if str(s).strip()],
        "hours": hours,
        "pricing": pricing,
        "faq": [f for f in (profile.get("faq") or []) if isinstance(f, dict) and f.get("q") and f.get("a")],
    }


def greeting(business) -> str:
    facts = business_facts(business)
    return (f"Bonjour, vous êtes bien chez {facts['name']}. Je suis l'assistante, "
            "on ne peut pas vous répondre pour le moment. Je prends votre demande "
            "et on vous rappelle rapidement. Que puis-je faire pour vous ?")


def build_system_prompt(business) -> str:
    facts = business_facts(business)
    prof = detect_profession(business)
    cfg = profession_config(prof)
    known, unknown = [], []

    def add(label, value):
        (known if value else unknown).append(f"- {label} : {value}" if value else f"- {label}")

    add("Nom", facts["name"])
    add("Activité", cfg["metier"] + (f" — {facts['description']}" if facts["description"] else ""))
    add("Adresse", facts["address"])
    add("Zones d'intervention", ", ".join(facts["service_areas"]))
    add("Prestations", ", ".join(facts["services"]))
    add("Horaires", " ; ".join(facts["hours"]))
    add("Tarifs", " ; ".join(facts["pricing"]))
    faq = "\n".join(f"- Q : {f['q']} → R : {f['a']}" for f in facts["faq"][:10])

    questions = "\n".join(f"{i}. [{key}] {q}" for i, (key, q) in enumerate(cfg["questions"], 1))
    extra = "\n".join(f"- {r}" for r in cfg.get("extra_rules", []))
    return f"""Tu es la réceptionniste téléphonique de « {facts['name']} » ({cfg['label']}).
Le gérant est occupé et n'a pas pu décrocher. Tu parles français, au téléphone : phrases courtes,
polies, chaleureuses, une seule question à la fois. Tu vouvoies toujours.

INFORMATIONS CONNUES (les seules que tu peux affirmer) :
{chr(10).join(known)}
{('FAQ du commerce :' + chr(10) + faq) if faq else ''}
INFORMATIONS INCONNUES (ne jamais les inventer) :
{chr(10).join(unknown) if unknown else '- aucune'}
- Disponibilités et planning du gérant (toujours inconnus)

RÈGLES STRICTES :
- N'invente JAMAIS de prix, de devis, de délai, de disponibilité ni de rendez-vous confirmé.
- Si on te demande une information inconnue : dis que le gérant rappellera pour la préciser.
- Tu ne confirmes jamais un créneau : tu notes le souhait, le gérant rappellera pour confirmer.
- Si la situation est urgente (panne, fuite, coupure, danger…), note-le et rassure : le gérant
  est prévenu immédiatement par SMS. En cas de danger (gaz, incendie), conseille le 18 ou le 112.
{extra}
QUESTIONS À POSER, dans l'ordre, en sautant celles déjà répondues :
{questions}

Quand toutes les informations utiles sont recueillies (ou si l'appelant veut raccrocher),
remercie, récapitule en une phrase et annonce un rappel rapide, puis termine (done=true).

FORMAT DE RÉPONSE : uniquement un objet JSON, sans markdown :
{{"reply": "ce que tu dis à l'appelant", "fields": {{"motif": "", "urgence": false, "adresse": "", "creneau": "", "nom": "", "telephone": ""}}, "done": false}}
Dans "fields", ne mets que ce que l'appelant a réellement dit."""


# ──────────────────────────────────────────────────────────────────────────────
# Tour de conversation
# ──────────────────────────────────────────────────────────────────────────────

def llm_complete(business, system: str, prompt: str) -> str:
    """Appel LLM via la chaîne de providers existante (Gemini → …). Remplaçable en test."""
    manager = LocalPulseManager({"business_id": getattr(business, "id", None),
                                 "name": getattr(business, "name", ""), "types": _types(business)})
    return manager._call(prompt, max_tokens=400, system=system, temperature=0.3)


def _parse_llm_json(raw: str) -> dict | None:
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None
    if not isinstance(data, dict) or not str(data.get("reply") or "").strip():
        return None
    data["fields"] = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    return data


def _fallback_turn(business, collected: dict, last_answer: str) -> dict:
    """Script déterministe si le LLM est indisponible : question suivante non répondue."""
    cfg = profession_config(detect_profession(business))
    questions = cfg["questions"]
    pending = collected.get("_pending")
    fields = {}
    if pending and last_answer:
        fields[pending] = detect_urgency(last_answer) if pending == "urgence" else last_answer
    elif last_answer and not collected.get("motif"):
        fields["motif"] = last_answer
    merged = {**collected, **fields}
    for key, q in questions:
        if key not in merged or merged[key] in ("", None):
            return {"reply": q, "fields": {**fields, "_pending": key}, "done": False}
    return {"reply": "Merci, c'est bien noté. Vous serez rappelé très rapidement. Au revoir !",
            "fields": {**fields, "_pending": None}, "done": True}


def next_turn(business, transcript: list[dict], collected: dict, speech: str) -> dict:
    """Renvoie {"reply", "fields", "done"}. Ne lève jamais d'exception."""
    dialogue = "\n".join(f"{'Appelant' if t['role'] == 'caller' else 'Toi'} : {t['text']}" for t in transcript)
    prompt = (f"Conversation jusqu'ici :\n{dialogue}\n\nInformations déjà notées : "
              f"{json.dumps({k: v for k, v in collected.items() if not k.startswith('_')}, ensure_ascii=False)}\n\n"
              "Réponds à l'appelant (JSON uniquement).")
    try:
        data = _parse_llm_json(llm_complete(business, build_system_prompt(business), prompt))
    except Exception as exc:
        print(f"[RECEPTIONNISTE] LLM indisponible ({exc}) → script de secours")
        data = None
    result = data or _fallback_turn(business, collected, speech)
    if detect_urgency(speech):
        result["fields"]["urgence"] = True
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Résumé & notification du gérant
# ──────────────────────────────────────────────────────────────────────────────

def build_summary(business, call) -> dict:
    collected = {k: v for k, v in (call.collected or {}).items() if not k.startswith("_")}
    caller_text = " ".join(t["text"] for t in (call.transcript or []) if t.get("role") == "caller")
    urgent = bool(collected.get("urgence") is True or detect_urgency(caller_text))
    motif = collected.get("motif") or (caller_text[:200] if caller_text else "")
    if call.mode == "voicemail":
        motif = motif or "Message vocal laissé (voir enregistrement)"
    if call.mode == "whatsapp_message":
        motif = caller_text[:500]
    return {
        "caller": {"nom": collected.get("nom") or "", "telephone": collected.get("telephone") or call.from_number or ""},
        "motif": motif,
        "urgence": urgent,
        "adresse": collected.get("adresse") or "",
        "creneau": collected.get("creneau") or "",
        "rappel": True,
        "mode": call.mode,
        "profession": detect_profession(business),
        "enregistrement": call.recording_url or "",
    }


def format_sms(business, summary: dict) -> str:
    head = "🚨 URGENT – " if summary["urgence"] else ""
    source = "Message WhatsApp" if str(summary.get("mode", "")).startswith("whatsapp") else "Appel manqué"
    c = summary["caller"]
    lines = [f"{head}{source} récupéré ({business_facts(business)['name']})",
             f"De : {c['nom'] or 'inconnu'} {c['telephone']}".strip()]
    for label, key in (("Motif", "motif"), ("Adresse", "adresse"), ("Créneau", "creneau")):
        if summary.get(key):
            lines.append(f"{label} : {summary[key]}")
    if summary.get("enregistrement"):
        lines.append(f"Message : {summary['enregistrement']}")
    lines.append("→ À rappeler")
    return "\n".join(lines)[:1500]


def to_e164(phone: str) -> str:
    digits = re.sub(r"[^\d+]", "", phone or "")
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if digits.startswith("0") and len(digits) == 10:
        digits = "+33" + digits[1:]
    return digits if re.fullmatch(r"\+\d{8,15}", digits) else ""


NOTIFY_CHANNELS = ("whatsapp", "sms", "email")
DEFAULT_CHANNELS = ["whatsapp", "sms"]


def notify_channels(addon) -> list[str]:
    raw = getattr(addon, "notify_channels", None) if addon is not None else None
    chans = [c for c in (raw or []) if c in NOTIFY_CHANNELS] if isinstance(raw, list) else []
    return chans or list(DEFAULT_CHANNELS)


def _twilio_message(sender: str, to: str, body: str, label: str) -> bool:
    """POST sur l'API Messages de Twilio. False (sans exception) si non configuré ou en échec."""
    sid, token = (os.getenv(k, "").strip() for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"))
    if not (sid and token and sender and to):
        print(f"[RECEPTIONNISTE] {label} non envoyé (Twilio non configuré ou numéro invalide)\n{body}")
        return False
    try:
        r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                          data={"From": sender, "To": to, "Body": body}, auth=(sid, token), timeout=10)
        if r.status_code >= 300:
            print(f"[RECEPTIONNISTE] {label} refusé par Twilio ({r.status_code})")
            return False
        return True
    except Exception as exc:
        print(f"[RECEPTIONNISTE] {label} échoué ({exc})")
        return False


def send_sms(to: str, body: str) -> bool:
    to = to_e164(to)
    return _twilio_message(os.getenv("TWILIO_PHONE_NUMBER", "").strip(), to, body, "SMS")


def send_whatsapp(to: str, body: str) -> bool:
    """WhatsApp via Twilio : from whatsapp:+TWILIO_WHATSAPP_NUMBER. Hors fenêtre de 24 h, Meta
    exige un modèle (template) approuvé : configurer l'expéditeur Twilio en conséquence."""
    number = to_e164(os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip().removeprefix("whatsapp:"))
    to = to_e164(to)
    return _twilio_message(f"whatsapp:{number}" if number else "", f"whatsapp:{to}" if to else "", body, "WhatsApp")


def notify_owner(business, addon, summary: dict) -> dict:
    """Prévient le gérant sur les canaux choisis (whatsapp / sms / email). Ne lève jamais."""
    from backend.services.alerts import send_alert
    body = format_sms(business, summary)
    phone = (getattr(addon, "notify_phone", None) or business.owner_phone or "")
    email = (getattr(addon, "notify_email", None) or business.owner_email or "")
    channels = notify_channels(addon)
    sent = {c: False for c in channels}
    for channel in channels:
        try:
            if channel == "whatsapp" and phone:
                sent[channel] = send_whatsapp(phone, body)
            elif channel == "sms" and phone:
                sent[channel] = send_sms(phone, body)
            elif channel == "email" and email:
                subject = ("[URGENT] " if summary["urgence"] else "") + "Appel manqué récupéré par votre réceptionniste"
                sent[channel] = send_alert(subject, body + "\n\n" + json.dumps(summary, ensure_ascii=False, indent=2), to=email)
        except Exception as exc:
            print(f"[RECEPTIONNISTE] notification {channel} échouée ({exc})")
    return sent


def twiml_message(text: str) -> str:
    return twiml(f"<Message>{escape(text)}</Message>")


# ──────────────────────────────────────────────────────────────────────────────
# TwiML & signature Twilio
# ──────────────────────────────────────────────────────────────────────────────

def _say(text: str) -> str:
    return f"<Say language={quoteattr(LANG)} voice={quoteattr(VOICE)}>{escape(text)}</Say>"


def twiml(*verbs: str) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?><Response>' + "".join(verbs) + "</Response>"


def twiml_gather(text: str, action: str) -> str:
    return twiml(
        f'<Gather input="speech" language="{LANG}" speechTimeout="auto" timeout="6" '
        f'action={quoteattr(action)} method="POST">{_say(text)}</Gather>',
        # Silence : on relance une fois via la même action (SpeechResult vide).
        f"<Redirect method=\"POST\">{escape(action)}</Redirect>",
    )


def twiml_hangup(text: str) -> str:
    return twiml(_say(text), "<Hangup/>")


def twiml_voicemail(business, action: str) -> str:
    name = business_facts(business)["name"]
    return twiml(
        _say(f"Bonjour, vous êtes bien chez {name}. Nous ne pouvons pas vous répondre pour le moment. "
             "Laissez votre nom, votre numéro et l'objet de votre appel après le bip, on vous rappelle rapidement."),
        f'<Record maxLength="120" playBeep="true" timeout="5" action={quoteattr(action)} method="POST"/>',
        _say("Nous n'avons pas reçu de message. Au revoir."),
        "<Hangup/>",
    )


def compute_signature(auth_token: str, url: str, params: dict) -> str:
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def valid_signature(url: str, params: dict, signature: str, auth_token: str | None = None) -> bool:
    """Valide X-Twilio-Signature. Fail closed si TWILIO_AUTH_TOKEN est absent."""
    token = (auth_token if auth_token is not None else os.getenv("TWILIO_AUTH_TOKEN", "")).strip()
    if not token or not signature:
        return False
    return hmac.compare_digest(compute_signature(token, url, params), signature)
