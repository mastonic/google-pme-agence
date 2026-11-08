"""Service email centralisé de Pulse Locale PME.

Toutes les demandes des sites (.fr, .info, .store) et les commandes Stripe passent par ici :

1. `enqueue_*` enregistre l'email dans la file `email_outbox`, dans la même transaction que la
   demande : une panne SMTP ne fait jamais perdre une demande client.
2. `dispatch()` envoie les emails en attente (immédiatement après la demande, puis par la boucle
   de relance) avec nouvelle tentative et délai croissant (backoff).
3. `event_key` est unique : un double clic, un retry HTTP ou un webhook Stripe rejoué ne produit
   jamais deux emails.

Transport : SMTP authentifié (IONOS). Aucun identifiant n'est écrit dans le code : tout vient des
variables d'environnement (Secret Manager en production). Sans SMTP_HOST, rien n'est envoyé et les
emails restent en file (statut `pending`) jusqu'à la configuration.
"""
from __future__ import annotations

import datetime
import hashlib
import html
import logging
import os
import re
import smtplib
import socket
import ssl
import time
import uuid
from email.message import EmailMessage
from email.utils import formataddr, make_msgid, parseaddr

log = logging.getLogger("pulse.email")

BRAND = "Pulse Locale PME"
DOMAIN = "pulse-locale-pme.fr"
SITE_URL = "https://pulse-locale-pme.fr"

# ──────────────────────────────────────────────────────────────────────────────
# Configuration (variables d'environnement, jamais de secret dans le code)
# ──────────────────────────────────────────────────────────────────────────────

# Boîtes de destination : adresses publiques, surchargeables par variable d'environnement.
MAILBOX_DEFAULTS = {
    "contact": "contact@pulse-locale-pme.fr",
    "devis": "devis@pulse-locale-pme.fr",
    "commandes": "commandes@pulse-locale-pme.fr",
    "support": "support@pulse-locale-pme.fr",
    "audit": "audit@pulse-locale-pme.fr",
}


def mailbox(name: str) -> str:
    return (os.getenv(f"EMAIL_{name.upper()}") or MAILBOX_DEFAULTS[name]).strip()


# Type de demande → (boîte destinataire, libellé, modèle d'accusé de réception)
KINDS: dict[str, tuple[str, str, str]] = {
    "contact": ("contact", "Message de contact", "contact"),
    "product_info": ("contact", "Question sur un produit", "contact"),
    "guide": ("contact", "Téléchargement du guide gratuit", "contact"),
    "devis": ("devis", "Demande de devis", "devis"),
    "demo": ("devis", "Demande de démonstration", "devis"),
    "audit": ("audit", "Demande d'audit / test de visibilité", "audit"),
    "support": ("support", "Demande de support", "support"),
    "order_paid": ("commandes", "Commande payée", "order"),
}

SITE_LABELS = {"fr": "pulse-locale-pme.fr (site principal)", "info": "pulse-locale-pme.info (ressources)",
               "store": "pulse-locale-pme.store (boutique)", "autre": "Autre / inconnu"}

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-']{1,64}@[A-Za-z0-9.\-]{1,190}\.[A-Za-z]{2,24}$")
RETRY_DELAYS = (60, 300, 1800, 7200, 21600)   # 1 min, 5 min, 30 min, 2 h, 6 h puis abandon
MAX_ATTEMPTS = len(RETRY_DELAYS) + 1
SMTP_TIMEOUT = 20


class EmailConfigError(Exception):
    pass


class EmailSendError(Exception):
    def __init__(self, message: str, transient: bool):
        super().__init__(message)
        self.transient = transient


def valid_email(addr) -> str:
    """Adresse nettoyée si la syntaxe est sûre (aucun retour à la ligne, aucun nom affiché), sinon ''."""
    if not isinstance(addr, str):
        return ""
    addr = addr.strip()
    if any(c in addr for c in "\r\n\t<>,;\"\\ ") or not EMAIL_RE.match(addr) or ".." in addr:
        return ""
    return addr.lower()


def mask(addr: str) -> str:
    """Adresse masquée pour les journaux (pas de donnée personnelle complète dans les logs)."""
    if not addr or "@" not in addr:
        return "?"
    user, dom = addr.split("@", 1)
    return f"{user[:1]}***@{dom}"


