import React, { useState, useEffect } from 'react'
import { LayoutDashboard, QrCode, Bell, FileText, Settings } from 'lucide-react'
import Dashboard from './components/Dashboard.jsx'
import NewParapheur from './components/NewParapheur.jsx'
import ParapheurDetail from './components/ParapheurDetail.jsx'
import Scanner from './components/Scanner.jsx'
import AlertsView from './components/AlertsView.jsx'
import { loadParapheurs, getAlerts } from './store.js'

const NAV = [
  { key: 'dashboard', label: 'Tableau de bord', Icon: LayoutDashboard },
  { key: 'scanner', label: 'Scanner', Icon: QrCode },
  { key: 'alertes', label: 'Alertes', Icon: Bell },
]

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [parapheurs, setParapheurs] = useState([])
  const [selected, setSelected] = useState(null) // parapheur detail
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    setParapheurs(loadParapheurs())
    // Demander permission notifications
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
    // Check alerts every minute
    const interval = setInterval(checkAndNotify, 60_000)
    return () => clearInterval(interval)
  }, [])

  function refresh() {
    setParapheurs(loadParapheurs())
  }

  function checkAndNotify() {
    const list = loadParapheurs()
    const alerts = getAlerts(list)
    if (alerts.length > 0 && Notification.permission === 'granted') {
      const urgent = alerts.filter(a => a.type === 'danger')
      if (urgent.length > 0) {
        new Notification('CAP SUD — Parapheurs en retard', {
          body: `${urgent.length} dossier(s) en retard : ${urgent.map(a => a.par.reference).join(', ')}`,
          icon: '/logo192.png',
          tag: 'parapheur-urgent'
        })
      }
    }
  }

  const alerts = getAlerts(parapheurs)
  const alertCount = alerts.length

  // Detail view
  if (selected) {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
        <div className="topbar">
          <div className="topbar-logo">
            <span>CAP SUD</span>
            <span className="badge">PARAPHEUR</span>
          </div>
        </div>
        <div className="content">
          <ParapheurDetail
            par={selected}
            onBack={() => setSelected(null)}
            onUpdated={() => { refresh(); setSelected(null) }}
          />
        </div>
      </div>
    )
  }

  // Create view
  if (creating) {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
        <div className="topbar">
          <div className="topbar-logo">
            <span>CAP SUD</span>
            <span className="badge">PARAPHEUR</span>
          </div>
        </div>
        <div className="content">
          <NewParapheur
            onCreated={(par) => {
              refresh()
              setCreating(false)
              setSelected(par)
            }}
            onCancel={() => setCreating(false)}
          />
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div className="topbar">
        <div className="topbar-logo">
          <CAPSUDLogo />
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, lineHeight: 1 }}>CAP SUD</div>
            <div style={{ fontSize: 10, opacity: .7, lineHeight: 1.2 }}>Parapheur Numérique</div>
          </div>
        </div>
        <div className="topbar-actions">
          {alertCount > 0 && (
            <div style={{ position: 'relative' }}>
              <Bell size={22} color="#fff" />
              <span style={{
                position: 'absolute', top: -4, right: -4,
                background: 'var(--cs-rouge)', color: '#fff',
                borderRadius: '50%', width: 16, height: 16,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 700
              }}>{alertCount > 9 ? '9+' : alertCount}</span>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="content">
        {tab === 'dashboard' && (
          <Dashboard
            parapheurs={parapheurs}
            onSelect={setSelected}
            onNew={() => setCreating(true)}
          />
        )}
        {tab === 'scanner' && (
          <Scanner onFound={(par) => { setSelected(par); setTab('dashboard') }} />
        )}
        {tab === 'alertes' && (
          <AlertsView parapheurs={parapheurs} onSelect={(par) => { setSelected(par) }} />
        )}
      </div>

      {/* Bottom nav */}
      <nav className="bottom-nav">
        {NAV.map(({ key, label, Icon }) => (
          <button key={key} className={`nav-item ${tab === key ? 'active' : ''}`} onClick={() => setTab(key)}>
            <div style={{ position: 'relative' }}>
              <Icon />
              {key === 'alertes' && alertCount > 0 && (
                <span style={{
                  position: 'absolute', top: -4, right: -6,
                  background: 'var(--cs-rouge)', color: '#fff',
                  borderRadius: '50%', width: 14, height: 14,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 9, fontWeight: 700
                }}>{alertCount > 9 ? '9+' : alertCount}</span>
              )}
            </div>
            {label}
          </button>
        ))}
      </nav>
    </div>
  )
}

function CAPSUDLogo() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
      <rect width="32" height="32" rx="6" fill="#D4AC0D" />
      <text x="16" y="22" textAnchor="middle" fill="#1A5276" fontSize="11" fontWeight="800" fontFamily="Inter, sans-serif">CS</text>
    </svg>
  )
}
