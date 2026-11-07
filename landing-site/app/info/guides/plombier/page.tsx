import type { Metadata } from 'next'
import { article, breadcrumbs, faqPage, pageMeta } from '../../../lib/seo'
import { JsonLd } from '../../../components/JsonLd'
import { SubShell } from '../../../components/SubShell'

const TITLE = 'Plombier : comment apparaître en premier sur Google Maps dans sa ville (guide 2026)'
const DESC = 'Guide pratique pour plombiers : catégories Google, zone d’intervention, services, avis et appels d’urgence. Les réglages qui font sonner le téléphone.'
const PATH = '/info/guides/plombier/'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: PATH, type: 'article' })

const FAQS: [string, string][] = [
  ['Quelle catégorie Google choisir quand on est plombier ?', 'La catégorie principale « Plombier », complétée par 2 à 4 catégories secondaires réellement exercées : chauffagiste, service de débouchage, entreprise de chauffe-eau.'],
  ['Un plombier sans local doit-il afficher son adresse sur Google ?', 'Non. Il peut se déclarer entreprise de services de proximité, masquer son adresse et indiquer les communes où il intervient.'],
  ['Combien d’avis faut-il pour bien se classer sur Google Maps ?', 'Il n’y a pas de chiffre officiel. Le plus efficace est d’avoir plus d’avis récents que vos concurrents directs, et d’y répondre systématiquement.'],
]

export default function Guide() {
  return (
    <SubShell variant="info">
      <JsonLd items={[breadcrumbs([['Accueil', '/'], ['Ressources', '/info/'], ['Guides métier', '/info/#guides'], ['Plombier', '/info/guides/plombier/']]), article({ path: PATH, title: TITLE, description: DESC, published: '2026-11-07', section: 'Guides métier' }), faqPage(FAQS)]} />
      <article className="article">
        <p className="crumbs"><a href="/info/">Ressources</a> / <a href="/info/#guides">Guides métier</a> / Plombier</p>
        <span className="eyebrow">Guide métier · Plombier</span>
        <h1>Plombier : sortir en premier sur Google Maps quand un client a une fuite.</h1>
        <div className="meta"><span>Lecture : 7 min</span><time dateTime="2026-11-07">Mis à jour le 7 novembre 2026</time></div>

        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>Pour qu’un plombier apparaisse en premier sur Google Maps dans sa ville, il faut une fiche Google Business complète avec la catégorie « Plombier », une zone d’intervention limitée aux communes réellement couvertes, la liste détaillée des services, des avis récents qui parlent de rapidité et de prix respecté, et un numéro qui répond.</p>
        </div>
        <p>
          Un client qui a de l’eau partout ne compare pas dix devis. Il tape « plombier » ou « plombier urgence » sur
          son téléphone et appelle l’un des trois premiers résultats de la carte. Ce guide vous explique comment faire
          partie de ces trois-là.
        </p>

        <nav className="toc" aria-label="Sommaire">
          <strong className="mont">Au sommaire</strong>
          <ol>
            <li>Les bonnes catégories</li>
            <li>Déclarer sa zone d’intervention</li>
            <li>Les services à lister</li>
            <li>Les avis qui rassurent en urgence</li>
            <li>Être joignable (vraiment)</li>
          </ol>
        </nav>

        <h2>1. Les bonnes catégories</h2>
        <p>
          Catégorie principale : <strong>Plombier</strong>. Ajoutez ensuite les catégories secondaires qui correspondent
          vraiment à votre activité : <em>Chauffagiste</em>, <em>Service de débouchage</em>, <em>Entreprise de
          chauffe-eau</em>. N’ajoutez pas une catégorie que vous ne faites pas : Google le repère avec les avis.
        </p>

        <h2>2. Déclarer sa zone d’intervention</h2>
        <p>
          Vous travaillez chez vos clients : déclarez-vous en « entreprise de services de proximité » et masquez votre
          adresse si vous recevez à domicile. Listez les communes que vous couvrez vraiment (Trappes, Élancourt,
          Plaisir, Montigny…), pas tout le département.
        </p>

        <h2>3. Les services à lister</h2>
        <ul>
          <li>Recherche de fuite</li>
          <li>Débouchage canalisation / WC</li>
          <li>Remplacement chauffe-eau / ballon</li>
          <li>Dépannage urgence 7j/7 (seulement si c’est vrai)</li>
          <li>Rénovation salle de bains</li>
        </ul>
        <p>Chaque service avec une phrase de description : ce sont des mots que Google relie aux recherches.</p>

        <div className="callout">
          <strong className="mont">L’astuce qui change tout</strong>
          <p>
            Après chaque intervention, envoyez un SMS avec votre lien d’avis pendant que le client est encore soulagé.
            Le taux de réponse est bien meilleur à chaud que trois jours plus tard.
          </p>
        </div>

        <h2>4. Les avis qui rassurent en urgence</h2>
        <p>
          En urgence, le client lit deux ou trois avis, pas plus. Il cherche : rapidité, prix annoncé respecté, propreté.
          Répondez à chaque avis en reprenant ces mots (« merci, ravi d’être intervenu rapidement à Plaisir »). Ça
          rassure le lecteur et renforce votre fiche.
        </p>

        <h2>5. Être joignable (vraiment)</h2>
        <p>
          Horaires exacts, horaires spéciaux pour les jours fériés, et un numéro qui répond. Un appel manqué, c’est un
          client perdu : il rappelle le suivant. Si vous êtes sur un chantier, un renvoi vers un assistant qui prend le
          message et vous l’envoie par SMS évite de perdre ces appels.
        </p>

        <h2>Questions fréquentes</h2>
        {FAQS.map(([q, a]) => (
          <div key={q}>
            <h3>{q}</h3>
            <p>{a}</p>
          </div>
        ))}

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>Vous voulez qu’on le fasse pour vous ?</strong>
          <p>Le pack Fiche Google optimisée applique tout ce guide à votre fiche, livré en 5 jours.</p>
          <div className="hero-ctas">
            <a href="/store/fiche-google-optimisee/" className="btn btn-primary btn-sm">Voir le pack à 149 € →</a>
            <a href="/info/outil-gratuit/" className="btn btn-ghost btn-sm">Faire le test gratuit</a>
          </div>
        </div>
      </article>
    </SubShell>
  )
}
