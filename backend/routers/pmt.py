"""API transport sanitaire : bons de transport (PMT) des clients ambulanciers.

Flux : scan → lecture → contrôles → dossier → export vers le logiciel de
facturation du client (CSV, Excel, JSON ou ZIP de dossiers complets).
"""

import asyncio
import datetime
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.models.database import BASE_DIR, PmtExportProfile, PmtVoucher, get_db
from backend.services import pmt, pmt_export

router = APIRouter(prefix="/pmt", tags=["transport-sanitaire"])

STATUSES = ("draft", "validated", "exported", "billed")


def _scan_dir() -> str:
    return os.environ.get("PMT_SCAN_DIR") or os.path.join(BASE_DIR, "data", "pmt_scans")


def _keep_scans() -> bool:
    return os.environ.get("PMT_KEEP_SCANS", "1") != "0"


def _save_scan(voucher_id: str, content: bytes, mime: str) -> str:
    folder = _scan_dir()
    os.makedirs(folder, mode=0o700, exist_ok=True)
    path = os.path.join(folder, voucher_id + pmt_export.SCAN_EXT.get(mime, ".bin"))
    with open(path, "wb") as f:
        f.write(content)
    os.chmod(path, 0o600)
    return path


def _read_scan(v: dict):
    path = v.get("scan_path")
    if not path or not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        return f.read()


def _delete_scan(v: PmtVoucher) -> None:
    if v.scan_path and os.path.isfile(v.scan_path):
        os.remove(v.scan_path)
    v.scan_path = None


def _export_input(v: PmtVoucher) -> dict:
    return {
        "id": v.id, "data": v.data, "transport": v.transport, "transporteur": v.transporteur,
        "scan_path": v.scan_path, "scan_mime": v.scan_mime,
    }


