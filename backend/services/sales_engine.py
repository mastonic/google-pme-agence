"""Moteur commercial interne de Local Pulse.

Run 2:
- transforme l'audit en démonstration commerciale avant/après;
- prépare une séquence de prospection humaine (aucun envoi automatique);
- calcule la prochaine action CRM et son échéance.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List


def _name(data: Dict[str, Any]) -> str:
    return (data.get("name") or "ce commerce").strip()


def _first_name(data: Dict[str, Any]) -> str:
    return (data.get("owner_first_name") or "").strip()


def _greeting(data: Dict[str, Any]) -> str:
    first = _first_name(data)
    return f"Bonjour {first}," if first else "Bonjour,"


def _audit_issues(data: Dict[str, Any]) -> list[dict]:
    audit = data.get("website_audit") or {}
    issues = audit.get("issues") or []
    return [x for x in issues if isinstance(x, dict)]


def build_sales_snapshot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Construit le support de vente à partir de faits observés, sans promettre de ROI."""
    name = _name(data)
    rating = float(data.get("rating") or 0)
    reviews = int(data.get("user_ratings_total") or 0)
    digital = round(float(data.get("digital_health_score") or 0))
    opportunity = round(float(data.get("opportunity_score") or 0))
    website = data.get("website")
    audit = data.get("website_audit") or {}
    audit_score = audit.get("score")

    current = []
    if rating > 0:
        current.append({
            "label": "Réputation Google",
            "value": f"{rating:.1f}/5 · {reviews} avis",
            "status": "strong" if rating >= 4.2 and reviews >= 15 else "medium",
        })
    else:
        current.append({"label": "Réputation Google", "value": "Peu de preuve sociale détectée", "status": "weak"})

    current.append({
        "label": "Présence digitale",
        "value": f"{digital}/100",
        "status": "weak" if digital < 45 else "medium" if digital < 70 else "strong",
    })
    current.append({
        "label": "Site actuel",
        "value": (
            f"Audit {round(float(audit_score))}/100" if website and audit_score is not None
            else "Site détecté, audit à compléter" if website
            else "Aucun site détecté"
        ),
        "status": "weak" if not website or (audit_score is not None and float(audit_score) < 55) else "medium",
    })

    issue_to_fix = {
        "HTTPS absent": ("Sécurisation HTTPS", "Site rassurant et accessible en HTTPS"),
        "Mobile non optimisé": ("Expérience mobile", "Parcours mobile clair et responsive"),
        "Meta description absente": ("SEO local", "Balises locales propres et orientées clic"),
        "Schema LocalBusiness absent": ("SEO local", "Données structurées LocalBusiness"),
        "Appel en 1 clic absent": ("Conversion", "Bouton appel visible sur mobile"),
        "Formulaire de contact absent": ("Conversion", "Formulaire court de demande de contact"),
        "CTA commercial faible": ("Conversion", "CTA principal visible immédiatement"),
        "Preuve sociale faible": ("Confiance", "Avis clients mis en avant"),
        "Pages légales non détectées": ("Confiance", "Mentions légales et confidentialité"),
        "Réponse serveur lente": ("Performance", "Pages plus légères et rapides"),
        "Site inaccessible": ("Disponibilité", "Présence web stable et accessible"),
    }

    proposed: List[Dict[str, str]] = []
    seen = set()
    for issue in _audit_issues(data):
        title = issue.get("title") or ""
        label, result = issue_to_fix.get(
            title,
            ("Amélioration digitale", issue.get("recommendation") or title or "Correction du point détecté"),
        )
        key = (label, result)
        if key in seen:
            continue
        seen.add(key)
        proposed.append({"label": label, "result": result, "source_issue": title})
        if len(proposed) >= 5:
            break

    if not website and not proposed:
        proposed.extend([
            {"label": "Présence web", "result": "Site professionnel adapté au commerce", "source_issue": "Aucun site"},
            {"label": "Conversion", "result": "Téléphone, formulaire et CTA visibles", "source_issue": "Aucun site"},
            {"label": "SEO local", "result": "Base technique pour être compris localement", "source_issue": "Aucun site"},
        ])

    if data.get("generated_html"):
        proposed.insert(0, {
            "label": "Démo prête",
            "result": "Une version personnalisée est déjà disponible pour comparaison",
            "source_issue": "Local Pulse",
        })

    if rating >= 4.2 and reviews >= 15 and digital < 65:
        hook = (
            f"{name} a déjà une preuve de demande forte sur Google, "
            "mais sa présence digitale ne transforme pas encore pleinement cette réputation en prises de contact."
        )
    elif digital < 50:
        hook = (
            f"Le principal levier détecté pour {name} est la présence digitale : "
            "l'objectif est de rendre le parcours client plus simple entre Google et la prise de contact."
        )
    else:
        hook = (
            f"{name} dispose déjà d'une base digitale correcte. "
            "La démo sert à montrer les améliorations de conversion et de visibilité locale encore possibles."
        )

    talking_points = []
    if rating >= 4.2:
        talking_points.append(f"Partir d'un point positif : la note Google de {rating:.1f}/5.")
    if reviews >= 30:
        talking_points.append(f"Valoriser les {reviews} avis existants plutôt que critiquer l'activité.")
    if website and audit_score is not None:
        talking_points.append(f"Montrer visuellement 2 ou 3 écarts de l'audit du site ({round(float(audit_score))}/100).")
    if data.get("generated_html"):
        talking_points.append("Ouvrir directement la démo pendant l'appel : montrer avant d'expliquer.")
    talking_points.append("Ne promettre aucun volume de clients : vendre les améliorations concrètes du parcours local.")

    return {
        "version": 1,
        "headline": f"Avant / Après — {name}",
        "hook": hook,
        "opportunity_score": opportunity,
        "digital_health_score": digital,
        "current": current,
        "proposed": proposed[:6],
        "talking_points": talking_points,
    }


