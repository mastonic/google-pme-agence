"""Planning des courses et validation départ / arrivée / retour par l'équipage.

Cycle d'une mission :
    planifiee → acceptee → en_cours (départ validé) → arrivee (patient déposé)
              → terminee (retour validé) ; annulee à tout moment avant la fin.

Cycle d'une journée : brouillon → publie (visible par les équipiers) → valide
(clôturée par le gérant : plus de modification).

Les heures réelles de départ alimentent le dossier de facturation : le
rattachement des traces GPS se fait sur l'heure réellement validée, pas sur
l'heure prévue. Aucune position GPS n'est enregistrée ici (le boîtier certifié
s'en charge) : seulement l'horodatage, l'auteur et, en option, le compteur.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from backend.services import pmt, pmt_equipe

MISSION_STATUSES = {
    "planifiee": "Planifiée",
    "acceptee": "Acceptée",
    "en_cours": "En route",
    "arrivee": "Patient déposé",
    "terminee": "Terminée",
    "annulee": "Annulée",
}
DAY_STATUSES = {"brouillon": "Brouillon", "publie": "Publié", "valide": "Validé"}

# action → (statuts de départ autorisés, statut d'arrivée)
TRANSITIONS = {
    "accepter": (("planifiee",), "acceptee"),
    "depart": (("planifiee", "acceptee"), "en_cours"),
    "arrivee": (("en_cours",), "arrivee"),
    "retour": (("en_cours", "arrivee"), "terminee"),
    "annuler": (("planifiee", "acceptee", "en_cours", "arrivee"), "annulee"),
}
ACTION_LABELS = {"accepter": "Mission acceptée", "depart": "Départ validé", "arrivee": "Arrivée validée",
                 "retour": "Retour validé", "annuler": "Mission annulée"}
TRAJETS = {"aller": "Aller", "retour": "Retour", "aller_retour": "Aller-retour"}
DEFAULT_DURATION_MIN = 60


def now_local() -> dt.datetime:
    """Heure française (PMT_TIMEZONE), quelle que soit l'horloge du serveur (souvent en UTC)."""
    from backend.services.pmt_traces import _local_tz
    return dt.datetime.now(_local_tz()).replace(tzinfo=None)


class TransitionError(ValueError):
    pass


def normalize_mission(raw: dict) -> dict:
    m = dict(raw or {})
    m["date"] = pmt._iso(m.get("date"))
    m["heure_prevue"] = (m.get("heure_prevue") or "")[:5]
    m["duree_min"] = int(m.get("duree_min") or DEFAULT_DURATION_MIN)
    m["type_trajet"] = m.get("type_trajet") if m.get("type_trajet") in TRAJETS else "aller"
    m["mode"] = m.get("mode") if m.get("mode") in ("ambulance", "tap") else "ambulance"
    m["equipage_ids"] = [i for i in (m.get("equipage_ids") or []) if i]
    for f in ("patient_nom", "adresse_depart", "adresse_arrivee", "vehicule", "notes"):
        m[f] = str(m.get(f) or "").strip()
    m["patient_nom"] = m["patient_nom"].upper()
    return m


def window(mission: dict) -> Optional[tuple[dt.datetime, dt.datetime]]:
    d = pmt.parse_date(mission.get("date"))
    h = mission.get("heure_prevue") or ""
    if not d or len(h) < 4:
        return None
    try:
        hh, mm = map(int, h.split(":")[:2])
    except ValueError:
        return None
    start = dt.datetime.combine(d, dt.time(hh, mm))
    return start, start + dt.timedelta(minutes=int(mission.get("duree_min") or DEFAULT_DURATION_MIN))