def _voucher_dict(v: PmtVoucher) -> dict:
    analysis = pmt.analyze(v.data, v.transport)
    return {
        "id": v.id,
        "business_id": v.business_id,
        "source_filename": v.source_filename,
        "extraction_provider": v.extraction_provider,
        "transporteur": pmt.Transporteur.model_validate(v.transporteur or {}).model_dump(),
        "status": v.status,
        "has_scan": bool(v.scan_path and os.path.isfile(v.scan_path)),
        "exportable": pmt_export.is_exportable(analysis["readiness"], v.status or "draft"),
        "exported_at": v.exported_at.isoformat() if v.exported_at else None,
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


# ── Bons de transport ─────────────────────────────────────────────────────────

@router.post("/extract")
async def extract_voucher(
    file: UploadFile = File(...),
    business_id: str = Form(None),
    db: Session = Depends(get_db),
):
    """Scan PDF / photo d'une PMT → dossier avec données extraites et contrôles."""
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

    v = PmtVoucher(
        id=str(uuid.uuid4()),
        business_id=business_id or None,
        source_filename=file.filename,
        extraction_provider=result["provider"],
        data=result["data"].model_dump(),
        transport={},
    )
    if _keep_scans():
        v.scan_path = _save_scan(v.id, content, mime)
        v.scan_mime = mime
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


def _query(db: Session, business_id: str = None):
    q = db.query(PmtVoucher)
    if business_id:
        q = q.filter(PmtVoucher.business_id == business_id)
    return q


@router.get("/vouchers")
async def list_vouchers(business_id: str = None, readiness: str = None, limit: int = 200, db: Session = Depends(get_db)):
    q = _query(db, business_id)
    if readiness:
        q = q.filter(PmtVoucher.readiness == readiness)
    rows = q.order_by(PmtVoucher.created_at.desc()).limit(max(1, min(limit, 1000))).all()
    return [_voucher_dict(v) for v in rows]


@router.get("/stats")
async def voucher_stats(business_id: str = None, db: Session = Depends(get_db)):
    """Taux de dossiers prêts à envoyer (objectif 80-90 %) et principales causes d'anomalie."""
    rows = _query(db, business_id).all()
    return pmt_export.stats([
        {"readiness": v.readiness, "status": v.status, "checks": v.checks, "exported_at": v.exported_at}
        for v in rows
    ])


@router.get("/vouchers/export.csv")
async def export_vouchers_csv(business_id: str = None, db: Session = Depends(get_db)):
    """Export CSV de tous les bons (format standard)."""
    rows = _query(db, business_id).order_by(PmtVoucher.created_at.asc()).all()
    content, mime, ext = pmt_export.render([_export_input(v) for v in rows], pmt_export.preset("standard"))
    return _file_response(content, mime, ext)


@router.get("/vouchers/{voucher_id}")
async def get_voucher(voucher_id: str, db: Session = Depends(get_db)):
    return _voucher_dict(_get(db, voucher_id))


@router.patch("/vouchers/{voucher_id}")
async def update_voucher(voucher_id: str, payload: dict, db: Session = Depends(get_db)):
    """Corrections de l'utilisateur, détails de la course, cadre transporteur, statut."""
    v = _get(db, voucher_id)
    edited = False
    if "data" in payload and payload["data"] != v.data:
        v.data = payload["data"]
        edited = True
    if "transport" in payload and payload["transport"] != v.transport:
        v.transport = payload["transport"]
        edited = True
    if "transporteur" in payload:
        v.transporteur = pmt.Transporteur.model_validate(payload["transporteur"] or {}).model_dump()
    if "business_id" in payload:
        v.business_id = payload["business_id"] or None
    _refresh(v)
    # Un dossier modifié après export doit être revérifié puis réexporté.
    if edited and v.status in ("exported", "billed"):
        v.status = "draft"
    if "status" in payload:
        status = payload["status"]
        if status not in STATUSES:
            raise HTTPException(status_code=400, detail="Statut inconnu")
        if status != "draft" and v.readiness == "bloquant":
            raise HTTPException(status_code=409, detail="Des anomalies bloquantes restent à corriger")
        v.status = status
    db.commit()
    return _voucher_dict(v)


@router.delete("/vouchers/{voucher_id}")
async def delete_voucher(voucher_id: str, db: Session = Depends(get_db)):
    """Suppression définitive du dossier et de son scan (droit à l'effacement)."""
    v = _get(db, voucher_id)
    _delete_scan(v)
    db.delete(v)
    db.commit()
    return {"deleted": voucher_id}


@router.get("/vouchers/{voucher_id}/fiche", response_class=HTMLResponse)
async def voucher_fiche(voucher_id: str, db: Session = Depends(get_db)):
    return HTMLResponse(pmt.render_fiche_html(_export_input(_get(db, voucher_id))))


@router.get("/vouchers/{voucher_id}/scan")
async def voucher_scan(voucher_id: str, db: Session = Depends(get_db)):
    v = _get(db, voucher_id)
    content = _read_scan(_export_input(v))
    if content is None:
        raise HTTPException(status_code=404, detail="Scan non conservé pour ce dossier")
    return Response(content=content, media_type=v.scan_mime or "application/octet-stream",
                    headers={"Content-Disposition": "inline", "Cache-Control": "no-store"})


@router.post("/scans/purge")
async def purge_scans(days: int = 90, db: Session = Depends(get_db)):
    """Supprime les scans des dossiers exportés depuis plus de `days` jours (les données restent)."""
    limit = datetime.datetime.utcnow() - datetime.timedelta(days=max(0, days))
    rows = db.query(PmtVoucher).filter(PmtVoucher.exported_at != None, PmtVoucher.exported_at < limit).all()  # noqa: E711
    purged = 0
    for v in rows:
        if v.scan_path:
            _delete_scan(v)
            purged += 1
    db.commit()
    return {"purged": purged}


# ── Exports vers le logiciel de facturation ───────────────────────────────────

def _file_response(content: bytes, mime: str, ext: str, count: int = None) -> Response:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    headers = {
        "Content-Disposition": f'attachment; filename="transports-{stamp}.{ext}"',
        "Cache-Control": "no-store",
    }
    if count is not None:
        headers["X-Export-Count"] = str(count)
    return Response(content=content, media_type=mime, headers=headers)


def _profile_from_db(db: Session, profile_id: int) -> pmt_export.ExportProfile:
    row = db.query(PmtExportProfile).filter(PmtExportProfile.id == profile_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Profil d'export introuvable")
    return pmt_export.ExportProfile.model_validate({**row.config, "name": row.name})


@router.get("/export/options")
async def export_options():
    """Champs exportables, formats prédéfinis et options de mise en forme."""
    return {
        "fields": pmt_export.field_catalog(),
        "presets": pmt_export.preset_catalog(),
        **pmt_export.options_catalog(),
    }


@router.post("/export")
async def export_vouchers(payload: dict, db: Session = Depends(get_db)):
    """Génère le fichier à importer dans le logiciel de facturation.

    payload : {preset | profile_id | profile, business_id, scope, ids, mark_exported}
    scope : a_exporter (défaut : exportables pas encore exportés) | exportables | tous
    """
    try:
        if payload.get("profile"):
            profile = pmt_export.ExportProfile.model_validate(payload["profile"])
        elif payload.get("profile_id"):
            profile = _profile_from_db(db, int(payload["profile_id"]))
        else:
            profile = pmt_export.preset(payload.get("preset") or "standard")
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    scope = payload.get("scope") or "a_exporter"
    if scope not in ("a_exporter", "exportables", "tous"):
        raise HTTPException(status_code=400, detail="Périmètre inconnu")
    q = _query(db, payload.get("business_id"))
    if payload.get("ids"):
        q = q.filter(PmtVoucher.id.in_(list(payload["ids"])))
    rows = q.order_by(PmtVoucher.created_at.asc()).all()
    if scope != "tous":
        rows = [v for v in rows if pmt_export.is_exportable(v.readiness, v.status or "draft")]
    if scope == "a_exporter":
        rows = [v for v in rows if not v.exported_at]
    if not rows:
        raise HTTPException(status_code=404, detail="Aucun dossier à exporter")

    content, mime, ext = await asyncio.to_thread(
        pmt_export.render, [_export_input(v) for v in rows], profile, _read_scan)

    # Marquer comme exporté évite d'envoyer deux fois le même transport (rejet pour doublon).
    if payload.get("mark_exported", scope == "a_exporter"):
        batch = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        now = datetime.datetime.utcnow()
        for v in rows:
            if v.readiness != "bloquant":
                v.exported_at = now
                v.export_batch = batch
                if v.status in ("draft", "validated"):
                    v.status = "exported"
        db.commit()
    return _file_response(content, mime, ext, count=len(rows))


@router.get("/export/profiles")
async def list_profiles(business_id: str = None, db: Session = Depends(get_db)):
    q = db.query(PmtExportProfile)
    if business_id:
        q = q.filter((PmtExportProfile.business_id == business_id) | (PmtExportProfile.business_id == None))  # noqa: E711
    return [{**r.config, "id": r.id, "business_id": r.business_id, "name": r.name}
            for r in q.order_by(PmtExportProfile.name).all()]


def _validated_config(payload: dict) -> pmt_export.ExportProfile:
    try:
        return pmt_export.ExportProfile.model_validate(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/profiles")
async def create_profile(payload: dict, db: Session = Depends(get_db)):
    profile = _validated_config(payload)
    row = PmtExportProfile(business_id=payload.get("business_id") or None, name=profile.name,
                           config=profile.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id, "business_id": row.business_id, **row.config}


@router.put("/export/profiles/{profile_id}")
async def update_profile(profile_id: int, payload: dict, db: Session = Depends(get_db)):
    row = db.query(PmtExportProfile).filter(PmtExportProfile.id == profile_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Profil d'export introuvable")
    profile = _validated_config(payload)
    row.name = profile.name
    row.config = profile.model_dump()
    if "business_id" in payload:
        row.business_id = payload["business_id"] or None
    db.commit()
    return {"id": row.id, "business_id": row.business_id, **row.config}


@router.delete("/export/profiles/{profile_id}")
async def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    row = db.query(PmtExportProfile).filter(PmtExportProfile.id == profile_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Profil d'export introuvable")
    db.delete(row)
    db.commit()
    return {"deleted": profile_id}
