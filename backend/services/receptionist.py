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
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from xml.sax.saxutils import escape, quoteattr

import requests

from backend.agents.manager import LocalPulseManager, display_business_name

MAX_TURNS = 8
VOICE = os.getenv("RECEPTIONIST_VOICE", "Polly.Lea")
LANG = "fr-FR"

# Voix proposées au gérant. "say" : voix Twilio <Say> (moteur gather) ; "relay" : voix
# ConversationRelay (moteur relay), surchargeables par variables d'environnement.
VOICES = {
    "femme": {"label": "Voix féminine", "say": os.getenv("RECEPTIONIST_VOICE", "Polly.Lea-Neural"),
              "relay": os.getenv("RECEPTIONIST_RELAY_VOICE_FEMME", "")},
    "homme": {"label": "Voix masculine", "say": os.getenv("RECEPTIONIST_VOICE_HOMME", "Polly.Remi-Neural"),
              "relay": os.getenv("RECEPTIONIST_RELAY_VOICE_HOMME", "")},
}
FORWARD_MODES = {
    # code de renvoi GSM (France) : **CODE*numéro#  — désactivation : ##CODE#
    "no_answer": {"label": "Si je ne décroche pas", "code": "61"},
    "busy": {"label": "Si je suis déjà en ligne", "code": "67"},
    "unreachable": {"label": "Si mon téléphone est éteint", "code": "62"},
    "always": {"label": "Tous les appels", "code": "21"},
}
DEFAULT_SETTINGS = {
    "agent_name": "",          # prénom de l'assistante (facultatif)
    "voice": "femme",
    "greeting": "",            # message d'accueil personnalisé ("" = message par défaut)
    "profession": "",          # "" = détection automatique
    "extra_info": "",          # infos réelles que l'IA peut donner (devis gratuit, zone…)
    "custom_question": "",     # question supplémentaire posée avant le nom
    "forward_modes": ["no_answer", "busy", "unreachable"],
}


def _clean(value, limit: int) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def normalize_settings(raw) -> dict:
    """Réglages du gérant, validés et complétés par les valeurs par défaut."""
    raw = raw if isinstance(raw, dict) else {}
    out = dict(DEFAULT_SETTINGS)
    out["agent_name"] = _clean(raw.get("agent_name"), 30)
    out["voice"] = raw.get("voice") if raw.get("voice") in VOICES else "femme"
    out["greeting"] = _clean(raw.get("greeting"), 400)
    out["profession"] = raw.get("profession") if raw.get("profession") in PROFESSIONS else ""
    out["extra_info"] = str(raw.get("extra_info") or "").strip()[:1500]
    out["custom_question"] = _clean(raw.get("custom_question"), 200)
    modes = raw.get("forward_modes")
    if isinstance(modes, list):
        modes = [m for m in dict.fromkeys(modes) if m in FORWARD_MODES]
        out["forward_modes"] = modes or list(DEFAULT_SETTINGS["forward_modes"])
    return out


def addon_settings(addon) -> dict:
    return normalize_settings(getattr(addon, "settings", None) if addon is not None else None)


def say_voice(settings: dict | None) -> str:
    return VOICES[normalize_settings(settings)["voice"]]["say"]


def forward_codes(number: str, settings: dict | None = None) -> list[dict]:
    """Codes à composer depuis le mobile du gérant pour renvoyer ses appels vers la réceptionniste."""
    if not number:
        return []
    modes = normalize_settings(settings)["forward_modes"]
    return [{"mode": m, "label": FORWARD_MODES[m]["label"],
             "activate": f"**{FORWARD_MODES[m]['code']}*{number}#",
             "deactivate": f"##{FORWARD_MODES[m]['code']}#"} for m in modes]

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


def effective_profession(business, settings: dict | None = None) -> str:
    chosen = normalize_settings(settings)["profession"] if settings else ""
    return chosen or detect_profession(business)


