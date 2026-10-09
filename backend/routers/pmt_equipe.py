"""API équipe : registre des salariés, échéances des documents, accès employés."""

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import PmtEmployee, PmtUser, PmtVoucher, get_db
from backend.routers.pmt_auth import get_current_user, require_manager
from backend.services import pmt_auth, pmt_equipe
from backend.services.pmt_auth import CurrentUser

router = APIRouter(prefix="/pmt/equipe", tags=["transport-sanitaire-equipe"],
                   dependencies=[Depends(get_current_user)])


def _dict(e: PmtEmployee, full: bool = True) -> dict:
    data = pmt_equipe.normalize(e.data)
    base = {"id": e.id, "business_id": e.business_id, "nom": data.nom, "prenom": data.prenom,
            "qualification": data.qualification, "actif": data.actif}
    if not full:
        return base   # vue employé : de quoi choisir un coéquipier, sans les données RH
    return {**base, **data.model_dump(), "user_id": e.user_id,
            "conformite": pmt_equipe.compliance(data), "a_un_acces": e.user_id is not None}


def _scope(db: Session, user: CurrentUser, business_id):
    q = db.query(PmtEmployee)
    scope = user.scope(business_id)
    if scope or not user.is_admin:
        q = q.filter(PmtEmployee.business_id == scope)
    return q


def _get(db: Session, employee_id: str, user: CurrentUser) -> PmtEmployee:
    e = db.query(PmtEmployee).filter(PmtEmployee.id == employee_id).first()
    if not e or not user.can_access(e.business_id):
        raise HTTPException(status_code=404, detail="Salarié introuvable")
    return e


def _refresh_open_vouchers(db: Session, employee: PmtEmployee) -> int:
    """Documents mis à jour : les dossiers non exportés où il figure sont recontrôlés."""
    from backend.routers.pmt import _refresh, resolve_crew
    count = 0
    for v in db.query(PmtVoucher).filter(PmtVoucher.business_id == employee.business_id,
                                         PmtVoucher.exported_at == None).all():  # noqa: E711
        if employee.id in ((v.transport or {}).get("equipage_ids") or []):
            resolve_crew(db, v)
            _refresh(v)
            count += 1
    return count


@router.get("")
async def list_employees(business_id: str = None, db: Session = Depends(get_db),
                         user: CurrentUser = Depends(get_current_user)):
    rows = _scope(db, user, business_id).all()
    out = [_dict(e, full=user.is_manager) for e in rows]
    return sorted(out, key=lambda x: (not x["actif"], x["nom"], x["prenom"]))


@router.get("/alertes")
async def alerts(business_id: str = None, db: Session = Depends(get_db),
                 user: CurrentUser = Depends(require_manager)):
    """Échéances : documents expirés ou expirant dans les 60 jours."""
    rows = [_dict(e) for e in _scope(db, user, business_id).all()]
    active = [r for r in rows if r["actif"]]
    return {
        "salaries_actifs": len(active),
        "non_conformes": sum(1 for r in active if r["conformite"]["status"] == "non_conforme"),
        "a_renouveler": sum(1 for r in active if r["conformite"]["status"] == "bientot"),
        "details": [{"id": r["id"], "nom": f"{r['prenom']} {r['nom']}".strip(), **r["conformite"]}
                    for r in active if r["conformite"]["status"] != "ok"],
    }


@router.post("")
async def create_employee(payload: dict, db: Session = Depends(get_db),
                          user: CurrentUser = Depends(require_manager)):
    business_id = user.scope(payload.get("business_id") or None)
    if not business_id:
        raise HTTPException(status_code=400, detail="Choisir l'entreprise du salarié")
    data = pmt_equipe.normalize(payload)
    if not data.nom:
        raise HTTPException(status_code=400, detail="Nom obligatoire")
    if not data.afgsu2_fin and payload.get("afgsu2_obtention"):
        data.afgsu2_fin = pmt_equipe.afgsu_end_from_obtention(payload["afgsu2_obtention"])
    e = PmtEmployee(id=str(uuid.uuid4()), business_id=business_id, data=data.model_dump())
    db.add(e)
    db.commit()
    return _dict(e)


@router.put("/{employee_id}")
async def update_employee(employee_id: str, payload: dict, db: Session = Depends(get_db),
                          user: CurrentUser = Depends(require_manager)):
    e = _get(db, employee_id, user)
    data = pmt_equipe.normalize({**(e.data or {}), **payload})
    if not data.afgsu2_fin and payload.get("afgsu2_obtention"):
        data.afgsu2_fin = pmt_equipe.afgsu_end_from_obtention(payload["afgsu2_obtention"])
    e.data = data.model_dump()
    e.updated_at = datetime.datetime.utcnow()
    refreshed = _refresh_open_vouchers(db, e)
    if not data.actif and e.user_id:
        # Salarié parti : son accès est coupé.
        u = db.query(PmtUser).filter(PmtUser.id == e.user_id).first()
        if u:
            u.active = False
            u.token_version = (u.token_version or 1) + 1
    db.commit()
    return {**_dict(e), "dossiers_recontroles": refreshed}


@router.delete("/{employee_id}")
async def delete_employee(employee_id: str, db: Session = Depends(get_db),
                          user: CurrentUser = Depends(require_manager)):
    e = _get(db, employee_id, user)
    if e.user_id:
        u = db.query(PmtUser).filter(PmtUser.id == e.user_id).first()
        if u:
            db.delete(u)
    db.delete(e)
    db.commit()
    return {"deleted": employee_id}


@router.post("/{employee_id}/acces")
async def create_access(employee_id: str, payload: dict, db: Session = Depends(get_db),
                        user: CurrentUser = Depends(require_manager)):
    """Compte « employé » : photographier les bons et compléter les courses, rien d'autre."""
    e = _get(db, employee_id, user)
    if e.user_id:
        raise HTTPException(status_code=409, detail="Ce salarié a déjà un accès")
    email = (payload.get("email") or "").strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Adresse e-mail invalide")
    problem = pmt_auth.password_problem(payload.get("password") or "")
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    if db.query(PmtUser).filter(PmtUser.email == email).first():
        raise HTTPException(status_code=409, detail="Ce compte existe déjà")
    u = PmtUser(email=email, password_hash=pmt_auth.hash_password(payload["password"]), role="employe",
                business_id=e.business_id)
    db.add(u)
    db.flush()
    e.user_id = u.id
    db.commit()
    return _dict(e)
