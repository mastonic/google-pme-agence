import type { Metadata } from 'next'
import { abs, AUTHOR_PATH, breadcrumbs, FOUNDER_ID, itemList, pageMeta } from '../../../seo/seo'
import { JsonLd } from '../../../components/JsonLd'
import { SubShell } from '../../../components/SubShell'
import { GUIDES } from '../../guides/guides'

const TITLE = 'Ludovic Rigah, fondateur de Pulse Locale PME'
const DESC = 'Ludovic Rigah, président de HoldMasto et fondateur de Pulse Locale PME, signe les guides sur Google Maps, la fiche Google et la visibilité dans les IA.'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: AUTHOR_PATH })

const ARTICLES: [string, string][] = [
  ...GUIDES.map((g) => [`Guide ${g.metier.toLowerCase()}`, `/info/guides/${g.slug}/`] as [string, string]),
  ['ChatGPT, Gemini et commerces locaux', '/info/actus/chatgpt-gemini-commerces-locaux/'],
]

export default function Auteur() {
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Ressources', '/info/'], ['Ludovic Rigah', AUTHOR_PATH]]),
          { '@type': 'ProfilePage', '@id': abs(AUTHOR_PATH) + '#page', url: abs(AUTHOR_PATH), name: TITLE, inLanguage: 'fr-FR', mainEntity: { '@id': FOUNDER_ID } },
          itemList('Contenus signés par Ludovic Rigah', ARTICLES),
        ]}
      />
      <article className="article">
        <p className="crumbs"><a href="/info/">Ressources</a> / Auteur</p>
        <span className="eyebrow">Auteur et fondateur</span>
        <h1>Ludovic Rigah, fondateur de Pulse Locale PME</h1>
        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>
            Ludovic Rigah est président de HoldMasto (SASU, RCS Fort-de-France 106 121 536), la maison mère qui édite
            et opère Pulse Locale PME. Il a fondé le service pour que les artisans, commerçants et TPE soient trouvés
            sur Google Maps, recommandés par les assistants IA et ne perdent plus d’appels. Il signe les guides et
            les actualités publiés sur ce site.
          </p>
        </div>

        <h2>Pourquoi Pulse Locale PME</h2>
        <p>
          Un client qui cherche un artisan ou un commerce sur son téléphone appelle l’un des premiers résultats de la
          carte. S’il tombe sur une fiche incomplète ou une messagerie, il passe au suivant. Pulse Locale PME réunit
          ce qui fait la différence à ce moment-là : une fiche Google bien réglée, un site cohérent, des avis réguliers
          et une réceptionniste IA qui répond quand l’entrepreneur ne peut pas décrocher.
        </p>

        <h2>Notre ligne éditoriale</h2>
        <ul>
          <li>Des conseils fondés sur les règles publiques de Google Business Profile, sans astuce qui risque une suspension.</li>
          <li>Aucune promesse de position garantie : Google ne la garantit à personne.</li>
          <li>Un guide par métier, rédigé à partir des vraies recherches des clients, et mis à jour quand les règles changent.</li>
          <li>Les prix sont affichés hors taxes, sans frais cachés.</li>
        </ul>

        <h2>Contenus signés</h2>
        <ul>
          {ARTICLES.map(([name, path]) => (
            <li key={path}><a href={path} className="link-underline">{name}</a></li>
          ))}
        </ul>

        <h2>Contact</h2>
        <p>
          Pour une question sur un guide ou sur l’offre : <a href="mailto:contact-plp@holdmasto.fr" className="link-underline">contact-plp@holdmasto.fr</a>.
          Les informations légales de l’éditeur sont dans les <a href="/mentions-legales/#mentions" className="link-underline">mentions légales</a>.
        </p>
      </article>
    </SubShell>
  )
}
