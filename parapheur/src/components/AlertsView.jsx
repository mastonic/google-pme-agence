import React from 'react'
import { AlertTriangle, Clock, CheckCircle, Bell, BellOff } from 'lucide-react'
import { getAlerts } from '../store.js'
import { format, differenceInDays } from 'date-fns'
import { fr } from 'date-fns/locale'

const ICON = {
  danger: <AlertTriangle size={18} color="var(--cs-rouge)" />,
  warning: <Clock size={18} color="var(--cs-or)" />,
  info: <Bell size={18} color="var(--cs-bleu)" />,
}

export default function AlertsView({ parapheurs, onSelect }) {
  const alerts = getAlerts(parapheurs)

  const enCours = parapheurs.filter(p => p.statut === 'en_cours')
  const sansDeadline = enCours.filter(p => !p.deadline)

  return (
    <div className="fade-in">
      <div className="header-banner" style={{ marginBottom: 16 }}>
        <h2>Alertes & Relances</h2>
        <p>{alerts.length} alerte{alerts.length > 1 ? 's' : ''} active{alerts.length > 1 ? 's' : ''}</p>
      </div>

      {alerts.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <CheckCircle size={48} color="var(--cs-vert)" style={{ opacity: 1, marginBottom: 12 }} />
            <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--cs-vert)', marginBottom: 6 }}>Tout est sous contrôle</div>
            <p>Aucun dossier en retard ou proche de l'échéance.</p>
          </div>
        </div>
      ) : (
        <>
          <div className="section-title">Alertes en cours</div>
          {alerts.map((a, i) => (
            <div key={i} className={`alert-item ${a.type}`} style={{ cursor: 'pointer' }} onClick={() => onSelect(a.par)}>
              <div className="alert-icon">{ICON[a.type]}</div>
              <div className="alert-body">
                <div className="alert-title">{a.par.reference} — {a.par.objet}</div>
                <div className="alert-desc">{a.msg}</div>
                <div className="alert-desc">{a.par.service}</div>
              </div>
              <div style={{ fontSize: 11, color: 'var(--cs-muted)', flexShrink: 0, alignSelf: 'center' }}>→</div>
            </div>
          ))}
        </>
      )}

      {/* Parapheurs sans deadline */}
      {sansDeadline.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div className="section-title">Sans échéance définie ({sansDeadline.length})</div>
          <div className="card" style={{ padding: '4px 16px' }}>
            {sansDeadline.map(par => (
              <div key={par.id} className="par-item" onClick={() => onSelect(par)}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--cs-bleu)' }}>{par.reference}</div>
                  <div style={{ fontSize: 13 }}>{par.objet}</div>
                  <div style={{ fontSize: 11, color: 'var(--cs-muted)' }}>{par.service}</div>
                </div>
                <BellOff size={14} color="var(--cs-muted)" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Résumé hebdo */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>Résumé de la semaine</div>
        <WeeklySummary parapheurs={parapheurs} />
      </div>

      {/* Tip notifications */}
      <div className="alert-item info" style={{ marginTop: 8 }}>
        <div className="alert-icon"><Bell size={18} color="var(--cs-bleu)" /></div>
        <div className="alert-body">
          <div className="alert-title">Notifications push</div>
          <div className="alert-desc">Installez l'application (PWA) sur votre écran d'accueil pour recevoir des rappels automatiques.</div>
        </div>
      </div>
    </div>
  )
}

function WeeklySummary({ parapheurs }) {
  const now = new Date()
  const thisWeek = parapheurs.filter(p => {
    const d = new Date(p.createdAt)
    return differenceInDays(now, d) <= 7
  })
  const validated = parapheurs.filter(p => {
    if (p.statut !== 'valide') return false
    const last = p.history[p.history.length - 1]
    return last && differenceInDays(now, new Date(last.date)) <= 7
  })

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
      {[
        { label: 'Créés cette semaine', value: thisWeek.length, color: 'var(--cs-bleu)' },
        { label: 'Validés cette semaine', value: validated.length, color: 'var(--cs-vert)' },
        { label: 'En cours total', value: parapheurs.filter(p => p.statut === 'en_cours').length, color: 'var(--cs-or)' },
        { label: 'Urgents actifs', value: parapheurs.filter(p => p.priorite === 'urgent' && p.statut === 'en_cours').length, color: 'var(--cs-rouge)' },
      ].map(({ label, value, color }) => (
        <div key={label} style={{ background: 'var(--cs-gris)', borderRadius: 8, padding: '10px 12px' }}>
          <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
          <div style={{ fontSize: 11, color: 'var(--cs-muted)', marginTop: 2 }}>{label}</div>
        </div>
      ))}
    </div>
  )
}
