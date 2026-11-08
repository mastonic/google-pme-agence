import type { Metadata } from 'next'
import { ArticleLayout, metaFor, type Section, type Source } from '../../../components/ArticleLayout'
import { PricingTable } from '../../../components/Pricing'
import { siteHref } from '../../../seo/domains'
import { pageMeta } from '../../../seo/seo'

const SLUG = 'prix-site-internet-artisan-yvelines'
export const metadata: Metadata = pageMeta(metaFor(SLUG))

const SOURCES: Source[] = [
  ['Web Ranker, « Agence web Yvelines (78) », tarifs publics consultés le 8 novembre 2026', 'https://webranker.fr/agence-web-yvelines'],
  ['Dix Mille Heures, comparatif des agences web de Saint-Germain-en-Laye, consulté le 8 novembre 2026', 'https://www.dixmilleheures.fr/articles/agences-web-saint-germain-en-laye'],
  ['Refonte Up, « Consultant SEO 78 (Yvelines) pour artisans », consulté le 8 novembre 2026', 'https://refonte-up.fr/agence-seo/yvelines/'],
  ['Google, « Do you need an SEO? » (Search Central)', 'https://developers.google.com/search/docs/fundamentals/do-i-need-seo'],
]

const SECTIONS: Section[] = [
  {
    id: 'deux-modeles', title: 'Deux façons de payer un site : à l’achat ou en abonnement',
    body: (<>
      <p>Un site internet d’artisan se paie de deux manières. <strong>À l’achat</strong>, vous réglez la création en une fois, puis vous payez séparément l’hébergement, le nom de domaine et la maintenance. <strong>En abonnement</strong>, vous payez un montant mensuel qui inclut la création, l’hébergement et la maintenance, sans grosse somme au départ.</p>
      <p>Aucun modèle n’est meilleur dans l’absolu : l’achat convient si vous voulez être propriétaire d’un site que vous ferez évoluer vous-même ; l’abonnement convient si vous voulez un site tenu à jour sans vous en occuper. Avant de comparer des prix, vérifiez toujours ce qui est inclus, et ce qui se passe si vous arrêtez.</p>
    </>),
  },
  {
    id: 'prix-releves', title: 'Les prix publics relevés dans les Yvelines',
    body: (<>
      <p>Les prix ci-dessous sont des offres publiques d’agences et de prestataires intervenant dans les Yvelines, relevées le 8 novembre 2026. Ils évoluent : vérifiez-les auprès de chaque prestataire.</p>
      <div className="table-wrap">
        <table className="seo-table">
          <caption>Exemples de prix publics (hors taxes sauf mention contraire)</caption>
          <thead><tr><th scope="col">Prestation</th><th scope="col">Prix public relevé</th><th scope="col">Source</th></tr></thead>
          <tbody>
            <tr><th scope="row">Site vitrine 5 pages (achat)</th><td>1 490 € HT</td><td>[1]</td></tr>
            <tr><th scope="row">Site vitrine 5 pages (abonnement)</th><td>149 € HT / mois</td><td>[1]</td></tr>
            <tr><th scope="row">Site jusqu’à 10 pages avec fiche Google</th><td>2 490 € HT ou 279 € HT / mois</td><td>[1]</td></tr>
            <tr><th scope="row">Site vitrine (agence près de Saint-Germain-en-Laye)</th><td>à partir de 990 € HT</td><td>[2]</td></tr>
            <tr><th scope="row">Maintenance</th><td>à partir de 50 € HT / mois</td><td>[1]</td></tr>
            <tr><th scope="row">Suivi SEO local mensuel (consultant)</th><td>à partir de 247 € / mois</td><td>[3]</td></tr>
            <tr><th scope="row">Boutique en ligne (e-commerce)</th><td>sur devis</td><td>[1]</td></tr>
          </tbody>
        </table>
      </div>
      <p>Ces exemples ne constituent pas une étude de marché : ils montrent l’ordre de grandeur des offres publiques consultées, à prestations différentes.</p>
    </>),
  },
  {
    id: 'vitrine-ecommerce', title: 'Site vitrine ou e-commerce : ce qui change le prix',
    body: (<>
      <p>Un <strong>site vitrine</strong> présente votre activité : services, zone d’intervention, réalisations, horaires, contact. C’est le besoin de la grande majorité des artisans. Un <strong>site e-commerce</strong> permet de vendre en ligne : catalogue, paiement, livraison, stocks, conditions générales de vente. Il demande plus de développement, plus de maintenance et des obligations supplémentaires, d’où des prix généralement sur devis.</p>
      <p>Pour un plombier, un électricien ou un coiffeur, la question n’est presque jamais l’e-commerce : c’est d’être trouvé localement et joignable.</p>
    </>),
  },
  {
    id: 'frais-recurrents', title: 'Les frais récurrents à ne pas oublier',
    body: (<>
      <ul>
        <li><strong>Nom de domaine</strong> : renouvelé chaque année.</li>
        <li><strong>Hébergement et certificat SSL</strong> : indispensables pour que le site reste en ligne et sécurisé (https).</li>
        <li><strong>Maintenance</strong> : mises à jour techniques, sauvegardes, correctifs de sécurité.</li>
        <li><strong>Modifications</strong> : nouveaux services, photos, horaires. Vérifiez combien sont incluses.</li>
        <li><strong>Référencement</strong> : la mise en ligne ne suffit pas pour être trouvé ; le suivi de la fiche Google et des contenus a un coût, interne ou externe.</li>
      </ul>
      <p>Comparez toujours un coût sur 12 ou 24 mois, pas seulement le prix affiché le premier mois.</p>
    </>),
  },
  {
    id: 'maintenance', title: 'Maintenance : ce qu’elle doit couvrir',
    body: (<>
      <p>Une maintenance utile couvre au minimum les mises à jour de sécurité, les sauvegardes, la surveillance de la disponibilité et le renouvellement du certificat. Demandez par écrit le délai d’intervention en cas de panne, le nombre de modifications incluses et la manière de récupérer votre contenu si vous partez.</p>
    </>),
  },
  {
    id: 'tarifs-pulse', title: 'Les tarifs Pulse Locale PME',
    body: (<>
      <p>Pulse Locale PME fonctionne en abonnement, sans frais de création, avec une démonstration de votre futur site avant tout paiement. Les tarifs sont identiques dans les Yvelines, en Eure-et-Loir et partout en France.</p>
      <PricingTable />
    </>),
  },
  {
    id: 'comparatif', title: 'Tableau comparatif transparent',
    body: (<>
      <div className="table-wrap">
        <table className="seo-table">
          <caption>Comparer à prestations équivalentes : les questions à se poser</caption>
          <thead><tr><th scope="col">Critère</th><th scope="col">Site à l’achat</th><th scope="col">Site en abonnement</th></tr></thead>
          <tbody>
            <tr><th scope="row">Dépense au départ</th><td>Élevée (création)</td><td>Faible ou nulle</td></tr>
            <tr><th scope="row">Coût sur 24 mois</th><td>Création + hébergement + maintenance</td><td>24 mensualités, tout compris</td></tr>
            <tr><th scope="row">Mises à jour</th><td>À organiser vous-même ou en option</td><td>Incluses dans la limite du forfait</td></tr>
            <tr><th scope="row">Si vous arrêtez</th><td>Le site vous appartient, à héberger ailleurs</td><td>À vérifier dans le contrat (récupération du contenu, du domaine)</td></tr>
            <tr><th scope="row">Pour qui</th><td>Projet stable, budget disponible</td><td>Besoin d’un site suivi, trésorerie à préserver</td></tr>
          </tbody>
        </table>
      </div>
      <p>Chez Pulse Locale PME, la formule Starter à 49 € HT par mois représente 1 176 € HT sur 24 mois (ou 980 € HT en paiement annuel), hébergement, SSL et maintenance compris. Les formules Pro et Élite ajoutent le référencement local et la réceptionniste IA.</p>
    </>),
  },
]

