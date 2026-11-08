import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { article, breadcrumbs, faqPage, howTo, pageMeta } from '../../../seo/seo'
import { JsonLd } from '../../../components/JsonLd'
import { SubShell } from '../../../components/SubShell'
import { Byline } from '../../../components/Byline'
import { GUIDES, PUBLISHED, UPDATED, guideBySlug, type Guide } from '../guides'

export const dynamicParams = false

export function generateStaticParams() {
  return GUIDES.map((g) => ({ slug: g.slug }))
}

const pathOf = (g: Guide) => `/info/guides/${g.slug}/`

export function generateMetadata({ params }: { params: { slug: string } }): Metadata {
  const g = guideBySlug(params.slug)
  if (!g) return {}
  return pageMeta({ title: g.title, description: g.description, path: pathOf(g), type: 'article' })
}

const DATE_FR = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(UPDATED))

/** Étapes communes à tous les guides, nourries par le contenu propre au métier. */
function steps(g: Guide): { id: string; title: string; summary: string }[] {
  const s = [
    { id: 'recherches', title: 'Comprendre ce que vos clients tapent', summary: `Les recherches réelles : ${g.searches.slice(0, 3).join(', ')}…` },
    { id: 'categories', title: 'Choisir les bonnes catégories', summary: `Catégorie principale « ${g.categories.main} », puis des catégories secondaires réellement exercées.` },
    { id: 'zone', title: 'Adresse ou zone d’intervention', summary: g.zone },
    { id: 'services', title: 'Lister vos services', summary: g.services.join(', ') + '.' },
    { id: 'photos', title: 'Publier les bonnes photos', summary: g.photos },
    { id: 'avis', title: 'Obtenir et répondre aux avis', summary: g.reviews },
  ]
  if (g.extra) s.push({ id: 'specifique', title: g.extra.title, summary: g.extra.body })
  s.push({ id: 'joignable', title: 'Être joignable (vraiment)', summary: g.reachable })
  s.push({ id: 'ia', title: 'Être recommandé par ChatGPT, Gemini et Google', summary: g.ai })
  return s
}

function checklist(g: Guide): string[] {
  return [
    `Fiche Google Business revendiquée et vérifiée, nom exact sans mots-clés`,
    `Catégorie principale « ${g.categories.main} »`,
    `${g.categories.secondary.length} catégories secondaires au maximum, toutes réellement exercées`,
    'Adresse ou zone d’intervention exacte, cohérente avec la réalité',
    'Horaires exacts, horaires spéciaux des jours fériés à jour',
    `Au moins ${Math.min(5, g.services.length)} services décrits en une phrase chacun`,
    'Photos réelles et récentes (au moins une nouvelle par mois)',
    'Un avis demandé après chaque client satisfait, une réponse à chaque avis',
    'Même nom, adresse et téléphone sur la fiche, le site et les annuaires',
    'Un numéro qui répond, même quand vous êtes occupé',
  ]
}