def _clean_header(value: str, limit: int = 200) -> str:
    """Valeur d'en-tête sans retour à la ligne (anti-injection d'en-têtes)."""
    return re.sub(r"[\r\n\t]+", " ", str(value or "")).strip()[:limit]


def smtp_config() -> dict:
    """Configuration SMTP lue dans l'environnement. Les valeurs secrètes ne sont jamais renvoyées."""
    port = int(os.getenv("SMTP_PORT") or 587)
    secure = (os.getenv("SMTP_SECURE") or ("ssl" if port == 465 else "starttls")).strip().lower()
    return {
        "host": (os.getenv("SMTP_HOST") or "").strip(),
        "port": port,
        "secure": secure if secure in ("ssl", "starttls") else "starttls",
        "user": (os.getenv("SMTP_USER") or "").strip(),
        "password": os.getenv("SMTP_PASSWORD") or "",
        "from": (os.getenv("SMTP_FROM") or "").strip(),
        "allowed_from": [a.strip().lower() for a in (os.getenv("SMTP_ALLOWED_FROM") or "").split(",") if a.strip()],
    }


def config_status() -> dict:
    """État de la configuration, sans aucune valeur secrète (cockpit / diagnostic)."""
    c = smtp_config()
    return {
        "smtp_host": c["host"] or None, "smtp_port": c["port"], "smtp_secure": c["secure"],
        "smtp_user_set": bool(c["user"]), "smtp_password_set": bool(c["password"]),
        "sender": sender_address() if c["user"] else None,
        "ready": bool(c["host"] and c["user"] and c["password"]),
        "mailboxes": {k: mailbox(k) for k in MAILBOX_DEFAULTS},
    }


def sender_address() -> str:
    """Adresse d'expédition autorisée.

    IONOS n'accepte qu'un expéditeur authentifié du même domaine. On n'utilise SMTP_FROM que s'il
    s'agit du compte SMTP lui-même ou d'une adresse explicitement autorisée (SMTP_ALLOWED_FROM),
    sur le domaine pulse-locale-pme.fr. Sinon : repli sur le compte SMTP (journalisé).
    """
    c = smtp_config()
    user = valid_email(c["user"])
    wanted = valid_email(parseaddr(c["from"])[1]) if c["from"] else ""
    if wanted and wanted.endswith("@" + DOMAIN) and (wanted == user or wanted in c["allowed_from"]):
        return wanted
    if wanted and wanted != user:
        log.warning("email.sender_refused from=%s (non autorisé) -> repli sur le compte SMTP", mask(wanted))
    return user


# ──────────────────────────────────────────────────────────────────────────────
# Transport
# ──────────────────────────────────────────────────────────────────────────────

def build_message(to: str, subject: str, text: str, html_body: str | None = None,
                  reply_to: str | None = None, event_key: str | None = None) -> EmailMessage:
    sender = sender_address()
    to_addr = valid_email(to)
    if not sender:
        raise EmailConfigError("SMTP_USER absent ou invalide : aucun expéditeur authentifié")
    if not to_addr:
        raise EmailSendError("destinataire invalide", transient=False)
    msg = EmailMessage()
    msg["Subject"] = _clean_header(subject, 180)
    msg["From"] = formataddr((BRAND, sender))
    msg["To"] = to_addr
    rt = valid_email(reply_to) if reply_to else ""
    if rt:
        msg["Reply-To"] = rt
    msg["Message-ID"] = make_msgid(domain=DOMAIN)
    if event_key:
        msg["X-Pulse-Event"] = _clean_header(event_key, 120)
    msg.set_content(text, charset="utf-8")
    if html_body:
        msg.add_alternative(html_body, subtype="html", charset="utf-8")
    return msg