const FAQS: [string, string][] = [
  ['Quel est le prix moyen d’un site vitrine pour artisan dans les Yvelines ?', 'Nous ne publions pas de moyenne faute d’étude représentative. Les offres publiques relevées le 8 novembre 2026 vont d’environ 990 € HT à 2 490 € HT à l’achat selon le nombre de pages, ou de 49 € HT à 279 € HT par mois en abonnement selon les services inclus.'],
  ['Un site à 0 € de création est-il gratuit ?', 'Non : le coût est étalé dans l’abonnement mensuel. Comparez le total sur 12 ou 24 mois et vérifiez les conditions d’arrêt.'],
  ['Le référencement est-il inclus dans le prix d’un site ?', 'Rarement au-delà des bases techniques. Le suivi de la fiche Google et des contenus locaux est souvent une prestation à part. Chez Pulse Locale PME, il est inclus à partir de la formule Pro.'],
  ['Puis-je voir le site avant de payer ?', 'Chez Pulse Locale PME, oui : une démonstration personnalisée est offerte avant tout paiement.'],
]

export default function Page() {
  return (
    <ArticleLayout
      slug={SLUG}
      answer="Dans les Yvelines, les offres publiques relevées en novembre 2026 placent un site vitrine d’artisan entre environ 990 € et 2 490 € HT à l’achat, ou entre 49 € et 279 € HT par mois en abonnement selon les services inclus. À cela s’ajoutent nom de domaine, hébergement et maintenance si vous achetez. Comparez toujours le coût total sur 24 mois et ce qui est réellement inclus."
      sections={SECTIONS}
      faqs={FAQS}
      sources={SOURCES}
      related={['choisir-agence-seo-local-yvelines', 'prix-optimisation-fiche-google-business-profile']}
      cta={<div className="callout dark"><strong className="mont" style={{ fontSize: 20 }}>Voir votre site avant de payer</strong><p>Démonstration gratuite et sans engagement de votre futur site.</p><div className="hero-ctas"><a href={siteHref('/agence-seo-local-yvelines/')} className="btn btn-primary btn-sm">Notre accompagnement dans les Yvelines →</a><a href={siteHref('/#offres')} className="btn btn-ghost btn-sm">Voir les formules</a></div></div>}
    />
  )
}
