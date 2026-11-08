import type { Metadata } from 'next'
import { abs, breadcrumbs, itemList, ORG_ID, pageMeta } from '../../seo/seo'
import { siteHref } from '../../seo/domains'
import { JsonLd } from '../../components/JsonLd'
import { PageHero, SubShell } from '../../components/SubShell'
import { ARTICLES, articlePath } from './articles'

const TITLE = 'Articles : prix, Google Maps, SEO local et IA pour TPE'
const DESC = 'Prix d’un site d’artisan, fiche Google, choix d’une agence SEO local, visibilité dans ChatGPT, réceptionniste IA : des réponses sourcées et à jour.'

export const metadata: Metadata = pageMeta({ title: TITLE, description: DESC, path: '/info/articles/' })

export default function Articles() {
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Ressources', '/info/'], ['Articles', '/info/articles/']]),
          { '@type': 'CollectionPage', name: 'Articles Pulse Locale PME', url: abs('/info/articles/'), inLanguage: 'fr-FR', publisher: { '@id': ORG_ID } },
          itemList('Articles', ARTICLES.map((a) => [a.title, articlePath(a.slug)])),
        ]}
      />
      <PageHero eyebrow="Articles de fond" title="Des réponses claires, sourcées et datées." lead="Prix, Google Maps, choix d’un prestataire, intelligence artificielle : chaque article commence par une réponse courte et cite ses sources.">
        <a href={siteHref('/info/seo-aeo-geo/')} className="btn btn-primary">SEO, AEO, GEO : le guide →</a>
      </PageHero>
      <section className="wrap section">
        <div className="grid-280">
          {ARTICLES.map((a) => (
            <a key={a.slug} href={siteHref(articlePath(a.slug))} className="card" data-reveal="stagger">
              <span className="card-tag">Article · {a.readMin} min</span>
              <h2 style={{ fontSize: 20 }}>{a.title}</h2>
              <p>{a.card}</p>
              <span className="link-underline">Lire l’article →</span>
            </a>
          ))}
        </div>
      </section>
    </SubShell>
  )
}