def _smtp_send(msg: EmailMessage) -> None:
    c = smtp_config()
    if not (c["host"] and c["user"] and c["password"]):
        raise EmailConfigError("SMTP non configuré (SMTP_HOST, SMTP_USER, SMTP_PASSWORD)")
    ctx = ssl.create_default_context()
    try:
        if c["secure"] == "ssl":
            server = smtplib.SMTP_SSL(c["host"], c["port"], timeout=SMTP_TIMEOUT, context=ctx)
        else:
            server = smtplib.SMTP(c["host"], c["port"], timeout=SMTP_TIMEOUT)
        with server:
            if c["secure"] == "starttls":
                server.starttls(context=ctx)
            server.login(c["user"], c["password"])
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise EmailSendError(f"authentification SMTP refusée ({exc.smtp_code})", transient=False)
    except smtplib.SMTPRecipientsRefused:
        raise EmailSendError("destinataire refusé par le serveur", transient=False)
    except smtplib.SMTPSenderRefused as exc:
        raise EmailSendError(f"expéditeur refusé ({exc.smtp_code})", transient=False)
    except smtplib.SMTPResponseException as exc:
        # 4xx : temporaire (dont « Mail send limit exceeded » IONOS) ; 5xx : définitif.
        raise EmailSendError(f"réponse SMTP {exc.smtp_code}", transient=400 <= exc.smtp_code < 500)
    except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, socket.timeout, OSError) as exc:
        raise EmailSendError(f"connexion SMTP impossible ({type(exc).__name__})", transient=True)


def send_email(to: str, subject: str, text: str, html_body: str | None = None,
               reply_to: str | None = None, event_key: str | None = None,
               retries: int = 2, backoff: float = 1.5) -> bool:
    """Envoi direct (synchrone) avec quelques tentatives rapprochées sur erreur temporaire.

    Renvoie True si envoyé, False sinon (jamais d'exception : l'appelant ne doit pas planter).
    Pour les demandes clients, préférer `enqueue_*` + `dispatch` (aucune perte en cas de panne).
    """
    try:
        msg = build_message(to, subject, text, html_body, reply_to, event_key)
    except (EmailConfigError, EmailSendError) as exc:
        log.warning("email.not_sent to=%s subject=%r reason=%s", mask(to), subject[:60], exc)
        return False
    for attempt in range(retries + 1):
        try:
            _smtp_send(msg)
            log.info("email.sent to=%s subject=%r event=%s", mask(to), subject[:60], event_key or "-")
            return True
        except EmailConfigError as exc:
            log.warning("email.not_configured to=%s reason=%s", mask(to), exc)
            return False
        except EmailSendError as exc:
            if not exc.transient or attempt == retries:
                log.error("email.failed to=%s attempt=%d reason=%s", mask(to), attempt + 1, exc)
                return False
            log.warning("email.retry to=%s attempt=%d reason=%s", mask(to), attempt + 1, exc)
            time.sleep(backoff * (2 ** attempt))
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Modèles (HTML responsive + texte brut)
# ──────────────────────────────────────────────────────────────────────────────

INK, TEAL, MUTED = "#1E293B", "#00A896", "#64748B"


def _html_layout(title: str, paragraphs: list[str], rows: list[tuple[str, str]] | None = None,
                 footer: str | None = None) -> str:
    e = html.escape
    paras = "".join(f'<p style="margin:0 0 14px;font-size:16px;line-height:1.6;color:{INK}">{e(p)}</p>' for p in paragraphs)
    table = ""
    if rows:
        table = ('<table role="presentation" style="width:100%;border-collapse:collapse;margin:8px 0 18px;font-size:15px">'
                 + "".join(f'<tr><td style="padding:8px 10px;border-bottom:1px solid #E2E8F0;color:{MUTED};width:38%;vertical-align:top">{e(k)}</td>'
                           f'<td style="padding:8px 10px;border-bottom:1px solid #E2E8F0;color:{INK};white-space:pre-wrap">{e(v)}</td></tr>'
                           for k, v in rows) + "</table>")
    foot = e(footer or f"{BRAND} · édité par HoldMasto · {SITE_URL.replace('https://', '')}")
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title></head><body style="margin:0;background:#F5F8FA;font-family:Inter,Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;padding:24px 16px">
 <div style="font:800 18px Montserrat,Arial,sans-serif;color:{INK}">PULSE <span style="color:{TEAL}">LOCALE</span> PME</div>
 <div style="background:#fff;border:1px solid #E2E8F0;border-radius:18px;padding:28px;margin-top:16px">
  <h1 style="font:800 21px Montserrat,Arial,sans-serif;color:{INK};margin:0 0 16px">{e(title)}</h1>
  {paras}{table}
 </div>
 <p style="font-size:12px;color:#94A3B8;text-align:center;margin:16px 0">{foot}</p>
