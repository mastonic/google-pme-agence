"""Rapport mensuel envoyé par e-mail aux clients PulsePro.

Le 1er de chaque mois, chaque client actif reçoit le bilan du mois écoulé :
visites, appels, WhatsApp, itinéraires, formulaires, provenance des visites,
valeur potentielle (contacts × panier moyen) et appels de la Réceptionniste IA.
"""
from __future__ import annotations

import datetime
import html
import os
from typing import Any

from sqlalchemy.orm import Session

from backend.models.database import Business, SiteDailyStat

MONTHS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
             "septembre", "octobre", "novembre", "décembre"]
METRICS = [
    ("visits", "Visites du site"),
    ("calls", "Clics « Appeler »"),
    ("whatsapp", "Clics WhatsApp"),
    ("directions", "Demandes d'itinéraire"),
    ("forms", "Formulaires envoyés"),
]
BRAND = "#00A896"
INK = "#1E293B"


def month_bounds(period: str) -> tuple[datetime.date, datetime.date]:
    """« AAAA-MM » → (premier jour, dernier jour)."""
    year, month = (int(x) for x in period.split("-"))
    start = datetime.date(year, month, 1)
    nxt = datetime.date(year + (month == 12), month % 12 + 1, 1)
    return start, nxt - datetime.timedelta(days=1)


def previous_period(period: str) -> str:
    start, _ = month_bounds(period)
    prev = start - datetime.timedelta(days=1)
    return f"{prev.year:04d}-{prev.month:02d}"


def last_closed_period(today: datetime.date | None = None) -> str:
    """Mois écoulé (le rapport du 1er novembre porte sur octobre)."""
    today = today or datetime.date.today()
    prev = today.replace(day=1) - datetime.timedelta(days=1)
    return f"{prev.year:04d}-{prev.month:02d}"


def _period_label(period: str) -> str:
    start, _ = month_bounds(period)
    return f"{MONTHS_FR[start.month - 1]} {start.year}"


def _totals(db: Session, business_id: str, period: str) -> dict[str, int]:
    start, end = month_bounds(period)
    rows = db.query(SiteDailyStat).filter(SiteDailyStat.business_id == business_id,
                                          SiteDailyStat.day >= start.isoformat(),
                                          SiteDailyStat.day <= end.isoformat()).all()
    return {k: sum(int(getattr(r, k) or 0) for r in rows) for k, _ in METRICS}


def _delta(cur: int, prev: int) -> int | None:
    return None if not prev else round((cur - prev) / prev * 100)


def _receptionist(db: Session, b: Business, period: str) -> dict | None:
    try:
        from backend.models.database import ReceptionistCall
    except Exception:
        return None
    start, end = month_bounds(period)
    start_dt = datetime.datetime.combine(start, datetime.time.min)
    end_dt = datetime.datetime.combine(end, datetime.time.max)
    q = db.query(ReceptionistCall).filter(ReceptionistCall.business_id == b.id,
                                          ReceptionistCall.created_at >= start_dt,
                                          ReceptionistCall.created_at <= end_dt)
    received = q.count()
    if not received:
        return None
    return {
        "received": received,
        "urgent": q.filter(ReceptionistCall.urgent.is_(True)).count(),
        "recovered": q.filter(ReceptionistCall.recovered.is_(True)).count(),
    }


