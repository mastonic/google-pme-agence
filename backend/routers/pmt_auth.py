"""Comptes et connexion du module transport sanitaire."""

import datetime
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from backend.models.database import PmtUser, SessionLocal, get_db
from backend.services import pmt_auth
from backend.services.pmt_auth import CurrentUser

router = APIRouter(prefix="/pmt/auth", tags=["transport-sanitaire-auth"])

UNAUTHORIZED = HTTPException(
    status_code=401, detail="Connexion requise", headers={"WWW-Authenticate": "Bearer"})


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UNAUTHORIZED
    claims = pmt_auth.read_token(authorization[7:].strip())
    if not claims:
        raise UNAUTHORIZED
    user = db.query(PmtUser).filter(PmtUser.id == claims.get("sub")).first()
    # token_version : un changement de mot de passe ou une désactivation coupe les sessions ouvertes.
    if not user or not user.active or user.token_version != claims.get("ver"):
        raise UNAUTHORIZED
    return CurrentUser(id=user.id, email=user.email, role=user.role, business_id=user.business_id)


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Réservé à l'administrateur")
    return user


def _user_dict(u: PmtUser) -> dict:
    return {
        "id": u.id, "email": u.email, "role": u.role, "business_id": u.business_id, "active": u.active,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


def _normalize_email(email: str) -> str:
    email = (email or "").strip().lower()
    if "@" not in email or len(email) > 254:
        raise HTTPException(status_code=400, detail="Adresse e-mail invalide")
    return email


@router.post("/login")
async def login(payload: dict, request: Request, db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    key = f"{email}|{request.client.host if request.client else ''}"
    if pmt_auth.throttle.locked(key):
        raise HTTPException(status_code=429, detail="Trop de tentatives : réessayer dans 15 minutes")
    user = db.query(PmtUser).filter(PmtUser.email == email).first()
    if not user or not user.active or not pmt_auth.verify_password(password, user.password_hash):
        pmt_auth.throttle.fail(key)
        raise HTTPException(status_code=401, detail="E-mail ou mot de passe incorrect")
    pmt_auth.throttle.reset(key)
    user.last_login_at = datetime.datetime.utcnow()
    db.commit()
    return {"token": pmt_auth.issue_token(user.id, user.token_version), "user": _user_dict(user),
            "expires_in": pmt_auth.TOKEN_TTL_SECONDS}


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)):
    return user.__dict__


@router.post("/password")
async def change_password(payload: dict, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(PmtUser).filter(PmtUser.id == user.id).first()
    if not pmt_auth.verify_password(payload.get("current_password") or "", row.password_hash):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    problem = pmt_auth.password_problem(payload.get("new_password") or "")
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    row.password_hash = pmt_auth.hash_password(payload["new_password"])
    row.token_version = (row.token_version or 1) + 1
    db.commit()
    return {"token": pmt_auth.issue_token(row.id, row.token_version)}


# ── Gestion des comptes (admin) ───────────────────────────────────────────────

@router.get("/users")
async def list_users(_: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    return [_user_dict(u) for u in db.query(PmtUser).order_by(PmtUser.email).all()]


@router.post("/users")
async def create_user(payload: dict, _: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    email = _normalize_email(payload.get("email"))
    role = payload.get("role") or "client"
    if role not in pmt_auth.ROLES:
        raise HTTPException(status_code=400, detail="Rôle inconnu")
    if role == "client" and not payload.get("business_id"):
        raise HTTPException(status_code=400, detail="Un compte client doit être rattaché à une entreprise")
    problem = pmt_auth.password_problem(payload.get("password") or "")
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    if db.query(PmtUser).filter(PmtUser.email == email).first():
        raise HTTPException(status_code=409, detail="Ce compte existe déjà")
    u = PmtUser(email=email, password_hash=pmt_auth.hash_password(payload["password"]), role=role,
                business_id=payload.get("business_id") if role == "client" else None)
    db.add(u)
    db.commit()
    return _user_dict(u)


@router.patch("/users/{user_id}")
async def update_user(user_id: int, payload: dict, admin: CurrentUser = Depends(require_admin),
                      db: Session = Depends(get_db)):
    u = db.query(PmtUser).filter(PmtUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    if "active" in payload:
        if u.id == admin.id and not payload["active"]:
            raise HTTPException(status_code=400, detail="Impossible de désactiver son propre compte")
        u.active = bool(payload["active"])
        u.token_version = (u.token_version or 1) + 1
    if payload.get("password"):
        problem = pmt_auth.password_problem(payload["password"])
        if problem:
            raise HTTPException(status_code=400, detail=problem)
        u.password_hash = pmt_auth.hash_password(payload["password"])
        u.token_version = (u.token_version or 1) + 1
    if "business_id" in payload and u.role == "client":
        if not payload["business_id"]:
            raise HTTPException(status_code=400, detail="Un compte client doit être rattaché à une entreprise")
        u.business_id = payload["business_id"]
        u.token_version = (u.token_version or 1) + 1
    db.commit()
    return _user_dict(u)


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de supprimer son propre compte")
    u = db.query(PmtUser).filter(PmtUser.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Compte introuvable")
    db.delete(u)
    db.commit()
    return {"deleted": user_id}


def seed_admin_from_env() -> None:
    """Crée le premier administrateur depuis PMT_ADMIN_EMAIL / PMT_ADMIN_PASSWORD s'il n'en existe aucun."""
    email = (os.environ.get("PMT_ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("PMT_ADMIN_PASSWORD") or ""
    db = SessionLocal()
    try:
        if db.query(PmtUser).filter(PmtUser.role == "admin").first():
            return
        if not email or not password:
            print("ℹ️  Module transport : aucun administrateur. Définir PMT_ADMIN_EMAIL et PMT_ADMIN_PASSWORD.")
            return
        problem = pmt_auth.password_problem(password)
        if problem:
            print(f"⚠️  PMT_ADMIN_PASSWORD refusé : {problem}")
            return
        db.add(PmtUser(email=email, password_hash=pmt_auth.hash_password(password), role="admin"))
        db.commit()
        print(f"Module transport : administrateur {email} créé.")
    finally:
        db.close()