</div></body></html>"""


def _hello(first_name: str) -> str:
    first = _clean_header(first_name, 60).split(" ")[0] if first_name else ""
    return f"Bonjour {first}," if first else "Bonjour,"


SIGNATURE = "L'équipe Pulse Locale PME"


def customer_template(template: str, first_name: str = "", ref: str = "", product: str = "",
                      amount: str = "", reply_to: str = "") -> tuple[str, list[str], list[tuple[str, str]]]:
    """(objet, paragraphes, lignes du tableau) des accusés de réception. Aucun délai contractuel."""
    hello = _hello(first_name)
    if template == "devis":
        return ("Votre demande de devis a bien été reçue",
                [hello, "Merci pour votre intérêt pour Pulse Locale PME.", "Votre demande de devis a été enregistrée.",
                 "Nous reviendrons vers vous pour échanger sur votre projet et vos besoins.", SIGNATURE], [])
    if template == "audit":
        return ("Votre demande d'audit de visibilité locale",
                [hello, "Votre demande d'audit a bien été reçue.",
                 "Nous allons examiner les informations transmises et vous contacter pour la suite.", SIGNATURE], [])
    if template == "support":
        return ("Votre demande de support a été enregistrée",
                [hello, "Nous avons bien reçu votre demande de support.",
                 "Notre équipe vous répondra dès que possible.", SIGNATURE], [("Référence", ref)])
    if template == "order":
        return ("Confirmation de votre commande Pulse Locale PME",
                [hello, "Votre paiement a été confirmé.",
                 "Vous recevrez les prochaines informations concernant votre prestation.", SIGNATURE],
                [("Référence", ref), ("Prestation", product), ("Montant", amount)])
    return ("Nous avons bien reçu votre message | Pulse Locale PME",
            [hello, "Nous avons bien reçu votre message.",
             "Notre équipe prendra connaissance de votre demande et reviendra vers vous dès que possible.",
             "À bientôt,", SIGNATURE + "\n" + (reply_to or mailbox("contact"))], [])


def render_customer(template: str, **kw) -> tuple[str, str, str]:
    subject, paras, rows = customer_template(template, **kw)
    rows = [(k, v) for k, v in rows if v]
    text = "\n\n".join(paras[:-1]) + ("\n\n" + "\n".join(f"{k} : {v}" for k, v in rows) if rows else "") + "\n\n" + paras[-1]
    text += ("\n\n—\nCet email confirme la réception de votre demande ; il ne vous inscrit à aucune liste. "
             f"Vos données : {SITE_URL}/mentions-legales/#rgpd")
    return subject, text, _html_layout(subject, paras, rows,
                                       footer=f"{BRAND} · HoldMasto · Email de confirmation, sans inscription à une liste.")


def render_internal(kind_label: str, fields: list[tuple[str, str]]) -> tuple[str, str]:
    rows = [(k, str(v)) for k, v in fields if v not in (None, "")]
    text = "\n".join(f"{k} : {v}" for k, v in rows) + "\n\n→ Cockpit, onglet « Leads »."
    return text, _html_layout(kind_label, ["Nouvelle demande reçue depuis les sites Pulse Locale PME."], rows,
                              footer="Notification interne — ne pas transférer (données personnelles).")


# ──────────────────────────────────────────────────────────────────────────────
# File d'envoi (outbox) : enregistrement, envoi, relances
# ──────────────────────────────────────────────────────────────────────────────

def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def new_event_id() -> str:
    return uuid.uuid4().hex


def enqueue(db, event_key: str, category: str, kind: str, to: str, subject: str, text: str,
            html_body: str | None = None, reply_to: str | None = None, lead_id: int | None = None,
            ref: str | None = None):
    """Ajoute un email à la file. Idempotent : un `event_key` déjà présent n'est jamais dupliqué."""
    from backend.models.database import EmailOutbox
    existing = db.query(EmailOutbox).filter(EmailOutbox.event_key == event_key).first()
    if existing:
        log.info("email.duplicate_ignored event=%s", event_key)
        return existing
    row = EmailOutbox(event_key=event_key, category=category, kind=kind, to_addr=to,
                      reply_to=reply_to or None, subject=_clean_header(subject, 180), body_text=text,
                      body_html=html_body, status="pending", attempts=0, next_attempt_at=_now(),
                      lead_id=lead_id, ref=ref)
    db.add(row)
    db.flush()
    log.info("email.queued id=%s event=%s category=%s kind=%s to=%s", row.id, event_key, category, kind, mask(to))
    return row