export default function GuidePage({ params }: { params: { slug: string } }) {
  const g = guideBySlug(params.slug)
  if (!g) notFound()
  const path = pathOf(g)
  const st = steps(g)
  const related = g.related.map(guideBySlug).filter(Boolean) as Guide[]
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Ressources', '/info/'], ['Guides métier', '/info/guides/'], [g.metier, path]]),
          article({ path, title: g.title, description: g.description, published: PUBLISHED, modified: UPDATED, section: 'Guides métier', about: g.metier }),
          howTo({ path, name: g.h1, steps: st.map((x) => [x.title, x.summary]) }),
          faqPage(g.faqs),
        ]}
      />
      <article className="article">
        <p className="crumbs">
          <a href="/info/">Ressources</a> / <a href="/info/guides/">Guides métier</a> / {g.metier}
        </p>
        <span className="eyebrow">Guide métier · {g.metier}</span>
        <h1>{g.h1}</h1>
        <div className="meta">
          <span>Lecture : {g.readMin} min</span>
          <time dateTime={UPDATED}>Mis à jour le {DATE_FR}</time>
          <Byline />
        </div>

        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>{g.enBref}</p>
        </div>
        <p>{g.intro}</p>

        <nav className="toc" aria-label="Sommaire">
          <strong className="mont">Au sommaire</strong>
          <ol>
            {st.map((x, i) => (
              <li key={x.id}><a href={`#etape-${i + 1}`}>{x.title}</a></li>
            ))}
            <li><a href="#checklist">La checklist</a></li>
            <li><a href="#faq">Questions fréquentes</a></li>
          </ol>
        </nav>

        <h2 id="etape-1">1. Comprendre ce que vos clients tapent</h2>
        <p>Vos futurs clients ne cherchent pas votre nom : ils décrivent leur besoin. Les recherches les plus fréquentes pour un {g.metier.toLowerCase()} :</p>
        <ul>{g.searches.map((q) => <li key={q}>« {q} »</li>)}</ul>
        <p>Chacune de ces expressions doit se retrouver naturellement dans votre fiche Google (services, description, réponses aux avis) et sur votre site.</p>

        <h2 id="etape-2">2. Choisir les bonnes catégories</h2>
        <p>
          Catégorie principale : <strong>{g.categories.main}</strong>. C’est le réglage qui pèse le plus dans votre classement.
          Ajoutez ensuite les catégories secondaires qui correspondent vraiment à votre activité :{' '}
          {g.categories.secondary.map((c, i) => (<span key={c}><em>{c}</em>{i < g.categories.secondary.length - 1 ? ', ' : '.'}</span>))}
          {' '}Choisissez toujours l’intitulé le plus proche dans la liste proposée par Google, et n’ajoutez pas une catégorie que vous n’exercez pas.
        </p>

        <h2 id="etape-3">3. Adresse ou zone d’intervention</h2>
        <p>{g.zone}</p>

        <h2 id="etape-4">4. Lister vos services</h2>
        <ul>{g.services.map((x) => <li key={x}>{x}</li>)}</ul>
        <p>Décrivez chaque service en une phrase simple : ce sont des mots que Google et les assistants IA relient aux recherches de vos clients.</p>

        <h2 id="etape-5">5. Publier les bonnes photos</h2>
        <p>{g.photos}</p>

        <h2 id="etape-6">6. Obtenir et répondre aux avis</h2>
        <p>{g.reviews}</p>

        <div className="callout">
          <strong className="mont">L’astuce qui change tout</strong>
          <p>{g.tip}</p>
        </div>

        {g.extra && (
          <>
            <h2 id="etape-7">7. {g.extra.title}</h2>
            <p>{g.extra.body}</p>
            {g.extra.list && <ul>{g.extra.list.map((x) => <li key={x}>{x}</li>)}</ul>}
          </>
        )}

        <h2 id={`etape-${g.extra ? 8 : 7}`}>{g.extra ? 8 : 7}. Être joignable (vraiment)</h2>
        <p>{g.reachable}</p>

        <h2 id={`etape-${g.extra ? 9 : 8}`}>{g.extra ? 9 : 8}. Être recommandé par ChatGPT, Gemini et Google</h2>
        <p>{g.ai}</p>
        <p>
          Les assistants IA et les réponses générées par Google reprennent les informations les plus claires et les plus
          cohérentes : un nom, une adresse et un téléphone identiques partout, des services décrits simplement, des avis
          récents et des réponses directes aux questions que se posent vos clients.
        </p>

        <h2 id="checklist">La checklist {g.metier.toLowerCase()} en 10 points</h2>
        <ol>{checklist(g).map((x) => <li key={x}>{x}</li>)}</ol>

        <h2 id="faq">Questions fréquentes</h2>
        {g.faqs.map(([q, a]) => (
          <div key={q}>
            <h3>{q}</h3>
            <p>{a}</p>
          </div>
        ))}

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>Vous voulez qu’on le fasse pour vous ?</strong>
          <p>Le pack Fiche Google optimisée applique tout ce guide à votre fiche, livré en 5 jours. Et la réceptionniste IA répond aux appels que vous ne pouvez pas prendre.</p>
          <div className="hero-ctas">
            <a href="/store/fiche-google-optimisee/" className="btn btn-primary btn-sm">Voir le pack à 149 € HT →</a>
            <a href="/info/outil-gratuit/" className="btn btn-ghost btn-sm">Faire le test gratuit</a>
          </div>
        </div>

        {related.length > 0 && (
          <nav aria-label="Guides voisins">
            <h2>Guides voisins</h2>
            <ul>
              {related.map((r) => (
                <li key={r.slug}><a href={pathOf(r)} className="link-underline">Guide {r.metier.toLowerCase()} : {r.card}</a></li>
              ))}
              <li><a href="/info/guides/" className="link-underline">Tous les guides métier</a></li>
            </ul>
          </nav>
        )}
      </article>
    </SubShell>
  )
}
