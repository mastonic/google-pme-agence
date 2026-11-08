import type { Metadata } from 'next'
import { ArticleLayout, metaFor, type Section, type Source } from '../../../components/ArticleLayout'
import { siteHref } from '../../../seo/domains'
import { pageMeta } from '../../../seo/seo'

const SLUG = 'choisir-agence-seo-local-yvelines'
export const metadata: Metadata = pageMeta(metaFor(SLUG))

const SOURCES: Source[] = [
  ['Google, « Do you need an SEO? Tips for hiring an SEO » (Search Central)', 'https://developers.google.com/search/docs/fundamentals/do-i-need-seo'],
  ['Google, « Google Search Essentials » (consignes)', 'https://developers.google.com/search/docs/essentials'],
  ['Google, « Conseils pour améliorer votre classement local sur Google »', 'https://support.google.com/business/answer/7091'],
  ['Google Maps, règles relatives aux faux contenus et avis', 'https://support.google.com/contributionpolicy/answer/7400114'],
]

const SECTIONS: Section[] = [
  {
    id: 'besoin', title: 'Commencer par votre besoin, pas par l’agence',
    body: (<>
      <p>Avant de comparer des prestataires, écrivez en trois lignes ce que vous attendez : plus d’appels ? être visible dans quelles communes (Versailles, Montigny-le-Bretonneux, Trappes, Poissy…) ? un nouveau site ou seulement la fiche Google ? Un bon prestataire vous posera de lui-même ces questions, ainsi que : qui sont vos concurrents, comment vos clients vous trouvent aujourd’hui, ce qui vous distingue [1].</p>
    </>),
  },
  {
    id: 'criteres', title: 'Les critères de sélection',
    body: (<>
      <ul>
        <li><strong>Expérience locale et métier</strong> : a-t-il accompagné des entreprises comparables, dans des secteurs comparables ? Demandez des exemples vérifiables [1].</li>
        <li><strong>Méthode écrite</strong> : audit, priorités, calendrier, indicateurs suivis.</li>
        <li><strong>Respect des consignes de Google</strong> : un prestataire sérieux s’y réfère explicitement [1][2].</li>
        <li><strong>Transparence</strong> : il vous dit ce qu’il modifie, sur votre site comme sur votre fiche [1].</li>
        <li><strong>Propriété</strong> : votre fiche Google, votre nom de domaine et vos comptes (Search Console, statistiques) restent à votre nom.</li>
      </ul>
    </>),
  },
  {
    id: 'questions', title: 'Les questions à poser avant de signer',
    body: (<>
      <ol>
        <li>Pouvez-vous me montrer des réalisations et des résultats que je peux vérifier ?</li>
        <li>Quels résultats attendez-vous, dans quel délai, et comment les mesurez-vous ?</li>
        <li>Que faites-vous concrètement chaque mois ?</li>
        <li>Qui sera mon interlocuteur et comment communique-t-on ?</li>
        <li>Allez-vous me communiquer toutes les modifications effectuées ?</li>
        <li>Que se passe-t-il si j’arrête, et que puis-je récupérer (site, contenus, accès) ?</li>
      </ol>
      <p>Ces questions reprennent pour l’essentiel celles que Google recommande de poser à un prestataire SEO [1].</p>
    </>),
  },
  {
    id: 'livrables', title: 'Les livrables à exiger',
    body: (<>
      <ul>
        <li>Un audit initial écrit (fiche Google, site, concurrence locale, priorités).</li>
        <li>La liste des actions réalisées chaque mois.</li>
        <li>Un rapport régulier : appels, demandes, visibilité de la fiche, positions sur quelques recherches clés.</li>
        <li>Les accès à vos outils (fiche Google, Search Console) à votre nom.</li>
      </ul>
    </>),
  },
  {
    id: 'contrat', title: 'Contrat et transparence des prix',
    body: (<>
      <p>Lisez la durée d’engagement, les conditions de résiliation, ce qui est inclus dans le forfait (nombre de contenus, de modifications), les frais annexes et la propriété des livrables. Un prix affiché « à partir de » doit être accompagné de ce qu’il comprend. Méfiez-vous d’un devis qui ne détaille rien.</p>
      <p>Pulse Locale PME affiche ses tarifs publiquement (dès 49 € HT par mois, sans engagement en mensuel) et les conditions sont présentées avant tout paiement : <a href={siteHref('/#offres')} className="link-underline">voir les formules</a>.</p>
    </>),
  },
  {
    id: 'alertes', title: 'Les signaux d’alerte',
    body: (<>
      <ul>
        <li><strong>Une garantie de première position</strong> : « personne ne peut garantir une première place sur Google », écrit Google [1].</li>
        <li><strong>Un « partenariat privilégié » avec Google</strong> pour mieux vous classer : il est impossible de payer pour un meilleur classement local [3].</li>
        <li><strong>Des avis achetés ou des faux avis</strong> proposés : interdits et sanctionnables [4].</li>
        <li><strong>Des méthodes secrètes</strong> ou le refus d’expliquer ce qui est modifié [1].</li>
        <li><strong>Des comptes créés au nom du prestataire</strong> plutôt qu’au vôtre.</li>
        <li><strong>Des fiches Google multiples</strong> pour des adresses où vous n’avez pas d’établissement.</li>
      </ul>
    </>),
  },
  {
    id: 'methodes', title: 'Comparer les méthodes, pas seulement les prix',
    body: (<>
      <p>Les prestataires des Yvelines proposent des approches différentes : consultant indépendant avec suivi mensuel, agence web qui vend le site à l’achat, abonnement tout compris, audit ponctuel. Aucune n’est mauvaise en soi : la bonne dépend de votre budget, de votre besoin (site, fiche, contenus) et du temps que vous voulez y consacrer. Comparez à prestations équivalentes et sur la même durée.</p>
      <p>L’approche de Pulse Locale PME : un abonnement sans frais de création, une démonstration avant paiement, un travail à distance, des tarifs publics. <a href={siteHref('/methode/')} className="link-underline">Notre méthode en détail</a>.</p>
    </>),
  },
]