def _attempt(db, row) -> None:
    row.attempts = (row.attempts or 0) + 1
    try:
        msg = build_message(row.to_addr, row.subject, row.body_text, row.body_html, row.reply_to, row.event_key)
        _smtp_send(msg)
    except EmailConfigError as exc:
        # Pas de configuration : on n'épuise pas les tentatives, la demande attend la configuration.
        row.attempts -= 1
        row.status, row.last_error = "pending", str(exc)[:300]
        row.next_attempt_at = _now() + datetime.timedelta(minutes=15)
        log.warning("email.waiting_config id=%s event=%s", row.id, row.event_key)
        return
    except EmailSendError as exc:
        row.last_error = str(exc)[:300]
        if exc.transient and row.attempts < MAX_ATTEMPTS:
            delay = RETRY_DELAYS[min(row.attempts - 1, len(RETRY_DELAYS) - 1)]
            row.status, row.next_attempt_at = "failed", _now() + datetime.timedelta(seconds=delay)
            log.warning("email.retry_scheduled id=%s event=%s attempt=%d in=%ss reason=%s",
                        row.id, row.event_key, row.attempts, delay, exc)
        else:
            row.status = "dead"
            log.error("email.dead id=%s event=%s attempts=%d reason=%s", row.id, row.event_key, row.attempts, exc)
        return
    except Exception as exc:  # garde-fou : une erreur inattendue ne bloque pas la file
        row.status, row.last_error = "failed", f"{type(exc).__name__}"[:300]
        row.next_attempt_at = _now() + datetime.timedelta(seconds=RETRY_DELAYS[0])
        log.exception("email.unexpected id=%s event=%s", row.id, row.event_key)
        return
    row.status, row.sent_at, row.last_error = "sent", _now(), None
    log.info("email.sent id=%s event=%s category=%s to=%s", row.id, row.event_key, row.category, mask(row.to_addr))


def dispatch(db, ids: list[int] | None = None, limit: int = 25) -> dict:
    """Envoie les emails en attente (ou ceux de `ids`). Chaque email est « réservé » avant l'envoi :
    deux exécutions simultanées ne l'enverront jamais deux fois."""
    from backend.models.database import EmailOutbox
    q = db.query(EmailOutbox).filter(EmailOutbox.status.in_(("pending", "failed")),
                                     EmailOutbox.next_attempt_at <= _now())
    if ids:
        q = q.filter(EmailOutbox.id.in_(ids))
    stats = {"sent": 0, "failed": 0, "dead": 0, "pending": 0}
    for row in q.order_by(EmailOutbox.id).limit(limit).all():
        claimed = (db.query(EmailOutbox)
                   .filter(EmailOutbox.id == row.id, EmailOutbox.status.in_(("pending", "failed")))
                   .update({"status": "sending"}, synchronize_session=False))
        db.commit()
        if not claimed:
            continue
        db.refresh(row)
        _attempt(db, row)
        db.commit()
        stats[row.status if row.status in stats else "failed"] += 1
    return stats


def dispatch_in_new_session(ids: list[int] | None = None) -> dict:
    """Pour les tâches de fond (FastAPI BackgroundTasks, boucle de relance)."""
    from backend.models.database import SessionLocal
    db = SessionLocal()
    try:
        return dispatch(db, ids)
    except Exception:
        log.exception("email.dispatch_error")
        return {}
    finally:
        db.close()


def purge_outbox(db, days: int = 90) -> int:
    """Conservation limitée (RGPD) : les emails envoyés ou abandonnés de plus de `days` jours sont supprimés."""
    from backend.models.database import EmailOutbox
    cutoff = _now() - datetime.timedelta(days=days)
    n = (db.query(EmailOutbox).filter(EmailOutbox.status.in_(("sent", "dead")), EmailOutbox.created_at < cutoff)
         .delete(synchronize_session=False))
    db.commit()
    return n


# ──────────────────────────────────────────────────────────────────────────────
# API métier : notifications internes et accusés de réception
# ──────────────────────────────────────────────────────────────────────────────

def ticket_ref(lead_id: int, kind: str) -> str:
    prefix = {"support": "SUP", "devis": "DEV", "demo": "DEM", "audit": "AUD"}.get(kind, "REQ")
    return f"{prefix}-{int(lead_id):06d}"


