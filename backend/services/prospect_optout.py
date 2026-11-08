"""Opposition à la prospection (CNIL, B2B) : chaque email de démo porte un lien de désinscription signé.

Le lien ne contient que l'identifiant du commerce et une signature HMAC : personne ne peut
désinscrire un autre commerce sans le lien reçu.
"""
import hashlib
import hmac
import os
import urllib.parse

LEGAL_SENDER = "HoldMasto (SASU, RCS Fort-de-France 106 121 536), éditeur de Pulse Locale PME"
PRIVACY_URL = "https://pulse-locale-pme.fr/mentions-legales/#rgpd"


def _secret() -> bytes:
    for name in ("OPTOUT_SECRET", "INTEGRATIONS_KEY", "ADMIN_API_TOKEN"):
        v = os.getenv(name, "").strip()
        if v:
            return v.encode()
    return b"pulse-locale-pme-optout"


def opt_out_signature(business_id: str) -> str:
    return hmac.new(_secret(), f"optout:{business_id}".encode(), hashlib.sha256).hexdigest()[:32]


def verify_opt_out(business_id: str, signature: str) -> bool:
    return bool(signature) and hmac.compare_digest(opt_out_signature(business_id), signature)


def opt_out_url(business_id: str) -> str:
    base = (os.getenv("PUBLIC_BASE_URL") or os.getenv("FRONTEND_URL") or "https://pulse-locale-pme.fr").rstrip("/")
    bid = urllib.parse.quote(str(business_id), safe="")
    return f"{base}/prospects/stop/{bid}?s={opt_out_signature(str(business_id))}"


def prospect_footer(business_id: str) -> str:
    """Mentions obligatoires d'un email de prospection : identité, source des données, opposition."""
    lines = [
        "—",
        "Vous recevez ce message car votre établissement est référencé publiquement sur Google Maps.",
        f"Expéditeur : {LEGAL_SENDER}.",
    ]
    if business_id:
        lines.append(f"Pour ne plus être contacté : {opt_out_url(business_id)} (ou répondez « STOP »).")
    else:
        lines.append("Pour ne plus être contacté, répondez « STOP ».")
    lines.append(f"Vos données et vos droits : {PRIVACY_URL}")
    return "\n".join(lines)