const FAQS: [string, string][] = [
  ['Faut-il choisir une agence installée dans les Yvelines ?', 'Pas nécessairement. La proximité peut faciliter les rencontres, mais ce qui compte est la connaissance de votre marché local, la méthode et la transparence. Beaucoup d’accompagnements se font à distance.'],
  ['Combien coûte une agence SEO local ?', 'Les offres publiques consultées vont de l’audit ponctuel à l’accompagnement mensuel, avec des écarts importants selon le contenu. Comparez ce qui est inclus et la durée d’engagement. Chez Pulse Locale PME : dès 49 € HT par mois, SEO local inclus à partir de 149 € HT.'],
  ['En combien de temps une agence obtient-elle des résultats ?', 'Les corrections de fiche sont visibles en quelques jours à quelques semaines ; la progression dans le classement se mesure plutôt en mois. Méfiez-vous des délais garantis.'],
  ['Que dois-je garder à mon nom ?', 'Votre fiche Google, votre nom de domaine, vos comptes Search Console et statistiques, et idéalement vos contenus.'],
]

export default function Page() {
  return (
    <ArticleLayout
      slug={SLUG}
      answer="Pour choisir une agence SEO local dans les Yvelines, vérifiez son expérience dans votre secteur et vos communes, demandez une méthode écrite, des exemples vérifiables et des livrables mensuels, exigez que la fiche Google et le nom de domaine restent à votre nom, et lisez les conditions d’engagement. Fuyez toute garantie de première position : Google rappelle que personne ne peut la garantir."
      sections={SECTIONS}
      faqs={FAQS}
      sources={SOURCES}
      related={['prix-site-internet-artisan-yvelines', 'apparaitre-chatgpt-gemini-perplexity']}
      cta={<div className="callout dark"><strong className="mont" style={{ fontSize: 20 }}>Comparez avec notre approche</strong><p>Tarifs publics, démonstration avant paiement, accompagnement à distance dans tout le 78.</p><div className="hero-ctas"><a href={siteHref('/agence-seo-local-yvelines/')} className="btn btn-primary btn-sm">Pulse Locale PME dans les Yvelines →</a><a href={siteHref('/info/outil-gratuit/')} className="btn btn-ghost btn-sm">Test de visibilité gratuit</a></div></div>}
    />
  )
}
