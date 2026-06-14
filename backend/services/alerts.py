"""
Alertes de supervision.

Envoie un email via SMTP si les variables d'environnement sont configurées
(SMTP_HOST, ALERT_EMAIL...), sinon se contente de logguer — toujours tolérant
aux pannes pour ne jamais interrompre la supervision.
"""
import os
import json
import smtplib
from email.message import EmailMessage


def send_alert(subject: str, payload) -> bool:
    body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2)

    host = os.getenv("SMTP_HOST")
    to = os.getenv("ALERT_EMAIL")
    if not (host and to):
        print(f"[ALERT] {subject}\n{body}")
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "alerts@local-pulse"))
        msg["To"] = to
        msg.set_content(body)

        port = int(os.getenv("SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            if os.getenv("SMTP_USER"):
                server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            server.send_message(msg)
        print(f"[ALERT] email envoyé à {to} : {subject}")
        return True
    except Exception as e:
        print(f"[ALERT] envoi SMTP échoué ({e}) — {subject}\n{body}")
        return False
