// Packs digitaux « Facture Électronique Ready » vendus sur pulse-locale-pme.store.
// checkoutUrl : lien de paiement Lemon Squeezy / Stripe à renseigner. Tant qu'il est vide,
// le bouton ouvre le formulaire de commande (OrderButton) comme le reste de la boutique.

export const FE_UPDATED = '2026-11-20'
export const FE_PATH = '/store/facture-electronique/'
export const fePackPath = (slug: string) => `${FE_PATH}${slug}/`

export type FePack = {
  slug: string
  kind: 'base' | 'metier' | 'pro'
  tag: string
  gold?: boolean
  name: string
  short: string
  price: number
  checkoutUrl?: string
  title: string // h1 de la page produit
  lead: string
  contents: string[] // contenu exact du ZIP livré
  situations?: [string, string][] // cas concrets (packs métier)
  forWho: string[]
  seoTitle: string
  seoDescription: string
}

const BASE = [
  'Guide « Facture électronique 2027 : le guide de survie » (PDF, 8 pages)',
  'Checklist « Prêt pour 2027 ? » à imprimer (PDF)',
  'Modèle de facture conforme avec les 4 nouvelles mentions (Excel)',
]
const KIT = 'Kit de suivi Excel : checklist, clients + contrôle SIREN, factures émises et reçues, synthèse e-reporting, comparatif plateformes'

