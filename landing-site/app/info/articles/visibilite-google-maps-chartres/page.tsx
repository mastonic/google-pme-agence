import type { Metadata } from 'next'
import { ArticleLayout, metaFor, type Section, type Source } from '../../../components/ArticleLayout'
import { siteHref } from '../../../seo/domains'
import { pageMeta } from '../../../seo/seo'

const SLUG = 'visibilite-google-maps-chartres'
export const metadata: Metadata = pageMeta(metaFor(SLUG))

const SOURCES: Source[] = [
  ['Google, « Conseils pour améliorer votre classement local sur Google »', 'https://support.google.com/business/answer/7091'],
  ['Google, « Consignes relatives à la représentation de votre établissement sur Google »', 'https://support.google.com/business/answer/3038177'],
  ['Google, « Gérer votre zone de service »', 'https://support.google.com/business/answer/9157481'],
  ['Google, « Conseils pour obtenir plus d’avis »', 'https://support.google.com/business/answer/3474122'],
  ['Google Maps, règles relatives aux contenus interdits et restreints (faux avis)', 'https://support.google.com/contributionpolicy/answer/7400114'],
  ['Google, « Ajouter ou revendiquer votre fiche d’établissement »', 'https://support.google.com/business/answer/2911778'],
]

const SECTIONS: Section[] = [
  {
    id: 'comment-google-classe', title: 'Comment Google classe les entreprises sur la carte',
    body: (<>
      <p>Google indique que les résultats locaux reposent principalement sur trois critères : la <strong>pertinence</strong> (votre fiche correspond-elle à la recherche ?), la <strong>distance</strong> (êtes-vous proche de la personne ou du lieu recherché ?) et la <strong>notoriété</strong> (votre entreprise est-elle connue, citée, bien notée ?) [1]. Google précise aussi qu’il est impossible de payer pour un meilleur classement local [1].</p>
      <p>Vous ne contrôlez pas la distance. En revanche, la pertinence et la notoriété dépendent largement de votre fiche, de vos avis et de la cohérence de vos informations.</p>
    </>),
  },
  {
    id: 'fiche', title: 'Étape 1 : revendiquer et compléter la fiche Google Business Profile',
    body: (<>
      <p>Commencez par vérifier que vous êtes bien le propriétaire de votre fiche [6]. Une fiche non revendiquée peut être modifiée par des tiers et vous ne pouvez ni répondre aux avis ni publier.</p>
      <p>Le nom doit être celui de votre entreprise, sans mots-clés ajoutés (« Plomberie Martin », pas « Plombier Chartres pas cher Martin ») : Google l’exige dans ses consignes [2].</p>
    </>),
  },
  {
    id: 'categories', title: 'Étape 2 : choisir les bonnes catégories',
    body: (<>
      <p>La catégorie principale est le réglage le plus structurant : choisissez la plus précise qui décrit votre activité principale. Ajoutez ensuite des catégories secondaires uniquement pour des activités réellement exercées. Une catégorie trop large vous met en concurrence avec tout le monde ; une catégorie inexacte vous fait apparaître sur des recherches qui ne vous apporteront rien.</p>
    </>),
  },
  {
    id: 'zone', title: 'Étape 3 : régler adresse et zone d’intervention autour de Chartres',
    body: (<>
      <p>Si vous recevez vos clients (salon, restaurant, boutique), affichez votre adresse exacte. Si vous vous déplacez chez eux et ne les recevez pas, Google demande de retirer l’adresse et de définir une zone de service, qui ne doit pas dépasser environ deux heures de route depuis votre base [3].</p>
      <p>Autour de Chartres, déclarez les communes réellement desservies, par exemple Lucé, Mainvilliers, Lèves, Luisant ou Champhol, plutôt qu’un département entier. Une zone crédible vaut mieux qu’une zone immense.</p>
    </>),
  },
  {
    id: 'services-photos', title: 'Étape 4 : services, photos et horaires',
    body: (<>
      <ul>
        <li><strong>Services</strong> : listez chaque prestation avec une description simple, dans les mots de vos clients.</li>
        <li><strong>Photos</strong> : publiez des photos réelles et récentes (vitrine, équipe, réalisations, véhicule). Évitez les images de banque d’images.</li>
        <li><strong>Horaires</strong> : tenez à jour les horaires spéciaux (jours fériés, congés). Un client qui trouve porte close laisse souvent un avis négatif.</li>
        <li><strong>Publications</strong> : une actualité, une offre ou une réalisation de temps en temps montre que la fiche est active.</li>
      </ul>
      <p>Pour un restaurant ou un hébergement proche de la cathédrale, les photos et les horaires de saison sont souvent les premiers éléments consultés par les visiteurs.</p>
    </>),
  },
  {
    id: 'avis', title: 'Étape 5 : obtenir des avis authentiques',
    body: (<>
      <p>Google recommande de demander des avis à vos clients, par exemple avec un lien ou un QR code [4]. En revanche, offrir une contrepartie (remise, cadeau) en échange d’un avis est interdit et considéré comme un contenu faux et trompeur [4][5]. N’achetez jamais d’avis : en plus du risque de sanction, ils sont inutiles pour gagner la confiance des clients.</p>
      <p>Répondez à chaque avis, positif comme négatif, de façon précise et courtoise. Les réponses sont lues par les futurs clients.</p>
    </>),
  },
  {
    id: 'coherence', title: 'Étape 6 : des informations identiques partout',
    body: (<>
      <p>Votre nom, votre adresse (si affichée) et votre téléphone doivent être identiques sur votre fiche Google, votre site internet, vos pages sur les annuaires et les réseaux sociaux. Les incohérences (ancien numéro, ancienne adresse) brouillent Google comme les assistants IA qui s’appuient sur ces informations.</p>
    </>),
  },
  {
    id: 'mesure', title: 'Étape 7 : mesurer les résultats',
    body: (<>
      <p>Les statistiques de la fiche (dans l’espace de gestion Google Business Profile) indiquent le nombre de vues, d’appels, de demandes d’itinéraire et de clics vers le site. Comparez-les mois par mois plutôt que jour par jour. Notez en parallèle les demandes réellement reçues (appels, messages) : c’est ce qui compte pour votre chiffre d’affaires.</p>
      <p>Testez aussi vos recherches cibles depuis un téléphone, à plusieurs endroits de l’agglomération : les résultats changent selon la position de la personne.</p>
    </>),
  },
]

