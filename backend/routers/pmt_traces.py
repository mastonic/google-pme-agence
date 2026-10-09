"""API traces de géolocalisation : import des exports de boîtiers et rattachement aux dossiers."""

import asyncio
import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.models.database import PmtTrace, PmtVoucher, get_db
from backend.routers.pmt_auth import get_current_user
from backend.services import pmt, pmt_traces
from backend.services.pmt_auth import CurrentUser

router = APIRouter(prefix="/pmt/traces", tags=["transport-sanitaire-traces"],
                   dependencies=[Depends(get_current_user)])

MAX_IMPORT_BYTES = 30 * 1024 * 1024


def _trace_dict(t: PmtTrace) -> dict:
    return {
        "key": t.id, "business_id": t.business_id, "voucher_id": t.voucher_id, "match_score": t.match_score,
        "vehicule": t.vehicule, "reference": t.reference,
        "start": t.start_at.isoformat() if t.start_at else None,
        "end": t.end_at.isoformat() if t.end_at else None,
        "km": round(t.km or 0, 2), "points": t.points, "trous": t.trous, "km_trous": round(t.km_trous or 0, 2),
        "source": t.source, "source_file": t.source_file, "warnings": t.warnings or [],
    }


def _purge_expired(db: Session) -> int:
    """Résumés de traces effacés après la durée de conservation (3 mois par défaut)."""
    limit = datetime.datetime.utcnow() - datetime.timedelta(days=pmt_traces.retention_days())
    rows = db.query(PmtTrace).filter(PmtTrace.created_at < limit).all()
    for r in rows:
        db.delete(r)
    return len(rows)


def _clear_voucher(db: Session, voucher_id: str) -> None:
    """Retire la trace et ses km d'un dossier."""
    from backend.routers.pmt import _refresh
    v = db.query(PmtVoucher).filter(PmtVoucher.id == voucher_id).first()
    if v:
        transport = dict(v.transport or {})
        transport.pop("trace", None)
        transport["km_geoloc"] = None
        v.transport = transport
        _refresh(v)


def _attach(db: Session, trace: PmtTrace, voucher: PmtVoucher, score: int) -> None:
    from backend.routers.pmt import _refresh
    # La trace quitte son ancien dossier ; le dossier perd son ancienne trace.
    if trace.voucher_id and trace.voucher_id != voucher.id:
        _clear_voucher(db, trace.voucher_id)
    for other in db.query(PmtTrace).filter(PmtTrace.voucher_id == voucher.id, PmtTrace.id != trace.id).all():
        other.voucher_id, other.match_score = None, 0
    trace.voucher_id, trace.match_score = voucher.id, score
    voucher.transport = pmt_traces.apply_to_transport(voucher.transport, _trace_dict(trace))
    edited = voucher.status in ("exported", "billed")
    _refresh(voucher)
    if edited:
        voucher.status = "draft"


def _scope_query(db: Session, model, user: CurrentUser, business_id):
    q = db.query(model)
    scope = user.scope(business_id)
    if scope or not user.is_admin:
        q = q.filter(model.business_id == scope)
    return q


