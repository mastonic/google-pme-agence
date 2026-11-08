import type { ReactNode } from 'react'
import { article, breadcrumbs, faqPage } from '../seo/seo'
import { siteHref } from '../seo/domains'
import { articleBySlug, articlePath, ARTICLES } from '../info/articles/articles'
import { Byline } from './Byline'
import { JsonLd } from './JsonLd'
import { SubShell } from './SubShell'

export type Section = { id: string; title: string; body: ReactNode }
export type Source = [string, string] // [libellé, url]

const fmtDate = (d: string) => new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(d))

/** Gabarit des articles de fond du .info : réponse directe, sommaire, sections, FAQ, sources. */
export function ArticleLayout({ slug, answer, sections, faqs, sources, related, cta }: {
  slug: string
  answer: string
  sections: Section[]
  faqs: [string, string][]
  sources: Source[]
  related: string[]
  cta?: ReactNode
}) {
  const a = articleBySlug(slug)!
  const path = articlePath(slug)
  const rel = related.map((r) => ARTICLES.find((x) => x.slug === r)).filter(Boolean) as typeof ARTICLES
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Ressources', '/info/'], ['Articles', '/info/articles/'], [a.title, path]]),
          { ...article({ path, title: a.title, description: a.description, published: a.published, modified: a.modified, section: 'Articles' }), keywords: a.keyword, citation: sources.map(([, url]) => url) },
          faqPage(faqs),
        ]}
      />
      <article className="article">
        <p className="crumbs">
          <a href={siteHref('/info/')}>Ressources</a> / <a href={siteHref('/info/articles/')}>Articles</a>
        </p>
        <h1>{a.title}</h1>
        <div className="meta">
          <span>Lecture : {a.readMin} min</span>
          <time dateTime={a.published}>Publié le {fmtDate(a.published)}</time>
          {a.modified !== a.published && <time dateTime={a.modified}>Mis à jour le {fmtDate(a.modified)}</time>}
          <Byline />
        </div>
        <div className="callout" role="note">
          <strong className="mont">La réponse courte</strong>
          <p>{answer}</p>
        </div>
        <nav className="toc" aria-label="Sommaire">
          <strong className="mont">Au sommaire</strong>
          <ol>
            {sections.map((s) => <li key={s.id}><a href={`#${s.id}`}>{s.title}</a></li>)}
            <li><a href="#faq">Questions fréquentes</a></li>
            <li><a href="#sources">Sources</a></li>
          </ol>
        </nav>
        {sections.map((s) => (
          <section key={s.id} aria-labelledby={s.id} style={{ display: 'contents' }}>
            <h2 id={s.id}>{s.title}</h2>
            {s.body}
          </section>
        ))}
        <h2 id="faq">Questions fréquentes</h2>
        {faqs.map(([q, ans]) => (
          <div key={q}>
            <h3>{q}</h3>
            <p>{ans}</p>
          </div>
        ))}
        {cta ?? (
          <div className="callout dark">
            <strong className="mont" style={{ fontSize: 20 }}>Et pour votre entreprise ?</strong>
            <p>Le test de visibilité gratuit vous donne un score sur 100 et vos actions prioritaires, en 8 questions.</p>
            <div className="hero-ctas">
              <a href={siteHref('/info/outil-gratuit/')} className="btn btn-primary btn-sm">Faire le test gratuit →</a>
              <a href={siteHref('/#offres')} className="btn btn-ghost btn-sm">Voir les formules</a>
            </div>
          </div>
        )}
        <h2 id="sources">Sources</h2>
        <ol className="sources">
          {sources.map(([label, url]) => (
            <li key={url}><a href={url} rel="noopener" target="_blank">{label}</a></li>
          ))}
        </ol>
        {rel.length > 0 && (
          <nav aria-label="À lire aussi">
            <h2>À lire aussi</h2>
            <ul>
              {rel.map((r) => <li key={r.slug}><a href={siteHref(articlePath(r.slug))} className="link-underline">{r.title}</a></li>)}
              <li><a href={siteHref('/info/seo-aeo-geo/')} className="link-underline">SEO, AEO et GEO : le guide de référence</a></li>
            </ul>
          </nav>
        )}
      </article>
    </SubShell>
  )
}

export const metaFor = (slug: string) => {
  const a = articleBySlug(slug)!
  return { title: a.title, description: a.description, path: articlePath(slug), type: 'article' as const }
}
