// Source unique des tarifs publics affichés dans les contenus SEO (pages locales, articles, FAQ).
// Doit rester aligné sur backend/services/plans.py (abonnements, réceptionniste, Pack Connecté)
// et sur app/store/page.tsx (packs). Tous les prix sont hors taxes.

export const PLANS_HT = [
  { name: 'Starter', monthly: 49, annual: 490, summary: 'Site vitrine jusqu’à 5 pages, hébergement, SSL, maintenance, 1 modification par mois.' },
  { name: 'Pro', monthly: 149, annual: 1490, summary: 'Starter + nom de domaine, SEO local, optimisation et suivi de la fiche Google, suivi des appels et demandes, 3 modifications par mois.' },
  { name: 'Élite', monthly: 299, annual: 2990, summary: 'Pro + réceptionniste IA et Pack Connecté inclus, 4 contenus SEO et 4 publications Google par mois, automatisation des demandes d’avis, jusqu’à 10 modifications par mois.' },
] as const

export const PACKS_HT = {
  ficheGoogle: { name: 'Fiche Google optimisée', price: 149, delay: '5 jours ouvrés', path: '/store/fiche-google-optimisee/' },
  avis: { name: 'Pack 50 avis', price: 99, path: '/store/#packs' },
  auditIA: { name: 'Audit visibilité IA', price: 99, path: '/store/#packs' },
} as const

export const RECEPTIONIST = {
  monthly: 39,
  includedCalls: 100,
  extraCallHT: '0,83',
  extraCallTTC: '1',
  trialDays: 30,
  trialCalls: 60,
} as const

export const CONNECT_PACK_HT = 19

export const fmt = (n: number) => n.toLocaleString('fr-FR').replace(/ /g, ' ')
