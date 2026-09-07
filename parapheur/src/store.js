import { v4 as uuid } from 'uuid'
import { supabase, hasSupabase } from './supabase.js'

const KEY = 'capsud_parapheurs'
const SETTINGS_KEY = 'capsud_settings'

// ── localStorage helpers ───────────────────────────────────
function localLoad() {
  try { return JSON.parse(localStorage.getItem(KEY) || '[]') } catch { return [] }
}
function localSaveAll(list) {
  localStorage.setItem(KEY, JSON.stringify(list))
}
function localSaveOne(par) {
  const list = localLoad()
  const idx = list.findIndex(p => p.id === par.id)
  if (idx >= 0) list[idx] = par
  else list.unshift(par)
  localSaveAll(list)
}

// ── Public API ─────────────────────────────────────────────

export function genRef() {
  const y = new Date().getFullYear()
  return `PAR-${y}-${String(Math.floor(Math.random() * 9000) + 1000)}`
}

export async function loadParapheurs() {
  if (!hasSupabase) return localLoad()
  const { data, error } = await supabase
    .from('parapheurs')
    .select('data')
    .order('updated_at', { ascending: false })
  if (error) { console.error('Supabase load error:', error); return localLoad() }
  return data.map(r => r.data)
}

export async function saveParapheurs(list) {
  if (!hasSupabase) { localSaveAll(list); return }
  // Remplace toute la table (utilisé pour import et seed)
  await supabase.from('parapheurs').delete().neq('id', '')
  if (list.length > 0) {
    const now = new Date().toISOString()
    await supabase.from('parapheurs').upsert(
      list.map(par => ({ id: par.id, data: par, updated_at: now }))
    )
  }
}

export async function createParapheur({ objet, service, priorite, deadline, circuit, notes }) {
  const id = uuid()
  const par = {
    id,
    reference: genRef(),
    objet,
    service,
    priorite: priorite || 'normal',
    notes: notes || '',
    createdAt: new Date().toISOString(),
    deadline: deadline || null,
    circuit: circuit.map((step, i) => ({
      ...step,
      ordre: i,
      statut: i === 0 ? 'en_cours' : 'en_attente',
      date: null,
      commentaire: ''
    })),
    statut: 'en_cours',
    history: [{ action: 'Création', date: new Date().toISOString(), auteur: 'Système' }]
  }
  if (!hasSupabase) {
    const list = localLoad()
    list.unshift(par)
    localSaveAll(list)
  } else {
    const { error } = await supabase.from('parapheurs').insert({
      id: par.id,
      data: par,
      updated_at: new Date().toISOString()
    })
    if (error) console.error('Supabase insert error:', error)
  }
  return par
}

export async function updateStepStatut(parapheurId, stepOrdre, statut, commentaire = '', auteur = '') {
  const list = await loadParapheurs()
  const par = list.find(p => p.id === parapheurId)
  if (!par) return null

  const step = par.circuit[stepOrdre]
  step.statut = statut
  step.date = new Date().toISOString()
  step.commentaire = commentaire

  par.history.push({
    action: `Étape ${stepOrdre + 1} — ${statut === 'valide' ? 'Validé' : 'Refusé'}`,
    date: new Date().toISOString(),
    auteur: auteur || step.nom || step.role
  })

  if (statut === 'refuse') {
    par.statut = 'refuse'
  } else if (statut === 'valide') {
    const next = par.circuit[stepOrdre + 1]
    if (next) {
      next.statut = 'en_cours'
    } else {
      par.statut = 'valide'
      par.history.push({ action: 'Parapheur validé complet', date: new Date().toISOString(), auteur: 'Système' })
    }
  }

  if (!hasSupabase) {
    localSaveOne(par)
  } else {
    const { error } = await supabase.from('parapheurs')
      .update({ data: par, updated_at: new Date().toISOString() })
      .eq('id', parapheurId)
    if (error) console.error('Supabase update error:', error)
  }
  return par
}