export const FE_PACKS: FePack[] = [
  {
    slug: 'pack-starter', kind: 'base', tag: 'Pour démarrer', name: 'Pack Starter', price: 29,
    short: 'L’essentiel pour comprendre la réforme et préparer vos factures en une soirée.',
    title: 'Comprendre la facture électronique 2027 en une soirée.',
    lead: 'Un guide clair, une checklist à cocher et un modèle de facture déjà conforme. Sans jargon, sans abonnement.',
    contents: BASE,
    forWho: ['Micro-entrepreneurs', 'Indépendants qui facturent peu', 'Ceux qui veulent juste savoir quoi faire'],
    seoTitle: 'Pack Starter facture électronique 2027 : guide + checklist + modèle | 29 €',
    seoDescription: 'Guide PDF, checklist et modèle de facture conforme 2027 (SIREN client, catégorie d’opération…) pour TPE et micro-entrepreneurs. 29 € HT, téléchargement immédiat.',
  },
  {
    slug: 'taxi-vtc', kind: 'metier', tag: 'Pack métier', name: 'Pack Taxi & VTC', price: 49,
    short: 'Courses particuliers, comptes entreprises, hôtels, transport CPAM : chaque cas expliqué.',
    title: 'Taxi ou VTC : vos factures prêtes pour septembre 2027.',
    lead: 'Vous facturez des particuliers, des entreprises et parfois l’Assurance Maladie. Ce pack vous dit exactement ce qui change pour chaque type de course.',
    contents: ['Guide Taxi & VTC (PDF, 7 pages) avec cas concrets et exemple de facture', ...BASE, KIT],
    situations: [
      ['Course payée par un particulier', 'Pas de facture électronique : vos recettes partent en e-reporting via la plateforme.'],
      ['Compte entreprise ou hôtel', 'Facture électronique obligatoire avec le SIREN du client. Idéal : un récapitulatif mensuel.'],
      ['Transport de patients (CPAM)', 'Le circuit Assurance Maladie reste à part : on vous explique quoi vérifier.'],
      ['Réservation via une plateforme', 'Qui facture qui ? On clarifie si la plateforme est votre client ou un intermédiaire.'],
    ],
    forWho: ['Taxis conventionnés ou non', 'Chauffeurs VTC', 'Petites sociétés de transport'],
    seoTitle: 'Facture électronique taxi et VTC 2027 : pack guide + modèles | 49 €',
    seoDescription: 'Ce que la facture électronique change pour les taxis et VTC : courses particuliers, comptes entreprises, CPAM. Guide métier, checklist, modèle et kit Excel. 49 € HT.',
  },
  {
    slug: 'artisan-batiment', kind: 'metier', tag: 'Pack métier', gold: true, name: 'Pack Artisan du bâtiment', price: 49,
    short: 'Particuliers, sous-traitance, syndics, acomptes et situations de travaux.',
    title: 'Artisan du bâtiment : passez à la facture électronique sans y laisser vos soirées.',
    lead: 'Plombier, électricien, maçon, peintre, menuisier : entre devis, acomptes, situations et autoliquidation, ce pack vous montre ce qui change chantier par chantier.',
    contents: ['Guide Artisans du bâtiment (PDF, 7 pages) avec cas concrets et exemple de facture', ...BASE, KIT],
    situations: [
      ['Chantier chez un particulier', 'Pas d’e-invoicing, mais e-reporting. Votre facture classique reste due.'],
      ['Sous-traitance', 'Facture électronique obligatoire + mention d’autoliquidation de la TVA.'],
      ['Syndic ou bailleur', 'Facture électronique si le client est assujetti : vérifiez son SIREN.'],
      ['Acomptes et situations', 'Chaque facture passe par la plateforme : choisissez un outil qui gère les situations.'],
    ],
    forWho: ['Artisans du second œuvre', 'Entreprises du gros œuvre', 'Sous-traitants BTP'],
    seoTitle: 'Facture électronique artisan du bâtiment 2027 : pack complet | 49 €',
    seoDescription: 'Facture électronique pour artisans BTP : sous-traitance et autoliquidation, acomptes, situations, adresse de chantier. Guide métier, checklist, modèle et kit Excel. 49 € HT.',
  },
  {
    slug: 'profession-liberale', kind: 'metier', tag: 'Pack métier', name: 'Pack Profession libérale', price: 49,
    short: 'Patients et clients particuliers, interventions en entreprise, activité mixte.',
    title: 'Profession libérale : ce que la facture électronique change vraiment pour vous.',
    lead: 'Kiné, ostéo, psychologue, coach, consultant : vos patients sont surtout des particuliers, mais vos missions en entreprise, elles, basculent en 2027.',
    contents: ['Guide Professions libérales (PDF, 7 pages) avec cas concrets et exemple de facture', ...BASE, KIT],
    situations: [
      ['Patient ou client particulier', 'Pas de facture électronique, mais des données de recettes à transmettre selon votre situation.'],
      ['Intervention en entreprise', 'Facture électronique obligatoire avec le SIREN du client.'],
      ['Actes remboursés', 'Les circuits SESAM-Vitale restent distincts de la réforme.'],
      ['Activité mixte', 'Séparez bien vos flux particuliers et entreprises dans votre outil.'],
    ],
    forWho: ['Professions de santé libérales', 'Coachs et consultants', 'Architectes et bureaux d’études'],
    seoTitle: 'Facture électronique profession libérale 2027 : kiné, ostéo, consultant | 49 €',
    seoDescription: 'Facture électronique pour professions libérales : patients particuliers, missions en entreprise, activité mixte. Guide métier, checklist, modèle et kit Excel. 49 € HT.',
  },
  {
    slug: 'commercant', kind: 'metier', tag: 'Pack métier', name: 'Pack Commerçant', price: 49,
    short: 'Ventes en caisse, commandes pro, vente en ligne, factures fournisseurs.',
    title: 'Commerçant : votre caisse, vos clients pros et la facture électronique.',
    lead: 'Boutique, restaurant, boulangerie, e-commerce : l’essentiel de vos ventes reste en caisse, mais vos commandes pros et vos fournisseurs basculent.',
    contents: ['Guide Commerçants (PDF, 7 pages) avec cas concrets et exemple de facture', ...BASE, KIT],
    situations: [
      ['Vente en caisse à un particulier', 'Pas d’e-invoicing : vos totaux partent en e-reporting.'],
      ['Commande d’un professionnel', 'Facture électronique obligatoire : demandez le SIREN dès le devis.'],
      ['Vente en ligne à l’étranger', 'E-reporting des opérations internationales.'],
      ['Factures fournisseurs', 'Vous les recevez déjà sur votre plateforme depuis septembre 2026.'],
    ],
    forWho: ['Commerces de proximité', 'Restaurateurs et traiteurs', 'E-commerçants'],
    seoTitle: 'Facture électronique commerçant 2027 : caisse, clients pros, e-reporting | 49 €',
    seoDescription: 'Facture électronique pour commerçants : ventes en caisse, commandes pros, vente en ligne, fournisseurs. Guide métier, checklist, modèle et kit Excel. 49 € HT.',
  },
  {
    slug: 'pack-automatisation', kind: 'pro', tag: 'Pour aller plus loin', name: 'Pack Automatisation', price: 89,
    short: 'Moins de saisie : 5 scénarios Make / Zapier + Notion autour de votre plateforme.',
    title: 'Automatisez votre facturation sans écrire une ligne de code.',
    lead: 'Devis accepté → brouillon de facture, contrôle SIREN automatique, relances d’impayés, tableau de bord mensuel : 5 scénarios prêts à reproduire.',
    contents: ['Guide « Automatiser sa facturation sans coder » (PDF) : 5 scénarios Make/Zapier + structure Notion', KIT, 'Modèle de facture conforme (Excel)', 'Checklist « Prêt pour 2027 ? » (PDF)'],
    forWho: ['Indépendants à l’aise avec les outils en ligne', 'TPE avec beaucoup de factures', 'Ceux qui détestent la saisie'],
    seoTitle: 'Automatiser sa facturation électronique avec Make, Zapier et Notion | 89 €',
    seoDescription: '5 scénarios no-code pour automatiser devis, contrôle SIREN, relances et suivi autour de votre plateforme agréée. Guide PDF + kit Excel. 89 € HT.',
  },
  {
    slug: 'pack-complet-zero-stress', kind: 'pro', tag: 'Meilleure offre', gold: true, name: 'Pack Complet « Zéro Stress 2027 »', price: 147,
    short: 'Tout : guide, 4 guides métier, automatisation, modèles, kit Excel et mises à jour 12 mois.',
    title: 'Tout ce qu’il faut pour être prêt en 2027. Et rester à jour.',
    lead: 'Le guide complet, les 4 guides métier, le pack automatisation, tous les modèles Excel, et les mises à jour envoyées par email pendant 12 mois si les règles changent.',
    contents: [...BASE, 'Les 4 guides métier : Taxi & VTC, Bâtiment, Profession libérale, Commerçant (PDF)', 'Guide « Automatiser sa facturation sans coder » (PDF)', KIT, 'Mises à jour pendant 12 mois, envoyées par email'],
    forWho: ['Entreprises à plusieurs activités', 'Comptables et conseillers qui accompagnent des TPE', 'Ceux qui veulent tout, une fois pour toutes'],
    seoTitle: 'Pack complet facture électronique 2027 « Zéro Stress » : tous les guides | 147 €',
    seoDescription: 'Le pack le plus complet : guide 2027, 4 guides métier, automatisation no-code, modèles et kit Excel, mises à jour 12 mois. 147 € HT, téléchargement immédiat.',
  },
]