def build_report(db: Session, b: Business, period: str | None = None) -> dict[str, Any]:
    """Données + e-mail (texte et HTML) du rapport d'un mois donné."""
    from backend.client_space_api import (
        avg_ticket, display_business_name, potential_value, source_totals, space_url,
    )

    period = period or last_closed_period()
    prev = previous_period(period)
    cur, before = _totals(db, b.id, period), _totals(db, b.id, prev)
    start, end = month_bounds(period)
    sources = source_totals(db, b.id, start, end)
    ticket = avg_ticket(b)
    contacts = cur["calls"] + cur["whatsapp"] + cur["forms"]
    contacts_prev = before["calls"] + before["whatsapp"] + before["forms"]
    value = potential_value(contacts, ticket)
    receptionist = _receptionist(db, b, period)
    name = display_business_name(b.name or "") or "votre commerce"
    first = (b.owner_first_name or "").strip()
    label = _period_label(period)
    link = space_url()

    data = {
        "business_id": b.id, "business_name": name, "period": period, "period_label": label,
        "to": b.owner_email or "",
        "metrics": [{"key": k, "label": l, "value": cur[k], "previous": before[k], "delta": _delta(cur[k], before[k])}
                    for k, l in METRICS],
        "contacts": contacts, "contacts_delta": _delta(contacts, contacts_prev),
        "sources": sources[:6], "avg_ticket": ticket, "value": value,
        "receptionist": receptionist,
    }

    # Phrase d'accroche
    if not any(cur.values()):
        headline = f"Pas encore de visite enregistrée en {label} : on surveille, et on vous tient au courant."
    elif data["contacts_delta"] is not None and data["contacts_delta"] > 0:
        headline = f"Bonne nouvelle : {contacts} contact(s) en {label}, soit {data['contacts_delta']}\u00a0% de plus que le mois précédent."
    else:
        headline = f"{cur['visits']} visite(s) et {contacts} contact(s) reçus grâce à votre site en {label}."
    data["headline"] = headline

    subject = f"Votre bilan PulsePro de {label} — {name}"

    # Texte brut
    lines = [f"Bonjour{(' ' + first) if first else ''},", "", headline, ""]
    for m in data["metrics"]:
        d = "" if m["delta"] is None else f" ({'+' if m['delta'] >= 0 else ''}{m['delta']} %)"
        lines.append(f"- {m['label']} : {m['value']}{d}")
    if value:
        lines += ["", f"Valeur potentielle : {value:,} € ({contacts} contacts × {ticket} € de panier moyen)".replace(",", " ")]
    if sources:
        lines += ["", "D'où viennent vos visiteurs :"] + [f"- {s['label']} : {s['visits']}" for s in sources[:6]]
    if receptionist:
        lines += ["", f"Réceptionniste IA : {receptionist['received']} appel(s) pris pour vous"
                      f"{', dont ' + str(receptionist['urgent']) + ' urgent(s)' if receptionist['urgent'] else ''}."]
    lines += ["", f"Le détail jour par jour est dans votre espace : {link}", "", "L'équipe PulsePro"]
    text = "\n".join(lines)

    # HTML (tableaux + styles en ligne : compatible avec les messageries)
    e = html.escape
    rows = "".join(
        f'<tr><td style="padding:10px 0;border-bottom:1px solid #EEF2F5;color:#475569">{e(m["label"])}</td>'
        f'<td style="padding:10px 0;border-bottom:1px solid #EEF2F5;text-align:right;font-weight:700;color:{INK}">{m["value"]}</td>'
        f'<td style="padding:10px 0 10px 12px;border-bottom:1px solid #EEF2F5;text-align:right;white-space:nowrap;'
        f'color:{"#047857" if (m["delta"] or 0) >= 0 else "#B91C1C"};font-size:13px">'
        f'{"" if m["delta"] is None else (("+" if m["delta"] >= 0 else "") + str(m["delta"]) + " %")}</td></tr>'
        for m in data["metrics"])
    src_html = ""
    if sources:
        total = sum(s["visits"] for s in sources) or 1
        src_html = (f'<h2 style="font:700 16px Montserrat,Arial,sans-serif;color:{INK};margin:28px 0 8px">D\'où viennent vos visiteurs</h2>'
                    + "".join(
                        f'<div style="margin:8px 0"><div style="display:flex;justify-content:space-between;font-size:14px;color:#475569">'
                        f'<span>{e(s["label"])}</span><b style="color:{INK}">{s["visits"]}</b></div>'
                        f'<div style="height:6px;background:#EEF2F5;border-radius:3px"><div style="height:6px;border-radius:3px;'
                        f'background:{BRAND};width:{round(s["visits"] / total * 100)}%"></div></div></div>'
                        for s in sources[:6]))
    value_html = ""
    if value:
        value_html = (f'<div style="margin:24px 0;padding:18px 20px;border-radius:14px;background:#E6F7F5">'
                      f'<div style="font-size:13px;color:#028090;font-weight:600">Valeur potentielle générée</div>'
                      f'<div style="font:800 28px Montserrat,Arial,sans-serif;color:{INK};margin-top:4px">{value:,} €</div>'
                      f'<div style="font-size:13px;color:#475569">{contacts} contacts × {ticket} € de panier moyen</div></div>').replace(",", "&#8239;")
    rec_html = ""
    if receptionist:
        rec_html = (f'<p style="margin:20px 0 0;padding:14px 16px;border-radius:12px;background:{INK};color:#fff;font-size:14px">'
                    f'☎ Réceptionniste IA : <b>{receptionist["received"]}</b> appel(s) pris pour vous'
                    f'{", dont <b>" + str(receptionist["urgent"]) + "</b> urgent(s)" if receptionist["urgent"] else ""}.</p>')
    body_html = f"""<!DOCTYPE html><html lang="fr"><body style="margin:0;background:#F5F8FA;font-family:Inter,Arial,sans-serif">
<div style="max-width:560px;margin:0 auto;padding:24px 16px">
 <div style="font:800 18px Montserrat,Arial,sans-serif;color:{INK}">PULSE<span style="color:{BRAND}">PRO</span></div>
 <div style="background:#fff;border:1px solid #E2E8F0;border-radius:18px;padding:28px;margin-top:16px">
  <div style="font-size:13px;font-weight:600;color:#028090;text-transform:uppercase;letter-spacing:.08em">Bilan de {e(label)}</div>
  <h1 style="font:800 22px Montserrat,Arial,sans-serif;color:{INK};margin:8px 0 6px">{e(name)}</h1>
  <p style="font-size:15px;line-height:1.55;color:#475569;margin:0 0 18px">Bonjour{(' ' + e(first)) if first else ''}, {e(headline[0].lower() + headline[1:])}</p>
  <table role="presentation" style="width:100%;border-collapse:collapse;font-size:15px">{rows}</table>
  {value_html}{src_html}{rec_html}
  <p style="margin:28px 0 0"><a href="{e(link)}" style="display:inline-block;background:{INK};color:#fff;text-decoration:none;padding:13px 22px;border-radius:999px;font-weight:600">Voir le détail dans mon espace</a></p>
 </div>
 <p style="font-size:12px;color:#94A3B8;text-align:center;margin:16px 0">Pulse-Pro · solution éditée par HoldMasto · mesure d'audience anonyme, sans cookie.</p>
</div></body></html>"""

    data.update({"subject": subject, "text": text, "html": body_html})
    return data


