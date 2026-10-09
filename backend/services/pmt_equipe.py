"""Équipe d'une société d'ambulances : qualifications, documents, conformité des équipages.

Règles (Code de la santé publique, R. 6312-7 et R. 6312-10 ; guides ARS) :
- ambulance : deux personnes, dont au moins une titulaire du DEA (ou CCA / DA) ;
- VSL (transport assis professionnalisé) : une personne, DEA / CCA / DA ou
  auxiliaire ambulancier ;
- chaque équipier : attestation préfectorale d'aptitude à la conduite
  d'ambulance et AFGSU de niveau 2 en cours de validité (recyclage tous les
  4 ans), salarié déclaré à l'ARS.

Un transport réalisé par un équipage non conforme expose à un indu lors d'un
contrôle et à une sanction de l'ARS : on le signale avant la facturation.

Minimisation : aucune donnée médicale ; de la visite médicale on ne garde que
la date de fin d'aptitude.
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from backend.services import pmt

QUALIFICATIONS = {
    "DEA": "Diplôme d'État d'ambulancier",
    "CCA": "Certificat de capacité d'ambulancier",
    "DA": "Diplôme d'ambulancier",
    "auxiliaire": "Auxiliaire ambulancier",
    "conducteur": "Conducteur d'ambulance",
    "stagiaire": "Stagiaire",
    "autre": "Autre",
}
LEADER = {"DEA", "CCA", "DA"}                 # peut être chef d'équipage d'une ambulance
TAP_OK = LEADER | {"auxiliaire"}             # peut conduire seul un VSL
SECOND = TAP_OK | {"conducteur"}             # peut être second équipier d'une ambulance
CONTRATS = ("CDI", "CDD", "interim", "vacataire", "mise_a_disposition")
AFGSU_YEARS = 4
SOON_DAYS = 60

DOCUMENTS = {
    "attestation_prefectorale_fin": "Attestation préfectorale de conduite",
    "afgsu2_fin": "AFGSU niveau 2",
    "permis_fin": "Permis de conduire",
    "aptitude_medicale_fin": "Aptitude médicale",
}
REQUIRED_DOCUMENTS = ("attestation_prefectorale_fin", "afgsu2_fin")


class Employee(BaseModel):
    model_config = ConfigDict(extra="ignore")
    nom: str = ""
    prenom: str = ""
    qualification: str = "autre"
    numero_rpps: str = ""
    attestation_prefectorale_fin: str = ""   # AAAA-MM-JJ, date portée sur l'attestation
    afgsu2_fin: str = ""
    permis_fin: str = ""
    aptitude_medicale_fin: str = ""
    contrat: str = "CDI"
    contrat_debut: str = ""
    contrat_fin: str = ""
    declare_ars_le: str = ""
    actif: bool = True

    @field_validator("qualification")
    @classmethod
    def _qualif(cls, v):
        return v if v in QUALIFICATIONS else "autre"

    @field_validator("contrat")
    @classmethod
    def _contrat(cls, v):
        return v if v in CONTRATS else "CDI"


def normalize(raw) -> Employee:
    e = Employee.model_validate(raw or {})
    e.nom = e.nom.strip().upper()
    e.prenom = e.prenom.strip()
    for f in (*DOCUMENTS, "contrat_debut", "contrat_fin", "declare_ars_le"):
        setattr(e, f, pmt._iso(getattr(e, f)))
    return e


def afgsu_end_from_obtention(obtention: str) -> str:
    d = pmt.parse_date(obtention)
    if not d:
        return ""
    try:
        return d.replace(year=d.year + AFGSU_YEARS).isoformat()
    except ValueError:     # 29 février
        return (d + dt.timedelta(days=365 * AFGSU_YEARS + 1)).isoformat()


def compliance(raw, on: Optional[dt.date] = None) -> dict:
    """État d'un salarié à une date : ok | bientot (moins de 60 jours) | non_conforme."""
    e = normalize(raw)
    on = on or dt.date.today()
    issues, soon = [], []
    for field, label in DOCUMENTS.items():
        end = pmt.parse_date(getattr(e, field))
        if not end:
            if field in REQUIRED_DOCUMENTS:
                issues.append(f"{label} : date de fin de validité non renseignée")
            continue
        if end < on:
            issues.append(f"{label} expirée depuis le {end.strftime('%d/%m/%Y')}")
        elif (end - on).days <= SOON_DAYS:
            soon.append(f"{label} expire le {end.strftime('%d/%m/%Y')}")
    start, end = pmt.parse_date(e.contrat_debut), pmt.parse_date(e.contrat_fin)
    if start and start > on:
        issues.append(f"Contrat commençant le {start.strftime('%d/%m/%Y')}")
    if end and end < on:
        issues.append(f"Contrat terminé le {end.strftime('%d/%m/%Y')}")
    if not e.actif:
        issues.append("Salarié inactif")
    if not e.declare_ars_le:
        soon.append("Déclaration à l'ARS non renseignée")
    status = "non_conforme" if issues else ("bientot" if soon else "ok")
    return {"status": status, "problemes": issues, "alertes": soon}


def snapshot(employee_id: str, raw) -> dict:
    """Ce qu'un dossier garde de chaque équipier : de quoi contrôler à la date du transport."""
    e = normalize(raw)
    return {"id": employee_id, "nom": f"{e.prenom} {e.nom}".strip(), "qualification": e.qualification,
            **{f: getattr(e, f) for f in (*DOCUMENTS, "contrat_debut", "contrat_fin")}, "actif": e.actif}


def check_crew(mode: Optional[str], crew: list[dict], on: Optional[dt.date]) -> list[dict]:
    """Contrôles d'équipage pour un dossier (format des contrôles de pmt.validate_pmt)."""
    checks = []

    def add(level, code, message, fix=""):
        checks.append({"level": level, "code": code, "field": "transport.equipage_ids", "message": message, "fix": fix})

    qualifs = [m.get("qualification") for m in crew]
    if mode == "ambulance":
        if len(crew) < 2:
            add("error", "EQUIPAGE_INCOMPLET", "Une ambulance roule avec deux équipiers.",
                "Renseigner le second équipier de la course.")
        elif not any(q in LEADER for q in qualifs):
            add("error", "EQUIPAGE_SANS_DEA", "Aucun équipier titulaire du DEA (ou CCA / DA) dans l'ambulance.",
                "Un équipage d'ambulance doit compter au moins un diplômé d'État.")
        elif not all(q in SECOND for q in qualifs):
            add("error", "EQUIPAGE_QUALIFICATION", "Un équipier n'a pas la qualification requise pour une ambulance.",
                "Second équipier : DEA, CCA, auxiliaire ambulancier ou conducteur d'ambulance.")
    elif mode == "tap":
        if not crew:
            add("warning", "EQUIPAGE_VIDE", "Conducteur du VSL non renseigné.")
        elif not any(q in TAP_OK for q in qualifs):
            add("error", "EQUIPAGE_QUALIFICATION", "Le conducteur du VSL n'a pas la qualification requise.",
                "DEA, CCA ou auxiliaire ambulancier.")
    for m in crew:
        state = compliance(m, on)
        if state["problemes"]:
            add("error", "EQUIPIER_NON_CONFORME", f"{m.get('nom') or 'Équipier'} : {state['problemes'][0]}.",
                "Un transport réalisé par un équipier non en règle peut être réclamé en indu lors d'un contrôle.")
    return checks
