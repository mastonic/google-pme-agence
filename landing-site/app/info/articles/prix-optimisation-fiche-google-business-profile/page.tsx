import type { Metadata } from 'next'
import { ArticleLayout, metaFor, type Section, type Source } from '../../../components/ArticleLayout'
import { siteHref } from '../../../seo/domains'
import { PACKS_HT } from '../../../seo/offers'
import { pageMeta } from '../../../seo/seo'

const SLUG = 'prix-optimisation-fiche-google-business-profile'
export const metadata: Metadata = pageMeta(metaFor(SLUG))

const SOURCES: Source[] = [
  ['Google, « Ajouter ou revendiquer votre fiche d’établissement » (service gratuit)', 'https://support.google.com/business/answer/2911778'],
  ['Google, « Valider votre établissement sur Google »', 'https://support.google.com/business/answer/7107242'],
  ['Google, « Conseils pour améliorer votre classement local sur Google »', 'https://support.google.com/business/answer/7091'],
  ['Google, consignes de représentation des établissements', 'https://support.google.com/business/answer/3038177'],
  ['Web Ranker, « Agence web Yvelines (78) », tarifs publics consultés le 8 novembre 2026', 'https://webranker.fr/agence-web-yvelines'],
  ['ComeUp, catégorie « Google My Business », offres de freelances consultées le 8 novembre 2026', 'https://comeup.com/categorie/google-my-business'],
]

const SECTIONS: Section[] = [
  {
    id: 'gratuit', title: 'La fiche est gratuite, l’optimisation est un travail',
    body: (<>
      <p>Créer et gérer une fiche Google Business Profile ne coûte rien chez Google [1]. Ce que l’on paie à un prestataire, c’est le temps passé à la compléter, à la corriger et à la faire vivre, ainsi que son expérience des règles de Google [4].</p>
    </>),
  },
  {
    id: 'actions', title: 'Les actions réalisées lors d’une optimisation',
    body: (<>
      <ul>
        <li>Revendication et validation de la fiche si nécessaire [1][2].</li>
        <li>Choix de la catégorie principale et des catégories secondaires.</li>
        <li>Nom conforme aux consignes, description locale, attributs.</li>
        <li>Adresse ou zone de service, horaires et horaires spéciaux.</li>
        <li>Liste des services ou produits, avec descriptions.</li>
        <li>Photos réelles, publications.</li>
        <li>Mise en place d’une méthode de demande d’avis et de réponse aux avis.</li>
        <li>Vérification de la cohérence avec le site et les annuaires.</li>
      </ul>
    </>),
  },
  {
    id: 'prix-releves', title: 'Les prix publics relevés',
    body: (<>
      <div className="table-wrap">
        <table className="seo-table">
          <caption>Exemples de prix publics consultés le 8 novembre 2026</caption>
          <thead><tr><th scope="col">Type d’offre</th><th scope="col">Prix</th><th scope="col">Source</th></tr></thead>
          <tbody>
            <tr><th scope="row">Freelances (plateforme ComeUp), prix de départ affichés</th><td>de 18,15 $US à 1 076,70 $US selon les offres</td><td>[6]</td></tr>
            <tr><th scope="row">Agence web Yvelines, gestion de fiche</th><td>89 € HT / mois + 149 € HT de mise en service</td><td>[5]</td></tr>
            <tr><th scope="row">Pulse Locale PME, pack unique</th><td>{PACKS_HT.ficheGoogle.price} € HT, une fois</td><td>Boutique</td></tr>
          </tbody>
        </table>
      </div>
      <p>Ces écarts s’expliquent par des contenus très différents : simple réglage ponctuel, accompagnement mensuel, rédaction, photos, gestion des avis.</p>
    </>),
  },
  {
    id: 'facteurs', title: 'Ce qui fait varier le prix',
    body: (<>
      <ul>
        <li><strong>Ponctuel ou mensuel</strong> : une optimisation unique ou un suivi continu (publications, avis, statistiques).</li>
        <li><strong>État de départ</strong> : fiche à créer, à récupérer, en double ou suspendue.</li>
        <li><strong>Nombre de services et de photos</strong> à produire.</li>
        <li><strong>Livrables</strong> : rapport avant/après, publications rédigées, méthode d’avis.</li>
      </ul>
    </>),
  },
  {
    id: 'delais', title: 'Délais',
    body: (<>
      <p>La mise à jour d’une fiche prend quelques jours ; la validation par Google peut demander davantage selon la méthode exigée [2]. Les effets sur la visibilité se mesurent ensuite sur plusieurs semaines, car le classement dépend aussi de la distance et de la notoriété [3].</p>
    </>),
  },
  {
    id: 'livrables', title: 'Les livrables à exiger',
    body: (<>
      <ul>
        <li>La liste des modifications réalisées.</li>
        <li>Une capture ou un rapport avant / après.</li>
        <li>Les accès qui restent à votre nom : vous devez rester propriétaire de la fiche.</li>
        <li>Une méthode simple pour continuer seul (avis, photos, publications).</li>
      </ul>
    </>),
  },
  {
    id: 'limites', title: 'Les limites',
    body: (<>
      <p>Aucune optimisation ne garantit une position : Google rappelle qu’on ne peut pas payer pour un meilleur classement local [3]. Une fiche parfaite pour une entreprise éloignée du client restera derrière une fiche correcte plus proche. Et les avis ne s’achètent pas : les contreparties sont interdites.</p>
    </>),
  },
  {
    id: 'offre', title: 'L’offre Pulse Locale PME à 149 € HT',
    body: (<>
      <p>Le pack Fiche Google optimisée est vendu {PACKS_HT.ficheGoogle.price} € HT, une seule fois, livré en {PACKS_HT.ficheGoogle.delay} : catégories, description locale, photos, services, publications et rapport avant/après. Si vous passez en formule Pro dans les 30 jours, ce montant est déduit de votre premier mois. <a href={siteHref(PACKS_HT.ficheGoogle.path)} className="link-underline">Voir le détail du pack</a>.</p>
    </>),
  },
]

