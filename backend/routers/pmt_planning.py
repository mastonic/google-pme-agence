"""API planning : courses du jour, publication, validation départ / arrivée / retour, clôture."""

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import PmtEmployee, PmtMission, PmtPlanningDay, PmtVoucher, get_db
from backend.routers.pmt_auth import get_current_user, require_manager
from backend.services import pmt, pmt_planning
from backend.services.pmt_auth import CurrentUser

router = APIRouter(prefix="/pmt/planning", tags=["transport-sanitaire-planning"],
                   dependencies=[Depends(get_current_user)])


def _business(user: CurrentUser, business_id) -> str:
    b = user.scope(business_id or None)
    if not b:
        raise HTTPException(status_code=400, detail="Choisir le client ambulancier")
    return b


def _day(db: Session, business_id: str, date: str) -> PmtPlanningDay:
    key = f"{business_id}|{date}"
    d = db.query(PmtPlanningDay).filter(PmtPlanningDay.id == key).first()
    if not d:
        d = PmtPlanningDay(id=key, business_id=business_id, date=date, status="brouillon")
        db.add(d)
        db.flush()
    return d


def _employees(db: Session, business_id: str) -> dict:
    return {e.id: e.data for e in db.query(PmtEmployee).filter(PmtEmployee.business_id == business_id).all()}


def _my_employee_id(db: Session, user: CurrentUser):
    e = db.query(PmtEmployee).filter(PmtEmployee.user_id == user.id).first()
    return e.id if e else None


def _mission_dict(m: PmtMission, employees: dict, problems=None) -> dict:
    data = m.data or {}
    names = []
    for eid in data.get("equipage_ids") or []:
        emp = employees.get(eid)
        names.append(pmt_planning._name(emp) if emp else "?")
    return {
        "id": m.id, "business_id": m.business_id, **data, "status": m.status,
        "status_label": pmt_planning.MISSION_STATUSES.get(m.status, m.status),
        "events": m.events or [], "voucher_id": m.voucher_id, "equipage_noms": names,
        "km_compteur": pmt_planning.odometer_km({"events": m.events or []}),
        "problemes": problems or [],
    }


def _as_plain(m: PmtMission) -> dict:
    return {"id": m.id, **(m.data or {}), "status": m.status, "events": m.events or []}


def _check_editable(day: PmtPlanningDay):
    if day.status == "valide":
        raise HTTPException(status_code=409, detail="Journée validée : plus de modification possible")


@router.get("/jour")
async def get_day(date: str, business_id: str = None, db: Session = Depends(get_db),
                  user: CurrentUser = Depends(require_manager)):
    """Planning complet d'une journée, avec les problèmes détectés (chevauchements, équipage)."""
    b = _business(user, business_id)
    date = pmt._iso(date)
    day = _day(db, b, date)
    missions = db.query(PmtMission).filter(PmtMission.business_id == b, PmtMission.date == date).all()
    employees = _employees(db, b)
    problems = pmt_planning.conflicts([_as_plain(m) for m in missions], employees)
    rows = sorted((_mission_dict(m, employees, problems.get(m.id)) for m in missions),
                  key=lambda x: x.get("heure_prevue") or "")
    db.commit()
    return {
        "date": date, "business_id": b, "status": day.status,
        "status_label": pmt_planning.DAY_STATUSES[day.status],
        "published_at": day.published_at.isoformat() if day.published_at else None,
        "validated_at": day.validated_at.isoformat() if day.validated_at else None,
        "validated_by": day.validated_by,
        "missions": rows, "resume": pmt_planning.day_summary([_as_plain(m) for m in missions]),
    }


@router.post("/missions")
async def create_mission(payload: dict, db: Session = Depends(get_db), user: CurrentUser = Depends(require_manager)):
    b = _business(user, payload.get("business_id"))
    data = pmt_planning.normalize_mission(payload)
    if not data["date"] or not data["heure_prevue"]:
        raise HTTPException(status_code=400, detail="Date et heure de prise en charge obligatoires")
    day = _day(db, b, data["date"])
    _check_editable(day)
    valid_ids = set(_employees(db, b))
    data["equipage_ids"] = [i for i in data["equipage_ids"] if i in valid_ids]
    m = PmtMission(id=str(uuid.uuid4()), business_id=b, date=data["date"], data=data, status="planifiee", events=[])
    db.add(m)
    db.commit()
    return _mission_dict(m, _employees(db, b))