def send_internal_notification(db, lead) -> object:
    """Notification interne vers la boîte du type de demande ; Reply-To = client (syntaxe validée)."""
    kind = lead.kind if lead.kind in KINDS else "contact"
    box, label, _ = KINDS[kind]
    when = (lead.created_at or _now()).strftime("%d/%m/%Y %H:%M UTC")
    name = lead.contact_name or lead.business_name or lead.email or lead.phone or "Inconnu"
    fields = [
        ("Type de demande", label), ("Date et heure", when), ("Site d'origine", SITE_LABELS.get(lead.site or "autre", lead.site)),
        ("Page", lead.referrer), ("Nom", lead.contact_name), ("Email", lead.email), ("Téléphone", lead.phone),
        ("Entreprise", lead.business_name), ("Ville", lead.city), ("Produit", lead.product), ("Message", lead.message),
        ("Score", lead.score), ("Rappel souhaité", lead.callback_slot), ("Référence", ticket_ref(lead.id, kind)),
        ("Identifiant CRM", f"lead #{lead.id}"), ("Statut", lead.status),
    ]
    text, html_body = render_internal(label, fields)
    subject = f"[{label}] {name}"
    return enqueue(db, f"lead:{lead.id}:internal", "internal", kind, mailbox(box), subject, text, html_body,
                   reply_to=valid_email(lead.email) or None, lead_id=lead.id)


def send_customer_confirmation(db, lead) -> object | None:
    """Accusé de réception au client (transactionnel, pas d'inscription marketing)."""
    to = valid_email(lead.email)
    if not to:
        return None
    kind = lead.kind if lead.kind in KINDS else "contact"
    box, _, template = KINDS[kind]
    subject, text, html_body = render_customer(
        template, first_name=lead.contact_name or "", ref=ticket_ref(lead.id, kind), reply_to=mailbox(box))
    return enqueue(db, f"lead:{lead.id}:ack", "customer", kind, to, subject, text, html_body,
                   reply_to=mailbox(box), lead_id=lead.id)


def send_audit_confirmation(db, lead):
    lead.kind = "audit"
    return send_customer_confirmation(db, lead)


def send_support_confirmation(db, lead):
    lead.kind = "support"
    return send_customer_confirmation(db, lead)


def send_order_confirmation(db, order: dict) -> list:
    """Commande payée (événement Stripe authentifié, paiement vérifié par l'appelant).

    `order` : {event_ref, email, name, product, amount_cents, currency, order_ref, business_id}.
    Envoie l'accusé client + la notification interne à commandes@. Idempotent sur `event_ref`.
    """
    rows = []
    amount = f"{order.get('amount_cents', 0) / 100:.2f} {str(order.get('currency') or 'eur').upper()}".replace(".", ",")
    ref = order.get("order_ref") or order["event_ref"]
    to = valid_email(order.get("email"))
    if to:
        subject, text, html_body = render_customer("order", first_name=order.get("name") or "", ref=ref,
                                                   product=order.get("product") or "", amount=amount)
        rows.append(enqueue(db, f"order:{order['event_ref']}:ack", "customer", "order_paid", to, subject, text,
                            html_body, reply_to=mailbox("commandes"), ref=order["event_ref"]))
    fields = [("Type de demande", "Commande payée (Stripe, paiement vérifié)"),
              ("Date et heure", _now().strftime("%d/%m/%Y %H:%M UTC")), ("Site d'origine", SITE_LABELS["store"]),
              ("Client", order.get("name")), ("Email", order.get("email")), ("Prestation", order.get("product")),
              ("Montant", amount), ("Référence", ref), ("Commerce (CRM)", order.get("business_id"))]
    text, html_body = render_internal("Commande payée", fields)
    rows.append(enqueue(db, f"order:{order['event_ref']}:internal", "internal", "order_paid", mailbox("commandes"),
                        f"[Commande payée] {order.get('product') or ''} · {amount}", text, html_body,
                        reply_to=to or None, ref=order["event_ref"]))
    return rows


def dedupe_key(email: str, kind: str, message: str) -> str:
    msg = re.sub(r"\s+", " ", (message or "").strip().lower())
    raw = f"{(email or '').lower()}|{kind}|{msg}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]