def build_outreach_sequence(data: Dict[str, Any], demo_url: str) -> List[Dict[str, Any]]:
    """Prépare quatre contacts. Les contenus restent à valider/copier par l'utilisateur."""
    name = _name(data)
    greeting = _greeting(data)
    rating = float(data.get("rating") or 0)
    reviews = int(data.get("user_ratings_total") or 0)
    audit = data.get("website_audit") or {}
    issues = _audit_issues(data)
    first_issue = (issues[0].get("title") if issues else "") or "quelques points de conversion locale"

    proof_line = ""
    if rating >= 4.0 and reviews > 0:
        proof_line = f"J'ai vu vos {reviews} avis Google et votre note de {rating:.1f}/5 : vous avez déjà une vraie preuve de confiance locale. "

    initial_body = (
        f"{greeting}\n\n"
        f"{proof_line}En regardant la présence digitale de {name}, j'ai repéré {first_issue.lower()}.\n\n"
        "J'ai préparé une démo personnalisée pour vous montrer concrètement ce que je changerais, "
        "sans vous demander de refaire quoi que ce soit vous-même.\n\n"
        f"Démo : {demo_url}\n\n"
        "Si le résultat vous parle, je peux vous expliquer en 15 minutes comment je m'occupe de la mise en place et du suivi.\n\n"
        "Bonne journée,\nLudovic\nLocal Pulse"
    )

    call_script = (
        f"Bonjour, Ludovic de Local Pulse. Je vous appelle au sujet de {name}. "
        "J'ai regardé votre présence Google et votre site, puis j'ai préparé une démo personnalisée. "
        "Je ne vous appelle pas pour vous vendre un site générique : je veux simplement vous montrer "
        "les points précis que j'ai détectés et la version que j'ai préparée. "
        "Est-ce que vous avez deux minutes maintenant, ou je vous rappelle à un meilleur moment ?"
    )

    followup_body = (
        f"{greeting}\n\n"
        f"Je reviens simplement vers vous pour la démo préparée pour {name}.\n"
        f"{demo_url}\n\n"
        "Le plus simple est de regarder la différence pendant 2 minutes : parcours mobile, prise de contact "
        "et mise en avant de votre réputation locale.\n\n"
        "Si vous voulez, dites-moi simplement « appelez-moi » et je vous montre les points importants.\n\n"
        "Ludovic — Local Pulse"
    )

    final_body = (
        f"{greeting}\n\n"
        f"Je clôture mon suivi concernant la démo de {name}. Je vous laisse le lien une dernière fois :\n"
        f"{demo_url}\n\n"
        "Si le sujet n'est pas prioritaire, aucun souci. Si vous souhaitez que je vous explique les améliorations "
        "identifiées, répondez simplement à ce message et je vous rappelle.\n\n"
        "Ludovic — Local Pulse"
    )

    return [
        {
            "index": 0, "day_offset": 0, "channel": "email",
            "title": "Envoyer la démo personnalisée",
            "subject": f"J'ai préparé une démo pour {name}",
            "content": initial_body,
            "why": "Premier contact : apporter une preuve concrète avant de parler d'offre.",
        },
        {
            "index": 1, "day_offset": 2, "channel": "phone",
            "title": "Appel court de suivi",
            "subject": "",
            "content": call_script,
            "why": "Vérifier que la démo a été vue et proposer un échange court.",
        },
        {
            "index": 2, "day_offset": 5, "channel": "email",
            "title": "Relance valeur",
            "subject": f"Votre démo {name} — les 3 points à regarder",
            "content": followup_body,
            "why": "Ramener le prospect vers les améliorations visibles, sans pression.",
        },
        {
            "index": 3, "day_offset": 10, "channel": "email",
            "title": "Dernière relance",
            "subject": f"Je clôture le suivi — {name}",
            "content": final_body,
            "why": "Fermer proprement la séquence et éviter les relances indéfinies.",
        },
    ]


