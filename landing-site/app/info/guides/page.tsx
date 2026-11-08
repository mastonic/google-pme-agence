import type { Metadata } from 'next'
import { abs, breadcrumbs, itemList, ORG_ID, pageMeta } from '../../seo/seo'
import { JsonLd } from '../../components/JsonLd'
import { PageHero, SubShell } from '../../components/SubShell'
import { GUIDES } from './guides'

const TITLE = 'Guides par métier : être trouvé sur Google Maps et les IA'
const DESC = 'Plombier, coiffeur, restaurant, garage, taxi… Un guide par métier pour sortir en premier sur Google Maps et être recommandé par ChatGPT et Gemini.'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: '/info/guides/' })

export default function Guides() {
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Ressources', '/info/'], ['Guides métier', '/info/guides/']]),
          { '@type': 'CollectionPage', name: 'Guides par métier', url: abs('/info/guides/'), inLanguage: 'fr-FR', publisher: { '@id': ORG_ID } },
          itemList('Guides par métier', GUIDES.map((g) => [`Guide ${g.metier.toLowerCase()}`, `/info/guides/${g.slug}/`])),
        ]}
      />
      <PageHero
        eyebrow="Guides métier gratuits"
        title="Votre métier a ses propres règles sur Google."
        lead="Un plombier ne se cherche pas comme un coiffeur. Chaque guide part des vraies recherches de vos clients et vous donne les réglages qui font sonner le téléphone."
      >
        <a href="/info/outil-gratuit/" className="btn btn-primary">Tester ma visibilité en 30 s →</a>
      </PageHero>
      <section className="wrap section">
        <div className="grid-280">
          {GUIDES.map((g) => (
            <a key={g.slug} href={`/info/guides/${g.slug}/`} className="card" data-reveal="stagger">
              <span className="card-tag">Guide métier</span>
              <h2 style={{ fontSize: 20 }}>Guide {g.metier.toLowerCase()}</h2>
              <p>{g.card}</p>
              <span className="link-underline">Lire le guide →</span>
            </a>
          ))}
        </div>
      </section>
    </SubShell>
  )
}
