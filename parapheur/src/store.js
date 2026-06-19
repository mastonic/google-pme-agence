import { v4 as uuid } from 'uuid'

const KEY = 'capsud_parapheurs'
const NOTIF_KEY = 'capsud_notifications'

export function genRef() {
  const y = new Date().getFullYear()
  const n = String(Math.floor(Math.random() * 9000) + 1000)
  return `PAR-${y}-${n}`
}

export function loadParapheurs() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch { return [] }
}

export function saveParapheurs(list) {
  localStorage.setItem(KEY, JSON.stringify(list))
}

export function createParapheur({ objet, service, priorite, deadline, circuit, notes }) {
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
  const list = loadParapheurs()
  list.unshift(par)
  saveParapheurs(list)
  return par
}

export function updateStepStatut(parapheurId, stepOrdre, statut, commentaire = '', auteur = '') {
  const list = loadParapheurs()
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

  saveParapheurs(list)
  return par
}

export function archiveParapheur(id) {
  const list = loadParapheurs()
  const par = list.find(p => p.id === id)
  if (par) {
    par.statut = 'archive'
    par.history.push({ action: 'Archivé', date: new Date().toISOString(), auteur: 'Système' })
    saveParapheurs(list)
  }
}

export function deleteParapheur(id) {
  const list = loadParapheurs().filter(p => p.id !== id)
  saveParapheurs(list)
}

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

    // Step bloquée > 3 jours
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