def _get(db: Session, mission_id: str, user: CurrentUser) -> PmtMission:
    m = db.query(PmtMission).filter(PmtMission.id == mission_id).first()
    if not m or not user.can_access(m.business_id):
        raise HTTPException(status_code=404, detail="Mission introuvable")
    return m


@router.put("/missions/{mission_id}")
async def update_mission(mission_id: str, payload: dict, db: Session = Depends(get_db),
                         user: CurrentUser = Depends(require_manager)):
    m = _get(db, mission_id, user)
    _check_editable(_day(db, m.business_id, m.date))
    data = pmt_planning.normalize_mission({**(m.data or {}), **payload})
    if data["date"] != m.date:
        _check_editable(_day(db, m.business_id, data["date"]))
    valid_ids = set(_employees(db, m.business_id))
    data["equipage_ids"] = [i for i in data["equipage_ids"] if i in valid_ids]
    m.data, m.date = data, data["date"]
    db.commit()
    return _mission_dict(m, _employees(db, m.business_id))


@router.delete("/missions/{mission_id}")
async def delete_mission(mission_id: str, db: Session = Depends(get_db), user: CurrentUser = Depends(require_manager)):
    m = _get(db, mission_id, user)
    _check_editable(_day(db, m.business_id, m.date))
    if m.status not in ("planifiee", "acceptee", "annulee"):
        raise HTTPException(status_code=409, detail="Mission commencée : l'annuler plutôt que la supprimer")
    db.delete(m)
    db.commit()
    return {"deleted": mission_id}


@router.post("/jour/publier")
async def publish_day(payload: dict, db: Session = Depends(get_db), user: CurrentUser = Depends(require_manager)):
    """Les équipiers voient leurs missions du jour à partir de la publication."""
    b = _business(user, payload.get("business_id"))
    day = _day(db, b, pmt._iso(payload.get("date")))
    _check_editable(day)
    day.status = "publie"
    day.published_at = datetime.datetime.utcnow()
    db.commit()
    return {"date": day.date, "status": day.status}


@router.post("/jour/valider")
async def validate_day(payload: dict, db: Session = Depends(get_db), user: CurrentUser = Depends(require_manager)):
    """Clôture de la journée par le gérant. Refusée s'il reste des missions non terminées (sauf forcer)."""
    b = _business(user, payload.get("business_id"))
    date = pmt._iso(payload.get("date"))
    day = _day(db, b, date)
    if day.status == "valide":
        return {"date": date, "status": day.status}
    missions = db.query(PmtMission).filter(PmtMission.business_id == b, PmtMission.date == date).all()
    open_ = [m for m in missions if m.status not in ("terminee", "annulee")]
    if open_ and not payload.get("forcer"):
        raise HTTPException(status_code=409, detail=f"{len(open_)} mission(s) non terminée(s) : les clôturer ou les annuler")
    day.status = "valide"
    day.validated_at = datetime.datetime.utcnow()
    day.validated_by = user.email
    db.commit()
    return {"date": date, "status": day.status, "missions_non_terminees": len(open_)}


