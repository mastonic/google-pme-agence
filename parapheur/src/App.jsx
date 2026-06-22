import React, { useState, useEffect } from 'react'
import { LayoutDashboard, QrCode, Bell, FlaskConical } from 'lucide-react'
import Dashboard from './components/Dashboard.jsx'
import NewParapheur from './components/NewParapheur.jsx'
import ParapheurDetail from './components/ParapheurDetail.jsx'
import Scanner from './components/Scanner.jsx'
import AlertsView from './components/AlertsView.jsx'
import { loadParapheurs, getAlerts } from './store.js'
import { injectSeedData, hasSeedData } from './seedData.js'

const NAV = [
  { key: 'dashboard', label: 'Tableau de bord', Icon: LayoutDashboard },
  { key: 'scanner', label: 'Scanner QR', Icon: QrCode },
  { key: 'alertes', label: 'Alertes', Icon: Bell },
]

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [parapheurs, setParapheurs] = useState([])
  const [selected, setSelected] = useState(null)
  const [creating, setCreating] = useState(false)
  const [showSeedBanner, setShowSeedBanner] = useState(false)
  const [seedLoaded, setSeedLoaded] = useState(false)

  useEffect(() => {
    const list = loadParapheurs()
    setParapheurs(list)
    setSeedLoaded(hasSeedData())

    // Détection QR scan via URL : ?id={parapheurId}
    const params = new URLSearchParams(window.location.search)
    const idFromUrl = params.get('id')
    if (idFromUrl) {
      const found = list.find(p => p.id === idFromUrl)
      if (found) {
        setSelected(found)
        // Nettoyer l'URL sans recharger
        window.history.replaceState({}, '', window.location.pathname)
      } else {
        setTab('scanner')
      }
    }

    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
    const interval = setInterval(checkAndNotify, 60_000)
    return () => clearInterval(interval)
  }, [])

  function refresh() {
    const list = loadParapheurs()
    setParapheurs(list)
    setSeedLoaded(hasSeedData())
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

  function handleLoadDemo() {
    injectSeedData()
    refresh()
    setSeedLoaded(true)
    setShowSeedBanner(true)
    setTimeout(() => setShowSeedBanner(false), 4000)
  }

  const alerts = getAlerts(parapheurs)
  const alertCount = alerts.length

  const topbar = (
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
            <span style={{ position: 'absolute', top: -4, right: -4, background: 'var(--cs-rouge)', color: '#fff', borderRadius: '50%', width: 16, height: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700 }}>
              {alertCount > 9 ? '9+' : alertCount}
            </span>
          </div>
        )}
      </div>
    </div>
  )

  if (selected) {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
        {topbar}
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

  if (creating) {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
        {topbar}
        <div className="content">
          <NewParapheur
            onCreated={(par) => { refresh(); setCreating(false); setSelected(par) }}
            onCancel={() => setCreating(false)}
          />
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
      {topbar}

      {showSeedBanner && (
        <div style={{ background: 'var(--cs-vert)', color: '#fff', padding: '10px 16px', fontSize: 13, fontWeight: 600, textAlign: 'center' }}>
          ✓ 5 parapheurs de démonstration chargés avec succès !
        </div>
      )}

      <div className="content">
        {tab === 'dashboard' && (
          <>
            {!seedLoaded && (
              <div className="alert-item info" style={{ marginBottom: 12, cursor: 'pointer' }} onClick={handleLoadDemo}>
                <div className="alert-icon"><FlaskConical size={18} color="var(--cs-bleu)" /></div>
                <div className="alert-body">
                  <div className="alert-title">Charger la démo CAP SUD</div>
                  <div className="alert-desc">5 parapheurs fictifs réalistes pour tester toutes les fonctionnalités → cliquez ici</div>
                </div>
                <div style={{ alignSelf: 'center', fontSize: 18 }}>→</div>
              </div>
            )}
            {seedLoaded && (
              <div style={{ textAlign: 'right', marginBottom: 8 }}>
                <span style={{ fontSize: 11, color: 'var(--cs-muted)', cursor: 'pointer', textDecoration: 'underline' }} onClick={handleLoadDemo}>
                  Recharger les données démo
                </span>
              </div>
            )}
            <Dashboard
              parapheurs={parapheurs}
              onSelect={setSelected}
              onNew={() => setCreating(true)}
            />
          </>
        )}
        {tab === 'scanner' && (
          <Scanner onFound={(par) => { setSelected(par) }} />
        )}
        {tab === 'alertes' && (
          <AlertsView parapheurs={parapheurs} onSelect={(par) => { setSelected(par) }} />
        )}
      </div>

      <nav className="bottom-nav">
        {NAV.map(({ key, label, Icon }) => (
          <button key={key} className={`nav-item ${tab === key ? 'active' : ''}`} onClick={() => setTab(key)}>
            <div style={{ position: 'relative' }}>
              <Icon />
              {key === 'alertes' && alertCount > 0 && (
                <span style={{ position: 'absolute', top: -4, right: -6, background: 'var(--cs-rouge)', color: '#fff', borderRadius: '50%', width: 14, height: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 700 }}>
                  {alertCount > 9 ? '9+' : alertCount}
                </span>
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
