import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { abs, breadcrumbs, faqPage, localService, pageMeta } from '../../../seo/seo'
import { Byline } from '../../../components/Byline'
import { JsonLd } from '../../../components/JsonLd'
import { OrderButton } from '../../../components/OrderButton'
import { SubShell } from '../../../components/SubShell'
import { guideBySlug, type Guide } from '../../../info/guides/guides'
import { DEPTS, ZONES_UPDATED, cityOf, cityPath, deptBySlug, deptPath } from '../../zones'

export const dynamicParams = false

export function generateStaticParams() {
  return DEPTS.flatMap((d) => d.cities.map((c) => ({ dept: d.slug, ville: c.slug })))
}

export function generateMetadata({ params }: { params: { dept: string; ville: string } }): Metadata {
  const d = deptBySlug(params.dept)
  const c = cityOf(params.dept, params.ville)
  if (!d || !c) return {}
  return pageMeta({ title: c.title, description: c.description, path: cityPath(d, c) })
}

const DATE_FR = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(ZONES_UPDATED))

export default function CityPage({ params }: { params: { dept: string; ville: string } }) {
  const d = deptBySlug(params.dept)
  const c = cityOf(params.dept, params.ville)
  if (!d || !c) notFound()
  const path = cityPath(d, c)
  const region = `${d.name} (${d.code})`
  const guides = c.metiers.map(guideBySlug).filter(Boolean) as Guide[]
  const others = d.cities.filter((x) => x.slug !== c.slug)
  return (
    <SubShell variant="info">
      <JsonLd
        items={[
          breadcrumbs([['Accueil', '/'], ['Zones desservies', '/zones/'], [d.name, deptPath(d)], [c.name, path]]),
          { '@type': 'WebPage', '@id': abs(path) + '#page', url: abs(path), name: c.title, inLanguage: 'fr-FR', dateModified: ZONES_UPDATED, about: { '@type': 'City', name: c.name, containedInPlace: { '@type': 'AdministrativeArea', name: region } } },
          localService({ path, name: `Fiche Google, site et réceptionniste IA à ${c.name}`, description: c.enBref, areas: c.communes, region }),
          faqPage(c.faqs),
        ]}
      />
      <article className="article">
        <p className="crumbs">
          <a href="/zones/">Zones desservies</a> / <a href={deptPath(d)}>{d.name}</a> / {c.name}
        </p>
        <span className="eyebrow">{region} · {c.name}</span>
        <h1>{c.h1}</h1>
        <div className="meta">
          <time dateTime={ZONES_UPDATED}>Mis à jour le {DATE_FR}</time>
          <Byline />
        </div>

        <div className="callout" role="note">
          <strong className="mont">En bref</strong>
          <p>{c.enBref}</p>
        </div>
        {c.context.map((p) => <p key={p.slice(0, 24)}>{p}</p>)}

        <h2 id="zones">Communes desservies autour de {c.name}</h2>
        <ul className="cols-2">{c.communes.map((x) => <li key={x}>{x}</li>)}</ul>
        <p>Nous accompagnons les entreprises de ces communes entièrement en ligne : pas de rendez-vous en agence, tout se suit depuis votre espace client.</p>

        <h2 id="recherches">Ce que vos clients tapent à {c.name}</h2>
        <ul>{c.searches.map((q) => <li key={q}>« {q} »</li>)}</ul>
        <p>Ces expressions doivent se retrouver naturellement dans votre fiche Google (catégories, services, réponses aux avis) et sur votre site, avec le même nom, la même adresse et le même téléphone partout.</p>

        <h2 id="receptionniste">Réceptionniste IA : ne plus perdre un appel à {c.name}</h2>
        <p>{c.reception}</p>
        <ul>
          <li>Votre numéro ne change pas : simple renvoi d’appel quand vous ne décrochez pas.</li>
          <li>Appels et messages WhatsApp pris au nom de votre entreprise, résumé envoyé par WhatsApp ou SMS.</li>
          <li>Essai gratuit de 30 jours (60 appels), puis 39 € HT par mois avec 100 appels inclus, ou incluse dans Élite.</li>
        </ul>
        <div className="hero-ctas">
          <OrderButton product={`Réceptionniste IA – ${c.name}`} source="callback" title={`Activer ma réceptionniste IA à ${c.name}`} className="btn btn-primary btn-sm">
            Essayer la réceptionniste IA →
          </OrderButton>
        </div>

        <h2 id="methode">Notre méthode en 4 étapes</h2>
        <ol>
          <li><strong>Diagnostic gratuit</strong> de votre fiche Google et de vos concurrents à {c.name}.</li>
          <li><strong>Fiche Google optimisée</strong> : catégories, zone d’intervention, services, photos, horaires.</li>
          <li><strong>Site cohérent et avis réguliers</strong> pour gagner la confiance de Google et des assistants IA.</li>
          <li><strong>Réceptionniste IA</strong> pour transformer chaque appel en client.</li>
        </ol>

        <h2 id="tarifs">Tarifs</h2>
        <p>
          Les mêmes partout, hors taxes et sans frais de création : Starter 49 € HT par mois (site vitrine), Pro 149 € HT
          (fiche Google optimisée et SEO local), Élite 299 € HT (réceptionniste IA incluse). Sans engagement, ou 2 mois
          offerts en annuel. Le pack <a href="/store/fiche-google-optimisee/" className="link-underline">Fiche Google optimisée</a> existe aussi à 149 € HT, sans abonnement.
        </p>

        {guides.length > 0 && (
          <>
            <h2 id="guides">Guides pour votre métier</h2>
            <ul>
              {guides.map((g) => (
                <li key={g.slug}><a href={`/info/guides/${g.slug}/`} className="link-underline">Guide {g.metier.toLowerCase()}</a> : {g.card}</li>
              ))}
            </ul>
          </>
        )}

        <h2 id="faq">Questions fréquentes à {c.name}</h2>
        {c.faqs.map(([q, a]) => (
          <div key={q}>
            <h3>{q}</h3>
            <p>{a}</p>
          </div>
        ))}

        <div className="callout dark">
          <strong className="mont" style={{ fontSize: 20 }}>Où en est votre fiche Google à {c.name} ?</strong>
          <p>Le test de visibilité gratuit vous donne un score sur 100 en 8 questions, et les actions prioritaires.</p>
          <div className="hero-ctas">
            <a href="/info/outil-gratuit/" className="btn btn-primary btn-sm">Faire le test gratuit →</a>
            <a href="/#offres" className="btn btn-ghost btn-sm">Voir les formules</a>
          </div>
        </div>

        <nav aria-label="Villes voisines">
          <h2>Autres villes : {d.name}</h2>
          <ul>
            {others.map((x) => (
              <li key={x.slug}><a href={cityPath(d, x)} className="link-underline">{x.name}</a></li>
            ))}
            <li><a href={deptPath(d)} className="link-underline">Tout le département {region}</a></li>
          </ul>
        </nav>
      </article>
    </SubShell>
  )
}