def questions_for(business, settings: dict | None = None) -> list[tuple[str, str]]:
    """Questions du métier, avec la question personnalisée du gérant insérée avant le nom."""
    questions = list(profession_config(effective_profession(business, settings))["questions"])
    custom = normalize_settings(settings)["custom_question"] if settings else ""
    if custom:
        at = next((i for i, (k, _) in enumerate(questions) if k == "nom"), len(questions))
        questions.insert(at, ("precision", custom))
    return questions


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


def default_greeting(business, settings: dict | None = None) -> str:
    facts = business_facts(business)
    name = normalize_settings(settings)["agent_name"]
    # Transparence (règlement européen sur l'IA) : l'appelant sait qu'il parle à une assistante virtuelle.
    who = f"Je suis {name}, l'assistante virtuelle" if name else "Je suis l'assistante virtuelle"
    return (f"Bonjour, vous êtes bien chez {facts['name']}. {who}, "
            "on ne peut pas vous répondre pour le moment. Je prends votre demande "
            "et on vous rappelle rapidement. Que puis-je faire pour vous ?")


def greeting(business, settings: dict | None = None) -> str:
    custom = normalize_settings(settings)["greeting"]
    return custom or default_greeting(business, settings)


def build_system_prompt(business, settings: dict | None = None) -> str:
    settings = normalize_settings(settings)
    facts = business_facts(business)
    prof = effective_profession(business, settings)
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
    if settings["extra_info"]:
        faq = (faq + "\n" if faq else "") + "Précisions données par le gérant :\n" + settings["extra_info"]

    questions = "\n".join(f"{i}. [{key}] {q}" for i, (key, q) in enumerate(questions_for(business, settings), 1))
    extra = "\n".join(f"- {r}" for r in cfg.get("extra_rules", []))
    persona = f" Tu t'appelles {settings['agent_name']}." if settings["agent_name"] else ""
    return f"""Tu es la réceptionniste téléphonique de « {facts['name']} » ({cfg['label']}).{persona}
Le gérant est occupé et n'a pas pu décrocher. Tu parles français, au téléphone : phrases courtes,
polies, chaleureuses, une seule question à la fois. Tu vouvoies toujours.

INFORMATIONS CONNUES (les seules que tu peux affirmer) :
{chr(10).join(known)}
{('FAQ et précisions du commerce :' + chr(10) + faq) if faq else ''}
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
{{"reply": "ce que tu dis à l'appelant", "fields": {{"motif": "", "urgence": false, "adresse": "", "creneau": "", "precision": "", "nom": "", "telephone": ""}}, "done": false}}
Dans "fields", ne mets que ce que l'appelant a réellement dit."""


# ──────────────────────────────────────────────────────────────────────────────
# Tour de conversation
# ──────────────────────────────────────────────────────────────────────────────

LLM_MAX_TOKENS = int(os.getenv("RECEPTIONIST_LLM_MAX_TOKENS", "1024"))
GEMINI_MODEL = os.getenv("RECEPTIONIST_GEMINI_MODEL", "").strip()
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Réflexion minimale : au téléphone, la latence prime. Le 1er réglage accepté par l'API est mémorisé.
_THINKING_CANDIDATES = [{"thinkingLevel": "minimal"}, {"thinkingLevel": "low"}, {"thinkingBudget": 0}, None]
_thinking_ok: list = []


def _gemini_model() -> str:
    if GEMINI_MODEL:
        return GEMINI_MODEL
    from backend.agents.manager import PROVIDERS_TEXT
    return next((p["model"] for p in PROVIDERS_TEXT if p["type"] == "gemini"), "")