@router.post("/import")
async def import_traces(
    file: UploadFile = File(...),
    business_id: str = Form(None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Export GPX, KML ou CSV d'un boîtier → courses, km, rattachement automatique aux dossiers."""
    business_id = user.scope(business_id or None)
    if user.is_admin and not business_id:
        raise HTTPException(status_code=400, detail="Choisir le client ambulancier concerné par ces traces")
    content = await file.read()
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=400, detail="Fichier trop lourd (30 Mo maximum)")
    try:
        trips = await asyncio.to_thread(pmt_traces.parse_file, content, file.filename or "")
    except Exception as e:  # XML malformé, colonnes inconnues…
        raise HTTPException(status_code=400, detail=f"Fichier de traces illisible : {str(e)[:200]}")
    if not trips:
        raise HTTPException(status_code=400, detail="Aucune course trouvée dans ce fichier")

    purged = _purge_expired(db)
    created = duplicates = 0
    rows = []
    for trip in trips:
        d = trip.as_dict()
        row = db.query(PmtTrace).filter(PmtTrace.id == d["key"]).first()
        if row:
            duplicates += 1
        else:
            row = PmtTrace(id=d["key"], business_id=business_id, vehicule=trip.vehicule, reference=trip.reference,
                           start_at=trip.start, end_at=trip.end, km=trip.km, points=trip.points, trous=trip.trous,
                           km_trous=trip.km_trous, source=trip.source, source_file=file.filename,
                           warnings=trip.warnings)
            db.add(row)
            created += 1
        rows.append(row)
    db.flush()

    # Rattachement : dossiers des jours couverts par l'import, pas encore réglés.
    days = {r.start_at.date().isoformat() for r in rows if r.start_at}
    vouchers = [v for v in db.query(PmtVoucher).filter(PmtVoucher.business_id == business_id).all()
                if pmt.normalize_transport(v.transport).date_transport in days and v.status != "billed"]
    free = [_trace_dict(r) for r in rows if not r.voucher_id]
    candidates = [{"id": v.id, "transport": v.transport} for v in vouchers
                  if not (v.transport or {}).get("trace")]
    matches = pmt_traces.assign(free, candidates)
    by_key = {r.id: r for r in rows}
    by_id = {v.id: v for v in vouchers}
    for vid, (tkey, score) in matches.items():
        _attach(db, by_key[tkey], by_id[vid], score)
    db.commit()

    without_trace = [v for v in vouchers if not (v.transport or {}).get("trace")]
    return {
        "courses_lues": len(trips), "importees": created, "doublons_ignores": duplicates,
        "rattachees": len(matches), "anciennes_supprimees": purged,
        "dossiers_sans_trace": [{"id": v.id, "patient": " ".join(
            x for x in (pmt.normalize_pmt(v.data).beneficiaire.nom, pmt.normalize_pmt(v.data).beneficiaire.prenom) if x),
            "date": pmt.normalize_transport(v.transport).date_transport} for v in without_trace],
        "avec_trous": sum(1 for r in rows if r.trous),
    }


@router.get("")
async def list_traces(business_id: str = None, rattachees: str = None, limit: int = 500,
                      db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    q = _scope_query(db, PmtTrace, user, business_id)
    if rattachees == "non":
        q = q.filter(PmtTrace.voucher_id == None)  # noqa: E711
    elif rattachees == "oui":
        q = q.filter(PmtTrace.voucher_id != None)  # noqa: E711
    rows = q.order_by(PmtTrace.start_at.desc()).limit(max(1, min(limit, 5000))).all()
    return [_trace_dict(r) for r in rows]


def _get(db: Session, key: str, user: CurrentUser) -> PmtTrace:
    t = db.query(PmtTrace).filter(PmtTrace.id == key).first()
    if not t or not user.can_access(t.business_id):
        raise HTTPException(status_code=404, detail="Trace introuvable")
    return t


@router.post("/{key}/attach")
async def attach_trace(key: str, payload: dict, db: Session = Depends(get_db),
                       user: CurrentUser = Depends(get_current_user)):
    """Rattachement manuel quand la correspondance automatique est ambiguë."""
    t = _get(db, key, user)
    v = db.query(PmtVoucher).filter(PmtVoucher.id == payload.get("voucher_id")).first()
    if not v or v.business_id != t.business_id or not user.can_access(v.business_id):
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    _attach(db, t, v, 100)
    db.commit()
    return _trace_dict(t)


@router.post("/{key}/detach")
async def detach_trace(key: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    t = _get(db, key, user)
    if t.voucher_id:
        _clear_voucher(db, t.voucher_id)
    t.voucher_id, t.match_score = None, 0
    db.commit()
    return _trace_dict(t)


@router.delete("/{key}")
async def delete_trace(key: str, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    t = _get(db, key, user)
    db.delete(t)
    db.commit()
    return {"deleted": key}
