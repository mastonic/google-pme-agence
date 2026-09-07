import React, { useState } from 'react'
import { FileText, Clock, CheckCircle, AlertTriangle, XCircle, Archive } from 'lucide-react'
import { getStats, getAlerts } from '../store.js'
import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'

const STATUT_LABEL = {
  en_cours: 'En cours',
  valide: 'Validé',
  refuse: 'Refusé',
  archive: 'Archivé',
  brouillon: 'Brouillon',
}

function StatutBadge({ statut, priorite }) {
  const cls = statut === 'valide' ? 'valide' : statut === 'refuse' ? 'refuse' : statut === 'archive' ? 'archive' : 'en_cours'
  if (priorite === 'urgent' && statut === 'en_cours') {
    return <span className="badge-statut badge-urgent">⚡ Urgent</span>
  }
  return <span className={`badge-statut badge-${cls}`}>{STATUT_LABEL[statut] || statut}</span>
}

function ProgressSteps({ circuit }) {
  const total = circuit.length
  const done = circuit.filter(s => s.statut === 'valide').length
  const pct = Math.round((done / total) * 100)
  const cls = pct === 100 ? 'ok' : pct >= 50 ? 'warn' : ''
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--cs-muted)', marginBottom: 3 }}>
        {done}/{total} étape{total > 1 ? 's' : ''}
      </div>
      <div className="progress-bar">
        <div className={`progress-fill ${cls}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function Dashboard({ parapheurs, onSelect, onNew }) {
  const [filter, setFilter] = useState('tous')
  const stats = getStats(parapheurs)
  const alerts = getAlerts(parapheurs)

  const TABS = [
    { key: 'tous', label: `Tous (${stats.total})` },
    { key: 'en_cours', label: `En cours (${stats.en_cours})` },
    { key: 'urgent', label: `Urgents (${stats.urgent})` },
    { key: 'valide', label: `Validés (${stats.valide})` },
    { key: 'refuse', label: `Refusés (${stats.refuse})` },
    { key: 'archive', label: `Archivés (${stats.archive})` },
  ]

  const filtered = parapheurs.filter(p => {
    if (filter === 'tous') return true
    if (filter === 'urgent') return p.priorite === 'urgent' && p.statut === 'en_cours'
    return p.statut === filter
  })

  return (
    <div className="fade-in">
      {alerts.length > 0 && (
        <div className="urgency-bar">
          <AlertTriangle size={14} />
          {alerts.length} alerte{alerts.length > 1 ? 's' : ''} — voir l'onglet Alertes
        </div>
      )}

      <div className="stats-row" style={{ marginTop: 16 }}>
        <div className="stat-card">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat-card">
          <span className="stat-value" style={{ color: 'var(--cs-or)' }}>{stats.en_cours}</span>
          <span className="stat-label">En cours</span>
        </div>
        <div className="stat-card ok">
          <span className="stat-value">{stats.valide}</span>
          <span className="stat-label">Validés</span>
        </div>
        <div className="stat-card urgent">
          <span className="stat-value">{stats.urgent}</span>
          <span className="stat-label">Urgents</span>
        </div>
      </div>

      <div className="tab-bar">
        {TABS.map(t => (
          <button key={t.key} className={`tab-btn ${filter === t.key ? 'active' : ''}`} onClick={() => setFilter(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="card" style={{ padding: '4px 16px' }}>
        {filtered.length === 0 ? (
          <div className="empty-state">
            <FileText size={40} />
            <p>Aucun parapheur dans cette catégorie</p>
          </div>
        ) : (
          filtered.map(par => (
            <div key={par.id} className="par-item" onClick={() => onSelect(par)}>
              <div className="par-icon">
                <FileText size={20} />
              </div>
              <div className="par-info">
                <div className="par-ref">{par.reference} · {par.service}</div>
                <div className="par-objet">{par.objet}</div>
                <div style={{ marginTop: 6 }}>
                  <ProgressSteps circuit={par.circuit} />
                </div>
                <div className="par-meta" style={{ marginTop: 4 }}>
                  {formatDistanceToNow(new Date(par.createdAt), { addSuffix: true, locale: fr })}
                  {par.deadline && ` · Échéance ${new Date(par.deadline).toLocaleDateString('fr-FR')}`}
                </div>
              </div>
              <div className="par-right">
                <StatutBadge statut={par.statut} priorite={par.priorite} />
                {par.deadline && new Date(par.deadline) < new Date() && par.statut === 'en_cours' && (
                  <span style={{ fontSize: 10, color: 'var(--cs-rouge)', fontWeight: 600 }}>EN RETARD</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      <button className="fab" onClick={onNew} title="Nouveau parapheur">
        <span style={{ fontSize: 24, lineHeight: 1 }}>+</span>
      </button>
    </div>
  )
}