def gemini_fast(system: str, prompt: str, timeout: float = 20) -> str:
    """Appel Gemini direct (REST) : réponse JSON imposée, réflexion minimale. Lève en cas d'échec."""
    key, model = os.getenv("GEMINI_API_KEY", "").strip(), _gemini_model()
    if not key or not model:
        raise RuntimeError("Gemini non configuré")
    candidates = _thinking_ok[:1] or _THINKING_CANDIDATES
    last = None
    for thinking in candidates:
        cfg = {"responseMimeType": "application/json", "maxOutputTokens": LLM_MAX_TOKENS, "temperature": 0.3}
        if thinking:
            cfg["thinkingConfig"] = thinking
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": cfg}
        r = requests.post(_GEMINI_URL.format(model=model), params={"key": key}, json=body, timeout=timeout)
        if r.status_code == 400 and thinking and "thinking" in r.text.lower():
            last = RuntimeError(f"Gemini 400 ({thinking})")
            continue  # réglage de réflexion non pris en charge par ce modèle : on essaie le suivant
        if r.status_code >= 300:
            raise RuntimeError(f"Gemini {r.status_code}: {r.text[:200]}")
        if not _thinking_ok:
            _thinking_ok.append(thinking)
        parts = (r.json().get("candidates") or [{}])[0].get("content", {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text.strip():
            raise RuntimeError("Gemini : réponse vide")
        return text
    raise last or RuntimeError("Gemini indisponible")


def llm_complete(business, system: str, prompt: str) -> str:
    """Gemini direct et rapide, puis la chaîne de providers existante en secours. Remplaçable en test."""
    try:
        return gemini_fast(system, prompt)
    except Exception as exc:
        print(f"[RECEPTIONNISTE] Gemini rapide indisponible ({str(exc)[:160]}) → chaîne de providers")
    manager = LocalPulseManager({"business_id": getattr(business, "id", None),
                                 "name": getattr(business, "name", ""), "types": _types(business)})
    return manager._call(prompt, max_tokens=LLM_MAX_TOKENS, system=system, temperature=0.3)


_REPLY_RE = re.compile(r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)"', re.S)


def _parse_llm_json(raw: str) -> dict | None:
    if not raw:
        return None
    data = None
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            data = json.loads(m.group(0))
        except ValueError:
            data = None
    if not isinstance(data, dict):
        # JSON tronqué (limite de tokens) : on récupère au moins la phrase à dire à l'appelant.
        r = _REPLY_RE.search(raw)
        if not r:
            return None
        try:
            reply = json.loads(f'"{r.group(1)}"')
        except ValueError:
            return None
        data = {"reply": reply, "fields": {}, "done": False}
    if not str(data.get("reply") or "").strip():
        return None
    data["fields"] = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    return data


def _fallback_turn(business, collected: dict, last_answer: str, settings: dict | None = None) -> dict:
    """Script déterministe si le LLM est indisponible : question suivante non répondue."""
    questions = questions_for(business, settings)
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


# Délai maximal accordé à l'IA. Twilio abandonne un webhook au bout de 15 s : au téléphone, on bascule
# sur le script de secours avant (9 s à l'oral pour laisser le temps à la synthèse vocale, 11 s à l'écrit).
VOICE_LLM_TIMEOUT = float(os.getenv("RECEPTIONIST_LLM_TIMEOUT", "9"))
TEXT_LLM_TIMEOUT = float(os.getenv("RECEPTIONIST_TEXT_LLM_TIMEOUT", "11"))
_LLM_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="receptionist-llm")


def _llm_with_timeout(business, system: str, prompt: str, timeout: float | None) -> str:
    if not timeout:
        return llm_complete(business, system, prompt)
    return _LLM_POOL.submit(llm_complete, business, system, prompt).result(timeout=timeout)


def next_turn(business, transcript: list[dict], collected: dict, speech: str, settings: dict | None = None,
              timeout: float | None = None) -> dict:
    """Renvoie {"reply", "fields", "done"}. Ne lève jamais d'exception.

    timeout : au-delà, le script de secours répond (l'appel ne reste jamais sans réponse)."""
    dialogue = "\n".join(f"{'Appelant' if t['role'] == 'caller' else 'Toi'} : {t['text']}" for t in transcript)
    prompt = (f"Conversation jusqu'ici :\n{dialogue}\n\nInformations déjà notées : "
              f"{json.dumps({k: v for k, v in collected.items() if not k.startswith('_')}, ensure_ascii=False)}\n\n"
              "Réponds à l'appelant (JSON uniquement).")
    started = time.monotonic()
    try:
        data = _parse_llm_json(_llm_with_timeout(business, build_system_prompt(business, settings), prompt, timeout))
        print(f"[RECEPTIONNISTE] LLM {time.monotonic() - started:.1f} s"
              + ("" if data else " → réponse illisible, script de secours"))
    except FuturesTimeout:
        print(f"[RECEPTIONNISTE] LLM trop lent (> {timeout:.0f} s) → script de secours")
        data = None
    except Exception as exc:
        print(f"[RECEPTIONNISTE] LLM indisponible ({exc}) → script de secours")
        data = None
    result = data or _fallback_turn(business, collected, speech, settings)
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
        "precision": collected.get("precision") or "",
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
    for label, key in (("Motif", "motif"), ("Adresse", "adresse"), ("Créneau", "creneau"), ("Précision", "precision")):
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

def _say(text: str, voice: str | None = None) -> str:
    return f"<Say language={quoteattr(LANG)} voice={quoteattr(voice or VOICE)}>{escape(text)}</Say>"


def twiml(*verbs: str) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?><Response>' + "".join(verbs) + "</Response>"


def twiml_gather(text: str, action: str, voice: str | None = None) -> str:
    return twiml(
        f'<Gather input="speech" language="{LANG}" speechTimeout="auto" timeout="6" '
        f'action={quoteattr(action)} method="POST">{_say(text, voice)}</Gather>',
        # Silence : on relance une fois via la même action (SpeechResult vide).
        f"<Redirect method=\"POST\">{escape(action)}</Redirect>",
    )


def twiml_hangup(text: str, voice: str | None = None) -> str:
    return twiml(_say(text, voice), "<Hangup/>")


def twiml_voicemail(business, action: str, voice: str | None = None) -> str:
    name = business_facts(business)["name"]
    return twiml(
        _say(f"Bonjour, vous êtes bien chez {name}. Nous ne pouvons pas vous répondre pour le moment. "
             "Laissez votre nom, votre numéro et l'objet de votre appel après le bip, on vous rappelle rapidement.", voice),
        f'<Record maxLength="120" playBeep="true" timeout="5" action={quoteattr(action)} method="POST"/>',
        _say("Nous n'avons pas reçu de message. Au revoir.", voice),
        "<Hangup/>",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Moteur « relay » : Twilio ConversationRelay (voix temps réel, interruptions)
# ──────────────────────────────────────────────────────────────────────────────
# gather (défaut) : <Gather speech> + <Say>, un aller-retour HTTP par phrase (simple, robuste,
#                   ~2-4 s de latence, pas d'interruption possible).
# relay           : <Connect><ConversationRelay> ; Twilio gère reconnaissance vocale et synthèse
#                   (voix neuronales), notre WebSocket ne reçoit que du texte. Latence < 1 s,
#                   l'appelant peut couper la parole. Même LLM, même prompt, mêmes résumés.

def engine() -> str:
    return "relay" if os.getenv("RECEPTIONIST_ENGINE", "gather").strip().lower() == "relay" else "gather"


def twiml_relay(ws_url: str, welcome: str, settings: dict | None = None, action: str = "") -> str:
    voice = VOICES[normalize_settings(settings)["voice"]]["relay"]
    attrs = {
        "url": ws_url,
        "welcomeGreeting": welcome,
        "language": LANG,
        "interruptible": "true",
        "ttsProvider": os.getenv("RECEPTIONIST_RELAY_TTS_PROVIDER", "").strip(),
        "voice": voice,
        "transcriptionProvider": os.getenv("RECEPTIONIST_RELAY_STT_PROVIDER", "").strip(),
    }
    attr = " ".join(f"{k}={quoteattr(v)}" for k, v in attrs.items() if v)
    act = f" action={quoteattr(action)} method=\"POST\"" if action else ""
    return twiml(f"<Connect{act}><ConversationRelay {attr}/></Connect>")


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