@router.get("/mes-missions")
async def my_missions(date: str = None, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """Missions de l'équipier connecté, sur les journées publiées."""
    me = _my_employee_id(db, user)
    if not me:
        return {"date": date, "missions": [], "info": "Aucun salarié rattaché à ce compte"}
    date = pmt._iso(date or pmt_planning.now_local().date().isoformat())
    day = db.query(PmtPlanningDay).filter(PmtPlanningDay.id == f"{user.business_id}|{date}").first()
    if not day or day.status == "brouillon":
        return {"date": date, "missions": [], "info": "Planning du jour pas encore publié"}
    employees = _employees(db, user.business_id)
    rows = [m for m in db.query(PmtMission).filter(PmtMission.business_id == user.business_id,
                                                   PmtMission.date == date).all()
            if me in ((m.data or {}).get("equipage_ids") or [])]
    return {"date": date, "missions": sorted((_mission_dict(m, employees) for m in rows),
                                             key=lambda x: x.get("heure_prevue") or "")}


@router.post("/missions/{mission_id}/action")
async def mission_action(mission_id: str, payload: dict, db: Session = Depends(get_db),
                         user: CurrentUser = Depends(get_current_user)):
    """Validation par l'équipage : accepter, départ, arrivée, retour (ou annuler pour le gérant)."""
    m = _get(db, mission_id, user)
    action = payload.get("action")
    day = _day(db, m.business_id, m.date)
    if day.status == "valide":
        raise HTTPException(status_code=409, detail="Journée validée : plus de modification possible")
    if not user.is_manager:
        if day.status != "publie":
            raise HTTPException(status_code=403, detail="Planning pas encore publié")
        if _my_employee_id(db, user) not in ((m.data or {}).get("equipage_ids") or []):
            raise HTTPException(status_code=403, detail="Vous n'êtes pas sur cette mission")
        if action == "annuler":
            raise HTTPException(status_code=403, detail="Seul le gérant peut annuler une mission")
    km = payload.get("km_compteur")
    try:
        km = float(km) if km not in (None, "") else None
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Compteur kilométrique invalide")
    try:
        updated = pmt_planning.apply_action(_as_plain(m), action, user.email, km_compteur=km)
    except pmt_planning.TransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    m.status, m.events = updated["status"], updated["events"]

    warnings = []
    if action == "depart":
        employees = _employees(db, m.business_id)
        warnings = pmt_planning.conflicts([_as_plain(m)], employees).get(m.id, [])
    if action == "retour":
        _link_voucher(db, m, user)
    db.commit()
    out = _mission_dict(m, _employees(db, m.business_id))
    out["avertissements"] = warnings
    return out


def _link_voucher(db: Session, m: PmtMission, user: CurrentUser) -> None:
    """Retour validé : le dossier de facturation est créé (ou complété) avec l'heure réelle et l'équipage."""
    from backend.routers.pmt import _refresh, resolve_crew
    plain = _as_plain(m)
    transport = pmt_planning.transport_from_mission(plain)
    v = db.query(PmtVoucher).filter(PmtVoucher.id == m.voucher_id).first() if m.voucher_id else None
    if v is None:
        nom = (m.data or {}).get("patient_nom", "")
        v = PmtVoucher(id=str(uuid.uuid4()), business_id=m.business_id, extraction_provider="planning",
                       data={"beneficiaire": {"nom": nom}, "mode": (m.data or {}).get("mode"),
                             "trajet": {"depart_libelle": (m.data or {}).get("adresse_depart", ""),
                                        "arrivee_libelle": (m.data or {}).get("adresse_arrivee", ""),
                                        "aller_retour": (m.data or {}).get("type_trajet") == "aller_retour"}},
                       transport=transport, transporteur={})
        db.add(v)
        m.voucher_id = v.id
    else:
        v.transport = {**(v.transport or {}), **{k: val for k, val in transport.items() if val}}
    resolve_crew(db, v)
    _refresh(v)


@router.post("/missions/{mission_id}/dossier")
async def attach_voucher(mission_id: str, payload: dict, db: Session = Depends(get_db),
                         user: CurrentUser = Depends(get_current_user)):
    """Rattacher la mission à un dossier existant (bon déjà photographié)."""
    m = _get(db, mission_id, user)
    v = db.query(PmtVoucher).filter(PmtVoucher.id == payload.get("voucher_id")).first()
    if not v or v.business_id != m.business_id:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    m.voucher_id = v.id
    if m.status == "terminee":
        _link_voucher(db, m, user)
    db.commit()
    return _mission_dict(m, _employees(db, m.business_id))
