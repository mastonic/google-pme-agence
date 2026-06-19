import React, { useEffect, useRef, useState } from 'react'
import QRCode from 'qrcode'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { Check, X, Printer, ArrowLeft, Archive, Clock, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import { updateStepStatut, archiveParapheur, deleteParapheur } from '../store.js'

const STATUT_ICON = {
  en_attente: <span style={{ color: 'var(--cs-muted)' }}>○</span>,
  en_cours: <Clock size={16} color="var(--cs-or)" />,
  valide: <CheckCircle2 size={16} color="var(--cs-vert)" />,
  refuse: <XCircle size={16} color="var(--cs-rouge)" />,
}

function StepModal({ step, onConfirm, onClose }) {
  const [comment, setComment] = useState('')
  const [auteur, setAuteur] = useState(step.nom || '')
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={e => e.stopPropagation()}>
        <div className="modal-handle" />
        <div className="modal-title">Mettre à jour l'étape {step.ordre + 1}</div>
        <div style={{ fontSize: 14, color: 'var(--cs-muted)', marginBottom: 16 }}>
          {step.role}{step.nom ? ` — ${step.nom}` : ''}
        </div>
        <div className="form-group">
          <label className="form-label">Nom du signataire</label>
          <input className="form-input" value={auteur} onChange={e => setAuteur(e.target.value)} placeholder={step.role} />
        </div>
        <div className="form-group">
          <label className="form-label">Commentaire (optionnel)</label>
          <textarea className="form-textarea" value={comment} onChange={e => setComment(e.target.value)}
            placeholder="Observations, réserves, motif de refus…" />
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
          <button className="btn btn-danger" style={{ flex: 1 }} onClick={() => onConfirm('refuse', comment, auteur)}>
            <X size={16} /> Refuser
          </button>
          <button className="btn btn-success" style={{ flex: 1 }} onClick={() => onConfirm('valide', comment, auteur)}>
            <Check size={16} /> Valider
          </button>
        </div>
        <button className="btn btn-secondary btn-full" style={{ marginTop: 8 }} onClick={onClose}>Annuler</button>
      </div>
    </div>
  )
}

