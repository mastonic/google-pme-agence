"""API rejets CPAM : import des retours, suivi des rejets jusqu'au paiement."""

import asyncio
import datetime
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.models.database import PmtReturn, PmtVoucher, get_db
from backend.routers.pmt_auth import get_current_user
from backend.services import pmt_rejets
from backend.services.pmt_auth import CurrentUser

router = APIRouter(prefix="/pmt/rejets", tags=["transport-sanitaire-rejets"],
                   dependencies=[Depends(get_current_user)])

MAX_IMPORT_BYTES = 15 * 1024 * 1024
DOCUMENT_MIME = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/heic"}


def _row_dict(r: PmtReturn) -> dict:
    motif = next((m for m in pmt_rejets.catalogue() if m["categorie"] == r.categorie), None) or {}
    return {
        "id": r.id, "business_id": r.business_id, "voucher_id": r.voucher_id, "match_score": r.match_score,
        "source": r.source, "type_retour": r.type_retour, "part": r.part,
        "numero_facture": r.numero_facture, "date_facturation": r.date_facturation, "date_soins": r.date_soins,
        "nir": r.nir, "nom_patient": r.nom_patient, "organisme": r.organisme,
        "montant_facture": r.montant_facture, "montant_paye": r.montant_paye,
        "montant_en_jeu": pmt_rejets.amount_at_stake({"type_retour": r.type_retour,
                                                       "montant_facture": r.montant_facture,
                                                       "montant_paye": r.montant_paye}),
        "code_rejet": r.code_rejet, "libelle_rejet": r.libelle_rejet,
        "categorie": r.categorie, "motif_label": motif.get("label", "Paiement" if r.type_retour == "paiement" else ""),
        "cause": motif.get("cause", ""), "action": motif.get("action", ""), "recuperable": motif.get("recuperable"),
        "diagnostic": r.diagnostic, "diagnostic_label": pmt_rejets.DIAGNOSIS_LABELS.get(r.diagnostic or "", ""),
        "status": r.status, "status_label": pmt_rejets.STATUSES.get(r.status, r.status), "note": r.note,
        "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _vouchers(db: Session, business_id):
    q = db.query(PmtVoucher)
    if business_id:
        q = q.filter(PmtVoucher.business_id == business_id)
    return q.all()


def _parse_upload(content: bytes, filename: str, mime: str) -> tuple[list, str, dict, str]:
    """Retourne (lignes, source, rapport, fournisseur)."""
    name = (filename or "").lower()
    if mime in DOCUMENT_MIME or name.endswith((".pdf", ".jpg", ".jpeg", ".png", ".webp", ".heic")):
        if mime not in DOCUMENT_MIME:
            mime = "application/pdf" if name.endswith(".pdf") else "image/jpeg"
        result = pmt_rejets.read_document(content, mime)
        return result["data"], "document", {}, result["provider"]
    text = pmt_rejets._decode(content) if content[:2] != b"PK" else ""
    if text and pmt_rejets.looks_like_b2r(text):
        return pmt_rejets.parse_b2r(text), "b2r", {}, ""
    lines, report = pmt_rejets.parse_table(content, filename)
    return lines, "tableur", report, ""


def _ingest(db: Session, lines: list, business_id, source: str, user: CurrentUser) -> dict:
    vouchers = _vouchers(db, business_id)
    by_id = {v.id: v for v in vouchers}
    candidates = [{"id": v.id, "data": v.data, "transport": v.transport} for v in vouchers]
    batch = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    created = duplicates = matched = payments = recovered = 0
    for line in lines:
        key = pmt_rejets.line_key(business_id, line)
        if db.query(PmtReturn).filter(PmtReturn.line_key == key).first():
            duplicates += 1
            continue
        best, score = pmt_rejets.best_match(line, candidates)
        voucher = by_id.get(best["id"]) if best else None
        motif = pmt_rejets.classify(line)
        row = PmtReturn(
            id=str(uuid.uuid4()), line_key=key, business_id=business_id,
            voucher_id=voucher.id if voucher else None, match_score=score, import_batch=batch, source=source,
            **line.model_dump(exclude={"nir_cle"}),
            categorie=motif["categorie"],
            diagnostic=None if line.type_retour == "paiement" else pmt_rejets.diagnosis(
                motif, voucher.checks if voucher else None),
            status="recupere" if line.type_retour == "paiement" else "a_traiter",
        )
        if voucher:
            matched += 1
        if line.type_retour == "paiement":
            payments += 1
            if voucher:
                # Paiement reçu : le dossier est facturé et réglé, ses rejets ouverts sont récupérés.
                voucher.status = "billed"
                for open_row in db.query(PmtReturn).filter(
                        PmtReturn.voucher_id == voucher.id,
                        PmtReturn.type_retour != "paiement",
                        PmtReturn.status.in_(pmt_rejets.OPEN_STATUSES)).all():
                    open_row.status = "recupere"
                    open_row.resolved_at = datetime.datetime.utcnow()
                    recovered += 1
        db.add(row)
        db.flush()
        created += 1
    db.commit()
    return {"lignes_lues": len(lines), "importees": created, "doublons_ignores": duplicates,
            "rattachees": matched, "paiements": payments, "rejets_recuperes": recovered, "lot": batch}


@router.post("/import")
async def import_returns(
    file: UploadFile = File(...),
    business_id: str = Form(None),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Fichier B2-retour, export tableur des rejets/paiements, ou relevé PDF/photo."""
    business_id = user.scope(business_id or None)
    if user.is_admin and not business_id:
        raise HTTPException(status_code=400, detail="Choisir le client ambulancier concerné par ce retour")
    content = await file.read()
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=400, detail="Fichier trop lourd (15 Mo maximum)")
    try:
        lines, source, report, provider = await asyncio.to_thread(
            _parse_upload, content, file.filename or "", (file.content_type or "").lower())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    if not lines:
        raise HTTPException(status_code=400, detail="Aucune ligne de retour trouvée dans ce fichier")
    summary = _ingest(db, lines, business_id, source, user)
    return {**summary, "source": source, "colonnes_reconnues": report.get("colonnes", {}),
            "colonnes_ignorees": report.get("ignorees", []), "fournisseur": provider}


@router.post("/manuel")
async def add_manual(payload: dict, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    """Saisie d'un rejet à la main (lu sur un courrier ou un écran)."""
    business_id = user.scope(payload.get("business_id") or None)
    if user.is_admin and not business_id:
        raise HTTPException(status_code=400, detail="Choisir le client ambulancier")
    line = pmt_rejets.normalize_line(payload)
    return _ingest(db, [line], business_id, "manuel", user)


def _query(db: Session, user: CurrentUser, business_id):
    q = db.query(PmtReturn)
    scope = user.scope(business_id)
    if scope or not user.is_admin:
        q = q.filter(PmtReturn.business_id == scope)
    return q


@router.get("")
async def list_returns(business_id: str = None, status: str = None, categorie: str = None,
                       type_retour: str = None, voucher_id: str = None, limit: int = 300,
                       db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    q = _query(db, user, business_id)
    if status == "ouverts":
        q = q.filter(PmtReturn.status.in_(pmt_rejets.OPEN_STATUSES))
    elif status:
        q = q.filter(PmtReturn.status == status)
    if categorie:
        q = q.filter(PmtReturn.categorie == categorie)
    if type_retour:
        q = q.filter(PmtReturn.type_retour == type_retour)
    elif not voucher_id:
        q = q.filter(PmtReturn.type_retour != "paiement")
    if voucher_id:
        q = q.filter(PmtReturn.voucher_id == voucher_id)
    rows = q.order_by(PmtReturn.created_at.desc()).limit(max(1, min(limit, 2000))).all()
    return [_row_dict(r) for r in rows]


@router.get("/stats")
async def return_stats(business_id: str = None, db: Session = Depends(get_db),
                       user: CurrentUser = Depends(get_current_user)):
    return pmt_rejets.stats([_row_dict(r) for r in _query(db, user, business_id).all()])


@router.get("/catalogue")
async def motif_catalogue():
    return {"motifs": pmt_rejets.catalogue(), "statuts": pmt_rejets.STATUSES,
            "diagnostics": pmt_rejets.DIAGNOSIS_LABELS}


def _get(db: Session, return_id: str, user: CurrentUser) -> PmtReturn:
    r = db.query(PmtReturn).filter(PmtReturn.id == return_id).first()
    if not r or not user.can_access(r.business_id):
        raise HTTPException(status_code=404, detail="Retour introuvable")
    return r


@router.patch("/{return_id}")
async def update_return(return_id: str, payload: dict, db: Session = Depends(get_db),
                        user: CurrentUser = Depends(get_current_user)):
    r = _get(db, return_id, user)
    if "status" in payload:
        if payload["status"] not in pmt_rejets.STATUSES:
            raise HTTPException(status_code=400, detail="Statut inconnu")
        r.status = payload["status"]
        r.resolved_at = datetime.datetime.utcnow() if r.status in ("recupere", "abandonne") else None
    if "note" in payload:
        r.note = (payload["note"] or "")[:2000]
    if "voucher_id" in payload:
        vid = payload["voucher_id"] or None
        if vid:
            v = db.query(PmtVoucher).filter(PmtVoucher.id == vid).first()
            if not v or v.business_id != r.business_id or not user.can_access(v.business_id):
                raise HTTPException(status_code=404, detail="Dossier introuvable")
            if r.type_retour != "paiement":
                motif = next((m for m in pmt_rejets.catalogue() if m["categorie"] == r.categorie),
                             pmt_rejets.OTHER_MOTIF)
                r.diagnostic = pmt_rejets.diagnosis(motif, v.checks)
        r.voucher_id = vid
        r.match_score = 100 if vid else 0
    db.commit()
    return _row_dict(r)


@router.post("/{return_id}/reopen")
async def reopen_voucher(return_id: str, db: Session = Depends(get_db),
                         user: CurrentUser = Depends(get_current_user)):
    """Rouvre le dossier d'origine pour le corriger puis le réexporter."""
    r = _get(db, return_id, user)
    if not r.voucher_id:
        raise HTTPException(status_code=400, detail="Aucun dossier rattaché à ce rejet")
    v = db.query(PmtVoucher).filter(PmtVoucher.id == r.voucher_id).first()
    if not v or not user.can_access(v.business_id):
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    v.status = "draft"
    v.exported_at = None   # il repartira au prochain export « nouveaux dossiers prêts »
    r.status = "en_correction"
    db.commit()
    return {"voucher_id": v.id, "status": r.status}


@router.delete("/{return_id}")
async def delete_return(return_id: str, db: Session = Depends(get_db),
                        user: CurrentUser = Depends(get_current_user)):
    r = _get(db, return_id, user)
    db.delete(r)
    db.commit()
    return {"deleted": return_id}