def conflicts(missions: list[dict], employees: dict[str, dict]) -> dict[str, list[str]]:
    """Problèmes de planification par mission : chevauchements, équipage, documents."""
    out: dict[str, list[str]] = {m["id"]: [] for m in missions}
    active = [m for m in missions if m.get("status") != "annulee"]
    for i, a in enumerate(active):
        wa = window(a)
        for b in active[i + 1:]:
            wb = window(b)
            if not wa or not wb or not (wa[0] < wb[1] and wb[0] < wa[1]):
                continue
            shared = set(a["equipage_ids"]) & set(b["equipage_ids"])
            for eid in shared:
                name = _name(employees.get(eid))
                out[a["id"]].append(f"{name} est aussi sur la mission de {b['heure_prevue']}")
                out[b["id"]].append(f"{name} est aussi sur la mission de {a['heure_prevue']}")
            if a["vehicule"] and b["vehicule"] and _plate(a["vehicule"]) == _plate(b["vehicule"]):
                out[a["id"]].append(f"Véhicule {a['vehicule']} déjà pris à {b['heure_prevue']}")
                out[b["id"]].append(f"Véhicule {b['vehicule']} déjà pris à {a['heure_prevue']}")
    for m in active:
        crew = [pmt_equipe.snapshot(eid, employees[eid]) for eid in m["equipage_ids"] if eid in employees]
        on = pmt.parse_date(m.get("date"))
        for c in pmt_equipe.check_crew(m["mode"], crew, on):
            if c["code"] != "EQUIPAGE_VIDE":
                out[m["id"]].append(c["message"])
        if not m["equipage_ids"]:
            out[m["id"]].append("Équipage non affecté")
        if not m["vehicule"]:
            out[m["id"]].append("Véhicule non affecté")
    return out


def _name(emp: Optional[dict]) -> str:
    if not emp:
        return "Un équipier"
    e = pmt_equipe.normalize(emp)
    return f"{e.prenom} {e.nom}".strip()


def _plate(v: str) -> str:
    import re
    return re.sub(r"[^A-Z0-9]", "", (v or "").upper())


def apply_action(mission: dict, action: str, actor: str, at: Optional[dt.datetime] = None,
                 km_compteur: Optional[float] = None) -> dict:
    """Fait avancer la mission ; lève TransitionError si l'étape n'est pas possible."""
    if action not in TRANSITIONS:
        raise TransitionError("Action inconnue")
    allowed, target = TRANSITIONS[action]
    status = mission.get("status") or "planifiee"
    if status not in allowed:
        raise TransitionError(f"Impossible : la mission est « {MISSION_STATUSES.get(status, status)} ».")
    at = at or now_local()
    m = dict(mission)
    event = {"action": action, "label": ACTION_LABELS[action], "at": at.replace(microsecond=0).isoformat(), "par": actor}
    if km_compteur is not None:
        event["km_compteur"] = km_compteur
    m["events"] = [*(m.get("events") or []), event]
    m["status"] = target
    return m


def event_time(mission: dict, action: str) -> Optional[str]:
    for e in reversed(mission.get("events") or []):
        if e.get("action") == action:
            return e.get("at")
    return None


def odometer_km(mission: dict) -> Optional[float]:
    """Km relevés au compteur entre le départ et le retour (contrôle de cohérence avec la trace)."""
    start = next((e.get("km_compteur") for e in mission.get("events") or [] if e.get("action") == "depart"
                  and e.get("km_compteur") is not None), None)
    end = next((e.get("km_compteur") for e in reversed(mission.get("events") or []) if e.get("action") == "retour"
                and e.get("km_compteur") is not None), None)
    if start is None or end is None or end < start:
        return None
    return round(end - start, 1)


def transport_from_mission(mission: dict) -> dict:
    """Détails de course pré-remplis dans le dossier de facturation, à partir de ce qui a été validé."""
    depart = event_time(mission, "depart")
    return {
        "date_transport": mission.get("date"),
        "heure_depart": (depart or "")[11:16] or mission.get("heure_prevue", ""),
        "vehicule": mission.get("vehicule", ""),
        "equipage_ids": list(mission.get("equipage_ids") or []),
    }


def day_summary(missions: list[dict]) -> dict:
    counts = {k: 0 for k in MISSION_STATUSES}
    for m in missions:
        counts[m.get("status") or "planifiee"] = counts.get(m.get("status") or "planifiee", 0) + 1
    open_ = [m for m in missions if m.get("status") not in ("terminee", "annulee")]
    late = []
    now = now_local()
    for m in missions:
        w = window(m)
        if w and m.get("status") in ("planifiee", "acceptee") and now > w[0] + dt.timedelta(minutes=15):
            late.append(m["id"])
    return {"total": len(missions), "par_statut": counts, "non_terminees": len(open_), "en_retard": late}
