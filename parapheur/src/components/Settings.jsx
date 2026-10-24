import React, { useState, useRef } from 'react'
import { Server, Database, Info, Eye, EyeOff, Download, Upload, Trash2, ChevronRight, ChevronDown } from 'lucide-react'
import { loadSettings, saveSettings, loadParapheurs, saveParapheurs } from '../store.js'

const DEFAULT_LDAP = {
  enabled: false,
  type: 'openldap',
  proxyUrl: '',
  server: '',
  port: 389,
  ssl: false,
  baseDn: '',
  bindDn: '',
  bindPassword: '',
  userFilter: '(objectClass=inetOrgPerson)',
  loginAttr: 'uid',
  nameAttr: 'cn',
  emailAttr: 'mail',
}

const DEFAULT_CFG = {
  general: { collectivite: 'CAP SUD Martinique' },
  ldap: { ...DEFAULT_LDAP },
}

function merge(stored) {
  return {
    general: { ...DEFAULT_CFG.general, ...(stored.general || {}) },
    ldap: { ...DEFAULT_CFG.ldap, ...(stored.ldap || {}) },
  }
}

export default function SettingsView({ onDataChanged }) {
  const [cfg, setCfg] = useState(() => merge(loadSettings()))
  const [toast, setToast] = useState('')
  const [showPwd, setShowPwd] = useState(false)
  const [ldapOpen, setLdapOpen] = useState(false)
  const [ldapStatus, setLdapStatus] = useState(null) // null | 'testing' | 'ok' | 'error'
  const [ldapMsg, setLdapMsg] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [importMsg, setImportMsg] = useState('')
  const importRef = useRef(null)

  function setGeneral(k, v) { setCfg(c => ({ ...c, general: { ...c.general, [k]: v } })) }
  function setLdap(k, v)    { setCfg(c => ({ ...c, ldap: { ...c.ldap, [k]: v } })) }

  function showToast(msg) {
    setToast(msg)
    setTimeout(() => setToast(''), 3000)
  }

  function handleSave() {
    saveSettings(cfg)
    showToast('✓ Paramètres sauvegardés')
  }

  async function handleTestLdap() {
    if (!cfg.ldap.proxyUrl) {
      setLdapStatus('error')
      setLdapMsg('Renseignez d\'abord l\'URL du proxy LDAP.')
      return
    }
    setLdapStatus('testing')
    setLdapMsg('')
    try {
      const url = cfg.ldap.proxyUrl.replace(/\/$/, '') + '/health'
      const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
      if (res.ok) {
        setLdapStatus('ok')
        setLdapMsg('Proxy accessible.')
      } else {
        setLdapStatus('error')
        setLdapMsg(`Statut HTTP ${res.status}`)
      }
    } catch (e) {
      setLdapStatus('error')
      setLdapMsg('Inaccessible : ' + (e.message || 'timeout'))
    }
  }

  async function handleExport() {
    const parapheurs = await loadParapheurs()
    const data = {
      parapheurs,
      settings: cfg,
      exportedAt: new Date().toISOString(),
      version: '1.0',
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `parapheurs-capsud-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(a.href)
  }

  function handleImport(e) {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = async ev => {
      try {
        const data = JSON.parse(ev.target.result)
        if (data.parapheurs) await saveParapheurs(data.parapheurs)
        if (data.settings) { saveSettings(data.settings); setCfg(merge(data.settings)) }
        setImportMsg(`✓ Import réussi — ${data.parapheurs?.length || 0} parapheurs chargés.`)
        setTimeout(() => setImportMsg(''), 4000)
        if (onDataChanged) onDataChanged()
      } catch {
        setImportMsg('✗ Fichier invalide ou corrompu.')
        setTimeout(() => setImportMsg(''), 3000)
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  async function handleDeleteAll() {
    await saveParapheurs([])
    setConfirmDelete(false)
    showToast('Toutes les données ont été effacées.')
    if (onDataChanged) onDataChanged()
  }

  const loginPlaceholder = cfg.ldap.type === 'activedirectory' ? 'sAMAccountName' : 'uid'
  const namePlaceholder  = cfg.ldap.type === 'activedirectory' ? 'displayName' : 'cn'

  return (
    <div className="fade-in">
      {/* Toast */}
      {toast && (
        <div style={{ position: 'fixed', top: 68, left: 0, right: 0, zIndex: 300, display: 'flex', justifyContent: 'center', pointerEvents: 'none' }}>
          <div style={{ background: 'var(--cs-texte)', color: '#fff', padding: '10px 20px', borderRadius: 24, fontSize: 14, fontWeight: 600, boxShadow: 'var(--shadow-md)' }}>
            {toast}
          </div>
        </div>
      )}

      <div className="header-banner" style={{ marginBottom: 16 }}>
        <h2>Paramètres</h2>
        <p>Configuration de l'application</p>
      </div>

      {/* ── Général ─────────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Général</span>
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Nom de la collectivité</label>
          <input className="form-input" value={cfg.general.collectivite}
            onChange={e => setGeneral('collectivite', e.target.value)} />
        </div>
      </div>

      {/* ── LDAP ────────────────────────────────────────────── */}
      <div className="card">
        {/* En-tête collapsible */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', marginBottom: 12 }}
          onClick={() => setLdapOpen(o => !o)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Server size={16} color="var(--cs-bleu)" />
            <span className="card-title">Authentification LDAP / Active Directory</span>
          </div>
          {ldapOpen
            ? <ChevronDown size={18} color="var(--cs-muted)" />
            : <ChevronRight size={18} color="var(--cs-muted)" />}
        </div>

        {/* Toggle activation */}
        <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 14, fontWeight: 500, marginBottom: ldapOpen ? 16 : 0 }}>
          <input type="checkbox" style={{ width: 18, height: 18, accentColor: 'var(--cs-bleu)' }}
            checked={cfg.ldap.enabled}
            onChange={e => setLdap('enabled', e.target.checked)} />
          Activer la connexion LDAP
          {cfg.ldap.enabled && (
            <span style={{ fontSize: 11, background: '#EBF5FB', color: 'var(--cs-bleu)', padding: '2px 8px', borderRadius: 10, fontWeight: 700 }}>
              Actif
            </span>
          )}
        </label>

        {/* Formulaire dépliable */}
        {ldapOpen && (
          <>
            {/* Note architecture */}
            <div style={{ padding: '10px 12px', background: '#FEF9E7', borderLeft: '3px solid var(--cs-or)', borderRadius: 6, fontSize: 12, lineHeight: 1.6, marginBottom: 16 }}>
              <strong>Prérequis :</strong> Un navigateur ne peut pas interroger LDAP directement (protocole TCP).
              Déployez un <strong>proxy REST</strong> côté serveur qui expose les routes <code>/health</code>, <code>/auth</code> et <code>/users</code>.
              L'app y envoie les identifiants — c'est le proxy qui interroge l'annuaire.
            </div>

            {/* Proxy URL */}
            <div className="form-group">
              <label className="form-label">URL du proxy REST <span>*</span></label>
              <input className="form-input" placeholder="https://ldap-proxy.votre-collectivite.fr/api"
                value={cfg.ldap.proxyUrl} onChange={e => setLdap('proxyUrl', e.target.value)} />
              <p className="form-hint">
                L'app appellera <code>{cfg.ldap.proxyUrl ? cfg.ldap.proxyUrl.replace(/\/$/, '') : 'https://…'}/auth</code> pour authentifier un agent
              </p>
            </div>

            {/* Type + Port */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Type d'annuaire</label>
                <select className="form-input" value={cfg.ldap.type} onChange={e => setLdap('type', e.target.value)}>
                  <option value="openldap">OpenLDAP</option>
                  <option value="activedirectory">Active Directory</option>
                  <option value="autre">Autre</option>
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Port</label>
                <select className="form-input" value={cfg.ldap.port} onChange={e => setLdap('port', parseInt(e.target.value))}>
                  <option value={389}>389 — LDAP</option>
                  <option value={636}>636 — LDAPS (SSL)</option>
                </select>
              </div>
            </div>

            {/* Serveur */}
            <div className="form-group">
              <label className="form-label">Serveur LDAP (hostname, pour le proxy)</label>
              <input className="form-input" placeholder="ldap.mairie-martinique.fr"
                value={cfg.ldap.server} onChange={e => setLdap('server', e.target.value)} />
            </div>

            {/* Base DN */}
            <div className="form-group">
              <label className="form-label">Base DN</label>
              <input className="form-input" placeholder="dc=mairie,dc=fr"
                value={cfg.ldap.baseDn} onChange={e => setLdap('baseDn', e.target.value)} />
            </div>

            {/* Bind DN */}
            <div className="form-group">
              <label className="form-label">DN de service (bind)</label>
              <input className="form-input" placeholder="cn=svc-parapheur,ou=apps,dc=mairie,dc=fr"
                value={cfg.ldap.bindDn} onChange={e => setLdap('bindDn', e.target.value)} />
            </div>

            {/* Mot de passe */}
            <div className="form-group">
              <label className="form-label">Mot de passe de service</label>
              <div style={{ position: 'relative' }}>
                <input className="form-input" type={showPwd ? 'text' : 'password'}
                  style={{ paddingRight: 44 }}
                  value={cfg.ldap.bindPassword}
                  onChange={e => setLdap('bindPassword', e.target.value)} />
                <button type="button"
                  style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--cs-muted)', padding: 0, display: 'flex' }}
                  onClick={() => setShowPwd(s => !s)}>
                  {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <p className="form-hint">Stocké en localStorage — utiliser un compte de service dédié, droits lecture seule uniquement.</p>
            </div>

            {/* Attributs */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Filtre utilisateurs</label>
                <input className="form-input" placeholder="(objectClass=inetOrgPerson)"
                  value={cfg.ldap.userFilter} onChange={e => setLdap('userFilter', e.target.value)} />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Attribut login</label>
                <input className="form-input" placeholder={loginPlaceholder}
                  value={cfg.ldap.loginAttr} onChange={e => setLdap('loginAttr', e.target.value)} />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Attribut nom complet</label>
                <input className="form-input" placeholder={namePlaceholder}
                  value={cfg.ldap.nameAttr} onChange={e => setLdap('nameAttr', e.target.value)} />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Attribut e-mail</label>
                <input className="form-input" placeholder="mail"
                  value={cfg.ldap.emailAttr} onChange={e => setLdap('emailAttr', e.target.value)} />
              </div>
            </div>

            {/* Test connexion */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 16 }}>
              <button className="btn btn-secondary btn-sm" onClick={handleTestLdap} disabled={ldapStatus === 'testing'}>
                <Server size={14} />
                {ldapStatus === 'testing' ? 'Test en cours…' : 'Tester le proxy'}
              </button>
              {ldapStatus === 'ok' && (
                <span style={{ fontSize: 12, color: 'var(--cs-vert)', fontWeight: 600 }}>✓ {ldapMsg}</span>
              )}
              {ldapStatus === 'error' && (
                <span style={{ fontSize: 12, color: 'var(--cs-rouge)', fontWeight: 600 }}>✗ {ldapMsg}</span>
              )}
            </div>
          </>
        )}
      </div>

      {/* ── Données ─────────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Database size={16} color="var(--cs-bleu)" />
            <span className="card-title">Données</span>
          </div>
        </div>

        {importMsg && (
          <div style={{
            padding: '8px 12px', borderRadius: 6, fontSize: 13, fontWeight: 600, marginBottom: 12,
            background: importMsg.startsWith('✓') ? '#E9F7EF' : '#FDEDEC',
            color: importMsg.startsWith('✓') ? 'var(--cs-vert)' : 'var(--cs-rouge)',
          }}>
            {importMsg}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button className="btn btn-secondary btn-full" onClick={handleExport}>
            <Download size={15} /> Exporter tous les parapheurs (JSON)
          </button>

          <button className="btn btn-secondary btn-full" onClick={() => importRef.current.click()}>
            <Upload size={15} /> Importer des parapheurs (JSON)
          </button>
          <input ref={importRef} type="file" accept=".json" style={{ display: 'none' }} onChange={handleImport} />

          {!confirmDelete ? (
            <button
              style={{ background: 'transparent', color: 'var(--cs-rouge)', border: '1px solid var(--cs-rouge)', borderRadius: 8, padding: '10px 18px', fontSize: 14, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
              onClick={() => setConfirmDelete(true)}>
              <Trash2 size={15} /> Effacer toutes les données
            </button>
          ) : (
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setConfirmDelete(false)}>Annuler</button>
              <button className="btn btn-danger" style={{ flex: 1 }} onClick={handleDeleteAll}>Confirmer</button>
            </div>
          )}
        </div>
      </div>

      {/* ── À propos ─────────────────────────────────────────── */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <Info size={16} color="var(--cs-bleu)" />
          <span className="card-title">À propos</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 7, fontSize: 13 }}>
          {[
            ['Version', '1.0.0 — MVP pilote'],
            ['Collectivité', cfg.general.collectivite],
            ['Dépôt', 'mastonic/parrafeur'],
            ['Hébergement', 'Vercel (HTTPS)'],
            ['Stockage', 'localStorage — local, sans serveur'],
            ['LDAP', cfg.ldap.enabled ? `Actif (${cfg.ldap.type})` : 'Désactivé'],
          ].map(([k, v]) => (
            <div key={k} style={{ display: 'flex', gap: 8 }}>
              <span style={{ color: 'var(--cs-muted)', width: 100, flexShrink: 0 }}>{k}</span>
              <span style={{ fontWeight: 500 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      <button className="btn btn-primary btn-full" style={{ marginBottom: 8 }} onClick={handleSave}>
        Sauvegarder les paramètres
      </button>
    </div>
  )
}
