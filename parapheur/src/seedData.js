import { v4 as uuid } from 'uuid'
import { saveParapheurs, loadParapheurs } from './store.js'

// Données de test réalistes pour CAP SUD Martinique
// Simule un vrai contexte d'une communauté d'agglomération

function daysAgo(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString()
}

function daysFromNow(n) {
  const d = new Date()
  d.setDate(d.getDate() + n)
  return d.toISOString().split('T')[0]
}

export function hasSeedData() {
  return loadParapheurs().some(p => p._seed === true)
}

export function injectSeedData() {
  const existing = loadParapheurs().filter(p => !p._seed)

  const seed = [

    // ─── CAS 1 : PARAPHEUR EN COURS – ÉTAPE 2/4 ──────────────────────────────
    // QR imprimé sur le dossier, déjà validé par le service marchés,
    // actuellement sur le bureau du DAF
    {
      _seed: true,
      id: 'seed-001-marche-voirie-2026',
      reference: 'PAR-2026-0142',
      objet: 'Délibération n°2026-042 — Attribution marché réhabilitation Salle des Fêtes de Rivière-Pilote (lot 2 : électricité)',
      service: 'Direction des Travaux',
      priorite: 'urgent',
      notes: 'Dossier lié à la DETR 2026 — délai impératif avant le conseil communautaire du 27 juin.',
      createdAt: daysAgo(5),
      deadline: daysFromNow(2),
      statut: 'en_cours',
      circuit: [
        {
          ordre: 0,
          role: 'Service Marchés Publics',
          nom: 'Marie DORMOY',
          statut: 'valide',
          date: daysAgo(3),
          commentaire: 'Dossier conforme — rapport d\'analyse joint. Attribution au groupement SOCOTEC / ETAB pour 87 450 € HT.'
        },
        {
          ordre: 1,
          role: 'Directeur des Finances (DAF)',
          nom: 'Jean-Louis BERTRAND',
          statut: 'en_cours',
          date: daysAgo(1),
          commentaire: ''
        },
        {
          ordre: 2,
          role: 'Directeur Général des Services (DGS)',
          nom: 'Sandrine LACROIX',
          statut: 'en_attente',
          date: null,
          commentaire: ''
        },
        {
          ordre: 3,
          role: 'Président — Signature exécutoire',
          nom: 'M. le Président',
          statut: 'en_attente',
          date: null,
          commentaire: ''
        }
      ],
      history: [
        { action: 'Création du parapheur', date: daysAgo(5), auteur: 'Marie DORMOY' },
        { action: 'Étape 1 — Validé', date: daysAgo(3), auteur: 'Marie DORMOY' },
        { action: 'Étape 2 transmise au DAF', date: daysAgo(3), auteur: 'Système' },
      ]
    },

    // ─── CAS 2 : PARAPHEUR EN COURS – ÉTAPE 1/3 ──────────────────────────────
    // Dossier RH — convention de partenariat, parcours normal
    {
      _seed: true,
      id: 'seed-002-convention-pole-emploi',
      reference: 'PAR-2026-0138',
      objet: 'Convention de partenariat CAP SUD / Pôle Emploi Martinique — Insertion professionnelle 2026-2028',
      service: 'Direction des Ressources Humaines',
      priorite: 'normal',
      notes: '',
      createdAt: daysAgo(2),
      deadline: daysFromNow(10),
      statut: 'en_cours',
      circuit: [
        {
          ordre: 0,
          role: 'Chargée de mission RH',
          nom: 'Carole MONDESIR',
          statut: 'en_cours',
          date: daysAgo(2),
          commentaire: ''
        },
        {
          ordre: 1,
          role: 'Directeur Général des Services (DGS)',
          nom: 'Sandrine LACROIX',
          statut: 'en_attente',
          date: null,
          commentaire: ''
        },
        {
          ordre: 2,
          role: 'Élu délégué à l\'emploi',
          nom: 'Mme MARIE-SAINTE',
          statut: 'en_attente',
          date: null,
          commentaire: ''
        }
      ],
      history: [
        { action: 'Création du parapheur', date: daysAgo(2), auteur: 'Carole MONDESIR' },
      ]
    },

    // ─── CAS 3 : PARAPHEUR REFUSÉ ─────────────────────────────────────────────
    // Marché refusé par le DGS — pièce manquante
    {
      _seed: true,
      id: 'seed-003-refuse-dgs',
      reference: 'PAR-2026-0131',
      objet: 'Avenant n°1 — Marché de maintenance parc informatique (prestataire NUMERIA)',
      service: 'Direction des Services Techniques',
      priorite: 'normal',
      notes: 'Avenant de 12 500 € — dépassement seuil initial de 10 %.',
      createdAt: daysAgo(8),
      deadline: daysFromNow(-1),
      statut: 'refuse',
      circuit: [
        {
          ordre: 0,
          role: 'Agent instructeur',
          nom: 'Thierry CÉLESTE',
          statut: 'valide',
          date: daysAgo(6),
          commentaire: 'Avenant justifié — devis joint.'
        },
        {
          ordre: 1,
          role: 'Directeur Général des Services (DGS)',
          nom: 'Sandrine LACROIX',
          statut: 'refuse',
          date: daysAgo(4),
          commentaire: 'Refus : fiche d\'impact budgétaire manquante. Retourner le dossier au service avec pièce complémentaire avant réengagement.'
        },
        {
          ordre: 2,
          role: 'Président',
          nom: 'M. le Président',
          statut: 'en_attente',
          date: null,
          commentaire: ''
        }
      ],
      history: [
        { action: 'Création du parapheur', date: daysAgo(8), auteur: 'Thierry CÉLESTE' },
        { action: 'Étape 1 — Validé', date: daysAgo(6), auteur: 'Thierry CÉLESTE' },
        { action: 'Étape 2 — Refusé', date: daysAgo(4), auteur: 'Sandrine LACROIX' },
      ]
    },

    // ─── CAS 4 : PARAPHEUR VALIDÉ COMPLET ────────────────────────────────────
    // Arrêté signé par le Président
    {
      _seed: true,
      id: 'seed-004-arrete-valide',
      reference: 'PAR-2026-0118',
      objet: 'Arrêté n°2026-018 — Autorisation de voirie permanente RN1 secteur Marin / Le Vauclin',
      service: 'Direction de l\'Urbanisme',
      priorite: 'normal',
      notes: '',
      createdAt: daysAgo(15),
      deadline: daysFromNow(-5),
      statut: 'valide',
      circuit: [
        {
          ordre: 0,
          role: 'Instructrice urbanisme',
          nom: 'Fabiola ROSETTE',
          statut: 'valide',
          date: daysAgo(13),
          commentaire: 'Instruction conforme au PLU intercommunal.'
        },
        {
          ordre: 1,
          role: 'Directeur Général des Services (DGS)',
          nom: 'Sandrine LACROIX',
          statut: 'valide',
          date: daysAgo(10),
          commentaire: 'Validé — aucune réserve juridique.'
        },
        {
          ordre: 2,
          role: 'Président — Signature exécutoire',
          nom: 'M. le Président',
          statut: 'valide',
          date: daysAgo(7),
          commentaire: 'Signé et transmis à la Préfecture pour contrôle de légalité.'
        }
      ],
      history: [
        { action: 'Création du parapheur', date: daysAgo(15), auteur: 'Fabiola ROSETTE' },
        { action: 'Étape 1 — Validé', date: daysAgo(13), auteur: 'Fabiola ROSETTE' },
        { action: 'Étape 2 — Validé', date: daysAgo(10), auteur: 'Sandrine LACROIX' },
        { action: 'Étape 3 — Validé', date: daysAgo(7), auteur: 'M. le Président' },
        { action: 'Parapheur validé complet', date: daysAgo(7), auteur: 'Système' },
      ]
    },

    // ─── CAS 5 : PARAPHEUR EN RETARD ─────────────────────────────────────────
    // Délibération budget bloquée depuis 4 jours chez le chef de service
    {
      _seed: true,
      id: 'seed-005-retard-budget',
      reference: 'PAR-2026-0149',
      objet: 'Décision modificative n°2 — Budget principal 2026 (virement de crédits section investissement)',
      service: 'Direction des Finances',
      priorite: 'urgent',
      notes: 'Virement de 43 000 € du chapitre 21 vers chapitre 23 pour financement travaux urgents STEP du Marin.',
      createdAt: daysAgo(7),
      deadline: daysFromNow(-2),
      statut: 'en_cours',
      circuit: [
        {
          ordre: 0,
          role: 'Contrôleur de gestion',
          nom: 'Pascal OLANDIER',
          statut: 'valide',
          date: daysAgo(6),
          commentaire: 'Chiffres vérifiés — impact neutre sur l\'équilibre budgétaire.'
        },
        {
          ordre: 1,
          role: 'Chef du service Finances',
          nom: 'Micheline FLÉMIN',
          statut: 'en_cours',
          date: daysAgo(4),
          commentaire: ''
        },
        {
          ordre: 2,
          role: 'Directeur des Finances (DAF)',
          nom: 'Jean-Louis BERTRAND',
          statut: 'en_attente',
          date: null,
          commentaire: ''
        },
        {
          ordre: 3,
          role: 'DGS',
          nom: 'Sandrine LACROIX',
          statut: 'en_attente',
          date: null,
          commentaire: ''
        }
      ],
      history: [
        { action: 'Création du parapheur', date: daysAgo(7), auteur: 'Pascal OLANDIER' },
        { action: 'Étape 1 — Validé', date: daysAgo(6), auteur: 'Pascal OLANDIER' },
        { action: 'Étape 2 transmise au Chef des Finances', date: daysAgo(6), auteur: 'Système' },
      ]
    }
  ]

  saveParapheurs([...seed, ...existing])
  return seed
}
