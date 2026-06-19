import React, { useState } from 'react'
import { Plus, Trash2, ChevronDown } from 'lucide-react'
import { createParapheur, CIRCUITS_PREDEFINED, SERVICES } from '../store.js'

export default function NewParapheur({ onCreated, onCancel }) {
  const [step, setStep] = useState(1) // 1: infos, 2: circuit, 3: recap
  const [objet, setObjet] = useState('')
  const [service, setService] = useState('')
  const [priorite, setPriorite] = useState('normal')
  const [deadline, setDeadline] = useState('')
  const [notes, setNotes] = useState('')
  const [circuit, setCircuit] = useState([
    { role: 'Agent instructeur', nom: '' },
    { role: 'Chef de service', nom: '' },
    { role: 'DGS', nom: '' },
  ])
  const [circuitTemplate, setCircuitTemplate] = useState(0)

  function applyTemplate(idx) {
    setCircuitTemplate(idx)
    setCircuit(CIRCUITS_PREDEFINED[idx].steps.map(s => ({ ...s })))
  }

  function addStep() {
    setCircuit([...circuit, { role: '', nom: '' }])
  }

  function removeStep(i) {
    if (circuit.length <= 1) return
    setCircuit(circuit.filter((_, idx) => idx !== i))
  }

  function updateStep(i, field, val) {
    const c = [...circuit]
    c[i] = { ...c[i], [field]: val }
    setCircuit(c)
  }

  function handleCreate() {
    const par = createParapheur({ objet, service, priorite, deadline: deadline || null, circuit, notes })
    onCreated(par)
  }

  const canNext1 = objet.trim() && service.trim()
  const canNext2 = circuit.every(s => s.role.trim())

  if (step === 1) return (
    <div className="fade-in">
      <div className="header-banner">
        <h2>Nouveau parapheur</h2>
        <p>Étape 1 / 3 — Informations</p>
      </div>

      <div className="form-group">
        <label className="form-label">Objet <span>*</span></label>
        <input className="form-input" placeholder="Ex: Marché de voirie 2026 — Avenant n°2" value={objet} onChange={e => setObjet(e.target.value)} />
      </div>

      <div className="form-group">
        <label className="form-label">Service émetteur <span>*</span></label>
        <select className="form-select" value={service} onChange={e => setService(e.target.value)}>
          <option value="">— Sélectionner —</option>
          {SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Priorité</label>
        <div className="chips">
          {[['normal', 'Normal'], ['urgent', '⚡ Urgent']].map(([v, l]) => (
            <span key={v} className={`chip ${priorite === v ? 'selected' : ''}`} onClick={() => setPriorite(v)}>{l}</span>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Date limite de validation</label>
        <input type="date" className="form-input" value={deadline} onChange={e => setDeadline(e.target.value)}
          min={new Date().toISOString().split('T')[0]} />
      </div>

      <div className="form-group">
        <label className="form-label">Notes / Observations</label>
        <textarea className="form-textarea" placeholder="Informations complémentaires…" value={notes} onChange={e => setNotes(e.target.value)} />
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn btn-secondary" style={{ flex: 1 }} onClick={onCancel}>Annuler</button>
        <button className="btn btn-primary" style={{ flex: 2 }} disabled={!canNext1} onClick={() => setStep(2)}>
          Suivant — Circuit
        </button>
      </div>
    </div>
  )

  if (step === 2) return (
    <div className="fade-in">
      <div className="header-banner">
        <h2>Circuit de validation</h2>
        <p>Étape 2 / 3 — Signataires</p>
      </div>

      <div className="form-group">
        <label className="form-label">Modèle de circuit</label>
        <select className="form-select" value={circuitTemplate} onChange={e => applyTemplate(Number(e.target.value))}>
          {CIRCUITS_PREDEFINED.map((c, i) => <option key={i} value={i}>{c.label}</option>)}
        </select>
      </div>

      <hr className="divider" />
      <div className="section-title">Étapes ({circuit.length})</div>

      {circuit.map((step, i) => (
        <div key={i} className="card" style={{ padding: 12, marginBottom: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <div style={{
              width: 24, height: 24, borderRadius: '50%',
              background: 'var(--cs-bleu)', color: '#fff',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 12, fontWeight: 700, flexShrink: 0
            }}>{i + 1}</div>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Étape {i + 1}</span>
            {circuit.length > 1 && (
              <button className="btn btn-sm" style={{ marginLeft: 'auto', background: '#FDEDEC', color: 'var(--cs-rouge)', border: 'none' }}
                onClick={() => removeStep(i)}>
                <Trash2 size={12} />
              </button>
            )}
          </div>
          <div className="form-group" style={{ marginBottom: 8 }}>
            <label className="form-label">Rôle <span>*</span></label>
            <input className="form-input" placeholder="Ex: DGS, Directeur financier…" value={step.role}
              onChange={e => updateStep(i, 'role', e.target.value)} />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Nom (optionnel)</label>
            <input className="form-input" placeholder="Prénom NOM" value={step.nom}
              onChange={e => updateStep(i, 'nom', e.target.value)} />
          </div>
        </div>
      ))}

      <button className="btn btn-secondary btn-full" onClick={addStep} style={{ marginBottom: 16 }}>
        <Plus size={16} /> Ajouter une étape
      </button>

      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setStep(1)}>Retour</button>
        <button className="btn btn-primary" style={{ flex: 2 }} disabled={!canNext2} onClick={() => setStep(3)}>
          Suivant — Récap
        </button>
      </div>
    </div>
  )

  return (
    <div className="fade-in">
      <div className="header-banner">
        <h2>Récapitulatif</h2>
        <p>Étape 3 / 3 — Confirmation</p>
      </div>

      <div className="card">
        <div className="section-title">Dossier</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div><strong>Objet :</strong> {objet}</div>
          <div><strong>Service :</strong> {service}</div>
          <div><strong>Priorité :</strong> {priorite === 'urgent' ? '⚡ Urgent' : 'Normal'}</div>
          {deadline && <div><strong>Échéance :</strong> {new Date(deadline).toLocaleDateString('fr-FR')}</div>}
          {notes && <div><strong>Notes :</strong> {notes}</div>}
        </div>
      </div>

      <div className="card">
        <div className="section-title">Circuit ({circuit.length} étapes)</div>
        <div className="circuit">
          {circuit.map((s, i) => (
            <div key={i} className="circuit-step">
              <div className="step-dot en_cours" style={{ background: 'var(--cs-bleu)', color: '#fff', border: 'none' }}>{i + 1}</div>
              <div className="step-body">
                <div className="step-role">{s.role}</div>
                {s.nom && <div className="step-nom">{s.nom}</div>}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setStep(2)}>Retour</button>
        <button className="btn btn-or" style={{ flex: 2 }} onClick={handleCreate}>
          ✓ Créer et générer le QR
        </button>
      </div>
    </div>
  )
}