const FAQS: [string, string][] = [
  ['Combien de temps pour apparaître sur Google Maps à Chartres ?', 'Une fiche nouvellement vérifiée peut apparaître rapidement, mais gagner des places sur des recherches disputées prend généralement des semaines à des mois, selon la concurrence et le rythme des avis. Aucun prestataire ne peut garantir une position.'],
  ['Mon entreprise est à Lucé, puis-je ressortir à Chartres ?', 'Si vous vous déplacez chez vos clients, déclarez Chartres dans votre zone de service. Si vous recevez vos clients, la distance joue davantage, mais une fiche complète et bien notée peut ressortir au-delà de votre commune.'],
  ['Faut-il un site internet pour être bien classé sur Google Maps ?', 'Ce n’est pas obligatoire, mais un site cohérent avec la fiche renforce la pertinence et la confiance, et sert de source aux assistants IA.'],
  ['Puis-je créer une fiche par commune desservie ?', 'Non. Une fiche correspond à un établissement réel. Créer des fiches sans établissement est contraire aux consignes de Google et peut entraîner une suspension.'],
]

export default function Page() {
  return (
    <ArticleLayout
      slug={SLUG}
      answer="Pour être plus visible sur Google Maps à Chartres, revendiquez votre fiche Google Business Profile, choisissez la catégorie la plus précise, déclarez une zone d’intervention réaliste (Lucé, Mainvilliers, Lèves…) si vous vous déplacez, décrivez vos services, publiez des photos réelles, demandez des avis authentiques sans contrepartie et gardez des informations identiques partout. Google classe selon la pertinence, la distance et la notoriété ; personne ne peut payer pour un meilleur classement."
      sections={SECTIONS}
      faqs={FAQS}
      sources={SOURCES}
      related={['prix-optimisation-fiche-google-business-profile', 'apparaitre-chatgpt-gemini-perplexity']}
      cta={<div className="callout dark"><strong className="mont" style={{ fontSize: 20 }}>Vous êtes en Eure-et-Loir ?</strong><p>Fiche Google, site et réceptionniste IA pour les entreprises de Chartres, Dreux et du 28.</p><div className="hero-ctas"><a href={siteHref('/agence-seo-local-eure-et-loir/')} className="btn btn-primary btn-sm">Notre accompagnement en Eure-et-Loir →</a><a href={siteHref('/store/fiche-google-optimisee/')} className="btn btn-ghost btn-sm">Pack Fiche Google à 149 € HT</a></div></div>}
    />
  )
}
