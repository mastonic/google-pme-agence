"""API transport sanitaire : bons de transport (PMT) des clients ambulanciers."""

import asyncio
import datetime
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from backend.models.database import PmtVoucher, get_db
from backend.services import pmt

router = APIRouter(prefix="/pmt", tags=["transport-sanitaire"])


def _voucher_dict(v: PmtVoucher) -> dict:
    analysis = pmt.analyze(v.data, v.transport)
    return {
        "id": v.id,
        "business_id": v.business_id,
        "source_filename": v.source_filename,
        "extraction_provider": v.extraction_provider,
        "transporteur": pmt.Transporteur.model_validate(v.transporteur or {}).model_dump(),
        "status": v.status,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
        **analysis,
    }


def _refresh(v: PmtVoucher) -> None:
    analysis = pmt.analyze(v.data, v.transport)
    v.data = analysis["data"]
    v.transport = analysis["transport"]
    v.checks = analysis["checks"]
    v.readiness = analysis["readiness"]
    if v.readiness == "bloquant" and v.status != "draft":
        v.status = "draft"


def _get(db: Session, voucher_id: str) -> PmtVoucher:
    v = db.query(PmtVoucher).filter(PmtVoucher.id == voucher_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Bon de transport introuvable")
    return v


@router.post("/extract")
async def extract_voucher(
    file: UploadFile = File(...),
    business_id: str = Form(None),
    db: Session = Depends(get_db),
):
    """Scan PDF / photo d'une PMT → données extraites + contrôles. Le scan n'est pas conservé."""
    content = await file.read()
    mime = (file.content_type or "").lower()
    if mime == "image/jpg":
        mime = "image/jpeg"
    try:
        result = await asyncio.to_thread(pmt.extract_pmt, content, mime)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        del content

    v = PmtVoucher(
        id=str(uuid.uuid4()),
        business_id=business_id or None,
        source_filename=file.filename,
        extraction_provider=result["provider"],
        data=result["data"].model_dump(),
        transport={},
    )
    _refresh(v)
    db.add(v)
    db.commit()
    return _voucher_dict(v)


@router.post("/vouchers")
async def create_voucher(payload: dict, db: Session = Depends(get_db)):
    """Saisie manuelle (sans lecture automatique)."""
    v = PmtVoucher(
        id=str(uuid.uuid4()),
        business_id=payload.get("business_id") or None,
        extraction_provider="manual",
        data=payload.get("data") or {},
        transport=payload.get("transport") or {},
        transporteur=payload.get("transporteur") or {},
    )
    _refresh(v)
    db.add(v)
    db.commit()
    return _voucher_dict(v)


@router.post("/validate")
async def validate_only(payload: dict):
    """Contrôles sans enregistrement (aperçu pendant la correction)."""
    return pmt.analyze(payload.get("data"), payload.get("transport"))


@router.get("/vouchers")
async def list_vouchers(business_id: str = None, readiness: str = None, limit: int = 200, db: Session = Depends(get_db)):
    q = db.query(PmtVoucher)
    if business_id:
        q = q.filter(PmtVoucher.business_id == business_id)
    if readiness:
        q = q.filter(PmtVoucher.readiness == readiness)
    rows = q.order_by(PmtVoucher.created_at.desc()).limit(max(1, min(limit, 1000))).all()
    return [_voucher_dict(v) for v in rows]


@router.get("/vouchers/export.csv")
async def export_vouchers(business_id: str = None, db: Session = Depends(get_db)):
    q = db.query(PmtVoucher)
    if business_id:
        q = q.filter(PmtVoucher.business_id == business_id)
    rows = q.order_by(PmtVoucher.created_at.asc()).all()
    csv_text = pmt.export_csv([{"id": v.id[:8], "data": v.data, "transport": v.transport} for v in rows])
    stamp = datetime.date.today().isoformat()
    return Response(
        content=csv_text.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="bons-transport-{stamp}.csv"'},
    )


@router.get("/vouchers/{voucher_id}")
async def get_voucher(voucher_id: str, db: Session = Depends(get_db)):
    return _voucher_dict(_get(db, voucher_id))


@router.patch("/vouchers/{voucher_id}")
async def update_voucher(voucher_id: str, payload: dict, db: Session = Depends(get_db)):
    """Corrections de l'utilisateur, détails de la course, cadre transporteur, statut."""
    v = _get(db, voucher_id)
    if "data" in payload:
        v.data = payload["data"]
    if "transport" in payload:
        v.transport = payload["transport"]
    if "transporteur" in payload:
        v.transporteur = pmt.Transporteur.model_validate(payload["transporteur"] or {}).model_dump()
    if "business_id" in payload:
        v.business_id = payload["business_id"] or None
    _refresh(v)
    if "status" in payload:
        status = payload["status"]
        if status not in ("draft", "validated", "billed"):
            raise HTTPException(status_code=400, detail="Statut inconnu")
        if status in ("validated", "billed") and v.readiness == "bloquant":
            raise HTTPException(status_code=409, detail="Des anomalies bloquantes restent à corriger")
        v.status = status
    db.commit()
    return _voucher_dict(v)


@router.delete("/vouchers/{voucher_id}")
async def delete_voucher(voucher_id: str, db: Session = Depends(get_db)):
    """Suppression définitive (droit à l'effacement)."""
    v = _get(db, voucher_id)
    db.delete(v)
    db.commit()
    return {"deleted": voucher_id}


@router.get("/vouchers/{voucher_id}/fiche", response_class=HTMLResponse)
async def voucher_fiche(voucher_id: str, db: Session = Depends(get_db)):
    v = _get(db, voucher_id)
    return HTMLResponse(pmt.render_fiche_html({
        "id": v.id, "data": v.data, "transport": v.transport, "transporteur": v.transporteur,
    }))