export async function archiveParapheur(id) {
  const list = await loadParapheurs()
  const par = list.find(p => p.id === id)
  if (!par) return
  par.statut = 'archive'
  par.history.push({ action: 'Archivé', date: new Date().toISOString(), auteur: 'Système' })
  if (!hasSupabase) {
    localSaveOne(par)
  } else {
    await supabase.from('parapheurs')
      .update({ data: par, updated_at: new Date().toISOString() })
      .eq('id', id)
  }
}

export async function deleteParapheur(id) {
  if (!hasSupabase) {
    localSaveAll(localLoad().filter(p => p.id !== id))
  } else {
    await supabase.from('parapheurs').delete().eq('id', id)
  }
}

// ── Settings (toujours localStorage) ──────────────────────
export function loadSettings() {
  try { return JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}') } catch { return {} }
}
export function saveSettings(s) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(s))
}

// ── Calculs sur la liste (synchrones) ─────────────────────
export function getAlerts(list) {
  const now = new Date()
  const alerts = []
  list.forEach(par => {
    if (par.statut === 'valide' || par.statut === 'archive') return
    if (!par.deadline) return
    const deadline = new Date(par.deadline)
    const diffDays = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24))
    if (diffDays < 0) {
      alerts.push({ type: 'danger', par, msg: `En retard de ${Math.abs(diffDays)} jour(s)` })
    } else if (diffDays <= 2) {
      alerts.push({ type: 'warning', par, msg: `Échéance dans ${diffDays} jour(s)` })
    } else if (diffDays <= 5) {
      alerts.push({ type: 'info', par, msg: `Échéance dans ${diffDays} jour(s)` })
    }
    const currentStep = par.circuit.find(s => s.statut === 'en_cours')
    if (currentStep?.date) {
      const stepAge = Math.ceil((now - new Date(currentStep.date)) / (1000 * 60 * 60 * 24))
      if (stepAge >= 3) {
        alerts.push({ type: 'warning', par, msg: `En attente de ${currentStep.nom || currentStep.role} depuis ${stepAge}j` })
      }
    }
  })
  return alerts
}

export function getStats(list) {
  return {
    total: list.length,
    en_cours: list.filter(p => p.statut === 'en_cours').length,
    valide: list.filter(p => p.statut === 'valide').length,
    urgent: list.filter(p => p.priorite === 'urgent' && p.statut === 'en_cours').length,
    refuse: list.filter(p => p.statut === 'refuse').length,
    archive: list.filter(p => p.statut === 'archive').length,
  }
}

export const CIRCUITS_PREDEFINED = [
  {
    label: 'Standard (3 étapes)',
    steps: [
      { role: 'Agent instructeur', nom: '' },
      { role: 'Chef de service', nom: '' },
      { role: 'DGS', nom: '' },
    ]
  },
  {
    label: 'Délibération (4 étapes)',
    steps: [
      { role: 'Agent instructeur', nom: '' },
      { role: 'Chef de service', nom: '' },
      { role: 'DGS', nom: '' },
      { role: 'Élu signataire', nom: '' },
    ]
  },
  {
    label: 'Marché public (5 étapes)',
    steps: [
      { role: 'Service marchés', nom: '' },
      { role: 'Contrôle interne', nom: '' },
      { role: 'DAF', nom: '' },
      { role: 'DGS', nom: '' },
      { role: 'Président / Maire', nom: '' },
    ]
  },
  {
    label: 'Simple (2 étapes)',
    steps: [
      { role: 'Agent instructeur', nom: '' },
      { role: 'Directeur', nom: '' },
    ]
  },
]

export const SERVICES = [
  'Direction Générale',
  'Direction des Finances',
  'Direction des Ressources Humaines',
  'Direction des Travaux',
  'Direction de l\'Urbanisme',
  'Direction des Affaires Juridiques',
  'Direction de la Communication',
  'Direction des Services Techniques',
  'Cabinet du Président',
  'Autres',
]