export default function ParapheurDetail({ par: initialPar, onBack, onUpdated }) {
  const [par, setPar] = useState(initialPar)
  const [activeStep, setActiveStep] = useState(null)
  const [showDelete, setShowDelete] = useState(false)
  const canvasRef = useRef(null)

  const qrData = `CAPSUD-PAR:${par.id}:${par.reference}`

  useEffect(() => {
    if (canvasRef.current) {
      QRCode.toCanvas(canvasRef.current, qrData, {
        width: 200,
        margin: 2,
        color: { dark: '#1A5276', light: '#ffffff' }
      })
    }
  }, [par.id])

  function handleStepUpdate(statut, comment, auteur) {
    const updated = updateStepStatut(par.id, activeStep.ordre, statut, comment, auteur)
    if (updated) { setPar({ ...updated }); onUpdated() }
    setActiveStep(null)
  }

  function handleArchive() {
    archiveParapheur(par.id)
    onUpdated()
    onBack()
  }

  function handleDelete() {
    deleteParapheur(par.id)
    onUpdated()
    onBack()
  }

  function handlePrint() {
    window.print()
  }

  const currentStepIdx = par.circuit.findIndex(s => s.statut === 'en_cours')
  const progress = Math.round((par.circuit.filter(s => s.statut === 'valide').length / par.circuit.length) * 100)

  return (
    <div className="fade-in">
      {activeStep && (
        <StepModal
          step={activeStep}
          onConfirm={handleStepUpdate}
          onClose={() => setActiveStep(null)}
        />
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button className="btn btn-secondary btn-sm" onClick={onBack}>
          <ArrowLeft size={14} /> Retour
        </button>
        <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--cs-muted)', letterSpacing: .5 }}>{par.reference}</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          <button className="btn btn-secondary btn-sm" onClick={handlePrint} title="Imprimer la fiche QR">
            <Printer size={14} />
          </button>
          {par.statut === 'valide' && (
            <button className="btn btn-sm" style={{ background: '#F2F3F4', color: 'var(--cs-muted)' }} onClick={handleArchive}>
              <Archive size={14} />
            </button>
          )}
        </div>
      </div>

      {/* En-tête dossier */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 11, color: 'var(--cs-muted)', marginBottom: 4 }}>{par.service}</div>
            <div style={{ fontSize: 17, fontWeight: 700, lineHeight: 1.3 }}>{par.objet}</div>
            {par.priorite === 'urgent' && (
              <span className="badge-statut badge-urgent" style={{ marginTop: 8, display: 'inline-flex' }}>⚡ Urgent</span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, marginTop: 12, flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 10, color: 'var(--cs-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Créé le</div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>{format(new Date(par.createdAt), 'dd MMM yyyy', { locale: fr })}</div>
          </div>
          {par.deadline && (
            <div>
              <div style={{ fontSize: 10, color: 'var(--cs-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Échéance</div>
              <div style={{ fontSize: 13, fontWeight: 500, color: new Date(par.deadline) < new Date() && par.statut === 'en_cours' ? 'var(--cs-rouge)' : 'inherit' }}>
                {format(new Date(par.deadline), 'dd MMM yyyy', { locale: fr })}
                {new Date(par.deadline) < new Date() && par.statut === 'en_cours' && ' ⚠'}
              </div>
            </div>
          )}
          <div>
            <div style={{ fontSize: 10, color: 'var(--cs-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Avancement</div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>{progress}%</div>
          </div>
        </div>

        <div className="progress-bar" style={{ marginTop: 10 }}>
          <div className={`progress-fill ${progress === 100 ? 'ok' : progress >= 50 ? 'warn' : ''}`} style={{ width: `${progress}%` }} />
        </div>

        {par.notes && (
          <div style={{ marginTop: 12, padding: '8px 10px', background: 'var(--cs-gris)', borderRadius: 6, fontSize: 13 }}>
            📝 {par.notes}
          </div>
        )}
      </div>

      {/* QR Code */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">QR Code — Suivi mobile</span>
        </div>
        <div className="qr-box">
          <div style={{ textAlign: 'center', marginBottom: 4 }}>
            <div style={{ fontSize: 11, color: 'var(--cs-muted)', marginBottom: 2 }}>CAP SUD — Parapheur numérique</div>
          </div>
          <canvas ref={canvasRef} />
          <div className="qr-ref">{par.reference}</div>
          <div style={{ fontSize: 11, color: 'var(--cs-muted)', textAlign: 'center' }}>
            Scanner pour accéder directement à ce dossier
          </div>
        </div>
        <button className="btn btn-primary btn-full" style={{ marginTop: 12 }} onClick={handlePrint}>
          <Printer size={16} /> Imprimer la fiche + QR Code
        </button>
      </div>

      {/* Circuit */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Circuit de validation</span>
          <span style={{ fontSize: 12, color: 'var(--cs-muted)' }}>
            {par.circuit.filter(s => s.statut === 'valide').length}/{par.circuit.length}
          </span>
        </div>
        <div className="circuit">
          {par.circuit.map((step, i) => (
            <div key={i} className="circuit-step">
              <div className={`step-dot ${step.statut}`}>{STATUT_ICON[step.statut] || i + 1}</div>
              <div className="step-body">
                <div className="step-role">{step.role}</div>
                {step.nom && <div className="step-nom">{step.nom}</div>}
                {step.date && (
                  <div className="step-date">
                    {format(new Date(step.date), 'dd MMM yyyy à HH:mm', { locale: fr })}
                  </div>
                )}
                {step.commentaire && <div className="step-comment">{step.commentaire}</div>}
                {step.statut === 'en_cours' && par.statut !== 'refuse' && (
                  <button className="btn btn-primary btn-sm" style={{ marginTop: 8 }} onClick={() => setActiveStep(step)}>
                    Mettre à jour
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Historique */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: 12 }}>Historique</div>
        {par.history.map((h, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8, fontSize: 13 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--cs-bleu)', flexShrink: 0, marginTop: 5 }} />
            <div style={{ flex: 1 }}>
              <span style={{ fontWeight: 500 }}>{h.action}</span>
              <span style={{ color: 'var(--cs-muted)', marginLeft: 8, fontSize: 11 }}>
                {format(new Date(h.date), 'dd/MM/yyyy HH:mm', { locale: fr })}
                {h.auteur && ` — ${h.auteur}`}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      {par.statut !== 'archive' && (
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          {!showDelete ? (
            <button className="btn btn-secondary btn-full" onClick={() => setShowDelete(true)}>
              Supprimer ce parapheur
            </button>
          ) : (
            <>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowDelete(false)}>Annuler</button>
              <button className="btn btn-danger" style={{ flex: 1 }} onClick={handleDelete}>Confirmer suppression</button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