def send_email(to: str, subject: str, text: str, html_body: str | None = None) -> bool:
    """Envoi SMTP (mêmes variables que les alertes). False si non configuré ou en échec."""
    import smtplib
    from email.message import EmailMessage

    host = os.getenv("SMTP_HOST")
    if not host or not to:
        print(f"[RAPPORT] SMTP non configuré ou destinataire absent : rapport non envoyé ({to})")
        return False
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "contact@pulsepro.fr"))
    msg["To"] = to
    msg.set_content(text)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=20) as server:
            server.starttls()
            if os.getenv("SMTP_USER"):
                server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            server.send_message(msg)
        return True
    except Exception as exc:
        print(f"[RAPPORT] envoi échoué ({exc})")
        return False


def send_monthly_reports(db: Session, period: str | None = None, force: bool = False) -> dict:
    """Envoie le rapport du mois écoulé à tous les clients actifs (une seule fois par mois et par client)."""
    from backend.client_space_api import _profile, is_live, set_profile

    period = period or last_closed_period()
    sent, skipped, failed = 0, 0, 0
    for b in db.query(Business).filter(Business.subscription_status.in_(("active", "trialing"))).all():
        if not is_live(b) or not b.owner_email:
            skipped += 1
            continue
        profile = _profile(b)
        reports = profile.get("reports") if isinstance(profile.get("reports"), dict) else {}
        if reports.get("enabled") is False or (reports.get("last_period") == period and not force):
            skipped += 1
            continue
        report = build_report(db, b, period)
        if send_email(b.owner_email, report["subject"], report["text"], report["html"]):
            reports.update({"last_period": period, "last_sent_at": datetime.datetime.utcnow().isoformat() + "Z"})
            profile["reports"] = reports
            set_profile(b, profile)
            db.commit()
            sent += 1
        else:
            failed += 1
    return {"period": period, "sent": sent, "skipped": skipped, "failed": failed}