const FAQS: [string, string][] = [
  ['Peut-on optimiser sa fiche Google soi-même ?', 'Oui, tout se fait gratuitement depuis l’espace Google Business Profile. Un prestataire fait gagner du temps et évite les erreurs (nom avec mots-clés, mauvaise catégorie, zone trop large).'],
  ['Faut-il un abonnement pour optimiser sa fiche Google ?', 'Non. Une optimisation ponctuelle suffit souvent pour corriger les bases. Un suivi mensuel est utile si vous voulez publier régulièrement et gérer les avis.'],
  ['Une agence peut-elle garantir la première place sur Google Maps ?', 'Non. Google indique qu’il est impossible de payer pour un meilleur classement local. Méfiez-vous de ce type de promesse.'],
  ['Qui reste propriétaire de la fiche ?', 'Vous. Le prestataire peut être ajouté comme gestionnaire, mais la propriété doit rester à votre nom.'],
]

export default function Page() {
  return (
    <ArticleLayout
      slug={SLUG}
      answer="La fiche Google Business Profile est gratuite ; c’est le travail d’optimisation que l’on paie. Les offres publiques relevées vont de moins de 20 $US à plus de 1 000 $US chez des freelances, et jusqu’à des suivis mensuels de 89 € HT par mois en agence. Pulse Locale PME propose une optimisation complète en une fois à 149 € HT, livrée en 5 jours ouvrés. Aucune offre ne peut garantir une position sur Google Maps."
      sections={SECTIONS}
      faqs={FAQS}
      sources={SOURCES}
      related={['visibilite-google-maps-chartres', 'prix-site-internet-artisan-yvelines']}
    />
  )
}