export const FE_FAQ: [string, string][] = [
  ['Je suis micro-entrepreneur en franchise de TVA, suis-je concerné ?', 'Oui. La franchise vous dispense de facturer la TVA, pas de la réforme : réception des factures électroniques depuis le 1er septembre 2026, émission au 1er septembre 2027.'],
  ['Qu’est-ce que je reçois exactement ?', 'Un fichier ZIP téléchargeable avec des guides PDF et des modèles Excel, prêts à utiliser. Le contenu exact est listé sur la page de chaque pack.'],
  ['Est-ce que ça remplace une plateforme agréée ?', 'Non. La loi impose une plateforme agréée pour émettre vos factures. Nos packs vous aident à comprendre, choisir la bonne et préparer vos données. Plusieurs plateformes ont des offres gratuites pour les micro-entrepreneurs.'],
  ['Les informations sont-elles à jour ?', 'Édition de novembre 2026, intégrant les sanctions de la loi de finances 2026. Le pack Complet inclut 12 mois de mises à jour. Ces documents restent des informations générales et ne remplacent pas votre comptable.'],
  ['Je peux avoir une facture ?', 'Oui, une facture au nom de votre entreprise est envoyée automatiquement après le paiement.'],
  ['Et si la date de 2027 est reportée ?', 'Le travail de préparation (SIREN clients, modèles, choix de la plateforme) reste utile dans tous les cas : vous serez prêt plus tôt.'],
]
