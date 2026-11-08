import type { Metadata } from 'next'
import { abs, breadcrumbs, ORG_ID, pageMeta } from '../seo/seo'
import { JsonLd } from '../components/JsonLd'
import { PageHero, SubShell } from '../components/SubShell'
import { GUIDES } from './guides/guides'
import { ARTICLES, articlePath } from './articles/articles'
import { siteHref } from '../seo/domains'

export const metadata: Metadata = pageMeta({
  title: 'Être trouvé sur Google Maps et les IA : guides pour artisans | Pulse Locale PME',
  description: 'Guides par métier, actus Google Maps et IA, test de visibilité gratuit et guide PDF : tout pour attirer plus de clients locaux, expliqué simplement.',
  path: '/info/',
})


const NEWS = [
  ['chatgpt-gemini-commerces-locaux', 'IA', 'ChatGPT et Gemini recommandent des commerces : comment être dans la liste'],
  ['', 'Google Maps', 'Fiche suspendue : les 5 erreurs qui déclenchent un blocage'],
  ['', 'Avis', 'Faux avis : ce que Google supprime désormais (et comment réagir)'],
]

export default function Info() {
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Ressources', '/info/']]),
          { '@type': 'CollectionPage', name: 'Ressources Pulse Locale PME', url: abs('/info/'), inLanguage: 'fr-FR', publisher: { '@id': ORG_ID } },
        ]}
      />
      <PageHero
        eyebrow="Ressources gratuites pour TPE, artisans et commerçants"
        title="Être trouvé sur Google, expliqué simplement."
        lead="Des guides concrets par métier, l’actu Google Maps et IA décryptée, et un test gratuit pour savoir où vous en êtes. Sans jargon, sans blabla."
      >
        <a href={siteHref('/info/outil-gratuit/')} className="btn btn-primary">Tester ma visibilité en 30 s →</a>
        <a href={siteHref('/info/guide-gratuit/')} className="btn btn-ghost">Télécharger le guide PDF</a>
      </PageHero>

      <section className="band-white">
        <div className="wrap section">
          <div className="grid-280">
            <a href={siteHref('/info/outil-gratuit/')} className="card" data-reveal="stagger">
              <span className="card-tag">Outil gratuit</span>
              <h3>Votre score de visibilité locale</h3>
              <p>8 questions, un score sur 100 et les 3 actions qui vous rapporteront le plus de clients.</p>
              <span className="link-underline">Faire le test →</span>
            </a>
            <a href={siteHref('/info/guide-gratuit/')} className="card" data-reveal="stagger">
              <span className="card-tag">Guide PDF</span>
              <h3>Les 10 erreurs qui cachent votre commerce sur Google</h3>
              <p>La checklist qu’on utilise pour auditer nos clients. 14 pages, à lire en 15 minutes.</p>
              <span className="link-underline">Télécharger →</span>
            </a>
            <a href={siteHref('/info/guides/plombier/')} className="card" data-reveal="stagger">
              <span className="card-tag">Guide métier</span>
              <h3>Plombier : sortir en premier sur Google Maps</h3>
              <p>L’exemple complet, étape par étape, adapté aux urgences et aux zones d’intervention.</p>
              <span className="link-underline">Lire le guide →</span>
            </a>
          </div>
        </div>
      </section>

      <section id="guides" className="wrap section">
        <div className="section-head" data-reveal="0">
          <span className="eyebrow">Guides par métier</span>
          <h2 className="h2">Votre métier a ses propres règles sur Google.</h2>
          <p className="section-lead">Un plombier ne se cherche pas comme un coiffeur. Chaque guide part des vraies recherches de vos clients.</p>
        </div>
        <div className="grid-280">
          {GUIDES.map((g) => (
            <a key={g.slug} href={siteHref(`/info/guides/${g.slug}/`)} className="card" data-reveal="stagger">
              <h3>Guide {g.metier.toLowerCase()}</h3>
              <p>{g.card}</p>
              <span className="small muted">Lire le guide →</span>
            </a>
          ))}
        </div>
      </section>

      <section id="articles" className="wrap section">
        <div className="section-head" data-reveal="0">
          <span className="eyebrow">Articles de fond</span>
          <h2 className="h2">Prix, Google Maps, IA : des réponses sourcées.</h2>
        </div>
        <div className="grid-280">
          <a href={siteHref('/info/seo-aeo-geo/')} className="card" data-reveal="stagger">
            <span className="card-tag gold">Guide de référence</span>
            <h3>SEO, AEO et GEO : définitions, différences et méthodes</h3>
            <span className="small muted">Lire le guide →</span>
          </a>
          {ARTICLES.map((a) => (
            <a key={a.slug} href={siteHref(articlePath(a.slug))} className="card" data-reveal="stagger">
              <span className="card-tag">Article</span>
              <h3>{a.title}</h3>
              <span className="small muted">Lire l’article →</span>
            </a>
          ))}
        </div>
      </section>

      <section id="actus" className="band-white">
        <div className="wrap section">
          <div className="section-head" data-reveal="0">
            <span className="eyebrow">Actus</span>
            <h2 className="h2">Ce qui change sur Google et dans les IA, et ce que ça change pour vous.</h2>
          </div>
          <div className="grid-280">
            {NEWS.map(([slug, tag, t]) => (
              slug ? (
                <a key={t} href={siteHref(`/info/actus/${slug}/`)} className="card" data-reveal="stagger">
                  <span className="card-tag">{tag}</span>
                  <h3>{t}</h3>
                  <span className="small muted">Lire l’article →</span>
                </a>
              ) : (
                <div key={t} className="card" data-reveal="stagger">
                  <span className="card-tag">{tag}</span>
                  <h3>{t}</h3>
                  <span className="small muted">Bientôt disponible</span>
                </div>
              )
            ))}
          </div>
        </div>
      </section>

      <section className="final-band">
        <div className="final" data-reveal="0">
          <h2>Pas le temps de tout faire vous-même ?</h2>
          <p>Nos packs à prix fixe font le travail à votre place, livrés en quelques jours.</p>
          <a href={siteHref('/store/')} className="btn btn-final">Voir la boutique →</a>
        </div>
      </section>
    </SubShell>
  )
}