def derive_next_action(data: Dict[str, Any], now: datetime.datetime | None = None) -> Dict[str, Any]:
    """Calcule la meilleure action suivante à partir de l'état du prospect."""
    now = now or datetime.datetime.utcnow()
    if data.get("prospecting_opt_out"):
        return {"action": "none", "label": "Ne pas contacter", "reason": "Prospect opposé à la prospection", "due_at": None}
    stage = data.get("crm_stage") or "prospect"
    if stage in ("won", "lost"):
        return {"action": "none", "label": "Aucune relance", "reason": f"Pipeline: {stage}", "due_at": None}

    if not data.get("generated_html"):
        return {
            "action": "generate_demo", "label": "Générer la démo",
            "reason": "La démonstration commerciale n'est pas encore prête.",
            "due_at": now.isoformat(),
        }

    if not (data.get("owner_email") or data.get("owner_phone") or data.get("business_phone")):
        return {
            "action": "enrich_contact", "label": "Enrichir le contact",
            "reason": "Aucun canal de contact exploitable n'est enregistré.",
            "due_at": now.isoformat(),
        }

    status = data.get("outreach_status") or "not_started"
    if status == "not_started":
        return {
            "action": "start_outreach", "label": "Démarrer la séquence",
            "reason": "Démo prête et canal de contact disponible.",
            "due_at": now.isoformat(),
        }

    due = data.get("next_action_due_at")
    if isinstance(due, datetime.datetime):
        due_iso = due.isoformat()
    else:
        due_iso = str(due) if due else None

    step = int(data.get("outreach_step") or 0)
    sequence = data.get("outreach_sequence") or []
    if status == "active" and step < len(sequence):
        item = sequence[step]
        return {
            "action": "outreach_step",
            "label": item.get("title") or "Relancer le prospect",
            "reason": item.get("why") or "Étape prévue dans la séquence commerciale.",
            "channel": item.get("channel"),
            "step": step,
            "due_at": due_iso or now.isoformat(),
        }

    return {
        "action": "review", "label": "Revoir le prospect",
        "reason": "Séquence terminée : décider de poursuivre, négocier ou classer.",
        "due_at": due_iso,
    }


def due_date(started_at: datetime.datetime, day_offset: int) -> datetime.datetime:
    return started_at + datetime.timedelta(days=int(day_offset or 0))
