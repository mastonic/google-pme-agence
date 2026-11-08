"""
Alertes de supervision.

Envoi via le service email centralisé (backend/services/email_service.py, SMTP authentifié).
Destinataire par défaut : ALERT_EMAIL, sinon la boîte contact. Sans SMTP configuré, l'alerte est
seulement journalisée — toujours tolérant aux pannes pour ne jamais interrompre la supervision.
"""
import json
import os


def send_alert(subject: str, payload, to: str | None = None) -> bool:
    """`to` permet d'écrire à un destinataire précis (ex. gérant) ; par défaut ALERT_EMAIL."""
    from backend.services import email_service as es
    body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2)
    to = to or os.getenv("ALERT_EMAIL") or es.mailbox("contact")
    if not es.smtp_config()["host"]:
        print(f"[ALERT] {subject}\n{body}")
        return False
    ok = es.send_email(to, subject, body)
    if not ok:
        print(f"[ALERT] envoi échoué — {subject}")
    return ok
